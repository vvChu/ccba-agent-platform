"""Tests for ConverterRegistry."""

from pathlib import Path

import pytest

from mdconverter.core.gemini import LLMConverter
from mdconverter.core.pandoc import PandocConverter
from mdconverter.core.registry import ConverterRegistry


class TestConverterRegistry:
    """Test ConverterRegistry class."""

    def test_get_returns_registered_converter(self) -> None:
        """Test get returns a registered converter class."""
        # PandocConverter should be registered via mdconverter.core
        converter_class = ConverterRegistry.get("pandoc")
        assert converter_class is PandocConverter

    def test_get_returns_none_for_unknown(self) -> None:
        """Test get returns None for unregistered name."""
        result = ConverterRegistry.get("nonexistent")
        assert result is None

    def test_create_returns_instance(self, tmp_path: Path) -> None:
        """Test create returns converter instance."""
        converter = ConverterRegistry.create("pandoc", output_dir=tmp_path)
        assert isinstance(converter, PandocConverter)

    def test_create_raises_for_unknown(self) -> None:
        """Test create raises ValueError for unknown converter."""
        with pytest.raises(ValueError, match="Unknown converter"):
            ConverterRegistry.create("nonexistent")

    def test_auto_select_for_docx(self, tmp_path: Path) -> None:
        """Test auto_select picks correct converter for docx."""
        converter = ConverterRegistry.auto_select(".docx", output_dir=tmp_path)
        # Pandoc has priority 10, should be selected for docx
        assert isinstance(converter, PandocConverter)

    def test_auto_select_for_pdf(self, tmp_path: Path) -> None:
        """Test auto_select picks LlamaParseConverter for pdf (priority 30)."""
        from mdconverter.core.llamaparse import LlamaParseConverter

        converter = ConverterRegistry.auto_select(".pdf", output_dir=tmp_path)
        # LlamaParse has priority 30, LLM has priority 50, so LlamaParse wins
        assert isinstance(converter, LlamaParseConverter)

    def test_auto_select_raises_for_unsupported(self) -> None:
        """Test auto_select raises for unsupported extension."""
        with pytest.raises(ValueError, match="No converter supports"):
            ConverterRegistry.auto_select(".xyz")

    def test_list_all_returns_info(self) -> None:
        """Test list_all returns converter information."""
        result = ConverterRegistry.list_all()

        assert len(result) >= 3  # pandoc, llm, llamaparse

        names = [r["name"] for r in result]
        assert "pandoc" in names
        assert "llm" in names
        assert "llamaparse" in names

    def test_llm_converter_registered(self) -> None:
        """Test LLMConverter is registered as 'llm'."""
        converter_class = ConverterRegistry.get("llm")
        assert converter_class is LLMConverter
