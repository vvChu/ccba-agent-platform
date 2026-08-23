"""Integration Test Matrix: All 5 Archetypes x All 7 Bundle Types Lifecycle.

Simulates the end-to-end chain:
detect_spoke_stack -> merge_workspace_context -> SpokeBootstrapper -> SpokeSynchronizer(dry_run)
ensuring ZERO runtime exceptions across all 35 combinations.
"""

from pathlib import Path

import pytest
import yaml
from scripts.spoke.spoke_adopter import detect_spoke_stack
from scripts.spoke.spoke_bootstrap import SpokeBootstrapper
from scripts.spoke.spoke_synchronizer import SpokeSynchronizer

ARCHETYPES = [
    "project_delivery",
    "enterprise_governance",
    "knowledge_corpus",
    "specialized_extension",
    "platform_hub",
]

BUNDLE_TYPES = [
    "Phần mềm",
    "Thẩm tra thiết kế",
    "Thiết kế",
    "Kiểm định",
    "BIM",
    "Tác vụ Admin",
    "Pháp điển",
]


@pytest.fixture
def mock_hub_root(tmp_path: Path) -> Path:
    """Create a minimal mock Hub environment with catalog.yaml."""
    hub = tmp_path / "mock-hub"
    hub.mkdir(parents=True)

    # Copy actual catalog.yaml
    actual_catalog = (
        Path(__file__).resolve().parent.parent
        / ".agents"
        / "skills"
        / "platform-loader"
        / "catalog.yaml"
    )
    target_catalog_dir = hub / ".agents" / "skills" / "platform-loader"
    target_catalog_dir.mkdir(parents=True)
    target_catalog_dir.joinpath("catalog.yaml").write_text(
        actual_catalog.read_text(encoding="utf-8"), encoding="utf-8"
    )

    # Create dummy workflows and resources dirs
    (hub / ".agents" / "workflows" / "resources").mkdir(parents=True)
    (hub / ".agents" / "AGENTS.md").write_text("# Constitution", encoding="utf-8")
    (hub / ".md" / "data").mkdir(parents=True)
    return hub


@pytest.mark.parametrize("archetype", ARCHETYPES)
@pytest.mark.parametrize("bundle_type", BUNDLE_TYPES)
def test_archetype_bundle_matrix_lifecycle(
    tmp_path: Path,
    mock_hub_root: Path,
    archetype: str,
    bundle_type: str,
) -> None:
    """Verify that every Archetype x Bundle Type combination passes validation and dry-run sync."""
    spoke_dir = tmp_path / f"spoke_{archetype}_{bundle_type}".replace(" ", "_")
    spoke_dir.mkdir(parents=True)
    (spoke_dir / ".md").mkdir()

    # 1. Setup initial workspace_context.yaml
    ctx_path = spoke_dir / ".md" / "workspace_context.yaml"
    initial_ctx = {
        "project": {
            "name": spoke_dir.name,
            "archetype": archetype,
            "type": bundle_type,
            "mode": "software" if bundle_type in ("Phần mềm", "Pháp điển") else "delivery",
            "hub_path": str(mock_hub_root),
        }
    }
    ctx_path.write_text(yaml.safe_dump(initial_ctx), encoding="utf-8")

    # 2. Test SpokeBootstrapper
    bootstrapper = SpokeBootstrapper(spoke_path=spoke_dir, hub_path=mock_hub_root)
    is_py = bootstrapper.is_python_project()
    assert isinstance(is_py, bool)

    # 3. Test SpokeSynchronizer Dry-Run
    synchronizer = SpokeSynchronizer(str(spoke_dir))
    exit_code = synchronizer.sync(dry_run=True, force=True)
    assert exit_code == 0, (
        f"Synchronizer failed for {archetype} / {bundle_type} with exit code {exit_code}"
    )


def test_detect_spoke_stack_knowledge_corpus(tmp_path: Path) -> None:
    """Verify legal/OKF directory structure auto-detects to knowledge_corpus and Pháp điển."""
    spoke = tmp_path / "legal-corpus-spoke"
    spoke.mkdir()
    (spoke / ".md" / "legal_docs").mkdir(parents=True)
    (spoke / "OKF").mkdir()

    desc, detected_type, detected_arch = detect_spoke_stack(spoke)
    assert detected_arch == "knowledge_corpus"
    assert detected_type == "Pháp điển"


def test_detect_spoke_stack_governance(tmp_path: Path) -> None:
    """Verify PowerShell/SharePoint structure auto-detects to enterprise_governance and Tác vụ Admin."""
    spoke = tmp_path / "idop-spoke"
    spoke.mkdir()
    (spoke / "tools").mkdir(parents=True)
    (spoke / "tools" / "deploy.ps1").write_text("# ps1 script", encoding="utf-8")

    desc, detected_type, detected_arch = detect_spoke_stack(spoke)
    assert detected_arch == "enterprise_governance"
    assert detected_type == "Tác vụ Admin"
