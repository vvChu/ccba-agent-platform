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
import re
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

        command = fm.get("command")
        if command:
            entry["command"] = str(command).strip()

        package_path = fm.get("package_path")
        if package_path:
            entry["package_path"] = str(package_path).replace("\\", "/")

        tier = fm.get("tier")
        if tier:
            entry["tier"] = str(tier).strip()

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


def compile_seams(hub_root: Path = HUB_ROOT) -> list[dict[str, Any]]:
    """Scan all packages/*/AGENTS.md and compile public deep seams list."""
    pkgs_dir = hub_root / "packages"
    if not pkgs_dir.exists():
        return []

    compiled: list[dict[str, Any]] = []

    for pkg_dir in sorted(pkgs_dir.iterdir(), key=lambda p: p.name):
        if not pkg_dir.is_dir() or pkg_dir.name.startswith("."):
            continue

        agents_md = pkg_dir / "AGENTS.md"
        if not agents_md.exists():
            continue

        text = agents_md.read_text(encoding="utf-8")
        lines = text.strip().splitlines()

        # Extract description (text between title and first bullet point)
        desc = ""
        for line in lines[1:]:
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith("-"):
                break
            desc += " " + line_str if desc else line_str

        # Extract Public Deep Seams
        seams_m = re.search(
            r"-\s+\*\*Public Deep Seams\*\*:(.*?)(?=\n-\s+\*\*|\Z)", text, re.DOTALL
        )
        public_seams_raw = seams_m.group(1).strip() if seams_m else ""
        seam_lines = [
            line.strip().lstrip("-* ").strip()
            for line in public_seams_raw.splitlines()
            if line.strip()
        ]

        # Extract Contracts
        contracts_m = re.search(r"-\s+\*\*Contracts\*\*:(.*?)(?=\n-\s+\*\*|\Z)", text, re.DOTALL)
        contracts = contracts_m.group(1).strip().replace("\n", " ") if contracts_m else ""

        # Extract Scoped Tests
        tests_m = re.search(r"-\s+\*\*Scoped Tests\*\*:(.*?)(?=\n-\s+\*\*|\Z)", text, re.DOTALL)
        scoped_tests = tests_m.group(1).strip().replace("\n", " ") if tests_m else ""

        rel_path = str(pkg_dir.relative_to(hub_root)).replace("\\", "/")

        entry: dict[str, Any] = {
            "package": pkg_dir.name,
            "path": rel_path,
            "description": desc,
            "public_seams": seam_lines,
            "contracts": contracts,
            "tests": scoped_tests,
        }
        compiled.append(entry)

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
    seams = compile_seams(hub_root)

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
        "seams": seams,
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
        diffs.append(f"Missing skills in catalog.yaml: {sorted(missing_skills)}")

    extra_skills = set(existing_skills.keys()) - set(compiled_skills.keys())
    if extra_skills:
        diffs.append(f"Orphaned skills in catalog.yaml: {sorted(extra_skills)}")

    # Deep diff on shared skills (description, triggers, bundle, command, etc.)
    common_skills = sorted(set(compiled_skills.keys()) & set(existing_skills.keys()))
    for s_name in common_skills:
        cur = existing_skills[s_name]
        comp = compiled_skills[s_name]
        all_fields = sorted(set(cur.keys()) | set(comp.keys()))
        for field in all_fields:
            val_cur = cur.get(field)
            val_comp = comp.get(field)
            if val_cur != val_comp:
                diffs.append(
                    f"Skill '{s_name}' metadata drift in field '{field}':\n"
                    f"  catalog.yaml: {val_cur!r}\n"
                    f"  frontmatter:  {val_comp!r}"
                )

    # Compare workflows
    existing_wfs = {w.get("name"): w for w in existing_data.get("workflows", [])}
    compiled_wfs = {w.get("name"): w for w in compiled_data.get("workflows", [])}

    missing_wfs = set(compiled_wfs.keys()) - set(existing_wfs.keys())
    if missing_wfs:
        diffs.append(f"Missing workflows in catalog.yaml: {sorted(missing_wfs)}")

    extra_wfs = set(existing_wfs.keys()) - set(compiled_wfs.keys())
    if extra_wfs:
        diffs.append(f"Orphaned workflows in catalog.yaml: {sorted(extra_wfs)}")

    # Deep diff on shared workflows
    common_wfs = sorted(set(compiled_wfs.keys()) & set(existing_wfs.keys()))
    for w_name in common_wfs:
        cur = existing_wfs[w_name]
        comp = compiled_wfs[w_name]
        all_fields = sorted(set(cur.keys()) | set(comp.keys()))
        for field in all_fields:
            val_cur = cur.get(field)
            val_comp = comp.get(field)
            if val_cur != val_comp:
                diffs.append(
                    f"Workflow '{w_name}' metadata drift in field '{field}':\n"
                    f"  catalog.yaml: {val_cur!r}\n"
                    f"  frontmatter:  {val_comp!r}"
                )

    # Compare seams
    existing_seams = {s.get("package"): s for s in existing_data.get("seams", [])}
    compiled_seams = {s.get("package"): s for s in compiled_data.get("seams", [])}

    missing_seams = set(compiled_seams.keys()) - set(existing_seams.keys())
    if missing_seams:
        diffs.append(f"Missing seams in catalog.yaml: {sorted(missing_seams)}")

    extra_seams = set(existing_seams.keys()) - set(compiled_seams.keys())
    if extra_seams:
        diffs.append(f"Orphaned seams in catalog.yaml: {sorted(extra_seams)}")

    common_seams = sorted(set(compiled_seams.keys()) & set(existing_seams.keys()))
    for pkg_name in common_seams:
        cur = existing_seams[pkg_name]
        comp = compiled_seams[pkg_name]
        all_fields = sorted(set(cur.keys()) | set(comp.keys()))
        for field in all_fields:
            val_cur = cur.get(field)
            val_comp = comp.get(field)
            if val_cur != val_comp:
                diffs.append(
                    f"Package seam '{pkg_name}' property '{field}' mismatch:\n"
                    f"  catalog.yaml: {val_cur!r}\n"
                    f"  compiled:     {val_comp!r}"
                )

    # Deep diff on base configuration (from catalog_base.yaml)
    for base_field in ["hub_path", "hub_repo", "notebook_ids", "bundles", "rules", "knowledge"]:
        cur_val = existing_data.get(base_field)
        comp_val = compiled_data.get(base_field)
        if cur_val != comp_val:
            diffs.append(
                f"Base config drift in field '{base_field}':\n"
                f"  catalog.yaml:      {cur_val!r}\n"
                f"  catalog_base.yaml: {comp_val!r}"
            )

    if diffs:
        return False, "\n".join(diffs)
    return True, "Catalog is 100% in sync"


def query_catalog(hub_root: Path = HUB_ROOT, query_term: str = "") -> int:
    """Fast CLI search across Public Deep Seams and Skills in catalog."""
    term = query_term.lower().strip()
    if not term:
        print("[ERROR] Please provide a non-empty search keyword.", file=sys.stderr)
        return 1

    catalog = compile_catalog_dict(hub_root)

    matching_seams = []
    for s in catalog.get("seams", []):
        pkg = str(s.get("package", ""))
        desc = str(s.get("description", ""))
        seam_strs = " ".join(s.get("public_seams", []))
        contracts = str(s.get("contracts", ""))
        if (
            term in pkg.lower()
            or term in desc.lower()
            or term in seam_strs.lower()
            or term in contracts.lower()
        ):
            matching_seams.append(s)

    matching_skills = []
    for sk in catalog.get("skills", []):
        name = str(sk.get("name", ""))
        desc = str(sk.get("description", ""))
        triggers = " ".join(sk.get("triggers", []))
        cmd = str(sk.get("command", ""))
        if (
            term in name.lower()
            or term in desc.lower()
            or term in triggers.lower()
            or term in cmd.lower()
        ):
            matching_skills.append(sk)

    print("=" * 80)
    print(f"🔍 CCBA Platform Catalog Query: '{query_term}'")
    print(f"   Matches: {len(matching_seams)} Deep Seam(s), {len(matching_skills)} Skill(s)")
    print("=" * 80)

    if matching_seams:
        print("\n📦 [Tier 1: Monorepo Package Deep Seams]")
        for s in matching_seams:
            print(f"• Package:     {s['package']} ({s['path']})")
            print(f"  Description: {s['description']}")
            print("  Public Seams:")
            for seam in s.get("public_seams", []):
                print(f"    - {seam}")
            if s.get("contracts"):
                print(f"  Contracts:   {s['contracts']}")
            if s.get("tests"):
                print(f"  Tests:       {s['tests']}")
            print("-" * 60)

    if matching_skills:
        print("\n⚡ [Tier 2/3: Agent Skills & Workflows]")
        for sk in matching_skills:
            cmd = sk.get("command") or f"/{sk['name']}"
            print(f"• Skill:       {sk['name']} ({cmd})")
            print(f"  Bundle:      {sk.get('bundle', '_core')}")
            print(f"  Description: {sk.get('description', '')}")
            triggers = ", ".join(sk.get("triggers", []))
            if triggers:
                print(f"  Triggers:    {triggers}")
            print("-" * 60)

    if not matching_seams and not matching_skills:
        print(f"\n[INFO] No seams or skills found matching '{query_term}'.")
        print("Tip: Check spelling or try a broader keyword (e.g. 'pccc', 'pdf', 'docx', 'eval').")

    print("=" * 80)
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="CCBA Catalog Manifest Compiler (ADR 0047)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if catalog.yaml is in sync with frontmatters (returns non-zero if out of sync).",
    )
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        default=None,
        help="Search Public Deep Seams and Skills in CCBA Catalog.",
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

    if args.query:
        return query_catalog(HUB_ROOT, args.query)

    if args.check:
        in_sync, msg = check_catalog_in_sync(HUB_ROOT)
        if in_sync:
            print(
                "[OK] [Catalog Compiler] catalog.yaml is 100% in-sync with frontmatters and packages."
            )
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
    seams_count = len(compile_seams(HUB_ROOT))
    print(
        f"[OK] [Catalog Compiler] Compiled catalog.yaml successfully ({skills_count} skills, {wfs_count} workflows, {seams_count} package seams)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
