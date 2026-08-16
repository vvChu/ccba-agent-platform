"""test_pipeline_all_in_one.py - TDD unit tests for All-in-One ConversionPipeline Deep Seam."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mdconverter.core.base import ConversionResult, ConversionStatus, ConversionTool
from mdconverter.core.pipeline import (
    ConversionPipeline,
    LinkPatcherPostProcessor,
    get_default_post_processors,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_default_post_processors_registered() -> None:
    """Verify all standard post-processors are registered in default chain."""
    processors = get_default_post_processors()
    proc_types = [p.__class__.__name__ for p in processors]

    assert "VNLegalPostProcessor" in proc_types
    assert "LinkPatcherPostProcessor" in proc_types


def test_pipeline_post_processing_integration(tmp_path: Path) -> None:
    """Verify ConversionPipeline automatically runs post-processing and link patching."""
    pipeline = ConversionPipeline(tool=ConversionTool.AUTO, output_dir=tmp_path)

    raw_markdown = """# Quy Chuẩn Kỹ Thuật Quốc Gia

Điều 1. Phạm vi điều chỉnh
Quy chuẩn này quy định về an toàn cháy.

Xem thêm tại [Phụ lục 1](appendices/phu_luc_1.md).
"""
    output_file = tmp_path / "sample.md"
    output_file.write_text(raw_markdown, encoding="utf-8")

    mock_converter = MagicMock()
    mock_converter.convert = AsyncMock(
        return_value=ConversionResult(
            source_path=tmp_path / "sample.docx",
            output_path=output_file,
            content=raw_markdown,
            status=ConversionStatus.SUCCESS,
            tool_used=ConversionTool.PANDOC,
        )
    )

    with patch.object(pipeline, "_create_converter_for_file", return_value=mock_converter):
        result = pipeline.convert(tmp_path / "sample.docx")

    assert result.status == ConversionStatus.SUCCESS
    assert result.content is not None
    # Link patcher should have normalized the relative link to ./appendices/
    assert "[Phụ lục 1](./appendices/phu_luc_1.md)" in result.content
    assert result.output_path is not None
    assert result.output_path.exists()
    assert "[Phụ lục 1](./appendices/phu_luc_1.md)" in result.output_path.read_text(encoding="utf-8")


def test_pipeline_custom_post_processor_toggle(tmp_path: Path) -> None:
    """Verify individual post-processors can be customized or toggled."""
    custom_pipeline = ConversionPipeline(
        tool=ConversionTool.AUTO,
        output_dir=tmp_path,
        post_processors=[LinkPatcherPostProcessor()],
    )
    assert len(custom_pipeline.post_processors) == 1
    assert isinstance(custom_pipeline.post_processors[0], LinkPatcherPostProcessor)
