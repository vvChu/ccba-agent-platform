"""Custom exceptions for mdconverter.

Provides a unified exception hierarchy for consistent error handling.
"""


class MDConvertError(Exception):
    """Base exception for all mdconverter errors."""


class ConverterNotAvailableError(MDConvertError):
    """Converter tool not installed or configured.

    Raised when a required external tool (e.g., Pandoc) is not available.
    """


class ConversionTimeoutError(MDConvertError):
    """Conversion exceeded time limit.

    Raised when a conversion operation takes longer than the configured timeout.
    """


class InvalidInputError(MDConvertError):
    """Input file invalid or unsupported.

    Raised when the input file doesn't exist, is corrupted, or has an
    unsupported format.
    """


class ProviderError(MDConvertError):
    """LLM Provider returned an error.

    Raised when an LLM API call fails (e.g., rate limit, auth error, network).
    """
