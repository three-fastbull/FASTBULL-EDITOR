import shutil
import subprocess

import pytest

from lib.fastbull_audio import normalize_voice


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg unavailable")
def test_normalize_voice_keeps_video_and_audio(tmp_path):
    source = tmp_path / "source.mp4"
    output = tmp_path / "normalized.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=navy:s=320x568:r=30:d=1",
        "-f", "lavfi", "-i", "sine=frequency=300:sample_rate=48000:duration=1",
        "-c:v", "libx264", "-c:a", "aac", "-shortest", str(source), "-loglevel", "error",
    ], check=True)
    normalize_voice(source, output)
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(output)
    ], capture_output=True, text=True, check=True)
    assert {"video", "audio"} <= set(probe.stdout.split())
