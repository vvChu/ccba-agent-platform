"""Automated CI Gate: Hub-Spoke Taxonomy & Bundle Integrity (ADR 0041, ADR 0044).

Ensures all workflow/skill applies_to declarations, CLI choices, and bootstrap
defaults remain 100% consistent with catalog.yaml bundles.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG_PATH = HUB_ROOT / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
WORKFLOWS_DIR = HUB_ROOT / ".agents" / "workflows"
SKILLS_DIR = HUB_ROOT / ".agents" / "skills"

VALID_ARCHETYPES = {
    "project_delivery",
    "enterprise_governance",
    "knowledge_corpus",
    "specialized_extension",
    "platform_hub",
}


@pytest.fixture(scope="module")
def catalog_bundles() -> set[str]:
    """Extract registered bundle names from catalog.yaml."""
    assert CATALOG_PATH.exists(), f"catalog.yaml not found at {CATALOG_PATH}"
    data = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8")) or {}
    bundles = data.get("bundles", {})
    assert isinstance(bundles, dict), "bundles section must be a dictionary"
    return set(bundles.keys())


def test_catalog_has_standard_bundles(catalog_bundles: set[str]) -> None:
    """Verify catalog.yaml contains all 7 core CCBA bundle types."""
    expected = {
        "Phần mềm",
        "Thẩm tra thiết kế",
        "Thiết kế",
        "Kiểm định",
        "BIM",
        "Tác vụ Admin",
        "Pháp điển",
    }
    assert expected.issubset(catalog_bundles), (
        f"catalog.yaml is missing expected bundles: {expected - catalog_bundles}"
    )


def test_all_workflows_applies_to_match_catalog_bundles(catalog_bundles: set[str]) -> None:
    """Scan every workflow file and verify all applies_to items exist in catalog.yaml bundles."""
    workflow_files = list(WORKFLOWS_DIR.glob("*.md"))
    if not workflow_files:
        pytest.skip("All workflows migrated to skills (.agents/skills/*/SKILL.md)")

    errors: list[str] = []

    for wf in workflow_files:
        content = wf.read_text(encoding="utf-8")
        if not content.startswith("---"):
            continue

        parts = content.split("---", 2)
        if len(parts) < 3:
            continue

        try:
            fm: dict[str, Any] = yaml.safe_load(parts[1]) or {}
        except Exception as e:
            errors.append(f"{wf.name}: Failed to parse YAML frontmatter: {e}")
            continue

        applies_to = fm.get("applies_to")
        if not applies_to:
            continue

        if isinstance(applies_to, str):
            applies_to = [applies_to]

        if isinstance(applies_to, list):
            for item in applies_to:
                if str(item) not in catalog_bundles:
                    errors.append(
                        f"{wf.name}: Invalid applies_to item '{item}'. Must be one of: {sorted(catalog_bundles)}"
                    )

    assert not errors, "\n".join(errors)


def test_all_skills_applies_to_match_catalog_bundles(catalog_bundles: set[str]) -> None:
    """Scan every skill file and verify all applies_to items exist in catalog.yaml bundles."""
    skill_files = list(SKILLS_DIR.glob("**/SKILL.md"))
    assert len(skill_files) > 0, "No skill files found to test"

    errors: list[str] = []

    for sf in skill_files:
        content = sf.read_text(encoding="utf-8")
        if not content.startswith("---"):
            continue

        parts = content.split("---", 2)
        if len(parts) < 3:
            continue

        try:
            fm: dict[str, Any] = yaml.safe_load(parts[1]) or {}
        except Exception as e:
            errors.append(f"{sf.relative_to(HUB_ROOT)}: Failed to parse YAML frontmatter: {e}")
            continue

        applies_to = fm.get("applies_to")
        if not applies_to:
            continue

        if isinstance(applies_to, str):
            applies_to = [applies_to]

        if isinstance(applies_to, list):
            for item in applies_to:
                if str(item) not in catalog_bundles:
                    errors.append(
                        f"{sf.relative_to(HUB_ROOT)}: Invalid applies_to item '{item}'. Must be one of: {sorted(catalog_bundles)}"
                    )

    assert not errors, "\n".join(errors)


def test_spoke_bootstrap_archetype_defaults_validity() -> None:
    """Verify ARCHETYPE_TIER1_DEFAULTS in spoke_bootstrap.py only uses valid ADR 0041 archetypes."""
    from scripts.spoke.spoke_bootstrap import ARCHETYPE_TIER1_DEFAULTS

    for arch in ARCHETYPE_TIER1_DEFAULTS.keys():
        assert arch in VALID_ARCHETYPES, (
            f"Invalid archetype '{arch}' in ARCHETYPE_TIER1_DEFAULTS. Must be in {VALID_ARCHETYPES}"
        )


def test_adopt_spoke_cli_type_help_completeness(catalog_bundles: set[str]) -> None:
    """Verify adopt_spoke.py help message lists all registered bundle types."""
    adopt_script = HUB_ROOT / "scripts" / "adopt_spoke.py"
    assert adopt_script.exists()
    content = adopt_script.read_text(encoding="utf-8")

    for bundle in catalog_bundles:
        assert f"'{bundle}'" in content or f'"{bundle}"' in content, (
            f"Bundle type '{bundle}' is missing from scripts/adopt_spoke.py help/options"
        )


def test_catalog_yaml_is_compiled_and_in_sync() -> None:
    """Verify catalog.yaml is compiled and 100% in sync with markdown frontmatters (ADR 0047)."""
    from scripts.governance.compile_catalog import check_catalog_in_sync

    in_sync, msg = check_catalog_in_sync(HUB_ROOT)
    assert in_sync, f"catalog.yaml is out of sync with frontmatters:\n{msg}"
