"""test_workflow_script_parity.py - Automated Governance Test for Workflow & Codebase Parity.

Verifies that:
1. Every script path referenced in all .agents/workflows/*.md exists in the codebase (or is documented spoke script).
2. Every Hub-level script execution ([hub_path]/scripts/...) resolves to a valid file in Hub.
3. Every Python module CLI invocation (python -m <package>) references a valid registered package in packages/.
4. Every markdown file cross-link in workflows resolves to an existing file on disk.

Ensures zero doc-code drift across the entire CCBA Hub-and-Spoke platform.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.fast, pytest.mark.unit]

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOWS_DIR = HUB_ROOT / ".agents" / "workflows"
SKILLS_DIR = HUB_ROOT / ".agents" / "skills"
PACKAGES_DIR = HUB_ROOT / "packages"

# Recognized Spoke-specific scripts executed within Spoke context
SPOKE_SPECIFIC_SCRIPTS = {
    "scripts/validate_legal_spoke.py",
    "scripts/verify_docx_against_pdf.py",
    "scripts/sync_notebooklm_knowledge.py",
    "scripts/check_spoke_cleanliness.py",
    "scripts/check_hub_import_depth.py",
}


def test_all_workflows_exist_and_are_readable() -> None:
    """Verify workflows directory is populated and valid."""
    workflow_files = list(WORKFLOWS_DIR.glob("*.md"))
    assert len(workflow_files) >= 50, f"Expected >= 50 workflows, found {len(workflow_files)}"


def test_hub_script_references_exist_on_disk() -> None:
    """Verify every script referenced with [hub_path] or at Hub root exists in Hub repo."""
    hub_script_pattern = re.compile(
        r"(?:\[hub_path\][\\/]|python\s+)(scripts[\\/][a-zA-Z0-9_\-\\\/\.]+\.py)"
    )

    workflow_files = list(WORKFLOWS_DIR.glob("*.md"))
    errors: list[str] = []

    for wf in workflow_files:
        content = wf.read_text(encoding="utf-8")
        for match in hub_script_pattern.findall(content):
            clean_rel = match.replace("\\", "/")
            # If it's a known spoke-level script run inside a spoke workspace, allow it
            if clean_rel in SPOKE_SPECIFIC_SCRIPTS:
                continue

            actual_file = HUB_ROOT / clean_rel
            if not actual_file.exists():
                errors.append(
                    f"Workflow '{wf.name}' references non-existent script: {clean_rel}"
                )

    assert not errors, "Detected broken script references in workflows:\n" + "\n".join(errors)


def test_python_module_invocations_match_packages() -> None:
    """Verify python -m <package> in workflows references real packages in packages/."""
    module_pattern = re.compile(r"python\s+-m\s+([a-zA-Z0-9_]+)")
    workflow_files = list(WORKFLOWS_DIR.glob("*.md"))

    # Discover registered package module names
    registered_modules = {"pytest", "ruff", "venv", "pip", "unittest"}
    for pkg in PACKAGES_DIR.iterdir():
        if pkg.is_dir():
            src_dir = pkg / "src"
            if src_dir.exists():
                for sub in src_dir.iterdir():
                    if sub.is_dir() or sub.suffix == ".py":
                        registered_modules.add(sub.stem)
            else:
                registered_modules.add(pkg.name.replace("-", "_"))

    errors: list[str] = []
    for wf in workflow_files:
        content = wf.read_text(encoding="utf-8")
        for mod in module_pattern.findall(content):
            if mod not in registered_modules:
                errors.append(
                    f"Workflow '{wf.name}' invokes unregistered module: python -m {mod}"
                )

    assert not errors, "Detected invalid python -m module calls:\n" + "\n".join(errors)


def test_workflow_relative_links_resolve() -> None:
    """Verify relative file links inside workflow markdown files exist."""
    link_pattern = re.compile(r"\[.*?\]\(([^\)]+)\)")
    workflow_files = list(WORKFLOWS_DIR.glob("*.md"))

    errors: list[str] = []
    for wf in workflow_files:
        content = wf.read_text(encoding="utf-8")
        for target in link_pattern.findall(content):
            # Ignore URL schemes, anchors, or variable/wildcard placeholders
            if (
                target.startswith("http://")
                or target.startswith("https://")
                or target.startswith("#")
                or target.startswith("conversation:")
                or "[" in target
                or "<" in target
                or ">" in target
                or target.startswith("file://")
            ):
                continue
            # Strip anchors from file target
            clean_target = target.split("#")[0].strip()
            if not clean_target:
                continue

            resolved_path = (wf.parent / clean_target).resolve()
            if not resolved_path.exists():
                errors.append(
                    f"Workflow '{wf.name}' contains broken relative link: {target} -> {resolved_path}"
                )

    assert not errors, "Detected broken relative links in workflows:\n" + "\n".join(errors)
