"""TDD Unit Tests for Spoke Shared SDKs Inspector (Zero-Latency File Inspection)."""

from pathlib import Path

import pytest
from scripts.spoke.spoke_synchronizer import SharedSdkInspector


@pytest.fixture
def mock_hub_with_packages(tmp_path: Path) -> Path:
    """Creates a mock Hub with packages/ccba-ai and packages/ccba-ooxml."""
    hub_dir = tmp_path / "mock-hub"
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
    assert status.get("ccba-ai") is False
    assert status.get("ccba-ooxml") is False

    recs = inspector.get_recommendations()
    assert len(recs) == 2
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
    (site_packages / "ccba_ai.pth").write_text(
        str(mock_hub_with_packages / "packages" / "ccba-ai"), encoding="utf-8"
    )
    (site_packages / "ccba_ooxml.pth").write_text(
        str(mock_hub_with_packages / "packages" / "ccba-ooxml"), encoding="utf-8"
    )

    inspector = SharedSdkInspector(spoke_dir, mock_hub_with_packages, project_type="Phần mềm")
    assert inspector.is_python_project()
    status = inspector.inspect()
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

    (site_packages / "ccba_ai-0.1.0.dist-info").mkdir(parents=True, exist_ok=True)
    (site_packages / "__editable__.ccba_ooxml-0.1.0.pth").write_text("...", encoding="utf-8")

    inspector = SharedSdkInspector(spoke_dir, mock_hub_with_packages, project_type="Phần mềm")
    status = inspector.inspect()
    assert status.get("ccba-ai") is True
    assert status.get("ccba-ooxml") is True
    assert inspector.get_recommendations() == []
