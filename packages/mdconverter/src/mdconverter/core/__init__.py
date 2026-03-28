"""Core converters package - Generic document conversion logic."""

from mdconverter.core.base import BaseConverter, ConversionResult
from mdconverter.core.cache import ConversionCache
from mdconverter.core.exceptions import (
    ConversionTimeoutError,
    ConverterNotAvailableError,
    InvalidInputError,
    MDConvertError,
    ProviderError,
)
from mdconverter.core.gemini import GeminiConverter, LLMConverter
from mdconverter.core.llamaparse import LlamaParseConverter
from mdconverter.core.pandoc import PandocConverter
from mdconverter.core.registry import ConverterRegistry


def _register_builtin_converters() -> None:
    """Register built-in converters using the public API."""
    # Use programmatic registration (equivalent to decorator)
    ConverterRegistry.register("pandoc", priority=10)(PandocConverter)  # Fast, local
    ConverterRegistry.register("llamaparse", priority=30)(LlamaParseConverter)  # Scanned PDFs
    ConverterRegistry.register("llm", priority=50)(LLMConverter)  # Versatile, needs API


_register_builtin_converters()

__all__ = [
    "BaseConverter",
    "ConversionCache",
    "ConversionResult",
    "ConverterRegistry",
    "LLMConverter",
    "GeminiConverter",  # Backward compat alias
    "LlamaParseConverter",
    "PandocConverter",
    "MDConvertError",
    "ConverterNotAvailableError",
    "ConversionTimeoutError",
    "InvalidInputError",
    "ProviderError",
]
