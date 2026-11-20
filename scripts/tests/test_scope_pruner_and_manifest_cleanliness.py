"""Tests for Wave 2 H3: scope compilation, scope_pruner --prune-unscoped, and manifest cleanliness."""

from __future__ import annotations

from pathlib import Path

from ccba_harness._guardrail_manifest import write_guardrail_manifest
from scripts.spoke.check_spoke_cleanliness import scan_spoke_cleanliness
from scripts.spoke.sync.coordinator import SpokeSynchronizer
from scripts.spoke.sync.scope_pruner import (
    reconcile_existing_skills,
    should_sync_skill_to_spoke,
)


def test_cleanliness_legacy_spoke_without_manifest_strict_returns_zero(tmp_path: Path) -> None:
    """Legacy Spokes lacking guardrails_manifest.json emit [INFO] and exit 0 even with strict=True."""
    (tmp_path / "scripts").mkdir(parents=True)
    (tmp_path / "scripts" / "worker.py").write_text("X = 1\n", encoding="utf-8")
    code, msgs = scan_spoke_cleanliness(tmp_path, strict=True)
    assert code == 0
    assert any("Chưa có guardrails_manifest.json" in m for m in msgs)


def test_cleanliness_fails_closed_on_tampered_guardrail_manifest(tmp_path: Path) -> None:
    """Spoke with guardrails_manifest.json passes when intact and fails closed on tamper."""
    g_dir = tmp_path / "scripts" / "_guardrails"
    g_dir.mkdir(parents=True)
    safe_file = g_dir / "safe_pytest.py"
    safe_file.write_text("X = 1\n", encoding="utf-8")
    guardrail_manifest_py = (
        Path(__file__).resolve().parents[2]
        / "packages"
        / "ccba-harness"
        / "src"
        / "ccba_harness"
        / "_guardrail_manifest.py"
    )
    (g_dir / "_guardrail_manifest.py").write_text(
        guardrail_manifest_py.read_text(encoding="utf-8"), encoding="utf-8"
    )
    write_guardrail_manifest(
        tmp_path,
        ["scripts/_guardrails/safe_pytest.py", "scripts/_guardrails/_guardrail_manifest.py"],
    )

    code_ok, _ = scan_spoke_cleanliness(tmp_path, strict=True)
    assert code_ok == 0

    safe_file.write_text("X = 999\n", encoding="utf-8")
    code_bad, msgs_bad = scan_spoke_cleanliness(tmp_path, strict=True)
    assert code_bad == 1
    assert any("SHA-256 mismatch" in m for m in msgs_bad)


def test_scope_filtering_and_prune_unscoped_preserves_custom_and_other_bundles(
    tmp_path: Path,
) -> None:
    """Filter scope:hub on collect, and --prune-unscoped only deletes scope:hub folders."""
    hub_root = tmp_path / "hub"
    spoke_root = tmp_path / "spoke"
    spoke_skills = spoke_root / ".agents" / "skills"
    for folder in (
        "ccba-adr-lifecycle",
        "ccba-bim-other",
        "verify-idop",
        "ccba-infrastructure-manager",
        "legacy-ask",
    ):
        (spoke_skills / folder).mkdir(parents=True)
        (spoke_skills / folder / "SKILL.md").write_text(f"# {folder}\n", encoding="utf-8")

    catalog = {
        "skills": [
            {
                "name": "ccba-tdd",
                "bundle": "_core",
                "skill_path": ".agents/skills/ccba-tdd/SKILL.md",
            },
            {
                "name": "ccba-universal",
                "bundle": "_core",
                "scope": "universal",
                "skill_path": ".agents/skills/ccba-universal/SKILL.md",
            },
            {
                "name": "ccba-adr-lifecycle",
                "bundle": "_core",
                "scope": "hub",
                "skill_path": ".agents/skills/ccba-adr-lifecycle/SKILL.md",
            },
            {
                "name": "ccba-bim-other",
                "bundle": "_bim",
                "scope": "universal",
                "skill_path": ".agents/skills/ccba-bim-other/SKILL.md",
            },
        ],
        "workflows": [],
    }
    assert should_sync_skill_to_spoke({"scope": "hub"}) is False
    assert should_sync_skill_to_spoke({}) is True

    sync_engine = SpokeSynchronizer(str(spoke_root))
    skills_to_sync, _ = sync_engine._collect_sync_targets(catalog, hub_root, ["_core"])
    assert [s["dest_name"] for s in skills_to_sync] == ["ccba-tdd", "ccba-universal"]

    synced = {"ccba-tdd", "ccba-universal"}
    aliases = {"legacy-ask": "ccba-not-in-synced"}

    # Default prune_unscoped=False preserves hub-scoped and custom skills
    act_default = reconcile_existing_skills(
        spoke_root, spoke_skills, synced, aliases, catalog=catalog, prune_unscoped=False
    )
    assert all(a["status"] == "PRESERVED" for a in act_default)
    assert (spoke_skills / "ccba-adr-lifecycle").is_dir()

    # Dry-run with prune_unscoped=True logs REMOVED but keeps directory intact
    act_dry = reconcile_existing_skills(
        spoke_root,
        spoke_skills,
        synced,
        aliases,
        catalog=catalog,
        prune_unscoped=True,
        dry_run=True,
    )
    statuses_dry = {a["name"]: a["status"] for a in act_dry}
    assert statuses_dry["ccba-adr-lifecycle"] == "REMOVED"
    assert statuses_dry["ccba-bim-other"] == "PRESERVED"
    assert statuses_dry["verify-idop"] == "PRESERVED"
    assert statuses_dry["ccba-infrastructure-manager"] == "PRESERVED"
    assert (spoke_skills / "ccba-adr-lifecycle").is_dir()

    # Apply with prune_unscoped=True deletes ONLY scope: hub
    reconcile_existing_skills(
        spoke_root,
        spoke_skills,
        synced,
        aliases,
        catalog=catalog,
        prune_unscoped=True,
        dry_run=False,
    )
    assert not (spoke_skills / "ccba-adr-lifecycle").exists()
    assert (spoke_skills / "ccba-bim-other").is_dir()
    assert (spoke_skills / "verify-idop").is_dir()
    assert (spoke_skills / "ccba-infrastructure-manager").is_dir()
    assert (spoke_skills / "legacy-ask").is_dir()


def test_cli_forwards_prune_unscoped_only_when_enabled(tmp_path: Path) -> None:
    """Verify CLI passes prune_unscoped=True only when --prune-unscoped is explicitly set."""
    from unittest.mock import patch

    from scripts.spoke.sync.cli import run_spoke_sync_cli

    with patch("scripts.spoke.sync.cli.sync_project", return_value=0) as mock_sync:
        assert run_spoke_sync_cli(["--spoke", str(tmp_path), "--apply", "--prune-unscoped"]) == 0
        assert mock_sync.call_args.kwargs.get("prune_unscoped") is True
