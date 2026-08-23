"""Automated CI Gate: Global Skills & Navigation Integrity.

Ensures that global entry skills (such as ccba-platform/SKILL.md) do not contain
broken paths or stale references to deleted skills/workflows.
"""

import re
from pathlib import Path

import pytest

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
GLOBAL_SKILL_PATH = Path.home() / ".gemini" / "config" / "skills" / "ccba-platform" / "SKILL.md"


def test_global_ccba_platform_skill_has_no_dead_links() -> None:
    """Verify all [hub_path] and relative links in ccba-platform/SKILL.md exist on disk."""
    if not GLOBAL_SKILL_PATH.exists():
        pytest.skip(f"Global skill not found at {GLOBAL_SKILL_PATH}")

    content = GLOBAL_SKILL_PATH.read_text(encoding="utf-8")

    # Match markdown links: [text](file:///[hub_path]/path or [hub_path]/path)
    # Also match table rows with `[hub_path]/...`
    pattern = re.compile(r"\[hub_path\]/([^\s\)\`\|\"]+)")
    matches = pattern.findall(content)

    assert len(matches) > 0, "No [hub_path] references found in global skill"

    dead_links: list[str] = []
    for rel_path_str in matches:
        clean_rel = rel_path_str.strip().rstrip(")")
        target = HUB_ROOT / clean_rel
        if not target.exists():
            dead_links.append(f"[hub_path]/{clean_rel} -> {target} DOES NOT EXIST")

    assert not dead_links, (
        f"Found {len(dead_links)} dead link(s) in {GLOBAL_SKILL_PATH}:\n" + "\n".join(dead_links)
    )


def test_platform_loader_workflows_exist() -> None:
    """Verify that every workflow registered in catalog.yaml exists in .agents/workflows/."""
    catalog_path = HUB_ROOT / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    import yaml
    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    workflows = data.get("workflows", [])

    missing: list[str] = []
    for wf in workflows:
        name = wf.get("name", "")
        wf_path_rel = wf.get("workflow_path", f".agents/workflows/{name}.md")
        wf_file = HUB_ROOT / wf_path_rel
        if not wf_file.exists():
            missing.append(f"Workflow '{name}' ({wf_path_rel}) not found on disk")

    assert not missing, "\n".join(missing)
