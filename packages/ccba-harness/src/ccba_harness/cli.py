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
                override_deterministic=True if args.deterministic else None,
                override_orchestrated=True if args.orchestrated else None,
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


def _parse_commands_from_file(file_path: Path) -> list[str]:
    """Parse list of commands from a text or JSON file."""
    import json

    content = file_path.read_text(encoding="utf-8").strip()
    commands: list[str] = []
    if content.startswith("["):
        try:
            loaded = json.loads(content)
            if isinstance(loaded, list):
                commands.extend(str(item).strip() for item in loaded if item)
        except Exception as err:
            print(f"ERROR: Failed to parse JSON commands file: {err}", file=sys.stderr)
            return []
    else:
        for line in content.splitlines():
            cleaned = line.strip()
            if cleaned and not cleaned.startswith("#"):
                commands.append(cleaned)
    return commands


def run_verify_doc_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for deterministic document artifact verification."""
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
        prog="ccba-harness verify-doc",
        description="Verify a document artifact's presence, size, and headings contract.",
    )
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Path to the document artifact (.md, .docx, .pptx, etc.)",
    )
    parser.add_argument(
        "--min-bytes",
        type=int,
        default=100,
        help="Minimum expected file size in bytes (default: 100)",
    )
    parser.add_argument(
        "--required-headings",
        type=str,
        default=None,
        help="Comma-separated list of heading titles required in markdown",
    )
    parser.add_argument(
        "--cwd",
        type=str,
        default=None,
        help="Base working directory to resolve relative paths",
    )

    args = parser.parse_args(args_list)

    from .verifier import verify_document_artifact

    headings = (
        [h.strip() for h in args.required_headings.split(",") if h.strip()]
        if args.required_headings
        else None
    )

    result = verify_document_artifact(
        target_path=args.target,
        min_bytes=args.min_bytes,
        required_headings=headings,
        cwd=args.cwd,
    )

    if result.passed:
        if result.stdout:
            print(result.stdout)
        return 0
    else:
        print(f"ERROR: {result.error_message}", file=sys.stderr)
        return 1


def run_verify_patch_cli(args_list: Sequence[str] | None = None) -> int:
    """CLI entry point for deterministic patch verification (`ccba-harness verify-patch`)."""
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
        prog="ccba-harness verify-patch",
        description="Verify patches & code changes deterministically via CLI exit codes.",
    )
    parser.add_argument(
        "pos_commands",
        nargs="*",
        default=[],
        help="Command strings to execute sequentially",
    )
    parser.add_argument(
        "-c",
        "--cmd",
        "--commands",
        dest="commands",
        nargs="+",
        default=[],
        help="Command string(s) to execute",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to a text or JSON file containing commands",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-command execution timeout in seconds (default: 60.0)",
    )
    parser.add_argument(
        "--cwd",
        type=str,
        default=None,
        help="Working directory for command execution",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failing command",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full result in JSON format",
    )
    parser.add_argument(
        "--report-file",
        type=str,
        default=None,
        help="Write markdown or JSON verification report to path",
    )
    parser.add_argument(
        "--preset",
        type=str,
        choices=["code", "doc", "skill", "adr", "telemetry", "ci"],
        default=None,
        help="Verification preset to automatically generate standard check commands",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="Target file or directory path for the preset",
    )
    parser.add_argument(
        "--min-bytes",
        type=int,
        default=100,
        help="Minimum expected bytes for 'doc' preset (default: 100)",
    )
    parser.add_argument(
        "--required-headings",
        type=str,
        default=None,
        help="Comma-separated required headings for 'doc' preset",
    )

    args = parser.parse_args(args_list)

    commands_to_run: list[str] = []
    if args.commands:
        commands_to_run.extend(args.commands)
    if args.pos_commands:
        commands_to_run.extend(args.pos_commands)

    if args.file:
        f_path = Path(args.file)
        if not f_path.exists():
            print(f"ERROR: Commands file does not exist: {f_path}", file=sys.stderr)
            return 1
        parsed_cmds = _parse_commands_from_file(f_path)
        commands_to_run.extend(parsed_cmds)

    if not commands_to_run and not args.preset:
        print("ERROR: No commands or preset specified for verification.", file=sys.stderr)
        return 1

    headings = (
        [h.strip() for h in args.required_headings.split(",") if h.strip()]
        if args.required_headings
        else None
    )

    from .verifier import verify_patch_execution

    report = verify_patch_execution(
        commands=commands_to_run,
        preset=args.preset,
        target=args.target,
        min_bytes=args.min_bytes,
        required_headings=headings,
        cwd=Path(args.cwd).resolve() if args.cwd else None,
        timeout=args.timeout,
        fail_fast=args.fail_fast,
    )

    if args.report_file:
        import json

        rf_path = Path(args.report_file)
        rf_path.parent.mkdir(parents=True, exist_ok=True)
        if rf_path.suffix.lower() == ".json":
            rf_path.write_text(
                json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
            )
        else:
            rf_path.write_text(report.to_markdown(), encoding="utf-8")

    if args.json:
        import json

        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(report.to_markdown())

    return 0 if report.all_passed else 1


def run_telemetry_cli(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for subagent runtime telemetry (`ccba-harness telemetry`)."""
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

    from .telemetry import (
        OtelSpanExporter,
        analyze_subagent_transcript,
        audit_swarm_session,
        check_subagent_budget,
    )

    parser = argparse.ArgumentParser(
        prog="ccba-harness telemetry",
        description="Subagent runtime telemetry and token monitoring.",
    )
    sub = parser.add_subparsers(dest="telemetry_cmd", required=True)

    # Subcommand: inspect
    p_insp = sub.add_parser("inspect", help="Inspect subagent trajectory & tokens")
    p_insp.add_argument("target", help="Conversation ID or transcript.jsonl path")
    p_insp.add_argument("--json", action="store_true", help="Output raw JSON")

    # Subcommand: budget-check
    p_bud = sub.add_parser("budget-check", help="Enforce token/duration budget")
    p_bud.add_argument("target", help="Conversation ID or transcript.jsonl path")
    p_bud.add_argument("--max-tokens", type=int, default=None, help="Maximum allowed tokens")
    p_bud.add_argument("--max-duration", type=float, default=None, help="Maximum allowed seconds")

    # Subcommand: export-otel
    p_otel = sub.add_parser("export-otel", help="Export OpenTelemetry GenAI OTLP JSON trace")
    p_otel.add_argument("target", help="Conversation ID or transcript.jsonl path")
    p_otel.add_argument("--out", type=str, default=None, help="Output file path")

    # Subcommand: audit-swarm
    p_swarm = sub.add_parser(
        "audit-swarm", help="Audit token consumption across a multi-agent swarm session"
    )
    p_swarm.add_argument("target", help="Parent conversation ID, transcript path, or directory")
    p_swarm.add_argument(
        "--max-swarm-tokens", type=int, default=None, help="Max total tokens for whole swarm"
    )
    p_swarm.add_argument(
        "--max-subagent-tokens", type=int, default=None, help="Max tokens per subagent"
    )
    p_swarm.add_argument("--max-cost", type=float, default=None, help="Max total cost in USD")
    p_swarm.add_argument("--json", action="store_true", help="Output raw JSON")
    p_swarm.add_argument("--out", type=str, default=None, help="Save markdown/json report to file")

    # Subcommand: dashboard
    p_dash = sub.add_parser("dashboard", help="Generate interactive HTML Swarm Telemetry Dashboard")
    p_dash.add_argument("target", help="Parent conversation ID, transcript path, or directory")
    p_dash.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output HTML file path (default: .md/reports/swarm_telemetry_dashboard.html)",
    )
    p_dash.add_argument("--title", type=str, default=None, help="Custom dashboard title")

    # Subcommand: fleet
    p_fleet = sub.add_parser("fleet", help="Cross-Spoke enterprise fleet telemetry & analytics")
    p_fleet.add_argument(
        "--json", action="store_true", help="Output fleet metrics as raw JSON dictionary"
    )
    p_fleet.add_argument(
        "--dashboard", action="store_true", help="Generate standalone HTML fleet dashboard"
    )
    p_fleet.add_argument(
        "--out",
        type=str,
        default=None,
        help="File path to save the HTML dashboard or JSON report",
    )
    p_fleet.add_argument("--title", type=str, default=None, help="Custom fleet dashboard title")

    # Subcommand: economy
    p_eco = sub.add_parser("economy", help="Prompt density & token economy optimization")
    p_eco.add_argument(
        "--scan-skills",
        action="store_true",
        help="Scan and score Prompt Density Index (PDI) for all skills",
    )
    p_eco.add_argument(
        "--session",
        type=str,
        default=None,
        help="Evaluate role-aware Token ROI for a subagent session",
    )
    p_eco.add_argument(
        "--role",
        type=str,
        default=None,
        help="Override role for ROI evaluation (coder, investigator, reviewer, general)",
    )
    p_eco.add_argument(
        "--prune-report", action="store_true", help="Generate actionable prompt pruning diff report"
    )
    p_eco.add_argument("--json", action="store_true", help="Output results as raw JSON")
    p_eco.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output file path (default for report: .md/reports/prompt_economy_report.md)",
    )

    args = parser.parse_args(argv)

    import json

    if args.telemetry_cmd == "economy":
        from .economy import (
            audit_token_economy,
            calculate_role_aware_roi,
            generate_prompt_pruning_report,
        )

        session_metrics = None
        if args.session:
            try:
                session_metrics = analyze_subagent_transcript(args.session)
            except Exception as err:
                print(f"[Warning] Could not load session '{args.session}': {err}", file=sys.stderr)

        report = audit_token_economy(session_metrics=session_metrics)
        if args.session and session_metrics and args.role:
            report.session_roi = calculate_role_aware_roi(session_metrics, role_override=args.role)

        if args.prune_report:
            out_file = Path(args.out) if args.out else Path(".md/reports/prompt_economy_report.md")
            generate_prompt_pruning_report(report, output_path=out_file)
            print(f"[Success] Generated Prompt Pruning Report at: {out_file.resolve()}")
            print(f"  Total Skills: {report.total_skills}")
            print(f"  Average PDI: {report.avg_pdi:.1f} / 100.0")
            print(f"  Bloated Skills: {report.bloated_skills_count}")
            print(f"  Estimated Token Savings: ~{report.estimated_token_savings:,} tokens")
            return 0

        if args.json:
            payload = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
            if args.out:
                Path(args.out).write_text(payload, encoding="utf-8")
                print(f"[Success] Saved JSON economy report to {args.out}")
            else:
                print(payload)
            return 0

        # Markdown output
        md_text = report.to_markdown()
        if args.out:
            Path(args.out).write_text(md_text, encoding="utf-8")
            print(f"[Success] Saved economy report to {args.out}")
        else:
            print(md_text)
        return 0

    if args.telemetry_cmd == "fleet":
        from .fleet import aggregate_fleet_telemetry, render_fleet_dashboard

        if args.dashboard:
            try:
                out_path, report = render_fleet_dashboard(
                    output_path=Path(args.out) if args.out else None,
                    title=args.title,
                )
                print(f"[Success] Generated Cross-Spoke Fleet Dashboard at: {out_path.resolve()}")
                print(f"  Fleet Hub: {report.hub_name}")
                print(f"  Spokes: {report.total_spokes} ({report.online_spokes} Online)")
                print(f"  Total Fleet Tokens: {report.total_fleet_tokens:,}")
                print(f"  Total Fleet Cost: ${report.total_fleet_cost_usd:.4f} USD")
                return 0
            except Exception as err:
                print(f"[Error] Failed to render fleet dashboard: {err}", file=sys.stderr)
                return 1
        else:
            try:
                report = aggregate_fleet_telemetry()
                if args.json:
                    out_content = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
                else:
                    out_content = report.to_markdown()

                if args.out:
                    out_p = Path(args.out)
                    out_p.parent.mkdir(parents=True, exist_ok=True)
                    out_p.write_text(out_content, encoding="utf-8")
                    print(f"[Success] Saved fleet telemetry report to {out_p}")
                else:
                    print(out_content)
                return 0
            except Exception as err:
                print(f"[Error] Failed to aggregate fleet telemetry: {err}", file=sys.stderr)
                return 1

    if args.telemetry_cmd == "dashboard":
        from .dashboard import render_swarm_dashboard

        try:
            out_path, report = render_swarm_dashboard(
                args.target,
                output_path=args.out,
                title=args.title,
            )
            print(f"[Success] Generated Swarm Telemetry Dashboard at: {out_path.resolve()}")
            print(f"  Parent Session: {report.parent_conversation_id}")
            print(f"  Subagents: {report.total_subagents}")
            print(f"  Total Tokens: {report.total_swarm_tokens:,}")
            print(f"  Estimated Cost: ${report.total_cost_usd:.4f} USD")
            return 0
        except Exception as err:
            print(
                f"[Error] Failed to render dashboard for '{args.target}': {err}",
                file=sys.stderr,
            )
            return 1

    if args.telemetry_cmd == "audit-swarm":
        try:
            report, passed, msg = audit_swarm_session(
                args.target,
                max_swarm_tokens=args.max_swarm_tokens,
                max_subagent_tokens=args.max_subagent_tokens,
                max_total_cost_usd=args.max_cost,
            )
        except Exception as err:
            print(f"[Error] Failed to audit swarm for '{args.target}': {err}", file=sys.stderr)
            return 1

        out_content = (
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
            if args.json
            else report.to_markdown()
        )
        if args.out:
            out_p = Path(args.out)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(out_content, encoding="utf-8")
            print(f"[Success] Saved swarm report to {out_p}")
        else:
            print(out_content)

        if not passed:
            print(f"[FAIL] Swarm budget violation: {msg}", file=sys.stderr)
            return 1
        return 0

    try:
        metrics = analyze_subagent_transcript(args.target)
    except Exception as err:
        print(f"[Error] Failed to analyze transcript for '{args.target}': {err}", file=sys.stderr)
        return 1

    if args.telemetry_cmd == "inspect":
        if args.json:
            print(json.dumps(metrics.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(metrics.to_markdown())
        return 0

    elif args.telemetry_cmd == "budget-check":
        passed, msg = check_subagent_budget(
            metrics,
            max_tokens=args.max_tokens,
            max_duration_sec=args.max_duration,
        )
        if passed:
            print(f"[PASS] {msg}")
            print(
                f"  Consumed: {metrics.total_tokens:,} tokens in {metrics.total_duration_sec:.1f}s"
            )
            return 0
        else:
            print(f"[FAIL] Budget violation: {msg}", file=sys.stderr)
            print(
                f"  Actual: {metrics.total_tokens:,} tokens in {metrics.total_duration_sec:.1f}s",
                file=sys.stderr,
            )
            return 1

    elif args.telemetry_cmd == "export-otel":
        otlp = OtelSpanExporter.to_otlp_json(metrics)
        payload = json.dumps(otlp, indent=2, ensure_ascii=False)
        if args.out:
            out_p = Path(args.out)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(payload, encoding="utf-8")
            print(f"[Success] Exported OTLP trace to {out_p}")
        else:
            print(payload)
        return 0

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

    # Subcommand: verify-patch
    patch_parser = subparsers.add_parser(
        "verify-patch",
        help="Verify patches & code changes deterministically via CLI exit codes.",
    )
    patch_parser.add_argument(
        "pos_commands",
        nargs="*",
        default=[],
        help="Command strings to execute sequentially",
    )
    patch_parser.add_argument(
        "-c",
        "--cmd",
        "--commands",
        dest="commands",
        nargs="+",
        default=[],
        help="Command string(s) to execute",
    )
    patch_parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to a text or JSON file containing commands",
    )
    patch_parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-command execution timeout in seconds (default: 60.0)",
    )
    patch_parser.add_argument(
        "--cwd",
        type=str,
        default=None,
        help="Working directory for command execution",
    )
    patch_parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failing command",
    )
    patch_parser.add_argument(
        "--json",
        action="store_true",
        help="Output full result in JSON format",
    )
    patch_parser.add_argument(
        "--report-file",
        type=str,
        default=None,
        help="Write markdown or JSON verification report to path",
    )

    # Subcommand: verify-doc
    doc_parser = subparsers.add_parser(
        "verify-doc",
        help="Verify a document artifact's presence, size, and headings contract.",
    )
    doc_parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Path to the document artifact (.md, .docx, .pptx, etc.)",
    )
    doc_parser.add_argument(
        "--min-bytes",
        type=int,
        default=100,
        help="Minimum expected file size in bytes (default: 100)",
    )
    doc_parser.add_argument(
        "--required-headings",
        type=str,
        default=None,
        help="Comma-separated list of heading titles required in markdown",
    )
    doc_parser.add_argument(
        "--cwd",
        type=str,
        default=None,
        help="Base working directory to resolve relative paths",
    )

    # Subcommand: telemetry
    subparsers.add_parser(
        "telemetry",
        help="Subagent runtime telemetry and token monitoring.",
    )

    if not argv:
        parser.print_help()
        return 0

    # Fast dispatch for explicit subcommands
    if argv[0] == "validate-skill":
        return run_skill_validation_cli(argv[1:])
    if argv[0] == "evaluate-gpi":
        return run_evaluate_gpi_cli(argv[1:])
    if argv[0] == "eval":
        return run_eval_cli(argv[1:])
    if argv[0] == "verify-patch":
        return run_verify_patch_cli(argv[1:])
    if argv[0] == "verify-doc":
        return run_verify_doc_cli(argv[1:])
    if argv[0] == "telemetry":
        return run_telemetry_cli(argv[1:])

    # Fallback to general parsing
    parsed = parser.parse_args(argv)
    if parsed.subcommand == "validate-skill":
        return run_skill_validation_cli(argv[1:])
    if parsed.subcommand == "evaluate-gpi":
        return run_evaluate_gpi_cli(argv[1:])
    if parsed.subcommand == "eval":
        return run_eval_cli(argv[1:])
    if parsed.subcommand == "verify-patch":
        return run_verify_patch_cli(argv[1:])
    if parsed.subcommand == "verify-doc":
        return run_verify_doc_cli(argv[1:])
    if parsed.subcommand == "telemetry":
        return run_telemetry_cli(argv[1:])

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
