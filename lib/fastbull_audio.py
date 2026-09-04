"""Free local voice cleanup and delivery loudness normalization."""

from __future__ import annotations

import subprocess
from pathlib import Path


def normalize_voice(input_path: str | Path, output_path: str | Path) -> Path:
    source = Path(input_path)
    target = Path(output_path)
    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-i", str(source),
        "-map", "0:v:0", "-map", "0:a:0",
        "-c:v", "copy",
        "-af", "highpass=f=70,lowpass=f=16000,loudnorm=I=-16:LRA=11:TP=-1.5",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", str(target),
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0 or not target.is_file():
        raise RuntimeError((result.stderr or result.stdout or "FFmpeg voice normalization failed")[-1200:])
    return target
