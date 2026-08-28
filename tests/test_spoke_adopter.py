"""TDD Unit Tests for Brownfield Spoke Adoption & Non-Destructive Onboarding."""

from pathlib import Path

import pytest
import yaml
from scripts.spoke.spoke_adopter import (
    SpokeAdopter,
    SpokeDiscoveryReport,
    detect_spoke_stack,
    merge_workspace_context,
)


@pytest.fixture
def temp_spoke(tmp_path: Path) -> Path:
    """Fixture creating a mock brownfield spoke directory."""
    spoke_dir = tmp_path / "mock-idop-spoke"
    spoke_dir.mkdir(parents=True, exist_ok=True)
    return spoke_dir


def test_detect_spoke_stack_powershell(temp_spoke: Path):
    """Detects SharePoint / PowerShell stack."""
    (temp_spoke / "idop.ps1").write_text("Write-Output 'IDOP'", encoding="utf-8")
    (temp_spoke / "tools").mkdir(parents=True, exist_ok=True)
    (temp_spoke / "tools" / "deploy.ps1").write_text("# deploy", encoding="utf-8")

    stack, default_type, default_archetype = detect_spoke_stack(temp_spoke)
    assert "PowerShell" in stack or "SharePoint" in stack
    assert default_type == "Tác vụ Admin"
    assert default_archetype == "enterprise_governance"


def test_detect_spoke_stack_python(temp_spoke: Path):
    """Detects Python stack."""
    (temp_spoke / "pyproject.toml").write_text("[project]\nname='my-tool'", encoding="utf-8")
    stack, default_type, default_archetype = detect_spoke_stack(temp_spoke)
    assert "Python" in stack
    assert default_type == "Phần mềm"
    assert default_archetype == "specialized_extension"


def test_detect_spoke_stack_knowledge_corpus(temp_spoke: Path):
    """Detects OKF v2.4 Knowledge Corpus with legal_docs and legal_registry.yaml."""
    (temp_spoke / "legal_docs").mkdir(parents=True, exist_ok=True)
    (temp_spoke / "legal_registry.yaml").write_text("documents: []", encoding="utf-8")
    stack, default_type, default_archetype = detect_spoke_stack(temp_spoke)
    assert "Knowledge Base" in stack
    assert default_type == "Pháp điển"
    assert default_archetype == "knowledge_corpus"


def test_discovery_report_on_mature_spoke(temp_spoke: Path):
    """Generates detailed 3-tier discovery report for mature spoke."""
    # Setup mock git
    (temp_spoke / ".git").mkdir()
    # Setup custom workspace context
    md_dir = temp_spoke / ".md"
    md_dir.mkdir()
    custom_yaml = {
        "project_name": "MOCK-IDOP",
        "custom_milestone": "Stage 2 Ready",
        "document_groups": {"governance": ["rule1.md", "rule2.md"]},
    }
    with open(md_dir / "workspace_context.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(custom_yaml, f)

    (temp_spoke / "AGENTS.md").write_text("# Custom Constitution", encoding="utf-8")

    adopter = SpokeAdopter(temp_spoke)
    report = adopter.discover()

    assert isinstance(report, SpokeDiscoveryReport)
    assert report.has_git is True
    assert report.has_workspace_context is True
    assert report.has_custom_agents_md is True
    assert report.existing_context_data.get("custom_milestone") == "Stage 2 Ready"


def test_additive_merge_preserves_custom_fields(temp_spoke: Path):
    """Additive merge preserves 100% of existing custom fields and adds platform keys."""
    md_dir = temp_spoke / ".md"
    md_dir.mkdir()
    ctx_path = md_dir / "workspace_context.yaml"
    original_data = {
        "project_name": "CUSTOM-SPOKE",
        "custom_milestone": "Production Phase 1",
        "database": "Custom DB Schema",
        "document_groups": {"custom_group": ["file1.md"]},
        "initial_reading_sequence": [".md/file1.md"],
    }
    with open(ctx_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(original_data, f)

    hub_path = Path("D:/GitHubProjects/ccba-agent-platform")
    merged_data, backup_path = merge_workspace_context(
        ctx_path=ctx_path, hub_path=hub_path, project_type="Phần mềm", mode="hybrid"
    )

    assert backup_path.exists()
    assert merged_data["custom_milestone"] == "Production Phase 1"
    assert merged_data["database"] == "Custom DB Schema"
    assert "custom_group" in merged_data["document_groups"]
    assert merged_data["project"]["name"] == "CUSTOM-SPOKE"
    assert merged_data["project"]["type"] == "Phần mềm"
    assert merged_data["project"]["mode"] == "hybrid"
    assert "always" in merged_data.get("must_read", {})


def test_adopt_project_installs_maskara_hook(temp_spoke: Path):
    """Installs Maskara pre-commit hook if git repository exists."""
    (temp_spoke / ".git").mkdir()
    (temp_spoke / ".md").mkdir()
    (temp_spoke / ".md" / "workspace_context.yaml").write_text(
        "project_name: Test\n", encoding="utf-8"
    )

    adopter = SpokeAdopter(temp_spoke)
    adopter.install_security_guardrails()

    hook_file = temp_spoke / ".git" / "hooks" / "pre-commit"
    assert hook_file.exists()
    hook_content = hook_file.read_text(encoding="utf-8")
    assert "Maskara" in hook_content
