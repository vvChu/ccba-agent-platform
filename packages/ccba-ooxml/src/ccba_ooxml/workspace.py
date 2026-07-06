"""Workspace context manager for OOXML files (.docx, .pptx, .xlsx)"""

from __future__ import annotations

import logging
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as DET

from .pack import pack_document
from .unpack import unpack_document

logger = logging.getLogger(__name__)


class OOXMLWorkspace:
    """A context manager that manages the lifecycle of an unpacked OOXML document.

    Handles temporary directory extraction, XML parsing/serialization, and
    automatic validation and packing upon successful exit.
    """

    def __init__(self, file_path: str | Path, validate: bool = True) -> None:
        """Initialize the workspace manager.

        Args:
            file_path: Path to the target Office document.
            validate: Whether to validate the document on saving (default: True).
        """
        self.file_path = Path(file_path).resolve()
        self.validate = validate
        self._temp_dir_obj: tempfile.TemporaryDirectory[str] | None = None
        self.working_dir: Path | None = None

    def __enter__(self) -> OOXMLWorkspace:
        """Unpack the document and enter the context."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Source file not found: {self.file_path}")

        # Create temporary working directory
        self._temp_dir_obj = tempfile.TemporaryDirectory(prefix="ooxml_ws_")
        self.working_dir = Path(self._temp_dir_obj.name)

        # Unpack the document
        unpack_document(self.file_path, self.working_dir)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        """Pack changes, validate, and clean up workspace on exit."""
        try:
            if exc_type is None and self.working_dir:
                # If no exception occurred, pack and validate changes
                temp_output = self.working_dir.parent / f"repacked_{self.file_path.name}"

                # Pack and validate to a temporary file first to avoid corrupting original
                pack_success = pack_document(
                    self.working_dir, temp_output, validate=self.validate
                )

                if pack_success:
                    # Overwrite the original document only if packing & validation succeeded
                    shutil.copy2(temp_output, self.file_path)
                else:
                    raise ValueError(f"Failed to repack or validate the document: {self.file_path.name}")

                # Cleanup temp output
                if temp_output.exists():
                    temp_output.unlink()
        finally:
            # Always clean up the workspace temporary directory
            if self._temp_dir_obj:
                self._temp_dir_obj.cleanup()
                self._temp_dir_obj = None
                self.working_dir = None

        return False  # Do not suppress exceptions raised inside the with block

    def get_file_path(self, rel_path: str | Path) -> Path:
        """Get the absolute path to a file inside the workspace.

        Args:
            rel_path: Relative path from the workspace root.

        Returns:
            Path: Absolute path to the file.
        """
        if not self.working_dir:
            raise RuntimeError("Workspace is not active.")
        return (self.working_dir / rel_path).resolve()

    def read_xml(self, rel_path: str | Path) -> ET.Element:
        """Read and parse an XML file inside the workspace using defusedxml.

        Args:
            rel_path: Relative path to the XML file.

        Returns:
            xml.etree.ElementTree.Element: The root element of the XML.
        """
        file_path = self.get_file_path(rel_path)
        if not file_path.exists():
            raise FileNotFoundError(f"XML file not found in workspace: {rel_path}")

        tree = DET.parse(str(file_path))
        return tree.getroot()

    def write_xml(self, rel_path: str | Path, root: ET.Element) -> None:
        """Write an XML root element back to a file in the workspace.

        Args:
            rel_path: Relative path to the destination XML file.
            root: The XML root element to serialize.
        """
        file_path = self.get_file_path(rel_path)

        # Ensure parent directories exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        tree = ET.ElementTree(root)
        # Register namespaces to prevent ns0 prefixes if present
        # (Minidom/condense will handle formatting, we just output standard XML)
        tree.write(str(file_path), encoding="utf-8", xml_declaration=True)
