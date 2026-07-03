"""Tests for the ccba-ooxml package."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from ccba_ooxml import pack_document, unpack_document


def test_unpack_and_pack_cycle():
    """Verify that unpack_document and pack_document can process a mock zip file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock zip file resembling a minimal docx (with XML)
        mock_docx = temp_path / "test.docx"
        with zipfile.ZipFile(mock_docx, "w") as zf:
            zf.writestr(
                "[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types></Types>'
            )
            zf.writestr(
                "word/document.xml",
                '<?xml version="1.0" encoding="UTF-8"?><document><body>Hello</body></document>',
            )

        # Unpack it
        unpack_dir = temp_path / "unpacked"
        unpack_document(mock_docx, unpack_dir)

        # Verify files unpacked and XML pretty printed
        doc_xml = unpack_dir / "word/document.xml"
        assert doc_xml.exists()
        content = doc_xml.read_text(encoding="utf-8")
        assert "  <body>" in content  # should be indented

        # Pack it back (without validation for mock file)
        repacked_docx = temp_path / "repacked.docx"
        success = pack_document(unpack_dir, repacked_docx, validate=False)

        assert success
        assert repacked_docx.exists()

        # Check content of repacked (should be compressed XML back)
        with zipfile.ZipFile(repacked_docx) as zf:
            repacked_content = zf.read("word/document.xml").decode("utf-8")
            assert "<body>Hello" in repacked_content
            # The condensed XML should not have excess indent spaces
            assert "  <body>" not in repacked_content
