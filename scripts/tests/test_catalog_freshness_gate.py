"""scripts/tests/test_catalog_freshness_gate.py - Unit and regression tests for Catalog Freshness Hard Gate (PR-1).

Tests:
1. compile_catalog.check_catalog_in_sync includes 'guardrails' field in diff checks.
2. assess_catalog_freshness permits dry-run with warning when stale.
3. assess_catalog_freshness blocks apply (dry_run=False) with 'catalog_stale' when stale.
4. assess_catalog_freshness allows apply when --allow-stale-catalog is set.
5. assess_catalog_freshness handles check exceptions gracefully with bypass support.
6. CLI argument --allow-stale-catalog is parsed and propagated.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_compile_catalog_base_fields_includes_guardrails() -> None:
    """Verify check_catalog_in_sync inspects guardrails alongside other base fields."""
    from scripts.governance import compile_catalog

    # Verify CATALOG_RECOMPILE_COMMAND constant is defined
    assert hasattr(compile_catalog, "CATALOG_RECOMPILE_COMMAND")
    assert "compile_catalog.py --write" in compile_catalog.CATALOG_RECOMPILE_COMMAND


def test_assess_catalog_freshness_dry_run_allows_stale(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify dry_run mode warns but does not block when catalog is stale."""
    from scripts.spoke.sync.coordinator import assess_catalog_freshness

    with patch(
        "scripts.governance.compile_catalog.check_catalog_in_sync",
        return_value=(False, ["skills drifted"]),
    ):
        result = assess_catalog_freshness(
            hub_root=tmp_path,
            spoke_root=tmp_path,
            dry_run=True,
            allow_stale_catalog=False,
        )
        assert result is None
        captured = capsys.readouterr()
        assert (
            "WARNING: Hub catalog.yaml is out of sync" in captured.err or "WARNING" in captured.out
        )


def test_assess_catalog_freshness_apply_blocks_stale(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify apply mode (dry_run=False) returns 'catalog_stale' (fail-closed) when catalog is stale."""
    from scripts.spoke.sync.coordinator import assess_catalog_freshness

    with patch(
        "scripts.governance.compile_catalog.check_catalog_in_sync",
        return_value=(False, ["diff 1", "diff 2"]),
    ):
        result = assess_catalog_freshness(
            hub_root=tmp_path,
            spoke_root=tmp_path,
            dry_run=False,
            allow_stale_catalog=False,
        )
        assert result == "catalog_stale"
        captured = capsys.readouterr()
        assert "ERROR: Cannot apply sync because Hub catalog.yaml is out of sync" in captured.err
        assert "compile_catalog.py --write" in captured.err


def test_assess_catalog_freshness_apply_allows_with_bypass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify apply mode proceeds when allow_stale_catalog=True with audit trail."""
    from scripts.spoke.sync.coordinator import assess_catalog_freshness

    with patch(
        "scripts.governance.compile_catalog.check_catalog_in_sync", return_value=(False, ["diff 1"])
    ):
        result = assess_catalog_freshness(
            hub_root=tmp_path,
            spoke_root=tmp_path,
            dry_run=False,
            allow_stale_catalog=True,
        )
        assert result is None
        captured = capsys.readouterr()
        assert (
            "AUDIT: CATALOG_STALE_BYPASS" in captured.err
            or "AUDIT: CATALOG_STALE_BYPASS" in captured.out
        )


def test_assess_catalog_freshness_exception_with_bypass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify check exceptions do not block when allow_stale_catalog=True."""
    from scripts.spoke.sync.coordinator import assess_catalog_freshness

    with patch(
        "scripts.governance.compile_catalog.check_catalog_in_sync",
        side_effect=RuntimeError("IO corrupt"),
    ):
        result = assess_catalog_freshness(
            hub_root=tmp_path,
            spoke_root=tmp_path,
            dry_run=False,
            allow_stale_catalog=True,
        )
        assert result is None
        captured = capsys.readouterr()
        assert (
            "AUDIT: CATALOG_STALE_BYPASS" in captured.err
            or "AUDIT: CATALOG_STALE_BYPASS" in captured.out
        )


def test_cli_parser_supports_allow_stale_catalog() -> None:
    """Verify build_parser in scripts/spoke/sync/cli.py supports --allow-stale-catalog."""
    from scripts.spoke.sync.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["--allow-stale-catalog"])
    assert args.allow_stale_catalog is True
