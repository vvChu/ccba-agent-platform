"""test_notebooklm_suite.py - 6-Feature Contract & Statechart Bug-Path Replay Suite for ccba-notebooklm.

Covers all features declared in `verify-ccba-notebooklm/features/INDEX.md`:
- FEAT-NLM-001: Public Deep Seams (__all__ 15 symbols, 2-Tier Interface & Alias Parity)
- FEAT-NLM-002: Maskara Gate Upload Block (bug_path_1), Bypass (bug_path_2), Fail-Open (bug_path_3) & Prompt Gate
- FEAT-NLM-003: Registry Path Normalization, SHA-256 Persistence, Context Routing & Task State
- FEAT-NLM-004: Quota >= 90% Threshold & Orphan Garbage Collection Warn Replay (bug_path_4)
- FEAT-NLM-005: Statechart Anti-Lie, bug_path Parity & post_process_summary Idempotency
- FEAT-NLM-006: Surface Diff Parity, LF SHA-256 Provenance Lock & 4-State Drift Classifier
"""

from __future__ import annotations

import asyncio
import importlib.util
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

import ccba_notebooklm
from ccba_notebooklm import CCBANotebookLMClient, NotebookLMClient
from ccba_notebooklm import _gc as nlm_gc
from ccba_notebooklm import _registry as nlm_reg
from ccba_notebooklm import _security as nlm_sec
from ccba_notebooklm._artifacts import post_process_summary

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> Any:
    """Dynamically load run_verify_notebooklm.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_notebooklm.py"
    spec = importlib.util.spec_from_file_location("run_verify_notebooklm", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_notebooklm"] = mod
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


def _patch_registry_paths(monkeypatch: pytest.MonkeyPatch, sandbox: Path) -> None:
    """Redirect _registry global paths cleanly inside tmp_path."""
    monkeypatch.chdir(sandbox)
    monkeypatch.setattr(nlm_reg, "CONTEXT_FILE", sandbox / ".md" / "workspace_context.yaml")
    monkeypatch.setattr(
        nlm_reg, "REGISTRY_FILE", sandbox / ".md" / "data" / "sources_registry.yaml"
    )
    monkeypatch.setattr(
        nlm_reg, "TASK_STATE_FILE", sandbox / ".md" / "scratch" / "notebooklm_task_state.yaml"
    )


def test_feat_nlm_001_public_seams_and_tier_aliases() -> None:
    """Verify FEAT-NLM-001: 15 public __all__ exports and NotebookLMClient backward alias."""
    expected = {
        "HAS_NOTEBOOKLM",
        "CCBANotebookLMClient",
        "NotebookLMClient",
        "check_auth",
        "get_client",
        "delete_notebook",
        "delete_source",
        "extract_and_summarize",
        "get_or_create_project_notebook",
        "get_source_id_by_path",
        "handle_artifact_flow",
        "list_notebooks",
        "list_sources",
        "query_rag",
        "share_notebook",
    }
    assert set(ccba_notebooklm.__all__) == expected
    assert NotebookLMClient is CCBANotebookLMClient
    for symbol in expected:
        assert hasattr(ccba_notebooklm, symbol)


def test_feat_nlm_002_maskara_gate_and_prompt_sanitization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify FEAT-NLM-002: Maskara upload gate (bug_path_1/2/3) & fail-closed prompt gate."""
    monkeypatch.chdir(tmp_path)

    # bug_path_2: URL, missing file, and binary bytes return (source_path, False)
    assert nlm_sec.run_maskara_gate("https://example.com/spec.pdf") == (
        "https://example.com/spec.pdf",
        False,
    )
    missing_file = str(tmp_path / "does_not_exist.md")
    assert nlm_sec.run_maskara_gate(missing_file) == (missing_file, False)

    bin_file = tmp_path / "archive.bin"
    bin_file.write_bytes(b"\x00\x01\x02\xff\xfe")
    assert nlm_sec.run_maskara_gate(str(bin_file)) == (str(bin_file), False)

    sample_note = tmp_path / "design_note.md"
    sample_note.write_text("Alpha payload value inside doc.\n", encoding="utf-8")

    # bug_path_1: Critical finding blocks upload with ValueError
    critical_stub = [
        {"rule_id": "openai-api-key", "severity": "critical", "name": "CritMatch", "line": 1}
    ]
    monkeypatch.setattr(nlm_sec, "detect_secrets_in_text", lambda *_a, **_kw: critical_stub)
    with pytest.raises(ValueError, match="CHẶN vì lý do an toàn thông tin"):
        nlm_sec.run_maskara_gate(str(sample_note))

    # Non-critical finding writes temporary redacted copy under tmp_path/.md/scratch/redacted
    low_stub = [{"rule_id": "generic-match", "severity": "low", "start": 6, "end": 13}]
    monkeypatch.setattr(nlm_sec, "detect_secrets_in_text", lambda *_a, **_kw: low_stub)
    monkeypatch.setattr(
        nlm_sec, "apply_raw_redactions", lambda raw, _f: (raw.replace(b"payload", b"<REDACT>"), 1)
    )
    redacted_path, is_temp = nlm_sec.run_maskara_gate(str(sample_note))
    assert is_temp is True
    assert Path(redacted_path).is_file()
    assert b"<REDACT>" in Path(redacted_path).read_bytes()

    # bug_path_3: Unexpected scanner error fails open in run_maskara_gate with [Warn]
    def _boom_scanner(*_a: Any, **_kw: Any) -> list[dict[str, Any]]:
        raise RuntimeError("scanner backend crash")

    monkeypatch.setattr(nlm_sec, "detect_secrets_in_text", _boom_scanner)
    assert nlm_sec.run_maskara_gate(str(sample_note)) == (str(sample_note), False)
    assert "[Warn] Lỗi khi chạy Maskara Gate" in capsys.readouterr().err

    # sanitize_prompt_for_query is fail-closed when scanner fails, and redacts non-critical findings
    with pytest.raises(RuntimeError, match="Fail-Closed"):
        nlm_sec.sanitize_prompt_for_query("Analyze clause 4 please")

    monkeypatch.setattr(nlm_sec, "detect_secrets_in_text", lambda *_a, **_kw: low_stub)
    assert "<REDACT>" in nlm_sec.sanitize_prompt_for_query("Check payload value")


def test_feat_nlm_003_registry_context_routing_and_task_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify FEAT-NLM-003: registry persistence, SHA-256, context routing & task state."""
    _patch_registry_paths(monkeypatch, tmp_path)

    doc_file = tmp_path / "docs" / "sample.md"
    doc_file.parent.mkdir(parents=True)
    doc_file.write_text("CCBA spec content\n", encoding="utf-8")

    rel = nlm_reg.normalize_to_relative(str(doc_file))
    assert rel == "docs/sample.md"
    assert nlm_reg.normalize_to_relative("https://ccba.vn/doc") == "https://ccba.vn/doc"

    digest = nlm_reg.get_file_sha256(str(doc_file))
    assert len(digest) == 64

    nlm_reg.update_registry(str(doc_file), "src-001", digest, "nb-core")
    loaded = nlm_reg.read_registry()
    assert loaded["docs/sample.md"]["source_id"] == "src-001"
    assert loaded["docs/sample.md"]["sha256"] == digest

    catalog = tmp_path / "catalog.yaml"
    catalog.write_text(
        yaml.safe_dump(
            {
                "notebook_ids": {"_core": "nb-core-id", "_software": "nb-soft-id"},
                "skills": [{"name": "ccba-tdd", "bundle": "_software"}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("NOTEBOOKLM_SOFTWARE_ID", "nb-env-override")
    routed = nlm_reg.route_session_to_workflow("tdd", catalog)
    assert routed == "nb-env-override"
    assert nlm_reg.get_notebook_id_from_context() == "nb-env-override"

    nlm_reg.save_task_state("nb-env-override", "task-42", "src-001", "audio")
    state = nlm_reg.read_task_state()
    assert state is not None and state["task_id"] == "task-42"
    nlm_reg.clear_task_state()
    assert nlm_reg.read_task_state() is None


def test_feat_nlm_004_quota_guard_and_orphan_gc_bug_path_4(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify FEAT-NLM-004: >=90% quota threshold triggers orphan GC and handles delete errors."""
    _patch_registry_paths(monkeypatch, tmp_path)
    doc_file = tmp_path / "keep.md"
    doc_file.write_text("keep", encoding="utf-8")
    nlm_reg.update_registry(str(doc_file), "src-keep", "abc", "nb-1")

    deleted_ids: list[str] = []

    class _FakeClient:
        async def get_account_tier(self) -> Any:
            return SimpleNamespace(tier="plus", plan_name="Plus")

        async def get_account_limits(self) -> Any:
            return SimpleNamespace(source_limit=10)

        async def list_sources(self, _notebook_id: str) -> list[Any]:
            # 9 out of 10 sources >= 90% threshold
            sources = [SimpleNamespace(id="src-keep", title="Keep")]
            sources.append(SimpleNamespace(id="src-orphan-ok", title="Orphan OK"))
            sources.append(SimpleNamespace(id="src-orphan-err", title="Orphan Err"))
            sources.extend(
                SimpleNamespace(id=f"src-extra-{i}", title=f"Extra {i}") for i in range(6)
            )
            return sources

        async def delete_source(self, _notebook_id: str, src_id: str) -> None:
            if src_id == "src-orphan-err":
                raise RuntimeError("remote delete timeout")
            deleted_ids.append(src_id)

    # Mock extra items into registry except src-orphan-ok & src-orphan-err
    for idx in range(6):
        extra = tmp_path / f"extra_{idx}.md"
        extra.write_text("x", encoding="utf-8")
        nlm_reg.update_registry(str(extra), f"src-extra-{idx}", "h", "nb-1")

    asyncio.run(nlm_gc.check_quota_and_warn(_FakeClient(), "nb-1"))
    stderr_text = capsys.readouterr().err
    assert "sắp đạt giới hạn (9/10)" in stderr_text
    assert "[Warn] Không thể xóa nguồn 'src-orphan-err'" in stderr_text
    assert "src-orphan-ok" in deleted_ids
    assert "src-keep" not in deleted_ids


def test_feat_nlm_005_statechart_anti_lie_and_summary_postprocess(tmp_path: Path) -> None:
    """Verify FEAT-NLM-005: Statechart Anti-Lie, bug_path parity & post_process_summary."""
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

    summary_file = tmp_path / "summary.md"
    summary_file.write_text("# Executive Summary\nKey finding body.\n", encoding="utf-8")
    post_process_summary(summary_file, "docs/spec.pdf", "nb-01", "src-99", "deadbeef")
    first_pass = summary_file.read_text(encoding="utf-8")
    assert 'source_id: "src-99"' in first_pass
    assert "*Tạo bởi CCBA" in first_pass

    # Running post_process_summary twice stays idempotent on attribution disclaimer
    post_process_summary(summary_file, "docs/spec.pdf", "nb-01", "src-99", "deadbeef")
    second_pass = summary_file.read_text(encoding="utf-8")
    assert second_pass.count("*Tạo bởi CCBA") == 1


def test_feat_nlm_006_surface_diff_provenance_and_drift_modes() -> None:
    """Verify FEAT-NLM-006: Surface Diff parity, LF SHA-256 provenance, and drift modes."""
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
