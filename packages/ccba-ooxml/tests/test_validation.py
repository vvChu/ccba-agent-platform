"""Tests for the OOXMLValidator class."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import pytest

from ccba_ooxml import unpack_document
from ccba_ooxml.validation import OOXMLValidator


@pytest.mark.slow
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

        # Test structured report validation
        report = validator.validate_report()
        assert hasattr(report, "is_valid")
        assert hasattr(report, "issues")
        assert hasattr(report, "validators_run")
        assert "DOCXSchemaValidator" in report.validators_run


@pytest.mark.fast
def test_make_secure_xml_parser_fresh_instance_per_call() -> None:
    """Verify _make_secure_xml_parser returns a fresh offline parser on every call."""
    from ccba_ooxml.validation.base import _make_secure_xml_parser

    p1 = _make_secure_xml_parser()
    p2 = _make_secure_xml_parser()
    assert p1 is not p2


@pytest.mark.fast
def test_parsed_ooxml_package_single_parse_and_immutable_clone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify ParsedOOXMLPackage parses once per file and clone_root isolates mutations."""
    import lxml.etree

    from ccba_ooxml.validation import BaseSchemaValidator
    from ccba_ooxml.validation.base import ParsedOOXMLPackage

    (tmp_path / "word").mkdir()
    doc_xml = tmp_path / "word" / "document.xml"
    doc_xml.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body><w:p><w:bookmarkStart w:id="1" w:name="a"/></w:p></w:body>'
        "</w:document>",
        encoding="utf-8",
    )

    real_parse = lxml.etree.parse
    parse_calls: list[tuple[str, object]] = []

    def spy_parse(source, parser=None, **kwargs):
        parse_calls.append((str(source), parser))
        return real_parse(source, parser=parser, **kwargs)

    monkeypatch.setattr(lxml.etree, "parse", spy_parse)
    pkg = ParsedOOXMLPackage(tmp_path)
    validator = BaseSchemaValidator(tmp_path, tmp_path / "orig.docx", parsed_package=pkg)

    assert validator.validate_xml() is True
    assert validator.validate_namespaces() is True
    assert validator.validate_unique_ids() is True
    assert len(parse_calls) == 1
    assert parse_calls[0][1] is not None

    cloned = pkg.clone_root("word/document.xml")
    cloned.clear()
    cached = pkg.get_root("word/document.xml")
    assert len(list(cached)) == 1


@pytest.mark.fast
def test_cond_xsd_dual_path_bypasses_cache_for_original_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify _validate_single_file_xsd uses fresh parser for extracted original_file."""
    import lxml.etree

    from ccba_ooxml.validation import BaseSchemaValidator
    from ccba_ooxml.validation.base import ParsedOOXMLPackage

    unpacked = tmp_path / "unpacked"
    unpacked.mkdir()
    unpacked_ct = unpacked / "[Content_Types].xml"
    unpacked_ct.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="xml" ContentType="application/xml"/>'
        "</Types>",
        encoding="utf-8",
    )

    orig_zip = tmp_path / "original.docx"
    with zipfile.ZipFile(orig_zip, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="xml" ContentType="application/xml"/>'
            "</Types>",
        )

    real_parse = lxml.etree.parse
    parsed_sources: list[str] = []

    def spy_parse(source, parser=None, **kwargs):
        label = getattr(source, "name", str(source))
        parsed_sources.append(str(label))
        return real_parse(source, parser=parser, **kwargs)

    pkg = ParsedOOXMLPackage(unpacked)
    validator = BaseSchemaValidator(unpacked, orig_zip, parsed_package=pkg)
    monkeypatch.setattr(lxml.etree, "parse", spy_parse)

    # First validation on unpacked caches unpacked/[Content_Types].xml
    ok, _ = validator._validate_single_file_xsd(unpacked_ct, unpacked)
    assert ok is True
    # Validation on original file MUST NOT hit unpacked cache
    orig_errors = validator._get_original_file_errors(unpacked_ct)
    assert orig_errors == set()
    assert any(
        str(unpacked_ct.resolve()) != src and "[Content_Types].xml" in src for src in parsed_sources
    )
