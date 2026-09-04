#!/usr/bin/env python3
"""One-command, local-first FASTBULL talking-head editor."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.fastbull_audio import normalize_voice
from lib.fastbull_edit_analysis import analyze_transcript, retime_transcript
from lib.fastbull_insert_planner import plan_inserts
from lib.fastbull_modes import get_mode_profile
from lib.fastbull_sfx import generate_fastbull_sfx
from lib.source_media_review import review_source_media
from tools.analysis.audio_probe import AudioProbe
from tools.analysis.frame_sampler import FrameSampler
from tools.analysis.transcriber import Transcriber
from tools.video.remotion_caption_burn import RemotionCaptionBurn
from tools.video.silence_cutter import SilenceCutter


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _natural_path_key(path: Path) -> tuple[tuple[int, int | str], ...]:
    parts = re.split(r"(\d+)", path.name)
    return tuple((0, int(part)) if part.isdigit() else (1, part.casefold()) for part in parts)


def _resolve_sources(args: argparse.Namespace) -> list[Path]:
    requested = list(args.input or [])
    if args.input_list:
        input_list = Path(args.input_list).expanduser().resolve()
        if not input_list.is_file():
            raise FileNotFoundError(f"ไม่พบรายการไฟล์: {input_list}")
        requested.extend(
            Path(line.strip())
            for line in input_list.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        )

    if not requested:
        raise ValueError("กรุณาเลือกไฟล์วิดีโออย่างน้อย 1 ไฟล์")

    resolved: list[Path] = []
    seen: set[Path] = set()
    for item in requested:
        path = Path(item).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"ไม่พบไฟล์: {path}")
        if path not in seen:
            resolved.append(path)
            seen.add(path)
    return sorted(resolved, key=_natural_path_key)


def _run_media_command(command: list[str], *, cwd: Path | None = None, label: str) -> None:
    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except OSError as error:
        raise RuntimeError(f"{label}: {error}") from error
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown FFmpeg error").strip()[-2000:]
        raise RuntimeError(f"{label}: {detail}")


def _has_audio_stream(source: Path) -> bool:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "a:0",
                "-show_entries", "stream=index", "-of", "csv=p=0", str(source),
            ],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError as error:
        raise RuntimeError(f"ตรวจเสียงของ {source.name} ไม่สำเร็จ: {error}") from error
    if result.returncode != 0:
        raise RuntimeError(f"ตรวจเสียงของ {source.name} ไม่สำเร็จ: {result.stderr.strip()}")
    return bool(result.stdout.strip())


def _join_sources(sources: list[Path], job_dir: Path) -> Path:
    if len(sources) == 1:
        return sources[0]

    parts_dir = job_dir / "joined_source_parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    normalized_parts: list[Path] = []
    video_filter = (
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30"
    )

    for index, source in enumerate(sources, start=1):
        print(f"  เตรียมไฟล์ {index}/{len(sources)}: {source.name}")
        part = parts_dir / f"part-{index:04d}.mp4"
        command = ["ffmpeg", "-y", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(source)]
        has_audio = _has_audio_stream(source)
        if not has_audio:
            command.extend(["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"])
        command.extend(["-map", "0:v:0", "-map", "0:a:0" if has_audio else "1:a:0"])
        if not has_audio:
            command.append("-shortest")
        command.extend([
            "-vf", video_filter,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", str(part),
        ])
        _run_media_command(command, label=f"เตรียมไฟล์ {source.name} ไม่สำเร็จ")
        normalized_parts.append(part)

    concat_list = parts_dir / "concat.txt"
    concat_list.write_text(
        "".join(f"file '{part.name}'\n" for part in normalized_parts),
        encoding="utf-8",
    )
    joined = job_dir / "00-source-joined.mp4"
    _run_media_command(
        [
            "ffmpeg", "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "1", "-i", concat_list.name,
            "-c", "copy", "-movflags", "+faststart", str(joined),
        ],
        cwd=parts_dir,
        label="รวมไฟล์วิดีโอไม่สำเร็จ",
    )
    return joined


def _version(command: list[str]) -> str | None:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=8,
                                encoding="utf-8", errors="replace")
        if result.returncode == 0:
            return (result.stdout or result.stderr).splitlines()[0].strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def doctor_report() -> dict[str, Any]:
    suffix = ".cmd" if os.name == "nt" else ""
    packages = {}
    for module in ("faster_whisper", "pythainlp", "cv2", "scenedetect", "pysubs2", "librosa"):
        try:
            importlib.import_module(module)
            packages[module] = True
        except Exception:
            packages[module] = False
    remotion = REPO_ROOT / "remotion-composer" / "node_modules" / ".bin" / f"remotion{suffix}"
    hyperframes = REPO_ROOT / "node_modules" / ".bin" / f"hyperframes{suffix}"
    chromium_candidates: list[Path] = [
        REPO_ROOT / ".runtime" / "hyperframes" / "chromium" / ("chrome.exe" if os.name == "nt" else "chromium"),
        REPO_ROOT / ".runtime" / "hyperframes" / "chromium" / "chromium.exe",
    ]
    if os.environ.get("HYPERFRAMES_BROWSER_PATH"):
        chromium_candidates.insert(0, Path(os.environ["HYPERFRAMES_BROWSER_PATH"]))
    if os.name == "nt":
        for base_name, relative in (
            ("PROGRAMFILES(X86)", "Microsoft/Edge/Application/msedge.exe"),
            ("PROGRAMFILES", "Google/Chrome/Application/chrome.exe"),
            ("LOCALAPPDATA", "Google/Chrome/Application/chrome.exe"),
        ):
            if os.environ.get(base_name):
                chromium_candidates.append(Path(os.environ[base_name]) / relative)
    checks = {
        "python_3_10_plus": sys.version_info >= (3, 10),
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "ffprobe": bool(shutil.which("ffprobe")),
        "node_22_plus": False,
        "remotion_local": remotion.is_file(),
        "hyperframes_local": hyperframes.is_file(),
        "chromium_local": any(path.is_file() for path in chromium_candidates),
        "thai_font": (REPO_ROOT / "assets" / "fonts" / "noto-sans-thai" / "NotoSansThai-Variable.ttf").is_file(),
        "python_packages": all(packages.values()),
    }
    node_version = _version(["node", "--version"])
    if node_version:
        match = re.search(r"(\d+)", node_version)
        checks["node_22_plus"] = bool(match and int(match.group(1)) >= 22)
    report = {
        "version": "1.0", "platform": platform.platform(), "python": sys.version.split()[0],
        "node": node_version, "ffmpeg_version": _version(["ffmpeg", "-version"]),
        "hyperframes_version": _version([str(hyperframes), "--version"]) if hyperframes.is_file() else None,
        "checks": checks, "package_checks": packages,
        "ready": all(checks.values()),
        "first_run_note": "Whisper speech model downloads once on first transcription, then runs locally.",
        "api_cost_baht": 0,
    }
    return report


class _LocalRegistry:
    def __init__(self) -> None:
        self.tools = {"audio_probe": AudioProbe(), "frame_sampler": FrameSampler()}

    def get(self, name: str):
        return self.tools.get(name)


def _load_transcript(args: argparse.Namespace, job_dir: Path, source: Path) -> dict[str, Any]:
    if args.transcript_json:
        print("[2/8] ใช้ transcript ที่มีเวลารายคำตามที่ระบุ...")
        supplied = _read_json(args.transcript_json)
        if isinstance(supplied, list):
            supplied = {"segments": supplied, "language": args.language}
        supplied.setdefault("language", args.language)
        supplied.setdefault("word_timestamp_normalization", "supplied")
        _write_json(job_dir / "transcript.json", supplied)
        return supplied

    print("[2/8] ถอดเสียงและจับเวลารายคำ...")
    result = Transcriber().execute({
        "input_path": str(source), "model_size": args.model,
        "language": args.language, "output_dir": str(job_dir),
    })
    if not result.success:
        raise RuntimeError(result.error or "Transcription failed")
    _write_json(job_dir / "transcript.json", result.data)
    return result.data


def _source_duration(review: dict[str, Any]) -> float:
    files = review.get("files") or []
    return sum(
        float(item.get("technical_probe", {}).get("duration_seconds", 0.0) or 0.0)
        for item in files
    )


def _quality_report(output: Path, expected_duration: float, caption_count: int) -> dict[str, Any]:
    probe_result = AudioProbe().execute({"input_path": str(output)})
    probe = probe_result.data if probe_result.success else {}
    video = probe.get("video") or {}
    audio = probe.get("audio") or {}
    duration = float(probe.get("duration_seconds", 0.0) or 0.0)
    checks = {
        "file_exists": output.is_file() and output.stat().st_size > 100_000,
        "vertical_1080x1920": video.get("width") == 1080 and video.get("height") == 1920,
        "h264_video": video.get("codec") == "h264",
        "audio_present": bool(audio.get("codec")),
        "duration_matches": abs(duration - expected_duration) <= 0.6,
        "captions_present": caption_count > 0,
    }
    return {
        "version": "1.0", "output": str(output), "probe": probe, "checks": checks,
        "technical_ready": all(checks.values()),
        "delivery_state": "technical_ready_manual_qc_required" if all(checks.values()) else "failed_technical_qc",
        "manual_checks": [
            "ฟังว่าจุดตัดไม่กินพยางค์ต้นหรือท้าย", "ตรวจคำสะกด ชื่อเฉพาะ ตัวเลข และคำเคลม",
            "ดูว่าซับไม่บังหน้าและปุ่มแพลตฟอร์ม", "ยืนยันสิทธิ์ของ B-roll ทุกไฟล์", "ดูคลิปเต็มหนึ่งรอบก่อนส่งลูกค้า",
        ],
    }


def run_job(args: argparse.Namespace, *, render: bool) -> Path:
    sources = _resolve_sources(args)
    profile = get_mode_profile(args.mode)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    source_label = sources[0].stem if len(sources) == 1 else f"{sources[0].stem}-multi-{len(sources)}"
    job_dir = Path(args.job_dir).expanduser().resolve() if args.job_dir else (
        Path.cwd() / "FASTBULL_OUTPUT" / f"{source_label}-{profile['key']}-{stamp}"
    )
    job_dir.mkdir(parents=True, exist_ok=True)
    _write_json(job_dir / "source_order.json", {
        "ordering": "natural_filename",
        "count": len(sources),
        "files": [str(path) for path in sources],
    })

    print("[1/8] ตรวจไฟล์ภาพ เสียง ความละเอียด และสุ่มเฟรม...")
    review = review_source_media(
        sources, {"transcribe": False, "review_output_dir": str(job_dir / "review_frames")}, _LocalRegistry()
    )
    _write_json(job_dir / "source_media_review.json", review)
    duration = _source_duration(review)
    if duration <= 0:
        raise RuntimeError("อ่านระยะเวลาคลิปไม่ได้")
    if len(sources) > 1:
        print(f"  รวมฟุต {len(sources)} ไฟล์ตามลำดับชื่อไฟล์...")
    source = _join_sources(sources, job_dir)
    if len(sources) > 1:
        joined_probe = AudioProbe().execute({"input_path": str(source)})
        if not joined_probe.success:
            raise RuntimeError(joined_probe.error or "ตรวจไฟล์ที่รวมแล้วไม่สำเร็จ")
        duration = float(joined_probe.data.get("duration_seconds", 0.0) or 0.0)
        if duration <= 0:
            raise RuntimeError("อ่านระยะเวลาฟุตที่รวมแล้วไม่ได้")

    transcript = _load_transcript(args, job_dir, source)
    segments = list(transcript.get("segments") or [])
    if not segments:
        raise RuntimeError("ไม่พบคำพูดในคลิป จึงยังสร้างซับอย่างปลอดภัยไม่ได้")

    corrections = _read_json(args.corrections_json) if args.corrections_json else {}
    print("[3/8] ตรวจคำไม่ชัด คำซ้ำ คำฟิลเลอร์ และช่วงเว้น...")
    edit_analysis = analyze_transcript(segments, exact_corrections=corrections)
    _write_json(job_dir / "edit_analysis.json", edit_analysis)

    print("[4/8] ตรวจและตัดช่วงเงียบตามโหมด...")
    keep_segments = [{"start": 0.0, "end": duration}]
    timeline_input = source
    mark_path = job_dir / "silence_map.json"
    if not args.keep_silence:
        cutter_inputs = {
            "input_path": str(source), "mode": "mark", "output_path": str(mark_path),
            "silence_threshold_db": profile["silence_threshold_db"],
            "min_silence_duration": profile["min_silence_duration"], "padding_seconds": 0.10,
        }
        mark = SilenceCutter().execute(cutter_inputs)
        if not mark.success:
            raise RuntimeError(mark.error or "Silence analysis failed")
        if mark_path.is_file():
            silence_map = _read_json(mark_path)
            keep_segments = silence_map.get("speech_segments") or keep_segments
            if silence_map.get("silences"):
                cut_path = job_dir / "01-jump-cut.mp4"
                cut = SilenceCutter().execute({**cutter_inputs, "mode": "remove", "output_path": str(cut_path)})
                if not cut.success:
                    raise RuntimeError(cut.error or "Silence cut failed")
                timeline_input = cut_path
        else:
            _write_json(mark_path, {"silences": [], "speech_segments": keep_segments, "total_duration": duration})
    else:
        _write_json(mark_path, {"silences": [], "speech_segments": keep_segments, "total_duration": duration, "skipped": True})

    retimed = retime_transcript(segments, keep_segments, language=transcript.get("language", args.language))
    edited_duration = sum(float(item["end"]) - float(item["start"]) for item in keep_segments)
    retimed_transcript = {**transcript, "segments": retimed, "duration_seconds": round(edited_duration, 3)}
    retimed_transcript["word_timestamps"] = [word for seg in retimed for word in seg.get("words", [])]
    _write_json(job_dir / "retimed_transcript.json", retimed_transcript)

    print("[5/8] ปรับเสียงพูดและความดังมาตรฐานโซเชียล...")
    normalized = job_dir / "02-voice-normalized.mp4"
    normalize_voice(timeline_input, normalized)

    print("[6/8] วาง Insert/B-roll และทางเลือกกราฟิกฟรี...")
    insert_plan = plan_inserts(retimed, duration_seconds=edited_duration, mode=profile["key"], broll_dirs=args.broll or [])
    _write_json(job_dir / "insert_plan.json", insert_plan)

    auto_headline = next((str(seg.get("text", "")).strip() for seg in retimed if str(seg.get("text", "")).strip()), "FASTBULL")[:52]
    headline = args.headline or auto_headline
    editorial_warnings = [] if args.headline else ["พาดหัวถูกดึงจากประโยคแรกอัตโนมัติ ควรให้บรรณาธิการยืนยันก่อนส่งลูกค้า"]
    manifest = {
        "version": "1.0", "source": str(source), "sources": [str(path) for path in sources],
        "source_joined": len(sources) > 1, "job_dir": str(job_dir), "mode": profile,
        "headline": headline, "page_name": args.page_name, "cta": args.cta or profile["cta"],
        "edit_analysis": str(job_dir / "edit_analysis.json"), "insert_plan": str(job_dir / "insert_plan.json"),
        "editorial_warnings": editorial_warnings,
        "cost": {"api_baht": 0, "note": "Local CPU/GPU, electricity and storage are not included."},
    }
    _write_json(job_dir / "job_manifest.json", manifest)

    if not render:
        print(f"วิเคราะห์เสร็จ: {job_dir}")
        return job_dir

    print("[7/8] เรนเดอร์ซับ พาดหัว Insert เอฟเฟกต์ และ CTA...")
    sfx_cues: list[dict[str, Any]] = []
    if not args.no_sfx:
        sfx = generate_fastbull_sfx(job_dir / "generated_sfx")
        sfx_cues.append({"path": sfx["impact"], "at_seconds": 0.0, "volume": 0.10})
        for cue in insert_plan["cues"][:4]:
            sfx_cues.append({"path": sfx["whoosh"], "at_seconds": cue["at_seconds"], "volume": 0.07})
        sfx_cues.append({"path": sfx["chime"], "at_seconds": max(0.0, edited_duration - 2.4), "volume": 0.09})

    output = Path(args.output).expanduser().resolve() if args.output else job_dir / "FASTBULL-FINAL.mp4"
    result = RemotionCaptionBurn().execute({
        "input_path": str(normalized), "output_path": str(output), "segments": retimed,
        "corrections": corrections, "style_preset": "fastbull_sport_luxury",
        "headline": headline, "eyebrow": args.eyebrow, "page_name": args.page_name,
        "cta": args.cta or profile["cta"], "language": transcript.get("language", args.language),
        "words_per_page": profile["words_per_page"], "sfx_cues": sfx_cues,
        "insert_cues": insert_plan["cues"], "force_ffmpeg": args.force_ffmpeg,
    })
    if not result.success:
        raise RuntimeError(result.error or "Final render failed")

    print("[8/8] ตรวจไฟล์ส่งออกอัตโนมัติ...")
    quality = _quality_report(output, edited_duration, len(retimed_transcript["word_timestamps"]))
    _write_json(job_dir / "quality_report.json", quality)
    if not quality["technical_ready"]:
        raise RuntimeError(f"ไฟล์เรนเดอร์ออกแล้วแต่ไม่ผ่าน Technical QC: {job_dir / 'quality_report.json'}")
    print(f"เสร็จ: {output}")
    print("สถานะ: ผ่าน Technical QC — กรุณาดูและฟังเต็มคลิปหนึ่งรอบก่อนส่งลูกค้า")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FASTBULL local-first automatic editor")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="ตรวจว่าเครื่องพร้อมตัดต่อหรือยัง")
    for command in ("analyze", "run"):
        cmd = sub.add_parser(command, help="วิเคราะห์อย่างเดียว" if command == "analyze" else "ตัดต่อและส่งออก")
        source_group = cmd.add_mutually_exclusive_group(required=True)
        source_group.add_argument("--input", action="append", type=Path, help="ไฟล์วิดีโอ; ใส่ซ้ำได้")
        source_group.add_argument("--input-list", type=Path, help="ไฟล์ข้อความที่มีที่อยู่วิดีโอทีละบรรทัด")
        cmd.add_argument("--mode", required=True, help="vlog, value/คุณค่า, awareness/รับรู้, sales/ขาย")
        cmd.add_argument("--headline")
        cmd.add_argument("--eyebrow", default="FASTBULL INSIGHT")
        cmd.add_argument("--page-name", default="FASTBULL")
        cmd.add_argument("--cta")
        cmd.add_argument("--language", default="th")
        cmd.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"])
        cmd.add_argument("--broll", action="append", help="โฟลเดอร์ B-roll; ใส่ซ้ำได้")
        cmd.add_argument("--transcript-json", help="ใช้ transcript ที่มี timestamps แทนการถอดใหม่")
        cmd.add_argument("--corrections-json", help="ไฟล์ JSON คำแก้ที่ยืนยันแล้ว")
        cmd.add_argument("--job-dir")
        cmd.add_argument("--keep-silence", action="store_true")
        cmd.add_argument("--no-sfx", action="store_true")
        cmd.add_argument("--force-ffmpeg", action="store_true", help="สำรองเท่านั้น; ไม่มีธีม premium")
        if command == "run":
            cmd.add_argument("--output")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "doctor":
            report = doctor_report()
            print(json.dumps(report, ensure_ascii=False, indent=2))
            print("พร้อมตัดต่อ" if report["ready"] else "ยังไม่พร้อม — รันสคริปต์ติดตั้งก่อน")
            return 0 if report["ready"] else 2
        run_job(args, render=args.command == "run")
        return 0
    except (FileNotFoundError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
