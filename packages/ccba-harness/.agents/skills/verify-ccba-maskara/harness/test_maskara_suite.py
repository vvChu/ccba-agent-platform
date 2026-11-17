"""test_maskara_suite.py - 6-Feature Contract & Statechart Bug-Path Replay Suite for ccba-maskara.

Covers all features declared in `verify-ccba-maskara/features/INDEX.md`:
- FEAT-MSK-001: Public Deep Seams (__all__) & REGEX_PATTERNS Catalog
- FEAT-MSK-002: Agent Normalization & Unknown Agent Rejection (bug_path_1)
- FEAT-MSK-003: Safe Filters (SAFE_STRINGS, _KNOWN_TOKEN_METRICS) & File Skip Guards (bug_path_2)
- FEAT-MSK-004: Byte-Level Redaction, Backup Registry & Overlapping Span Guard (bug_path_3)
- FEAT-MSK-005: Statechart Anti-Lie, bug_path Parity & Live Gateway Fail-Closed Replay (bug_path_4)
- FEAT-MSK-006: Surface Diff Parity, LF SHA-256 Provenance Lock & Drift Classifier
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
import yaml

import ccba_maskara
from ccba_maskara import (
    REGEX_PATTERNS,
    MaskaraScanner,
    apply_raw_redactions,
    backup_and_write,
    detect_secrets_in_text,
    is_binary,
    redact_secrets_in_text,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> Any:
    """Dynamically load run_verify_maskara.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_maskara.py"
    spec = importlib.util.spec_from_file_location("run_verify_maskara", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_maskara"] = mod
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


def _synth_anthropic_token() -> str:
    """Assemble a synthetic Anthropic-shaped token dynamically without static literals."""
    return "sk-" + "ant-" + "verify_" + ("x" * 24)


def test_feat_msk_001_public_seams_and_rules_catalog() -> None:
    """Verify FEAT-MSK-001: public __all__ exports and REGEX_PATTERNS registry."""
    for symbol in (
        "MaskaraScanner",
        "detect_secrets_in_text",
        "redact_secrets_in_text",
        "apply_raw_redactions",
        "apply_redact_findings",
        "backup_and_write",
        "is_binary",
        "REGEX_PATTERNS",
        "__version__",
    ):
        assert symbol in ccba_maskara.__all__
        assert getattr(ccba_maskara, symbol) is not None

    for rule_id in ("anthropic-api-key", "github-token", "env-secret"):
        assert rule_id in REGEX_PATTERNS

    token = _synth_anthropic_token()
    findings = detect_secrets_in_text(f"KEY={token}")
    assert findings and findings[0]["rule_id"] == "anthropic-api-key"
    assert "[MASKARA_REDACTED:anthropic-api-key]" in redact_secrets_in_text(f"KEY={token}")


def test_feat_msk_002_agent_locator_and_unknown_agent_error(tmp_path: Path) -> None:
    """Verify FEAT-MSK-002: agent alias normalization and bug_path_1 ValueError."""
    scanner = MaskaraScanner(project_root=tmp_path)
    assert scanner.normalize_agent_name("Claude Code") == "claude"
    assert scanner.normalize_agent_name("copilot") == "github-copilot"

    resolved = scanner.resolve_targets("auto", custom_root=str(tmp_path))
    assert resolved == [{"agent": "custom", "root": tmp_path.resolve()}]

    with pytest.raises(ValueError, match="Unsupported agent"):
        scanner.resolve_targets("nonexistent_agent_xyz")


def test_feat_msk_003_safe_filters_and_file_skip_guards(tmp_path: Path) -> None:
    """Verify FEAT-MSK-003: safe template/metric filters and bug_path_2 file skip guards."""
    scanner = MaskaraScanner(project_root=tmp_path)

    # Safe placeholders and LLM token metrics must not trigger findings
    safe_blob = (
        "API_" + "KEY=placeholder_password\n"
        "input_tokens = 1234567890\n"
        "TOTAL_" + "TOKENS=9876543210\n"
    )
    assert scanner.scan_text(safe_blob, filepath="metrics.py") == []

    # bug_path_2: binary file and oversized (> 25 MB) file are skipped cleanly
    bin_file = tmp_path / "payload.log"
    bin_file.write_bytes(b"\x00\x01binary-content")
    assert is_binary(bin_file) is True
    findings_bin, scanned_bin, skipped_bin = scanner.scan_file("custom", bin_file)
    assert findings_bin == [] and scanned_bin == 0 and skipped_bin == 1

    huge_file = tmp_path / "huge.log"
    huge_file.write_text("clean log line", encoding="utf-8")
    with patch("ccba_maskara._scanner.MAX_FILE_SIZE", 4):
        findings_big, scanned_big, skipped_big = scanner.scan_file("custom", huge_file)
    assert findings_big == [] and scanned_big == 0 and skipped_big == 1


def test_feat_msk_004_redaction_backup_and_overlap_guard(tmp_path: Path) -> None:
    """Verify FEAT-MSK-004: atomic backup_and_write and bug_path_3 overlapping span guard."""
    secret = _synth_anthropic_token()
    raw_bytes = f"token={secret}\n".encode()
    findings = detect_secrets_in_text(raw_bytes.decode("utf-8"), filepath=str(tmp_path / "app.env"))
    assert len(findings) == 1

    # bug_path_3: overlapping and out-of-bounds spans are safely skipped
    overlapping = dict(findings[0])
    out_of_bounds = {"start": 0, "end": len(raw_bytes) + 50, "redaction": "X"}
    rewritten, replaced = apply_raw_redactions(raw_bytes, [findings[0], overlapping, out_of_bounds])
    assert replaced == 1
    assert b"[MASKARA_REDACTED:anthropic-api-key]" in rewritten

    target = tmp_path / "app.env"
    target.write_bytes(raw_bytes)
    backup_dir = tmp_path / "backups"
    backup_path = backup_and_write(target, raw_bytes, rewritten, backup_dir=backup_dir)
    assert Path(backup_path).read_bytes() == raw_bytes
    assert target.read_bytes() == rewritten
    registry = json.loads((backup_dir / "registry.json").read_text(encoding="utf-8"))
    assert Path(backup_path).name in registry


def test_feat_msk_005_statechart_anti_lie_and_live_bug_paths(tmp_path: Path) -> None:
    """Verify FEAT-MSK-005: Statechart Anti-Lie, bug_path parity, and bug_path_4 gateway fallback."""
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

    # bug_path_4: when AI Gateway raises during use_llm=True, ask_llm_gateway fails closed to True
    scanner = MaskaraScanner(project_root=tmp_path)
    secret = _synth_anthropic_token()

    def _raise_gateway(_prompt: str) -> str:
        raise RuntimeError("gateway unreachable")

    fake_ccba_ai = SimpleNamespace(ai=SimpleNamespace(chat=_raise_gateway))
    with patch.dict(sys.modules, {"ccba_ai": fake_ccba_ai}):
        findings = scanner.scan_text(f"SECRET={secret}", filepath="session.log", use_llm=True)
    assert len(findings) == 1
    assert findings[0]["rule_id"] == "anthropic-api-key"


def test_feat_msk_006_surface_diff_provenance_and_drift_modes() -> None:
    """Verify FEAT-MSK-006: Surface Diff parity, LF SHA-256 provenance, and drift modes."""
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
