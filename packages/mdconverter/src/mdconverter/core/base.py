"""
Base converter classes and data models.

Provides abstract interfaces and common utilities for all converters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ConversionTool(str, Enum):
    """Available conversion tools."""

    LLM = "llm"
    PANDOC = "pandoc"
    LLAMAPARSE = "llamaparse"
    AUTO = "auto"


class ConversionStatus(str, Enum):
    """Status of a conversion operation."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


@dataclass
class ConversionResult:
    """Result of a document conversion operation."""

    source_path: Path
    output_path: Path | None = None
    status: ConversionStatus = ConversionStatus.SUCCESS
    tool_used: str = "unknown"
    content: str = ""
    quality_score: int = 0
    duration_seconds: float = 0.0
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if conversion was successful."""
        return self.status == ConversionStatus.SUCCESS

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source": str(self.source_path),
            "output": str(self.output_path) if self.output_path else None,
            "status": self.status.value,
            "tool": self.tool_used,
            "quality_score": self.quality_score,
            "duration": self.duration_seconds,
            "error": self.error_message,
        }


class BaseConverter(ABC):
    """Abstract base class for all document converters."""

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize converter with optional output directory."""
        self.output_dir = output_dir
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def convert(self, source_path: Path) -> ConversionResult:
        """
        Convert a document to Markdown.

        Args:
            source_path: Path to the source document.

        Returns:
            ConversionResult with status and content.
        """
        pass

    @abstractmethod
    def supports(self, file_extension: str) -> bool:
        """
        Check if this converter supports the given file extension.

        Args:
            file_extension: File extension (e.g., '.pdf', '.docx').

        Returns:
            True if supported, False otherwise.
        """
        pass

    def _calculate_quality(self, content: str, base_score: int = 50) -> int:
        """Calculate quality score (0-100) using weighted tier scoring.

        Uses tiered thresholds for length, structure density, table presence,
        and Vietnamese content ratio instead of simple boolean checks.

        Args:
            content: Converted Markdown content to evaluate.
            base_score: Starting score reflecting converter reliability.
                - 50: LLM-based converters (variable quality)
                - 60: Pandoc (reliable but no semantic understanding)
                - 70: LlamaParse (high-quality OCR)

        Returns:
            Integer quality score clamped to [0, 100].
        """
        score = base_score
        length = len(content)

        # Length scoring — tiered progression
        if length > 500:
            score += 5
        if length > 2000:
            score += 5
        if length > 5000:
            score += 5
        if length > 10000:
            score += 5

        # Structure density — reward more headings, not just presence
        heading_count = content.count("\n## ") + content.count("\n### ")
        if heading_count >= 1:
            score += 5
        if heading_count >= 5:
            score += 5
        if heading_count >= 10:
            score += 5

        # Table presence + quality
        table_rows = content.count("\n|")
        if table_rows >= 2:
            score += 5
        if table_rows >= 10:
            score += 5

        # Vietnamese content ratio
        if length > 0:
            vn_ratio = sum(1 for c in content if ord(c) > 127) / length
            if vn_ratio > 0.05:
                score += 3
            if vn_ratio > 0.15:
                score += 2

        return min(score, 100)

    def get_output_path(self, source_path: Path) -> Path:
        """Generate output path for the converted file."""
        output_name = source_path.stem.lower().replace(" ", "_") + ".md"
        parent_dir = self.output_dir if self.output_dir else source_path.parent
        return parent_dir / output_name

    def add_frontmatter(
        self,
        content: str,
        source_path: Path,
        tool: str = "unknown",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Add YAML frontmatter to converted content.

        Args:
            content: Markdown content.
            source_path: Original source file path.
            tool: Name of the conversion tool used.
            metadata: Optional pre-extracted metadata dict. When provided,
                fields like title, type, dates, issuer are included.
                When ``None``, only basic info (source, tool, date) is used.

        Returns:
            Content with YAML frontmatter prepended.
        """
        if content.startswith("---"):
            return content  # Already has frontmatter

        meta = metadata or {}

        frontmatter = f'''---
title: "{meta.get("title", source_path.stem)}"
source_file: "{source_path.name}"
conversion_tool: "{tool}"
conversion_date: "{datetime.now().isoformat()}"
'''

        # Append domain-specific fields only when metadata is provided
        if metadata:
            for key in (
                "short_title",
                "type",
                "decision_number",
                "issue_date",
                "effective_date",
                "issuer",
                "signer",
                "status",
            ):
                value = metadata.get(key, "")
                frontmatter += f'{key}: "{value}"\n'

        frontmatter += "---\n\n"
        return frontmatter + content
