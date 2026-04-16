"""
Universal LLM Converter — via AI Gateway.

All models accessed through a single AI Gateway endpoint (LiteLLM on Server Spark).
No need for separate provider routing — the gateway handles it.
"""

import asyncio
import logging
import time
import warnings
from pathlib import Path
from typing import Any

from mdconverter.config import get_settings
from mdconverter.core.base import BaseConverter, ConversionResult, ConversionStatus
from mdconverter.core.llm import GenerationConfig
from mdconverter.providers.gemini import GatewayProvider

logger = logging.getLogger(__name__)

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
        settings = get_settings()
        self.models = models or settings.models
        self.gateway_url = gateway_url
        self.system_prompt: str | None = None

    def supports(self, file_extension: str) -> bool:
        """Check if extension is supported."""
        return file_extension.lower() in self.SUPPORTED_EXTENSIONS

    # Chunking thresholds
    CHUNK_SIZE_PAGES: int = 15  # pages per chunk
    CHUNK_MIN_PAGES: int = 20  # only chunk PDFs larger than this

    async def convert(self, source_path: Path) -> ConversionResult:
        """Convert document using AI Gateway.

        For large PDFs (> CHUNK_MIN_PAGES), splits the document into
        chunks of CHUNK_SIZE_PAGES and converts each chunk separately,
        then merges the results.
        """
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

        # M3 fix: Non-blocking file read
        try:
            file_bytes = await asyncio.to_thread(source_path.read_bytes)
            mime_type = MIME_TYPES.get(source_path.suffix.lower(), "application/octet-stream")
        except Exception as e:
            return ConversionResult(
                source_path=source_path,
                status=ConversionStatus.FAILED,
                error_message=f"Read error: {e}",
            )

        # Check if chunking is needed (only for PDFs)
        if source_path.suffix.lower() == ".pdf":
            page_count = await asyncio.to_thread(self._get_pdf_page_count, source_path)
            if page_count and page_count > self.CHUNK_MIN_PAGES:
                logger.info(
                    "PDF has %d pages (>%d), using chunked conversion",
                    page_count,
                    self.CHUNK_MIN_PAGES,
                )
                return await self._convert_chunked(source_path, page_count, start_time)

        # Standard single-shot conversion
        return await self._convert_single(source_path, file_bytes, mime_type, start_time)

    async def _convert_single(
        self,
        source_path: Path,
        file_bytes: bytes,
        mime_type: str,
        start_time: float,
    ) -> ConversionResult:
        """Convert a single document (or chunk) via the model fallback chain."""
        settings = get_settings()
        prompt = self._get_conversion_prompt()
        gen_config = GenerationConfig(
            temperature=settings.temperature,
            max_output_tokens=settings.max_output_tokens,
            timeout_seconds=settings.timeout_seconds,
        )

        models_tried: list[str] = []
        errors_per_model: dict[str, str] = {}

        async with GatewayProvider(gateway_url=self.gateway_url) as provider:
            for model in self.models:
                models_tried.append(model)
                try:
                    content = await provider.generate(
                        prompt, file_bytes, mime_type, model, gen_config
                    )

                    if content and len(content) > settings.min_content_length:
                        output_path = self.get_output_path(source_path)
                        tool_name = f"llm/{model}"

                        # H1: Extract VN Legal metadata if applicable
                        metadata = self._extract_metadata(content, source_path)
                        final_content = self.add_frontmatter(
                            content, source_path, tool_name, metadata=metadata
                        )
                        await asyncio.to_thread(output_path.write_text, final_content, "utf-8")

                        return ConversionResult(
                            source_path=source_path,
                            output_path=output_path,
                            status=ConversionStatus.SUCCESS,
                            tool_used=tool_name,
                            content=final_content,
                            quality_score=self._calculate_quality(final_content, base_score=50),
                            duration_seconds=time.time() - start_time,
                            metadata={
                                "models_tried": models_tried,
                                "errors_per_model": errors_per_model,
                            },
                        )
                except Exception as e:
                    error_msg = str(e)
                    errors_per_model[model] = error_msg
                    logger.warning("Model %s failed for %s: %s", model, source_path.name, error_msg)
                    continue

        error_summary = "; ".join(f"{m}: {e}" for m, e in errors_per_model.items())
        return ConversionResult(
            source_path=source_path,
            status=ConversionStatus.FAILED,
            tool_used="llm-fallback",
            duration_seconds=time.time() - start_time,
            error_message=f"All models failed. {error_summary}",
            metadata={
                "models_tried": models_tried,
                "errors_per_model": errors_per_model,
            },
        )

    async def _convert_chunked(
        self,
        source_path: Path,
        total_pages: int,
        start_time: float,
    ) -> ConversionResult:
        """Split a large PDF into chunks, convert each, and merge.

        Delegates splitting to ``ccba_pdf_prep.split_pdf`` which writes
        chunk files to a temp directory.  Each chunk is then read back
        as bytes for the existing ``_convert_single`` flow.
        """
        import shutil
        import tempfile

        from ccba_pdf_prep import get_blind_chunks, split_pdf

        ranges = get_blind_chunks(total_pages, chunk_size=self.CHUNK_SIZE_PAGES)
        temp_dir = Path(tempfile.mkdtemp(prefix="llmconv_"))

        try:
            chunk_paths = await asyncio.to_thread(split_pdf, source_path, ranges, temp_dir)
            logger.info(
                "Split %s into %d chunks of ~%d pages",
                source_path.name,
                len(chunk_paths),
                self.CHUNK_SIZE_PAGES,
            )

            merged_parts: list[str] = []
            all_models_tried: list[str] = []
            all_errors: dict[str, str] = {}
            tool_used = "llm-chunked"

            for i, chunk_path in enumerate(chunk_paths):
                logger.info(
                    "Converting chunk %d/%d of %s", i + 1, len(chunk_paths), source_path.name
                )
                chunk_bytes = await asyncio.to_thread(chunk_path.read_bytes)
                result = await self._convert_single(
                    source_path, chunk_bytes, "application/pdf", start_time
                )

                if result.is_success and result.content:
                    # Strip frontmatter from chunks (only add to final)
                    content = self._strip_frontmatter(result.content)
                    merged_parts.append(f"<!-- chunk {i + 1}/{len(chunk_paths)} -->\n{content}")
                    if result.tool_used:
                        tool_used = result.tool_used  # Use last successful model
                else:
                    # Record chunk failure but continue
                    all_errors[f"chunk_{i + 1}"] = result.error_message or "unknown error"
                    merged_parts.append(
                        f"\n<!-- chunk {i + 1}/{len(chunk_paths)}: CONVERSION FAILED -->\n"
                    )

                all_models_tried.extend(result.metadata.get("models_tried", []))
                all_errors.update(result.metadata.get("errors_per_model", {}))

            # Merge results
            merged_content = "\n\n".join(merged_parts)

            if not merged_content.strip():
                return ConversionResult(
                    source_path=source_path,
                    status=ConversionStatus.FAILED,
                    tool_used=tool_used,
                    duration_seconds=time.time() - start_time,
                    error_message="All chunks failed",
                    metadata={"models_tried": all_models_tried, "errors_per_model": all_errors},
                )

            # Add frontmatter to merged result
            metadata = self._extract_metadata(merged_content, source_path)
            final_content = self.add_frontmatter(
                merged_content, source_path, f"{tool_used}/chunked", metadata=metadata
            )
            output_path = self.get_output_path(source_path)
            await asyncio.to_thread(output_path.write_text, final_content, "utf-8")

            return ConversionResult(
                source_path=source_path,
                output_path=output_path,
                status=ConversionStatus.SUCCESS,
                tool_used=f"{tool_used}/chunked",
                content=final_content,
                quality_score=self._calculate_quality(final_content, base_score=50),
                duration_seconds=time.time() - start_time,
                metadata={
                    "models_tried": list(set(all_models_tried)),
                    "errors_per_model": all_errors,
                    "chunks": len(chunk_paths),
                    "total_pages": total_pages,
                },
            )
        finally:
            await asyncio.to_thread(shutil.rmtree, temp_dir, True)

    # ------------------------------------------------------------------
    # PDF helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_pdf_page_count(source_path: Path) -> int | None:
        """Get page count from a PDF file path."""
        try:
            import fitz

            doc = fitz.open(str(source_path))
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return None

    @staticmethod
    def _strip_frontmatter(content: str) -> str:
        """Remove YAML frontmatter from content if present."""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content

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

    @staticmethod
    def _extract_metadata(content: str, source_path: Path) -> dict[str, str] | None:
        """Extract VN Legal metadata if applicable, else return None."""
        from mdconverter.plugins.vn_legal.detector import is_legal_document
        from mdconverter.plugins.vn_legal.metadata import extract_vn_legal_metadata

        if is_legal_document(content):
            return extract_vn_legal_metadata(content, source_path)
        return None


# L1 fix: Backward compatibility alias with deprecation warning
class GeminiConverter(LLMConverter):
    """Deprecated: Use ``LLMConverter`` instead."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            "GeminiConverter is deprecated, use LLMConverter instead",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
