"""TDD Unit Tests for Spoke Shared SDKs Inspector (Zero-Latency File Inspection)."""

from pathlib import Path

import pytest
from scripts.spoke.spoke_synchronizer import SharedSdkInspector


@pytest.fixture
def mock_hub_with_packages(tmp_path: Path) -> Path:
    """Creates a mock Hub with packages/ccba-harness, ccba-ai, and ccba-ooxml."""
    hub_dir = tmp_path / "mock-hub"
    (hub_dir / "packages" / "ccba-harness").mkdir(parents=True, exist_ok=True)
    (hub_dir / "packages" / "ccba-ai").mkdir(parents=True, exist_ok=True)
    (hub_dir / "packages" / "ccba-ooxml").mkdir(parents=True, exist_ok=True)
    return hub_dir


def test_non_python_project_returns_no_recommendations(
    tmp_path: Path, mock_hub_with_packages: Path
):
    """Non-Python spokes (e.g. Pure Consulting/Design without python files or venv) should not return any SDK prompts."""
    spoke_dir = tmp_path / "consulting-spoke"
    spoke_dir.mkdir()

    inspector = SharedSdkInspector(spoke_dir, mock_hub_with_packages, project_type="Thiết kế")
    assert not inspector.is_python_project()
    assert inspector.inspect() == {}
    assert inspector.get_recommendations() == []


def test_python_project_without_installed_packages_returns_recommendations(
    tmp_path: Path, mock_hub_with_packages: Path
):
    """Python spoke without installed editable packages should return install recommendations."""
    spoke_dir = tmp_path / "python-spoke"
    spoke_dir.mkdir()
    (spoke_dir / "pyproject.toml").write_text("[project]\nname='app'", encoding="utf-8")

    inspector = SharedSdkInspector(spoke_dir, mock_hub_with_packages, project_type="Phần mềm")
    assert inspector.is_python_project()
    status = inspector.inspect()
    assert status.get("ccba-harness") is False
    assert status.get("ccba-ai") is False
    assert status.get("ccba-ooxml") is False

    recs = inspector.get_recommendations()
    assert len(recs) == 3
    assert any("ccba-harness" in r for r in recs)
    assert any("ccba-ai" in r for r in recs)
    assert any("ccba-ooxml" in r for r in recs)
    assert all(r.startswith("pip install -e ") for r in recs)


def test_python_project_with_installed_packages_via_pth_returns_clean(
    tmp_path: Path, mock_hub_with_packages: Path
):
    """Python spoke with .venv containing .pth or egg-link should detect them and return no missing recommendations."""
    spoke_dir = tmp_path / "installed-python-spoke"
    spoke_dir.mkdir()

    # Create mock .venv with site-packages
    site_packages = spoke_dir / ".venv" / "Lib" / "site-packages"
    site_packages.mkdir(parents=True, exist_ok=True)

    # Mock editable install .pth files
    (site_packages / "ccba_harness.pth").write_text(
        str(mock_hub_with_packages / "packages" / "ccba-harness"), encoding="utf-8"
    )
    (site_packages / "ccba_ai.pth").write_text(
        str(mock_hub_with_packages / "packages" / "ccba-ai"), encoding="utf-8"
    )
    (site_packages / "ccba_ooxml.pth").write_text(
        str(mock_hub_with_packages / "packages" / "ccba-ooxml"), encoding="utf-8"
    )

    inspector = SharedSdkInspector(spoke_dir, mock_hub_with_packages, project_type="Phần mềm")
    assert inspector.is_python_project()
    status = inspector.inspect()
    assert status.get("ccba-harness") is True
    assert status.get("ccba-ai") is True
    assert status.get("ccba-ooxml") is True

    recs = inspector.get_recommendations()
    assert recs == []


def test_python_project_with_installed_packages_via_dist_info(
    tmp_path: Path, mock_hub_with_packages: Path
):
    """Python spoke with dist-info directory should detect package installation."""
    spoke_dir = tmp_path / "dist-info-spoke"
    spoke_dir.mkdir()

    site_packages = spoke_dir / "venv" / "lib" / "python3.11" / "site-packages"
    site_packages.mkdir(parents=True, exist_ok=True)

    (site_packages / "ccba_harness-0.1.0.dist-info").mkdir(parents=True, exist_ok=True)
    (site_packages / "ccba_ai-0.1.0.dist-info").mkdir(parents=True, exist_ok=True)
    (site_packages / "__editable__.ccba_ooxml-0.1.0.pth").write_text("...", encoding="utf-8")

    inspector = SharedSdkInspector(spoke_dir, mock_hub_with_packages, project_type="Phần mềm")
    status = inspector.inspect()
    assert status.get("ccba-harness") is True
    assert status.get("ccba-ai") is True
    assert status.get("ccba-ooxml") is True
    assert inspector.get_recommendations() == []


def test_spoke_bootstrapper_resolves_packages_and_generates_lockfile(
    tmp_path: Path, mock_hub_with_packages: Path
):
    """Verify SpokeBootstrapper resolves Tier 0 + declared packages and generates git-ignored lockfile."""
    from scripts.spoke.spoke_bootstrap import SpokeBootstrapper

    spoke_dir = tmp_path / "target-spoke"
    spoke_dir.mkdir()
    (spoke_dir / ".agents").mkdir()
    (spoke_dir / ".agents" / "workspace_context.yaml").write_text(
        "project:\n  name: target-spoke\n  archetype: knowledge_corpus\n  type: Phần mềm\nhub_packages:\n  - ccba-ooxml\n",
        encoding="utf-8",
    )

    bootstrapper = SpokeBootstrapper(spoke_path=spoke_dir, hub_path=mock_hub_with_packages)
    assert bootstrapper.is_python_project() is True

    packages = bootstrapper.resolve_target_packages()
    assert "ccba-harness" in packages
    assert "ccba-ai" in packages
    assert "ccba-ooxml" in packages
    # Check topology order: ccba-harness before ccba-ai
    assert packages.index("ccba-harness") < packages.index("ccba-ai")

    # Generate requirements-hub.txt
    req_file = bootstrapper.generate_requirements_hub_file(packages)
    assert req_file.exists()
    content = req_file.read_text(encoding="utf-8")
    assert "-e " in content
    assert "ccba-ai" in content

    # Check gitignore update
    bootstrapper.ensure_gitignore_rule()
    gitignore = spoke_dir / ".gitignore"
    assert gitignore.exists()
    gi_content = gitignore.read_text(encoding="utf-8")
    assert "requirements-hub.txt" in gi_content
    assert ".md/data/telemetry_summary.json" in gi_content
    assert ".md/data/*.json" in gi_content


def test_spoke_bootstrapper_non_python_project_ensures_gitignore(tmp_path: Path):
    """Verify SpokeBootstrapper.bootstrap updates .gitignore even for non-Python spokes."""
    from scripts.spoke.spoke_bootstrap import SpokeBootstrapper

    spoke_dir = tmp_path / "non-python-spoke"
    spoke_dir.mkdir()
    hub_dir = tmp_path / "hub"
    hub_dir.mkdir()

    bootstrapper = SpokeBootstrapper(spoke_path=spoke_dir, hub_path=hub_dir)
    ret = bootstrapper.bootstrap(dry_run=False)
    assert ret == 0

    gitignore = spoke_dir / ".gitignore"
    assert gitignore.exists()
    gi_content = gitignore.read_text(encoding="utf-8")
    assert ".md/data/telemetry_summary.json" in gi_content
    assert ".md/data/*.json" in gi_content


def test_sys_path_migration_cleans_boilerplate(tmp_path: Path):
    """Verify SysPathMigration tool removes sys.path.insert and HUB_SRC hacks."""
    from scripts.spoke.migrate_sys_path_hacks import SysPathMigration

    spoke_dir = tmp_path / "messy-spoke"
    spoke_dir.mkdir()
    script_file = spoke_dir / "test_script.py"
    script_file.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        'HUB_SRC = Path(r"D:\\GitHubProjects\\ccba-agent-platform\\packages\\ccba-legal-intel\\src")\n'
        "sys.path.insert(0, str(HUB_SRC))\n"
        "from ccba_legal.crawler import ChromeCDP\n"
        'print("hello")\n',
        encoding="utf-8",
    )

    migration = SysPathMigration(spoke_root=spoke_dir)
    migration.run(dry_run=False, backup=True)

    cleaned_content = script_file.read_text(encoding="utf-8")
    assert "HUB_SRC" not in cleaned_content
    assert "sys.path.insert" not in cleaned_content
    assert "from ccba_legal.crawler import ChromeCDP" in cleaned_content
    assert (spoke_dir / "test_script.py.bak").exists()
