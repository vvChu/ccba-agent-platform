# mypy: ignore-errors
"""CCBA Platform — YouTube/Video Watcher & Belief Archaeology Orchestrator.

Main entry point script to fetch transcripts, extract slide frames, and synthesize notes.
"""

import logging
import os
import sys
from pathlib import Path

# Setup Console UTF-8 compatibility for Windows diacritics
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Add current skill path to sys.path to enable local imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
_logger = logging.getLogger("ccba.youtube.orchestrator")

from transcript import fetch_youtube_transcript  # noqa: E402
from visual_extractor import extract_video_visuals  # noqa: E402

from ccba_pdf_prep.media import extract_youtube_video_id
from ccba_pdf_prep.media import find_ffmpeg_bin as _find_ffmpeg_bin


def synthesize_concept_notes(
    transcript: str, filenames: list[str], images_subfolder: str = "images", max_tokens: int = 8192
) -> str:
    """Synthesize learning notes inserting markdown links to slide images."""
    from ccba_ai import ai

    _logger.info("Synthesizing concept notes via LLM...")
    prompt = (
        "Bạn là trợ lý nghiên cứu học thuật cao cấp tại CCBA. Hãy phân tích phụ đề và danh sách hình ảnh slide trích xuất được từ video bài giảng để viết tài liệu tóm tắt kiến thức (Concept Notes) chuyên sâu bằng tiếng Việt.\n\n"
        "YÊU CẦU CỐT LÕI:\n"
        "1. Trình bày chi tiết, mạch lạc toàn bộ kiến thức trong video. Không tóm tắt sơ sài.\n"
        "2. Tích hợp đầy đủ các công thức toán học (dùng LaTeX), sơ đồ logic (dùng Mermaid), bảng biểu so sánh, và mã nguồn (code snippets) thực tế trong bài giảng.\n"
        f"3. Chèn các hình ảnh slide tương ứng vào đúng vị trí dòng chảy kiến thức bằng định dạng markdown: ![Mô tả slide](./{images_subfolder}/[tên_file_ảnh]). Viết alt-text chi tiết cho ảnh slide đó (chứa sơ đồ gì, công thức gì).\n\n"
        f"TRANSCRIPT PHỤ ĐỀ:\n---\n{transcript}\n---\n\n"
        f"DANH SÁCH HÌNH ẢNH SLIDE ĐÃ TRÍCH XUẤT:\n{filenames}\n\n"
        "Chỉ trả về nội dung Markdown của tài liệu Concept Notes. Không bọc mã nguồn Markdown trong code block lớn."
    )
    res = ai.chat(prompt, model="gemini-3.1-pro-high", max_tokens=max_tokens, temperature=0.31)
    return res.strip()


def synthesize_worldview_notes(
    transcript: str, speaker_name: str, video_title: str, max_tokens: int = 4096
) -> str:
    """Analyze speaker's hidden assumptions and worldviews based on template."""
    from ccba_ai import ai

    _logger.info("Analyzing speaker worldviews via LLM...")
    template_path = Path(__file__).parent.parent / "references" / "worldview_template.md"
    try:
        template_content = template_path.read_text(encoding="utf-8")
    except Exception:
        template_content = "Format using tables mapping Phenomenon, Hidden Belief, Valid When, Invalid When, Action items."

    prompt = (
        "Bạn là một triết gia và chuyên gia khảo cổ học niềm tin (Belief Archaeology). Dưới đây là phụ đề của một video thuyết trình/bài giảng.\n"
        "NHIỆM VỤ CỦA BẠN:\n"
        "Hãy đào sâu suy nghĩ, phân tích các giả định ngầm, các thế giới quan ẩn giấu mà diễn giả tin là hiển nhiên đúng nhưng không nói ra trực tiếp.\n"
        "Hãy viết tài liệu phân tích bằng tiếng Việt theo định dạng mẫu dưới đây:\n\n"
        f"MẪU TEMPLATE ĐỊNH DẠNG:\n---\n{template_content}\n---\n\n"
        f"THÔNG TIN BÀI GIẢNG:\n"
        f"- Diễn giả: {speaker_name}\n"
        f"- Video: {video_title}\n\n"
        f"TRANSCRIPT PHỤ ĐỀ:\n---\n{transcript}\n---\n\n"
        "Chỉ trả về nội dung Markdown hoàn chỉnh của tài liệu Worldview Notes. Không bọc trong code block lớn."
    )
    res = ai.chat(prompt, model="gemini-3.1-pro-high", max_tokens=max_tokens, temperature=0.31)
    return res.strip()


def synthesize_speaker_notes(transcript: str, speaker_name: str, max_tokens: int = 2048) -> str:
    """Generate speaker profile based on transcript and template."""
    from ccba_ai import ai

    _logger.info("Generating speaker profile via LLM...")
    template_path = Path(__file__).parent.parent / "references" / "speaker_profile_template.md"
    try:
        template_content = template_path.read_text(encoding="utf-8")
    except Exception:
        template_content = "Format containing Quick Facts, Top 5 Achievements, Differentiators, analyzed videos table."

    prompt = (
        "Bạn là một chuyên gia nhân sự và đánh giá chuyên gia. Hãy phân tích phụ đề để xây dựng hồ sơ diễn giả (Speaker Profile) bằng tiếng Việt theo định dạng mẫu dưới đây:\n\n"
        f"MẪU TEMPLATE ĐỊNH DẠNG:\n---\n{template_content}\n---\n\n"
        f"TÊN DIỄN GIẢ: {speaker_name}\n\n"
        f"TRANSCRIPT PHỤ ĐỀ:\n---\n{transcript}\n---\n\n"
        "Chỉ trả về nội dung Markdown hoàn chỉnh của tài liệu Speaker Notes. Yêu cầu viết cực kỳ súc tích, ngắn gọn từng mục để đảm bảo nội dung đầy đủ tất cả các phần của mẫu và không bị cắt cụt ở cuối. Không bọc trong code block lớn."
    )
    res = ai.chat(prompt, model="gemini-3.1-flash-lite", max_tokens=max_tokens, temperature=0.31)
    return res.strip()


def extract_speaker_from_transcript(transcript: str, default: str = "Diễn giả") -> str:
    """Uses LLM to detect the speaker's real name from the first part of transcript."""
    from ccba_ai import ai

    # If transcript is very short, just return default
    if not transcript or len(transcript) < 100:
        return default

    # Send only the first 3000 chars to save tokens
    sample = transcript[:3000]
    prompt = (
        "Bạn là trợ lý nghiên cứu học thuật cao cấp tại CCBA. Dưới đây là phần đầu của phụ đề một bài phát biểu hoặc bài giảng.\n"
        "Nhiệm vụ của bạn là xác định chính xác họ và tên của diễn giả (người nói chính) trong bài phát biểu này.\n\n"
        "Yêu cầu:\n"
        "1. Chỉ trả về duy nhất họ và tên của diễn giả (ví dụ: 'Đặng Lê Nguyên Vũ', 'TS. Trần Văn A'). Không giải thích thêm.\n"
        '2. Nếu không tìm thấy tên diễn giả cụ thể hoặc không chắc chắn, hãy trả về đúng giá trị mặc định sau (không bao gồm dấu ngoặc kép): "'
        + default
        + '"\n\n'
        f"ĐOẠN TRÍCH PHỤ ĐỀ:\n---\n{sample}\n---"
    )
    try:
        res = ai.chat(prompt, model="gemini-3.1-flash-lite", max_tokens=100, temperature=0.1)
        cleaned = res.strip().strip("'\"")
        # If it returned some long sentence instead of a name, fallback
        if (
            cleaned
            and len(cleaned) < 50
            and "phụ đề" not in cleaned.lower()
            and "không tìm thấy" not in cleaned.lower()
        ):
            return cleaned
    except Exception as e:
        _logger.warning(f"Error auto-detecting speaker name: {e}")
    return default


def _extract_video_id(video_url: str) -> str:
    """Extract YouTube video ID from URL or generate a unique slug."""
    import hashlib

    vid = extract_youtube_video_id(video_url)
    if vid:
        return vid

    if os.path.exists(video_url):
        return Path(video_url).stem

    return hashlib.md5(video_url.encode("utf-8")).hexdigest()[:11]


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CCBA youtube-learn Orchestrator.")
    parser.add_argument("video_url", type=str, help="URL of the video or local video path")
    parser.add_argument(
        "output_dir", type=str, nargs="?", default=None, help="Output directory path"
    )
    parser.add_argument(
        "--project", "-p", type=str, default=None, help="Tên đề tài/dự án (Cohesive Topic Folder)"
    )
    parser.add_argument("--speaker", type=str, default=None, help="Explicit speaker name")

    args = parser.parse_args()
    video_url = args.video_url
    video_id = _extract_video_id(video_url)

    # Resolve Output Directory Fallback
    if args.project:
        output_dir = (Path.cwd() / ".md" / "projects" / args.project).absolute()
    elif args.output_dir:
        output_dir = Path(args.output_dir).absolute()
    else:
        # Fallback to default cohesive topic folder
        output_dir = (Path.cwd() / ".md" / "projects" / "default_topic").absolute()

    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / f"images_{video_id}"

    _logger.info(f"CCBA youtube-learn run started. Output folder: {output_dir.absolute()}")

    # Pre-execution checks
    ffmpeg_path = _find_ffmpeg_bin()
    is_text_only = False
    if not ffmpeg_path:
        _logger.warning("ffmpeg is missing from the system. Falling back to TEXT-ONLY MODE.")
        is_text_only = True

    # Pre-execution API Key Check for non-YouTube URLs
    is_youtube = any(x in video_url for x in ["youtube.com", "youtu.be"])
    if not is_youtube:
        # Verify API Keys for Whisper STT
        gateway_key = os.environ.get("AI_GATEWAY_KEY") or os.environ.get("OPENAI_API_KEY")
        if not gateway_key:
            _logger.error(
                "API Key (AI_GATEWAY_KEY / OPENAI_API_KEY) is missing for non-YouTube STT transcription. Aborting execution to save bandwidth."
            )
            sys.exit(1)

    # 1. Fetch transcript
    _logger.info("Phase 2: Extracting/transcribing audio transcript...")
    transcript = fetch_youtube_transcript(video_url, output_dir)

    if not transcript:
        _logger.error("Failed to extract transcript. Exiting.")
        sys.exit(1)

    # Save raw transcript
    transcript_file = output_dir / f"raw_transcript_{video_id}.txt"
    transcript_file.write_text(transcript, encoding="utf-8")
    try:
        rel_path = transcript_file.relative_to(Path.cwd())
    except ValueError:
        rel_path = transcript_file.absolute()
    _logger.info(f"Saved raw transcript to {rel_path}")

    # 2. Extract images (if not in Text-Only Mode)
    saved_images = []
    if not is_text_only:
        _logger.info("Phase 3: Extracting video frames...")
        saved_images = extract_video_visuals(video_url, images_dir, transcript)
        _logger.info(f"Extracted and saved {len(saved_images)} slide images.")
    else:
        _logger.info("Skipping frame extraction due to missing ffmpeg.")

    # 3. Synthesize notes
    _logger.info("Phase 4: Generating knowledge synthesis documents...")

    # Try to extract metadata for naming
    speaker_name = "Diễn giả"
    video_title = "Bài giảng"
    try:
        import yt_dlp

        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if info:
                video_title = info.get("title", video_title)
                speaker_name = info.get("uploader", speaker_name)
    except Exception:
        pass

    # Use explicit speaker name if provided, otherwise extract from transcript
    if args.speaker:
        speaker_name = args.speaker
    else:
        speaker_name = extract_speaker_from_transcript(transcript, default=speaker_name)
        _logger.info(f"Auto-detected speaker name: {speaker_name}")

    # Calculate smart adaptive max_tokens limits based on transcript length
    transcript_len = len(transcript)
    if transcript_len > 60000:  # Video ~ >1 hour
        dynamic_concept_limit = 32768
        dynamic_worldview_limit = 8192
    elif transcript_len > 30000:  # Video ~ 30-60 minutes
        dynamic_concept_limit = 16384
        dynamic_worldview_limit = 6144
    else:  # Video ~ <30 minutes
        dynamic_concept_limit = 8192
        dynamic_worldview_limit = 4096

    def _safe_int_env(var_name: str, fallback: int) -> int:
        val = os.environ.get(var_name)
        if val is None:
            return fallback
        try:
            return int(val)
        except ValueError:
            _logger.warning(
                f"Invalid integer for env var '{var_name}': '{val}'. Using default '{fallback}'."
            )
            return fallback

    max_tokens_concept = _safe_int_env("MAX_TOKENS_CONCEPT", dynamic_concept_limit)
    max_tokens_worldview = _safe_int_env("MAX_TOKENS_WORLDVIEW", dynamic_worldview_limit)
    max_tokens_speaker = _safe_int_env("MAX_TOKENS_SPEAKER", 2048)

    images_subfolder = f"images_{video_id}" if not is_text_only else "images"
    concept_notes = synthesize_concept_notes(
        transcript, saved_images, images_subfolder=images_subfolder, max_tokens=max_tokens_concept
    )
    worldview_notes = synthesize_worldview_notes(
        transcript, speaker_name, video_title, max_tokens=max_tokens_worldview
    )
    speaker_notes = synthesize_speaker_notes(
        transcript, speaker_name, max_tokens=max_tokens_speaker
    )

    # Write files
    (output_dir / f"notes_concept_{video_id}.md").write_text(concept_notes, encoding="utf-8")
    (output_dir / f"notes_worldview_{video_id}.md").write_text(worldview_notes, encoding="utf-8")
    (output_dir / f"notes_speaker_{video_id}.md").write_text(speaker_notes, encoding="utf-8")

    _logger.info("All documents synthesized and saved successfully!")
    print("\n🎉 CCBA Belief Archaeology completed successfully!")
    print(f"📁 Output files saved at: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
