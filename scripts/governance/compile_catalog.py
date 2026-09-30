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
import ast
import hashlib
import json
import os
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

# Monorepo packages and their root package names
PACKAGE_MAP: dict[str, str] = {
    "ccba-ai": "ccba_ai",
    "ccba-diagram": "ccba_diagram",
    "ccba-harness": "ccba_harness",
    "ccba-legal-intel": "ccba_legal",
    "ccba-maskara": "ccba_maskara",
    "ccba-notebooklm": "ccba_notebooklm",
    "ccba-ooxml": "ccba_ooxml",
    "ccba-pdf-prep": "ccba_pdf_prep",
    "ccba-qc-core": "ccba_qc_core",
    "mdconverter": "mdconverter",
}


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


def _extract_module_exported_symbols(file_path: Path) -> set[str] | None:
    """Extract exported symbols from a python file using AST.

    If __all__ is explicitly defined (as a list/tuple of strings), returns that set.
    Otherwise, returns all top-level public definitions (functions, classes, assignments)
    and imported names that do not start with '_'.
    """
    if not file_path.is_file():
        return None
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except Exception:
        return None

    # First pass: check for explicit __all__
    exported: set[str] = set()
    has_all = False
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        has_all = True
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                exported.add(elt.value)
        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "__all__":
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    has_all = True
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            exported.add(elt.value)

    if has_all:
        return exported

    # Fallback: top-level public names
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                exported.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    exported.add(target.id)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                if not name.startswith("_"):
                    exported.add(name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                if not name.startswith("_"):
                    exported.add(name)
    return exported


def validate_seam_exports(hub_root: Path = HUB_ROOT) -> list[str]:
    """Validate all public deep seams declared in packages/*/AGENTS.md.

    Uses static AST analysis to ensure:
    1. The imported module belongs to the declaring package (no spoofing).
    2. The imported module or package exists on disk.
    3. Every declared symbol exists in __all__ or top-level definitions of that module.

    Returns:
        List of validation error messages. Empty list if 100% valid.
    """
    errors: list[str] = []
    pkgs_dir = hub_root / "packages"
    if not pkgs_dir.exists():
        return errors

    for pkg_dir in sorted(pkgs_dir.iterdir(), key=lambda p: p.name):
        if not pkg_dir.is_dir() or pkg_dir.name.startswith("."):
            continue

        agents_md = pkg_dir / "AGENTS.md"
        if not agents_md.exists():
            continue

        text = agents_md.read_text(encoding="utf-8")
        seams_m = re.search(
            r"-\s+\*\*Public Deep Seams\*\*:(.*?)(?=\n-\s+\*\*|\Z)", text, re.DOTALL
        )
        if not seams_m:
            continue

        raw_seams_block = seams_m.group(1)
        expected_root_pkg = PACKAGE_MAP.get(pkg_dir.name)
        if not expected_root_pkg:
            errors.append(
                f"Package '{pkg_dir.name}' is not registered in PACKAGE_MAP in compile_catalog.py."
            )
            continue

        # Find all `from <mod> import <symbols>` patterns
        matches = re.findall(r"from\s+([a-zA-Z0-9_\.]+)\s+import\s+([^`\n\(\)]+)", raw_seams_block)
        for mod_name, symbols_str in matches:
            mod_parts = mod_name.split(".")
            root_mod = mod_parts[0]

            # Invariant 1: Package spoofing guard
            if root_mod != expected_root_pkg:
                errors.append(
                    f"Package '{pkg_dir.name}' declares seam for foreign module '{mod_name}'. "
                    f"Expected root package '{expected_root_pkg}'."
                )
                continue

            # Invariant 2: Locate module file on disk
            root_src = pkg_dir / "src" / expected_root_pkg
            target_file: Path | None = None
            if len(mod_parts) == 1:
                init_file = root_src / "__init__.py"
                if init_file.is_file():
                    target_file = init_file
            else:
                sub_path = root_src.joinpath(*mod_parts[1:])
                if sub_path.is_dir() and (sub_path / "__init__.py").is_file():
                    target_file = sub_path / "__init__.py"
                elif sub_path.with_suffix(".py").is_file():
                    target_file = sub_path.with_suffix(".py")

            if target_file is None:
                errors.append(
                    f"Package '{pkg_dir.name}' declares seam module '{mod_name}' which does not exist under '{root_src}'."
                )
                continue

            # Invariant 3: Validate declared symbols against exported symbols
            exported_symbols = _extract_module_exported_symbols(target_file)
            if exported_symbols is None:
                errors.append(
                    f"Package '{pkg_dir.name}' seam module '{mod_name}' ({target_file}) could not be parsed."
                )
                continue

            # Extract individual symbol names (immunized against trailing punctuation)
            symbols = [
                s.strip().rstrip(".,;") for s in symbols_str.split(",") if s.strip().rstrip(".,;")
            ]
            for sym in symbols:
                if sym not in exported_symbols:
                    try:
                        rel_target = str(target_file.relative_to(hub_root))
                    except ValueError:
                        rel_target = str(target_file)
                    errors.append(
                        f"Package '{pkg_dir.name}' declares seam symbol '{sym}' from '{mod_name}', "
                        f"but '{sym}' is not exported by '{rel_target}'."
                    )

    return errors


def validate_seam_contracts(hub_root: Path = HUB_ROOT) -> list[str]:
    """Validate seam cards in seam-contracts.yaml via static AST inspection.

    Ensures:
    1. seam_id is unique, non-empty, and does not contain traversal characters (.. / \\).
    2. Package cards export the declared symbol from the declared package.
    3. Skill cards point to existing SKILL.md files and valid commands.
    4. forbidden_substitute_imports contains valid AST module names.
    """
    errors: list[str] = []
    contracts_file = hub_root / "seam-contracts.yaml"
    if not contracts_file.is_file():
        return errors

    try:
        data = yaml.safe_load(contracts_file.read_text(encoding="utf-8")) or {}
    except Exception as e:
        return [f"Failed to parse seam-contracts.yaml: {e}"]

    cards = data.get("cards", [])
    if not cards:
        return ["seam-contracts.yaml contains no cards."]

    seen_ids: set[str] = set()
    pkgs_dir = hub_root / "packages"
    rev_package_map = {v: k for k, v in PACKAGE_MAP.items()}

    for card in cards:
        seam_id = str(card.get("seam_id", "")).strip()
        if not seam_id:
            errors.append("Seam card missing required 'seam_id'.")
            continue
        if ".." in seam_id or "/" in seam_id or "\\" in seam_id:
            errors.append(
                f"Seam ID '{seam_id}' contains invalid path characters ('..', '/', '\\')."
            )
        if seam_id in seen_ids:
            errors.append(f"Duplicate seam_id '{seam_id}' in seam-contracts.yaml.")
        seen_ids.add(seam_id)

        kind = card.get("kind")
        if kind not in ("package", "skill", "workflow"):
            errors.append(
                f"Card '{seam_id}' has invalid kind '{kind}'. Must be package, skill, or workflow."
            )

        cap = card.get("capability")
        if not isinstance(cap, dict) or "in" not in cap or "out" not in cap:
            errors.append(
                f"Card '{seam_id}' missing valid capability definition with 'in' and 'out' lists."
            )

        binding = card.get("binding")
        if not isinstance(binding, dict) or "mode" not in binding:
            errors.append(
                f"Card '{seam_id}' missing required 'binding' definition with 'mode' "
                "(local_import, remote_mcp, skill)."
            )
        else:
            mode = str(binding.get("mode", "")).strip()
            if mode not in ("local_import", "remote_mcp", "skill"):
                errors.append(
                    f"Card '{seam_id}' has invalid binding.mode '{mode}'. "
                    "Must be local_import, remote_mcp, or skill."
                )
            if kind == "package" and mode not in ("local_import", "remote_mcp"):
                errors.append(
                    f"Package card '{seam_id}' must use binding.mode 'local_import' or 'remote_mcp' (got '{mode}')."
                )
            elif kind == "skill" and mode != "skill":
                errors.append(
                    f"Skill card '{seam_id}' must use binding.mode 'skill' (got '{mode}')."
                )
            if mode == "remote_mcp":
                endpoint_env = str(binding.get("endpoint_env", "")).strip()
                if not endpoint_env:
                    errors.append(
                        f"Remote MCP card '{seam_id}' missing required 'endpoint_env' variable name."
                    )

        if kind == "package":
            imp_path = str(card.get("import_path", "")).strip()
            if not imp_path or ":" not in imp_path:
                errors.append(
                    f"Package card '{seam_id}' missing or invalid 'import_path' (expected 'module:Symbol')."
                )
                continue
            mod_name, sym_name = imp_path.split(":", 1)
            root_mod = mod_name.split(".")[0]
            pkg_folder_name = rev_package_map.get(root_mod)
            if not pkg_folder_name:
                errors.append(
                    f"Package card '{seam_id}' references unknown root package '{root_mod}'."
                )
                continue

            pkg_dir = pkgs_dir / pkg_folder_name
            target_file = None
            if "." not in mod_name:
                candidates = [
                    pkg_dir / "src" / root_mod / "__init__.py",
                    pkg_dir / root_mod / "__init__.py",
                    pkg_dir / "src" / f"{root_mod}.py",
                ]
            else:
                sub_path = "/".join(mod_name.split(".")[1:])
                candidates = [
                    pkg_dir / "src" / root_mod / f"{sub_path}.py",
                    pkg_dir / root_mod / f"{sub_path}.py",
                    pkg_dir / "src" / root_mod / sub_path / "__init__.py",
                    pkg_dir / root_mod / sub_path / "__init__.py",
                ]

            for c in candidates:
                if c.is_file():
                    target_file = c
                    break

            if not target_file:
                errors.append(f"Package card '{seam_id}' module '{mod_name}' not found on disk.")
                continue

            exported = _extract_module_exported_symbols(target_file)
            if exported is not None and sym_name not in exported:
                errors.append(
                    f"Package card '{seam_id}' declares symbol '{sym_name}' from '{mod_name}', "
                    f"but '{sym_name}' is not exported by '{target_file.name}'."
                )

        elif kind == "skill":
            skill_path = str(card.get("skill_path", "")).strip()
            if not skill_path or not (hub_root / skill_path).is_file():
                errors.append(
                    f"Skill card '{seam_id}' skill_path '{skill_path}' does not exist on disk."
                )
            cmd = str(card.get("command", "")).strip()
            if not cmd.startswith("/"):
                errors.append(f"Skill card '{seam_id}' command '{cmd}' must start with '/'.")

    return errors


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

    # Validate static seam exports (ADR 0047 / Issue #372)
    seam_errors = validate_seam_exports(hub_root)
    if seam_errors:
        diffs.extend([f"Static Seam Export Error: {err}" for err in seam_errors])

    # Validate seam contracts (ADR-0061 / Issue #439)
    contract_errors = validate_seam_contracts(hub_root)
    if contract_errors:
        diffs.extend([f"Seam Contract Error: {err}" for err in contract_errors])

    if diffs:
        return False, "\n".join(diffs)
    return True, "Catalog is 100% in sync"


def load_seam_contracts(hub_root: Path = HUB_ROOT) -> tuple[dict[str, Any], str]:
    """Loads seam-contracts.yaml and returns (parsed_dict, sha256_hash).

    The SHA-256 hash is computed over the raw bytes of the file on disk.
    If the file does not exist, returns empty dict and empty hash.
    """
    contracts_file = hub_root / "seam-contracts.yaml"
    if not contracts_file.is_file():
        return {}, ""
    try:
        raw_bytes = contracts_file.read_bytes()
        sha256 = hashlib.sha256(raw_bytes).hexdigest()
        data = yaml.safe_load(raw_bytes.decode("utf-8")) or {}
        return data, sha256
    except Exception as e:
        print(f"[ERROR] Failed to read seam-contracts.yaml: {e}", file=sys.stderr)
        return {}, ""


def match_seam_cards(
    cards: list[dict[str, Any]],
    in_types: list[str] | None = None,
    out_types: list[str] | None = None,
    hardware: str | None = None,
) -> list[dict[str, Any]]:
    """Filters seam cards according to Platform-Aware KISS v2.0 semantics.

    - Every requested in_type must be in card's capability.in (card can accept additional inputs).
    - Every requested out_type must be in card's capability.out.
    - If hardware is specified and not 'any', card.hardware must contain hardware or 'any'.
    """
    matches: list[dict[str, Any]] = []
    norm_in = [x.lower().strip() for x in in_types] if in_types else None
    norm_out = [x.lower().strip() for x in out_types] if out_types else None
    norm_hw = hardware.lower().strip() if hardware else None

    for card in cards:
        cap = card.get("capability", {})
        card_in = [str(x).lower().strip() for x in cap.get("in", [])]
        card_out = [str(x).lower().strip() for x in cap.get("out", [])]
        card_hw = [str(x).lower().strip() for x in card.get("hardware", [])]

        if norm_in:
            if not all(item in card_in for item in norm_in):
                continue

        if norm_out:
            if not all(item in card_out for item in norm_out):
                continue

        if norm_hw and norm_hw != "any":
            if norm_hw not in card_hw and "any" not in card_hw:
                continue

        matches.append(card)

    matches.sort(key=lambda c: str(c.get("seam_id", "")))
    return matches


def query_seam_contracts(
    hub_root: Path = HUB_ROOT,
    in_types: list[str] | None = None,
    out_types: list[str] | None = None,
    hardware: str | None = None,
    keyword: str | None = None,
    as_json: bool = False,
) -> tuple[int, dict[str, Any]]:
    """Queries seam capability contracts and catalog.

    Exit codes (ADR-0061 & ADR-0060):
    - 0: Match found (capability card match or keyword hint found).
    - 2: NO_MATCH (contract capability card does not exist, or keyword not found).
    - 1: Syntax error / missing inputs / corrupt snapshot.
    - 3: BLOCKED (all matching cards are remote_mcp and unreachable/offline).
    """
    from scripts.spoke.catalog_probe import CatalogProbeRunner
    from scripts.spoke.catalog_snapshot_client import (
        CatalogSnapshotMissing,
        CorruptSnapshotError,
        resolve_catalog_context,
    )

    try:
        contracts_data, index_sha256, catalog_data, source_type = resolve_catalog_context(
            project_root=hub_root,
            hub_root_override=hub_root if (hub_root / "seam-contracts.yaml").is_file() else None,
        )
    except CorruptSnapshotError as e:
        msg = f"Catalog snapshot is corrupt: {e}"
        payload = {"status": "corrupt", "message": msg, "exit_code": 1}
        if as_json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"❌ [CORRUPT] {msg}", file=sys.stderr)
        return 1, payload
    except CatalogSnapshotMissing as e:
        msg = str(e)
        payload = {"status": "ERROR", "message": msg, "exit_code": 1}
        if as_json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"❌ [ERROR] {msg}", file=sys.stderr)
        return 1, payload
    except Exception:
        contracts_data, index_sha256 = load_seam_contracts(hub_root)

    probe_runner = CatalogProbeRunner(hub_root)
    freshness = probe_runner.evaluate_freshness(current_seam_sha=index_sha256)
    cards = contracts_data.get("cards", [])

    has_contract_query = bool(in_types or out_types or hardware)
    has_keyword_query = bool(keyword and keyword.strip())

    if not has_contract_query and not has_keyword_query:
        msg = "Please provide either contract capability query (--in/--out/--hardware) or a search keyword."
        if as_json:
            print(
                json.dumps(
                    {
                        "status": "ERROR",
                        "message": msg,
                        "index_sha256": index_sha256,
                        "freshness": freshness,
                    },
                    indent=2,
                )
            )
        else:
            print(f"[ERROR] {msg}", file=sys.stderr)
        return 1, {"status": "ERROR", "message": msg, "freshness": freshness}

    if has_contract_query:
        matches = match_seam_cards(cards, in_types=in_types, out_types=out_types, hardware=hardware)
        if matches:
            all_remote_mcp = all(
                isinstance(c.get("binding"), dict)
                and c.get("binding", {}).get("mode") == "remote_mcp"
                for c in matches
            )
            if all_remote_mcp:
                all_blocked = True
                blocked_seam_id = matches[0].get("seam_id")
                for c in matches:
                    b = c.get("binding", {})
                    env_var = b.get("endpoint_env")
                    url = os.environ.get(env_var, "") if env_var else b.get("endpoint_url", "")
                    if url and probe_runner.check_mcp_health(url):
                        all_blocked = False
                        break
                if all_blocked:
                    payload = {
                        "status": "BLOCKED",
                        "index_sha256": index_sha256,
                        "freshness": freshness,
                        "count": len(matches),
                        "cards": matches,
                        "invoke": "blocked",
                        "reason": "health_timeout",
                        "seam_id": blocked_seam_id,
                    }
                    if as_json:
                        print(json.dumps(payload, indent=2, ensure_ascii=False))
                    else:
                        print(
                            f"❌ BLOCKED: Remote MCP unreachable (reason: health_timeout) for seam '{blocked_seam_id}' [index_sha256: {index_sha256}]",
                            file=sys.stderr,
                        )
                    return 3, payload

            payload = {
                "status": "MATCH",
                "index_sha256": index_sha256,
                "freshness": freshness,
                "count": len(matches),
                "cards": matches,
            }
            if as_json:
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print("=" * 80)
                print("🎯 CCBA Platform Seam Contracts Query: MATCH")
                print(f"   Index SHA-256: {index_sha256}")
                print(f"   Freshness:     {freshness}")
                print(f"   Matched Cards: {len(matches)}")
                print("=" * 80)
                for c in matches:
                    print(f"• Seam ID:     {c.get('seam_id')} (Kind: {c.get('kind')})")
                    if c.get("binding"):
                        print(f"  Binding:     {c.get('binding')}")
                    if c.get("import_path"):
                        print(f"  Import Path: {c.get('import_path')}")
                    if c.get("command"):
                        print(f"  Command:     {c.get('command')} ({c.get('skill_path')})")
                    cap = c.get("capability", {})
                    print(f"  Capability:  in={cap.get('in', [])} -> out={cap.get('out', [])}")
                    print(f"  Hardware:    {c.get('hardware', [])}")
                    print(f"  Owner:       {c.get('owner', 'unknown')}")
                    if c.get("forbidden_substitute_imports"):
                        print(f"  Forbidden:   {c.get('forbidden_substitute_imports')}")
                    print("-" * 60)
            return 0, payload
        else:
            payload = {
                "status": "NO_MATCH",
                "index_sha256": index_sha256,
                "freshness": freshness,
                "count": 0,
                "cards": [],
            }
            if as_json:
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print(f"NO_MATCH [index_sha256: {index_sha256}, freshness: {freshness}]")
            return 2, payload

    # Keyword only search (KEYWORD_HINT mode)
    assert keyword is not None
    term = keyword.lower().strip()
    matching_cards = []
    for c in cards:
        seam_id = str(c.get("seam_id", "")).lower()
        owner = str(c.get("owner", "")).lower()
        cap_in = " ".join(str(x).lower() for x in c.get("capability", {}).get("in", []))
        cap_out = " ".join(str(x).lower() for x in c.get("capability", {}).get("out", []))
        imp = str(c.get("import_path", "")).lower()
        cmd = str(c.get("command", "")).lower()
        if (
            term in seam_id
            or term in owner
            or term in cap_in
            or term in cap_out
            or term in imp
            or term in cmd
        ):
            matching_cards.append(c)

    # Also search catalog for hints
    catalog = compile_catalog_dict(hub_root)
    matching_seams = []
    for s in catalog.get("seams", []):
        pkg = str(s.get("package", "")).lower()
        desc = str(s.get("description", "")).lower()
        seam_strs = " ".join(s.get("public_seams", [])).lower()
        if term in pkg or term in desc or term in seam_strs:
            matching_seams.append(s)

    matching_skills = []
    for sk in catalog.get("skills", []):
        name = str(sk.get("name", "")).lower()
        desc = str(sk.get("description", "")).lower()
        triggers = " ".join(sk.get("triggers", [])).lower()
        cmd = str(sk.get("command", "")).lower()
        if term in name or term in desc or term in triggers or term in cmd:
            matching_skills.append(sk)

    total_hits = len(matching_cards) + len(matching_seams) + len(matching_skills)
    if total_hits > 0:
        payload = {
            "status": "KEYWORD_HINT",
            "index_sha256": index_sha256,
            "freshness": freshness,
            "keyword": keyword,
            "cards": matching_cards,
            "catalog_seams": matching_seams,
            "catalog_skills": matching_skills,
        }
        if as_json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("=" * 80)
            print(
                f"🔍 CCBA Platform Catalog Query: '{keyword}' (KEYWORD_HINT - NOT A CONTRACT RECEIPT)"
            )
            print(f"   Index SHA-256: {index_sha256}")
            print(f"   Freshness:     {freshness}")
            print(
                f"   Matched: {len(matching_cards)} Card(s), {len(matching_seams)} Deep Seam(s), {len(matching_skills)} Skill(s)"
            )
            print("=" * 80)
            if matching_cards:
                print("\n📋 [Capability Contract Cards]")
                for c in matching_cards:
                    print(f"• Seam ID:     {c.get('seam_id')} ({c.get('kind')})")
                    if c.get("import_path"):
                        print(f"  Import Path: {c.get('import_path')}")
                    if c.get("command"):
                        print(f"  Command:     {c.get('command')} ({c.get('skill_path')})")
                    print("-" * 60)
            if matching_seams:
                print("\n📦 [Tier 1: Monorepo Package Deep Seams]")
                for s in matching_seams:
                    print(f"• Package:     {s['package']} ({s['path']})")
                    for seam in s.get("public_seams", []):
                        print(f"    - {seam}")
                    print("-" * 60)
            if matching_skills:
                print("\n⚡ [Tier 2/3: Agent Skills]")
                for sk in matching_skills:
                    c_cmd = sk.get("command") or f"/{sk['name']}"
                    print(f"• Skill:       {sk['name']} ({c_cmd})")
                    print(f"  Description: {sk.get('description', '')}")
                    print("-" * 60)
        return 0, payload
    else:
        payload = {
            "status": "NO_MATCH",
            "index_sha256": index_sha256,
            "freshness": freshness,
            "keyword": keyword,
            "cards": [],
        }
        if as_json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"NO_MATCH [index_sha256: {index_sha256}, freshness: {freshness}]")
        return 2, payload


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
        "--in",
        dest="in_types",
        nargs="+",
        default=None,
        help="Input capability requirements (e.g. --in pdf docx)",
    )
    parser.add_argument(
        "--out",
        dest="out_types",
        nargs="+",
        default=None,
        help="Output capability requirements (e.g. --out markdown)",
    )
    parser.add_argument(
        "--hardware",
        type=str,
        default=None,
        help="Hardware constraint (e.g. any, dgx_spark, cuda)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON capability receipt or status",
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

    if args.in_types or args.out_types or args.hardware:
        exit_code, _ = query_seam_contracts(
            hub_root=HUB_ROOT,
            in_types=args.in_types,
            out_types=args.out_types,
            hardware=args.hardware,
            keyword=args.query,
            as_json=args.json,
        )
        return exit_code

    if args.query is not None:
        if args.json:
            exit_code, _ = query_seam_contracts(
                hub_root=HUB_ROOT,
                keyword=args.query,
                as_json=True,
            )
            return exit_code
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

    # Static seam symbol validation (ADR 0047 / Issue #372)
    seam_errors = validate_seam_exports(HUB_ROOT)
    if seam_errors:
        print("[ERROR] [Catalog Compiler] Static Seam Validation FAILED:", file=sys.stderr)
        for err in seam_errors:
            print(f"  ❌ {err}", file=sys.stderr)
        print("\nAborting catalog compilation due to phantom seam symbols.", file=sys.stderr)
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
