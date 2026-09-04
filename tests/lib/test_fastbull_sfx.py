import wave

from lib.fastbull_sfx import generate_fastbull_sfx


def test_generates_original_local_sfx(tmp_path):
    result = generate_fastbull_sfx(tmp_path)
    assert set(result) == {"whoosh", "tick", "impact", "chime"}
    for path in result.values():
        with wave.open(path, "rb") as audio:
            assert audio.getframerate() == 48000
            assert audio.getnframes() > 1000
