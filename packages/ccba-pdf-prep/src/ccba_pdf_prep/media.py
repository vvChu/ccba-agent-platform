"""Media processing engine: YouTube transcript extraction, video frame extraction, and perceptual hash deduplication.

Provides deterministic tools for:
- Parsing YouTube video IDs from multiple URL formats.
- Formatting and paragraphing speech-to-text transcripts with timestamp markers.
- Extracting frames from video files via FFmpeg with perceptual hash (pHash) deduplication.
- Formatting educational lesson notes with linked slide frames.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

_logger = logging.getLogger("ccba_pdf_prep.media")

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None  # type: ignore[assignment]


def extract_youtube_video_id(url: str) -> str | None:
    """Extract YouTube 11-character video ID from various URL formats.

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - https://www.youtube.com/live/VIDEO_ID
    - Raw VIDEO_ID string

    Args:
        url: Full URL or raw video ID.

    Returns:
        11-character video ID or None if not recognized.
    """
    clean_url = url.strip()
    if re.match(r"^[a-zA-Z0-9_-]{11}$", clean_url):
        return clean_url

    parsed = urllib.parse.urlparse(clean_url)
    if parsed.hostname in ("youtu.be", "www.youtu.be"):
        vid = parsed.path.strip("/")
        return vid if len(vid) == 11 else None

    if parsed.hostname in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            qs = urllib.parse.parse_qs(parsed.query)
            vids = qs.get("v", [])
            if vids and len(vids[0]) == 11:
                return vids[0]
        for prefix in ("/embed/", "/v/", "/live/"):
            if parsed.path.startswith(prefix):
                parts = parsed.path.split("/")
                if len(parts) > 2 and len(parts[2]) == 11:
                    return parts[2]

    return None


def format_whisper_transcript(raw_text: str) -> str:
    """Divide raw unpunctuated or continuous speech transcript into readable 5-sentence paragraphs.

    Args:
        raw_text: Continuous raw transcript string.

    Returns:
        Formatted multi-paragraph text string.
    """
    if not raw_text or not raw_text.strip():
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", raw_text.strip())
    paragraphs: list[str] = []
    for i in range(0, len(sentences), 5):
        chunk = " ".join(sentences[i : i + 5]).strip()
        if chunk:
            paragraphs.append(chunk)
    return "\n\n".join(paragraphs)


def group_transcript_segments(
    segments: list[dict[str, Any]],
    interval_seconds: float = 30.0,
) -> str:
    """Group subtitle transcript segments into interval blocks with timestamp headers [MM:SS].

    Args:
        segments: List of segment dicts with 'text' and 'start' (float seconds).
        interval_seconds: Window size in seconds for grouping (default: 30.0).

    Returns:
        Timestamped formatted transcript string.
    """
    if not segments:
        return ""

    formatted_lines: list[str] = []
    current_group_start: float | None = None
    current_group_texts: list[str] = []

    for seg in segments:
        text = str(seg.get("text", "")).strip()
        if not text:
            continue
        start = float(seg.get("start", 0.0))

        if current_group_start is None:
            current_group_start = start
            current_group_texts.append(text)
        elif start - current_group_start >= interval_seconds:
            minutes = int(current_group_start // 60)
            seconds = int(current_group_start % 60)
            time_str = f"[{minutes:02d}:{seconds:02d}]"
            formatted_lines.append(f"{time_str} " + " ".join(current_group_texts))
            current_group_start = start
            current_group_texts = [text]
        else:
            current_group_texts.append(text)

    if current_group_texts and current_group_start is not None:
        minutes = int(current_group_start // 60)
        seconds = int(current_group_start % 60)
        time_str = f"[{minutes:02d}:{seconds:02d}]"
        formatted_lines.append(f"{time_str} " + " ".join(current_group_texts))

    return "\n\n".join(formatted_lines)


def fetch_youtube_transcript(url: str, output_dir: Path | str | None = None) -> str:
    """Fetch transcripts from YouTube using youtube_transcript_api if available.

    Args:
        url: YouTube video URL or ID.
        output_dir: Optional directory for saving cached transcript text.

    Returns:
        Formatted transcript text.
    """
    video_id = extract_youtube_video_id(url)
    if not video_id:
        return ""

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        try:
            transcript = transcript_list.find_transcript(["vi", "en"])
        except Exception:
            codes = [t.language_code for t in transcript_list]
            if not codes:
                return ""
            transcript = transcript_list.find_transcript(codes)

        data = transcript.fetch()
        segments = []
        for s in data:
            if isinstance(s, dict):
                val_text = str(s.get("text", ""))
                val_start = float(s.get("start", 0.0))
            else:
                val_text = str(getattr(s, "text", ""))
                val_start = float(getattr(s, "start", 0.0))
            segments.append({"text": val_text, "start": val_start})

        res = group_transcript_segments(segments)
        if output_dir:
            out_p = Path(output_dir) / f"{video_id}_transcript.txt"
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(res, encoding="utf-8")
        return res
    except Exception as exc:
        _logger.warning(f"YouTube transcript extraction failed: {exc}")
        return ""


def compute_frame_hash(img_path: Path | str, size: int = 8) -> int | None:
    """Compute 64-bit average perceptual hash using pure PIL without external dependencies.

    Args:
        img_path: Path to image file.
        size: Dimension of resized grayscale image (default: 8 for 64-bit hash).

    Returns:
        Integer representing perceptual hash, or None if image cannot be read.
    """
    if PILImage is None:
        return None
    try:
        img = (
            PILImage.open(str(img_path))
            .convert("L")
            .resize((size, size), PILImage.Resampling.LANCZOS)
        )
        pixels = list(img.tobytes())
        if not pixels:
            return None
        avg = sum(pixels) / len(pixels)
        return sum(1 << i for i, px in enumerate(pixels) if px >= avg)
    except Exception:
        return None


def dedup_frames(frames: list[Path], threshold: int = 2) -> list[Path]:
    """Deduplicate near-identical video frames using pairwise perceptual hash Hamming distance.

    Args:
        frames: List of image file Paths.
        threshold: Maximum Hamming bit distance to consider two frames identical (default: 2).

    Returns:
        List of filtered unique frame Paths.
    """
    if len(frames) <= 1 or PILImage is None:
        return frames

    unique: list[Path] = []
    hashes: list[int] = []

    for f in frames:
        if not f.exists():
            continue
        curr_hash = compute_frame_hash(f)
        if curr_hash is None:
            unique.append(f)
            continue

        is_dup = False
        for h in hashes:
            dist = bin(curr_hash ^ h).count("1")
            if dist < threshold:
                is_dup = True
                break

        if not is_dup:
            unique.append(f)
            hashes.append(curr_hash)

    return unique


def find_ffmpeg_bin() -> str | None:
    """Find FFmpeg executable on system PATH or default Windows installation directories."""
    bin_path = shutil.which("ffmpeg")
    if bin_path:
        return bin_path

    fallbacks = [
        Path(r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"),
        Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
    ]
    for fb in fallbacks:
        if fb.exists():
            return str(fb)
    return None


def extract_video_frames(
    video_path: Path | str,
    output_dir: Path | str,
    fps: float = 0.2,
) -> list[Path]:
    """Extract frames from local video file using FFmpeg, sorted by timestamp.

    Args:
        video_path: Path to input MP4/MKV/WebM video file.
        output_dir: Directory where extracted JPEG frames will be saved.
        fps: Sampling rate in frames per second (e.g. 0.2 = 1 frame every 5 seconds).

    Returns:
        List of extracted and deduplicated frame Paths.
    """
    v_path = Path(video_path)
    out_dir = Path(output_dir)
    if not v_path.exists():
        raise FileNotFoundError(f"Video not found: {v_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_bin = find_ffmpeg_bin()
    if not ffmpeg_bin:
        _logger.warning("FFmpeg binary not found on system.")
        return []

    pattern = str(out_dir / "frame_%04d.jpg")
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i",
        str(v_path),
        "-vf",
        f"fps={fps}",
        "-q:v",
        "2",
        pattern,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except Exception as exc:
        _logger.error(f"FFmpeg frame extraction failed: {exc}")
        return []

    raw_frames = sorted(out_dir.glob("frame_*.jpg"))
    return dedup_frames(raw_frames)


def format_lesson_notes(
    transcript: str,
    image_files: list[str],
    images_subfolder: str = "images",
) -> str:
    """Format transcript text and associate slide images into clean Markdown lesson notes.

    Args:
        transcript: Subtitle transcript text.
        image_files: List of slide frame image filenames.
        images_subfolder: Relative folder where images are stored.

    Returns:
        Markdown structured document.
    """
    lines: list[str] = [
        "# TÀI LIỆU BÀI GIẢNG & TỔNG HỢP KIẾN THỨC",
        "",
        "## 1. Danh sách Hình ảnh & Slide Trích xuất",
        "",
    ]
    for img_name in image_files:
        lines.append(f"- ![{img_name}](./{images_subfolder}/{img_name})")

    lines.extend(
        [
            "",
            "## 2. Toàn văn Phụ đề Bài giảng",
            "",
            transcript,
        ]
    )
    return "\n".join(lines)


def get_heatmap_peaks(
    heatmap: list[dict[str, Any]],
    duration_sec: float,
    max_peaks: int = 10,
    min_gap_sec: float = 15.0,
) -> list[float]:
    """Parse YouTube heatmap data and find timestamps of highest user engagement.

    Args:
        heatmap: List of heatmap entry dicts containing 'start_time', 'end_time', and 'value'.
        duration_sec: Total duration of video in seconds.
        max_peaks: Maximum number of peak timestamps to return (default: 10).
        min_gap_sec: Minimum distance in seconds between consecutive peaks (default: 15.0).

    Returns:
        Sorted list of peak timestamps in seconds.
    """
    if not heatmap:
        return []

    valid_entries: list[tuple[float, float]] = []
    for entry in heatmap:
        start = float(entry.get("start_time", 0.0))
        end = float(entry.get("end_time", 0.0))
        val = entry.get("value")
        if val is not None:
            mid = start + (end - start) / 2.0
            if 0.0 <= mid <= duration_sec:
                valid_entries.append((float(val), mid))

    valid_entries.sort(key=lambda x: x[0], reverse=True)

    peaks: list[float] = []
    for _val, ts in valid_entries:
        if not any(abs(ts - p) < min_gap_sec for p in peaks):
            peaks.append(ts)
            if len(peaks) >= max_peaks:
                break

    return sorted(peaks)


def get_target_timestamps(
    duration_sec: float,
    chapters: list[dict[str, Any]] | None = None,
    heatmap: list[dict[str, Any]] | None = None,
) -> list[float]:
    """Calculate adaptive target timestamps for chapter-aware multi-sampling.

    Args:
        duration_sec: Video duration in seconds.
        chapters: Optional list of chapter dicts with 'start_time' and 'end_time'.
        heatmap: Optional YouTube engagement heatmap data.

    Returns:
        Sorted list of target timestamps in seconds with minimal 3s gap.
    """
    timestamps: list[float] = []
    if chapters:
        num_chapters = len(chapters)
        if num_chapters <= 3:
            p_factors = [0.15, 0.35, 0.55, 0.75, 0.95]
        elif num_chapters <= 6:
            p_factors = [0.20, 0.40, 0.60, 0.80, 0.95]
        elif num_chapters <= 12:
            p_factors = [0.25, 0.50, 0.75, 0.95]
        else:
            p_factors = [0.33, 0.66, 0.95]

        for ch in chapters:
            start = float(ch.get("start_time", 0.0))
            end = float(ch.get("end_time", duration_sec))
            if start < 0.0:
                start = 0.0
            if end > duration_sec:
                end = duration_sec
            if end <= start:
                continue

            for p in p_factors:
                ts = start + (end - start) * p
                if 0.0 <= ts <= duration_sec:
                    timestamps.append(ts)
    else:
        # Fallback: dense coarse sampling
        n_points = 25
        step = duration_sec / (n_points + 1)
        for i in range(1, n_points + 1):
            ts = i * step
            if 0.0 <= ts <= duration_sec:
                timestamps.append(ts)

    if heatmap:
        peaks = get_heatmap_peaks(heatmap, duration_sec)
        timestamps.extend(peaks)

    timestamps = sorted(set(timestamps))
    filtered_ts: list[float] = []
    for ts in timestamps:
        if not filtered_ts or ts - filtered_ts[-1] >= 3.0:
            filtered_ts.append(ts)

    return filtered_ts


def download_grid_image(
    url: str,
    dest_path: Path,
    timeout: int = 10,
    max_retries: int = 3,
) -> bool:
    """Download storyboard grid image with exponential retry and User-Agent headers.

    Args:
        url: Image URL string.
        dest_path: Destination path on local filesystem.
        timeout: HTTP request timeout in seconds.
        max_retries: Number of download retry attempts.

    Returns:
        True if download succeeded and file was written, False otherwise.
    """
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                dest_path.write_bytes(resp.read())
            return True
        except Exception as e:
            _logger.warning(f"Download grid failed (Attempt {attempt}/{max_retries}): {e}")
    return False


def extract_storyboard_frames(
    sb_spec: dict[str, Any],
    tmp_dir: Path,
    target_timestamps: list[float],
    duration_sec: float,
) -> list[Path]:
    """Download storyboard grids and crop target timestamps into static frame files.

    Args:
        sb_spec: Storyboard specification dict (sb0/sb1/sb2 format).
        tmp_dir: Directory for temporary grids and cropped frames.
        target_timestamps: Timestamps to sample.
        duration_sec: Total duration of the video.

    Returns:
        List of generated static frame Paths.
    """
    fragments = sb_spec.get("fragments") or []
    if not fragments or PILImage is None:
        return []

    rows = int(sb_spec.get("rows") or 3)
    columns = int(sb_spec.get("columns") or 3)
    num_tiles = rows * columns
    if num_tiles <= 0:
        num_tiles = 9

    fragment_duration = sb_spec.get("fragment_duration")
    if not fragment_duration:
        total_dur = sum(float(f.get("duration", 0.0)) for f in fragments)
        if total_dur > 0:
            fragment_duration = total_dur / len(fragments)
        else:
            fragment_duration = duration_sec / len(fragments) if fragments else 88.62
    else:
        fragment_duration = float(fragment_duration)

    tile_duration = fragment_duration / num_tiles
    grid_cache: dict[int, Any] = {}
    static_frames: list[Path] = []

    for i, ts in enumerate(target_timestamps):
        frag_idx = int(ts // fragment_duration)
        if frag_idx >= len(fragments):
            frag_idx = len(fragments) - 1
        if frag_idx < 0:
            frag_idx = 0

        tile_idx = int((ts % fragment_duration) // tile_duration)
        if tile_idx >= num_tiles:
            tile_idx = num_tiles - 1
        if tile_idx < 0:
            tile_idx = 0

        grid_url = fragments[frag_idx].get("url")
        if not grid_url:
            continue

        if frag_idx not in grid_cache:
            grid_path = tmp_dir / f"grid_{frag_idx}.jpg"
            if download_grid_image(grid_url, grid_path):
                try:
                    with PILImage.open(grid_path) as img:
                        grid_cache[frag_idx] = img.copy()
                except Exception as e:
                    _logger.warning(f"Could not open grid image {frag_idx}: {e}")
                    continue
            else:
                continue

        grid_img = grid_cache[frag_idx]
        w, h = grid_img.size
        tile_w = w // columns
        tile_h = h // rows

        r = tile_idx // columns
        c = tile_idx % columns
        box = (c * tile_w, r * tile_h, (c + 1) * tile_w, (r + 1) * tile_h)

        try:
            tile = grid_img.crop(box)
            out_path = tmp_dir / f"frame_static_{i:04d}.jpg"
            tile.save(out_path, "JPEG")
            static_frames.append(out_path)
        except Exception as e:
            _logger.warning(f"Error cropping storyboard tile {tile_idx}: {e}")

    return static_frames


__all__ = [
    "extract_youtube_video_id",
    "format_whisper_transcript",
    "group_transcript_segments",
    "fetch_youtube_transcript",
    "compute_frame_hash",
    "dedup_frames",
    "find_ffmpeg_bin",
    "extract_video_frames",
    "format_lesson_notes",
    "get_heatmap_peaks",
    "get_target_timestamps",
    "download_grid_image",
    "extract_storyboard_frames",
]
