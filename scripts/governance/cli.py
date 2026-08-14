"""cli.py - CLI Handlers and Terminal Formatter for Governance Audits.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .coordinator import DocumentAuditor


def run_docs_validation_cli(
    auditor: DocumentAuditor, args_list: list[str] | None = None
) -> int:
    """CLI entry point for document validation (validate_docs.py)."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass
        if hasattr(sys.stderr, "reconfigure"):
            try:
                sys.stderr.reconfigure(encoding="utf-8")
            except Exception:
                pass

    parser = argparse.ArgumentParser(description="Validate documentation accuracy.")
    parser.add_argument(
        "docs_dir",
        nargs="?",
        default="docs",
        help="Directory containing markdown files (default: docs)",
    )
    parser.add_argument(
        "--src",
        default="scripts,packages",
        help="Comma-separated directories to search for code definitions",
    )
    parser.add_argument("--root", default=".", help="Project workspace root directory")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically convert absolute workspace links to relative links",
    )
    parser.add_argument(
        "--changed", action="store_true", help="Only validate markdown files changed in git"
    )

    args = parser.parse_args(args_list)

    auditor.project_root = Path(args.root).resolve()
    docs_dir = Path(args.docs_dir)
    if not docs_dir.is_absolute():
        docs_dir = auditor.project_root / docs_dir

    src_paths = [Path(p.strip()) for p in args.src.split(",")]
    resolved_src_paths = []
    for p in src_paths:
        if not p.is_absolute():
            resolved_src_paths.append(auditor.project_root / p)
        else:
            resolved_src_paths.append(p)
    resolved_src_paths.append(auditor.project_root)

    if not docs_dir.exists():
        print(f"\x1b[31mError:\x1b[0m Docs directory '{docs_dir}' does not exist.")
        return 1

    exclude_dirs = {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "claudekit-engineer",
        "claudekit-marketing",
        ".pytest_cache",
        "extracted_docs",
        "scratch",
        ".system_generated",
        "CDE",
    }
    md_files = []

    if docs_dir.is_file():
        if docs_dir.suffix == ".md" and not docs_dir.name.endswith("_compiled.md"):
            md_files.append(docs_dir)
    else:
        for p in docs_dir.rglob("*.md"):
            if p.is_file():
                if p.name.endswith("_compiled.md"):
                    continue
                if any(ex in p.parts for ex in exclude_dirs):
                    continue
                if ".agents" in p.parts:
                    idx = p.parts.index(".agents")
                    if len(p.parts) > idx + 1:
                        subfolder = p.parts[idx + 1]
                        if subfolder not in {"skills", "workflows"}:
                            continue
                md_files.append(p)

    for root_file in [
        "README.md",
        "PLATFORM.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CONTEXT.md",
    ]:
        root_path = auditor.project_root / root_file
        if root_path.exists() and root_path not in md_files:
            md_files.append(root_path)

    if not md_files:
        print("No markdown files found to validate.")
        return 0

    env_vars = auditor.load_env_example()
    modified_files = auditor.get_modified_files()

    if args.changed:
        md_files = [f for f in md_files if f.resolve() in modified_files]

    registry = auditor.load_legal_registry()
    registry_map = auditor.build_markdown_to_doc_map(registry)

    print(f"Scanned {len(md_files)} markdown file(s).")
    print(
        f"Searching code declarations in: {', '.join(str(p.relative_to(auditor.project_root)) for p in resolved_src_paths if p.exists())}"
    )
    print("-" * 60)

    total_issues = 0
    broken_links_count = 0
    hard_errors_count = 0
    bundle_roots = set()

    for filepath in md_files:
        relative_path = (
            filepath.relative_to(auditor.project_root)
            if filepath.is_relative_to(auditor.project_root)
            else filepath
        )
        issues = auditor.validate_markdown_file(
            filepath,
            resolved_src_paths,
            env_vars,
            fix=args.fix,
            registry_map=registry_map,
        )

        parts = filepath.resolve().parts
        if "legal_docs" in parts:
            idx = parts.index("legal_docs")
            if idx + 1 < len(parts):
                bundle_roots.add(Path(*parts[: idx + 2]))

        file_has_issues = any(issues.values())
        if file_has_issues:
            print(f"\n\x1b[4mFile: {relative_path}\x1b[0m")
            is_modified = filepath.resolve() in modified_files
            if not modified_files:
                if os.getenv("GITHUB_ACTIONS") == "true":
                    is_modified = False
                else:
                    is_modified = True

            is_hard_error = is_modified or ("legal_docs" in docs_dir.parts)

            for line, field, err in issues.get("okf_frontmatter", []):
                if is_hard_error:
                    print(
                        f"  [L{line}] \x1b[31mOKF Frontmatter Error:\x1b[0m field `{field}` - {err}"
                    )
                    total_issues += 1
                    hard_errors_count += 1
                else:
                    print(
                        f"  [L{line}] \x1b[33mOKF Frontmatter Warning:\x1b[0m field `{field}` - {err}"
                    )
                    total_issues += 1

            for line, symbol, err in issues.get("code_refs", []):
                print(f"  [L{line}] \x1b[33mCode Ref Warning:\x1b[0m `{symbol}` - {err}")
                total_issues += 1

            for line, link, err in issues.get("okf_links", []):
                if is_hard_error:
                    print(f"  [L{line}] \x1b[31mOKF Link Error:\x1b[0m ({link}) - {err}")
                    total_issues += 1
                    hard_errors_count += 1
                else:
                    print(f"  [L{line}] \x1b[33mOKF Link Warning:\x1b[0m ({link}) - {err}")
                    total_issues += 1

            for line, link, err in sorted(issues.get("links", [])):
                if "[AUTO-FIXED]" in err:
                    print(f"  [L{line}] \x1b[32mLink Fixed:\x1b[0m ({link}) - {err}")
                elif "[WARNING]" in err:
                    print(f"  [L{line}] \x1b[33mLink Warning:\x1b[0m ({link}) - {err}")
                    total_issues += 1
                else:
                    if is_hard_error:
                        print(f"  [L{line}] \x1b[31mBroken Link Error:\x1b[0m ({link}) - {err}")
                        total_issues += 1
                        broken_links_count += 1
                    else:
                        print(
                            f"  [L{line}] \x1b[33mLink Warning (Old File):\x1b[0m ({link}) - [SOFT-WARN] {err}"
                        )
                        total_issues += 1

            for line, link, err in issues.get("okf_conflicts", []):
                if is_hard_error:
                    print(f"  [L{line}] \x1b[31mOKF Conflict Error:\x1b[0m ({link}) - {err}")
                    total_issues += 1
                    hard_errors_count += 1
                else:
                    print(f"  [L{line}] \x1b[33mOKF Conflict Warning:\x1b[0m ({link}) - {err}")
                    total_issues += 1

            for line, var, err in issues.get("env_vars", []):
                print(f"  [L{line}] \x1b[33mEnv Var Warning:\x1b[0m `{var}` - {err}")
                total_issues += 1

    orphan_issues_count = 0
    for root in sorted(bundle_roots):
        orphans = auditor.scan_orphan_files(root)
        if orphans:
            print(f"\n\x1b[4mBundle: {root.relative_to(auditor.project_root)}\x1b[0m")
            for o in sorted(orphans):
                rel_o = o.relative_to(auditor.project_root)
                bundle_has_mod = any(f.is_relative_to(root) for f in modified_files)
                is_hard = bundle_has_mod or ("legal_docs" in docs_dir.parts)

                if is_hard:
                    print(
                        f"  \x1b[31mOrphan File Error:\x1b[0m {rel_o} is not referenced by any other markdown file in the bundle."
                    )
                    total_issues += 1
                    orphan_issues_count += 1
                else:
                    print(
                        f"  \x1b[33mOrphan File Warning:\x1b[0m {rel_o} is not referenced by any other markdown file in the bundle."
                    )
                    total_issues += 1

    arch_drift_issues = auditor.check_architecture_drift()
    if arch_drift_issues:
        print("\n\x1b[4mArchitecture Drift Check\x1b[0m")
        for err in arch_drift_issues:
            print(f"  \x1b[31mDrift Error:\x1b[0m {err}")
            total_issues += 1
            hard_errors_count += 1

    print("-" * 60)
    if total_issues > 0:
        print(f"Completed with {total_issues} issue(s) detected.")
        if broken_links_count > 0 or hard_errors_count > 0 or orphan_issues_count > 0:
            print(
                "\x1b[31m[ERROR] Detected hard errors/broken links. Blocking commit/build.\x1b[0m"
            )
            return 1
        else:
            print(
                "\x1b[33m[WARN] Warnings/Old file broken links detected. Committing/building is allowed.\x1b[0m"
            )
            return 0
    else:
        print(
            "\x1b[32mDocumentation validation completed successfully! No issues detected.\x1b[0m"
        )
        return 0


def run_skills_validation_cli(
    auditor: DocumentAuditor, args_list: list[str] | None = None
) -> int:
    """CLI entry point for skill validation (validate_skills.py)."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass
        if hasattr(sys.stderr, "reconfigure"):
            try:
                sys.stderr.reconfigure(encoding="utf-8")
            except Exception:
                pass

    parser = argparse.ArgumentParser(description="Validate CCBA Agent Skills.")
    parser.add_argument(
        "skills_dir",
        nargs="?",
        default=".agents/skills",
        help="Directory containing skills (default: .agents/skills)",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Validate a specific SKILL.md file instead of the whole directory",
    )
    args = parser.parse_args(args_list)

    if args.file:
        target_path = Path(args.file)
        if not target_path.is_absolute():
            target_path = auditor.project_root / target_path
        skills_files = [target_path] if target_path.exists() else []
    else:
        search_path = Path(args.skills_dir)
        if not search_path.is_absolute():
            search_path = auditor.project_root / search_path
        skills_files = list(search_path.rglob("SKILL.md")) if search_path.exists() else []

    if not skills_files:
        print("No SKILL.md files found for validation.")
        return 0

    total_errors = 0
    for skill_path in skills_files:
        issues = auditor.audit_skill(skill_path)
        if issues:
            rel_path = (
                skill_path.relative_to(auditor.project_root)
                if skill_path.is_relative_to(auditor.project_root)
                else skill_path
            )
            print(f"\n\x1b[31m[ERROR]\x1b[0m {rel_path}:")
            for issue_item in issues:
                print(f"  Line {issue_item.line_number}: {issue_item.message}")
                total_errors += 1

    if total_errors > 0:
        print(f"\nValidation failed with {total_errors} error(s).")
        return 1

    print(f"\x1b[32mSuccessfully validated {len(skills_files)} SKILL.md file(s).\x1b[0m")
    return 0
