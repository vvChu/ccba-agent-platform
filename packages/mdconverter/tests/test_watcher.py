"""Tests for FileWatcher module."""

import time
from pathlib import Path
from unittest.mock import MagicMock

from mdconverter.core.watcher import ConversionEventHandler, FileWatcher


class TestConversionEventHandler:
    """Test ConversionEventHandler class."""

    def test_supported_extensions(self) -> None:
        """Test supported file extensions."""
        handler = ConversionEventHandler(MagicMock())
        assert ".pdf" in handler.SUPPORTED_EXTENSIONS
        assert ".docx" in handler.SUPPORTED_EXTENSIONS
        assert ".html" in handler.SUPPORTED_EXTENSIONS
        assert ".txt" not in handler.SUPPORTED_EXTENSIONS

    def test_should_process_valid_extension(self) -> None:
        """Test _should_process returns True for valid files."""
        handler = ConversionEventHandler(MagicMock())
        assert handler._should_process(Path("test.pdf")) is True
        assert handler._should_process(Path("test.docx")) is True

    def test_should_process_invalid_extension(self) -> None:
        """Test _should_process returns False for invalid files."""
        handler = ConversionEventHandler(MagicMock())
        assert handler._should_process(Path("test.txt")) is False
        assert handler._should_process(Path("test.py")) is False

    def test_debounce_same_file(self) -> None:
        """Test debounce prevents multiple triggers."""
        handler = ConversionEventHandler(MagicMock())
        path = Path("test.pdf")

        # First call should pass
        assert handler._should_process(path) is True

        # Immediate second call should be debounced
        assert handler._should_process(path) is False

    def test_debounce_different_files(self) -> None:
        """Test debounce allows different files."""
        handler = ConversionEventHandler(MagicMock())

        assert handler._should_process(Path("test1.pdf")) is True
        assert handler._should_process(Path("test2.pdf")) is True


class TestFileWatcher:
    """Test FileWatcher class."""

    def test_init(self, tmp_path: Path) -> None:
        """Test FileWatcher initialization."""
        callback = MagicMock()
        watcher = FileWatcher(tmp_path, callback)

        assert watcher.watch_path == tmp_path
        assert watcher.is_running is False

    def test_start_stop(self, tmp_path: Path) -> None:
        """Test start and stop methods."""
        callback = MagicMock()
        watcher = FileWatcher(tmp_path, callback)

        watcher.start()
        assert watcher.is_running is True

        watcher.stop()
        # Give observer thread time to clean up
        time.sleep(0.1)
        assert watcher.is_running is False

    def test_recursive_option(self, tmp_path: Path) -> None:
        """Test recursive option is stored."""
        callback = MagicMock()

        watcher1 = FileWatcher(tmp_path, callback, recursive=False)
        assert watcher1.recursive is False

        watcher2 = FileWatcher(tmp_path, callback, recursive=True)
        assert watcher2.recursive is True
