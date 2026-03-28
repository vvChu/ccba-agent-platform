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
        """Add YAML frontmatter to converted content with VN Legal metadata extraction."""
        if content.startswith("---"):
            return content  # Already has frontmatter

        # Extract VN Legal metadata from content
        metadata = self._extract_vn_legal_metadata(content, source_path)
        
        frontmatter = f'''---
title: "{metadata.get('title', source_path.stem)}"
short_title: "{metadata.get('short_title', '')}"
type: "{metadata.get('type', 'Document')}"
decision_number: "{metadata.get('decision_number', '')}"
issue_date: "{metadata.get('issue_date', '')}"
effective_date: "{metadata.get('effective_date', '')}"
issuer: "{metadata.get('issuer', '')}"
signer: "{metadata.get('signer', '')}"
status: "{metadata.get('status', 'converted')}"
source_file: "{source_path.name}"
conversion_tool: "{tool}"
conversion_date: "{datetime.now().isoformat()}"
---

'''
        return frontmatter + content

    def _extract_vn_legal_metadata(self, content: str, source_path: Path) -> dict[str, str]:
        """Extract metadata from Vietnamese legal document content."""
        import re
        
        metadata: dict[str, str] = {
            "title": source_path.stem,
            "short_title": "",
            "type": "Document",
            "decision_number": "",
            "issue_date": "",
            "effective_date": "",
            "issuer": "",
            "signer": "",
            "status": "converted",
        }
        
        # Look at first 3000 chars for metadata
        header = content[:3000]
        
        # Extract decision number (Quyết định số XXX/QĐ-XXX)
        qd_match = re.search(r'(?:Quyết định\s+)?[Ss]ố[:\s]*(\d+/Q[ĐD][-–]?\w+)', header, re.IGNORECASE)
        if qd_match:
            metadata["decision_number"] = qd_match.group(1)
        
        # Extract issue date (ngày DD tháng MM năm YYYY)
        date_match = re.search(r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})', header, re.IGNORECASE)
        if date_match:
            day, month, year = date_match.groups()
            metadata["issue_date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Extract effective date (có hiệu lực từ ngày DD/MM/YYYY)
        eff_match = re.search(r'hiệu lực\s+(?:từ\s+)?(?:ngày\s+)?(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})', header, re.IGNORECASE)
        if eff_match:
            date_str = eff_match.group(1).replace("/", "-")
            parts = date_str.split("-")
            if len(parts) == 3:
                metadata["effective_date"] = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
        
        # Extract issuer (Viện KHCN Xây dựng, Bộ Xây dựng, etc.)
        issuer_patterns = [
            r'(Viện\s+KH(?:CN)?\s+[^,\n]+)',
            r'(Bộ\s+[^,\n]+)',
            r'(VIỆN\s+[A-ZĐÀÁẢÃẠ\s]+)',
        ]
        for pattern in issuer_patterns:
            issuer_match = re.search(pattern, header)
            if issuer_match:
                metadata["issuer"] = issuer_match.group(1).strip()[:50]
                break
        
        # Extract signer
        signer_match = re.search(r'(?:VIỆN TRƯỞNG|Viện trưởng)[^\n]*\n[^\n]*\n\*\*([^*]+)\*\*', header)
        if signer_match:
            metadata["signer"] = signer_match.group(1).strip()
        
        # Determine document type
        type_keywords = {
            "Quy chế": "Quy chế nội bộ",
            "Quy định": "Quy định nội bộ", 
            "Quyết định": "Quyết định",
            "Thông tư": "Thông tư",
            "Nghị định": "Nghị định",
            "QCVN": "Quy chuẩn Việt Nam",
            "TCVN": "Tiêu chuẩn Việt Nam",
        }
        for keyword, doc_type in type_keywords.items():
            if keyword.lower() in header.lower():
                metadata["type"] = doc_type
                break
        
        # Extract title from first H1 or bold line
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()[:100]
        
        # Generate short_title
        if metadata["decision_number"]:
            metadata["short_title"] = f"QĐ {metadata['decision_number'].split('/')[0]}"
        
        # Set status
        metadata["status"] = "final"
        
        return metadata

