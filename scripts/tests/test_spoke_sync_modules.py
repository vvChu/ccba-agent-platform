"""test_spoke_sync_modules.py - Scoped Fast Unit Tests for Modularized Spoke Sync Package.

Validates discovery, catalog merge, registry, backup, sdk inspector, coordinator, and cli.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.spoke.sync import (
    CatalogMerger,
    GitWorkingTreeGuard,
    HubDiscoverer,
    HubNotFoundError,
    SharedSdkInspector,
    SpokeBackupManager,
    SpokeRegistrar,
    SpokeSyncEngine,
    SpokeSynchronizer,
    TestGuardrailCopier,
    are_dirs_identical,
    are_files_identical,
    list_project_backups,
    load_yaml,
    resolve_canonical_project_type,
    run_spoke_sync_cli,
    safe_remove,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_base_utilities(tmp_path: Path):
    """Test load_yaml, are_files_identical, are_dirs_identical, and safe_remove."""
    f1 = tmp_path / "test1.yaml"
    f2 = tmp_path / "test2.yaml"
    f1.write_text("key: value\n", encoding="utf-8")
    f2.write_text("key: value\n", encoding="utf-8")

    data = load_yaml(f1)
    assert data == {"key": "value"}
    assert are_files_identical(f1, f2)

    f2.write_text("key: different\n", encoding="utf-8")
    assert not are_files_identical(f1, f2)

    d1 = tmp_path / "dir1"
    d2 = tmp_path / "dir2"
    d1.mkdir()
    d2.mkdir()
    (d1 / "sub.txt").write_text("hello", encoding="utf-8")
    (d2 / "sub.txt").write_text("hello", encoding="utf-8")
    assert are_dirs_identical(d1, d2)

    (d2 / "sub.txt").write_text("world", encoding="utf-8")
    assert not are_dirs_identical(d1, d2)

    safe_remove(d1)
    assert not d1.exists()

    # Test safe_remove with normal and read-only files
    file_to_remove = tmp_path / "remove_me.txt"
    file_to_remove.write_text("temporary content", encoding="utf-8")
    assert file_to_remove.exists()
    safe_remove(file_to_remove)
    assert not file_to_remove.exists()

    # Test safe_remove with readonly file
    readonly_file = tmp_path / "readonly.txt"
    readonly_file.write_text("readonly content", encoding="utf-8")
    readonly_file.chmod(0o444)
    safe_remove(readonly_file)
    assert not readonly_file.exists()

    # Test safe_remove with non-existent path
    safe_remove(tmp_path / "non_existent.txt")



def test_resolve_canonical_project_type():
    """Test resolve_canonical_project_type with exact, alias, and fuzzy matching."""
    bundle_defs = {
        "Phần mềm": ["_core", "_software"],
        "Thẩm tra thiết kế": ["_core", "_qc", "_consulting"],
        "Thiết kế": ["_core", "_qc", "_consulting"],
        "Kiểm định": ["_core", "_qc", "_consulting"],
        "BIM": ["_core"],
        "Tác vụ Admin": ["_core", "_consulting"],
        "Pháp điển": ["_core", "_software"],
    }

    # 1. Exact match
    canonical, note = resolve_canonical_project_type("Pháp điển", bundle_defs)
    assert canonical == "Pháp điển"
    assert note is None

    # 2. Case-insensitive match
    canonical, note = resolve_canonical_project_type("phần mềm", bundle_defs)
    assert canonical == "Phần mềm"
    assert note is not None
    assert "chữ hoa/thường" in note

    # 3. Aliases
    aliases_to_test = [
        ("Kho Tri thức Pháp lý & Quy chuẩn", "Pháp điển"),
        ("Kho Tri thức Pháp lý", "Pháp điển"),
        ("Pháp lý & Quy chuẩn", "Pháp điển"),
        ("Legal Knowledge", "Pháp điển"),
        ("knowledge_corpus", "Pháp điển"),
        ("Software", "Phần mềm"),
        ("Tư vấn & Thẩm tra", "Thẩm tra thiết kế"),
        ("Thẩm tra", "Thẩm tra thiết kế"),
        ("QC", "Thẩm tra thiết kế"),
        ("BIM Consulting", "BIM"),
        ("Admin", "Tác vụ Admin"),
        ("Tác vụ Hành chính", "Tác vụ Admin"),
    ]
    for raw, expected in aliases_to_test:
        can, n = resolve_canonical_project_type(raw, bundle_defs)
        assert can == expected, f"Failed for {raw}: expected {expected}, got {can}"
        assert n is not None
        assert "Alias" in n

    # 4. Fuzzy match suggestion
    can, suggestion = resolve_canonical_project_type("Phap Dien OKF", bundle_defs)
    assert can is None
    assert suggestion is not None
    assert "Có phải ý bạn là" in suggestion

    # 5. Empty / missing
    can, err = resolve_canonical_project_type("", bundle_defs)
    assert can is None
    assert "bị trống" in err


def test_hub_discoverer_success_and_not_found(tmp_path: Path):
    """Test HubDiscoverer resolution and HubNotFoundError."""
    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()

    # When no valid hub is found anywhere
    discoverer = HubDiscoverer(spoke_root, context={})
    with patch.object(discoverer, "_is_valid_hub", return_value=False):
        with pytest.raises(HubNotFoundError):
            discoverer.discover()

    # Create mock hub with catalog
    hub_root = tmp_path / "hub"
    catalog_path = hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    catalog_path.parent.mkdir(parents=True)
    catalog_path.write_text("skills: []\n", encoding="utf-8")

    context = {"hub_path": str(hub_root)}
    discoverer2 = HubDiscoverer(spoke_root, context=context)
    discovered = discoverer2.discover()
    assert discovered.resolve() == hub_root.resolve()


def test_catalog_merger_atomic(tmp_path: Path):
    """Test CatalogMerger atomic YAML writing."""
    catalog_file = tmp_path / "catalog.yaml"
    merger = CatalogMerger(catalog_file)
    success = merger.atomic_write({"name": "test_hub", "bundles": ["_core"]})
    assert success is True
    assert catalog_file.exists()

    loaded = yaml.safe_load(catalog_file.read_text(encoding="utf-8"))
    assert loaded["name"] == "test_hub"


def test_spoke_registrar_metadata(tmp_path: Path):
    """Test SpokeRegistrar info builder."""
    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()
    ctx_file = spoke_root / ".md" / "workspace_context.yaml"
    ctx_file.parent.mkdir(parents=True)
    ctx_file.write_text("project:\n  sub_type: personal_sandbox\n", encoding="utf-8")

    registrar = SpokeRegistrar()
    info = registrar.build_spoke_info(spoke_root, tmp_path, "TestSpoke", "Phần mềm")
    assert info["name"] == "TestSpoke"
    assert info["is_sandbox"] is True


def test_sdk_inspector_and_guardrail_copier(tmp_path: Path):
    """Test SharedSdkInspector and TestGuardrailCopier."""
    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()
    hub_root = tmp_path / "hub"
    hub_root.mkdir()

    # Guardrail copier
    conftest = hub_root / "conftest.py"
    conftest.write_text("# pytest root conftest", encoding="utf-8")
    copier = TestGuardrailCopier(spoke_root, hub_root, "Phần mềm")
    copier.copy_if_needed(dry_run=False)
    assert (spoke_root / "conftest.py").exists()

    # SDK Inspector
    inspector = SharedSdkInspector(spoke_root, hub_root, "Phần mềm")
    assert inspector.is_python_project() is True
    assert isinstance(inspector.resolve_packages_to_check(), list)


def test_backup_and_git_guard(tmp_path: Path):
    """Test SpokeBackupManager and GitWorkingTreeGuard."""
    spoke_root = tmp_path / "spoke"
    agents_dir = spoke_root / ".agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "AGENTS.md").write_text("# Master", encoding="utf-8")

    mgr = SpokeBackupManager(spoke_root)
    backup_path = mgr.create_backup()
    assert backup_path is not None
    assert backup_path.exists()

    backups = mgr.list_backups()
    assert len(backups) == 1

    (agents_dir / "AGENTS.md").write_text("# Modified", encoding="utf-8")
    restored = mgr.restore_backup(backup_path)
    assert restored is True
    assert (agents_dir / "AGENTS.md").read_text(encoding="utf-8") == "# Master"

    guard = GitWorkingTreeGuard(spoke_root)
    assert guard.is_git_repo() is False
    is_clean, _ = guard.check_clean_working_tree()
    assert is_clean is True


def test_coordinator_alias_and_delegates(tmp_path: Path):
    """Test SpokeSynchronizer class, alias, and procedure delegates."""
    assert SpokeSyncEngine is SpokeSynchronizer

    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()
    (spoke_root / ".agents").mkdir()
    (spoke_root / ".agents" / "workspace_context.yaml").write_text(
        "project_name: Test\n", encoding="utf-8"
    )

    engine = SpokeSynchronizer(spoke_root)
    assert engine.spoke_root.resolve() == spoke_root.resolve()

    backups = list_project_backups(spoke_root)
    assert isinstance(backups, list)


def test_cli_runner_help(capsys):
    """Test run_spoke_sync_cli execution."""
    with pytest.raises(SystemExit) as exc_info:
        run_spoke_sync_cli(["--help"])
    assert exc_info.value.code == 0


def test_legal_knowledge_sync_orchestrator(tmp_path: Path):
    """Test LegalKnowledgeSyncOrchestrator identification and advisory behavior."""
    from scripts.spoke.sync import LegalKnowledgeSyncOrchestrator

    # 1. Non-legal spoke (Software)
    software_spoke = tmp_path / "software_spoke"
    software_spoke.mkdir()
    orch_soft = LegalKnowledgeSyncOrchestrator(software_spoke, tmp_path, "Phần mềm")
    assert orch_soft.is_legal_related_spoke() is False
    assert orch_soft.is_master_legal_corpus() is False
    res_soft = orch_soft.sync_or_advise(dry_run=True)
    assert res_soft["is_legal"] is False
    assert res_soft["status"] == "advised_zero_bloat"

    # 2. Legal spoke (Pháp điển by project type)
    legal_spoke = tmp_path / "legal_spoke"
    legal_spoke.mkdir()
    orch_legal = LegalKnowledgeSyncOrchestrator(legal_spoke, tmp_path, "Pháp điển")
    assert orch_legal.is_legal_related_spoke() is True
    assert orch_legal.is_master_legal_corpus() is False
    res_legal = orch_legal.sync_or_advise(dry_run=True)
    assert res_legal["is_legal"] is True
    assert res_legal["dry_run"] is True

    # 3. Spoke with legal_registry.yaml
    custom_spoke = tmp_path / "custom_spoke"
    custom_spoke.mkdir()
    (custom_spoke / "legal_registry.yaml").write_text("documents: []\n", encoding="utf-8")
    orch_custom = LegalKnowledgeSyncOrchestrator(custom_spoke, tmp_path, "BIM")
    assert orch_custom.is_legal_related_spoke() is True

    # 4. Master Legal Corpus Self-Loop Guard (ADR 0036 & ADR 0050)
    master_spoke = tmp_path / "ccba-legal-knowledge"
    master_spoke.mkdir()
    (master_spoke / "legal_docs").mkdir()
    (master_spoke / "legal_registry.yaml").write_text("documents: []\n", encoding="utf-8")
    orch_master = LegalKnowledgeSyncOrchestrator(master_spoke, tmp_path, "Pháp điển")
    assert orch_master.is_master_legal_corpus() is True
    res_master = orch_master.sync_or_advise(dry_run=False)
    assert res_master["is_master"] is True
    assert res_master["status"] == "master_corpus_preserved"
    assert not (master_spoke / ".md" / "legal_docs").exists()

    # 5. Master Legal Corpus identified via workspace_context.yaml archetype
    archetype_spoke = tmp_path / "archetype_corpus"
    archetype_spoke.mkdir()
    (archetype_spoke / ".md").mkdir()
    (archetype_spoke / ".md" / "workspace_context.yaml").write_text(
        "project:\n  archetype: knowledge_corpus\n", encoding="utf-8"
    )
    orch_archetype = LegalKnowledgeSyncOrchestrator(archetype_spoke, tmp_path, "Pháp điển")
    assert orch_archetype.is_master_legal_corpus() is True


def test_spoke_sync_bootstrap_flag(tmp_path: Path):
    """Test SpokeSynchronizer integration with bootstrap parameter."""
    spoke_root = tmp_path / "test_spoke"
    spoke_root.mkdir()
    (spoke_root / ".agents").mkdir()
    (spoke_root / ".agents" / "workspace_context.yaml").write_text(
        "project:\n  name: TestBootstrap\n  type: Phần mềm\n", encoding="utf-8"
    )

    hub_root = tmp_path / "mock_hub"
    cat_dir = hub_root / ".agents" / "skills" / "platform-loader"
    cat_dir.mkdir(parents=True)
    (cat_dir / "catalog.yaml").write_text(
        "bundles:\n  Phần mềm: [_core]\nskills: []\nworkflows: []\n", encoding="utf-8"
    )

    engine = SpokeSynchronizer(spoke_root=spoke_root, hub_root=hub_root)
    # Test dry-run with bootstrap=True
    code = engine.sync(dry_run=True, check_git=False, bootstrap=True)
    assert code == 0


def test_check_hub_import_depth_excludes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test check_hub_import_depth exclusions (.agents, .md, .venv) in single file and directory scan."""
    from scripts.spoke.check_hub_import_depth import main, scan_file

    # 1. File with violation
    bad_py = tmp_path / "bad.py"
    bad_py.write_text("from ccba_legal.crawler.chrome_cdp import something\n", encoding="utf-8")
    violations = scan_file(bad_py)
    assert len(violations) == 1

    # 2. File with top-level import (compliant)
    good_py = tmp_path / "good.py"
    good_py.write_text("from ccba_legal import ChromeCDP\n", encoding="utf-8")
    violations_good = scan_file(good_py)
    assert len(violations_good) == 0

    # 3. Directory scan with excluded folders containing deep imports
    mock_spoke = tmp_path / "mock_spoke"
    mock_spoke.mkdir()
    (mock_spoke / "src").mkdir()
    (mock_spoke / "src" / "app.py").write_text("from ccba_ai import ai\n", encoding="utf-8")

    # Put violations inside excluded folders (.agents, .md, .venv)
    for excluded in [".agents", ".md", ".venv"]:
        ex_dir = mock_spoke / excluded
        ex_dir.mkdir()
        (ex_dir / "deep.py").write_text(
            "from ccba_legal.crawler.chrome_cdp import helper\n", encoding="utf-8"
        )

    monkeypatch.setattr(sys, "argv", ["check_hub_import_depth.py", "--path", str(mock_spoke)])
    exit_code = main()
    assert exit_code == 0

    # If violation added in src/, directory scan must detect it and return 1
    (mock_spoke / "src" / "bad.py").write_text(
        "from ccba_legal.crawler.chrome_cdp import helper\n", encoding="utf-8"
    )
    exit_code_bad = main()
    assert exit_code_bad == 1


def test_run_spoke_sync_cli_with_bootstrap(tmp_path: Path):
    """Test run_spoke_sync_cli accepts --bootstrap and passes it to sync_project."""
    with patch("scripts.spoke.sync.cli.sync_project") as mock_sync:
        mock_sync.return_value = 0
        code = run_spoke_sync_cli(["--spoke", str(tmp_path), "--apply", "--bootstrap"])
        assert code == 0
        mock_sync.assert_called_once_with(
            str(tmp_path),
            None,
            dry_run=False,
            force=False,
            backup=True,
            bootstrap=True,
        )


def test_ccba_platform_cli_arguments():
    """Test ccba_platform_cli argument parser supports new flags."""
    from scripts.ccba_platform_cli import build_parser

    parser = build_parser()

    # Test adopt-spoke --archetype
    adopt_args = parser.parse_args(["adopt-spoke", "--archetype", "knowledge_corpus"])
    assert adopt_args.archetype == "knowledge_corpus"

    # Test sync-spoke flags
    sync_args = parser.parse_args(
        [
            "sync-spoke",
            "--apply",
            "--bootstrap",
            "--force",
            "--include-sandboxes",
        ]
    )
    assert sync_args.apply is True
    assert sync_args.bootstrap is True
    assert sync_args.force is True
    assert sync_args.include_sandboxes is True

    # Test doc-audit flags
    doc_args = parser.parse_args(["doc-audit", "--fix", "--changed", "--root", "."])
    assert doc_args.fix is True
    assert doc_args.changed is True
    assert doc_args.root == "."


def test_spoke_registrar_missing_key_behavior(tmp_path: Path, capsys):
    """Test SpokeRegistrar handles missing registry public key gracefully without legacy path."""
    hub_root = tmp_path / "mock_hub"
    hub_root.mkdir()
    (hub_root / ".agents" / "resources").mkdir(parents=True)
    # Note: no registry_public_key.pem created

    registrar = SpokeRegistrar()
    registrar.register(tmp_path, hub_root, "TestSpoke", "Phần mềm")

    captured = capsys.readouterr()
    assert "Hub registry public key not found" in captured.err
    assert "legacy path" not in captured.err


def test_sync_spoke_delegate_parity() -> None:
    """Test scripts/sync_spoke.py thin delegate contract and CLI parity."""
    import subprocess
    import sys

    from scripts import sync_spoke
    from scripts.spoke.sync import (
        list_project_backups,
        rollback_project,
        sync_all_spokes,
        sync_project,
    )
    from scripts.spoke.sync.cli import run_spoke_sync_cli

    # 1. Import and symbol parity
    assert sync_spoke.sync_project is sync_project
    assert sync_spoke.sync_all_spokes is sync_all_spokes
    assert sync_spoke.list_project_backups is list_project_backups
    assert sync_spoke.rollback_project is rollback_project
    assert sync_spoke.run_spoke_sync_cli is run_spoke_sync_cli

    # 2. In-process CLI delegate call
    with pytest.raises(SystemExit) as exc_info:
        sync_spoke.main(["--help"])
    assert exc_info.value.code == 0

    # 3. Subprocess CLI smoke test
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "sync_spoke.py"
    cmd = [sys.executable, str(script_path), "--help"]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    assert res.returncode == 0
    assert "CCBA Spoke Synchronizer (Safe-by-Default)" in res.stdout
    assert "--spoke" in res.stdout
    assert "--bootstrap" in res.stdout
    assert "--dry-run" in res.stdout
    assert "--apply" in res.stdout
