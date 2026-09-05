"""CCBA Dual-Track Questionnaire Engine v2.0.

Provides multi-format document rendering (.docx, HTML, micro-chat, email)
and two-way reply loops for questionnaires.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from pathlib import Path

from .chat_renderer import render_chat_snippet
from .docx_renderer import render_questionnaire_docx
from .email_renderer import render_email_table
from .html_renderer import render_questionnaire_html
from .models import (
    QuestionItem,
    QuestionnaireData,
    QuestionnaireMetadata,
    QuestionOption,
    QuestionType,
)
from .parser import parse_questionnaire_markdown
from .reply_engine import apply_questionnaire_reply, parse_reply_string


class QuestionnaireEngine:
    """High-level facade for CCBA Dual-Track Questionnaire operations."""

    @staticmethod
    def parse(source: str | Path) -> QuestionnaireData:
        """Parse a questionnaire from markdown text or file path."""
        return parse_questionnaire_markdown(source)

    @staticmethod
    def export_all(
        source: str | Path,
        output_dir: str | Path | None = None,
        base_url: str = "",
    ) -> dict[str, Path]:
        """Export all supported formats (.docx, .html, .chat.txt, .email.html).

        Args:
            source: Source markdown file path or text.
            output_dir: Target output directory. If None, uses parent dir of source.
            base_url: Optional base web URL for QR code and links.

        Returns:
            Dictionary mapping format name to output Path.
        """
        data = parse_questionnaire_markdown(source)
        if isinstance(source, Path) or (isinstance(source, str) and Path(source).is_file()):
            src_path = Path(source)
            out_dir = Path(output_dir) if output_dir else src_path.parent
            base_stem = src_path.stem
        else:
            out_dir = Path(output_dir or ".")
            base_stem = f"questionnaire_{data.metadata.doc_code.lower().replace('-', '_')}"

        out_dir.mkdir(parents=True, exist_ok=True)
        results: dict[str, Path] = {}

        # 1. Word DOCX
        docx_path = out_dir / f"{base_stem}.docx"
        results["docx"] = render_questionnaire_docx(data, docx_path)

        # 2. Standalone HTML Form
        html_path = out_dir / f"{base_stem}.html"
        results["html"] = render_questionnaire_html(data, html_path, base_url=base_url)

        # 3. Micro-Chat Snippet
        chat_path = out_dir / f"{base_stem}.chat.txt"
        chat_text = render_chat_snippet(data)
        chat_path.write_text(chat_text, encoding="utf-8")
        results["chat"] = chat_path

        # 4. Email HTML Table
        email_path = out_dir / f"{base_stem}.email.html"
        email_html = render_email_table(data)
        email_path.write_text(email_html, encoding="utf-8")
        results["email"] = email_path

        return results

    @staticmethod
    def reply(
        source_file: str | Path,
        reply_str: str,
        resolved_by: str = "Chủ đầu tư / Ban QLDA",
        output_file: str | Path | None = None,
    ) -> Path:
        """Apply a reply string to a questionnaire and update status."""
        return apply_questionnaire_reply(
            source_file=source_file,
            reply_str=reply_str,
            resolved_by=resolved_by,
            output_file=output_file,
        )


__all__ = [
    "QuestionType",
    "QuestionOption",
    "QuestionItem",
    "QuestionnaireMetadata",
    "QuestionnaireData",
    "QuestionnaireEngine",
    "parse_questionnaire_markdown",
    "render_questionnaire_docx",
    "render_questionnaire_html",
    "render_chat_snippet",
    "render_email_table",
    "parse_reply_string",
    "apply_questionnaire_reply",
]
