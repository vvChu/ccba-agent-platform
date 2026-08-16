"""
Conversion Pipeline — orchestrates convert → post-process → cache.

Extracted from convert_cmd.py (H2 fix) to separate business logic from CLI.
Defines a ``PostProcessor`` Protocol for extensible post-processing (H3 fix).
"""

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ccba_pdf_prep.core import Segment
    from mdconverter.core.analyzer import PDFReport

from mdconverter.core.base import BaseConverter, ConversionResult, ConversionStatus, ConversionTool
from mdconverter.core.cache import ConversionCache
from mdconverter.core.utils import get_blind_chunks, merge_markdown, split_pdf

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


class LinkPatcherPostProcessor:
    """Post-processor adapter for relative link patching."""

    def __init__(self) -> None:
        from mdconverter.core.link_patcher import LinkPatcher

        self._patcher = LinkPatcher()
        self._last_patched_count = 0

    def should_process(self, content: str) -> bool:
        """Check if content contains un-prefixed relative appendix links."""
        return bool(self._patcher.LINK_PATTERN.search(content))

    def process(self, content: str) -> str:
        """Patch relative links in content."""
        new_content, count = self._patcher.patch_content(content)
        self._last_patched_count = count
        return new_content

    def get_summary(self) -> dict[str, int]:
        """Get summary of patched links."""
        return {"relative_links_patched": self._last_patched_count}


def get_default_post_processors() -> list[PostProcessor]:
    """Get the default list of post-processors.

    Add new post-processors here as the system grows (e.g. for English
    documents, academic papers, etc.).

    Returns:
        List of PostProcessor instances.
    """
    return [VNLegalPostProcessor(), LinkPatcherPostProcessor()]


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
        extract_drawing: bool = False,
    ) -> None:
        self.tool = tool
        self.output_dir = output_dir
        self.cache = cache
        self.post_processors = (
            post_processors if post_processors is not None else get_default_post_processors()
        )
        self.extract_drawing = extract_drawing
        self._sem = asyncio.Semaphore(max_concurrency)

    def convert(self, file: Path | str) -> ConversionResult:
        """Synchronously convert a single file with caching and post-processing.

        Convenience wrapper around async ``process_file`` for synchronous callers.

        Note:
            If called from within an existing event loop, raises RuntimeError to prevent
            asyncio concurrency/semaphore binding issues. Callers in async contexts
            should use ``await pipeline.process_file(file)`` directly.
        """
        path = Path(file)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError(
                "ConversionPipeline.convert() cannot be called from within a running event loop. "
                "Please use 'await pipeline.process_file(file)' directly."
            )
        return asyncio.run(self.process_file(path))

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
        # No longer wrap entire process_file in semaphore to allow parallel segmenting
        # async with self._sem:  <-- REFACTORED
        loop = asyncio.get_running_loop()

        # 0. PDF analysis — classify and auto-select tool
        pdf_report = None
        if file.suffix.lower() == ".pdf":
            pdf_report = await self._analyze_pdf(file, loop)
            if pdf_report:
                # Drawing handling
                if pdf_report.category == "drawing" and self.extract_drawing:
                    logger.info("Drawing extraction enabled for %s", file.name)
                elif pdf_report.should_skip:
                    return ConversionResult(
                        source_path=file,
                        status=ConversionStatus.SKIPPED,
                        error_message=pdf_report.skip_reason,
                        metadata={"pdf_analysis": pdf_report.to_dict()},
                    )

                # Determine if we should use segmented processing
                is_hybrid = pdf_report.category == "hybrid"
                is_very_large = pdf_report.pages > 30

                if (is_hybrid or is_very_large) and self.tool in (ConversionTool.AUTO, "auto"):
                    return await self._process_segmented(file, pdf_report)

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

        # 2. Convert with semaphore protection
        converter = self._create_converter_for_file(file, pdf_report)
        async with self._sem:
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

    async def _process_segmented(self, file: Path, report: "PDFReport") -> ConversionResult:
        """Handle conversion by splitting PDF into segments or chunks.

        For Hybrid docs, routes segments to optimal models.
        For large docs, routes chunks to parallel processing.
        """
        import shutil
        import tempfile

        from mdconverter.core.analyzer import Segment

        loop = asyncio.get_running_loop()

        # 1. Determine ranges
        if report.category == "hybrid":
            segments = report.get_segments()
            logger.info("Hybrid document detected: %d segments", len(segments))
        else:
            # Blind chunking for large unified docs
            ranges = get_blind_chunks(report.pages, chunk_size=20)
            segments = [
                Segment(
                    start,
                    end,
                    "text" if report.category == "text_rich" else "scan",
                    report.recommended_model,
                )
                for start, end in ranges
            ]
            logger.info("Large document detected: %d chunks of 20 pages", len(segments))

        temp_dir = Path(tempfile.mkdtemp(prefix="mdconv_"))
        try:
            # 2. Split PDF
            ranges = [(s.start_page, s.end_page) for s in segments]
            chunk_paths = await loop.run_in_executor(None, split_pdf, file, ranges, temp_dir)

            # 3. Convert each chunk concurrently
            # Use semaphore-protected wrapper
            tasks = []
            for i, chunk_path in enumerate(chunk_paths):
                seg = segments[i]
                tasks.append(self._convert_segment_with_limit(i, len(segments), chunk_path, seg))

            # Execute concurrently
            results = await asyncio.gather(*tasks)

            segment_results: list[str] = []
            tool_used = "segmented"

            for i, res in enumerate(results):
                seg = segments[i]
                if res.is_success and res.content:
                    content = res.content
                    if "---" in content:
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            content = parts[2].strip()

                    marker = f"\n\n<!-- PAGE SEGMENT: {seg.start_page + 1}-{seg.end_page + 1} ({seg.page_type}) -->\n"
                    segment_results.append(marker + content)
                else:
                    segment_results.append(
                        f"\n\n> [!ERROR] Failed to convert pages {seg.start_page + 1}-{seg.end_page + 1}\n"
                    )

            # 4. Merge results
            final_content = merge_markdown(segment_results)

            # Add unified frontmatter
            # Use LLMConverter as a concrete proxy to access shared BaseConverter logic
            from mdconverter.core.gemini import LLMConverter

            dummy = LLMConverter(output_dir=self.output_dir)
            final_content = dummy.add_frontmatter(final_content, file, tool_used)

            output_path = self._expected_output_path(file)
            await asyncio.to_thread(output_path.write_text, final_content, "utf-8")

            result = ConversionResult(
                source_path=file,
                output_path=output_path,
                status=ConversionStatus.SUCCESS,
                tool_used=tool_used,
                content=final_content,
                metadata={"pdf_analysis": report.to_dict(), "segments": len(segments)},
            )

            # Post-process the final merged doc
            return await self._apply_post_processors(result)

        finally:
            # Cleanup temp files
            await loop.run_in_executor(None, shutil.rmtree, temp_dir)

    async def _convert_segment_with_limit(
        self, index: int, total: int, chunk_path: Path, segment: "Segment"
    ) -> ConversionResult:
        """Internal helper to convert a segment with semaphore protection."""
        logger.debug(
            "Processing segment %d/%d: pages %d-%d (%s)",
            index + 1,
            total,
            segment.start_page + 1,
            segment.end_page + 1,
            segment.page_type,
        )

        converter = self._create_converter_for_segment(chunk_path, segment)
        async with self._sem:
            return await converter.convert(chunk_path)

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
    async def _analyze_pdf(self, file: Path, loop: asyncio.AbstractEventLoop) -> "PDFReport | None":
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
        """Create the appropriate converter, optionally guided by PDF analysis."""
        from mdconverter.core.analyzer import PDFCategory

        # If we have a PDF report and tool is AUTO, use the recommendation
        if (
            pdf_report
            and pdf_report.recommended_model
            and self.tool in (ConversionTool.AUTO, "auto")
            and file.suffix.lower() == ".pdf"
        ):
            recommended = pdf_report.recommended_model
            category = pdf_report.category

            # Special case for Drawings if extraction is enabled
            if category == PDFCategory.DRAWING and self.extract_drawing:
                return self._create_drawing_converter(file)

            # For scanned/hybrid PDFs, create LLMConverter with recommended model first
            if category in (PDFCategory.SCANNED, PDFCategory.HYBRID):
                from mdconverter.config import get_settings
                from mdconverter.core.gemini import LLMConverter

                settings = get_settings()
                models = (
                    ([recommended] + [m for m in settings.models if m != recommended])
                    if recommended
                    else settings.models
                )
                return LLMConverter(output_dir=self.output_dir, models=models)

        # Default: use standard tool selection
        from mdconverter.cli.helpers import create_converter

        return create_converter(self.tool, file.suffix, self.output_dir)

    def _create_converter_for_segment(
        self, chunk_path: Path, segment: "Segment"
    ) -> "BaseConverter":
        """Create a converter specialized for a segment's page type."""
        from mdconverter.config import get_settings
        from mdconverter.core.gemini import LLMConverter

        settings = get_settings()
        recommended = segment.model_hint

        # Prioritize the recommended model for this segment type
        models = (
            ([recommended] + [m for m in settings.models if m != recommended])
            if recommended
            else settings.models
        )
        converter = LLMConverter(output_dir=None, models=models)  # No individual output dir

        # If it's a drawing segment, we might want to inject a custom prompt
        if segment.page_type == "drawing":
            converter.system_prompt = (
                "You are an engineering drawing assistant. Extract all structural notes, "
                "axes, grid labels, dimensions, and technical tables from this drawing. "
                "Output as clean Markdown."
            )

        return converter

    def _create_drawing_converter(self, file: Path) -> "BaseConverter":
        """Create an LLMConverter specifically for drawing extraction."""
        from mdconverter.config import get_settings
        from mdconverter.core.gemini import LLMConverter

        settings = get_settings()
        # Drawing always uses qwen-35b if available as it's the best for this
        preferred = "qwen3.5-35b"
        models = [preferred] + [m for m in settings.models if m != preferred]

        converter = LLMConverter(output_dir=self.output_dir, models=models)
        converter.system_prompt = (
            "You are an engineering drawing assistant. Extract all structural notes, "
            "axes, grid labels, dimensions, and technical tables from this drawing. "
            "Output as clean Markdown."
        )
        return converter

    async def _apply_post_processors(self, result: ConversionResult) -> ConversionResult:
        """Run all applicable post-processors on conversion result."""
        for pp in self.post_processors:
            if pp.should_process(result.content):
                processed = pp.process(result.content)
                if processed != result.content:
                    result.content = processed
                    # Persist processed content
                    if result.output_path and result.output_path.exists():
                        await asyncio.to_thread(result.output_path.write_text, processed, "utf-8")
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
