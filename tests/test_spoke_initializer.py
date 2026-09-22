"""TDD Unit Tests for Deterministic CCBA Spoke Initializer."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
import yaml
from scripts.spoke.spoke_initializer import SpokeInitializer, init_project


@pytest.fixture
def temp_hub(tmp_path: Path) -> Path:
    """Fixture creating a mock hub root directory."""
    hub = tmp_path / "mock-hub"
    hub.mkdir(parents=True, exist_ok=True)
    agents_dir = hub / ".agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "AGENTS.md").write_text(
        "# CCBA Agent Services Platform — Layer 1 Constitution\n\n"
        "## Core Invariants\n\n"
        "- **Virtual Hub Fallback**: In Spoke mode, fallback to Hub.\n",
        encoding="utf-8",
    )
    return hub


@pytest.fixture
def temp_spoke(tmp_path: Path) -> Path:
    """Fixture creating a clean spoke directory."""
    spoke = tmp_path / "target-spoke"
    spoke.mkdir(parents=True, exist_ok=True)
    return spoke


def test_scaffold_directories_and_index_md(temp_spoke: Path, temp_hub: Path):
    """Scaffolds .md/ and .agents/ directories and generates initial .md/INDEX.md."""
    initializer = SpokeInitializer(spoke_path=temp_spoke, hub_path=temp_hub, name="test-spoke")
    scaffolded = initializer.scaffold_directories(dry_run=False)

    assert (temp_spoke / ".md" / "extracted_docs").is_dir()
    assert (temp_spoke / ".md" / "knowledge").is_dir()
    assert (temp_spoke / ".md" / "archive").is_dir()
    assert (temp_spoke / ".agents").is_dir()

    index_md = temp_spoke / ".md" / "INDEX.md"
    assert index_md.exists()
    content = index_md.read_text(encoding="utf-8")
    assert "test-spoke" in content
    assert "workspace_context.yaml" in content
    assert len(scaffolded) == 4


def test_generate_workspace_context_all_archetypes(temp_spoke: Path, temp_hub: Path):
    """Tests that all 4 Archetypes generate correct schema with specific defaults."""
    archetypes = [
        ("project_delivery", "Thẩm tra thiết kế", "delivery", "third-party"),
        ("enterprise_governance", "Tác vụ Admin", "admin", None),
        ("knowledge_corpus", "Pháp điển", "software", "legal"),
        ("specialized_extension", "Phần mềm", "software", None),
    ]

    for arch, exp_type, exp_mode, exp_qc in archetypes:
        target_dir = temp_spoke / f"spoke_{arch}"
        target_dir.mkdir(parents=True, exist_ok=True)

        init = SpokeInitializer(spoke_path=target_dir, hub_path=temp_hub, archetype=arch)
        ctx_file = init.generate_workspace_context(dry_run=False)
        assert ctx_file.exists()

        data: dict[str, Any] = yaml.safe_load(ctx_file.read_text(encoding="utf-8"))
        proj = data["project"]
        assert proj["archetype"] == arch
        assert proj["type"] == exp_type
        assert proj["mode"] == exp_mode
        assert proj["qc_mode"] == exp_qc
        assert "hub_path" in proj

        if arch == "specialized_extension":
            assert proj["sub_type"] == "personal_sandbox"
            assert "qc_governance" in data
            assert data["qc_governance"]["authorized_qc_level"] == "LEVEL_1_TECHNICAL_CHECK"
            assert data["guardrails"]["sandbox_mode"] is True

        if arch == "knowledge_corpus":
            assert "ccba-legal-intel" in data.get("hub_packages", [])


def test_hub_path_relative_and_cross_drive(
    temp_spoke: Path, temp_hub: Path, monkeypatch: pytest.MonkeyPatch
):
    """Verifies relative POSIX hub path and graceful fallback to None on cross-drive ValueError."""
    init = SpokeInitializer(spoke_path=temp_spoke, hub_path=temp_hub)
    ctx_file = init.generate_workspace_context(dry_run=False)
    data = yaml.safe_load(ctx_file.read_text(encoding="utf-8"))
    assert data["project"]["hub_path"] == "../mock-hub"

    # Cross-drive mock (e.g. Windows C: vs D:)
    def mock_relpath(path, start=None):
        raise ValueError("path is on mount 'D:', start on mount 'C:'")

    monkeypatch.setattr(os.path, "relpath", mock_relpath)

    cross_dir = temp_spoke / "cross_spoke"
    cross_dir.mkdir(parents=True, exist_ok=True)
    cross_init = SpokeInitializer(spoke_path=cross_dir, hub_path=temp_hub)
    cross_file = cross_init.generate_workspace_context(dry_run=False)
    cross_data = yaml.safe_load(cross_file.read_text(encoding="utf-8"))
    assert cross_data["project"]["hub_path"] is None


def test_failsafe_gate_rejects_existing_context(temp_spoke: Path, temp_hub: Path, capsys):
    """Fail-Safe Gate rejects re-initialization when workspace_context exists unless force=True."""
    md_dir = temp_spoke / ".md"
    md_dir.mkdir(parents=True, exist_ok=True)
    ctx_file = md_dir / "workspace_context.yaml"
    ctx_file.write_text("project:\n  name: OldSpoke\n", encoding="utf-8")

    init = SpokeInitializer(spoke_path=temp_spoke, hub_path=temp_hub)

    # 1. Direct method raises FileExistsError without force
    with pytest.raises(FileExistsError):
        init.generate_workspace_context(dry_run=False, force=False)

    # 2. init() returns exit code 1 with instructions on stderr
    exit_code = init.init(dry_run=False, force=False)
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "FAIL-SAFE GATE" in captured.err
    assert "bootstrap-spoke --create-venv" in captured.err

    # 3. Check when context is in .agents/
    ctx_file.unlink()
    agents_dir = temp_spoke / ".agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "workspace_context.yaml").write_text("project: Old\n", encoding="utf-8")

    exit_code_agents = init.init(dry_run=False, force=False)
    assert exit_code_agents == 1

    # 4. force=True allows overwrite
    exit_code_force = init.init(dry_run=False, force=True)
    assert exit_code_force == 0


def test_dry_run_exits_zero_without_modifying_disk(temp_spoke: Path, temp_hub: Path, capsys):
    """Dry-run returns 0 and does not write files even if context exists."""
    md_dir = temp_spoke / ".md"
    md_dir.mkdir(parents=True, exist_ok=True)
    (md_dir / "workspace_context.yaml").write_text("project: Existing\n", encoding="utf-8")

    init = SpokeInitializer(spoke_path=temp_spoke, hub_path=temp_hub)
    exit_code = init.init(dry_run=True, force=False)
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "[DRY-RUN]" in captured.out
    assert "Phát hiện Spoke đã có cấu hình" in captured.out

    # On clean directory dry-run
    clean_spoke = temp_spoke / "clean_spoke"
    clean_init = SpokeInitializer(spoke_path=clean_spoke, hub_path=temp_hub)
    code_clean = clean_init.init(dry_run=True)
    assert code_clean == 0
    assert not clean_spoke.exists() or not (clean_spoke / ".md").exists()


def test_gitignore_comprehensive_rules(temp_spoke: Path, temp_hub: Path):
    """Ensures .gitignore contains hygiene rules and Spoke Leakage Guard rules."""
    init = SpokeInitializer(spoke_path=temp_spoke, hub_path=temp_hub)
    created = init.ensure_gitignore(dry_run=False)
    assert created is True

    gitignore = temp_spoke / ".gitignore"
    assert gitignore.exists()
    content = gitignore.read_text(encoding="utf-8")

    hygiene_expected = [".venv/", ".env", "__pycache__/", "*.pyc", ".pytest_cache/", ".coverage"]
    leakage_expected = [
        "requirements-hub.txt",
        ".md/teach/",
        ".md/scratch/",
        ".md/data/telemetry_summary.json",
        ".md/data/*.json",
        ".tmp/",
        ".out-of-scope/",
    ]

    for rule in hygiene_expected:
        assert rule in content
    for rule in leakage_expected:
        assert rule in content

    # Calling again returns False (idempotent, no changes needed)
    assert init.ensure_gitignore(dry_run=False) is False


def test_maskara_hook_posix_path_and_executable_mode(temp_spoke: Path, temp_hub: Path):
    """Tests Maskara pre-commit hook generation with POSIX path and executable mode."""
    # 1. No git directory -> logs info and returns False
    init = SpokeInitializer(spoke_path=temp_spoke, hub_path=temp_hub)
    installed_no_git = init.install_security_guardrails(dry_run=False)
    assert installed_no_git is False

    # 2. With git directory
    (temp_spoke / ".git").mkdir()
    installed = init.install_security_guardrails(dry_run=False)
    assert installed is True

    hook_file = temp_spoke / ".git" / "hooks" / "pre-commit"
    assert hook_file.exists()
    hook_content = hook_file.read_text(encoding="utf-8")
    assert "Maskara" in hook_content
    # POSIX hub path
    assert temp_hub.as_posix() in hook_content

    # Executable permissions (Linux/POSIX)
    if os.name == "posix":
        mode = hook_file.stat().st_mode
        assert mode & 0o111 != 0


def test_virtual_hub_fallback_in_agents_md(temp_spoke: Path, temp_hub: Path):
    """Tests Virtual Hub Fallback constitution creation and non-destructive merge."""
    init = SpokeInitializer(spoke_path=temp_spoke, hub_path=temp_hub)
    init.setup_virtual_hub_fallback(dry_run=False)

    agents_md = temp_spoke / ".agents" / "AGENTS.md"
    assert agents_md.exists()
    content = agents_md.read_text(encoding="utf-8")
    assert "Virtual Hub Fallback" in content

    # Existing custom sections should be preserved
    custom_section = "\n## Custom Spoke Section\n- Custom invariant\n"
    agents_md.write_text(content + custom_section, encoding="utf-8")

    init.setup_virtual_hub_fallback(dry_run=False)
    updated_content = agents_md.read_text(encoding="utf-8")
    assert "Virtual Hub Fallback" in updated_content
    assert "## Custom Spoke Section" in updated_content


def test_cli_init_spoke_argument_parsing_and_execution(
    temp_spoke: Path, temp_hub: Path, monkeypatch: pytest.MonkeyPatch
):
    """Tests CLI execution via ccba_platform_cli and init_spoke wrapper."""
    from scripts.ccba_platform_cli import main as platform_main
    from scripts.init_spoke import main as wrapper_main

    # 1. Test platform CLI with positional argument
    target_pos = temp_spoke / "cli_pos"
    monkeypatch.setattr(
        "sys.argv",
        [
            "ccba-platform",
            "init-spoke",
            str(target_pos),
            "--name",
            "cli-pos-spoke",
            "--archetype",
            "project_delivery",
            "--type",
            "Thiết kế",
        ],
    )
    res_pos = platform_main()
    assert res_pos == 0
    assert (target_pos / ".md" / "workspace_context.yaml").exists()

    # 2. Test platform CLI with -p / --path option
    target_opt = temp_spoke / "cli_opt"
    monkeypatch.setattr(
        "sys.argv",
        [
            "ccba-platform",
            "init-spoke",
            "-p",
            str(target_opt),
            "--archetype",
            "knowledge_corpus",
        ],
    )
    res_opt = platform_main()
    assert res_opt == 0
    ctx_data = yaml.safe_load(
        (target_opt / ".md" / "workspace_context.yaml").read_text(encoding="utf-8")
    )
    assert ctx_data["project"]["archetype"] == "knowledge_corpus"

    # 3. Test standalone init_spoke.py wrapper
    target_wrap = temp_spoke / "cli_wrap"
    monkeypatch.setattr(
        "sys.argv",
        [
            "init_spoke.py",
            str(target_wrap),
            "--archetype",
            "specialized_extension",
            "--sub-type",
            "personal_sandbox",
        ],
    )
    with pytest.raises(SystemExit) as excinfo:
        wrapper_main()
    assert excinfo.value.code == 0
    assert (target_wrap / ".md" / "workspace_context.yaml").exists()


def test_init_project_procedural_helper(temp_spoke: Path, temp_hub: Path):
    """Tests init_project procedural entrypoint function."""
    sub_dir = temp_spoke / "procedural"
    code = init_project(
        spoke_path=sub_dir,
        hub_path=temp_hub,
        name="procedural-spoke",
        archetype="enterprise_governance",
    )
    assert code == 0
    assert (sub_dir / ".md" / "workspace_context.yaml").exists()
    assert (sub_dir / ".md" / "INDEX.md").exists()
    assert (sub_dir / ".gitignore").exists()
    assert (sub_dir / ".agents" / "AGENTS.md").exists()


def test_conflicting_cli_paths(
    temp_spoke: Path, temp_hub: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    """Verifies that providing conflicting positional path and --path rejects with exit code 1."""
    from scripts.ccba_platform_cli import main as platform_main
    from scripts.init_spoke import main as wrapper_main

    pos_dir = temp_spoke / "path_a"
    opt_dir = temp_spoke / "path_b"

    # Platform CLI
    monkeypatch.setattr(
        "sys.argv",
        [
            "ccba-platform",
            "init-spoke",
            str(pos_dir),
            "-p",
            str(opt_dir),
        ],
    )
    res_platform = platform_main()
    assert res_platform == 1
    err_output = capsys.readouterr().err
    assert "Conflicting spoke paths specified" in err_output

    # Standalone wrapper CLI
    monkeypatch.setattr(
        "sys.argv",
        [
            "init_spoke.py",
            str(pos_dir),
            "--path",
            str(opt_dir),
        ],
    )
    with pytest.raises(SystemExit) as exc:
        wrapper_main()
    assert exc.value.code == 1


def test_install_security_guardrails_git_worktree(temp_spoke: Path, temp_hub: Path):
    """Tests that git worktree/submodule layout with .git file pointer installs hook correctly."""
    from scripts.spoke.spoke_adopter import install_security_guardrails

    main_repo = temp_spoke / "main_repo"
    main_git = main_repo / ".git"
    main_git.mkdir(parents=True)
    worktree_gitdir = main_git / "worktrees" / "wt1"
    worktree_gitdir.mkdir(parents=True)
    (worktree_gitdir / "commondir").write_text("../..\n", encoding="utf-8")

    wt_spoke = temp_spoke / "worktree_spoke"
    wt_spoke.mkdir(parents=True)
    (wt_spoke / ".git").write_text(f"gitdir: {worktree_gitdir.as_posix()}\n", encoding="utf-8")

    installed = install_security_guardrails(wt_spoke, temp_hub)
    assert installed is True
    # Hook should be installed in common hooks dir
    hook_file = main_git / "hooks" / "pre-commit"
    assert hook_file.exists()


def test_gitignore_exact_line_matching_prevents_leakage(temp_spoke: Path, temp_hub: Path):
    """Verifies that existing .env.example or redis_dist/ does not prevent adding .env and dist/."""
    init = SpokeInitializer(spoke_path=temp_spoke, hub_path=temp_hub)
    gitignore = temp_spoke / ".gitignore"
    gitignore.write_text(".env.example\n.env.local\nredis_dist/\n", encoding="utf-8")

    updated = init.ensure_gitignore(dry_run=False)
    assert updated is True

    content = gitignore.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]
    assert ".env" in lines
    assert "dist/" in lines


def test_sub_type_auto_selects_specialized_extension(temp_spoke: Path, temp_hub: Path):
    """Verifies that passing sub_type without archetype automatically selects specialized_extension."""
    init = SpokeInitializer(spoke_path=temp_spoke, hub_path=temp_hub, sub_type="personal_sandbox")
    assert init.archetype == "specialized_extension"
    assert init.sub_type == "personal_sandbox"


def test_legacy_agents_context_cleanup_on_force(temp_spoke: Path, temp_hub: Path):
    """Verifies that when legacy .agents/workspace_context.yaml exists, force overwrite removes it."""
    agents_dir = temp_spoke / ".agents"
    agents_dir.mkdir(parents=True)
    legacy_file = agents_dir / "workspace_context.yaml"
    legacy_file.write_text("project: legacy\n", encoding="utf-8")

    init = SpokeInitializer(spoke_path=temp_spoke, hub_path=temp_hub)
    ctx_file = init.generate_workspace_context(dry_run=False, force=True)

    assert ctx_file == temp_spoke / ".md" / "workspace_context.yaml"
    assert ctx_file.exists()
    assert not legacy_file.exists()


def test_sync_and_bootstrap_delegation(
    temp_spoke: Path, temp_hub: Path, monkeypatch: pytest.MonkeyPatch
):
    """Verifies that --sync and --bootstrap delegate properly and propagate exit codes."""
    init = SpokeInitializer(spoke_path=temp_spoke, hub_path=temp_hub)

    # 1. Successful sync and bootstrap
    class DummySync:
        def __init__(self, spoke_path=None, hub_root=None):
            pass

        def sync(self, dry_run=False, force=False):
            return 0

    class DummyBootstrap:
        def __init__(self, spoke_path=None, hub_path=None):
            pass

        def bootstrap(self, auto_create_venv=True, dry_run=False, force=False):
            return 0

    monkeypatch.setattr("scripts.spoke.spoke_synchronizer.SpokeSynchronizer", DummySync)
    monkeypatch.setattr("scripts.spoke.spoke_bootstrap.SpokeBootstrapper", DummyBootstrap)

    res_ok = init.init(sync=True, bootstrap=True)
    assert res_ok == 0

    # 2. Failed sync propagates non-zero code
    class FailingSync(DummySync):
        def sync(self, dry_run=False, force=False):
            return 42

    monkeypatch.setattr("scripts.spoke.spoke_synchronizer.SpokeSynchronizer", FailingSync)
    sub_fail = temp_spoke / "sub_fail"
    init_fail = SpokeInitializer(spoke_path=sub_fail, hub_path=temp_hub)
    res_fail = init_fail.init(sync=True)
    assert res_fail == 42


def test_invalid_archetype_error_handling(temp_spoke: Path, temp_hub: Path):
    """Verifies that invalid archetype returns 1 via init_project and raises ValueError via SpokeInitializer."""
    with pytest.raises(ValueError) as exc:
        SpokeInitializer(spoke_path=temp_spoke, hub_path=temp_hub, archetype="unknown_xyz")
    assert "Unknown archetype" in str(exc.value)

    res = init_project(spoke_path=temp_spoke, hub_path=temp_hub, archetype="unknown_xyz")
    assert res == 1
