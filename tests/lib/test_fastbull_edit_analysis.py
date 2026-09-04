from lib.fastbull_edit_analysis import analyze_transcript, build_keep_segments, merge_intervals, retime_transcript


def test_analysis_separates_safe_removals_from_review_flags():
    segments = [{"words": [
        {"word": "เอ่อ", "start": 0.0, "end": 0.3, "probability": 0.9},
        {"word": "ลงทุน", "start": 1.2, "end": 1.7, "probability": 0.4},
        {"word": "ลงทุน", "start": 1.8, "end": 2.2, "probability": 0.9},
    ]}]
    result = analyze_transcript(segments)
    types = {flag["type"] for flag in result["review_flags"]}
    assert {"isolated_filler", "pause", "low_confidence_word", "possible_repeat"} <= types
    assert result["safe_removal_candidates"] == [{"start": 0.0, "end": 0.3, "reason": "short_filler"}]


def test_keep_segments_and_retime_after_jump_cut():
    keep = build_keep_segments(5.0, [{"start": 1.0, "end": 3.0}])
    assert keep == [{"start": 0.0, "end": 1.0}, {"start": 3.0, "end": 5.0}]
    source = [{"words": [
        {"word": "หนึ่ง", "start": 0.2, "end": 0.8, "probability": 1},
        {"word": "สอง", "start": 3.2, "end": 3.8, "probability": 1},
    ]}]
    retimed = retime_transcript(source, keep)
    assert retimed[0]["words"][0]["start"] == 0.2
    assert retimed[1]["words"][0]["start"] == 1.2


def test_merge_intervals_handles_overlap():
    assert merge_intervals([
        {"start": 0, "end": 1, "reason": "a"},
        {"start": 0.9, "end": 2, "reason": "b"},
    ]) == [{"start": 0.0, "end": 2.0, "reason": "a+b"}]
