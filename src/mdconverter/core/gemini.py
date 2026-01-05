"""
Gemini API converter using Antigravity Proxy.

Supports PDF, DOCX, images, and other document formats.
"""

import base64
import time
from pathlib import Path
from typing import Any

import httpx

from mdconverter.config import settings
from mdconverter.core.base import BaseConverter, ConversionResult, ConversionStatus

# Supported MIME types
MIME_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".html": "text/html",
    ".htm": "text/html",
}


class GeminiConverter(BaseConverter):
    """Document converter using Google Gemini API via Antigravity Proxy."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".png", ".jpg", ".jpeg"}

    def __init__(
        self,
        output_dir: Path | None = None,
        proxy_url: str | None = None,
        models: list[str] | None = None,
    ) -> None:
        """Initialize Gemini converter."""
        super().__init__(output_dir)
        self.proxy_url = proxy_url or settings.antigravity_proxy
        self.models = models or settings.models
        self.client = httpx.Client(timeout=settings.timeout_seconds)

    def supports(self, file_extension: str) -> bool:
        """Check if extension is supported."""
        return file_extension.lower() in self.SUPPORTED_EXTENSIONS

    def convert(self, source_path: Path) -> ConversionResult:
        """Convert document using Gemini API."""
        start_time = time.time()

        if not source_path.exists():
            return ConversionResult(
                source_path=source_path,
                status=ConversionStatus.FAILED,
                error_message=f"File not found: {source_path}",
            )

        if not self.supports(source_path.suffix):
            return ConversionResult(
                source_path=source_path,
                status=ConversionStatus.SKIPPED,
                error_message=f"Unsupported extension: {source_path.suffix}",
            )

        # Try each model in fallback chain
        for model in self.models:
            try:
                content = self._convert_with_model(source_path, model)
                if content and len(content) > settings.min_content_length:
                    output_path = self.get_output_path(source_path)
                    final_content = self.add_frontmatter(content, source_path, f"gemini/{model}")
                    output_path.write_text(final_content, encoding="utf-8")

                    return ConversionResult(
                        source_path=source_path,
                        output_path=output_path,
                        status=ConversionStatus.SUCCESS,
                        tool_used=f"gemini/{model}",
                        content=final_content,
                        quality_score=self._calculate_quality(final_content),
                        duration_seconds=time.time() - start_time,
                    )
            except Exception:
                continue  # Try next model

        return ConversionResult(
            source_path=source_path,
            status=ConversionStatus.FAILED,
            tool_used="gemini",
            duration_seconds=time.time() - start_time,
            error_message="All models failed",
        )

    def _convert_with_model(self, source_path: Path, model: str) -> str:
        """Convert using specific model."""
        file_bytes = source_path.read_bytes()
        file_b64 = base64.b64encode(file_bytes).decode("utf-8")
        mime_type = MIME_TYPES.get(source_path.suffix.lower(), "application/octet-stream")

        prompt = self._get_conversion_prompt()

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": file_b64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": settings.temperature,
                "maxOutputTokens": settings.max_output_tokens,
            },
        }

        url = f"{self.proxy_url}/v1beta/models/{model}:generateContent"
        
        headers = {}
        if settings.antigravity_access_token:
            headers["Authorization"] = f"Bearer {settings.antigravity_access_token}"

        response = self.client.post(url, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()
        return self._extract_content(data)

    def _get_conversion_prompt(self) -> str:
        """Get the conversion prompt."""
        return """Convert this document to clean, well-structured Markdown.

RULES:
1. Preserve all content accurately - do NOT summarize or omit
2. Use proper heading hierarchy (# for main title, ## for sections, etc.)
3. Format tables using Markdown table syntax
4. Keep original numbering and bullet points
5. For Vietnamese text: maintain diacritics and special characters
6. Output ONLY Markdown, no explanations or code blocks wrapping

START CONVERSION NOW:"""

    def _extract_content(self, response_data: dict[str, Any]) -> str:
        """Extract text content from Gemini response."""
        try:
            candidates = response_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return str(parts[0].get("text", ""))
        except (KeyError, IndexError):
            pass
        return ""

    def _calculate_quality(self, content: str) -> int:
        """Calculate quality score (0-100)."""
        score = 50  # Base score

        # Length bonus
        if len(content) > 1000:
            score += 10
        if len(content) > 5000:
            score += 10

        # Structure bonus
        if "##" in content:
            score += 10
        if "###" in content:
            score += 5

        # Table bonus
        if "|" in content and "-|-" in content:
            score += 10

        # Vietnamese content bonus
        vn_chars = sum(1 for c in content if ord(c) > 127)
        if vn_chars / max(len(content), 1) > 0.1:
            score += 5

        return min(score, 100)
