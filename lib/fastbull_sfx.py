"""Generate small, original FASTBULL sound effects locally (no licensing cost)."""

from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np


def _write_wav(path: Path, samples: np.ndarray, sample_rate: int = 48000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    peak = max(float(np.max(np.abs(samples))), 1e-9)
    pcm = np.int16(np.clip(samples / peak * 0.72, -1, 1) * 32767)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def generate_fastbull_sfx(output_dir: str | Path, sample_rate: int = 48000) -> dict[str, str]:
    """Create deterministic whoosh, tick, impact and chime WAV files."""
    output = Path(output_dir)
    rng = np.random.default_rng(240315)
    results: dict[str, str] = {}

    duration = 0.42
    t = np.arange(int(sample_rate * duration)) / sample_rate
    whoosh = rng.normal(0, 1, len(t)) * np.sin(np.pi * np.minimum(t / duration, 1)) ** 2
    whoosh *= np.linspace(0.2, 1.0, len(t))
    whoosh_path = output / "fastbull-whoosh.wav"
    _write_wav(whoosh_path, whoosh, sample_rate)
    results["whoosh"] = str(whoosh_path)

    t = np.arange(int(sample_rate * 0.10)) / sample_rate
    tick = np.sin(2 * math.pi * 1800 * t) * np.exp(-t * 48)
    tick_path = output / "fastbull-tick.wav"
    _write_wav(tick_path, tick, sample_rate)
    results["tick"] = str(tick_path)

    t = np.arange(int(sample_rate * 0.32)) / sample_rate
    impact = (np.sin(2 * math.pi * 82 * t) + 0.35 * rng.normal(size=len(t))) * np.exp(-t * 13)
    impact_path = output / "fastbull-impact.wav"
    _write_wav(impact_path, impact, sample_rate)
    results["impact"] = str(impact_path)

    t = np.arange(int(sample_rate * 0.8)) / sample_rate
    chime = (np.sin(2 * math.pi * 659.25 * t) + 0.65 * np.sin(2 * math.pi * 987.77 * t)) * np.exp(-t * 4.8)
    chime_path = output / "fastbull-chime.wav"
    _write_wav(chime_path, chime, sample_rate)
    results["chime"] = str(chime_path)
    return results
