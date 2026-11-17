"""test_ai_suite.py - 6-Feature Contract & Statechart Bug-Path Replay Suite for ccba-ai.

Covers all features declared in `verify-ccba-ai/features/INDEX.md`:
- FEAT-AI-001: PEP 562 Lazy Public Seams & Exports
- FEAT-AI-002: Model Archetypes, Virtual Tiers & resolve_max_tokens
- FEAT-AI-003: Circuit Breaker State Machine & CircuitBreakerOpenError
- FEAT-AI-004: Multi-Tier Failover Cascade, CLI Affinity & Timeout Clamp
- FEAT-AI-005: 5-Block Lifecycle, Statechart Bug-Path Replay & Anti-Lie Validation
- FEAT-AI-006: Surface Diff Parity, LF SHA-256 Git Provenance & Drift Modes
"""

from __future__ import annotations

import importlib.util
import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
import yaml

import ccba_ai
from ccba_ai.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState
from ccba_ai.client import _compute_effective_timeout, _sanitize_gateway_url
from ccba_ai.exceptions import CCBAErrorCode
from ccba_ai.fallback import TieredFallbackRouter, TierType, map_model_for_tier
from ccba_ai.routing import ModelArchetype, choose_model, is_reasoning_model, resolve_max_tokens

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _load_runner_module() -> Any:
    """Dynamically loads run_verify_ai.py from the local harness directory."""
    runner_path = Path(__file__).resolve().parent / "run_verify_ai.py"
    spec = importlib.util.spec_from_file_location("run_verify_ai", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_ai"] = mod
    spec.loader.exec_module(mod)
    return mod


def _extract_statechart_lines(skill_md: Path) -> list[str]:
    """Extracts the first stateDiagram-v2 mermaid block from SKILL.md."""
    text = skill_md.read_text(encoding="utf-8")
    for block in re.findall(r"```mermaid\s*\n(.*?)```", text, flags=re.DOTALL):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip() and not ln.startswith("%%")]
        if lines and lines[0].startswith("stateDiagram"):
            return lines
    raise AssertionError(f"No stateDiagram block found in {skill_md}")


def _replay_bug_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replays both CircuitBreaker Fast-Fail and CascadeExhausted bug_paths on real ccba-ai."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    assert CircuitState(cb.state) == CircuitState.CLOSED and cb.allow_request()
    for _ in range(3):
        cb.record_failure(RuntimeError("gateway down"))
    assert CircuitState(cb.state) == CircuitState.OPEN
    with pytest.raises(CircuitBreakerOpenError) as exc_info:
        cb.check_allowed()
    assert exc_info.value.code == CCBAErrorCode.CIRCUIT_BREAKER_OPEN

    monkeypatch.setenv("GEMINI_API_KEY", "test-tier2-key")
    monkeypatch.delenv("CCBA_AI_MOCK", raising=False)
    agy = cast(Any, SimpleNamespace(is_available=lambda: True, sync_client="agy", async_client="a"))
    cop = cast(Any, SimpleNamespace(is_available=lambda: True, sync_client="cop", async_client="c"))
    router = TieredFallbackRouter(
        agy_provider=agy, copilot_provider=cop, enable_fallback=True, enable_mock_fallback=False
    )
    visited: list[tuple[Any, str]] = []

    def fail_tier(client: Any, mapped: str) -> str:
        visited.append((client, mapped))
        raise RuntimeError(f"tier failed for {mapped}")

    with pytest.raises(CircuitBreakerOpenError):
        router.execute_sync(
            cb.check_allowed, model="gemini-3.8-flash", fallback_fn_builder=fail_tier
        )
    assert len(visited) == 4
    assert visited[1][0] == "agy" and visited[2][0] == "cop"

    ok_router = TieredFallbackRouter(
        enable_fallback=True, enable_mock_fallback=True, mock_mode=True
    )
    assert (
        ok_router.execute_sync(
            cb.check_allowed, model="gemini-3.8-flash", fallback_fn_builder=lambda _c, m: f"ok:{m}"
        )
        == "ok:gemini-3.8-flash"
    )


def test_feat_ai_001_pep562_lazy_seams_and_exports() -> None:
    """Verifies FEAT-AI-001: PEP 562 lazy public seams and __all__ contracts."""
    for symbol in (
        "ai",
        "AIClient",
        "AsyncAIClient",
        "CircuitBreaker",
        "TieredFallbackRouter",
        "choose_model",
        "resolve_max_tokens",
    ):
        assert symbol in ccba_ai.__all__
        assert getattr(ccba_ai, symbol) is not None
    assert callable(ccba_ai.choose_model)


def test_feat_ai_002_model_archetypes_and_virtual_tier_routing() -> None:
    """Verifies FEAT-AI-002: choose_model virtual tiers, reasoning detection & max_tokens."""
    assert choose_model("ocr") == ModelArchetype.TIER_OCR
    assert choose_model("coding") == ModelArchetype.TIER_FAST
    assert choose_model("reasoning") == ModelArchetype.TIER_REASONING
    assert choose_model("local") == ModelArchetype.TIER_LOCAL
    assert choose_model("embedding") == "embedding-default"
    assert is_reasoning_model("gemini-3.8-flash-high") is True
    assert is_reasoning_model("gemini-3.8-flash") is False
    assert resolve_max_tokens("gemini-3.8-flash-high", 1024) == 16384
    assert resolve_max_tokens("gemini-3.8-flash-high", 500) == 500


def test_feat_ai_003_circuit_breaker_transitions_and_cooldown() -> None:
    """Verifies FEAT-AI-003: CircuitBreaker CLOSED -> OPEN -> HALF_OPEN -> CLOSED/OPEN."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.05)
    assert CircuitState(cb.state) == CircuitState.CLOSED and cb.allow_request()
    cb.record_failure()
    cb.record_failure()
    assert CircuitState(cb.state) == CircuitState.CLOSED
    cb.record_failure()
    assert CircuitState(cb.state) == CircuitState.OPEN
    assert not cb.allow_request()
    with pytest.raises(CircuitBreakerOpenError):
        cb.check_allowed()

    cb.last_state_change = time.time() - 0.2
    assert cb.allow_request() and CircuitState(cb.state) == CircuitState.HALF_OPEN
    cb.record_failure()
    assert CircuitState(cb.state) == CircuitState.OPEN
    cb.last_state_change = time.time() - 0.2
    assert cb.allow_request() and CircuitState(cb.state) == CircuitState.HALF_OPEN
    cb.record_success()
    assert CircuitState(cb.state) == CircuitState.CLOSED and cb.failure_count == 0


def test_feat_ai_004_multi_tier_failover_and_timeout_clamp() -> None:
    """Verifies FEAT-AI-004: Model mapping, CLI family affinity, URL sanitize & timeout clamp."""
    assert map_model_for_tier("gpt-5", TierType.TIER3_COPILOT) == "gpt-5.4-mini"
    assert map_model_for_tier("gpt-5-high", TierType.TIER3_COPILOT) == "gpt-5.4"
    assert (
        map_model_for_tier("gemini-4-argon-high", TierType.TIER1_GATEWAY) == "gemini-3.8-flash-high"
    )

    agy = cast(Any, SimpleNamespace(is_available=lambda: True, sync_client="a", async_client="a"))
    cop = cast(Any, SimpleNamespace(is_available=lambda: True, sync_client="c", async_client="c"))
    router = TieredFallbackRouter(agy_provider=agy, copilot_provider=cop)
    gpt_labels = [lbl for lbl, *_ in router._iter_cli_candidates("gpt-4o", is_async=False)]
    gem_labels = [
        lbl for lbl, *_ in router._iter_cli_candidates("gemini-3.8-flash", is_async=False)
    ]
    assert gpt_labels[0].startswith("Tier 3 (Copilot CLI:")
    assert gem_labels[0].startswith("Tier 3 (Antigravity CLI:")

    assert _sanitize_gateway_url("http://127.0.0.1:8045/v1") == "http://127.0.0.1:8090/v1"
    assert _compute_effective_timeout("gemini-3.8-flash-high", 30.0, 16384) >= 90.0
    assert _compute_effective_timeout("gemini-3.8-flash", 30.0, 1024) == 30.0


def test_feat_ai_005_statechart_bug_path_replay_and_anti_lie(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifies FEAT-AI-005: 5-block runner, Anti-Lie statechart & real code bug_path replay."""
    runner = _load_runner_module()
    if str(runner.REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(runner.REPO_ROOT))
    from tests.governance.test_skills_docs_integrity import verify_statechart_anti_lie

    skill_md = Path(__file__).resolve().parent.parent / "SKILL.md"
    assert verify_statechart_anti_lie(_extract_statechart_lines(skill_md)) == []

    port = runner.find_free_port()
    proc = runner.start_probe_server(port, tmp_path)
    try:
        assert runner.poll_readiness(f"http://127.0.0.1:{port}/healthz", timeout_seconds=5.0)
    finally:
        runner.cleanup_process_group(proc)
    assert not runner.is_port_in_use(port)

    _replay_bug_paths(monkeypatch)
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


def test_feat_ai_006_surface_diff_and_git_provenance() -> None:
    """Verifies FEAT-AI-006: Surface Diff parity and fail-closed LF SHA-256 provenance."""
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

    tampered = dict(cov_hashes)
    tampered[cov_paths[0]] = "0" * 64
    assert runner.check_git_provenance(sync_sha, cov_paths, expected_sha256=tampered) == [
        cov_paths[0]
    ]
    bad_sha = "deadbeef" * 5
    assert runner.check_git_provenance(bad_sha, cov_paths) == [
        f"UNVERIFIABLE_SYNC_COMMIT:{bad_sha}"
    ]
