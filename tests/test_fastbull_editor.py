import importlib.util
from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "fastbull_editor.py"
SPEC = importlib.util.spec_from_file_location("fastbull_editor", MODULE_PATH)
assert SPEC and SPEC.loader
fastbull_editor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fastbull_editor)


def test_doctor_report_has_actionable_checks():
    report = fastbull_editor.doctor_report()
    assert report["api_cost_baht"] == 0
    assert set(report["checks"]) >= {
        "python_3_10_plus", "ffmpeg", "ffprobe", "node_22_plus",
        "remotion_local", "hyperframes_local", "chromium_local", "thai_font",
    }
    assert report["ready"] == all(report["checks"].values())


def test_cli_requires_a_mode_for_run():
    parser = fastbull_editor.build_parser()
    args = parser.parse_args(["run", "--input", "clip.mp4", "--mode", "คุณค่า"])
    assert args.mode == "คุณค่า"
    assert args.input == [Path("clip.mp4")]


def test_cli_accepts_multiple_input_files():
    parser = fastbull_editor.build_parser()
    args = parser.parse_args([
        "run", "--input", "clip10.mp4", "--input", "clip2.mp4", "--mode", "vlog",
    ])
    assert args.input == [Path("clip10.mp4"), Path("clip2.mp4")]


def test_resolve_sources_uses_natural_filename_order(tmp_path):
    clip10 = tmp_path / "clip10.mp4"
    clip2 = tmp_path / "clip2.mp4"
    clip10.touch()
    clip2.touch()
    args = SimpleNamespace(input=[clip10, clip2], input_list=None)

    sources = fastbull_editor._resolve_sources(args)

    assert [path.name for path in sources] == ["clip2.mp4", "clip10.mp4"]


def test_resolve_sources_reads_windows_utf8_input_list(tmp_path):
    first = tmp_path / "01.mp4"
    second = tmp_path / "02.mp4"
    first.touch()
    second.touch()
    input_list = tmp_path / "selected.txt"
    input_list.write_text(f"{second}\n{first}\n", encoding="utf-8-sig")
    args = SimpleNamespace(input=None, input_list=input_list)

    sources = fastbull_editor._resolve_sources(args)

    assert sources == [first.resolve(), second.resolve()]


def test_source_duration_sums_all_reviewed_files():
    review = {
        "files": [
            {"technical_probe": {"duration_seconds": 3.25}},
            {"technical_probe": {"duration_seconds": 4.75}},
        ]
    }
    assert fastbull_editor._source_duration(review) == 8.0
