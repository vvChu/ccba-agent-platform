import argparse
import asyncio
import io
import sys
from pathlib import Path
from typing import Any

# Cấu hình UTF-8 cho console đầu ra trên Windows để tránh lỗi mã hóa ký tự tiếng Việt
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


import importlib.util

# Import dynamically from our own package
from . import (
    check_auth,
    delete_notebook,
    delete_source,
    extract_and_summarize,
    handle_artifact_flow,
    list_notebooks,
    list_sources,
    query_rag,
    share_notebook,
)
from ._client import (
    InfographicDetail,
    InfographicOrientation,
    InfographicStyle,
    QuizDifficulty,
    QuizQuantity,
    ReportFormat,
    SlideDeckFormat,
    SlideDeckLength,
    VideoFormat,
    VideoStyle,
)

# Optional skill_generator import (no sys.path mutation)
_SCRIPTS_DIR = Path(__file__).parents[4] / "scripts"
_skill_gen_path = _SCRIPTS_DIR / "skill_generator.py"
if _skill_gen_path.exists():
    try:
        _spec = importlib.util.spec_from_file_location("skill_generator", _skill_gen_path)
        skill_generator = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(skill_generator)
    except Exception:
        skill_generator = None
else:
    skill_generator = None


def main() -> int:
    parser = argparse.ArgumentParser(description="CCBA Platform NotebookLM Helper Wrapper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command check-auth
    subparsers.add_parser("check-auth", help="Kiểm tra trạng thái đăng nhập Google")

    # Sub-command extract
    parser_extract = subparsers.add_parser("extract", help="Import nguồn và kết xuất tóm tắt")
    parser_extract.add_argument(
        "--source", required=True, help="URL Youtube/Web hoặc đường dẫn file cục bộ"
    )
    parser_extract.add_argument(
        "--output", default=".md/extracted_docs/summaries/", help="Thư mục đầu ra"
    )

    # Sub-command query
    parser_query = subparsers.add_parser("query", help="Truy vấn RAG cô lập nguồn")
    parser_query.add_argument("--source", required=True, help="Tài liệu nguồn cần lọc RAG")
    parser_query.add_argument("--prompt", required=True, help="Câu hỏi truy vấn")

    # Sub-command audio
    parser_audio = subparsers.add_parser("audio", help="Sinh và tải Podcast Audio Overview")
    parser_audio.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_audio.add_argument("--output", default=".md/scratch/audio/", help="Thư mục lưu tệp mp3")

    # Sub-command quiz
    parser_quiz = subparsers.add_parser("quiz", help="Sinh quiz trắc nghiệm từ tài liệu")
    parser_quiz.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_quiz.add_argument(
        "--output", default=".md/scratch/quizzes/", help="Thư mục lưu tệp json"
    )
    parser_quiz.add_argument(
        "--quantity", choices=["fewer", "standard"], default="standard", help="Số lượng câu hỏi"
    )
    parser_quiz.add_argument(
        "--difficulty", choices=["easy", "medium", "hard"], default="medium", help="Độ khó"
    )

    # Sub-command slides
    parser_slides = subparsers.add_parser("slides", help="Sinh Slide thuyết trình dạng PDF")
    parser_slides.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_slides.add_argument(
        "--output", default=".md/scratch/slides/", help="Thư mục lưu tệp pdf"
    )
    parser_slides.add_argument(
        "--format", choices=["detailed", "presenter"], default="detailed", help="Định dạng slide"
    )
    parser_slides.add_argument(
        "--length", choices=["default", "short"], default="default", help="Độ dài"
    )
    parser_slides.add_argument("--language", default="en", help="Ngôn ngữ sinh slide")

    # Sub-command mindmap
    parser_mindmap = subparsers.add_parser("mindmap", help="Sinh sơ đồ tư duy dạng JSON")
    parser_mindmap.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_mindmap.add_argument(
        "--output", default=".md/scratch/mindmaps/", help="Thư mục lưu tệp json"
    )

    # Sub-command infographic
    parser_infographic = subparsers.add_parser("infographic", help="Sinh Infographic dạng PDF")
    parser_infographic.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_infographic.add_argument(
        "--output", default=".md/scratch/infographics/", help="Thư mục lưu"
    )
    parser_infographic.add_argument(
        "--orientation",
        choices=["portrait", "landscape"],
        default="portrait",
        help="Hướng khổ giấy",
    )
    parser_infographic.add_argument(
        "--detail",
        choices=["default", "summary", "detailed"],
        default="default",
        help="Mức chi tiết",
    )
    parser_infographic.add_argument(
        "--style",
        choices=["modern", "minimal", "colorful"],
        default="modern",
        help="Phong cách thiết kế",
    )

    # Sub-command study-guide
    parser_guide = subparsers.add_parser("study-guide", help="Sinh cẩm nang học tập dạng PDF")
    parser_guide.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_guide.add_argument("--output", default=".md/scratch/study_guides/", help="Thư mục lưu")

    # Sub-command data-table
    parser_table = subparsers.add_parser(
        "data-table", help="Trích xuất bảng dữ liệu cấu trúc dạng CSV"
    )
    parser_table.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_table.add_argument("--output", default=".md/scratch/data_tables/", help="Thư mục lưu")
    parser_table.add_argument("--instructions", default="", help="Chỉ dẫn thêm để trích xuất bảng")

    # Sub-command flashcards
    parser_flash = subparsers.add_parser("flashcards", help="Sinh thẻ ghi nhớ dạng JSON")
    parser_flash.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_flash.add_argument("--output", default=".md/scratch/flashcards/", help="Thư mục lưu")
    parser_flash.add_argument("--quantity", choices=["fewer", "standard"], default="standard")
    parser_flash.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium")

    # Sub-command report
    parser_report = subparsers.add_parser(
        "report", help="Sinh báo cáo chuyên sâu dạng Markdown/PDF"
    )
    parser_report.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_report.add_argument("--output", default=".md/scratch/reports/", help="Thư mục lưu")
    parser_report.add_argument(
        "--format",
        choices=["briefing_doc", "study_guide", "blog_post", "custom"],
        default="briefing_doc",
    )
    parser_report.add_argument("--instructions", default="")

    # Sub-command video
    parser_video = subparsers.add_parser("video", help="Sinh video tóm tắt dạng MP4")
    parser_video.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_video.add_argument("--output", default=".md/scratch/videos/", help="Thư mục lưu")
    parser_video.add_argument(
        "--format", choices=["explainer", "brief", "cinematic"], default="explainer"
    )
    parser_video.add_argument("--style", choices=["modern", "classic"], default="modern")

    # CLI LỆNH QUẢN TRỊ (CRUD CLI)

    # Sub-command list-notebooks
    subparsers.add_parser("list-notebooks", help="Liệt kê tất cả các notebook hiện có")

    # Sub-command delete-notebook
    parser_del_nb = subparsers.add_parser("delete-notebook", help="Xóa một notebook cụ thể")
    parser_del_nb.add_argument("--notebook-id", required=True, help="Notebook ID cần xóa")

    # Sub-command share-notebook
    parser_share = subparsers.add_parser(
        "share-notebook", help="Kích hoạt chia sẻ notebook và lấy Share URL"
    )
    parser_share.add_argument("--notebook-id", default=None, help="Notebook ID (tùy chọn)")

    # Sub-command list-sources
    parser_list_src = subparsers.add_parser("list-sources", help="Liệt kê các nguồn trong notebook")
    parser_list_src.add_argument("--notebook-id", default=None, help="Notebook ID (tùy chọn)")

    # Sub-command delete-source
    parser_del_src = subparsers.add_parser("delete-source", help="Xóa một nguồn cụ thể")
    parser_del_src.add_argument("--source-id", required=True, help="Source ID cần xóa")
    parser_del_src.add_argument("--notebook-id", default=None, help="Notebook ID (tùy chọn)")

    # Sub-command create-skill
    parser_create_skill = subparsers.add_parser(
        "create-skill", help="Tự động tạo Skill từ tệp Python script"
    )
    parser_create_skill.add_argument(
        "--script", required=True, help="Đường dẫn file script Python nguồn"
    )
    parser_create_skill.add_argument("--name", default=None, help="Tên Skill muốn tạo (tùy chọn)")

    # Sub-command sync-skills
    subparsers.add_parser("sync-skills", help="Đồng bộ tự động các cli_spec.yaml từ scripts")

    args = parser.parse_args()

    # Set event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        if args.command == "check-auth":
            return int(loop.run_until_complete(check_auth()))
        elif args.command == "extract":
            return int(loop.run_until_complete(extract_and_summarize(args.source, args.output)))
        elif args.command == "query":
            return int(loop.run_until_complete(query_rag(args.source, args.prompt)))
        elif args.command == "audio":
            return int(
                loop.run_until_complete(
                    handle_artifact_flow(
                        task_type="audio",
                        source_path=args.source,
                        output_dir=args.output,
                        output_filename_pattern="audio_overview_{source_id}.mp3",
                    )
                )
            )
        elif args.command == "quiz":
            qty = map_quiz_quantity(args.quantity)
            diff = map_quiz_difficulty(args.difficulty)
            return int(
                loop.run_until_complete(
                    handle_artifact_flow(
                        task_type="quiz",
                        source_path=args.source,
                        output_dir=args.output,
                        output_filename_pattern="quiz_{source_id}.json",
                        output_format="json",
                        quantity=qty,
                        difficulty=diff,
                    )
                )
            )
        elif args.command == "slides":
            fmt = map_slide_format(args.format)
            length = map_slide_length(args.length)
            return int(
                loop.run_until_complete(
                    handle_artifact_flow(
                        task_type="slides",
                        source_path=args.source,
                        output_dir=args.output,
                        output_filename_pattern="slides_{source_id}.pdf",
                        output_format="pdf",
                        language=args.language,
                        slide_format=fmt,
                        slide_length=length,
                    )
                )
            )
        elif args.command == "mindmap":
            return int(
                loop.run_until_complete(
                    handle_artifact_flow(
                        task_type="mindmap",
                        source_path=args.source,
                        output_dir=args.output,
                        output_filename_pattern="mindmap_{source_id}.json",
                    )
                )
            )
        elif args.command == "infographic":
            orient = map_info_orientation(args.orientation)
            det = map_info_detail(args.detail)
            sty = map_info_style(args.style)
            return int(
                loop.run_until_complete(
                    handle_artifact_flow(
                        task_type="infographic",
                        source_path=args.source,
                        output_dir=args.output,
                        output_filename_pattern="infographic_{source_id}.pdf",
                        orientation=orient,
                        detail_level=det,
                        style=sty,
                    )
                )
            )
        elif args.command == "study-guide":
            return int(
                loop.run_until_complete(
                    handle_artifact_flow(
                        task_type="study-guide",
                        source_path=args.source,
                        output_dir=args.output,
                        output_filename_pattern="study_guide_{source_id}.md",
                    )
                )
            )
        elif args.command == "data-table":
            return int(
                loop.run_until_complete(
                    handle_artifact_flow(
                        task_type="data-table",
                        source_path=args.source,
                        output_dir=args.output,
                        output_filename_pattern="data_table_{source_id}.csv",
                        instructions=args.instructions,
                    )
                )
            )
        elif args.command == "flashcards":
            qty = map_quiz_quantity(args.quantity)
            diff = map_quiz_difficulty(args.difficulty)
            return int(
                loop.run_until_complete(
                    handle_artifact_flow(
                        task_type="flashcards",
                        source_path=args.source,
                        output_dir=args.output,
                        output_filename_pattern="flashcards_{source_id}.json",
                        output_format="json",
                        quantity=qty,
                        difficulty=diff,
                    )
                )
            )
        elif args.command == "report":
            fmt = map_report_format(args.format)
            return int(
                loop.run_until_complete(
                    handle_artifact_flow(
                        task_type="report",
                        source_path=args.source,
                        output_dir=args.output,
                        output_filename_pattern="report_{source_id}.md",
                        report_format=fmt,
                        extra_instructions=args.instructions,
                    )
                )
            )
        elif args.command == "video":
            fmt = map_video_format(args.format)
            sty = map_video_style(args.style)
            return int(
                loop.run_until_complete(
                    handle_artifact_flow(
                        task_type="video",
                        source_path=args.source,
                        output_dir=args.output,
                        output_filename_pattern="video_{source_id}.mp4",
                        video_format=fmt,
                        video_style=sty,
                    )
                )
            )

        elif args.command == "list-notebooks":
            return int(loop.run_until_complete(list_notebooks()))
        elif args.command == "delete-notebook":
            return int(loop.run_until_complete(delete_notebook(args.notebook_id)))
        elif args.command == "share-notebook":
            return int(loop.run_until_complete(share_notebook(args.notebook_id)))
        elif args.command == "list-sources":
            return int(loop.run_until_complete(list_sources(args.notebook_id)))
        elif args.command == "delete-source":
            return int(loop.run_until_complete(delete_source(args.source_id, args.notebook_id)))
        elif args.command == "create-skill":
            if skill_generator:
                return int(skill_generator.create_skill_from_script(args.script, args.name))
            print("ERROR: Thư viện skill_generator không khả dụng.", file=sys.stderr)
            return 1
        elif args.command == "sync-skills":
            if skill_generator:
                return int(skill_generator.sync_all_skills())
            print("ERROR: Thư viện skill_generator không khả dụng.", file=sys.stderr)
            return 1
    finally:
        loop.close()

    return 1


# ---------------------------------------------------------------------------
# CLI Argument Mappers
# Translates string inputs from argparse into typing-safe enums.
# ---------------------------------------------------------------------------


def map_quiz_quantity(q: str) -> Any:
    if QuizQuantity is None:
        return None
    q_map = {"fewer": QuizQuantity.FEWER, "standard": QuizQuantity.STANDARD}
    return q_map.get(q.lower(), QuizQuantity.STANDARD)


def map_quiz_difficulty(d: str) -> Any:
    if QuizDifficulty is None:
        return None
    d_map = {
        "easy": QuizDifficulty.EASY,
        "medium": QuizDifficulty.MEDIUM,
        "hard": QuizDifficulty.HARD,
    }
    return d_map.get(d.lower(), QuizDifficulty.MEDIUM)


def map_slide_format(f: str) -> Any:
    if SlideDeckFormat is None:
        return None
    f_map = {
        "detailed": SlideDeckFormat.DETAILED_DECK,
        "presenter": SlideDeckFormat.PRESENTER_SLIDES,
    }
    return f_map.get(f.lower(), SlideDeckFormat.DETAILED_DECK)


def map_slide_length(slide_len: str) -> Any:
    if SlideDeckLength is None:
        return None
    l_map = {"default": SlideDeckLength.DEFAULT, "short": SlideDeckLength.SHORT}
    return l_map.get(slide_len.lower(), SlideDeckLength.DEFAULT)


def map_info_orientation(o: str) -> Any:
    if InfographicOrientation is None:
        return None
    o_map = {
        "portrait": InfographicOrientation.PORTRAIT,
        "landscape": InfographicOrientation.LANDSCAPE,
    }
    return o_map.get(o.lower(), InfographicOrientation.PORTRAIT)


def map_info_detail(d: str) -> Any:
    if InfographicDetail is None:
        return None
    d_map = {
        "default": InfographicDetail.STANDARD,
        "summary": InfographicDetail.CONCISE,
        "detailed": InfographicDetail.DETAILED,
    }
    return d_map.get(d.lower(), InfographicDetail.STANDARD)


def map_info_style(s: str) -> Any:
    if InfographicStyle is None:
        return None
    s_map = {
        "modern": InfographicStyle.PROFESSIONAL,
        "minimal": InfographicStyle.EDITORIAL,
        "colorful": InfographicStyle.INSTRUCTIONAL,
    }
    return s_map.get(s.lower(), InfographicStyle.AUTO_SELECT)


def map_report_format(f: str) -> Any:
    if ReportFormat is None:
        return None
    f_map = {
        "briefing_doc": ReportFormat.BRIEFING_DOC,
        "study_guide": ReportFormat.STUDY_GUIDE,
        "blog_post": ReportFormat.BLOG_POST,
        "custom": ReportFormat.CUSTOM,
    }
    return f_map.get(f.lower(), ReportFormat.BRIEFING_DOC)


def map_video_format(f: str) -> Any:
    if VideoFormat is None:
        return None
    f_map = {
        "explainer": VideoFormat.EXPLAINER,
        "brief": VideoFormat.BRIEF,
        "cinematic": VideoFormat.CINEMATIC,
    }
    return f_map.get(f.lower(), VideoFormat.EXPLAINER)


def map_video_style(s: str) -> Any:
    if VideoStyle is None:
        return None
    s_map = {"modern": VideoStyle.AUTO_SELECT, "classic": VideoStyle.CLASSIC}
    return s_map.get(s.lower(), VideoStyle.AUTO_SELECT)


if __name__ == "__main__":
    sys.exit(main())
