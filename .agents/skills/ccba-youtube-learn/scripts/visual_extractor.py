"""CCBA Platform — YouTube/Video Visual Extractor.

Extracts visual frames from YouTube videos.
Implements Two-Stage Hybrid Ingestion with Pillow perceptual hash and LLM-as-Judge filtering.
"""

import datetime
import json
import logging
import os
import re
import shutil
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any

# Setup logging
_logger = logging.getLogger("ccba.youtube.visual")

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None  # type: ignore[assignment]


from ccba_pdf_prep.media import (
    dedup_frames as _dedup_frames,
)
from ccba_pdf_prep.media import (
    extract_storyboard_frames as _get_storyboard_frames,
)
from ccba_pdf_prep.media import (
    find_ffmpeg_bin as _find_ffmpeg_bin,
)
from ccba_pdf_prep.media import (
    get_heatmap_peaks as _get_heatmap_peaks,  # noqa: F401
)
from ccba_pdf_prep.media import (
    get_target_timestamps as _get_target_timestamps,
)


def _parse_youtube_video_id(url: str) -> str:
    """Parse YouTube video ID from URL or return fallback identifier."""
    video_id: str | None = None
    parsed = urllib.parse.urlparse(url)
    if parsed.hostname in ("youtu.be", "www.youtu.be"):
        video_id = parsed.path[1:]
    elif parsed.hostname in ("youtube.com", "www.youtube.com"):
        if parsed.path == "/watch":
            qs = urllib.parse.parse_qs(parsed.query)
            video_id = qs.get("v", [None])[0]
        elif parsed.path.startswith(("/embed/", "/v/", "/live/")):
            video_id = parsed.path.split("/")[2]
    return video_id or "local_video"


def _resolve_cache_file(output_images_dir: Path) -> Path:
    """Resolve path to video_cache.json inside .md/scratch/cache."""
    resolved_dir = output_images_dir.resolve()
    if len(resolved_dir.parents) >= 2:
        cache_dir = resolved_dir.parents[1] / ".md" / "scratch" / "cache"
        if not (resolved_dir.parents[1] / ".md").exists():
            cache_dir = Path(".md") / "scratch" / "cache"
    else:
        cache_dir = Path(".md") / "scratch" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "video_cache.json"


def _load_cached_slides(
    cache_file: Path, video_id: str, output_images_dir: Path
) -> tuple[dict[str, Any], list[str] | None]:
    """Load cached slide list if all files still exist on disk."""
    cache_data: dict[str, Any] = {}
    if not cache_file.exists():
        return cache_data, None
    try:
        with open(cache_file, encoding="utf-8") as f:
            cache_data = json.load(f)
        if video_id in cache_data:
            entry = cache_data[video_id]
            cached_filenames: list[str] = list(entry.get("filenames", []))
            if cached_filenames and all(
                (output_images_dir / fn).exists() for fn in cached_filenames
            ):
                _logger.info(
                    f"[CACHE HIT] Đang sử dụng {len(cached_filenames)} ảnh slide được cache cho video {video_id}."
                )
                return cache_data, cached_filenames
    except Exception as ce:
        _logger.warning(f"Failed to read video cache: {ce}")
    return cache_data, None


def _save_cached_slides(
    cache_file: Path | None,
    cache_data: dict[str, Any],
    video_id: str,
    saved_filenames: list[str],
) -> None:
    """Persist extracted slide filenames to video_cache.json."""
    if not saved_filenames or cache_file is None:
        return
    try:
        cache_data[video_id] = {
            "filenames": saved_filenames,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        _logger.info(
            f"[CACHE WRITE] Đã lưu cache kết quả lọc {len(saved_filenames)} slide cho video {video_id}."
        )
    except Exception as ce:
        _logger.warning(f"Failed to write video cache: {ce}")


def _find_storyboard_spec(info_dict: dict[str, Any]) -> dict[str, Any] | None:
    """Locate highest-resolution storyboard format spec from yt-dlp info_dict."""
    formats = info_dict.get("formats", [])
    for target_sb in ["sb2", "sb1", "sb0"]:
        for fmt in formats:
            if isinstance(fmt, dict) and fmt.get("format_id") == target_sb:
                return fmt
    for fmt in formats:
        if isinstance(fmt, dict) and (
            "storyboard" in fmt.get("format_note", "") or fmt.get("format_id", "").startswith("sb")
        ):
            return fmt
    return None


def _download_fallback_video(url: str, tmp_dir: Path, video_id: str) -> Path | None:
    """Download lightweight video stream when storyboard CDN is unavailable."""
    import yt_dlp

    _logger.info("Storyboard CDN unavailable or PIL missing. Downloading video fallback...")
    out_tmpl = str(tmp_dir / f"{video_id}.%(ext)s")
    ydl_opts = {
        "format": "bestvideo[height<=480]/worstvideo",
        "outtmpl": out_tmpl,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    for file_path in tmp_dir.glob(f"{video_id}.*"):
        if file_path.is_file() and file_path.suffix in (".mp4", ".webm", ".mkv", ".m4v"):
            _logger.info(f"Video stream downloaded: {file_path.name}")
            return file_path
    _logger.error("Failed to download video stream.")
    return None


def _sample_static_ffmpeg_frames(
    video_path: Path, tmp_dir: Path, target_timestamps: list[float], ffmpeg_bin: str
) -> tuple[list[Path], dict[Path, dict[str, Any]]]:
    """Run FFmpeg static sampling across target timestamps."""
    startupinfo = None
    if os.name == "nt":
        startupinfo_class = getattr(subprocess, "STARTUPINFO", None)
        if startupinfo_class is not None:
            startupinfo = startupinfo_class()
            startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 0)

    static_frames: list[Path] = []
    frame_metadata: dict[Path, dict[str, Any]] = {}
    for i, ts in enumerate(target_timestamps):
        out_path = tmp_dir / f"frame_static_{i:04d}.jpg"
        cmd = [
            ffmpeg_bin,
            "-y",
            "-ss",
            str(round(ts, 2)),
            "-i",
            str(video_path),
            "-vframes",
            "1",
            str(out_path),
        ]
        res = subprocess.run(
            cmd, capture_output=True, startupinfo=startupinfo, text=True, timeout=180
        )
        if res.returncode == 0 and out_path.exists():
            static_frames.append(out_path)
            frame_metadata[out_path] = {"timestamp": ts, "original_index": i}
    return static_frames, frame_metadata


def _sample_candidate_frames(
    url: str,
    info_dict: dict[str, Any],
    tmp_dir: Path,
    video_id: str,
    ffmpeg_bin: str | None,
) -> tuple[list[Path], dict[Path, dict[str, Any]]]:
    """Sample candidate frames via Storyboard CDN or FFmpeg fallback."""
    duration_sec = info_dict.get("duration") or 600
    chapters = info_dict.get("chapters") or []
    heatmap = info_dict.get("heatmap") or []
    target_timestamps = _get_target_timestamps(duration_sec, chapters, heatmap)
    sb0 = _find_storyboard_spec(info_dict)
    force_video = os.environ.get("FORCE_VIDEO_FALLBACK", "false").lower() == "true"

    if sb0 and PILImage is not None and not force_video:
        _logger.info("Stage 1: Storyboard coarse sampling from Google CDN...")
        coarse_frames = _get_storyboard_frames(sb0, tmp_dir, target_timestamps, duration_sec)
        frame_metadata = {
            p: {
                "timestamp": target_timestamps[i] if i < len(target_timestamps) else 0.0,
                "original_index": i,
            }
            for i, p in enumerate(coarse_frames)
        }
        return coarse_frames, frame_metadata

    if not ffmpeg_bin:
        _logger.warning("FFmpeg not found in path! Fallback to Text-Only.")
        return [], {}

    video_path = _download_fallback_video(url, tmp_dir, video_id)
    if not video_path or not video_path.exists():
        return [], {}
    return _sample_static_ffmpeg_frames(video_path, tmp_dir, target_timestamps, ffmpeg_bin)


def _judge_educational_frames(
    extracted_frames: list[Path], transcript_text: str | None
) -> list[int]:
    """Use LLM-as-Judge to filter out Talking Heads and select educational slide indices."""
    from ccba_ai import ai
    from ccba_ai.routing import choose_model

    _logger.info(
        "Executing LLM-as-Judge to filter out Talking Heads and keep educational slides..."
    )
    prompt = (
        "Bạn là một LLM-as-Judge chuyên nghiệp, chịu trách nhiệm phân tích các khung hình của một video bài giảng để lọc ra các khung hình có giá trị tri thức trực quan cao nhất.\n\n"
        "NHIỆM VỤ CỦA BẠN:\n"
        "1. Phân tích sự tiến triển trực quan qua các khung hình được cung cấp (đã được đánh chỉ số 0, 1, 2... theo thứ tự thời gian).\n"
        "2. Đọc và đối chiếu chặt chẽ với phần AUDIO TRANSCRIPT CONTEXT bên dưới để hiểu nội dung học thuật được thảo luận.\n"
        "3. Báo cáo bằng TIẾNG VIỆT tóm tắt nội dung slide học thuật. Không viết 'ở khung hình 1', hãy diễn giải mượt mà.\n"
        "4. Lọc KEY_FRAMES theo nguyên tắc:\n"
        "   - CẤM TUYỆT ĐỐI chọn các khung hình 'Talking Head' (chân dung người nói cận cảnh mặt) mà KHÔNG có slide chữ, biểu đồ, sơ đồ đi kèm.\n"
        "   - Các khung hình slide lớn có ghép mặt nhỏ diễn giải ở góc (split-screen) vẫn ĐƯỢC CHẤP NHẬN.\n"
        "   - CẤM chọn ảnh subscribe, intro, outro, logo chuyển cảnh.\n"
        "   - CHỈ giữ lại các slide bài giảng đọc được chữ, sơ đồ kiến trúc, mã nguồn, hoặc bảng so sánh dữ liệu.\n\n"
        "Ở DÒNG CUỐI CÙNG của câu trả lời, xuất ra chính xác định dạng:\n"
        "KEY_FRAMES: [index1, index2, ...]\n"
        "Nếu không có ảnh nào có slide trực quan học thuật, hãy xuất ra: KEY_FRAMES: []"
    )
    if transcript_text:
        prompt += f"\n\n=== [AUDIO TRANSCRIPT CONTEXT] ===\n{transcript_text}\n==================================\n"

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for f_path in extracted_frames:
        b64_data = ai.encode_image(f_path, max_pixels=768)
        content.append(
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}}
        )

    judge_res = ai.chat_multi(
        [{"role": "user", "content": content}], model=choose_model("fast"), temperature=0.2
    )
    _logger.info("LLM-as-Judge response parsed successfully.")

    match = re.search(r"KEY_FRAMES:\s*(\[.*?\])", judge_res)
    if match:
        try:
            parsed = json.loads(match.group(1))
            if parsed:
                return [int(x) for x in parsed]
        except Exception:
            pass
    return list(range(len(extracted_frames)))


def _export_selected_frames(
    extracted_frames: list[Path],
    key_frame_indices: list[int],
    frame_metadata: dict[Path, dict[str, Any]],
    output_images_dir: Path,
    video_id: str,
) -> list[str]:
    """Convert and save selected key frames as WebP (or JPG fallback) in output_images_dir."""
    output_images_dir.mkdir(parents=True, exist_ok=True)
    saved_filenames: list[str] = []
    for idx in key_frame_indices:
        try:
            idx = int(idx)
            if 0 <= idx < len(extracted_frames):
                src_path = extracted_frames[idx]
                metadata = frame_metadata.get(src_path, {"timestamp": 0.0, "original_index": idx})
                ts_int = int(metadata["timestamp"])
                original_idx = metadata["original_index"]
                stem = f"yt_{video_id}_frame_{original_idx:03d}_ts{ts_int}"

                if PILImage is not None:
                    filename = f"{stem}.webp"
                    with PILImage.open(src_path) as img:
                        img.save(output_images_dir / filename, "WEBP", quality=80)
                else:
                    filename = f"{stem}.jpg"
                    shutil.copy(src_path, output_images_dir / filename)
                saved_filenames.append(filename)
        except Exception as save_err:
            _logger.warning(f"Failed to save frame index {idx}: {save_err}")
    return saved_filenames


def extract_video_visuals(
    url: str, output_images_dir: Path, transcript_text: str | None = None
) -> list[str]:
    """Extract slide & whiteboard frames from video. Returns list of saved filenames."""
    tmp_dir = output_images_dir.parent / "_video_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_bin = _find_ffmpeg_bin()

    try:
        import yt_dlp

        video_id = _parse_youtube_video_id(url)
        cache_file = _resolve_cache_file(output_images_dir)
        cache_data, cached = _load_cached_slides(cache_file, video_id, output_images_dir)
        if cached is not None:
            return cached

        _logger.info(f"Extracting metadata JIT for: {url}")
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)
        if not info_dict:
            return []

        extracted_frames, frame_metadata = _sample_candidate_frames(
            url, info_dict, tmp_dir, video_id, ffmpeg_bin
        )
        if len(extracted_frames) > 1:
            before_len = len(extracted_frames)
            extracted_frames = _dedup_frames(extracted_frames)
            _logger.info(f"Deduplication finished: {before_len} -> {len(extracted_frames)} frames.")
        if not extracted_frames:
            return []

        key_indices = _judge_educational_frames(extracted_frames, transcript_text)
        saved_filenames = _export_selected_frames(
            extracted_frames, key_indices, frame_metadata, output_images_dir, video_id
        )
        _save_cached_slides(cache_file, cache_data, video_id, saved_filenames)
        return saved_filenames
    except Exception as e:
        _logger.error(f"Visual extraction process encountered error: {e}")
        return []
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)
