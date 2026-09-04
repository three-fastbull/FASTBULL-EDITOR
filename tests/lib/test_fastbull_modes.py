import pytest

from lib.fastbull_modes import get_mode_profile, normalize_mode


@pytest.mark.parametrize("alias,expected", [("VLOG", "vlog"), ("คุณค่า", "value"), ("สร้างการรับรู้", "awareness"), ("ขาย", "sales")])
def test_mode_aliases(alias, expected):
    assert normalize_mode(alias) == expected


def test_profiles_have_distinct_pacing_and_cta():
    profiles = [get_mode_profile(name) for name in ("vlog", "value", "awareness", "sales")]
    assert len({profile["min_silence_duration"] for profile in profiles}) == 4
    assert len({profile["cta"] for profile in profiles}) == 4


def test_profile_is_a_copy():
    first = get_mode_profile("value")
    first["cta"] = "changed"
    assert get_mode_profile("value")["cta"] != "changed"


def test_unknown_mode_is_clear():
    with pytest.raises(ValueError, match="Unknown edit mode"):
        normalize_mode("documentary")
