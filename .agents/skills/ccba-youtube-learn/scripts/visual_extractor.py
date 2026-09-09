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
)
from ccba_pdf_prep.media import (
    find_ffmpeg_bin as _find_ffmpeg_bin,
)


def _get_heatmap_peaks(
    heatmap: list[dict[str, Any]], duration_sec: float, max_peaks: int = 10
) -> list[float]:
    """Parse YouTube heatmap and find the top timestamps of highest user engagement."""
    if not heatmap:
        return []

    valid_entries = []
    for entry in heatmap:
        start = entry.get("start_time", 0.0)
        end = entry.get("end_time", 0.0)
        val = entry.get("value")
        if val is not None:
            mid = start + (end - start) / 2.0
            if 0.0 <= mid <= duration_sec:
                valid_entries.append((val, mid))

    # Sort descending by engagement value
    valid_entries.sort(key=lambda x: x[0], reverse=True)

    # Choose top peaks avoiding duplicates close to each other (within 15s)
    peaks: list[float] = []
    for _val, ts in valid_entries:
        if not any(abs(ts - p) < 15.0 for p in peaks):
            peaks.append(ts)
            if len(peaks) >= max_peaks:
                break

    return sorted(peaks)


def _get_target_timestamps(
    duration_sec: float, chapters: list[dict[str, Any]], heatmap: list[dict[str, Any]] | None = None
) -> list[float]:
    """Calculate adaptive target timestamps for chapter-aware multi-sampling."""
    timestamps = []
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
            start = ch.get("start_time", 0.0)
            end = ch.get("end_time", duration_sec)
            if start < 0:
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
        # Fallback: dense coarse stage (sample 25 points)
        N = 25
        step = duration_sec / (N + 1)
        for i in range(1, N + 1):
            ts = i * step
            if 0.0 <= ts <= duration_sec:
                timestamps.append(ts)

    if heatmap:
        peaks = _get_heatmap_peaks(heatmap, duration_sec)
        timestamps.extend(peaks)

    # Sort and remove close timestamps (less than 3 seconds)
    timestamps = sorted(set(timestamps))
    filtered_ts: list[float] = []
    for ts in timestamps:
        if not filtered_ts or ts - filtered_ts[-1] >= 3.0:
            filtered_ts.append(ts)

    return filtered_ts


def _download_grid_with_retry(url: str, dest_path: Path) -> bool:
    """Download storyboard grid with timeout and headers."""
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                dest_path.write_bytes(resp.read())
            return True
        except Exception as e:
            _logger.warning(f"Download grid failed (Attempt {attempt}/3): {e}")
    return False


def _get_storyboard_frames(
    sb0: dict[str, Any], tmp_dir: Path, target_timestamps: list[float], duration_sec: float
) -> list[Path]:
    """Download storyboard grids and crop target timestamps into static frame files."""
    fragments = sb0.get("fragments") or []
    if not fragments or PILImage is None:
        return []

    rows = sb0.get("rows") or 3
    columns = sb0.get("columns") or 3
    num_tiles = rows * columns
    if num_tiles <= 0:
        num_tiles = 9

    fragment_duration = sb0.get("fragment_duration")
    if not fragment_duration:
        total_dur = sum(f.get("duration", 0) for f in fragments)
        if total_dur > 0:
            fragment_duration = total_dur / len(fragments)
        else:
            fragment_duration = duration_sec / len(fragments) if len(fragments) > 0 else 88.62

    tile_duration = fragment_duration / num_tiles
    grid_cache = {}
    static_frames = []

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
            if _download_grid_with_retry(grid_url, grid_path):
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
