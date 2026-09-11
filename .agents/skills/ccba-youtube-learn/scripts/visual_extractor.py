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
import urllib.request
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
    extract_storyboard_frames as _get_storyboard_frames,
    find_ffmpeg_bin as _find_ffmpeg_bin,
    get_heatmap_peaks as _get_heatmap_peaks,
    get_target_timestamps as _get_target_timestamps,
)


def extract_video_visuals(
    url: str, output_images_dir: Path, transcript_text: str | None = None
) -> list[str]:
    """Extract slide & whiteboard frames from video. Returns list of saved filenames."""
    tmp_dir = output_images_dir.parent / "_video_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    extracted_frames = []
    duration_sec = 600
    chapters: list[dict[str, Any]] = []
    heatmap: list[dict[str, Any]] = []
    video_id: str | None = "temp_video"
    info_dict = None
    cache_file: Path | None = None
    cache_data: dict[str, Any] = {}

    # Find FFmpeg binary
    ffmpeg_bin = _find_ffmpeg_bin()

    try:
        import yt_dlp

        # Parse Video ID
        parsed = urllib.parse.urlparse(url)
        if parsed.hostname in ("youtu.be", "www.youtu.be"):
            video_id = parsed.path[1:]
        elif parsed.hostname in ("youtube.com", "www.youtube.com"):
            if parsed.path == "/watch":
                qs = urllib.parse.parse_qs(parsed.query)
                video_id = qs.get("v", [None])[0]
            elif parsed.path.startswith(("/embed/", "/v/", "/live/")):
                video_id = parsed.path.split("/")[2]

        if not video_id:
            video_id = "local_video"

        # Check Cache
        resolved_dir = output_images_dir.resolve()
        if len(resolved_dir.parents) >= 2:
            cache_dir = resolved_dir.parents[1] / ".md" / "scratch" / "cache"
            if not (resolved_dir.parents[1] / ".md").exists():
                cache_dir = Path(".md") / "scratch" / "cache"
        else:
            cache_dir = Path(".md") / "scratch" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "video_cache.json"

        if cache_file.exists():
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
                        return cached_filenames
            except Exception as ce:
                _logger.warning(f"Failed to read video cache: {ce}")

        # 1. Fetch metadata
        _logger.info(f"Extracting metadata JIT for: {url}")
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)

        if not info_dict:
            return []

        duration_sec = info_dict.get("duration") or 600
        chapters = info_dict.get("chapters") or []
        heatmap = info_dict.get("heatmap") or []

        # Find storyboard CDN specs
        sb0 = None
        for target_sb in ["sb2", "sb1", "sb0"]:
            for fmt in info_dict.get("formats", []):
                if fmt.get("format_id") == target_sb:
                    sb0 = fmt
                    break
            if sb0:
                break
        if not sb0:
            for fmt in info_dict.get("formats", []):
                if "storyboard" in fmt.get("format_note", "") or fmt.get(
                    "format_id", ""
                ).startswith("sb"):
                    sb0 = fmt
                    break

        target_timestamps = _get_target_timestamps(duration_sec, chapters, heatmap)
        frame_metadata = {}

        # 2. Frame sampling
        force_video = os.environ.get("FORCE_VIDEO_FALLBACK", "false").lower() == "true"
        if sb0 and PILImage is not None and not force_video:
            _logger.info("Stage 1: Storyboard coarse sampling from Google CDN...")
            coarse_frames = _get_storyboard_frames(sb0, tmp_dir, target_timestamps, duration_sec)
            for i, p in enumerate(coarse_frames):
                frame_metadata[p] = {
                    "timestamp": target_timestamps[i] if i < len(target_timestamps) else 0.0,
                    "original_index": i,
                }
            extracted_frames = coarse_frames
        else:
            # Stage 2: Download raw video + FFmpeg
            if not ffmpeg_bin:
                _logger.warning(
                    "FFmpeg not found in path! Cannot extract frames from video stream. Fallback to Text-Only."
                )
                return []

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

            video_path: Path | None = None
            for file_path in tmp_dir.glob(f"{video_id}.*"):
                if file_path.is_file() and file_path.suffix in (".mp4", ".webm", ".mkv", ".m4v"):
                    video_path = file_path
                    break

            if not video_path or not video_path.exists():
                _logger.error("Failed to download video stream.")
                return []

            _logger.info(f"Video stream downloaded: {video_path.name}")

            # Run FFmpeg static sampling
            startupinfo = None
            if os.name == "nt":
                startupinfo_class = getattr(subprocess, "STARTUPINFO", None)
                if startupinfo_class is not None:
                    startupinfo = startupinfo_class()
                    flags = getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
                    startupinfo.dwFlags |= flags
            static_frames = []
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
                    cmd,
                    capture_output=True,
                    startupinfo=startupinfo,
                    text=True,
                    timeout=180,
                )
                if res.returncode == 0 and out_path.exists():
                    static_frames.append(out_path)
                    frame_metadata[out_path] = {
                        "timestamp": ts,
                        "original_index": i,
                    }
            extracted_frames = static_frames

        # 3. Deduplication
        if len(extracted_frames) > 1:
            before_len = len(extracted_frames)
            extracted_frames = _dedup_frames(extracted_frames)
            _logger.info(f"Deduplication finished: {before_len} -> {len(extracted_frames)} frames.")

        if not extracted_frames:
            return []

        # 4. LLM-as-Judge filter (reject pure Talking Head and outro/intro)
        from ccba_ai import ai

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

        # Multi-modal payload using ccba-ai chat_multi
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]

        for f_path in extracted_frames:
            # Encode image to base64 with maximum pixel size 768 for efficiency
            b64_data = ai.encode_image(f_path, max_pixels=768)
            content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}}
            )

        messages = [{"role": "user", "content": content}]

        judge_res = ai.chat_multi(messages, model="gemini-3.1-flash-lite", temperature=0.2)
        _logger.info("LLM-as-Judge response parsed successfully.")

        key_frame_indices = []
        match = re.search(r"KEY_FRAMES:\s*(\[.*?\])", judge_res)
        if match:
            try:
                key_frame_indices = json.loads(match.group(1))
            except Exception:
                pass

        if not key_frame_indices:
            # Auto fallback: keep all slides if judge output is unparseable
            key_frame_indices = list(range(len(extracted_frames)))

        # 5. Extract & Save selected frames as WebP to output_images_dir (Without max cap)
        output_images_dir.mkdir(parents=True, exist_ok=True)
        saved_filenames = []

        for idx in key_frame_indices:
            try:
                idx = int(idx)
                if 0 <= idx < len(extracted_frames):
                    src_path = extracted_frames[idx]
                    metadata = frame_metadata.get(
                        src_path, {"timestamp": 0.0, "original_index": idx}
                    )
                    ts_int = int(metadata["timestamp"])
                    original_idx = metadata["original_index"]

                    filename = f"yt_{video_id}_frame_{original_idx:03d}_ts{ts_int}.webp"
                    dest_path = output_images_dir / filename

                    if PILImage is not None:
                        # Convert static jpg to webp
                        with PILImage.open(src_path) as img:
                            img.save(dest_path, "WEBP", quality=80)
                    else:
                        # Direct copy if PIL is missing
                        dest_path_jpg = (
                            output_images_dir
                            / f"yt_{video_id}_frame_{original_idx:03d}_ts{ts_int}.jpg"
                        )
                        shutil.copy(src_path, dest_path_jpg)
                        filename = dest_path_jpg.name

                    saved_filenames.append(filename)
            except Exception as save_err:
                _logger.warning(f"Failed to save frame index {idx}: {save_err}")

        # Clean up temporary folder
        if tmp_dir.exists():
            try:
                shutil.rmtree(tmp_dir)
            except OSError:
                pass

        # Save to Cache
        if saved_filenames and cache_file is not None:
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

        return saved_filenames

    except Exception as e:
        _logger.error(f"Visual extraction process encountered error: {e}")
        # Make sure temporary folder is cleared
        if tmp_dir.exists():
            try:
                shutil.rmtree(tmp_dir)
            except OSError:
                pass
        return []
