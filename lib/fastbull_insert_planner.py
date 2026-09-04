"""Content-aware, copyright-safe insert planning for FASTBULL edits."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from lib.fastbull_modes import get_mode_profile


MEDIA_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".jpg", ".jpeg", ".png", ".webp"}
THAI_STOPWORDS = {"และ", "หรือ", "ที่", "เป็น", "อยู่", "แล้ว", "ก็", "จะ", "ของ", "ใน", "ให้", "ได้", "มี", "ครับ", "ค่ะ"}


def _tokens(text: str) -> list[str]:
    try:
        from pythainlp.tokenize import word_tokenize
        rough = word_tokenize(text.lower(), engine="newmm", keep_whitespace=False)
    except ImportError:
        rough = re.findall(r"[\w\u0E00-\u0E7F]+", text.lower())
    return [token.strip() for token in rough if len(token.strip()) >= 2 and token.strip() not in THAI_STOPWORDS]


def index_broll(directories: Iterable[str | Path]) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for directory in directories:
        root = Path(directory)
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in MEDIA_EXTENSIONS:
                continue
            sidecar = path.with_suffix(".txt")
            description = sidecar.read_text(encoding="utf-8") if sidecar.is_file() else ""
            searchable = f"{path.stem.replace('_', ' ').replace('-', ' ')} {description}"
            assets.append({
                "path": str(path.resolve()),
                "kind": "video" if path.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"} else "image",
                "tokens": sorted(set(_tokens(searchable))),
                "rights_status": "client_owned_or_editor_approved",
            })
    return assets


def _transcript_text_at(segments: list[dict[str, Any]], at: float, window: float = 3.5) -> str:
    matches = [str(s.get("text", "")).strip() for s in segments
               if float(s.get("end", 0)) >= at - window / 2 and float(s.get("start", 0)) <= at + window / 2]
    return " ".join(match for match in matches if match).strip()


def plan_inserts(
    segments: list[dict[str, Any]],
    *,
    duration_seconds: float,
    mode: str,
    broll_dirs: Iterable[str | Path] = (),
) -> dict[str, Any]:
    """Plan local B-roll or a deterministic motion-card fallback."""
    profile = get_mode_profile(mode)
    interval = float(profile["insert_interval_seconds"])
    assets = index_broll(broll_dirs)
    cues: list[dict[str, Any]] = []
    used: set[str] = set()
    at = max(float(profile["hook_seconds"]) + 1.0, interval)

    while at < max(0.0, duration_seconds - 2.0):
        context = _transcript_text_at(segments, at)
        keywords = _tokens(context)
        scored: list[tuple[int, dict[str, Any]]] = []
        for asset in assets:
            if asset["path"] in used:
                continue
            score = len(set(keywords) & set(asset["tokens"]))
            if score:
                scored.append((score, asset))
        scored.sort(key=lambda item: (-item[0], item[1]["path"]))
        if scored:
            chosen = scored[0][1]
            used.add(chosen["path"])
            cue = {
                "type": chosen["kind"], "source_type": "local_broll",
                "asset_path": chosen["path"], "rights_status": chosen["rights_status"],
                "at_seconds": round(at, 3), "duration_seconds": 2.4,
                "label": " ".join(keywords[:5]), "match_score": scored[0][0],
            }
        else:
            title = context[:70].strip() or "ประเด็นสำคัญ"
            cue = {
                "type": "motion_card", "source_type": "generated_local",
                "at_seconds": round(at, 3), "duration_seconds": 1.8,
                "label": title, "keywords": keywords[:6],
                "rights_status": "original_generated_graphic",
            }
        cues.append(cue)
        at += interval

    return {
        "version": "1.0", "mode": profile["key"], "cues": cues,
        "local_asset_count": len(assets),
        "copyright_policy": "Use only client-owned/editor-approved local media; otherwise render an original motion card.",
        "optional_free_sources": ["Wikimedia Commons", "NASA Image Library", "Pexels", "Pixabay"],
    }
