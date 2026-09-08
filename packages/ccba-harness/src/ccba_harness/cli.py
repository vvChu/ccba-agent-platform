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
from typing import Any

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
    parser.add_argument(
        "--enforce-gpi",
        action="store_true",
        help="Enforce GPI metrics block in SKILL.md frontmatter per RES-2026-ARCH-001",
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
            print(
                "ERROR: No SKILL.md or workflow files found matching specified targets.",
                file=sys.stderr,
            )
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
            issues = validator.audit_skill(
                target_path, check_shallow=True, enforce_gpi=args.enforce_gpi
            )
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


def _print_gpi_result(result: Any, as_json: bool = False) -> None:
    """Helper to format and print GPI evaluation results."""
    if as_json:
        import json

        data = {
            "name": result.name,
            "tier": result.tier.value,
            "passed_gate_0": result.passed_gate_0,
            "passed_gate_1": result.passed_gate_1,
            "gpi_score": result.gpi_score,
            "allow_standalone_skill": result.allow_standalone_skill,
            "target_location": result.target_location,
            "rationale": result.rationale,
            "breakdown": result.breakdown,
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    print("=" * 60)
    print("CCBA TWO-STAGE GRANULARITY DECISION EVALUATION")
    print(f"Capability Name : {result.name}")
    print(f"Assigned Tier   : {result.tier.value}")
    if result.gpi_score is not None:
        print(f"GPI Score       : {result.gpi_score:.2f} (Threshold: 12.0)")
    print(f"Standalone Skill: {'ALLOWED' if result.allow_standalone_skill else 'NOT PERMITTED'}")
    print(f"Target Location : {result.target_location}")
    print(f"Rationale       : {result.rationale}")
    if result.breakdown:
        print("Score Breakdown :")
        for k, v in result.breakdown.items():
            print(f"  - {k}: {v}")
    print("=" * 60)


def run_evaluate_gpi_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for GPI evaluation (`ccba-harness evaluate-gpi`)."""
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
        prog="ccba-harness evaluate-gpi",
        description="Evaluate Two-Stage Decision Framework & Granularity Placement Index (RES-2026-ARCH-001).",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Evaluate an existing SKILL.md file directly",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="proposed-capability",
        help="Name of proposed skill/capability",
    )
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Gate 0: Task is 100% solvable by deterministic algorithms (regex, AST, math, file I/O)",
    )
    parser.add_argument(
        "--orchestrated",
        action="store_true",
        help="Gate 1: Task coordinates multiple agents/checkpoints/HITL approval",
    )
    parser.add_argument("--s", type=float, default=None, help="Reasoning Steps (1-5)")
    parser.add_argument("--k", type=float, default=None, help="Interface / Schema Complexity (1-5)")
    parser.add_argument("--a", type=float, default=None, help="Autonomous Model Invocation (1-5)")
    parser.add_argument("--p", type=float, default=None, help="Parent Domain Coupling (1-5)")
    parser.add_argument("--parent", type=str, default=None, help="Parent/Master skill name")
    parser.add_argument("--json", action="store_true", help="Output result in JSON format")

    args = parser.parse_args(args_list)

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"ERROR: Skill file does not exist: {args.file}", file=sys.stderr)
            return 1
        validator = SkillValidator()
        try:
            from .gpi import GPIMetrics

            override_metrics: GPIMetrics | None = None
            if None not in (args.s, args.k, args.a, args.p):
                override_metrics = GPIMetrics(
                    s=float(args.s),
                    k=float(args.k),
                    a=float(args.a),
                    p=float(args.p),
                )
            result = validator.evaluate_skill_file(
                file_path,
                override_metrics=override_metrics,
                override_parent=args.parent,
            )
        except Exception as err:
            print(f"ERROR: Failed to evaluate skill file: {err}", file=sys.stderr)
            return 1

        _print_gpi_result(result, as_json=args.json)
        return 0

    from .gpi import (
        DecisionRequest,
        GPIMetrics,
        evaluate_two_stage_decision,
    )

    gpi_metrics: GPIMetrics | None = None
    if not args.deterministic and not args.orchestrated:
        if None in (args.s, args.k, args.a, args.p):
            print(
                "ERROR: When not deterministic or orchestrated, all 4 GPI metrics (--s, --k, --a, --p) are required.",
                file=sys.stderr,
            )
            return 1
        try:
            gpi_metrics = GPIMetrics(s=args.s, k=args.k, a=args.a, p=args.p)
        except (TypeError, ValueError) as err:
            print(f"ERROR: Invalid GPI metric values: {err}", file=sys.stderr)
            return 1

    try:
        request = DecisionRequest(
            name=args.name,
            is_deterministic=args.deterministic,
            is_orchestrated=args.orchestrated,
            gpi_metrics=gpi_metrics,
            parent_skill=args.parent,
        )
        result = evaluate_two_stage_decision(request)
    except Exception as err:
        print(f"ERROR: Evaluation failed: {err}", file=sys.stderr)
        return 1

    _print_gpi_result(result, as_json=args.json)
    return 0


def run_eval_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for skill evaluation benchmarks (`ccba-harness eval`)."""
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
        prog="ccba-harness eval",
        description="Run evaluation benchmarks for skills (CCBA Evals Framework).",
    )
    parser.add_argument(
        "--skill",
        type=str,
        default=None,
        help="Name or path of skill to evaluate (e.g. copywriting or .agents/skills/ccba-copywriting)",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=3,
        help="Number of evaluation trials (default: 3)",
    )
    parser.add_argument(
        "--auto-tune",
        action="store_true",
        help="Enable automatic prompt optimization via SkillOpt loop",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Path to test cases directory or JSON file",
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Project workspace root (default: auto-detected)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result in JSON format",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=85.0,
        help="Passing score threshold percentage (default: 85.0)",
    )

    args = parser.parse_args(args_list)

    if args.root:
        root_path = Path(args.root).resolve()
    else:
        cur = Path.cwd().resolve()
        root_path = cur
        for p in [cur, *cur.parents]:
            if (p / ".agents").exists() or (p / "pyproject.toml").exists():
                root_path = p
                break

    from .evals.runner import run_eval_pipeline

    dataset_target = args.dataset
    if args.dataset:
        d_path = Path(args.dataset)
        if not d_path.is_absolute():
            d_path = root_path / d_path
        if not d_path.exists():
            print(f"ERROR: Dataset path does not exist: {args.dataset}", file=sys.stderr)
            return 1
        dataset_target = str(d_path)

    try:
        report = run_eval_pipeline(
            skill=args.skill,
            trials=args.trials,
            auto_tune=args.auto_tune,
            dataset=dataset_target,
            project_root=root_path,
            pass_threshold=args.threshold,
        )
    except Exception as err:
        print(f"ERROR: Evaluation pipeline failed: {err}", file=sys.stderr)
        return 1

    if report.total_items == 0:
        err_msg = (
            f"No evaluation test cases found for target skill: {args.skill}"
            if args.skill
            else (
                f"No evaluation test cases found in dataset: {args.dataset}"
                if args.dataset
                else "No evaluation test cases found."
            )
        )
        print(f"ERROR: {err_msg}", file=sys.stderr)
        if args.json:
            import json

            data = {
                "skill": args.skill,
                "trials": args.trials,
                "auto_tune": args.auto_tune,
                "total_items": 0,
                "passed_items": 0,
                "failed_items": 0,
                "overall_score": 0.0,
                "pass_rate": 0.0,
                "passed": False,
                "summary_by_scorer": {},
                "metadata": report.metadata,
                "error": err_msg,
            }
            print(json.dumps(data, indent=2, ensure_ascii=False))
        return 1

    passed_all = (
        report.total_items > 0 and report.pass_rate >= args.threshold and report.failed_items == 0
    )

    if args.json:
        import json

        data = {
            "skill": args.skill,
            "trials": args.trials,
            "auto_tune": args.auto_tune,
            "total_items": report.total_items,
            "passed_items": report.passed_items,
            "failed_items": report.failed_items,
            "overall_score": report.overall_score,
            "pass_rate": report.pass_rate,
            "passed": passed_all,
            "summary_by_scorer": report.summary_by_scorer,
            "metadata": report.metadata,
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print("CCBA SKILL EVALUATION REPORT")
        print(f"Target Skill     : {args.skill or 'ALL'}")
        print(f"Evaluation Trials: {args.trials}")
        print(f"Auto-Tune Mode   : {'ENABLED' if args.auto_tune else 'DISABLED'}")
        print(f"Total Cases      : {report.total_items}")
        print(f"Passed Cases     : {report.passed_items}")
        print(f"Failed Cases     : {report.failed_items}")
        print(f"Overall Score    : {report.overall_score:.2f}% (Threshold: {args.threshold:.2f}%)")
        print(f"Pass Rate        : {report.pass_rate:.2f}%")
        print(f"Status           : {'PASS' if passed_all else 'FAIL'}")
        if report.summary_by_scorer:
            print("Scorer Breakdown :")
            for sc_name, sc_val in report.summary_by_scorer.items():
                print(f"  - {sc_name}: {sc_val:.2f}%")
        print("=" * 60)

    if not passed_all:
        return 1
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
    val_parser.add_argument(
        "--enforce-gpi",
        action="store_true",
        help="Enforce GPI metrics block in SKILL.md frontmatter per RES-2026-ARCH-001",
    )

    # Subcommand: evaluate-gpi
    gpi_parser = subparsers.add_parser(
        "evaluate-gpi",
        help="Evaluate Two-Stage Decision Framework & Granularity Placement Index (GPI).",
    )
    gpi_parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Evaluate an existing SKILL.md file directly",
    )
    gpi_parser.add_argument(
        "--name",
        type=str,
        default="proposed-capability",
        help="Name of proposed skill/capability",
    )
    gpi_parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Gate 0: Task is 100% solvable by deterministic algorithms",
    )
    gpi_parser.add_argument(
        "--orchestrated",
        action="store_true",
        help="Gate 1: Task coordinates multiple agents/checkpoints/HITL",
    )
    gpi_parser.add_argument("--s", type=float, default=None, help="Reasoning Steps (1-5)")
    gpi_parser.add_argument("--k", type=float, default=None, help="Interface Complexity (1-5)")
    gpi_parser.add_argument("--a", type=float, default=None, help="Autonomous Invocation (1-5)")
    gpi_parser.add_argument("--p", type=float, default=None, help="Parent Coupling (1-5)")
    gpi_parser.add_argument("--parent", type=str, default=None, help="Parent/Master skill name")
    gpi_parser.add_argument("--json", action="store_true", help="Output result in JSON format")

    # Subcommand: eval
    eval_parser = subparsers.add_parser(
        "eval",
        help="Run evaluation benchmarks for skills (CCBA Evals Framework).",
    )
    eval_parser.add_argument(
        "--skill",
        type=str,
        default=None,
        help="Name or path of skill to evaluate",
    )
    eval_parser.add_argument(
        "--trials",
        type=int,
        default=3,
        help="Number of evaluation trials (default: 3)",
    )
    eval_parser.add_argument(
        "--auto-tune",
        action="store_true",
        help="Enable automatic prompt optimization via SkillOpt loop",
    )
    eval_parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Path to test cases directory or JSON file",
    )
    eval_parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Project workspace root",
    )
    eval_parser.add_argument(
        "--json",
        action="store_true",
        help="Output result in JSON format",
    )
    eval_parser.add_argument(
        "--threshold",
        type=float,
        default=85.0,
        help="Passing score threshold percentage (default: 85.0)",
    )

    if not argv:
        parser.print_help()
        return 0

    # If first argument is validate-skill, parse and run
    if argv[0] == "validate-skill":
        return run_skill_validation_cli(argv[1:])

    # If first argument is evaluate-gpi, parse and run
    if argv[0] == "evaluate-gpi":
        return run_evaluate_gpi_cli(argv[1:])

    # If first argument is eval, parse and run
    if argv[0] == "eval":
        return run_eval_cli(argv[1:])

    # Fallback to general parsing
    parsed = parser.parse_args(argv)
    if parsed.subcommand == "validate-skill":
        return run_skill_validation_cli(argv[1:])
    if parsed.subcommand == "evaluate-gpi":
        return run_evaluate_gpi_cli(argv[1:])
    if parsed.subcommand == "eval":
        return run_eval_cli(argv[1:])

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
