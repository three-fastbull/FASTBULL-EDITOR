from lib.fastbull_insert_planner import index_broll, plan_inserts


def test_matches_local_broll_by_content(tmp_path):
    clip = tmp_path / "ลงทุน_เงิน.mp4"
    clip.write_bytes(b"placeholder")
    assets = index_broll([tmp_path])
    assert assets[0]["kind"] == "video"
    segments = [{"start": 0, "end": 20, "text": "วางแผนลงทุนและจัดการเงินให้ดี"}]
    result = plan_inserts(segments, duration_seconds=15, mode="value", broll_dirs=[tmp_path])
    assert result["cues"][0]["source_type"] == "local_broll"
    assert result["cues"][0]["asset_path"] == str(clip.resolve())


def test_falls_back_to_original_motion_card_without_broll():
    segments = [{"start": 0, "end": 20, "text": "สร้างเวลาให้ครอบครัว"}]
    result = plan_inserts(segments, duration_seconds=15, mode="awareness")
    assert result["cues"]
    assert all(cue["type"] == "motion_card" for cue in result["cues"])
    assert all(cue["rights_status"] == "original_generated_graphic" for cue in result["cues"])


def test_short_clip_does_not_force_insert():
    assert plan_inserts([], duration_seconds=4, mode="vlog")["cues"] == []
