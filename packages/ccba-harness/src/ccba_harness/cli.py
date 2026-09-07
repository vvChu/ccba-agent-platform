"""cli.py - Standalone Command-Line Interface for ccba-harness.

Provides offline & air-gapped governance tools for Spoke and Hub environments:
  ccba-harness validate-skill [paths...] [--file FILE] [--root ROOT] [--strict]

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .skill_validator import SkillAuditIssue, SkillValidator


def run_skill_validation_cli(
    args_list: Sequence[str] | None = None,
    validator: SkillValidator | None = None,
) -> int:
    """CLI entry point for standalone skill validation (`ccba-harness validate-skill`)."""
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

    parser = argparse.ArgumentParser(
        prog="ccba-harness validate-skill",
        description="Validate CCBA Agent Skills & Workflows offline/standalone.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=[],
        help="Directories or SKILL.md files to validate (default: .agents/skills or current dir)",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Validate a specific SKILL.md or workflow file",
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Project workspace root (default: auto-detected)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings (e.g., shallow skills < 35 lines) as hard errors",
    )
    args = parser.parse_args(args_list)

    if validator is None:
        root_path = Path(args.root).resolve() if args.root else Path.cwd()
        validator = SkillValidator(project_root=root_path)
    else:
        if args.root:
            validator.project_root = Path(args.root).resolve()

    skills_files: list[Path] = []
    has_explicit_targets = False

    if args.file:
        has_explicit_targets = True
        target_path = Path(args.file)
        if not target_path.is_absolute():
            target_path = validator.project_root / target_path
        skills_files.append(target_path)

    if args.paths:
        has_explicit_targets = True
        for p_str in args.paths:
            p = Path(p_str)
            if not p.is_absolute():
                p = validator.project_root / p
            if not p.exists():
                skills_files.append(p)
                continue
            if p.is_file():
                if p.name == "SKILL.md" or p.suffix == ".md":
                    skills_files.append(p)
            elif p.is_dir():
                skills_files.extend(p.rglob("SKILL.md"))

    if not has_explicit_targets:
        default_dir = validator.project_root / ".agents" / "skills"
        if default_dir.exists():
            skills_files = list(default_dir.rglob("SKILL.md"))
        else:
            # Fallback to scanning current directory
            skills_files = list(validator.project_root.rglob("SKILL.md"))

    # De-duplicate while preserving order
    seen: set[Path] = set()
    unique_skills_files: list[Path] = []
    for sf in skills_files:
        try:
            sf_res = sf.resolve()
        except Exception:
            sf_res = sf
        if sf_res not in seen:
            seen.add(sf_res)
            unique_skills_files.append(sf)
    skills_files = unique_skills_files

    if not skills_files:
        if has_explicit_targets:
            print("ERROR: No SKILL.md or workflow files found matching specified targets.", file=sys.stderr)
            return 1
        print("No SKILL.md files found for validation.")
        return 0

    total_errors = 0
    total_warnings = 0

    for target_path in skills_files:
        is_workflow = (
            target_path.is_relative_to(validator.project_root / ".agents" / "workflows")
            if target_path.is_relative_to(validator.project_root)
            else "workflows" in target_path.parts
        )
        if is_workflow:
            issues = validator.audit_workflow(target_path)
            error_prefix = "[WORKFLOW ERROR]"
        else:
            issues = validator.audit_skill(target_path, check_shallow=True)
            error_prefix = "[SKILL ERROR]"

        if issues:
            rel_path = (
                target_path.relative_to(validator.project_root)
                if target_path.is_relative_to(validator.project_root)
                else target_path
            )

            warnings: list[SkillAuditIssue] = []
            errors: list[SkillAuditIssue] = []
            for issue_item in issues:
                if issue_item.category.endswith("_WARNING"):
                    warnings.append(issue_item)
                else:
                    errors.append(issue_item)

            if warnings:
                print(f"\n\x1b[33m[SKILL WARNING]\x1b[0m {rel_path}:")
                for w in warnings:
                    print(f"  Line {w.line_number}: {w.message}")
                    total_warnings += 1
                    if args.strict:
                        total_errors += 1

            if errors:
                print(f"\n\x1b[31m{error_prefix}\x1b[0m {rel_path}:")
                for e in errors:
                    print(f"  Line {e.line_number}: {e.message}")
                    total_errors += 1

    # Validate all Workflows in .agents/workflows if full directory scan
    workflow_files: list[Path] = []
    if not has_explicit_targets:
        wf_dir = validator.project_root / ".agents" / "workflows"
        if wf_dir.exists():
            workflow_files = list(wf_dir.glob("*.md"))
            for wf_path in workflow_files:
                wf_issues = validator.audit_workflow(wf_path)
                if wf_issues:
                    rel_wf = (
                        wf_path.relative_to(validator.project_root)
                        if wf_path.is_relative_to(validator.project_root)
                        else wf_path
                    )
                    print(f"\n\x1b[31m[WORKFLOW ERROR]\x1b[0m {rel_wf}:")
                    for w_issue in wf_issues:
                        print(f"  Line {w_issue.line_number}: {w_issue.message}")
                        total_errors += 1

    # Run Workspace Hard CI Gates
    skills_dir = validator.project_root / ".agents" / "skills"
    if skills_dir.exists() and not has_explicit_targets:
        gate_issues = validator.audit_workspace_gates(skills_dir)
        gate_errors = [g for g in gate_issues if not g.category.endswith("_WARNING")]
        gate_warnings = [g for g in gate_issues if g.category.endswith("_WARNING")]

        if gate_warnings:
            print("\n\x1b[33m[WORKSPACE WARNING]\x1b[0m Workspace-level Warnings:")
            for gw in gate_warnings:
                print(f"  [{gw.category}] {gw.message}")
                total_warnings += 1
                if args.strict:
                    total_errors += 1

        if gate_errors:
            print("\n\x1b[31m[HARD CI GATE ERROR]\x1b[0m Workspace-level Skill Violations:")
            for ge in gate_errors:
                print(f"  [{ge.category}] {ge.message}")
                total_errors += 1

    if total_errors > 0:
        warn_note = f" (and {total_warnings} warning(s))" if total_warnings else ""
        print(f"\nValidation failed with {total_errors} error(s){warn_note}.")
        return 1

    wf_msg = f" and {len(workflow_files)} workflow file(s)" if workflow_files else ""
    warn_msg = f" with {total_warnings} warning(s)" if total_warnings else ""
    print(
        f"\x1b[32mSuccessfully validated {len(skills_files)} SKILL.md file(s){wf_msg}{warn_msg} across all CI Gates.\x1b[0m"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entry point for ccba-harness."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="ccba-harness",
        description="CCBA Security, Evaluation & Governance Harness CLI.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # Subcommand: validate-skill
    val_parser = subparsers.add_parser(
        "validate-skill",
        help="Validate CCBA skills and workflows format and CI gates.",
    )
    val_parser.add_argument(
        "paths",
        nargs="*",
        default=[],
        help="Directories or SKILL.md files to validate",
    )
    val_parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Validate a specific SKILL.md or workflow file",
    )
    val_parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Project workspace root",
    )
    val_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings (e.g. shallow skills < 35 lines) as hard errors",
    )

    if not argv:
        parser.print_help()
        return 0

    # If first argument is validate-skill, parse and run
    if argv[0] == "validate-skill":
        return run_skill_validation_cli(argv[1:])

    # Fallback to general parsing
    parsed = parser.parse_args(argv)
    if parsed.subcommand == "validate-skill":
        return run_skill_validation_cli(argv[1:])

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
