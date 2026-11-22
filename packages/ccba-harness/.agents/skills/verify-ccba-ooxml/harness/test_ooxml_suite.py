"""test_ooxml_suite.py - 6-Feature Contract & Statechart Bug-Path Replay Suite for ccba-ooxml.

Covers all features declared in `verify-ccba-ooxml/features/INDEX.md`:
- FEAT-OOX-001: PEP 562 _LAZY_EXPORTS (64 symbols), __all__ & __dir__ Parity
- FEAT-OOX-002: unpack_document Pretty-Printing, pack_document & condense_xml Behavior
- FEAT-OOX-003: OOXMLWorkspace Lifecycle, bug_path_1 (Inactive), bug_path_2 (Non-xlsx), bug_path_3 (Rollback)
- FEAT-OOX-004: TableReconstructor, StructuredTable & make_descriptive_table_slug
- FEAT-OOX-005: Statechart Anti-Lie, bug_path Parity & Symmetric Malformed-XML Warning (bug_path_4)
- FEAT-OOX-006: Surface Diff Parity, LF SHA-256 Provenance Lock & 4-State Drift Classifier
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest
import yaml
from docx import Document

import ccba_ooxml
from ccba_ooxml import (
    OOXMLWorkspace,
    StructuredTable,
    TableReconstructor,
    make_descriptive_table_slug,
    pack_document,
    unpack_document,
    vietnamese_to_ascii,
)
from ccba_ooxml.pack import condense_xml

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> Any:
    """Dynamically load run_verify_ooxml.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_ooxml.py"
    spec = importlib.util.spec_from_file_location("run_verify_ooxml", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_ooxml"] = mod
    spec.loader.exec_module(mod)
    return mod


def _extract_statechart_lines(skill_md: Path) -> list[str]:
    """Extract the first stateDiagram-v2 mermaid block from SKILL.md."""
    text = skill_md.read_text(encoding="utf-8")
    for block in re.findall(r"```mermaid\s*\n(.*?)```", text, flags=re.DOTALL):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip() and not ln.startswith("%%")]
        if lines and lines[0].startswith("stateDiagram"):
            return lines
    raise AssertionError(f"No stateDiagram block found in {skill_md}")


def _write_minimal_docx_zip(target: Path, doc_xml: str) -> None:
    """Write a minimal valid ZIP-packaged OOXML file in tmp_path."""
    with zipfile.ZipFile(target, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?><Types></Types>',
        )
        zf.writestr("word/document.xml", doc_xml)


def test_feat_oox_001_lazy_exports_and_dir_parity() -> None:
    """Verify FEAT-OOX-001: PEP 562 _LAZY_EXPORTS (72 symbols), __all__ & __dir__ parity."""
    assert len(ccba_ooxml.__all__) == 72
    assert set(ccba_ooxml.__all__) == set(ccba_ooxml._LAZY_EXPORTS.keys())

    dir_names = set(dir(ccba_ooxml))
    assert set(ccba_ooxml.__all__).issubset(dir_names)

    for sym in (
        "OOXMLWorkspace",
        "pack_document",
        "unpack_document",
        "TableReconstructor",
        "StructuredTable",
        "make_descriptive_table_slug",
        "vietnamese_to_ascii",
        "XlsxTemplateFiller",
        "XlsxWorkbookWriter",
        "XlsxReader",
    ):
        assert getattr(ccba_ooxml, sym) is not None

    missing_attr = "non_existent_ooxml_symbol_xyz"
    with pytest.raises(AttributeError, match="no attribute"):
        _ = getattr(ccba_ooxml, missing_attr)


def test_feat_oox_002_unpack_condense_and_pack_guards(tmp_path: Path) -> None:
    """Verify FEAT-OOX-002: unpack pretty-printing, condense_xml w:t retention & pack guards."""
    with pytest.raises(FileNotFoundError, match="Input file not found"):
        unpack_document(tmp_path / "missing.docx", tmp_path / "unpacked_missing")

    raw_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<!-- remove me --><w:body><w:p><w:r><w:t>  keep spaces  </w:t></w:r></w:p></w:body>"
        "</w:document>"
    )
    src_docx = tmp_path / "sample.docx"
    _write_minimal_docx_zip(src_docx, raw_xml)

    unpacked = tmp_path / "unpacked"
    unpack_document(src_docx, unpacked)
    pretty_text = (unpacked / "word" / "document.xml").read_text(encoding="utf-8")
    assert "\n" in pretty_text

    # Guard checks before successful pack
    with pytest.raises(ValueError, match="is not a directory"):
        pack_document(src_docx, tmp_path / "out.docx", validate=False)
    with pytest.raises(ValueError, match=r"must be a \.docx, \.pptx, or \.xlsx file"):
        pack_document(unpacked, tmp_path / "out.txt", validate=False)

    repacked = tmp_path / "repacked.docx"
    assert pack_document(unpacked, repacked, validate=False) is True
    with zipfile.ZipFile(repacked) as zf:
        packed_xml = zf.read("word/document.xml").decode("utf-8")
    assert "<!-- remove me -->" not in packed_xml
    assert "<w:t>  keep spaces  </w:t>" in packed_xml

    # Direct condense_xml smoke check preserves w:t whitespace
    single_xml = tmp_path / "inline.xml"
    single_xml.write_text(raw_xml, encoding="utf-8")
    condense_xml(single_xml)
    condensed = single_xml.read_text(encoding="utf-8")
    assert "remove me" not in condensed
    assert "<w:t>  keep spaces  </w:t>" in condensed


def test_feat_oox_003_workspace_lifecycle_and_bug_paths_1_2_3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify FEAT-OOX-003: OOXMLWorkspace missing file, path traversal, and bug_path_1/2/3."""
    with pytest.raises(FileNotFoundError, match="Source file not found"):
        with OOXMLWorkspace(tmp_path / "absent.docx", validate=False):
            pass

    # bug_path_1: Methods on inactive workspace raise RuntimeError
    inactive_ws = OOXMLWorkspace(tmp_path / "future.docx", validate=False)
    with pytest.raises(RuntimeError, match="Workspace is not active"):
        inactive_ws.validate_workspace()
    with pytest.raises(RuntimeError, match="Workspace is not active"):
        inactive_ws.get_file_path("word/document.xml")
    with pytest.raises(RuntimeError, match="Workspace is not active"):
        inactive_ws.get_docx_document()

    # Isolate calc.recalc_xlsx so soffice is never spawned even under mutation
    monkeypatch.setattr("ccba_ooxml.calc.recalc_xlsx", lambda *_a, **_kw: {"status": "recalc_mock"})

    docx_path = tmp_path / "work.docx"
    _write_minimal_docx_zip(
        docx_path,
        '<?xml version="1.0" encoding="UTF-8"?><document><body>Original Text</body></document>',
    )

    with OOXMLWorkspace(docx_path, validate=False) as ws:
        # bug_path_2: recalculate() on non-.xlsx returns error dictionary
        recalc_res = ws.recalculate()
        assert "error" in recalc_res
        assert ".xlsx" in recalc_res["error"]

        with pytest.raises(ValueError, match="Path traversal detected"):
            ws.get_file_path("../../etc/passwd")

        root = ws.read_xml("word/document.xml")
        body = root.find("body")
        assert body is not None
        body.text = "Updated Text"
        ws.write_xml("word/document.xml", root)
    assert ws.working_dir is None

    with zipfile.ZipFile(docx_path) as zf:
        assert "Updated Text" in zf.read("word/document.xml").decode("utf-8")

    # bug_path_3: Validation failure unlinks repacked temp, raises ValueError & keeps original
    monkeypatch.setattr("ccba_ooxml.pack.validate_document", lambda _p: False)
    before_bytes = docx_path.read_bytes()
    temp_dir_ref: Path | None = None
    with pytest.raises(ValueError, match="Failed to repack or validate"):
        with OOXMLWorkspace(docx_path, validate=True) as ws_fail:
            assert ws_fail.working_dir is not None
            temp_dir_ref = ws_fail.working_dir
            assert temp_dir_ref.exists()
            root = ws_fail.read_xml("word/document.xml")
            body = root.find("body")
            assert body is not None
            body.text = "Unvalidated Text"
            ws_fail.write_xml("word/document.xml", root)

    assert ws_fail.working_dir is None
    assert temp_dir_ref is not None and not temp_dir_ref.exists()
    assert docx_path.read_bytes() == before_bytes


def test_feat_oox_004_table_reconstructor_slugs_and_exports(tmp_path: Path) -> None:
    """Verify FEAT-OOX-004: TableReconstructor DOCX extraction, footnotes, exports & slugs."""
    assert vietnamese_to_ascii("Định mức bảng Độc lập") == "Dinh muc bang Doc lap"
    slug = make_descriptive_table_slug("1", "Bảng 1 - Danh mục vật tư và thiết bị")
    assert slug == "bang_01_danh_muc_vat_tu_thiet"

    docx_path = tmp_path / "tables_sample.docx"
    doc = Document()
    doc.add_paragraph("Bảng 1.2 - Thông số kỹ thuật")
    tbl = doc.add_table(rows=3, cols=2)
    tbl.rows[0].cells[0].text = "Hạng mục"
    tbl.rows[0].cells[1].text = "Giá trị"
    tbl.rows[1].cells[0].text = "Móng"
    tbl.rows[1].cells[1].text = "B25"
    tbl.rows[2].cells[0].text = "CHÚ THÍCH: Áp dụng theo TCVN"
    tbl.rows[2].cells[1].text = "CHÚ THÍCH: Áp dụng theo TCVN"
    doc.save(str(docx_path))

    extracted = TableReconstructor.extract_docx_tables(docx_path)
    assert len(extracted) == 1
    st: StructuredTable = extracted[0]
    assert st.num == "1.2"
    assert st.headers == ["Hạng mục", "Giá trị"]
    assert st.rows == [["Móng", "B25"]]
    assert st.footnotes == ["CHÚ THÍCH: Áp dụng theo TCVN"]

    md_table = st.to_markdown(anchor=True)
    assert '<a id="bang-1-2"></a>' in md_table
    assert "| Móng | B25 |" in md_table
    assert "_CHÚ THÍCH: Áp dụng theo TCVN_" in md_table

    assert st.to_json()["total_rows"] == 1
    assert "Hạng mục,Giá trị" in st.to_csv()

    raw_md = "### Bảng 1.2 - Bản cũ\n| Cũ |\n| --- |\n| X |\n"
    replaced = TableReconstructor.replace_markdown_tables(raw_md, extracted)
    assert "| Móng | B25 |" in replaced
    assert "| X |" not in replaced

    json_file, csv_file = TableReconstructor.save_table_exports(st, tmp_path / "tables_out")
    assert json.loads(json_file.read_text(encoding="utf-8"))["num"] == "1.2"
    assert csv_file.is_file()


def test_feat_oox_005_statechart_anti_lie_and_malformed_xml_bug_path_4(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify FEAT-OOX-005: Statechart Anti-Lie, bug_path parity & symmetric XML warning (bug_path_4)."""
    runner = _load_runner_module()
    if str(runner.REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(runner.REPO_ROOT))
    from tests.governance.test_statechart_anti_lie import (
        verify_bug_path_matches_statechart,
        verify_statechart_anti_lie,
    )

    skill_md = Path(__file__).resolve().parent.parent / "SKILL.md"
    assert verify_statechart_anti_lie(_extract_statechart_lines(skill_md)) == []
    assert verify_bug_path_matches_statechart(skill_md.read_text(encoding="utf-8")) == []

    # bug_path_4: both unpack_document & condense_xml warn to stderr and preserve raw XML safely
    raw_malformed = "<document><body><unclosed></document>"
    broken_docx = tmp_path / "broken_xml.docx"
    _write_minimal_docx_zip(broken_docx, raw_malformed)

    ws_broken = OOXMLWorkspace(broken_docx, validate=False)
    broken_dir_ref: Path | None = None
    with ws_broken:
        assert ws_broken.working_dir is not None
        broken_dir_ref = ws_broken.working_dir
        assert broken_dir_ref.exists()

    captured = capsys.readouterr()
    assert "Warning: Could not pretty print" in captured.err
    assert "Warning: Could not condense" in captured.err

    # Safe cleanup and raw XML content preserved
    assert ws_broken.working_dir is None
    assert broken_dir_ref is not None and not broken_dir_ref.exists()
    with zipfile.ZipFile(broken_docx) as zf:
        assert zf.read("word/document.xml").decode("utf-8") == raw_malformed


def test_feat_oox_006_surface_diff_provenance_and_drift_modes() -> None:
    """Verify FEAT-OOX-006: Surface Diff parity, LF SHA-256 provenance, and drift modes."""
    runner = _load_runner_module()
    skill_dir = Path(__file__).resolve().parent.parent
    features_idx = skill_dir / "features" / "INDEX.md"
    assert runner.verify_surface_diff(features_idx, Path(__file__).resolve()) == []

    fm = yaml.safe_load((skill_dir / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
    sync_sha = str(fm["sync_commit"])
    cov_paths = list(fm["covered_paths"])
    cov_hashes = dict(fm["covered_sha256"])
    assert set(cov_hashes.keys()) == set(cov_paths)
    assert runner.check_git_provenance(sync_sha, cov_paths, expected_sha256=cov_hashes) == []

    classify = runner.classify_drift_status
    assert (
        classify(
            env_blocked=False, suite_passed=True, contract_changed=False, intentional_change=False
        )
        == "in_sync"
    )
    assert (
        classify(
            env_blocked=False, suite_passed=True, contract_changed=True, intentional_change=True
        )
        == "updated"
    )
    assert (
        classify(
            env_blocked=False, suite_passed=False, contract_changed=True, intentional_change=False
        )
        == "bug"
    )
    assert (
        classify(
            env_blocked=True, suite_passed=False, contract_changed=False, intentional_change=False
        )
        == "blocked"
    )
