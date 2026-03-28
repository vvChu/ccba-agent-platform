"""Tests for the logging module."""

import logging
from unittest.mock import patch

import pytest

from mdconverter.core.logging import (
    DEFAULT_DATE_FORMAT,
    DEFAULT_FORMAT,
    StructuredFormatter,
    configure_logging,
    get_logger,
    log_operation,
)


class TestStructuredFormatter:
    """Tests for StructuredFormatter class."""

    def test_default_format(self) -> None:
        """Test default format string is used."""
        formatter = StructuredFormatter()
        assert formatter._fmt == DEFAULT_FORMAT
        assert formatter.datefmt == DEFAULT_DATE_FORMAT
        assert formatter.use_json is False

    def test_json_format(self) -> None:
        """Test JSON formatting output."""
        formatter = StructuredFormatter(use_json=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert '"level": "INFO"' in output
        assert '"message": "test message"' in output
        assert '"logger": "test"' in output

    def test_standard_format(self) -> None:
        """Test standard format (non-JSON)."""
        formatter = StructuredFormatter(use_json=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert "INFO" in output
        assert "test message" in output


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_sets_level(self) -> None:
        """Test that configure_logging sets the correct level."""
        configure_logging(level=logging.DEBUG)
        logger = logging.getLogger("mdconverter")
        assert logger.level == logging.DEBUG

    def test_quiet_mode_sets_warning_level(self) -> None:
        """Test quiet mode sets WARNING level."""
        configure_logging(quiet=True)
        logger = logging.getLogger("mdconverter")
        assert logger.level == logging.WARNING

    def test_handler_not_duplicated(self) -> None:
        """Test that multiple calls don't duplicate handlers."""
        # Reset global state
        import mdconverter.core.logging as log_module

        log_module._configured = False
        logger = logging.getLogger("mdconverter")
        logger.handlers.clear()

        configure_logging()
        initial_count = len(logger.handlers)

        configure_logging()
        configure_logging()

        assert len(logger.handlers) == initial_count


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self) -> None:
        """Test get_logger returns a Logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_adds_namespace(self) -> None:
        """Test get_logger adds mdconverter namespace."""
        logger = get_logger("my_module")
        assert logger.name == "mdconverter.my_module"

    def test_get_logger_preserves_namespace(self) -> None:
        """Test get_logger preserves existing mdconverter namespace."""
        logger = get_logger("mdconverter.existing")
        assert logger.name == "mdconverter.existing"

    def test_get_logger_caches(self) -> None:
        """Test get_logger returns cached logger."""
        logger1 = get_logger("cached_test")
        logger2 = get_logger("cached_test")
        assert logger1 is logger2


class TestLogOperation:
    """Tests for log_operation context manager."""

    def test_log_operation_logs_start_and_complete(self) -> None:
        """Test log_operation logs start and completion."""
        logger = get_logger("test_op")
        with patch.object(logger, "info") as mock_info:
            with log_operation(logger, "test_task"):
                pass

            assert mock_info.call_count == 2
            # Check start message
            assert "Starting: test_task" in mock_info.call_args_list[0][0][0]
            # Check complete message
            assert "Completed: test_task" in mock_info.call_args_list[1][0][0]

    def test_log_operation_logs_failure(self) -> None:
        """Test log_operation logs failure on exception."""
        logger = get_logger("test_fail")
        with patch.object(logger, "info"), patch.object(logger, "error") as mock_error:
            with pytest.raises(ValueError, match="test error"):
                with log_operation(logger, "failing_task"):
                    raise ValueError("test error")

            mock_error.assert_called_once()
            assert "Failed: failing_task" in mock_error.call_args[0][0]

    def test_log_operation_includes_context(self) -> None:
        """Test log_operation includes extra context."""
        logger = get_logger("test_context")
        with patch.object(logger, "info") as mock_info:
            with log_operation(logger, "context_task", file="test.pdf"):
                pass

            # Check extra_data in calls
            call_kwargs = mock_info.call_args_list[0][1]
            assert "extra_data" in call_kwargs.get("extra", {})
