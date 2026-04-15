"""
Conversion Pipeline — orchestrates convert → post-process → cache.

Extracted from convert_cmd.py (H2 fix) to separate business logic from CLI.
Defines a ``PostProcessor`` Protocol for extensible post-processing (H3 fix).
"""

import asyncio
import logging
from pathlib import Path
from typing import Protocol, runtime_checkable

from mdconverter.core.base import BaseConverter, ConversionResult, ConversionStatus, ConversionTool
from mdconverter.core.cache import ConversionCache

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Post-processor extensibility (replaces dead PluginManager — H3 fix)
# ---------------------------------------------------------------------------
@runtime_checkable
class PostProcessor(Protocol):
    """Protocol for document post-processors.

    Implement this to add domain-specific post-processing (e.g. VN Legal,
    English academic, etc.).  Add your implementation to
    ``get_default_post_processors()`` or pass via ``ConversionPipeline``.
    """

    def should_process(self, content: str) -> bool:
        """Return True if this processor should run on the given content."""
        ...

    def process(self, content: str) -> str:
        """Apply post-processing rules and return modified content."""
        ...

    def get_summary(self) -> dict[str, int]:
        """Return a summary of fixes applied (rule_name → count)."""
        ...


class VNLegalPostProcessor:
    """Post-processor adapter for Vietnamese legal documents."""

    def __init__(self) -> None:
        from mdconverter.plugins.vn_legal.detector import is_legal_document
        from mdconverter.plugins.vn_legal.processor import VNLegalProcessor

        self._is_legal = is_legal_document
        self._processor = VNLegalProcessor()

    def should_process(self, content: str) -> bool:
        """Check if content is a VN legal document."""
        return self._is_legal(content)

    def process(self, content: str) -> str:
        """Apply VN Legal processing rules."""
        return self._processor.process(content)

    def get_summary(self) -> dict[str, int]:
        """Get fix summary from the underlying processor."""
        return self._processor.get_fix_summary()


def get_default_post_processors() -> list[PostProcessor]:
    """Get the default list of post-processors.

    Add new post-processors here as the system grows (e.g. for English
    documents, academic papers, etc.).

    Returns:
        List of PostProcessor instances.
    """
    return [VNLegalPostProcessor()]  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# Conversion Pipeline
# ---------------------------------------------------------------------------
class ConversionPipeline:
    """Orchestrates file conversion with caching and post-processing.

    Args:
        tool: Which converter to use (auto, llm, pandoc, llamaparse).
        output_dir: Optional output directory for converted files.
        cache: Optional ConversionCache instance (None = no caching).
        post_processors: List of PostProcessor instances. Defaults to
            ``get_default_post_processors()``.
        max_concurrency: Maximum number of concurrent conversions.
    """

    def __init__(
        self,
        tool: ConversionTool | str = ConversionTool.AUTO,
        output_dir: Path | None = None,
        cache: ConversionCache | None = None,
        post_processors: list[PostProcessor] | None = None,
        max_concurrency: int = 10,
    ) -> None:
        self.tool = tool
        self.output_dir = output_dir
        self.cache = cache
        self.post_processors = (
            post_processors if post_processors is not None else get_default_post_processors()
        )
        self._sem = asyncio.Semaphore(max_concurrency)

    async def process_file(self, file: Path) -> ConversionResult:
        """Convert a single file with caching and post-processing.

        For PDF files, runs ``PDFAnalyzer`` first to classify the document
        and select the optimal converter/model.  Drawing PDFs are skipped
        automatically.

        Args:
            file: Path to the source file.

        Returns:
            ConversionResult with status, content, and metadata.
        """
        async with self._sem:
            loop = asyncio.get_running_loop()

            # 0. PDF analysis — classify and auto-select tool
            pdf_report = None
            if file.suffix.lower() == ".pdf":
                pdf_report = await self._analyze_pdf(file, loop)
                if pdf_report and pdf_report.should_skip:
                    return ConversionResult(
                        source_path=file,
                        status=ConversionStatus.SKIPPED,
                        error_message=pdf_report.skip_reason,
                        metadata={"pdf_analysis": pdf_report.to_dict()},
                    )

            # 1. Check cache
            if self.cache:
                cached_content = await loop.run_in_executor(None, self.cache.get, file)
                if cached_content:
                    output_path = self._expected_output_path(file)
                    await loop.run_in_executor(None, self._write_cached, output_path, cached_content)
                    return ConversionResult(
                        source_path=file,
                        output_path=output_path,
                        status=ConversionStatus.SUCCESS,
                        tool_used="cache",
                        content=cached_content,
                    )

            # 2. Create converter — use analyzer recommendation if available
            converter = self._create_converter_for_file(file, pdf_report)
            result = await converter.convert(file)

            # Attach analysis metadata
            if pdf_report:
                result.metadata["pdf_analysis"] = pdf_report.to_dict()

            # 3. Post-process
            if result.is_success and result.content:
                result = await self._apply_post_processors(result)

            # 4. Update cache
            if self.cache and result.is_success and result.content:
                await loop.run_in_executor(
                    None, self.cache.set, file, result.content, result.tool_used
                )

            return result

    async def process_batch(self, files: list[Path]) -> list[ConversionResult]:
        """Convert multiple files concurrently.

        Args:
            files: List of source file paths.

        Returns:
            List of ConversionResult in completion order.
        """
        tasks = [self.process_file(f) for f in files]
        results: list[ConversionResult] = []
        for future in asyncio.as_completed(tasks):
            results.append(await future)
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _analyze_pdf(
        self, file: Path, loop: asyncio.AbstractEventLoop
    ) -> "PDFReport | None":
        """Run PDF analysis in a thread to avoid blocking the event loop."""
        from mdconverter.core.analyzer import PDFAnalyzer, PDFReport

        analyzer = PDFAnalyzer()
        try:
            report: PDFReport = await loop.run_in_executor(None, analyzer.analyze, file)
            logger.info(
                "PDF analysis: %s → %s (confidence %.0f%%, model: %s)",
                file.name,
                report.category.value,
                report.confidence * 100,
                report.recommended_model,
            )
            return report
        except Exception as e:
            logger.warning("PDF analysis failed for %s: %s — using default tool", file.name, e)
            return None

    def _create_converter_for_file(
        self, file: Path, pdf_report: "PDFReport | None" = None
    ) -> "BaseConverter":
        """Create the appropriate converter, optionally guided by PDF analysis.

        When ``pdf_report`` suggests a specific model (e.g. ``ocr-primary``),
        creates an LLMConverter with that model prioritised at the top of
        the fallback chain.
        """
        from mdconverter.core.analyzer import PDFCategory

        # If we have a PDF report and tool is AUTO, use the recommendation
        if (
            pdf_report
            and pdf_report.recommended_model
            and self.tool in (ConversionTool.AUTO, ConversionTool.AUTO.value, "auto")
            and file.suffix.lower() == ".pdf"
        ):
            recommended = pdf_report.recommended_model
            category = pdf_report.category

            # For scanned/hybrid PDFs, create LLMConverter with OCR model first
            if category in (PDFCategory.SCANNED, PDFCategory.HYBRID):
                from mdconverter.config import get_settings
                from mdconverter.core.gemini import LLMConverter

                settings = get_settings()
                # Put recommended model first, keep others as fallback
                models = [recommended] + [m for m in settings.models if m != recommended]
                return LLMConverter(output_dir=self.output_dir, models=models)

        # Default: use standard tool selection
        from mdconverter.cli.helpers import create_converter

        return create_converter(self.tool, file.suffix, self.output_dir)

    async def _apply_post_processors(self, result: ConversionResult) -> ConversionResult:
        """Run all applicable post-processors on conversion result."""
        for pp in self.post_processors:
            if pp.should_process(result.content):
                processed = pp.process(result.content)
                if processed != result.content:
                    result.content = processed
                    # Persist processed content
                    if result.output_path and result.output_path.exists():
                        await asyncio.to_thread(
                            result.output_path.write_text, processed, "utf-8"
                        )
                    summary = pp.get_summary()
                    logger.debug("Post-processor applied: %s", summary)

        return result

    def _expected_output_path(self, file: Path) -> Path:
        """Compute output path for a file (mirrors BaseConverter.get_output_path)."""
        output_name = file.stem.lower().replace(" ", "_") + ".md"
        return (self.output_dir or file.parent) / output_name

    @staticmethod
    def _write_cached(output_path: Path, content: str) -> None:
        """Write cached content to disk (runs in executor)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
