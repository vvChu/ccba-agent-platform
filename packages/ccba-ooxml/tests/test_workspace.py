"""Tests for the OOXMLWorkspace Context Manager."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import pytest

from ccba_ooxml import OOXMLWorkspace


def test_ooxml_workspace_success_cycle():
    """Verify that OOXMLWorkspace can unpack, modify, and repack successfully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock zip file resembling a minimal docx
        mock_docx = temp_path / "test.docx"
        with zipfile.ZipFile(mock_docx, "w") as zf:
            zf.writestr(
                "[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types></Types>'
            )
            zf.writestr(
                "word/document.xml",
                '<?xml version="1.0" encoding="UTF-8"?><document><body>Hello</body></document>',
            )

        # Modify it via the workspace (without validation)
        with OOXMLWorkspace(mock_docx, validate=False) as ws:
            assert ws.working_dir is not None
            assert ws.working_dir.exists()

            # Read XML
            root = ws.read_xml("word/document.xml")
            body = root.find("body")
            assert body is not None
            assert body.text == "Hello"

            # Modify XML
            body.text = "Hello CCBA"
            ws.write_xml("word/document.xml", root)

        # Verify the original document is updated and the XML is condensed
        with zipfile.ZipFile(mock_docx) as zf:
            content = zf.read("word/document.xml").decode("utf-8")
            assert "<body>Hello CCBA</body>" in content
            assert "  <body>" not in content  # condensed


def test_ooxml_workspace_aborted_on_exception():
    """Verify that OOXMLWorkspace discards changes if an exception is raised inside."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock zip file
        mock_docx = temp_path / "test.docx"
        original_xml = (
            '<?xml version="1.0" encoding="UTF-8"?><document><body>Hello</body></document>'
        )
        with zipfile.ZipFile(mock_docx, "w") as zf:
            zf.writestr("[Content_Types].xml", "<Types></Types>")
            zf.writestr("word/document.xml", original_xml)

        # Modify it but raise exception
        with pytest.raises(RuntimeError):
            with OOXMLWorkspace(mock_docx, validate=False) as ws:
                root = ws.read_xml("word/document.xml")
                body = root.find("body")
                assert body is not None
                body.text = "Corrupted Text"
                ws.write_xml("word/document.xml", root)
                raise RuntimeError("Force failure")

        # Verify the original document was NOT updated
        with zipfile.ZipFile(mock_docx) as zf:
            content = zf.read("word/document.xml").decode("utf-8")
            assert "Corrupted Text" not in content
            assert "Hello" in content
