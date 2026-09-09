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


def test_all_skills_have_valid_bundle_field() -> None:
    """Scan every skill file and verify 'bundle' exists and belongs to registered bundles (ADR 0041, ADR 0044)."""
    from scripts.governance.skill_auditor import SkillAuditor

    auditor = SkillAuditor(HUB_ROOT)
    valid_bundles = auditor.get_valid_bundles()

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

        bundle = fm.get("bundle")
        if not bundle:
            errors.append(
                f"{sf.relative_to(HUB_ROOT)}: Missing required 'bundle' field in frontmatter"
            )
        elif str(bundle) not in valid_bundles:
            errors.append(
                f"{sf.relative_to(HUB_ROOT)}: Invalid bundle '{bundle}'. Must be one of: {sorted(valid_bundles)}"
            )

    assert not errors, "\n".join(errors)


def test_zero_unregistered_slash_commands_in_skills_and_readme() -> None:
    """Verify scanning .agents/skills/ and README.md yields zero references to unregistered slash commands."""
    from ccba_harness.skill_validator import SkillValidator

    validator = SkillValidator(HUB_ROOT)
    registered_commands = validator.get_registered_commands()

    files_to_check = sorted(SKILLS_DIR.rglob("*.md"))
    readme_path = HUB_ROOT / "README.md"
    if readme_path.exists():
        files_to_check.append(readme_path)

    errors: list[str] = []
    for md_file in files_to_check:
        if not md_file.exists():
            continue
        issues = validator.audit_slash_commands(
            md_file, registered_commands=registered_commands
        )
        for issue in issues:
            rel_file = (
                md_file.relative_to(HUB_ROOT)
                if md_file.is_relative_to(HUB_ROOT)
                else md_file
            )
            errors.append(f"{rel_file} -> {issue}")

    assert not errors, (
        f"Detected {len(errors)} unregistered slash command reference(s):\n"
        + "\n".join(errors)
    )


def test_standalone_skills_catalog_parity() -> None:
    """Ensure all Standalone and Master skills in .agents/skills/ declaring user-invocable: true maintain 1:1 parity with catalog.yaml."""
    assert CATALOG_PATH.exists(), f"catalog.yaml not found at {CATALOG_PATH}"
    catalog_data = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8")) or {}
    registered_skills = {
        s["name"]: s
        for s in catalog_data.get("skills", [])
        if isinstance(s, dict) and "name" in s
    }

    skill_files = sorted(SKILLS_DIR.glob("**/SKILL.md"))
    assert len(skill_files) > 0, "No skill files found to test"

    errors: list[str] = []
    invocable_count = 0

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
            errors.append(f"{sf.relative_to(HUB_ROOT)}: Failed to parse frontmatter: {e}")
            continue

        name = fm.get("name") or sf.parent.name
        user_invocable = fm.get("user-invocable", False)
        if isinstance(user_invocable, str):
            user_invocable = user_invocable.lower() in ("true", "1", "yes")
        command = fm.get("command")

        if user_invocable:
            invocable_count += 1
            if not command:
                errors.append(
                    f"Skill '{name}' has 'user-invocable: true' but is missing 'command: /{name}'"
                )
            elif name not in registered_skills:
                errors.append(
                    f"Skill '{name}' declares user-invocable command '{command}' but is missing from catalog.yaml"
                )
            else:
                cat_entry = registered_skills[name]
                cat_cmd = cat_entry.get("command")
                if cat_cmd != command:
                    errors.append(
                        f"Command mismatch for '{name}': frontmatter '{command}' != catalog '{cat_cmd}'"
                    )

    assert invocable_count >= 20, (
        f"Expected at least 20 user-invocable skills, found {invocable_count}"
    )
    assert not errors, (
        f"Found {len(errors)} standalone skills catalog parity error(s):\n"
        + "\n".join(errors)
    )


def test_skill_validator_link_validation_unit(tmp_path: Path) -> None:
    """Verify validate_markdown_links flags broken links and ignores external or valid links."""
    from ccba_harness.skill_validator import SkillValidator

    validator = SkillValidator(tmp_path)
    target_file = tmp_path / "valid_target.md"
    target_file.write_text("# Target\n", encoding="utf-8")

    doc = tmp_path / "doc.md"
    doc.write_text(
        "# Doc\n"
        "[Valid Link](valid_target.md)\n"
        "[Broken Link](missing_target.md)\n"
        "[External Link](https://example.com/docs)\n"
        "[Anchor Link](#heading)\n"
        "[Placeholder Link](<path-to-target>.md)\n",
        encoding="utf-8",
    )

    issues = validator.validate_markdown_links(doc)
    assert len(issues) == 1
    assert "missing_target.md" in str(issues[0])


def test_skill_validator_slash_command_audit_unit(tmp_path: Path) -> None:
    """Verify audit_slash_commands detects unregistered commands and suppresses false positives."""
    from ccba_harness.skill_validator import SkillValidator

    validator = SkillValidator(tmp_path)
    registered = {"/ccba-ask", "/platform-loader"}

    doc = tmp_path / "doc.md"
    doc.write_text(
        "# Doc\n"
        "Run `/ccba-ask` for inquiry.\n"
        "Run `/boost` for host deep reasoning.\n"
        "Run `/skill-repair` for host repair.\n"
        "Do not run `/fake-unregistered-cmd`.\n"
        "HTML tag: </div>\n"
        "Path: look in /src or /tmp\n"
        "Vietnamese word pair: thuật ngữ/khái niệm\n"
        "Placeholder: `/<cmd>` or `/<name>`\n",
        encoding="utf-8",
    )

    issues = validator.audit_slash_commands(doc, registered_commands=registered)
    assert len(issues) == 1
    assert "/fake-unregistered-cmd" in str(issues[0])


def test_skill_validator_audit_skill_directory_unit(tmp_path: Path) -> None:
    """Verify audit_skill_directory scans all markdown files in directory."""
    from ccba_harness.skill_validator import SkillValidator

    validator = SkillValidator(tmp_path)
    sub = tmp_path / "references"
    sub.mkdir(parents=True)
    ref = sub / "ref.md"
    ref.write_text("[Broken](nonexistent.md)\n", encoding="utf-8")

    issues = validator.audit_skill_directory(tmp_path)
    assert any("nonexistent.md" in str(i) for i in issues)
