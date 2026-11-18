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


def _build_unpacked_pptx(base_dir: Path, name: str = "deck.pptx") -> tuple[Path, Path]:
    """Create a 2-slide PPTX via DeckBuilder and unpack it into ``base_dir``."""
    from ccba_ooxml import build_presentation_from_markdown

    md_content = (
        '---\ntitle: "Kiem Dinh PPTX"\nauthor: "CCBA"\n---\n\n'
        "# Slide 1\n- Muc 1\n\n# Slide 2\n- Muc 2\n"
    )
    pptx_path = base_dir / name
    build_presentation_from_markdown(md_content, pptx_path)
    unpacked = base_dir / f"unpacked_{pptx_path.stem}"
    unpack_document(str(pptx_path), str(unpacked))
    return unpacked, pptx_path


def _prewarm_pptx_schemas() -> None:
    """Prewarm compiled XSD schemas for PPTX before attaching parse spies."""
    from ccba_ooxml.validation import PPTXSchemaValidator

    schemas_dir = Path(__file__).resolve().parents[1] / "src" / "ccba_ooxml" / "schemas"
    for key in ("ppt", ".rels", "[Content_Types].xml", "theme", "app.xml", "core.xml"):
        PPTXSchemaValidator.get_compiled_schema(
            schemas_dir / PPTXSchemaValidator.SCHEMA_MAPPINGS[key], schemas_dir
        )


def _snapshot_slide_xml(unpacked_dir: Path) -> dict[str, bytes]:
    """Read and serialize slide XML roots outside the measurement spy window."""
    import lxml.etree

    from ccba_ooxml.validation.base import make_secure_xml_parser

    snapshots: dict[str, bytes] = {}
    for slide_file in sorted((unpacked_dir / "ppt" / "slides").glob("slide*.xml")):
        rel = slide_file.relative_to(unpacked_dir).as_posix()
        root = lxml.etree.parse(str(slide_file), parser=make_secure_xml_parser()).getroot()
        snapshots[rel] = lxml.etree.tostring(root)
    return snapshots


def _make_parse_spy(unpacked_dir: Path, unpacked_calls: list[str], none_parsers: list[str]):
    """Build an ``lxml.etree.parse`` spy tracking unpacked calls and parser=None."""
    import lxml.etree

    real_parse = lxml.etree.parse
    unpacked_prefix = str(unpacked_dir.resolve())

    def spy_parse(source, parser=None, **kwargs):
        src_str = str(getattr(source, "name", source))
        if parser is None:
            none_parsers.append(src_str)
        if src_str.startswith(unpacked_prefix):
            unpacked_calls.append(src_str)
        return real_parse(source, parser=parser, **kwargs)

    return spy_parse


def _assert_ooxml_pptx_report_window(
    unpacked: Path,
    pptx_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    unpacked_calls: list[str],
    none_parsers: list[str],
) -> None:
    """Measure OOXMLValidator.validate_report() capturing its single ParsedOOXMLPackage."""
    from ccba_ooxml.validation import PPTXSchemaValidator
    from ccba_ooxml.validation.base import ParsedOOXMLPackage

    captured_pkgs: list[ParsedOOXMLPackage] = []
    orig_init = PPTXSchemaValidator.__init__

    def wrapped_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        captured_pkgs.append(self.parsed_package)

    monkeypatch.setattr(PPTXSchemaValidator, "__init__", wrapped_init)
    report = OOXMLValidator(unpacked, pptx_path, verbose=False).validate_report()
    assert capsys.readouterr().out == ""
    assert len(captured_pkgs) == 1
    assert none_parsers == []
    assert len(unpacked_calls) <= len(captured_pkgs[0].xml_files)
    assert report.is_valid is True
    assert report.issues == []
    assert "PPTXSchemaValidator" in report.validators_run


@pytest.mark.fast
def test_pptx_single_parse_oracle_and_clone_isolation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify PPTX validation runs <=N parses, 0 parser=None, quiet stdout, and clone safety."""
    import lxml.etree

    from ccba_ooxml.validation import PPTXSchemaValidator
    from ccba_ooxml.validation.base import ParsedOOXMLPackage

    unpacked, pptx_path = _build_unpacked_pptx(tmp_path)
    _prewarm_pptx_schemas()
    before_bytes = _snapshot_slide_xml(unpacked)
    assert before_bytes

    unpacked_calls: list[str] = []
    none_parsers: list[str] = []
    spy_parse = _make_parse_spy(unpacked, unpacked_calls, none_parsers)

    # Window A: direct PPTXSchemaValidator with shared ParsedOOXMLPackage
    pkg = ParsedOOXMLPackage(unpacked)
    monkeypatch.setattr(lxml.etree, "parse", spy_parse)
    validator = PPTXSchemaValidator(unpacked, pptx_path, verbose=False, parsed_package=pkg)
    assert validator.validate() is True
    assert capsys.readouterr().out == ""
    assert none_parsers == []
    assert len(unpacked_calls) <= len(pkg.xml_files)
    for slide_rel, expected_bytes in before_bytes.items():
        root_after = pkg.get_root(slide_rel)
        assert root_after is pkg.get_root(slide_rel)
        assert lxml.etree.tostring(root_after) == expected_bytes

    # Window B: OOXMLValidator.validate_report() capturing its single internal package
    unpacked_calls.clear()
    none_parsers.clear()
    _assert_ooxml_pptx_report_window(
        unpacked, pptx_path, monkeypatch, capsys, unpacked_calls, none_parsers
    )


def _assert_uuid_and_duplicate_layout_diags(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify UUID hex validation and duplicate slideLayout diagnostics + verbose parity."""
    from ccba_ooxml.validation import PPTXSchemaValidator

    unpacked, pptx_path = _build_unpacked_pptx(tmp_path / "uuid_dup", "uuid_dup.pptx")
    slide1 = unpacked / "ppt" / "slides" / "slide1.xml"
    slide1.write_text(
        slide1.read_text(encoding="utf-8").replace(
            'id="1"', 'id="{12345678-1234-1234-1234-12345678901Z}"', 1
        ),
        encoding="utf-8",
    )
    slide_rels = unpacked / "ppt" / "slides" / "_rels" / "slide1.xml.rels"
    extra_rel = (
        '<Relationship Id="rId99" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" '
        'Target="../slideLayouts/slideLayout1.xml"/>\n'
    )
    slide_rels.write_text(
        slide_rels.read_text(encoding="utf-8").replace(
            "</Relationships>", f"{extra_rel}</Relationships>"
        ),
        encoding="utf-8",
    )

    report = OOXMLValidator(unpacked, pptx_path, verbose=False).validate_report()
    assert capsys.readouterr().out == ""
    assert report.is_valid is False
    uuid_issues = [i for i in report.issues if "invalid hex characters" in i.message]
    assert uuid_issues and uuid_issues[0].file_path == "ppt/slides/slide1.xml"
    assert uuid_issues[0].line_number is not None
    dup_issues = [i for i in report.issues if "slideLayout references" in i.message]
    assert dup_issues and dup_issues[0].file_path == "ppt/slides/_rels/slide1.xml.rels"
    assert dup_issues[0].line_number is not None

    v_loud = PPTXSchemaValidator(unpacked, pptx_path, verbose=True)
    assert v_loud.validate_uuid_ids() is False
    assert "FAILED - Found 1 UUID ID validation errors:" in capsys.readouterr().out
    assert v_loud.validate_no_duplicate_slide_layouts() is False
    dup_out = capsys.readouterr().out
    assert "FAILED - Found slides with duplicate slideLayout references:" in dup_out
    assert "  ppt/slides/_rels/slide1.xml.rels: has 2 slideLayout references" in dup_out


def _assert_slide_layout_diagnostics(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify bad r:id, malformed .rels, and missing .rels diagnostics in slideMasters."""
    from ccba_ooxml.validation import PPTXSchemaValidator

    unpacked, pptx_path = _build_unpacked_pptx(tmp_path / "layout_case", "layout.pptx")
    master = unpacked / "ppt" / "slideMasters" / "slideMaster1.xml"
    master.write_text(
        master.read_text(encoding="utf-8").replace('r:id="rId1"', 'r:id="rIdMissing99"', 1),
        encoding="utf-8",
    )
    v_bad = PPTXSchemaValidator(unpacked, pptx_path, verbose=False)
    assert v_bad.validate_slide_layout_ids() is False
    assert capsys.readouterr().out == ""
    assert v_bad.last_diagnostics[0].file_path == "ppt/slideMasters/slideMaster1.xml"
    assert v_bad.last_diagnostics[0].line_number is not None

    v_loud = PPTXSchemaValidator(unpacked, pptx_path, verbose=True)
    assert v_loud.validate_slide_layout_ids() is False
    out = capsys.readouterr().out
    assert "FAILED - Found 1 slide layout ID validation errors:" in out
    assert "Remove invalid references or add missing slide layouts" in out

    master_rels = unpacked / "ppt" / "slideMasters" / "_rels" / "slideMaster1.xml.rels"
    master_rels.write_text("<Relationships>\n  <unclosed>\n</Relationships>", encoding="utf-8")
    v_mal = PPTXSchemaValidator(unpacked, pptx_path, verbose=False)
    assert v_mal.validate_slide_layout_ids() is False
    assert v_mal.last_diagnostics[0].file_path == "ppt/slideMasters/_rels/slideMaster1.xml.rels"
    assert v_mal.last_diagnostics[0].line_number is not None

    master_rels.unlink()
    v_miss = PPTXSchemaValidator(unpacked, pptx_path, verbose=False)
    assert v_miss.validate_slide_layout_ids() is False
    assert capsys.readouterr().out == ""
    assert v_miss.last_diagnostics[0].file_path == "ppt/slideMasters/slideMaster1.xml"
    assert v_miss.last_diagnostics[0].line_number is None
    assert (
        "Missing relationships file: ppt/slideMasters/_rels/slideMaster1.xml.rels"
        in v_miss.last_diagnostics[0].message
    )


def _build_notes_unpacked_fixture(base_dir: Path) -> Path:
    """Create unpacked slide .rels testing 3 notesSlide path forms + external URLs."""
    notes_dir = base_dir / "notes_unpacked"
    rels_dir = notes_dir / "ppt" / "slides" / "_rels"
    rels_dir.mkdir(parents=True)
    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    notes_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
    targets = {
        "slide1.xml.rels": [
            "../notesSlides/notesSlide1.xml",
            "https://example.com/notesSlide99.xml",
        ],
        "slide2.xml.rels": [
            "/ppt/notesSlides/notesSlide1.xml",
            "https://example.com/notesSlide99.xml",
        ],
        "slide3.xml.rels": ["../../ppt/notesSlides/notesSlide1.xml"],
    }
    for fname, tgt_list in targets.items():
        items = "".join(
            f'<Relationship Id="rId{i}" Type="{notes_type}" Target="{tgt}"/>\n'
            for i, tgt in enumerate(tgt_list, start=1)
        )
        (rels_dir / fname).write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="{rel_ns}">\n{items}</Relationships>\n',
            encoding="utf-8",
        )
    return notes_dir


def _assert_notes_canonicalization(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify notesSlide 3-form canonicalization and external URL exclusion."""
    from ccba_ooxml.validation import PPTXSchemaValidator

    notes_dir = _build_notes_unpacked_fixture(tmp_path)
    v_quiet = PPTXSchemaValidator(notes_dir, tmp_path / "notes.pptx", verbose=False)
    assert v_quiet.validate_notes_slide_references() is False
    assert capsys.readouterr().out == ""
    assert len(v_quiet.last_diagnostics) == 1
    diag = v_quiet.last_diagnostics[0]
    assert diag.file_path == "ppt/slides/_rels/slide2.xml.rels"
    assert diag.line_number is not None
    assert "ppt/notesSlides/notesSlide1.xml" in diag.message
    assert "slide1, slide2, slide3" in diag.message
    assert "https://" not in diag.message

    v_loud = PPTXSchemaValidator(notes_dir, tmp_path / "notes.pptx", verbose=True)
    assert v_loud.validate_notes_slide_references() is False
    out = capsys.readouterr().out
    assert "FAILED - Found 1 notes slide reference validation errors:" in out
    assert "    - ppt/slides/_rels/slide1.xml.rels" in out
    assert "    - ppt/slides/_rels/slide2.xml.rels" in out
    assert "    - ppt/slides/_rels/slide3.xml.rels" in out
    assert "Each slide may optionally have its own slide file." in out


def _assert_pptx_empty_guards(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify empty slideMasters/notes guards preserve collected_diagnostics."""
    from ccba_ooxml.validation import PPTXSchemaValidator

    empty_dir = tmp_path / "empty_pptx"
    empty_dir.mkdir()
    v_empty = PPTXSchemaValidator(empty_dir, tmp_path / "empty.pptx", verbose=True)
    assert v_empty.validate_content_types() is False
    assert len(v_empty.collected_diagnostics) == 1
    _ = capsys.readouterr()
    assert v_empty.validate_slide_layout_ids() is True
    assert v_empty.last_diagnostics == []
    assert v_empty.validate_notes_slide_references() is True
    assert v_empty.last_diagnostics == []
    assert len(v_empty.collected_diagnostics) == 1
    empty_out = capsys.readouterr().out
    assert "PASSED - No slide masters found" in empty_out
    assert "PASSED - No slide relationship files found" in empty_out


@pytest.mark.fast
def test_pptx_structured_diagnostics_notes_canonicalization_and_verbose_parity(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify PPTX structured diagnostics, notesSlide canonicalization, and verbose parity."""
    _assert_uuid_and_duplicate_layout_diags(tmp_path, capsys)
    _assert_slide_layout_diagnostics(tmp_path, capsys)
    _assert_notes_canonicalization(tmp_path, capsys)
    _assert_pptx_empty_guards(tmp_path, capsys)
