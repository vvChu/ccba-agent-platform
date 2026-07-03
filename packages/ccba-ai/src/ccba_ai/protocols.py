"""CCBA AI Quality Control Protocols.

These protocols establish explicit boundaries (seams) for the QC components
(Discovery, Audit, and Reporter) to enable static check, type safety, and testing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from ccba_ai.models import AuditReport


@runtime_checkable
class QCDiscoveryEngine(Protocol):
    """Protocol for drawing structure and metadata discovery engines."""

    async def discover(
        self,
        pdf_paths: list[Path],
        extract_titleblocks: bool = True,
        run_ai: bool = True,
    ) -> Any:
        """Run discovery over a set of drawings.

        Args:
            pdf_paths: List of PDFs.
            extract_titleblocks: If True, crop title block regions.
            run_ai: If True, extract metadata using vision OCR models.

        Returns:
            ProjectBackbone or dictionary of drawing metadata.
        """
        ...


@runtime_checkable
class QCAuditEngine(Protocol):
    """Protocol for drawing coordinate checks and multi-level audit passes."""

    async def run_multi_level_audit(
        self,
        level_images: dict[str, list[Path]],
        discipline_order: list[str] | None = None,
    ) -> list[AuditReport]:
        """Run concurrent multi-level audit passes.

        Args:
            level_images: Mapping level -> 4 discipline image paths.
            discipline_order: Names of the 4 disciplines.

        Returns:
            List of generated AuditReports.
        """
        ...


@runtime_checkable
class QCReporterEngine(Protocol):
    """Protocol for consolidating discovery and audit findings into reports."""

    def synthesize(
        self,
        backbone: Any | None = None,
        audit_results: list[AuditReport | dict] | None = None,
        output_path: Path = Path("report.md"),
    ) -> Path:
        """Synthesize technical markdown report.

        Args:
            backbone: The discovered document backbone index.
            audit_results: The list of level audit reports or dictionaries.
            output_path: Output target path for report file.

        Returns:
            Path of the saved markdown file.
        """
        ...
