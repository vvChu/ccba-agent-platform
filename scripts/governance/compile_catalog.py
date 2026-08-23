#!/usr/bin/env python3
"""compile_catalog.py - Catalog Manifest Compiler for CCBA Agent Platform (ADR 0047).

Compiles `.agents/skills/platform-loader/catalog.yaml` deterministically from:
1. Static high-level config in `catalog_base.yaml` (hub_path, bundles, rules, knowledge)
2. Single-Source-of-Truth YAML frontmatter in all `.agents/skills/**/SKILL.md`
3. Single-Source-of-Truth YAML frontmatter in all `.agents/workflows/*.md`

Supports `--check` for CI gate enforcement and `--write` (default) for regeneration.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
BASE_CATALOG_PATH = HUB_ROOT / ".agents" / "skills" / "platform-loader" / "catalog_base.yaml"
OUTPUT_CATALOG_PATH = HUB_ROOT / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
SKILLS_DIR = HUB_ROOT / ".agents" / "skills"
WORKFLOWS_DIR = HUB_ROOT / ".agents" / "workflows"


def extract_frontmatter(file_path: Path) -> dict[str, Any]:
    """Extract and parse YAML frontmatter from a markdown file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return {}
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}
        fm = yaml.safe_load(parts[1])
        return fm if isinstance(fm, dict) else {}
    except Exception as e:
        print(f"[Warning] Failed to parse frontmatter from {file_path}: {e}", file=sys.stderr)
        return {}


def compile_skills(hub_root: Path = HUB_ROOT) -> list[dict[str, Any]]:
    """Scan all SKILL.md files and build the skills list."""
    skills_dir = hub_root / ".agents" / "skills"
    skill_files = sorted(skills_dir.glob("**/SKILL.md"))

    compiled: list[dict[str, Any]] = []

    for sf in skill_files:
        fm = extract_frontmatter(sf)
        if not fm:
            continue

        name = str(fm.get("name") or sf.parent.name).strip()
        bundle = str(fm.get("bundle") or "_core").strip()
        description = str(fm.get("description") or "").strip()

        # Resolve triggers from triggers or keywords
        raw_triggers = fm.get("triggers") or fm.get("keywords") or []
        if isinstance(raw_triggers, str):
            raw_triggers = [raw_triggers]
        triggers = [str(t).strip() for t in raw_triggers if str(t).strip()]

        skill_path = str(sf.relative_to(hub_root)).replace("\\", "/")

        entry: dict[str, Any] = {
            "name": name,
            "bundle": bundle,
            "description": description,
            "triggers": triggers,
            "skill_path": skill_path,
        }

        package_path = fm.get("package_path")
        if package_path:
            entry["package_path"] = str(package_path).replace("\\", "/")

        compiled.append(entry)

    # Sort with platform-loader first, then alphabetically
    compiled.sort(key=lambda s: (0 if s["name"] == "platform-loader" else 1, s["name"]))
    return compiled


def compile_workflows(hub_root: Path = HUB_ROOT) -> list[dict[str, Any]]:
    """Scan all workflow markdown files and build the workflows list."""
    wf_dir = hub_root / ".agents" / "workflows"
    wf_files = sorted(wf_dir.glob("*.md"))

    compiled: list[dict[str, Any]] = []

    for wf in wf_files:
        fm = extract_frontmatter(wf)
        if not fm:
            continue

        name = str(fm.get("name") or wf.stem).strip()
        bundle = str(fm.get("bundle") or "_core").strip()
        command = str(fm.get("command") or f"/{wf.stem}").strip()
        description = str(fm.get("description") or "").strip()

        raw_triggers = fm.get("triggers") or fm.get("keywords") or []
        if isinstance(raw_triggers, str):
            raw_triggers = [raw_triggers]
        triggers = [str(t).strip() for t in raw_triggers if str(t).strip()]

        workflow_path = str(wf.relative_to(hub_root)).replace("\\", "/")

        entry: dict[str, Any] = {
            "name": name,
            "bundle": bundle,
            "command": command,
            "description": description,
            "triggers": triggers,
            "workflow_path": workflow_path,
        }
        compiled.append(entry)

    compiled.sort(key=lambda w: (0 if w["name"] == "init-ccba-spoke" else 1, w["name"]))
    return compiled


def compile_catalog_dict(hub_root: Path = HUB_ROOT) -> dict[str, Any]:
    """Compile the entire catalog dictionary."""
    base_file = hub_root / ".agents" / "skills" / "platform-loader" / "catalog_base.yaml"
    if base_file.exists():
        base_data = yaml.safe_load(base_file.read_text(encoding="utf-8")) or {}
    else:
        base_data = {}

    skills = compile_skills(hub_root)
    workflows = compile_workflows(hub_root)

    catalog: dict[str, Any] = {
        "hub_path": base_data.get("hub_path", "."),
        "hub_repo": base_data.get("hub_repo", "https://github.com/vvChu/ccba-agent-platform"),
        "notebook_ids": base_data.get(
            "notebook_ids",
            {
                "_core": "nb-mock-3",
                "_software": "nb-mock-software",
                "_qc": "nb-mock-qc",
                "_consulting": "nb-mock-consulting",
            },
        ),
        "bundles": base_data.get("bundles", {}),
        "skills": skills,
        "workflows": workflows,
        "rules": base_data.get("rules", []),
        "knowledge": base_data.get("knowledge", []),
    }
    return catalog


def generate_catalog_yaml(hub_root: Path = HUB_ROOT) -> str:
    """Generate cleanly formatted YAML string for catalog.yaml."""
    data = compile_catalog_dict(hub_root)
    yaml_str: str = str(
        yaml.safe_dump(
            data,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            indent=2,
        )
    )
    header = (
        "# =============================================================================\n"
        "# CCBA Agent Services Platform — Central Catalog Manifest (ADR 0047)\n"
        "# AUTO-COMPILED from SKILL.md / Workflow frontmatters + catalog_base.yaml\n"
        "# Regenerate via: python scripts/governance/compile_catalog.py\n"
        "# =============================================================================\n\n"
    )
    return header + yaml_str


def check_catalog_in_sync(hub_root: Path = HUB_ROOT) -> tuple[bool, str]:
    """Verify if catalog.yaml is 100% in-sync with current filesystem frontmatters."""
    catalog_path = hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    if not catalog_path.exists():
        return False, f"Target file does not exist: {catalog_path}"

    existing_content = catalog_path.read_text(encoding="utf-8")
    existing_data = yaml.safe_load(existing_content) or {}

    compiled_data = compile_catalog_dict(hub_root)

    # Compare skills
    existing_skills = {s.get("name"): s for s in existing_data.get("skills", [])}
    compiled_skills = {s.get("name"): s for s in compiled_data.get("skills", [])}

    diffs: list[str] = []

    missing_skills = set(compiled_skills.keys()) - set(existing_skills.keys())
    if missing_skills:
        diffs.append(f"Missing skills in catalog.yaml: {missing_skills}")

    extra_skills = set(existing_skills.keys()) - set(compiled_skills.keys())
    if extra_skills:
        diffs.append(f"Orphaned skills in catalog.yaml: {extra_skills}")

    # Compare workflows
    existing_wfs = {w.get("name"): w for w in existing_data.get("workflows", [])}
    compiled_wfs = {w.get("name"): w for w in compiled_data.get("workflows", [])}

    missing_wfs = set(compiled_wfs.keys()) - set(existing_wfs.keys())
    if missing_wfs:
        diffs.append(f"Missing workflows in catalog.yaml: {missing_wfs}")

    extra_wfs = set(existing_wfs.keys()) - set(compiled_wfs.keys())
    if extra_wfs:
        diffs.append(f"Orphaned workflows in catalog.yaml: {extra_wfs}")

    if diffs:
        return False, "\n".join(diffs)
    return True, "Catalog is 100% in sync"


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="CCBA Catalog Manifest Compiler (ADR 0047)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if catalog.yaml is in sync with frontmatters (returns non-zero if out of sync).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        default=True,
        help="Compile and write catalog.yaml to disk (default).",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print compiled YAML to stdout instead of writing to file.",
    )

    args = parser.parse_args(argv)

    if args.check:
        in_sync, msg = check_catalog_in_sync(HUB_ROOT)
        if in_sync:
            print("[OK] [Catalog Compiler] catalog.yaml is 100% in-sync with frontmatters.")
            return 0
        else:
            print(
                "[ERROR] [Catalog Compiler] catalog.yaml is OUT OF SYNC with frontmatters:",
                file=sys.stderr,
            )
            print(f"  {msg}", file=sys.stderr)
            print(
                "\n[INFO] Run 'python scripts/governance/compile_catalog.py' to regenerate catalog.yaml.",
                file=sys.stderr,
            )
            return 1

    compiled_yaml = generate_catalog_yaml(HUB_ROOT)

    if args.stdout:
        print(compiled_yaml)
        return 0

    OUTPUT_CATALOG_PATH.write_text(compiled_yaml, encoding="utf-8")
    skills_count = len(compile_skills(HUB_ROOT))
    wfs_count = len(compile_workflows(HUB_ROOT))
    print(
        f"[OK] [Catalog Compiler] Compiled catalog.yaml successfully ({skills_count} skills, {wfs_count} workflows)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
