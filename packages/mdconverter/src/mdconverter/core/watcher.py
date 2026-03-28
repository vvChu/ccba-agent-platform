"""
File Watcher for auto-conversion.

Monitors a directory for file changes and triggers conversion.
"""

import time
from collections.abc import Callable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class ConversionEventHandler(FileSystemEventHandler):
    """Event handler that triggers conversion on file changes."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".html", ".htm", ".pptx", ".xlsx"}
    DEBOUNCE_SECONDS = 1.0  # Avoid multiple triggers for same file

    def __init__(
        self,
        on_file_change: Callable[[Path], None],
        recursive: bool = False,
    ) -> None:
        """Initialize handler with callback function."""
        super().__init__()
        self.on_file_change = on_file_change
        self.recursive = recursive
        self._last_triggered: dict[Path, float] = {}

    def _should_process(self, path: Path) -> bool:
        """Check if file should be processed."""
        # Check extension
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False

        # Check debounce
        now = time.time()
        last_time = self._last_triggered.get(path, 0)
        if now - last_time < self.DEBOUNCE_SECONDS:
            return False

        self._last_triggered[path] = now
        return True

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        path = Path(str(event.src_path))
        if self._should_process(path):
            self.on_file_change(path)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return

        path = Path(str(event.src_path))
        if self._should_process(path):
            self.on_file_change(path)


class FileWatcher:
    """Watches a directory for file changes and triggers callbacks."""

    def __init__(
        self,
        watch_path: Path,
        on_file_change: Callable[[Path], None],
        recursive: bool = False,
    ) -> None:
        """
        Initialize file watcher.

        Args:
            watch_path: Directory to watch.
            on_file_change: Callback when a file changes.
            recursive: Whether to watch subdirectories.
        """
        self.watch_path = watch_path
        self.recursive = recursive
        self.handler = ConversionEventHandler(on_file_change, recursive)
        self.observer = Observer()
        self._running = False

    def start(self) -> None:
        """Start watching for file changes."""
        self.observer.schedule(
            self.handler,
            str(self.watch_path),
            recursive=self.recursive,
        )
        self.observer.start()
        self._running = True

    def stop(self) -> None:
        """Stop watching."""
        if self._running:
            self.observer.stop()
            self.observer.join()
            self._running = False

    def wait(self) -> None:
        """Wait for observer thread (blocking)."""
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    @property
    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running
