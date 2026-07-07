"""CCBA Platform — YouTube/Video Watcher & Belief Archaeology Orchestrator.

Main entry point script to fetch transcripts, extract slide frames, and synthesize notes.
"""

import sys
import os
import logging
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

from transcript import fetch_youtube_transcript
from visual_extractor import extract_video_visuals, _find_ffmpeg_bin


def synthesize_concept_notes(transcript: str, filenames: list[str]) -> str:
    """Synthesize learning notes inserting markdown links to slide images."""
    from ccba_ai import ai

    _logger.info("Synthesizing concept notes via LLM...")
    prompt = (
        "Bạn là trợ lý nghiên cứu học thuật cao cấp tại CCBA. Hãy phân tích phụ đề và danh sách hình ảnh slide trích xuất được từ video bài giảng để viết tài liệu tóm tắt kiến thức (Concept Notes) chuyên sâu bằng tiếng Việt.\n\n"
        "YÊU CẦU CỐT LÕI:\n"
        "1. Trình bày chi tiết, mạch lạc toàn bộ kiến thức trong video. Không tóm tắt sơ sài.\n"
        "2. Tích hợp đầy đủ các công thức toán học (dùng LaTeX), sơ đồ logic (dùng Mermaid), bảng biểu so sánh, và mã nguồn (code snippets) thực tế trong bài giảng.\n"
        "3. Chèn các hình ảnh slide tương ứng vào đúng vị trí dòng chảy kiến thức bằng định dạng markdown: ![Mô tả slide](./images/[tên_file_ảnh]). Viết alt-text chi tiết cho ảnh slide đó (chứa sơ đồ gì, công thức gì).\n\n"
        f"TRANSCRIPT PHỤ ĐỀ:\n---\n{transcript}\n---\n\n"
        f"DANH SÁCH HÌNH ẢNH SLIDE ĐÃ TRÍCH XUẤT:\n{filenames}\n\n"
        "Chỉ trả về nội dung Markdown của tài liệu Concept Notes. Không bọc mã nguồn Markdown trong code block lớn."
    )
    res = ai.chat(prompt, model="gemini-2.5-flash", max_tokens=8192, temperature=0.3)
    return res.strip()


def synthesize_worldview_notes(transcript: str, speaker_name: str, video_title: str) -> str:
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
    res = ai.chat(prompt, model="gemini-2.5-flash", max_tokens=4096, temperature=0.3)
    return res.strip()


def synthesize_speaker_notes(transcript: str, speaker_name: str) -> str:
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
        "Chỉ trả về nội dung Markdown hoàn chỉnh của tài liệu Speaker Notes. Không bọc trong code block lớn."
    )
    res = ai.chat(prompt, model="gemini-2.5-flash", max_tokens=2048, temperature=0.3)
    return res.strip()


def main():
    if len(sys.argv) < 2:
        print("Usage: python watch_video.py <video_url_or_path> [output_dir]")
        sys.exit(1)

    video_url = sys.argv[1]
    
    # Resolve Output Directory Fallback
    if len(sys.argv) >= 3:
        output_dir = Path(sys.argv[2]).absolute()
    else:
        # Fallback to .md/youtube-learn/ inside workspace
        output_dir = (Path.cwd() / ".md" / "youtube-learn").absolute()

    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"

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
        from ccba_ai import ai
        gateway_key = os.environ.get("AI_GATEWAY_KEY") or os.environ.get("OPENAI_API_KEY")
        if not gateway_key:
            _logger.error("API Key (AI_GATEWAY_KEY / OPENAI_API_KEY) is missing for non-YouTube STT transcription. Aborting execution to save bandwidth.")
            sys.exit(1)

    # 1. Fetch transcript
    _logger.info("Phase 2: Extracting/transcribing audio transcript...")
    transcript = fetch_youtube_transcript(video_url, output_dir)
    
    if not transcript:
        _logger.error("Failed to extract transcript. Exiting.")
        sys.exit(1)

    # Save raw transcript
    transcript_file = output_dir / "raw_transcript.txt"
    transcript_file.write_text(transcript, encoding="utf-8")
    _logger.info(f"Saved raw transcript to {transcript_file.relative_to(Path.cwd())}")

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

    concept_notes = synthesize_concept_notes(transcript, saved_images)
    worldview_notes = synthesize_worldview_notes(transcript, speaker_name, video_title)
    speaker_notes = synthesize_speaker_notes(transcript, speaker_name)

    # Write files
    (output_dir / "notes_concept.md").write_text(concept_notes, encoding="utf-8")
    (output_dir / "notes_worldview.md").write_text(worldview_notes, encoding="utf-8")
    (output_dir / "notes_speaker.md").write_text(speaker_notes, encoding="utf-8")

    _logger.info("All documents synthesized and saved successfully!")
    print(f"\n🎉 CCBA Belief Archaeology completed successfully!")
    print(f"📁 Output files saved at: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
