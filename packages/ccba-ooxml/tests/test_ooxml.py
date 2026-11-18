"""Tests for the ccba-ooxml package."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import pytest

from ccba_ooxml import OOXMLWorkspace, pack_document, unpack_document
from ccba_ooxml.pack import condense_xml

pytestmark = [pytest.mark.fast, pytest.mark.unit]


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


def test_condense_xml_malformed_warns_and_preserves_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify condense_xml warns to stderr, preserves raw XML, and keeps OOXMLWorkspace safe."""
    raw_malformed = "<document><body><unclosed></document>"
    bad_xml = tmp_path / "malformed.xml"
    bad_xml.write_text(raw_malformed, encoding="utf-8")

    condense_xml(bad_xml)
    assert "Warning: Could not condense" in capsys.readouterr().err
    assert bad_xml.read_text(encoding="utf-8") == raw_malformed

    broken_docx = tmp_path / "broken_roundtrip.docx"
    with zipfile.ZipFile(broken_docx, "w") as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types></Types>')
        zf.writestr("word/document.xml", raw_malformed)

    with OOXMLWorkspace(broken_docx, validate=False) as ws:
        assert ws.working_dir is not None and ws.working_dir.exists()

    err = capsys.readouterr().err
    assert "Warning: Could not pretty print" in err
    assert "Warning: Could not condense" in err
    assert ws.working_dir is None
    with zipfile.ZipFile(broken_docx) as zf:
        assert zf.read("word/document.xml").decode("utf-8") == raw_malformed


def test_pack_document_produces_deterministic_sha256_bytes(tmp_path: Path) -> None:
    """Verify repeated pack_document calls across distinct mtimes emit identical ZIP bytes."""
    import hashlib
    import os

    unpacked = tmp_path / "unpacked_det"
    (unpacked / "word").mkdir(parents=True)
    ct_path = unpacked / "[Content_Types].xml"
    doc_path = unpacked / "word" / "document.xml"
    ct_path.write_text('<?xml version="1.0" encoding="UTF-8"?><Types></Types>', encoding="utf-8")
    doc_path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?><document><body>Det</body></document>',
        encoding="utf-8",
    )

    out_1 = tmp_path / "det_1.docx"
    out_2 = tmp_path / "det_2.docx"
    assert pack_document(unpacked, out_1, validate=False) is True

    future_ts = 1_893_456_000.0
    os.utime(ct_path, (future_ts, future_ts))
    os.utime(doc_path, (future_ts, future_ts))
    assert pack_document(unpacked, out_2, validate=False) is True

    sha_1 = hashlib.sha256(out_1.read_bytes()).hexdigest()
    sha_2 = hashlib.sha256(out_2.read_bytes()).hexdigest()
    assert sha_1 == sha_2
    with zipfile.ZipFile(out_1) as zf:
        assert [info.filename for info in zf.infolist()] == [
            "[Content_Types].xml",
            "word/document.xml",
        ]
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in zf.infolist())
