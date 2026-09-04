"""Transcription tool wrapping faster-whisper / WhisperX.

Provides speech-to-text with word-level timestamps and optional speaker
diarization. Falls back gracefully when GPU or diarization dependencies
are not available.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ResumeSupport,
    ToolResult,
    ToolStability,
    ToolStatus,
    ToolTier,
)


class Transcriber(BaseTool):
    name = "transcriber"
    version = "0.2.0"
    tier = ToolTier.CORE
    capability = "analysis"
    provider = "whisperx"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC

    dependencies = ["python:faster_whisper", "python:pythainlp"]
    install_instructions = (
        "pip install faster-whisper  # CPU mode\n"
        "pip install faster-whisper[gpu]  # GPU mode (requires CUDA)\n"
        "pip install whisperx  # For diarization support"
    )
    agent_skills = ["speech-to-text"]

    capabilities = [
        "transcribe",
        "word_timestamps",
        "diarization",
        "language_detection",
    ]

    input_schema = {
        "type": "object",
        "required": ["input_path"],
        "properties": {
            "input_path": {"type": "string", "description": "Path to audio or video file"},
            "model_size": {
                "type": "string",
                "enum": ["tiny", "base", "small", "medium", "large-v2", "large-v3"],
                "default": "base",
            },
            "language": {"type": "string", "description": "ISO 639-1 language code, or null for auto-detect"},
            "diarize": {"type": "boolean", "default": False},
            "output_dir": {"type": "string", "description": "Directory for output files"},
        },
    }

    output_schema = {
        "type": "object",
        "properties": {
            "segments": {"type": "array"},
            "word_timestamps": {"type": "array"},
            "language": {"type": "string"},
            "duration_seconds": {"type": "number"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=2,
        ram_mb=2048,
        vram_mb=0,  # CPU by default; GPU optional
        disk_mb=500,
        network_required=False,
    )

    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["MemoryError"])
    resume_support = ResumeSupport.FROM_START
    idempotency_key_fields = ["input_path", "model_size", "language"]
    side_effects = ["writes transcript JSON to output_dir"]
    fallback = None
    user_visible_verification = [
        "Check transcript text against source audio",
        "Verify word timestamps align with speech",
    ]

    def get_status(self) -> ToolStatus:
        try:
            import faster_whisper  # noqa: F401
            return ToolStatus.AVAILABLE
        except ImportError:
            return ToolStatus.UNAVAILABLE

    def _has_diarization(self) -> bool:
        try:
            import whisperx  # noqa: F401
            return True
        except ImportError:
            return False

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        """Rough estimate: ~0.5x real-time on CPU for 'base' model."""
        return 60.0  # conservative default

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        input_path = Path(inputs["input_path"])
        model_size = inputs.get("model_size", "base")
        language = inputs.get("language")
        diarize = inputs.get("diarize", False)
        output_dir = Path(inputs.get("output_dir", input_path.parent))

        if not input_path.exists():
            return ToolResult(success=False, error=f"Input file not found: {input_path}")

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return ToolResult(
                success=False,
                error="faster-whisper is not installed. Run: pip install faster-whisper",
            )

        start = time.time()

        # faster-whisper executes through CTranslate2, so that runtime—not
        # PyTorch—is authoritative for CUDA availability and compute types.
        device = "cpu"
        compute_type = "int8"
        try:
            import ctranslate2

            if ctranslate2.get_cuda_device_count() > 0:
                supported = ctranslate2.get_supported_compute_types("cuda")
                for candidate in ("float16", "int8_float16", "float32"):
                    if candidate in supported:
                        device = "cuda"
                        compute_type = candidate
                        break
        except Exception:
            # Probing is advisory. CPU remains a safe deterministic baseline.
            pass

        def _transcribe_on(selected_device: str, selected_compute_type: str):
            model = WhisperModel(
                model_size,
                device=selected_device,
                compute_type=selected_compute_type,
            )
            segments_iter, transcription_info = model.transcribe(
                str(input_path),
                language=language,
                word_timestamps=True,
                vad_filter=True,
            )

            parsed_segments = []
            parsed_words = []
            # faster-whisper evaluates lazily. Draining the iterator here keeps
            # missing CUDA runtime libraries inside the fallback boundary.
            for seg in segments_iter:
                seg_data = {
                    "id": seg.id,
                    "start": round(seg.start, 3),
                    "end": round(seg.end, 3),
                    "text": seg.text.strip(),
                }

                if seg.words:
                    words = []
                    for word in seg.words:
                        word_entry = {
                            "word": word.word,
                            "start": round(word.start, 3),
                            "end": round(word.end, 3),
                            "probability": round(word.probability, 3),
                        }
                        words.append(word_entry)
                        parsed_words.append(word_entry)
                    seg_data["words"] = words

                parsed_segments.append(seg_data)

            return parsed_segments, parsed_words, transcription_info

        gpu_fallback_reason = None
        try:
            segments, word_timestamps, info = _transcribe_on(device, compute_type)
        except Exception as exc:
            if device == "cpu":
                raise
            gpu_fallback_reason = f"{type(exc).__name__}: {exc}"
            device = "cpu"
            compute_type = "int8"
            segments, word_timestamps, info = _transcribe_on(device, compute_type)

        detected_language = language or info.language
        duration = info.duration

        thai_normalized = False
        if detected_language == "th":
            segments, word_timestamps, thai_normalized = (
                self._normalize_thai_word_timestamps(segments)
            )

        # Optional diarization pass
        if diarize and self._has_diarization():
            segments = self._apply_diarization(
                str(input_path), segments, detected_language
            )

        elapsed = time.time() - start

        result_data = {
            "segments": segments,
            "word_timestamps": word_timestamps,
            "language": detected_language,
            "duration_seconds": round(duration, 3),
            "model_size": model_size,
            "device": device,
            "compute_type": compute_type,
            "gpu_fallback_reason": gpu_fallback_reason,
            "word_timestamp_normalization": (
                "pythainlp" if thai_normalized else "whisper"
            ),
        }

        # Write transcript JSON
        output_path = output_dir / f"{input_path.stem}_transcript.json"
        output_path.write_text(json.dumps(result_data, indent=2), encoding="utf-8")

        return ToolResult(
            success=True,
            data=result_data,
            artifacts=[str(output_path)],
            duration_seconds=round(elapsed, 2),
        )

    @staticmethod
    def _normalize_thai_word_timestamps(
        segments: list[dict],
    ) -> tuple[list[dict], list[dict], bool]:
        """Merge Whisper's Thai character timestamps into real Thai words.

        Whisper frequently emits one timestamp per Thai codepoint. PyThaiNLP
        supplies word boundaries; timings remain anchored to the first and
        last Whisper item that overlap each token, so karaoke highlighting is
        useful without inventing timing data.
        """
        try:
            from pythainlp.tokenize import word_tokenize
        except ImportError:
            words = [w for seg in segments for w in seg.get("words", [])]
            return segments, words, False

        changed = False
        rebuilt_words: list[dict] = []
        rebuilt_segments: list[dict] = []

        for original in segments:
            seg = dict(original)
            raw_words = list(original.get("words") or [])
            if not raw_words:
                rebuilt_segments.append(seg)
                continue

            pieces: list[str] = []
            spans: list[tuple[int, int, dict]] = []
            cursor = 0
            for raw in raw_words:
                piece = "".join(str(raw.get("word", "")).split())
                if not piece:
                    continue
                pieces.append(piece)
                spans.append((cursor, cursor + len(piece), raw))
                cursor += len(piece)

            source = "".join(pieces)
            text = str(seg.get("text") or source)
            tokens = [
                "".join(token.split())
                for token in word_tokenize(text, engine="newmm", keep_whitespace=False)
                if "".join(token.split())
            ]
            if not source or "".join(tokens) != source:
                rebuilt_segments.append(seg)
                rebuilt_words.extend(raw_words)
                continue

            merged: list[dict] = []
            token_start = 0
            for token in tokens:
                token_end = token_start + len(token)
                overlaps = [raw for start, end, raw in spans if start < token_end and end > token_start]
                if not overlaps:
                    token_start = token_end
                    continue
                probabilities = [float(w.get("probability", 0.0)) for w in overlaps]
                merged.append(
                    {
                        "word": token,
                        "start": round(float(overlaps[0]["start"]), 3),
                        "end": round(float(overlaps[-1]["end"]), 3),
                        "probability": round(sum(probabilities) / len(probabilities), 3),
                    }
                )
                token_start = token_end

            if merged:
                changed = changed or len(merged) != len(raw_words) or any(
                    a.get("word") != b.get("word") for a, b in zip(merged, raw_words)
                )
                seg["words"] = merged
                rebuilt_words.extend(merged)
            else:
                rebuilt_words.extend(raw_words)
            rebuilt_segments.append(seg)

        return rebuilt_segments, rebuilt_words, changed

    def _apply_diarization(
        self,
        audio_path: str,
        segments: list[dict],
        language: str,
    ) -> list[dict]:
        """Apply WhisperX diarization to assign speaker labels."""
        try:
            import whisperx

            # Load audio for alignment
            audio = whisperx.load_audio(audio_path)

            # Align segments with word timestamps
            align_model, align_metadata = whisperx.load_align_model(
                language_code=language, device="cpu"
            )
            aligned = whisperx.align(
                segments, align_model, align_metadata, audio, device="cpu"
            )

            # Diarize
            import os
            hf_token = os.environ.get("HF_TOKEN")
            if not hf_token:
                # Can't diarize without HuggingFace token for pyannote
                return segments

            diarize_model = whisperx.DiarizationPipeline(
                use_auth_token=hf_token, device="cpu"
            )
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, aligned)

            return result.get("segments", segments)
        except Exception:
            # Diarization is best-effort; return original segments on failure
            return segments
