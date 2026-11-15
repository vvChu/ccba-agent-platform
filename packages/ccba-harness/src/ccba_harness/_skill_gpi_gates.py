"""_skill_gpi_gates.py - Stage 1/2 GPI evaluation and workspace gate checks.

Internal decomposition module for `ccba_harness.skill_validator`.
Not a standalone package boundary for external callers unless explicitly re-exported.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ._skill_frontmatter import (
    MAX_MODEL_INVOKED_PER_BUNDLE,
    SkillAuditIssue,
    normalize_bool_flag,
    parse_markdown_frontmatter,
)
from .gpi import (
    GPI_STANDALONE_THRESHOLD,
    ArchitectureTier,
    DecisionRequest,
    DecisionResult,
    GPIMetrics,
    evaluate_two_stage_decision,
)

_TIER3_VALUES = {"orchestrator", "composite-orchestrator", "tier 3", "tier-3"}
_TIER2B_VALUES = {"kernel", "tier-2b", "tier_2b", "tier 2b"}
_TIER2A_VALUES = {
    "reference",
    "progressive-reference",
    "progressive_reference",
    "tier-2a",
    "tier_2a",
    "tier 2a",
}
_COORD_KEYWORDS = (
    "dispatch worker",
    "phân công worker",
    "worker subagent",
    "team_sheet",
    "spawn subagent",
    "giao cho subagent",
    "workers thực thi",
)
_SINGLE_WRITER_KEYWORDS = (
    "single-writer",
    "single writer",
    "read-only",
    "read only",
    "duy nhất orchestrator",
    "duy nhất có quyền ghi",
    "scratch",
)


def _issue(fp: str, msg: str, category: str, subj: str | None = None) -> SkillAuditIssue:
    """Build a line-1 SkillAuditIssue record concisely."""
    return SkillAuditIssue(1, fp if subj is None else subj, msg, category, fp)


def _extract_stage1_flags(meta: dict[str, Any]) -> tuple[bool, bool, bool]:
    """Extract deterministic, orchestrated, and tier-3 flags from frontmatter."""
    is_det = bool(
        normalize_bool_flag(
            meta.get(
                "is-deterministic", meta.get("is_deterministic", meta.get("deterministic", False))
            )
        )
    )
    is_tier3 = str(meta.get("tier", "")).lower() in _TIER3_VALUES
    is_orch = bool(
        normalize_bool_flag(
            meta.get(
                "is-orchestrated", meta.get("is_orchestrated", meta.get("orchestrated", False))
            )
        )
    )
    return is_det, (True if is_tier3 else is_orch), is_tier3


def _check_single_writer_protocol(
    file_path: Path, skill_name: str, content: str | None
) -> list[SkillAuditIssue]:
    """Verify Tier 3 multi-agent orchestrator documents Single-Writer Protocol (ADR-0053)."""
    raw_content = (
        content if content is not None else file_path.read_text(encoding="utf-8")
    ).lower()
    if not any(kw in raw_content for kw in _COORD_KEYWORDS) or any(
        kw in raw_content for kw in _SINGLE_WRITER_KEYWORDS
    ):
        return []
    msg = (
        f"Tier 3 Orchestrator '{skill_name}' coordinates workers/subagents but lacks "
        "Single-Writer Protocol (ADR-0053) specification (exclusive writer or read-only workers)."
    )
    return [_issue(str(file_path), msg, "SINGLE_WRITER_PROTOCOL_VIOLATION")]


def _evaluate_stage1_gates(
    file_path: Path, skill_name: str, meta: dict[str, Any], content: str | None
) -> tuple[bool, list[SkillAuditIssue]]:
    """Run Stage 1 Determinism and Orchestration invariant gates."""
    fp = str(file_path)
    is_det, is_orch, is_tier3 = _extract_stage1_flags(meta)
    issues: list[SkillAuditIssue] = []
    if is_det:
        issues.append(
            _issue(
                fp,
                f"Skill '{skill_name}' violates Gate 0 (Determinism Gate): task can be solved 100% "
                "deterministically (regex, AST parse, math, file I/O) and must be implemented as "
                "Tier 1 (Package Function / Deep Seam in packages/*), not a standalone skill.",
                "DETERMINISM_GATE_VIOLATION",
            )
        )
    if is_orch and not is_tier3:
        issues.append(
            _issue(
                fp,
                f"Skill '{skill_name}' violates Gate 1 (Orchestration Gate): task coordinates "
                "multiple agents, StateGraph checkpoints, or requires HITL approval, "
                "and must be implemented as Tier 3 (Composite Orchestrator) with 'tier: orchestrator'.",
                "ORCHESTRATION_GATE_VIOLATION",
            )
        )
    elif is_tier3:
        issues.extend(_check_single_writer_protocol(file_path, skill_name, content))
    return (is_det or is_orch), issues


def _check_declared_gpi_score(
    fp: str, skill_name: str, normalized_gpi: dict[str, Any], decision: DecisionResult
) -> list[SkillAuditIssue]:
    """Verify declared GPI score matches mathematical formula within 0.05 tolerance (COND-01)."""
    declared_score = (
        normalized_gpi.get("score")
        or normalized_gpi.get("total")
        or normalized_gpi.get("gpi_score")
    )
    if declared_score is None:
        return []
    try:
        dec_val = float(declared_score)
    except (TypeError, ValueError):
        return []
    expected_score = round(decision.gpi_score or 0.0, 2)
    if abs(dec_val - expected_score) <= 0.05:
        return []
    msg = (
        f"Skill '{skill_name}' declared GPI score {dec_val} does not match "
        f"mathematical formula 2.5*S + 2.0*K + 2.0*A - 1.5*P = {expected_score} "
        "(ADR-0066 / COND-01)."
    )
    return [_issue(fp, msg, "MISMATCHED_GPI_SCORE")]


def _build_gpi_metrics(normalized_gpi: dict[str, Any]) -> GPIMetrics:
    """Validate and construct GPIMetrics from normalized frontmatter mapping."""
    for m_key in ("s", "k", "a", "p"):
        if isinstance(normalized_gpi[m_key], bool):
            raise TypeError(f"Metric '{m_key}' must be numeric, got bool")
    return GPIMetrics(
        s=float(normalized_gpi["s"]),
        k=float(normalized_gpi["k"]),
        a=float(normalized_gpi["a"]),
        p=float(normalized_gpi["p"]),
    )


def _resolve_existing_tier(meta: dict[str, Any]) -> ArchitectureTier | None:
    """Resolve explicit existing tier declaration from skill frontmatter."""
    raw = str(meta.get("existing-tier") or meta.get("existing_tier") or meta.get("tier") or "")
    norm = raw.strip().lower()
    if norm in _TIER2B_VALUES:
        return ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL
    if norm in _TIER2A_VALUES:
        return ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE
    return None


def _evaluate_gpi_dict(
    fp: str, skill_name: str, meta: dict[str, Any], gpi_data: dict[str, Any], enforce_gpi: bool
) -> list[SkillAuditIssue]:
    """Evaluate validated `gpi` frontmatter dictionary and return audit issues."""
    norm = {str(k).lower(): v for k, v in gpi_data.items()}
    missing = [k for k in ("s", "k", "a", "p") if k not in norm]
    if missing:
        msg = f"Frontmatter 'gpi' is missing required metric keys: {missing}"
        return [_issue(fp, msg, "INVALID_GPI_METRICS")]
    try:
        metrics = _build_gpi_metrics(norm)
    except (TypeError, ValueError) as err:
        return [
            _issue(fp, f"Invalid GPI metric values in frontmatter: {err}", "INVALID_GPI_METRICS")
        ]

    decision = evaluate_two_stage_decision(
        DecisionRequest(
            name=skill_name,
            is_deterministic=False,
            is_orchestrated=False,
            gpi_metrics=metrics,
            parent_skill=meta.get("parent-skill", meta.get("parent_skill")),
            existing_tier=_resolve_existing_tier(meta),
        )
    )
    issues = _check_declared_gpi_score(fp, skill_name, norm, decision)
    if enforce_gpi and decision.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE:
        score = decision.gpi_score or 0.0
        msg = (
            f"Skill '{skill_name}' has GPI {score:.2f} < {GPI_STANDALONE_THRESHOLD} "
            "minimum threshold for Standalone Kernel Skill (Tier 2B). "
            "Must be placed in references/*.md of owning Master Skill as Tier 2A."
        )
        issues.append(_issue(fp, msg, "INSUFFICIENT_GPI_SCORE"))
    return issues


def audit_granularity_and_gpi_impl(
    file_path: Path,
    name: str | None,
    meta: dict[str, Any],
    enforce_gpi: bool = False,
    content: str | None = None,
) -> list[SkillAuditIssue]:
    """Audit skill against Two-Stage Granularity Decision Framework (RES-2026-ARCH-001)."""
    fp = str(file_path)
    skill_name = name or file_path.parent.name
    bypass_stage2, issues = _evaluate_stage1_gates(file_path, skill_name, meta, content)
    if bypass_stage2:
        return issues

    gpi_data = meta.get("gpi") or meta.get("GPI")
    if gpi_data is not None:
        if not isinstance(gpi_data, dict):
            msg = "Frontmatter 'gpi' field must be a dictionary containing s, k, a, p metrics."
            issues.append(_issue(fp, msg, "INVALID_GPI_METRICS"))
        else:
            issues.extend(_evaluate_gpi_dict(fp, skill_name, meta, gpi_data, enforce_gpi))
    elif enforce_gpi:
        msg = f"Skill '{skill_name}' is missing required 'gpi' metrics block under strict GPI enforcement."
        issues.append(_issue(fp, msg, "MISSING_GPI_METRICS"))
    return issues


def _load_frontmatter_for_decision(file_path: Path, yaml_module: Any) -> dict[str, Any]:
    """Read and parse YAML frontmatter dict for `evaluate_skill_file` with strict errors."""
    if not file_path.exists():
        raise FileNotFoundError(f"Skill file does not exist: {file_path}")
    spec = parse_markdown_frontmatter(
        file_path.read_text(encoding="utf-8"), yaml_module=yaml_module
    )
    if not spec.has_frontmatter:
        raise ValueError(f"File '{file_path}' has no valid YAML frontmatter '---'")
    if spec.error == "YAML_PACKAGE_MISSING":
        raise RuntimeError("PyYAML package is required to parse skill frontmatter.")
    if spec.error and spec.error.startswith("YAML_PARSE_ERROR:"):
        raise ValueError(spec.error)
    if spec.error is not None:
        raise ValueError(f"Frontmatter in '{file_path}' is not a valid dictionary.")
    return spec.metadata


def evaluate_skill_file_decision(
    file_path: Path,
    override_deterministic: bool | None = None,
    override_orchestrated: bool | None = None,
    override_metrics: GPIMetrics | None = None,
    override_parent: str | None = None,
    override_existing_tier: ArchitectureTier | str | None = None,
    override_force_tier_flip: bool = False,
    yaml_module: Any = None,
) -> DecisionResult:
    """Evaluate a SKILL.md file through Two-Stage Decision Framework."""
    meta = _load_frontmatter_for_decision(file_path, yaml_module)
    is_det, is_orch, _ = _extract_stage1_flags(meta)
    is_det = is_det if override_deterministic is None else override_deterministic
    is_orch = is_orch if override_orchestrated is None else override_orchestrated

    gpi_data = meta.get("gpi") or meta.get("GPI")
    metrics: GPIMetrics | None = None
    if gpi_data and isinstance(gpi_data, dict):
        norm = {str(k).lower(): v for k, v in gpi_data.items()}
        if all(k in norm for k in ("s", "k", "a", "p")):
            metrics = GPIMetrics(
                s=float(norm["s"]), k=float(norm["k"]), a=float(norm["a"]), p=float(norm["p"])
            )
    return evaluate_two_stage_decision(
        DecisionRequest(
            name=str(meta.get("name") or file_path.parent.name),
            is_deterministic=is_det,
            is_orchestrated=is_orch,
            gpi_metrics=metrics or override_metrics,
            parent_skill=override_parent or meta.get("parent-skill", meta.get("parent_skill")),
            existing_tier=override_existing_tier
            or meta.get("existing-tier")
            or meta.get("existing_tier"),
            force_tier_flip=override_force_tier_flip,
            metadata={"file_path": str(file_path)},
        )
    )


def _collect_workspace_skill_stats(
    skill_files: list[Path],
    yaml_module: Any,
    shallow_checker: Callable[[Path, str], list[SkillAuditIssue]],
) -> tuple[
    list[SkillAuditIssue], dict[str, list[Path]], dict[str, int], list[tuple[str, Path, str, str]]
]:
    """Scan all SKILL.md files once to gather duplicate names, bundle counts, and relations."""
    issues: list[SkillAuditIssue] = []
    seen_names: dict[str, list[Path]] = defaultdict(list)
    bundle_counts: dict[str, int] = defaultdict(int)
    relations: list[tuple[str, Path, str, str]] = []

    for sf in skill_files:
        try:
            content = sf.read_text(encoding="utf-8")
            issues.extend(shallow_checker(sf, content))
            spec = parse_markdown_frontmatter(content, yaml_module=yaml_module)
            if not spec.has_frontmatter or spec.error is not None:
                continue
            meta = spec.metadata
            name = str(meta.get("name") or "").strip()
            if name:
                seen_names[name.lower()].append(sf)
            for rel_field in ("dependencies", "sub_skills", "master_skill"):
                raw_rel = meta.get(rel_field)
                items = (
                    [raw_rel]
                    if isinstance(raw_rel, str)
                    else (raw_rel if isinstance(raw_rel, list) else [])
                )
                for item in items:
                    if isinstance(item, str) and item.strip():
                        relations.append((name or sf.parent.name, sf, rel_field, item.strip()))
            if not normalize_bool_flag(meta.get("disable-model-invocation", False)):
                bundle_counts[str(meta.get("bundle") or meta.get("layer") or "_default")] += 1
        except Exception:
            pass
    return issues, seen_names, bundle_counts, relations


def _check_gate_invariants(
    skills_dir: Path,
    project_root: Path,
    seen_names: dict[str, list[Path]],
    bundle_counts: dict[str, int],
    relations: list[tuple[str, Path, str, str]],
) -> list[SkillAuditIssue]:
    """Validate duplicate names, bundle ceilings, and skill dependency relations."""
    issues: list[SkillAuditIssue] = []
    for skill_name, paths in seen_names.items():
        if len(paths) > 1:
            rels = [
                str(p.relative_to(project_root) if p.is_relative_to(project_root) else p)
                for p in paths
            ]
            msg = f"Duplicate skill name '{skill_name}' found across multiple locations: {', '.join(rels)}"
            issues.append(
                _issue(str(paths[0]), msg, "ZERO_DUPLICATE_GATE_VIOLATION", subj=skill_name)
            )

    for bundle, count in bundle_counts.items():
        if count > MAX_MODEL_INVOKED_PER_BUNDLE:
            msg = (
                f"Context Budget Ceiling Exceeded: Bundle '{bundle}' has {count} "
                f"model-invoked skills (Max allowed: {MAX_MODEL_INVOKED_PER_BUNDLE}). "
                "Convert ritual workflows to 'disable-model-invocation: true' per ADR-0040."
            )
            issues.append(
                _issue(str(skills_dir), msg, "CONTEXT_BUDGET_CEILING_EXCEEDED", subj=bundle)
            )

    for src_skill, sf, rel_field, target_skill in relations:
        if target_skill.lower() not in seen_names:
            msg = f"Skill '{src_skill}' declares {rel_field} reference to unknown skill '{target_skill}'."
            issues.append(_issue(str(sf), msg, "DANGLING_SKILL_DEPENDENCY", subj=src_skill))
    return issues


def _to_skill_issue(raw: Any, md_file: Path, default_cat: str) -> SkillAuditIssue:
    """Convert AuditIssueString or plain string into SkillAuditIssue."""
    if hasattr(raw, "to_audit_issue"):
        issue: SkillAuditIssue = raw.to_audit_issue()
        return issue
    return _issue(str(md_file), str(raw), default_cat)


def audit_workspace_gates_impl(
    skills_dir: Path,
    project_root: Path,
    yaml_module: Any,
    shallow_checker: Callable[[Path, str], list[SkillAuditIssue]],
    link_validator: Callable[[Path], list[str]],
    cmd_auditor: Callable[[Path, set[str]], list[str]],
    registered_cmds: set[str],
) -> list[SkillAuditIssue]:
    """Perform workspace-level CI Gate checks across all skills and markdown docs."""
    skill_files = sorted(skills_dir.rglob("SKILL.md"), key=lambda p: p.as_posix())
    issues, seen_names, bundle_counts, relations = _collect_workspace_skill_stats(
        skill_files, yaml_module, shallow_checker
    )
    issues.extend(
        _check_gate_invariants(skills_dir, project_root, seen_names, bundle_counts, relations)
    )
    for md_file in sorted(skills_dir.rglob("*.md"), key=lambda p: p.as_posix()):
        issues.extend(
            _to_skill_issue(item, md_file, "BROKEN_MARKDOWN_LINK")
            for item in link_validator(md_file)
        )
        issues.extend(
            _to_skill_issue(item, md_file, "UNREGISTERED_SLASH_COMMAND")
            for item in cmd_auditor(md_file, registered_cmds)
        )
    return issues
