"""Tests for the OOXMLValidator class."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from ccba_ooxml import unpack_document
from ccba_ooxml.validation import OOXMLValidator


def test_ooxml_validator_docx():
    """Verify that OOXMLValidator can validate a docx document."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock zip file resembling a minimal docx (with XML)
        mock_docx = temp_path / "test.docx"
        with zipfile.ZipFile(mock_docx, "w") as zf:
            zf.writestr(
                "[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?><Types>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                "</Types>",
            )
            # Minimal wml file
            zf.writestr(
                "word/document.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                "<w:body><w:p><w:t>Hello</w:t></w:p></w:body></w:document>",
            )

        # Unpack it
        unpack_dir = temp_path / "unpacked"
        unpack_document(mock_docx, unpack_dir)

        # Instantiate validator
        validator = OOXMLValidator(unpack_dir, mock_docx, verbose=True)

        # Test validation runs without exceptions
        result = validator.validate()
        assert isinstance(result, bool)
