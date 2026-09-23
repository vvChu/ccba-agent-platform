"""Unit & Integration Tests for Legislative Consolidator Deep Seam on Hub."""

from pathlib import Path

import pytest

from ccba_legal.consolidator.dual_mode_parser import (
    DualModeASTParser,
)
from ccba_legal.consolidator.manifest_generator import ManifestGenerator
from ccba_legal.consolidator.patch_manifest_schema import (
    DefectSeverity,
    DocMode,
    PatchAction,
    PatchItem,
    PatchManifest,
    load_manifest,
)
from ccba_legal.consolidator.patcher import (
    LegislativeConsolidator,
)


@pytest.fixture
def sample_qcvn_md() -> str:
    return """# QUY CHUẨN KỸ THUẬT QUỐC GIA VỀ THIẾT KẾ MẪU

## MỤC LỤC
- [1  QUY ĐỊNH CHUNG](#muc-1)
- [2  QUY ĐỊNH KỸ THUẬT](#muc-2)

---

### <a id="muc-1" name="muc-1"></a>1  QUY ĐỊNH CHUNG

#### <a id="muc-1-1" name="muc-1-1"></a>1.1  Phạm vi điều chỉnh
Quy chuẩn này quy định các yêu cầu kỹ thuật đối với nhà và công trình.

#### <a id="muc-1-1-2" name="muc-1-1-2"></a>1.1.2  Đối tượng áp dụng
Áp dụng cho các tòa nhà hỗn hợp và chung cư.

#### <a id="muc-1-3" name="muc-1-3"></a>1.3  Tài liệu viện dẫn
TCVN 3890:2023, Phương tiện PCCC.

### <a id="muc-2" name="muc-2"></a>2  QUY ĐỊNH KỸ THUẬT

#### <a id="muc-2-1" name="muc-2-1"></a>2.1  Bậc chịu lửa
Công trình phải đảm bảo bậc chịu lửa tối thiểu bậc II.
"""


@pytest.fixture
def sample_luat_md() -> str:
    return """# LUẬT XÂY DỰNG MẪU

## CHƯƠNG I. QUY ĐỊNH CHUNG

### Điều 1. Phạm vi điều chỉnh
Luật này quy định quyền và nghĩa vụ của cơ quan, tổ chức, cá nhân.

### Điều 2. Đối tượng áp dụng
Áp dụng đối với cơ quan, tổ chức, cá nhân trong nước.
"""


def test_manifest_schema_validation(tmp_path: Path):
    manifest_yaml = """
target_doc_id: qcvn_test
amending_doc_id: sua_doi_test
doc_mode: qcvn
title: Test Quy Chuẩn
official_citation: TT 99/2026/TT-BXD
effective_date: "2026-12-31"
patches:
  - action: REPLACE
    target_anchor: muc-1-1-2
    citation: Sửa đổi bởi TT 99/2026
    defect_severity: CRITICAL_DEFECT
    new_content_inline: Nội dung sửa đổi mới
"""
    mfile = tmp_path / "test_manifest.yaml"
    mfile.write_text(manifest_yaml, encoding="utf-8")

    manifest = load_manifest(mfile)
    assert manifest.target_doc_id == "qcvn_test"
    assert manifest.doc_mode == DocMode.QCVN
    assert len(manifest.patches) == 1
    assert manifest.patches[0].action == PatchAction.REPLACE


def test_dual_mode_parser_qcvn(sample_qcvn_md: str):
    parser = DualModeASTParser()
    nodes = parser.parse(sample_qcvn_md, mode=DocMode.QCVN)

    flat = parser.flatten_ast(nodes)
    assert "muc-1" in flat
    assert "muc-1-1" in flat
    assert "muc-1-1-2" in flat
    assert "muc-2-1" in flat


def test_dual_mode_parser_luat(sample_luat_md: str):
    parser = DualModeASTParser()
    nodes = parser.parse(sample_luat_md, mode=DocMode.LUAT)

    flat = parser.flatten_ast(nodes)
    assert "D1" in flat
    assert "D2" in flat


def test_insert_after_patch(sample_qcvn_md: str, tmp_path: Path):
    manifest = PatchManifest(
        target_doc_id="qcvn_test",
        amending_doc_id="tt_31_2026",
        doc_mode=DocMode.QCVN,
        patches=[
            PatchItem(
                action=PatchAction.INSERT_AFTER,
                target_anchor="muc-1-1-2",
                new_anchor="muc-1-1-3",
                citation="Bổ sung bởi Sửa đổi 01:2026",
                defect_severity=DefectSeverity.CRITICAL_DEFECT,
                new_content_inline="Quy định chỗ để xe điện áp dụng cho chung cư mới và hiện hữu.",
            )
        ],
    )

    base_file = tmp_path / "base.md"
    base_file.write_text(sample_qcvn_md, encoding="utf-8")

    consolidator = LegislativeConsolidator(manifest)
    res = consolidator.consolidate(base_file, output_dir=tmp_path / "out")

    assert res.success
    assert res.added_clauses == 1
    out_md = res.consolidated_md_path.read_text(encoding="utf-8")
    assert "muc-1-1-3" in out_md


def test_triple_output_generation(sample_qcvn_md: str, tmp_path: Path):
    manifest = PatchManifest(
        target_doc_id="qcvn_test",
        amending_doc_id="tt_31_2026",
        doc_mode=DocMode.QCVN,
        title="Quy Chuẩn Thử Nghiệm",
        official_citation="Thông tư 31/2026/TT-BXD",
        effective_date="2026-12-15",
        patches=[
            PatchItem(
                action=PatchAction.REPLACE,
                target_anchor="muc-2-1",
                citation="Sửa đổi bậc chịu lửa",
                defect_severity=DefectSeverity.CRITICAL_DEFECT,
                new_content_inline="Nội dung mới cho 2.1",
            )
        ],
    )

    base_file = tmp_path / "base.md"
    base_file.write_text(sample_qcvn_md, encoding="utf-8")

    consolidator = LegislativeConsolidator(manifest)
    res = consolidator.consolidate(base_file, output_dir=tmp_path / "out")

    assert res.consolidated_md_path.exists()
    assert res.clauses_json_path.exists()
    assert res.diff_matrix_path.exists()


def test_manifest_generator_mock(tmp_path: Path):
    mock_llm_json = """{
      "target_doc_id": "qcvn_mock",
      "amending_doc_id": "tt_mock",
      "doc_mode": "qcvn",
      "title": "Mock Quy Chuẩn",
      "official_citation": "Thông tư Mock",
      "effective_date": "2026-12-15",
      "default_cong_bao_number": "999/2026",
      "default_jurisdiction": "CQXD",
      "patches": [
        {
          "action": "INSERT_AFTER",
          "target_anchor": "muc-1-1-2",
          "new_anchor": "muc-1-1-3",
          "citation": "Bổ sung bởi TT Mock",
          "defect_severity": "CRITICAL_DEFECT",
          "new_content_inline": "Nội dung quy chuẩn mới."
        }
      ]
    }"""

    base_f = tmp_path / "base.md"
    base_f.write_text("# Mock base", encoding="utf-8")
    amend_f = tmp_path / "amend.md"
    amend_f.write_text("# Mock amend", encoding="utf-8")
    out_yaml = tmp_path / "out_manifest.yaml"

    gen = ManifestGenerator()
    manifest = gen.generate_manifest_from_files(
        base_md_path=base_f,
        amending_md_path=amend_f,
        output_yaml_path=out_yaml,
        mock_response=mock_llm_json,
    )

    assert manifest.target_doc_id == "qcvn_mock"
    assert len(manifest.patches) == 1
    assert out_yaml.exists()


def test_insert_range_multi_node_clean_anchors(sample_qcvn_md: str, tmp_path: Path):
    manifest = PatchManifest(
        target_doc_id="qcvn_test",
        amending_doc_id="tt_31_2026",
        doc_mode=DocMode.QCVN,
        patches=[
            PatchItem(
                action=PatchAction.INSERT_RANGE_AFTER,
                target_anchor="muc-1-1-2",
                new_anchors=["muc-1-1-3", "muc-1-1-4"],
                citation="Bổ sung bởi Sửa đổi 01:2026",
                defect_severity=DefectSeverity.CRITICAL_DEFECT,
                new_content_inline=(
                    '#### <a id="muc-1-1-3" name="muc-1-1-3"></a>1.1.3  Khoản thứ nhất\n\n'
                    "Nội dung khoản thứ nhất.\n\n"
                    '#### <a id="muc-1-1-4" name="muc-1-1-4"></a>1.1.4  Khoản thứ hai\n\n'
                    "Nội dung khoản thứ hai."
                ),
            )
        ],
    )

    base_file = tmp_path / "base.md"
    base_file.write_text(sample_qcvn_md, encoding="utf-8")

    consolidator = LegislativeConsolidator(manifest)
    res = consolidator.consolidate(base_file, output_dir=tmp_path / "out")

    assert res.success
    assert res.added_clauses == 2
    out_md = res.consolidated_md_path.read_text(encoding="utf-8")
    assert '<a id="muc-1-1-3" name="muc-1-1-3"></a><a id=' not in out_md
    assert "muc-1-1-3" in out_md
    assert "muc-1-1-4" in out_md


def test_handle_consolidate_cli(sample_qcvn_md: str, tmp_path: Path):
    from argparse import Namespace

    from ccba_legal.cli import handle_consolidate

    manifest_yaml = """
target_doc_id: qcvn_test
amending_doc_id: sua_doi_test
doc_mode: qcvn
title: Test Quy Chuẩn
official_citation: TT 99/2026/TT-BXD
effective_date: "2026-12-31"
patches:
  - action: REPLACE
    target_anchor: muc-1-1-2
    citation: Sửa đổi bởi TT 99/2026
    defect_severity: CRITICAL_DEFECT
    new_content_inline: Nội dung sửa đổi mới
"""
    mfile = tmp_path / "manifest.yaml"
    mfile.write_text(manifest_yaml, encoding="utf-8")
    base_file = tmp_path / "base.md"
    base_file.write_text(sample_qcvn_md, encoding="utf-8")
    out_dir = tmp_path / "out_cli"

    args = Namespace(
        manifest=str(mfile),
        base=str(base_file),
        output=str(out_dir),
        amending=None,
    )
    exit_code = handle_consolidate(args)
    assert exit_code == 0
    assert (out_dir / "base.md").exists() or (out_dir / "qcvn_test.md").exists()


def test_append_action_preserves_metadata(sample_qcvn_md: str, tmp_path: Path):
    manifest_yaml = """
target_doc_id: qcvn_test
amending_doc_id: sua_doi_test
doc_mode: qcvn
title: Test Quy Chuẩn
official_citation: TT 99/2026/TT-BXD
effective_date: "2026-12-31"
patches:
  - action: APPEND
    target_anchor: muc-1-1-2
    citation: Bổ sung bởi TT 99/2026
    defect_severity: CRITICAL_DEFECT
    jurisdiction: national
    grace_period_end: "2027-06-30"
    source_pdf_page: 42
    new_content_inline: Nội dung bổ sung thêm
"""
    mfile = tmp_path / "manifest.yaml"
    mfile.write_text(manifest_yaml, encoding="utf-8")
    base_file = tmp_path / "base.md"
    base_file.write_text(sample_qcvn_md, encoding="utf-8")
    out_dir = tmp_path / "out_append"

    manifest = load_manifest(mfile)
    consolidator = LegislativeConsolidator(manifest)
    res = consolidator.consolidate(base_file, output_dir=out_dir)
    assert res.success is True

    # Check clauses.json for amended metadata
    import json

    clauses_data = json.loads((out_dir / "clauses.json").read_text(encoding="utf-8"))
    target = next((c for c in clauses_data if c["id"] == "muc-1-1-2"), None)
    assert target is not None
    assert target.get("is_amended") is True
    assert target.get("jurisdiction") == "national"
    assert target.get("grace_period_end") == "2027-06-30"
    assert target.get("source_pdf_page") == 42
    assert "Nội dung bổ sung thêm" in target.get("content", "")
