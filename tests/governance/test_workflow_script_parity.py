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
    "scripts/spoke_bootstrap.py",
}


def get_target_documents() -> list[Path]:
    """Collect all active skill definitions, reference documents, and workflow markdown files."""
    skills = sorted(SKILLS_DIR.rglob("*.md"))
    workflows = sorted(WORKFLOWS_DIR.glob("*.md")) if WORKFLOWS_DIR.exists() else []
    return skills + workflows


def test_all_skills_and_workflows_exist_and_are_readable() -> None:
    """Verify skills and workflows directories are populated and valid."""
    target_files = get_target_documents()
    assert len(target_files) >= 65, f"Expected >= 65 skills/workflows, found {len(target_files)}"
    for tf in target_files:
        assert tf.stat().st_size > 50, f"Target file '{tf}' is unexpectedly small or empty"


def test_hub_script_references_exist_on_disk() -> None:
    """Verify every script referenced with [hub_path] or at Hub root exists in Hub repo or skill."""
    hub_script_pattern = re.compile(
        r"(?:\[hub_path\][\\/]|python\s+)((?:scripts|\.agents[\\/]skills[\\/][a-zA-Z0-9_\-]+[\\/]scripts)[\\/][a-zA-Z0-9_\-\\\/\.]+\.py)"
    )

    target_files = get_target_documents()
    errors: list[str] = []

    for tf in target_files:
        content = tf.read_text(encoding="utf-8")
        for match in hub_script_pattern.findall(content):
            clean_rel = match.replace("\\", "/")
            # If it's a known spoke-level script run inside a spoke workspace, allow it
            if clean_rel in SPOKE_SPECIFIC_SCRIPTS:
                continue

            actual_hub_file = HUB_ROOT / clean_rel
            actual_local_file = tf.parent / clean_rel
            if not actual_hub_file.exists() and not actual_local_file.exists():
                errors.append(
                    f"File '{tf.relative_to(HUB_ROOT)}' references non-existent script: {clean_rel}"
                )

    assert not errors, "Detected broken script references in skills/workflows:\n" + "\n".join(
        errors
    )


def test_python_module_invocations_match_packages() -> None:
    """Verify python -m <package> in skills/workflows references real packages in packages/."""
    module_pattern = re.compile(r"python\s+-m\s+([a-zA-Z0-9_]+)")
    target_files = get_target_documents()

    # Discover registered package module names
    registered_modules = {
        "pytest",
        "ruff",
        "mypy",
        "venv",
        "pip",
        "unittest",
        "notebooklm",
        "markitdown",
    }
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
    for tf in target_files:
        content = tf.read_text(encoding="utf-8")
        for mod in module_pattern.findall(content):
            if mod not in registered_modules:
                errors.append(
                    f"File '{tf.relative_to(HUB_ROOT)}' invokes unregistered module: python -m {mod}"
                )

    assert not errors, "Detected invalid python -m module calls:\n" + "\n".join(errors)


def test_workflow_and_skill_relative_links_resolve() -> None:
    """Verify relative file links inside skills and workflow markdown files exist."""
    link_pattern = re.compile(r"\[.*?\]\(([^\)]+)\)")
    target_files = get_target_documents()

    errors: list[str] = []
    for tf in target_files:
        content = tf.read_text(encoding="utf-8")
        for target in link_pattern.findall(content):
            # Ignore URL schemes, anchors, or variable/wildcard placeholders
            if (
                target.startswith("http://")
                or target.startswith("https://")
                or target.startswith("#")
                or target.startswith("conversation:")
                or target.startswith("mailto:")
                or target.startswith("file://")
                or "[" in target
                or "<" in target
                or ">" in target
                or "{" in target
                or "..." in target
                or "*" in target
            ):
                continue
            # Strip anchors from file target
            clean_target = target.split("#")[0].strip()
            if not clean_target:
                continue

            resolved_path = (tf.parent / clean_target).resolve()
            if not resolved_path.exists():
                errors.append(
                    f"File '{tf.relative_to(HUB_ROOT)}' contains broken relative link: {target} -> {resolved_path}"
                )

    assert not errors, "Detected broken relative links in skills/workflows:\n" + "\n".join(errors)


def test_inline_script_and_reference_paths_exist() -> None:
    """Verify inline and backtick script and document references in skills resolve on disk."""
    script_pattern = re.compile(
        r"(?:python\s+|[\s\"\'\`])((?:[a-zA-Z0-9_\-\.\/]+)?(?:scripts|references)[\\/][a-zA-Z0-9_\-\\\/\.]+\.(?:py|sh|md|yaml|json|js))"
    )
    target_files = get_target_documents()
    errors: list[str] = []

    for tf in target_files:
        content = tf.read_text(encoding="utf-8")
        for match in script_pattern.findall(content):
            clean_rel = match.strip("`'\"").replace("\\", "/")
            if clean_rel.startswith(("http://", "https://", "<", "{", "$")):
                continue
            if any(c in clean_rel for c in ("<", ">", "{", "}", "*", "...")):
                continue
            if clean_rel in SPOKE_SPECIFIC_SCRIPTS:
                continue

            actual_local = (tf.parent / clean_rel).resolve()
            actual_hub = (HUB_ROOT / clean_rel).resolve()
            if not actual_local.exists() and not actual_hub.exists():
                errors.append(
                    f"File '{tf.relative_to(HUB_ROOT)}' references missing script/reference: {clean_rel}"
                )

    assert not errors, "Detected broken inline script/reference paths:\n" + "\n".join(errors)


def test_no_legacy_hardcoded_paths_in_skills() -> None:
    """Verify skills contain zero legacy Claude Desktop or pre-monorepo paths (ADR-0056)."""
    banned_patterns = [
        ("~/.claude/", "Legacy ~/.claude path"),
        ("/mnt/skills", "Legacy /mnt/skills path"),
        ("ooxml/scripts/", "Legacy ooxml/scripts path (use python -m ccba_ooxml)"),
        ("hitl-loop.template.sh", "Ghost HITL script reference"),
        ("scripts/notebooklm_cli.py", "Ghost notebooklm_cli.py reference"),
        (".claude/skills/design-system/", "Ghost design-system path"),
    ]
    target_files = get_target_documents()
    errors: list[str] = []

    for tf in target_files:
        content = tf.read_text(encoding="utf-8")
        for pattern, label in banned_patterns:
            if pattern in content:
                errors.append(f"File '{tf.relative_to(HUB_ROOT)}' contains {label}: '{pattern}'")

    assert not errors, "Detected legacy/ghost path patterns in skills:\n" + "\n".join(errors)
