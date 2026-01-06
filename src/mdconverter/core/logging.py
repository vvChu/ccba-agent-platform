"""Structured logging for mdconverter.

Provides consistent logging format with support for:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)
- Optional JSON output for machine parsing
- Context managers for operation timing
- Verbose/quiet modes for CLI
"""

import logging
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

# Module-level logger cache
_loggers: dict[str, logging.Logger] = {}

# Default format
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class StructuredFormatter(logging.Formatter):
    """Formatter with optional structured output."""

    def __init__(
        self,
        fmt: str = DEFAULT_FORMAT,
        datefmt: str = DEFAULT_DATE_FORMAT,
        use_json: bool = False,
    ) -> None:
        super().__init__(fmt, datefmt)
        self.use_json = use_json

    def format(self, record: logging.LogRecord) -> str:
        if self.use_json:
            import json

            data = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            # Add extra fields if present
            if hasattr(record, "extra_data"):
                data.update(record.extra_data)
            return json.dumps(data, ensure_ascii=False)
        return super().format(record)


def configure_logging(
    level: int = logging.INFO,
    use_json: bool = False,
    quiet: bool = False,
) -> None:
    """Configure root logging for mdconverter.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
        use_json: If True, output logs as JSON.
        quiet: If True, only show WARNING and above.
    """
    if quiet:
        level = logging.WARNING

    root = logging.getLogger("mdconverter")
    root.setLevel(level)

    # Remove existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(StructuredFormatter(use_json=use_json))
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given module.

    Args:
        name: Module name (typically __name__).

    Returns:
        Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    # Ensure name is under mdconverter namespace
    if not name.startswith("mdconverter"):
        name = f"mdconverter.{name}"

    logger = logging.getLogger(name)
    _loggers[name] = logger
    return logger


@contextmanager
def log_operation(
    logger: logging.Logger, operation: str, **context: Any
) -> Generator[None, None, None]:
    """Context manager for timing and logging operations.

    Args:
        logger: Logger instance.
        operation: Name of the operation.
        **context: Additional context to log.

    Yields:
        None

    Example:
        with log_operation(logger, "convert", file="test.pdf"):
            # ... do work ...
    """
    start = time.perf_counter()
    logger.info(f"Starting: {operation}", extra={"extra_data": context})

    try:
        yield
        duration = time.perf_counter() - start
        logger.info(
            f"Completed: {operation} ({duration:.2f}s)",
            extra={"extra_data": {**context, "duration_s": duration}},
        )
    except Exception as e:
        duration = time.perf_counter() - start
        logger.error(
            f"Failed: {operation} ({duration:.2f}s) - {e}",
            extra={"extra_data": {**context, "duration_s": duration, "error": str(e)}},
        )
        raise
