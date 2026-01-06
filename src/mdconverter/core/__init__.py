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

__all__ = [
    "BaseConverter",
    "ConversionCache",
    "ConversionResult",
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
