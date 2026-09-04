"""Editing-mode presets for the FASTBULL one-command editor."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


MODE_ALIASES = {
    "vlog": "vlog", "วีล็อก": "vlog", "ชีวิต": "vlog",
    "value": "value", "คุณค่า": "value", "ความรู้": "value",
    "awareness": "awareness", "รับรู้": "awareness", "สร้างการรับรู้": "awareness",
    "sales": "sales", "sale": "sales", "ขาย": "sales",
}

MODE_PROFILES: dict[str, dict[str, Any]] = {
    "vlog": {
        "label_th": "VLOG", "hook_seconds": 2.5, "silence_threshold_db": -36,
        "min_silence_duration": 0.8, "words_per_page": 5, "insert_interval_seconds": 8,
        "sfx_density": "light", "structure": ["เปิดด้วยเหตุการณ์", "พาไปด้วยกัน", "ข้อคิด", "ชวนติดตาม"],
        "cta": "ติดตามเพื่อดูตอนต่อไป", "editorial_rule": "เก็บลมหายใจและความเป็นธรรมชาติ",
    },
    "value": {
        "label_th": "คลิปสั้นเน้นคุณค่า", "hook_seconds": 1.8, "silence_threshold_db": -35,
        "min_silence_duration": 0.55, "words_per_page": 4, "insert_interval_seconds": 5,
        "sfx_density": "medium", "structure": ["ปัญหา", "คำตอบ", "ตัวอย่าง", "สรุปนำไปใช้"],
        "cta": "บันทึกคลิปนี้ไว้ใช้", "editorial_rule": "ตัดกระชับแต่ห้ามตัดเหตุผลสำคัญ",
    },
    "awareness": {
        "label_th": "สร้างการรับรู้", "hook_seconds": 2.0, "silence_threshold_db": -35,
        "min_silence_duration": 0.65, "words_per_page": 4, "insert_interval_seconds": 6,
        "sfx_density": "light", "structure": ["ความเชื่อเดิม", "มุมมองใหม่", "เรื่องของแบรนด์", "จำชื่อเพจ"],
        "cta": "ติดตาม FASTBULL", "editorial_rule": "ให้แบรนด์เด่นโดยไม่ขายตรงเกินไป",
    },
    "sales": {
        "label_th": "คลิปขาย", "hook_seconds": 1.5, "silence_threshold_db": -34,
        "min_silence_duration": 0.45, "words_per_page": 3, "insert_interval_seconds": 4,
        "sfx_density": "medium", "structure": ["ปัญหา", "ผลลัพธ์", "หลักฐาน", "ข้อเสนอ", "คำสั่งซื้อ"],
        "cta": "ส่งข้อความเพื่อรับรายละเอียด", "editorial_rule": "ข้อเสนอและ CTA ต้องชัด ห้ามแต่งคำเคลม",
    },
}


def normalize_mode(mode: str) -> str:
    normalized = MODE_ALIASES.get(mode.strip().lower())
    if normalized is None:
        choices = ", ".join(MODE_PROFILES)
        raise ValueError(f"Unknown edit mode {mode!r}. Choose: {choices}")
    return normalized


def get_mode_profile(mode: str) -> dict[str, Any]:
    key = normalize_mode(mode)
    profile = deepcopy(MODE_PROFILES[key])
    profile["key"] = key
    return profile
