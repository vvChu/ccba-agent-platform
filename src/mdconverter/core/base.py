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

    GEMINI = "gemini"
    PANDOC = "pandoc"
    LLAMAPARSE = "llamaparse"
    DOCLING = "docling"
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
    ) -> str:
        """Add YAML frontmatter to converted content."""
        frontmatter = f"""---
title: "{source_path.stem}"
type: "Document"
date: "{datetime.now().strftime("%Y-%m-%d")}"
status: "converted"
source_file: "{source_path.name}"
conversion_tool: "{tool}"
conversion_date: "{datetime.now().isoformat()}"
---

"""
        if content.startswith("---"):
            return content  # Already has frontmatter
        return frontmatter + content
