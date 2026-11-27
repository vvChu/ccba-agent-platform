"""Unit tests for Issue #928: guarded no-op backup snapshots and bootstrap lockfile drift."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PLATFORM_ROOT = Path(__file__).resolve().parents[2]
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

from scripts.spoke.spoke_bootstrap import (  # noqa: E402
    check_bootstrap_lockfile_drift,
    parse_requirements_hub_lockfile,
)
from scripts.spoke.sync.backup import (  # noqa: E402
    SpokeBackupManager,
    has_mutating_agents_actions,
)
from scripts.spoke.sync.coordinator import (  # noqa: E402
    SpokeSynchronizer,
    check_spoke_runtime_health,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _setup_minimal_hub_and_spoke(tmp_path: Path) -> tuple[Path, Path]:
    """Create a minimal Hub and Python Spoke fixture for sync tests."""
    hub_root = tmp_path / "hub"
    skill_dir = hub_root / ".agents" / "skills" / "ccba-demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: ccba-demo\n---\n# Demo v1\n", encoding="utf-8")

    cat_file = hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    cat_file.parent.mkdir(parents=True, exist_ok=True)
    cat_file.write_text(
        "bundles:\n"
        "  Phần mềm:\n"
        "    - _core\n"
        "skills:\n"
        "  - name: ccba-demo\n"
        "    bundle: _core\n"
        "    scope: universal\n"
        "    skill_path: .agents/skills/ccba-demo/SKILL.md\n"
        "workflows: []\n"
        "guardrails: []\n",
        encoding="utf-8",
    )

    spoke_root = tmp_path / "spoke"
    (spoke_root / ".agents").mkdir(parents=True)
    (spoke_root / ".agents" / "workspace_context.yaml").write_text(
        f"project_name: DemoSpoke\nproject_type: 'Phần mềm'\nhub_path: '{hub_root.as_posix()}'\n",
        encoding="utf-8",
    )
    return hub_root, spoke_root


def _seed_five_backups(spoke_root: Path) -> list[Path]:
    """Seed exactly 5 distinct historical snapshots in .md/backups/."""
    mgr = SpokeBackupManager(spoke_root)
    agents_dir = spoke_root / ".agents"
    created: list[Path] = []
    for idx in range(5):
        (agents_dir / "marker.txt").write_text(f"state-{idx}\n", encoding="utf-8")
        snap = mgr.create_backup()
        assert snap is not None
        created.append(snap)
    assert len(mgr.list_backups()) == 5
    return created


def _git(repo: Path, *args: str) -> str:
    """Run a deterministic git command in repo and return stripped stdout."""
    res = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return res.stdout.strip()


def _init_git_hub_with_packages(tmp_path: Path) -> tuple[Path, str]:
    """Create a real git Hub repo with ccba-harness, ccba-ai, and ccba-other packages."""
    hub_root = tmp_path / "git_hub"
    for pkg in ("ccba-harness", "ccba-ai", "ccba-other"):
        pkg_dir = hub_root / "packages" / pkg
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "pyproject.toml").write_text(
            f'[project]\nname = "{pkg}"\nversion = "0.1.0"\ndependencies = []\n',
            encoding="utf-8",
        )
    _git(hub_root, "init")
    _git(hub_root, "add", ".")
    _git(
        hub_root,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "init packages",
    )
    initial_sha = _git(hub_root, "rev-parse", "HEAD")[:12]
    return hub_root, initial_sha


def test_has_mutating_agents_actions_windows_and_non_agents_paths() -> None:
    """Verify action mutation check normalizes Windows separators and scopes to .agents/."""
    assert has_mutating_agents_actions(
        [{"type": "Rule", "name": "x", "status": "REMOVED", "path": ".agents\\rules\\legacy.md"}]
    )
    assert has_mutating_agents_actions(
        [{"type": "Skill", "name": "a", "status": "UPDATED", "path": "./.agents/skills/a"}]
    )
    assert not has_mutating_agents_actions(
        [{"type": "Guardrail", "name": "conftest", "status": "UPDATED", "path": "conftest.py"}]
    )
    assert not has_mutating_agents_actions(
        [
            {"type": "Skill", "name": "a", "status": "UNCHANGED", "path": ".agents/skills/a"},
            {"type": "Skill", "name": "b", "status": "PRESERVED", "path": ".agents/skills/b"},
            {"type": "Guardrail", "name": "c", "status": "MISSING_SRC", "path": ".agents/x"},
        ]
    )


def test_catalog_stale_does_not_create_or_evict_snapshots(tmp_path: Path) -> None:
    """catalog_stale halt must exit 1 before creating any snapshot or evicting old ones."""
    hub_root, spoke_root = _setup_minimal_hub_and_spoke(tmp_path)
    initial_snaps = _seed_five_backups(spoke_root)
    initial_names = [p.name for p in SpokeBackupManager(spoke_root).list_backups()]

    engine = SpokeSynchronizer(spoke_root, hub_root=hub_root)
    with patch(
        "scripts.spoke.sync.coordinator.assess_catalog_freshness",
        return_value="catalog_stale",
    ):
        code = engine.sync_spoke_bundle(dry_run=False, check_git=False, backup=True, pull_hub=False)

    assert code == 1
    current = SpokeBackupManager(spoke_root).list_backups()
    assert [p.name for p in current] == initial_names
    assert initial_snaps[0].exists()


def test_noop_apply_preserves_all_five_existing_snapshots(tmp_path: Path) -> None:
    """Repeated no-op --apply runs must discard staged snapshot and keep all 5 historical backups."""
    hub_root, spoke_root = _setup_minimal_hub_and_spoke(tmp_path)
    engine = SpokeSynchronizer(spoke_root, hub_root=hub_root)

    with patch("scripts.spoke.sync.coordinator.assess_catalog_freshness", return_value=None):
        # First sync brings Spoke up to date
        assert (
            engine.sync_spoke_bundle(dry_run=False, check_git=False, backup=False, pull_hub=False)
            == 0
        )
        initial_snaps = _seed_five_backups(spoke_root)
        initial_names = [p.name for p in SpokeBackupManager(spoke_root).list_backups()]

        # Three consecutive no-op runs must not evict any of the 5 historical snapshots
        for _ in range(3):
            res = engine.sync_spoke_bundle(
                dry_run=False, check_git=False, backup=True, pull_hub=False
            )
            assert res == 0

    after = SpokeBackupManager(spoke_root).list_backups()
    assert [p.name for p in after] == initial_names
    assert initial_snaps[0].exists()


def test_mutating_apply_keeps_new_snapshot_and_prunes_to_five(tmp_path: Path) -> None:
    """When skill content changes, sync must retain the pre-sync snapshot and prune to 5."""
    hub_root, spoke_root = _setup_minimal_hub_and_spoke(tmp_path)
    engine = SpokeSynchronizer(spoke_root, hub_root=hub_root)

    with patch("scripts.spoke.sync.coordinator.assess_catalog_freshness", return_value=None):
        assert (
            engine.sync_spoke_bundle(dry_run=False, check_git=False, backup=False, pull_hub=False)
            == 0
        )
        initial_snaps = _seed_five_backups(spoke_root)
        oldest_snap = initial_snaps[0]

        # Mutate skill content on Hub
        (hub_root / ".agents" / "skills" / "ccba-demo" / "SKILL.md").write_text(
            "---\nname: ccba-demo\n---\n# Demo v2\n", encoding="utf-8"
        )
        res = engine.sync_spoke_bundle(dry_run=False, check_git=False, backup=True, pull_hub=False)
        assert res == 0

    after = SpokeBackupManager(spoke_root).list_backups()
    assert len(after) == 5
    assert not oldest_snap.exists()
    # Latest snapshot must contain pre-sync Demo v1 content (proving snapshot ran before copy)
    latest_skill = after[0] / "skills" / "ccba-demo" / "SKILL.md"
    assert "Demo v1" in latest_skill.read_text(encoding="utf-8")


def test_dry_run_and_backup_false_never_create_backup_dir(tmp_path: Path) -> None:
    """Both dry_run=True (with pending NEW/UPDATED) and backup=False must never create .md/backups."""
    hub_root, spoke_root = _setup_minimal_hub_and_spoke(tmp_path)
    engine = SpokeSynchronizer(spoke_root, hub_root=hub_root)
    backup_root = spoke_root / ".md" / "backups"

    with patch("scripts.spoke.sync.coordinator.assess_catalog_freshness", return_value=None):
        assert (
            engine.sync_spoke_bundle(dry_run=True, check_git=False, backup=True, pull_hub=False)
            == 0
        )
        assert not backup_root.exists()

        assert (
            engine.sync_spoke_bundle(dry_run=False, check_git=False, backup=False, pull_hub=False)
            == 0
        )
        assert not backup_root.exists()


def test_audit_link_fix_keeps_snapshot_even_with_unchanged_actions(tmp_path: Path) -> None:
    """When audit_spoke_markdown_links mutates .agents/AGENTS.md without emitting an action, snapshot is kept."""
    hub_root, spoke_root = _setup_minimal_hub_and_spoke(tmp_path)
    agents_md = spoke_root / ".agents" / "AGENTS.md"
    agents_md.write_text("# Local Spoke\n", encoding="utf-8")

    mgr = SpokeBackupManager(spoke_root)
    snap = mgr.stage_backup_if_enabled(dry_run=False, backup=True)
    assert snap is not None

    # Simulate audit_spoke_markdown_links modifying AGENTS.md while all actions are UNCHANGED
    agents_md.write_text("# Local Spoke (link fixed)\n", encoding="utf-8")
    kept = mgr.finalize_if_mutated(
        snap,
        [{"type": "Rule", "name": "AGENTS.md", "status": "UNCHANGED", "path": ".agents/AGENTS.md"}],
    )
    assert kept == snap
    assert snap.exists()
    assert mgr.should_keep_snapshot(snap, None) is True


def test_single_item_sync_backup_retention_and_not_found_discard(tmp_path: Path) -> None:
    """On-demand sync keeps snapshot when mutating, discards on not-found and identical no-op."""
    hub_root, spoke_root = _setup_minimal_hub_and_spoke(tmp_path)
    engine = SpokeSynchronizer(spoke_root, hub_root=hub_root)
    mgr = SpokeBackupManager(spoke_root)

    with patch("scripts.spoke.sync.coordinator.assess_catalog_freshness", return_value=None):
        # Not-found item must exit 1 and discard staged snapshot
        assert (
            engine.sync_spoke_bundle(
                sync_item="non-existent-skill",
                dry_run=False,
                check_git=False,
                backup=True,
                pull_hub=False,
            )
            == 1
        )
        assert mgr.list_backups() == []

        # First real single-item sync mutates .agents/skills/ccba-demo -> keeps snapshot
        assert (
            engine.sync_spoke_bundle(
                sync_item="ccba-demo",
                dry_run=False,
                check_git=False,
                backup=True,
                pull_hub=False,
            )
            == 0
        )
        assert len(mgr.list_backups()) == 1

        # Second identical single-item sync -> no-op -> must not add another snapshot
        assert (
            engine.sync_spoke_bundle(
                sync_item="ccba-demo",
                dry_run=False,
                check_git=False,
                backup=True,
                pull_hub=False,
            )
            == 0
        )
        assert len(mgr.list_backups()) == 1


def test_parse_requirements_hub_lockfile_cross_platform(tmp_path: Path) -> None:
    """Parser handles Windows/POSIX paths, [extras], comments, and unknown commit."""
    win_drive = "D:"
    req = tmp_path / "requirements-hub.txt"
    req.write_text(
        "# AUTO-GENERATED\n"
        "# hub_commit: ef14e5173619\n"
        f"-e {win_drive}\\workspace\\hub\\packages\\ccba-harness\n"
        '-e "/home/user/hub/packages/ccba-ai[dev]"\n'
        "--editable=/home/user/hub/packages/ccba-maskara/\n",
        encoding="utf-8",
    )
    commit, pkgs = parse_requirements_hub_lockfile(req)
    assert commit == "ef14e5173619"
    assert pkgs == ["ccba-harness", "ccba-ai", "ccba-maskara"]

    req_unknown = tmp_path / "requirements-unknown.txt"
    req_unknown.write_text("# hub_commit: unknown\n-e /hub/packages/ccba-ai\n", encoding="utf-8")
    commit_u, pkgs_u = parse_requirements_hub_lockfile(req_unknown)
    assert commit_u is None
    assert pkgs_u == ["ccba-ai"]


def test_bootstrap_lockfile_drift_clean_vs_pyproject_vs_unrelated(tmp_path: Path) -> None:
    """Warn when target package pyproject.toml changes; stay silent for clean or unrelated package."""
    hub_root, initial_sha = _init_git_hub_with_packages(tmp_path)
    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()
    (spoke_root / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")
    (spoke_root / "requirements-hub.txt").write_text(
        f"# hub_commit: {initial_sha}\n"
        f"-e {hub_root / 'packages' / 'ccba-harness'}\n"
        f"-e {hub_root / 'packages' / 'ccba-ai'}\n",
        encoding="utf-8",
    )

    # 1. Clean state (same commit, all target packages present) -> None
    assert check_bootstrap_lockfile_drift(spoke_root, hub_root) is None

    # 2. Unrelated package pyproject.toml changes -> no false positive
    (hub_root / "packages" / "ccba-other" / "pyproject.toml").write_text(
        '[project]\nname = "ccba-other"\nversion = "0.2.0"\n', encoding="utf-8"
    )
    _git(hub_root, "add", ".")
    _git(
        hub_root,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "bump unrelated pkg",
    )
    assert check_bootstrap_lockfile_drift(spoke_root, hub_root) is None

    # 3. Target package pyproject.toml changes -> warn-only drift message
    (hub_root / "packages" / "ccba-ai" / "pyproject.toml").write_text(
        '[project]\nname = "ccba-ai"\nversion = "0.2.0"\ndependencies = ["httpx"]\n',
        encoding="utf-8",
    )
    _git(hub_root, "add", ".")
    _git(
        hub_root,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "bump ccba-ai deps",
    )
    warn = check_bootstrap_lockfile_drift(spoke_root, hub_root)
    assert warn is not None
    assert "[Bootstrap Drift]" in warn
    assert "ccba-ai" in warn
    assert "--bootstrap" in warn


def test_bootstrap_lockfile_drift_new_target_package_and_unverifiable_commit(
    tmp_path: Path,
) -> None:
    """Detect missing target package (even with unknown commit) and warn on unverifiable hex commit."""
    hub_root, _ = _init_git_hub_with_packages(tmp_path)
    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()
    (spoke_root / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")

    # Unknown commit + missing ccba-ai -> no git call needed, still reports missing target package
    (spoke_root / "requirements-hub.txt").write_text(
        f"# hub_commit: unknown\n-e {hub_root / 'packages' / 'ccba-harness'}\n",
        encoding="utf-8",
    )
    warn_unknown = check_bootstrap_lockfile_drift(spoke_root, hub_root)
    assert warn_unknown is not None
    assert "ccba-ai" in warn_unknown
    assert "--bootstrap" in warn_unknown

    # Unverifiable hex commit (not in git history) + missing ccba-ai -> reports BOTH
    (spoke_root / "requirements-hub.txt").write_text(
        f"# hub_commit: deadbeef1234\n-e {hub_root / 'packages' / 'ccba-harness'}\n",
        encoding="utf-8",
    )
    warn_unverifiable = check_bootstrap_lockfile_drift(spoke_root, hub_root)
    assert warn_unverifiable is not None
    assert "deadbeef1234" in warn_unverifiable
    assert "ccba-ai" in warn_unverifiable
    assert "--bootstrap" in warn_unverifiable


def test_runtime_health_and_apply_without_bootstrap_surface_drift_exit_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """sync_spoke_bundle(bootstrap=False) emits warn-only drift to stderr and exits 0."""
    hub_root, initial_sha = _init_git_hub_with_packages(tmp_path)
    cat_file = hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    cat_file.parent.mkdir(parents=True, exist_ok=True)
    cat_file.write_text(
        "bundles:\n  Phần mềm:\n    - _core\nskills: []\nworkflows: []\nguardrails: []\n",
        encoding="utf-8",
    )
    (hub_root / "packages" / "ccba-ai" / "pyproject.toml").write_text(
        '[project]\nname = "ccba-ai"\nversion = "0.3.0"\n', encoding="utf-8"
    )
    _git(hub_root, "add", ".")
    _git(
        hub_root,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "update ccba-ai",
    )

    spoke_root = tmp_path / "py_spoke"
    (spoke_root / ".agents").mkdir(parents=True)
    (spoke_root / ".agents" / "workspace_context.yaml").write_text(
        f"project_name: PySpoke\nproject_type: 'Phần mềm'\nhub_path: '{hub_root.as_posix()}'\n",
        encoding="utf-8",
    )
    (spoke_root / "pyproject.toml").write_text('[project]\nname = "py-spoke"\n', encoding="utf-8")
    (spoke_root / "requirements-hub.txt").write_text(
        f"# hub_commit: {initial_sha}\n"
        f"-e {hub_root / 'packages' / 'ccba-harness'}\n"
        f"-e {hub_root / 'packages' / 'ccba-ai'}\n",
        encoding="utf-8",
    )
    py_exec = spoke_root / ".venv" / "bin" / "python"
    py_exec.parent.mkdir(parents=True)
    py_exec.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    py_exec.chmod(0o755)

    real_run = subprocess.run

    def _mock_probe(
        cmd: list[str], *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        if cmd and cmd[0] == str(py_exec):
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")
        return real_run(cmd, *args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(subprocess, "run", _mock_probe)

    # Direct check_spoke_runtime_health call
    direct_warn = check_spoke_runtime_health(spoke_root, hub_root)
    assert direct_warn is not None
    assert "[Bootstrap Drift]" in direct_warn
    assert "ccba-ai" in direct_warn

    # Full sync_spoke_bundle(bootstrap=False) exits 0 and prints drift to stderr
    engine = SpokeSynchronizer(spoke_root, hub_root=hub_root)
    with patch("scripts.spoke.sync.coordinator.assess_catalog_freshness", return_value=None):
        code = engine.sync_spoke_bundle(
            dry_run=False, check_git=False, backup=False, bootstrap=False, pull_hub=False
        )
    assert code == 0
    captured = capsys.readouterr()
    assert "[Bootstrap Drift]" in captured.err
    assert "ccba-ai" in captured.err
    assert "--bootstrap" in captured.err
