"""test_legal_intel_suite.py - 6-Feature Contract & Statechart Bug-Path Replay Suite for ccba-legal-intel.

Covers all features declared in `verify-ccba-legal-intel/features/INDEX.md`:
- FEAT-LEG-001: PEP 562 _LAZY_EXPORTS (148 symbols), __all__ & __dir__ Parity
- FEAT-LEG-002: DynamicStatutoryResolver 3-Tier, Historical Predecessor (bug_path_2) & Date Guard (bug_path_1)
- FEAT-LEG-003: LegalGroundingGate, Link Exclusion, Authority Audits & National Fallback (bug_path_3)
- FEAT-LEG-004: ASTParser Hierarchy (D1-K1-Pa) & DeltaPatch Serialization Roundtrip
- FEAT-LEG-005: Statechart Anti-Lie, bug_path Parity & VBHNEngine Merge + Unmatched Skip (bug_path_4)
- FEAT-LEG-006: Surface Diff Parity, LF SHA-256 Provenance Lock & 4-State Drift Classifier
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

import ccba_legal
from ccba_legal import (
    ASTParser,
    DeltaPatch,
    DeltaPatchItem,
    DynamicStatutoryResolver,
    LegalGroundingGate,
    MergedLegalDocument,
    PatchAction,
    StatutoryRole,
    VBHNEngine,
    clear_resolver_cache,
    format_grounded_response,
    resolve_statutory_doc,
    verify_legal_grounding,
)
from ccba_legal import currency_resolver as leg_curr

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> Any:
    """Dynamically load run_verify_legal_intel.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_legal_intel.py"
    spec = importlib.util.spec_from_file_location("run_verify_legal_intel", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_legal_intel"] = mod
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


def test_feat_leg_001_lazy_exports_and_dir_parity() -> None:
    """Verify FEAT-LEG-001: PEP 562 _LAZY_EXPORTS (148 symbols), __all__ & __dir__ parity."""
    assert len(ccba_legal.__all__) == 148
    assert set(ccba_legal.__all__) == set(ccba_legal._LAZY_EXPORTS.keys())
    assert set(ccba_legal.__all__).issubset(set(dir(ccba_legal)))

    for sym in (
        "LegalGroundingGate",
        "DynamicStatutoryResolver",
        "resolve_statutory_doc",
        "ASTParser",
        "DeltaPatch",
        "VBHNEngine",
        "MergedLegalDocument",
    ):
        assert getattr(ccba_legal, sym) is not None

    missing_attr = "non_existent_legal_symbol_xyz"
    with pytest.raises(AttributeError, match="no attribute"):
        _ = getattr(ccba_legal, missing_attr)


def test_feat_leg_002_dynamic_statutory_resolver_and_temporal_invariance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify FEAT-LEG-002: DynamicStatutoryResolver 3-tier resolution, bug_path_1 & bug_path_2."""
    clear_resolver_cache()

    # bug_path_1: Invalid evaluation_date format raises ValueError
    with pytest.raises(ValueError, match="Invalid evaluation_date format"):
        resolve_statutory_doc(StatutoryRole.CONSTRUCTION_LAW, "invalid-date-fmt")

    # Isolate Tier 3 deterministic fallback inside tmp_path
    monkeypatch.setattr(
        leg_curr, "discover_master_registry_path", lambda _p=None: tmp_path / "missing.yaml"
    )
    monkeypatch.setattr(leg_curr, "resolve_project_root", lambda: tmp_path)
    monkeypatch.setattr(leg_curr, "_discover_currency_card_path", lambda: None)

    active_vn = DynamicStatutoryResolver.resolve_statutory_doc(
        StatutoryRole.CONSTRUCTION_LAW, "15/07/2026"
    )
    assert active_vn.doc_number == "135/2025/QH15"
    assert active_vn.status == "active"
    assert active_vn.source_origin == "fallback"

    # bug_path_2: Historical evaluation_date resolves superseded counterpart
    hist_doc = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_LAW, "2024-01-15")
    assert hist_doc.doc_number == "50/2014/QH13"
    assert hist_doc.status == "superseded"
    assert hist_doc.source_origin == "fallback"

    # Tier 2 currency card resolution in tmp_path
    card_file = tmp_path / "legal_currency_card.json"
    card_file.write_text(
        json.dumps(
            {
                "statutory_replacements": [
                    {
                        "domain": "Luật Xây dựng",
                        "document_number": "135/2025/QH15",
                        "effective_date": "2026-07-01",
                        "title": "Luật Xây dựng 2025 (Card)",
                        "supersedes": ["50/2014/QH13"],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(leg_curr, "_discover_currency_card_path", lambda: card_file)
    tier2 = resolve_statutory_doc("CONSTRUCTION_LAW", "2026-07-02")
    assert tier2.source_origin == "currency_card"
    assert tier2.doc_number == "135/2025/QH15"


def test_feat_leg_003_grounding_gate_citations_and_national_fallback() -> None:
    """Verify FEAT-LEG-003: LegalGroundingGate, link exclusion, authority check & bug_path_3."""
    docs = [
        {
            "id": "luat-xd-2025",
            "document_number": "135/2025/QH15",
            "short_name": "Luật Xây dựng 2025",
            "territory": "VN",
        }
    ]
    gate = LegalGroundingGate(default_jurisdiction="VN-HN")

    ok = gate.verify("Áp dụng theo [135/2025/QH15] về thẩm định thiết kế.", docs)
    assert ok["is_grounded"] is True
    assert ok["valid_citations"] == ["135/2025/QH15"]
    assert ok["is_national_fallback"] is True

    formatted_ok = gate.format("Áp dụng [135/2025/QH15].", docs)
    assert "Lưu ý Lãnh thổ (National Fallback)" in formatted_ok
    assert "⚠️ **Disclaimer:**" in formatted_ok

    # bug_path_3: Standard Markdown link [text](url) does NOT satisfy standalone citation regex
    ungrounded = format_grounded_response(
        "Xem thêm [Luật 135/2025/QH15](https://example.com) để biết chi tiết.",
        docs,
        jurisdiction="VN",
    )
    assert "Cảnh báo: Câu trả lời thiếu trích dẫn nguồn văn bản pháp lý hợp lệ" in ungrounded

    # Dissolved district authority post-2025-07-01 fails grounding even with valid citation
    bad_auth = verify_legal_grounding(
        "Theo [135/2025/QH15], UBND Quận thẩm định trực tiếp hồ sơ.",
        docs,
        jurisdiction="VN-HN",
    )
    assert bad_auth["is_grounded"] is False
    assert len(bad_auth["authority_violations"]) >= 1


def test_feat_leg_004_ast_parser_hierarchy_and_delta_patch_roundtrip() -> None:
    """Verify FEAT-LEG-004: ASTParser tree structure and DeltaPatch roundtrip serialization."""
    md = (
        "### Điều 1. Phạm vi điều chỉnh\n"
        "1. Quy định chung về quản lý dự án.\n"
        "a) Dự án sử dụng vốn đầu tư công.\n"
        "### Điều 2. Giải thích từ ngữ\n"
        "Nội dung chung.\n"
    )
    parser = ASTParser()
    nodes = parser.parse_markdown(md)
    flat = parser.flatten_ast(nodes)
    assert set(flat.keys()) == {"D1", "D1-K1", "D1-K1-Pa", "D2"}

    point = parser.find_node(nodes, "D1-K1-Pa")
    assert point is not None and point.parent_id == "D1-K1"
    assert "vốn đầu tư công" in point.content

    patch = DeltaPatch(
        target_doc_id="base-1",
        amending_doc_id="amend-2",
        patches=[
            DeltaPatchItem(
                node_id="D1-K1",
                action=PatchAction.REPLACE,
                old_text_anchor="1. Quy định chung",
                new_content="1. Quy định sửa đổi theo NĐ 217/2026/NĐ-CP.",
                citation="Khoản 1 Điều 2",
            )
        ],
    )
    restored = DeltaPatch.from_dict(patch.to_dict())
    assert restored.target_doc_id == "base-1"
    assert restored.patches[0].action == PatchAction.REPLACE


def test_feat_leg_005_statechart_anti_lie_and_vbhn_merge_bug_path_4(tmp_path: Path) -> None:
    """Verify FEAT-LEG-005: Statechart Anti-Lie, bug_path parity & VBHNEngine merge (bug_path_4)."""
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

    # bug_path_4: Apply REPLACE, ABROGATE, INSERT_AFTER and safely skip missing node_id D99-K9
    base_md = (
        "### Điều 1. Nguyên tắc\n1. Nội dung gốc khoản 1.\n### Điều 2. Quy định cũ\n1. Bị bãi bỏ.\n"
    )
    patch = DeltaPatch(
        target_doc_id="base",
        amending_doc_id="amend",
        patches=[
            DeltaPatchItem(
                node_id="D1-K1",
                action=PatchAction.REPLACE,
                new_content="1. Nội dung cập nhật khoản 1.",
                citation="Điều 3 SĐ",
            ),
            DeltaPatchItem(
                node_id="D1-K1",
                action=PatchAction.INSERT_AFTER,
                new_content="2. Khoản bổ sung mới.",
                citation="Điều 4 SĐ",
            ),
            DeltaPatchItem(
                node_id="D2",
                action=PatchAction.ABROGATE,
                citation="Bãi bỏ toàn Điều 2",
            ),
            DeltaPatchItem(
                node_id="D99-K9",
                action=PatchAction.REPLACE,
                new_content="Không được chèn vì node không tồn tại.",
            ),
        ],
    )
    out_vbhn = tmp_path / "vbhn" / "VBHN_out.md"
    merged: MergedLegalDocument = VBHNEngine().merge_documents(
        base_md,
        patch,
        doc_meta={"title": "VBHN Hợp Nhất"},
        output_path=out_vbhn,
    )
    assert out_vbhn.is_file()
    assert "Nội dung cập nhật khoản 1." in merged.content
    assert "Khoản bổ sung mới." in merged.content
    assert "Đã bị bãi bỏ: Bãi bỏ toàn Điều 2" in merged.content
    assert "Không được chèn vì node không tồn tại." not in merged.content
    assert merged.patch_summary["abrogated"] == 1
    assert merged.patch_summary["inserted"] == 1


def test_feat_leg_006_surface_diff_provenance_and_drift_modes() -> None:
    """Verify FEAT-LEG-006: Surface Diff parity, LF SHA-256 provenance, and drift modes."""
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
