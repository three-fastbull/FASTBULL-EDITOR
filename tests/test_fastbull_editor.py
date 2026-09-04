import importlib.util
from pathlib import Path


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
