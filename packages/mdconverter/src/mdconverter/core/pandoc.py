"""
Pandoc-based converter for DOCX, HTML, and other formats.

Uses Pandoc as a subprocess for reliable conversion.
"""

import asyncio
import shutil
import time
from pathlib import Path

from mdconverter.core.base import BaseConverter, ConversionResult, ConversionStatus


class PandocConverter(BaseConverter):
    """Document converter using Pandoc."""

    SUPPORTED_EXTENSIONS = {".docx", ".doc", ".html", ".htm", ".rtf", ".odt", ".epub"}

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize Pandoc converter."""
        super().__init__(output_dir)
        self._pandoc_available: bool | None = None

    def supports(self, file_extension: str) -> bool:
        """Check if extension is supported."""
        return file_extension.lower() in self.SUPPORTED_EXTENSIONS

    def is_pandoc_available(self) -> bool:
        """Check if Pandoc is installed."""
        if self._pandoc_available is None:
            self._pandoc_available = shutil.which("pandoc") is not None
        return self._pandoc_available

    async def convert(self, source_path: Path) -> ConversionResult:
        """Convert document using Pandoc."""
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

        if not self.is_pandoc_available():
            return ConversionResult(
                source_path=source_path,
                status=ConversionStatus.FAILED,
                error_message="Pandoc is not installed",
            )

        try:
            output_path = self.get_output_path(source_path)

            # Run Pandoc conversion async
            process = await asyncio.create_subprocess_exec(
                "pandoc",
                str(source_path),
                "-o",
                str(output_path),
                "-t",
                "gfm",
                "--wrap=none",
                "--extract-media",
                str(output_path.parent / "media"),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            except asyncio.TimeoutError as e:
                process.kill()
                raise asyncio.TimeoutError("Pandoc conversion timed out") from e

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Pandoc conversion failed"
                return ConversionResult(
                    source_path=source_path,
                    status=ConversionStatus.FAILED,
                    tool_used="pandoc",
                    duration_seconds=time.time() - start_time,
                    error_message=error_msg,
                )

            # Read and optionally add frontmatter
            # File I/O is blocking, but fast for text files.
            # Ideally use aiofiles, but standard io is acceptable for small/medium files in this context.
            content = output_path.read_text(encoding="utf-8")
            final_content = self.add_frontmatter(content, source_path, "pandoc")
            output_path.write_text(final_content, encoding="utf-8")

            return ConversionResult(
                source_path=source_path,
                output_path=output_path,
                status=ConversionStatus.SUCCESS,
                tool_used="pandoc",
                content=final_content,
                quality_score=self._calculate_quality(final_content),
                duration_seconds=time.time() - start_time,
            )

        except asyncio.TimeoutError:
            return ConversionResult(
                source_path=source_path,
                status=ConversionStatus.FAILED,
                tool_used="pandoc",
                duration_seconds=time.time() - start_time,
                error_message="Pandoc conversion timed out",
            )
        except Exception as e:
            return ConversionResult(
                source_path=source_path,
                status=ConversionStatus.FAILED,
                tool_used="pandoc",
                duration_seconds=time.time() - start_time,
                error_message=str(e),
            )

    def _calculate_quality(self, content: str) -> int:
        """Calculate quality score (0-100)."""
        score = 60  # Pandoc is reliable

        # Length check
        if len(content) > 500:
            score += 10
        if len(content) > 2000:
            score += 10

        # Structure check
        if "##" in content:
            score += 10
        if "|" in content:
            score += 10

        return min(score, 100)
