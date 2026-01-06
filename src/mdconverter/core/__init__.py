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

# Register built-in converters with priorities
# Lower priority = preferred for overlapping extensions
ConverterRegistry._converters["pandoc"] = PandocConverter
ConverterRegistry._priority["pandoc"] = 10  # Fast, local

ConverterRegistry._converters["llm"] = LLMConverter
ConverterRegistry._priority["llm"] = 50  # Versatile, needs API

ConverterRegistry._converters["llamaparse"] = LlamaParseConverter
ConverterRegistry._priority["llamaparse"] = 30  # Good for scanned PDFs

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
