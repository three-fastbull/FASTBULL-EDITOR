"""Conservative offline editorial analysis for FASTBULL talking-head clips."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Iterable


SAFE_FILLERS = {"เอ่อ", "อ่า", "อืม", "เอิ่ม", "uh", "um", "erm"}
SOFT_FILLERS = {"แบบว่า", "ก็คือ", "ประมาณว่า", "จริงๆ", "นะครับ", "นะคะ"}
PROTECTED_TERMS = {"fastbull", "vlog", "b-roll", "cta", "ai", "codex", "claude"}


def _clean(word: str) -> str:
    return re.sub(r"[^\w\u0E00-\u0E7F-]", "", word.lower()).strip()


def flatten_words(segments: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    words: list[dict[str, Any]] = []
    for segment_index, segment in enumerate(segments):
        for word_index, word in enumerate(segment.get("words") or []):
            item = dict(word)
            item["segment_index"] = segment_index
            item["word_index"] = word_index
            words.append(item)
    return words


def analyze_transcript(
    segments: list[dict[str, Any]],
    *,
    exact_corrections: dict[str, str] | None = None,
    low_confidence: float = 0.55,
    pause_seconds: float = 0.8,
) -> dict[str, Any]:
    """Create review flags and only narrowly safe deletion suggestions.

    The function never guesses facts or silently rewrites uncertain Thai. Exact
    corrections must be supplied by the editor/client; ambiguous findings stay
    in ``review_flags``.
    """
    corrections = {_clean(k): v for k, v in (exact_corrections or {}).items()}
    words = flatten_words(segments)
    flags: list[dict[str, Any]] = []
    safe_removals: list[dict[str, Any]] = []

    previous: dict[str, Any] | None = None
    for item in words:
        raw = str(item.get("word", ""))
        token = _clean(raw)
        start = float(item.get("start", 0.0))
        end = float(item.get("end", start))
        probability = float(item.get("probability", 1.0))

        if token in corrections:
            flags.append({"type": "approved_correction", "start": start, "end": end,
                          "original": raw, "replacement": corrections[token], "severity": "auto"})
        elif probability < low_confidence and token not in PROTECTED_TERMS:
            flags.append({"type": "low_confidence_word", "start": start, "end": end,
                          "word": raw, "confidence": round(probability, 3), "severity": "review"})

        if token in SAFE_FILLERS:
            cue = {"type": "isolated_filler", "start": start, "end": end,
                   "word": raw, "severity": "review"}
            flags.append(cue)
            if end - start <= 0.8:
                safe_removals.append({"start": start, "end": end, "reason": "short_filler"})
        elif token in SOFT_FILLERS:
            flags.append({"type": "soft_filler", "start": start, "end": end,
                          "word": raw, "severity": "review"})

        if previous is not None:
            prev_token = _clean(str(previous.get("word", "")))
            prev_end = float(previous.get("end", 0.0))
            if token and token == prev_token and token not in PROTECTED_TERMS:
                flags.append({"type": "possible_repeat", "start": start, "end": end,
                              "word": raw, "severity": "review"})
            gap = start - prev_end
            if gap >= pause_seconds:
                flags.append({"type": "pause", "start": prev_end, "end": start,
                              "duration": round(gap, 3), "severity": "auto"})
        previous = item

    return {
        "version": "1.0",
        "word_count": len(words),
        "review_flags": flags,
        "safe_removal_candidates": merge_intervals(safe_removals, gap=0.05),
        "approved_corrections": dict(exact_corrections or {}),
        "policy": "Only silence and explicit corrections are automatic; uncertain speech requires review.",
    }


def merge_intervals(intervals: Iterable[dict[str, Any]], gap: float = 0.0) -> list[dict[str, Any]]:
    ordered = sorted((dict(i) for i in intervals), key=lambda i: float(i["start"]))
    merged: list[dict[str, Any]] = []
    for item in ordered:
        item["start"] = float(item["start"])
        item["end"] = float(item["end"])
        if item["end"] <= item["start"]:
            continue
        if merged and item["start"] <= merged[-1]["end"] + gap:
            merged[-1]["end"] = max(merged[-1]["end"], item["end"])
            reasons = {str(merged[-1].get("reason", "edit")), str(item.get("reason", "edit"))}
            merged[-1]["reason"] = "+".join(sorted(reasons))
        else:
            merged.append(item)
    return merged


def build_keep_segments(duration: float, removals: Iterable[dict[str, Any]]) -> list[dict[str, float]]:
    cursor = 0.0
    keep: list[dict[str, float]] = []
    for cut in merge_intervals(removals):
        start = min(max(float(cut["start"]), 0.0), duration)
        end = min(max(float(cut["end"]), start), duration)
        if start > cursor:
            keep.append({"start": round(cursor, 3), "end": round(start, 3)})
        cursor = max(cursor, end)
    if cursor < duration:
        keep.append({"start": round(cursor, 3), "end": round(duration, 3)})
    return keep


def retime_transcript(
    segments: list[dict[str, Any]], keep_segments: list[dict[str, Any]], *, language: str = "th"
) -> list[dict[str, Any]]:
    """Map word timestamps from the source timeline to a jump-cut timeline."""
    mapped: list[dict[str, Any]] = []
    offset = 0.0
    for keep in keep_segments:
        keep_start = float(keep["start"])
        keep_end = float(keep["end"])
        for segment in segments:
            new_words: list[dict[str, Any]] = []
            for word in segment.get("words") or []:
                start = float(word.get("start", 0.0))
                end = float(word.get("end", start))
                if end <= keep_start or start >= keep_end:
                    continue
                new_word = deepcopy(word)
                new_word["start"] = round(offset + max(start, keep_start) - keep_start, 3)
                new_word["end"] = round(offset + min(end, keep_end) - keep_start, 3)
                if new_word["end"] > new_word["start"]:
                    new_words.append(new_word)
            if new_words:
                separator = "" if language == "th" else " "
                mapped.append({
                    "id": len(mapped),
                    "start": new_words[0]["start"],
                    "end": new_words[-1]["end"],
                    "text": separator.join(str(w.get("word", "")).strip() for w in new_words),
                    "words": new_words,
                })
        offset += max(0.0, keep_end - keep_start)
    mapped.sort(key=lambda segment: segment["start"])
    for index, segment in enumerate(mapped):
        segment["id"] = index
    return mapped
