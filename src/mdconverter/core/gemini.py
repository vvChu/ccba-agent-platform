"""
Universal LLM Converter.

Uses Provider pattern to support Gemini, DeepSeek, and Groq.
"""

import time
from pathlib import Path

from mdconverter.config import settings
from mdconverter.core.base import BaseConverter, ConversionResult, ConversionStatus
from mdconverter.core.llm import GenerationConfig, LLMProvider
from mdconverter.providers.gemini import GeminiProvider
from mdconverter.providers.openai import OpenAIProvider

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
    """
    Universal Document Converter.

    Legacy name 'GeminiConverter' kept for backward compatibility,
    but now supports multiple backends via Providers.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".png", ".jpg", ".jpeg"}

    def __init__(
        self,
        output_dir: Path | None = None,
        proxy_url: str | None = None,
        models: list[str] | None = None,
    ) -> None:
        """Initialize converter."""
        super().__init__(output_dir)
        self.models = models or settings.models

        # Initialize Providers
        self.gemini_provider = GeminiProvider(proxy_url=proxy_url)

        # DeepSeek (OpenAI Compatible)
        self.deepseek_provider = None
        if settings.deepseek_api_key:
            self.deepseek_provider = OpenAIProvider(
                base_url="https://api.deepseek.com",
                api_key=settings.deepseek_api_key
            )

        # Groq (OpenAI Compatible)
        self.groq_provider = None
        if settings.groq_api_key:
            self.groq_provider = OpenAIProvider(
                base_url="https://api.groq.com/openai/v1",
                api_key=settings.groq_api_key
            )

    def _get_provider_for_model(self, model: str) -> tuple[LLMProvider | None, str]:
        """Return (provider, model_name) based on model string."""
        if "deepseek" in model:
            return self.deepseek_provider, model
        elif "llama" in model or "mixtral" in model or "gemma" in model:
             # Groq models usually like 'llama-3.3-70b-versatile'
            return self.groq_provider, model
        else:
            # Default to Gemini
            return self.gemini_provider, model

    def supports(self, file_extension: str) -> bool:
        """Check if extension is supported."""
        return file_extension.lower() in self.SUPPORTED_EXTENSIONS

    async def convert(self, source_path: Path) -> ConversionResult:
        """Convert document using LLM Providers."""
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

        # Read file once
        try:
            file_bytes = source_path.read_bytes()
            mime_type = MIME_TYPES.get(source_path.suffix.lower(), "application/octet-stream")
        except Exception as e:
             return ConversionResult(
                source_path=source_path,
                status=ConversionStatus.FAILED,
                error_message=f"Read error: {e}",
            )

        prompt = self._get_conversion_prompt()
        gen_config = GenerationConfig(
            temperature=settings.temperature,
            max_output_tokens=settings.max_output_tokens,
            timeout_seconds=settings.timeout_seconds
        )

        # Try each model in fallback chain
        last_error = ""
        for model in self.models:
            provider, model_name = self._get_provider_for_model(model)
            if not provider:
                # Skip if provider not configured (no key)
                continue

            try:
                content = await provider.generate(prompt, file_bytes, mime_type, model_name, gen_config)

                if content and len(content) > settings.min_content_length:
                    output_path = self.get_output_path(source_path)
                    tool_name = f"llm/{model}"
                    final_content = self.add_frontmatter(content, source_path, tool_name)
                    output_path.write_text(final_content, encoding="utf-8")

                    return ConversionResult(
                        source_path=source_path,
                        output_path=output_path,
                        status=ConversionStatus.SUCCESS,
                        tool_used=tool_name,
                        content=final_content,
                        quality_score=self._calculate_quality(final_content),
                        duration_seconds=time.time() - start_time,
                    )
            except Exception as e:
                last_error = str(e)
                continue  # Try next model

        return ConversionResult(
            source_path=source_path,
            status=ConversionStatus.FAILED,
            tool_used="llm-fallback",
            duration_seconds=time.time() - start_time,
            error_message=f"All models failed. Last error: {last_error}",
        )

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
