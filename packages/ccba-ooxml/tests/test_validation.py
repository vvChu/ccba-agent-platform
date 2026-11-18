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


def _create_n_xml_docx_fixture(base_dir: Path, extra_parts: int = 13) -> tuple[Path, Path]:
    """Create a synthetic unpacked+zipped .docx with 16 XML/.rels parts."""
    unpacked = base_dir / "unpacked_16"
    (unpacked / "_rels").mkdir(parents=True)
    (unpacked / "word" / "_rels").mkdir(parents=True)
    (unpacked / "customXml").mkdir(parents=True)

    ct_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )
    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>Hello</w:t></w:r></w:p></w:body></w:document>"
    )
    word_rels_items = [
        '<Relationship Id="rId'
        + str(i)
        + '" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXml" '
        + f'Target="../customXml/item{i}.xml"/>'
        for i in range(1, extra_parts + 1)
    ]
    word_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(word_rels_items)
        + "</Relationships>"
    )
    files: dict[str, str] = {
        "[Content_Types].xml": ct_xml,
        "_rels/.rels": root_rels,
        "word/_rels/document.xml.rels": word_rels,
        "word/document.xml": doc_xml,
    }
    for i in range(1, extra_parts + 1):
        files[f"customXml/item{i}.xml"] = '<?xml version="1.0" encoding="UTF-8"?><root/>'

    # Exclude word/_rels/document.xml.rels or count carefully: 4 + 12 = 16 XML/.rels files
    for rel, body in files.items():
        target = unpacked / rel
        target.write_text(body, encoding="utf-8")

    orig_docx = base_dir / "fixture_16.docx"
    with zipfile.ZipFile(orig_docx, "w") as zf:
        for rel, body in files.items():
            zf.writestr(rel, body)
    return unpacked, orig_docx


@pytest.mark.fast
def test_ooxml_validator_16_xml_single_parse_and_quiet_stdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify 16-file .docx runs <=16 unpacked parses, 0 parser=None, and emits no stdout."""
    import lxml.etree

    from ccba_ooxml.validation import DOCXSchemaValidator

    unpacked, orig_docx = _create_n_xml_docx_fixture(tmp_path, extra_parts=12)
    schemas_dir = Path(__file__).resolve().parents[1] / "src" / "ccba_ooxml" / "schemas"
    for key in ("word", "[Content_Types].xml", ".rels"):
        DOCXSchemaValidator.get_compiled_schema(
            schemas_dir / DOCXSchemaValidator.SCHEMA_MAPPINGS[key], schemas_dir
        )

    real_parse = lxml.etree.parse
    unpacked_calls: list[tuple[str, object]] = []
    all_none_parsers: list[str] = []
    unpacked_resolved = str(unpacked.resolve())

    def spy_parse(source, parser=None, **kwargs):
        src_str = str(getattr(source, "name", source))
        if parser is None:
            all_none_parsers.append(src_str)
        if src_str.startswith(unpacked_resolved):
            unpacked_calls.append((src_str, parser))
        return real_parse(source, parser=parser, **kwargs)

    monkeypatch.setattr(lxml.etree, "parse", spy_parse)
    report = OOXMLValidator(unpacked, orig_docx, verbose=False).validate_report()
    captured = capsys.readouterr()

    assert captured.out == ""
    assert all_none_parsers == []
    assert len(unpacked_calls) <= 16
    assert report.is_valid is True
    assert report.issues == []


@pytest.mark.fast
def test_malformed_xml_reports_file_path_line_number_and_quiet_stdout(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify malformed word/document.xml reports file_path and line_number without stdout."""
    unpacked, orig_docx = _create_n_xml_docx_fixture(tmp_path, extra_parts=2)
    bad_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
        "  <w:body>\n"
        "    <w:p><w:unclosed></w:p>\n"
        "  </w:body>\n"
        "</w:document>\n"
    )
    (unpacked / "word" / "document.xml").write_text(bad_xml, encoding="utf-8")

    report = OOXMLValidator(unpacked, orig_docx, verbose=False).validate_report()
    captured = capsys.readouterr()

    assert captured.out == ""
    assert report.is_valid is False
    assert any(
        issue.file_path == "word/document.xml" and issue.line_number is not None
        for issue in report.issues
    )


@pytest.mark.fast
def test_redlining_validator_claude_tracked_changes_and_clone_isolation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify RedliningValidator strips Claude tracked changes on clones without stdout."""
    from ccba_ooxml.validation import RedliningValidator
    from ccba_ooxml.validation.base import ParsedOOXMLPackage

    w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    orig_doc = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<w:document xmlns:w="{w_ns}">'
        "<w:body><w:p><w:r><w:t>Alpha Beta</w:t></w:r></w:p></w:body></w:document>"
    )
    orig_docx = tmp_path / "orig_redline.docx"
    with zipfile.ZipFile(orig_docx, "w") as zf:
        zf.writestr("word/document.xml", orig_doc)

    unpacked = tmp_path / "unpacked_redline"
    (unpacked / "word").mkdir(parents=True)
    tracked_doc = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<w:document xmlns:w="{w_ns}">'
        "<w:body><w:p>"
        "<w:r><w:t>Alpha </w:t></w:r>"
        '<w:del w:id="1" w:author="Claude"><w:r><w:delText>Beta</w:delText></w:r></w:del>'
        '<w:ins w:id="2" w:author="Claude"><w:r><w:t>Gamma</w:t></w:r></w:ins>'
        "</w:p></w:body></w:document>"
    )
    doc_path = unpacked / "word" / "document.xml"
    doc_path.write_text(tracked_doc, encoding="utf-8")

    pkg = ParsedOOXMLPackage(unpacked)
    validator = RedliningValidator(unpacked, orig_docx, verbose=False, parsed_package=pkg)
    assert validator.validate() is True
    assert capsys.readouterr().out == ""
    cached_root = pkg.get_root("word/document.xml")
    assert len(cached_root.findall(f".//{{{w_ns}}}ins")) == 1
    assert len(cached_root.findall(f".//{{{w_ns}}}delText")) == 1

    # Untracked text change alongside Claude edits must fail in RedliningValidator
    doc_path.write_text(tracked_doc.replace("Alpha ", "UntrackedEdit "), encoding="utf-8")
    report = OOXMLValidator(unpacked, orig_docx, verbose=False).validate_report()
    assert capsys.readouterr().out == ""
    assert report.is_valid is False
    assert any(issue.file_path == "word/document.xml" for issue in report.issues)
