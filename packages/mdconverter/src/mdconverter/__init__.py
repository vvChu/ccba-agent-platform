"""
mdconverter - Modern Document to Markdown Converter

A powerful Python library for converting documents (PDF, DOCX, HTML) to clean,
standardized Markdown with special support for Vietnamese legal documents.
"""

__version__ = "2.2.0"
__author__ = "IBST BIM Team"

from mdconverter.config import Settings, get_settings
from mdconverter.core import (
    BaseConverter,
    ConversionCache,
    ConversionPipeline,
    ConversionResult,
    ConverterRegistry,
    PostProcessor,
    MDConvertError,
    ConverterNotAvailableError,
    ConversionTimeoutError,
    InvalidInputError,
    ProviderError,
)

__all__ = [
    "Settings",
    "get_settings",
    "BaseConverter",
    "ConversionCache",
    "ConversionPipeline",
    "ConversionResult",
    "ConverterRegistry",
    "PostProcessor",
    "MDConvertError",
    "ConverterNotAvailableError",
    "ConversionTimeoutError",
    "InvalidInputError",
    "ProviderError",
    "__version__",
]

