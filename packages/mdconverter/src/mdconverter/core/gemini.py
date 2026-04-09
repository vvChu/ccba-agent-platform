"""
Universal LLM Converter — via AI Gateway.

All models accessed through a single AI Gateway endpoint (LiteLLM on Server Spark).
No need for separate provider routing — the gateway handles it.
"""

import time
from pathlib import Path

from mdconverter.config import settings
from mdconverter.core.base import BaseConverter, ConversionResult, ConversionStatus
from mdconverter.core.llm import GenerationConfig
from mdconverter.providers.gemini import GeminiProvider

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


class LLMConverter(BaseConverter):
    """
    Universal LLM-based Document Converter.

    All models are accessed through the unified AI Gateway.
    Uses fallback chain for reliability.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".png", ".jpg", ".jpeg"}

    def __init__(
        self,
        output_dir: Path | None = None,
        gateway_url: str | None = None,
        models: list[str] | None = None,
    ) -> None:
        """Initialize converter."""
        super().__init__(output_dir)
        self.models = models or settings.models

        # Single provider — AI Gateway handles all model routing
        self.provider = GeminiProvider(gateway_url=gateway_url)

    def supports(self, file_extension: str) -> bool:
        """Check if extension is supported."""
        return file_extension.lower() in self.SUPPORTED_EXTENSIONS

    async def convert(self, source_path: Path) -> ConversionResult:
        """Convert document using AI Gateway."""
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
            mime_type = MIME_TYPES.get(source_path.suffix.lower(), "application/octet-stream")
            
            # PDF Chunking Logic
            if source_path.suffix.lower() == ".pdf":
                try:
                    from pypdf import PdfReader, PdfWriter
                    import io
                    
                    reader = PdfReader(source_path)
                    total_pages = len(reader.pages)
                    chunk_size = settings.pdf_max_pages_single_pass
                    file_chunks = []
                    
                    if total_pages > chunk_size:
                        for i in range(0, total_pages, chunk_size):
                            writer = PdfWriter()
                            for j in range(i, min(i + chunk_size, total_pages)):
                                writer.add_page(reader.pages[j])
                            chunk_io = io.BytesIO()
                            writer.write(chunk_io)
                            file_chunks.append(chunk_io.getvalue())
                    else:
                        file_chunks.append(source_path.read_bytes())
                except ImportError:
                    # Fallback if pypdf is not installed
                    file_chunks = [source_path.read_bytes()]
            else:
                file_chunks = [source_path.read_bytes()]
                
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
            timeout_seconds=settings.timeout_seconds,
        )

        # Try each model in fallback chain (all via same gateway)
        last_error = ""
        for model in self.models:
            all_content = []
            success = True
            try:
                for chunk_bytes in file_chunks:
                    content = await self.provider.generate(
                        prompt, chunk_bytes, mime_type, model, gen_config
                    )
                    if not content:
                        success = False
                        last_error = "Model returned empty content."
                        break
                    all_content.append(content)
                
                if success:
                    merged_content = "\n\n".join(all_content)
                    if len(merged_content) > settings.min_content_length:
                        output_path = self.get_output_path(source_path)
                        tool_name = f"llm/{model}"
                        final_content = self.add_frontmatter(merged_content, source_path, tool_name)
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
        return """Convert this ENTIRE document to clean, well-structured Markdown.

CRITICAL RULES:
1. **CONVERT ALL CONTENT** - Do NOT stop early, do NOT summarize, do NOT skip ANY pages
2. Use proper heading hierarchy (# for main title, ## for Chương, ### for Điều, #### for Mục)
3. Format ALL tables using Markdown table syntax with proper alignment
4. Keep ALL original numbering, bullet points, and list formatting
5. For Vietnamese text: maintain ALL diacritics and special characters
6. Output ONLY raw Markdown - no code blocks, no explanations

VIETNAMESE LEGAL DOCUMENT STRUCTURE:
- Keep "Chương I, II, III..." as ## headings
- Keep "Điều 1, 2, 3..." as ### headings
- Keep "Mục I, II, III..." as #### headings
- Keep numbered lists (1., 2., 3. or a), b), c)) as proper lists
- Preserve all Phụ lục (Appendix) content at the end

IMPORTANT: This document may have 20-50+ pages. You MUST convert EVERY page from start to finish.
Continue until you reach the very end of the document including all Phụ lục (Appendices).

START CONVERSION - CONVERT EVERYTHING:"""

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


# Backward compatibility alias
GeminiConverter = LLMConverter
