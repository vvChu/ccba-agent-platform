"""
Core module for standardizing and patching relative links in Markdown documents.
Provides a Deep Module interface supporting both in-memory strings and file/directory targets.
"""

import re
from pathlib import Path


class LinkPatcher:
    """Deep module for standardizing relative markdown links (e.g. appendices/ -> ./appendices/).

    Encapsulates regex matching for both text links [text](appendices/...) and image links
    ![alt](appendices/...), avoiding accidental modification of links already prefixed with ./ or ../.
    """

    # Matches Markdown link destination starting with appendices/ that is NOT preceded by . or / or \
    LINK_PATTERN = re.compile(r"(?<=[\(\"])(?<![\./\\])appendices/", re.IGNORECASE)

    def patch_content(self, content: str) -> tuple[str, int]:
        """Standardizes relative appendix links inside a raw Markdown string.

        Args:
            content: Raw Markdown content string.

        Returns:
            Tuple of (patched_content, count_of_links_patched).
        """
        patched_content, count = self.LINK_PATTERN.subn("./appendices/", content)
        return patched_content, count

    def patch_file(self, file_path: Path) -> bool:
        """Standardizes relative links in a single Markdown file on disk.

        Args:
            file_path: Path to the target Markdown file.

        Returns:
            True if the file was modified, False otherwise.
        """
        if not file_path.exists() or not file_path.is_file():
            return False

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return False

        new_content, count = self.patch_content(content)
        if count > 0 and new_content != content:
            file_path.write_text(new_content, encoding="utf-8")
            return True

        return False

    def patch_links(self, target_path: Path) -> list[Path]:
        """Scans and standardizes relative links in markdown files (file or directory).

        Args:
            target_path: Path to a markdown file or directory containing markdown files.

        Returns:
            List of Paths of files that were modified.
        """
        if not target_path.exists():
            return []

        files_to_patch: list[Path] = []
        if target_path.is_dir():
            files_to_patch.extend(target_path.rglob("*.md"))
        else:
            files_to_patch.append(target_path)

        modified_files: list[Path] = []
        for fpath in files_to_patch:
            if self.patch_file(fpath):
                modified_files.append(fpath)

        return modified_files
