"""Tests for Phase 1 Media Deep Seams in ccba-pdf-prep."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from ccba_pdf_prep import (
    compute_frame_hash,
    dedup_frames,
    extract_storyboard_frames,
    extract_youtube_video_id,
    find_ffmpeg_bin,
    format_lesson_notes,
    format_whisper_transcript,
    get_heatmap_peaks,
    get_target_timestamps,
    group_transcript_segments,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_extract_youtube_video_id_patterns():
    """Verify robust YouTube video ID extraction across supported URL patterns."""
    expected = "dQw4w9WgXcQ"

    patterns = [
        f"https://www.youtube.com/watch?v={expected}",
        f"http://www.youtube.com/watch?v={expected}&feature=related",
        f"https://youtu.be/{expected}",
        f"https://www.youtube.com/embed/{expected}",
        f"https://www.youtube.com/v/{expected}",
        f"https://www.youtube.com/live/{expected}",
        expected,
    ]

    for url in patterns:
        extracted = extract_youtube_video_id(url)
        assert extracted == expected, f"Failed for pattern: {url}"

    assert extract_youtube_video_id("https://invalid.com/video") is None
    assert extract_youtube_video_id("") is None
    assert extract_youtube_video_id("short") is None


def test_format_whisper_transcript():
    """Test paragraphing continuous sentences."""
    sentences = " ".join([f"Sentence number {i}." for i in range(12)])
    formatted = format_whisper_transcript(sentences)

    paragraphs = formatted.split("\n\n")
    assert len(paragraphs) == 3
    assert paragraphs[0].count(".") == 5
    assert paragraphs[1].count(".") == 5
    assert paragraphs[2].count(".") == 2

    assert format_whisper_transcript("") == ""


def test_group_transcript_segments():
    """Test grouping transcript segments into timestamped 30-second blocks."""
    segments = [
        {"start": 0.0, "text": "Welcome to the lecture."},
        {"start": 10.5, "text": "Today we discuss BIM governance."},
        {"start": 32.0, "text": "In phase 2 we review regulations."},
        {"start": 65.0, "text": "Finally, we conclude."},
    ]

    res = group_transcript_segments(segments, interval_seconds=30.0)
    lines = res.split("\n\n")
    assert len(lines) == 3
    assert lines[0].startswith("[00:00]")
    assert "Welcome to the lecture" in lines[0]
    assert "Today we discuss" in lines[0]
    assert lines[1].startswith("[00:32]")
    assert lines[2].startswith("[01:05]")


def test_compute_frame_hash_and_dedup():
    """Test perceptual hash computation and frame deduplication."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)

        # Create two identical white images
        img1_path = dir_path / "img1.png"
        img2_path = dir_path / "img2.png"
        img1 = Image.new("RGB", (64, 64), color="white")
        img1.save(img1_path)
        img2 = Image.new("RGB", (64, 64), color="white")
        img2.save(img2_path)

        # Create a contrasting image (half black, half white)
        img3_path = dir_path / "img3.png"
        img3 = Image.new("RGB", (64, 64), color="black")
        for x in range(32):
            for y in range(64):
                img3.putpixel((x, y), (255, 255, 255))
        img3.save(img3_path)

        hash1 = compute_frame_hash(img1_path)
        hash2 = compute_frame_hash(img2_path)
        hash3 = compute_frame_hash(img3_path)

        assert hash1 == hash2
        assert hash1 != hash3

        # Deduplicate [img1, img2, img3] -> should drop img2
        deduped = dedup_frames([img1_path, img2_path, img3_path])
        assert len(deduped) == 2
        assert img1_path in deduped
        assert img3_path in deduped
        assert img2_path not in deduped


def test_find_ffmpeg_bin():
    """Test find_ffmpeg_bin returns string or None."""
    with patch("shutil.which", return_value="/opt/bin/ffmpeg"):
        bin_path = find_ffmpeg_bin()
        assert bin_path == "/opt/bin/ffmpeg"


def test_format_lesson_notes():
    """Test generating structured lesson notes markdown."""
    notes = format_lesson_notes(
        transcript="[00:00] Sample lecture transcript text.",
        image_files=["slide_01.webp", "slide_02.webp"],
        images_subfolder="lecture_images",
    )

    assert "# TÀI LIỆU BÀI GIẢNG & TỔNG HỢP KIẾN THỨC" in notes
    assert "![slide_01.webp](./lecture_images/slide_01.webp)" in notes
    assert "![slide_02.webp](./lecture_images/slide_02.webp)" in notes
    assert "[00:00] Sample lecture transcript text." in notes


def test_get_heatmap_peaks():
    """Test extracting top heatmap engagement peaks with minimum gap."""
    heatmap = [
        {"start_time": 0.0, "end_time": 10.0, "value": 0.2},
        {"start_time": 10.0, "end_time": 20.0, "value": 0.9},
        {"start_time": 20.0, "end_time": 30.0, "value": 0.85},  # within 15s of 15.0 -> dropped
        {"start_time": 100.0, "end_time": 110.0, "value": 0.95},
    ]
    peaks = get_heatmap_peaks(heatmap, duration_sec=200.0, max_peaks=5, min_gap_sec=15.0)
    assert len(peaks) == 2
    assert 105.0 in peaks
    assert 15.0 in peaks
    assert get_heatmap_peaks([], 100.0) == []


def test_get_target_timestamps_with_chapters():
    """Test target timestamp generation with chapter metadata."""
    chapters = [
        {"start_time": 0.0, "end_time": 100.0},
        {"start_time": 100.0, "end_time": 200.0},
    ]
    ts = get_target_timestamps(duration_sec=200.0, chapters=chapters)
    assert len(ts) > 0
    assert all(0.0 <= t <= 200.0 for t in ts)
    for i in range(1, len(ts)):
        assert ts[i] - ts[i - 1] >= 3.0


def test_get_target_timestamps_fallback():
    """Test fallback when no chapters provided."""
    ts = get_target_timestamps(duration_sec=100.0)
    assert len(ts) == 25
    assert all(0.0 <= t <= 100.0 for t in ts)


def test_extract_storyboard_frames_tile_math():
    """Test storyboard grid tiling and frame cropping math."""
    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_path = Path(temp_dir)
        grid_img = Image.new("RGB", (90, 90), color="blue")
        grid_file = tmp_path / "source_grid.jpg"
        grid_img.save(grid_file)

        sb_spec = {
            "rows": 3,
            "columns": 3,
            "fragment_duration": 90.0,
            "fragments": [{"url": "http://mock.cdn/grid_0.jpg", "duration": 90.0}],
        }

        def mock_download(url, dest_path, **kwargs):
            import shutil

            shutil.copyfile(grid_file, dest_path)
            return True

        with patch("ccba_pdf_prep.media.download_grid_image", side_effect=mock_download):
            frames = extract_storyboard_frames(
                sb_spec=sb_spec,
                tmp_dir=tmp_path,
                target_timestamps=[5.0, 15.0, 45.0],
                duration_sec=90.0,
            )
            assert len(frames) == 3
            for f in frames:
                assert f.exists()
                with Image.open(f) as img:
                    assert img.size == (30, 30)

