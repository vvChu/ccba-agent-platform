"""economy.py - Token Economy & Prompt Density Optimization Engine.

Implements architectural cost optimization and prompt hygiene (ADR-0030, ADR-0058):
1. Prompt Density Index (PDI): Quantifies directive-to-prose density in SKILL.md.
2. Fast Sentence Hashing: Detects inter-skill copy-paste duplication without CI latency penalty (< 300ms).
3. Role-Aware Token ROI: Evaluates token investment efficiency against productive trajectory outputs.
4. Human-In-The-Loop (HITL) Prompt Pruning Diff generation.
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ccba_harness.telemetry import SubagentSessionMetrics, TokenEstimator


@dataclass
class SkillPromptMetrics:
    """Quantitative prompt economy metrics for a single SKILL.md."""

    skill_name: str
    skill_path: str
    char_count: int
    line_count: int
    estimated_tokens: int
    directive_count: int
    prose_word_count: int
    code_block_ratio: float
    pdi_score: float  # 0.0 to 100.0 (higher = denser, more actionable)
    duplicate_sentences: list[str] = field(default_factory=list)
    overhead_status: str = "Optimal"  # "Optimal", "Moderate", "Bloated"
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to a clean serializable dictionary."""
        data = asdict(self)
        data["code_block_ratio"] = round(self.code_block_ratio, 3)
        data["pdi_score"] = round(self.pdi_score, 1)
        return data


@dataclass
class TokenROIMetrics:
    """Return-on-Investment (ROI) metric for an agent execution session."""

    conversation_id: str
    role: str  # "coder", "investigator", "reviewer", "general"
    prompt_tokens: int
    completion_tokens: int
    turns_count: int
    productive_score: float
    token_roi: float  # Productive score per 100K prompt tokens
    efficiency_tier: str  # "Tier A (High)", "Tier B (Standard)", "Tier C (Low / Inefficient)"
    summary_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert ROI metrics to serializable dictionary."""
        data = asdict(self)
        data["productive_score"] = round(self.productive_score, 2)
        data["token_roi"] = round(self.token_roi, 2)
        return data


@dataclass
class EconomyAuditReport:
    """Platform-wide audit report synthesizing prompt density and token efficiency."""

    total_skills: int
    avg_pdi: float
    total_prompt_tokens_est: int
    bloated_skills_count: int
    skills_metrics: list[SkillPromptMetrics] = field(default_factory=list)
    session_roi: TokenROIMetrics | None = None
    estimated_token_savings: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert economy report to dictionary."""
        return {
            "total_skills": self.total_skills,
            "avg_pdi": round(self.avg_pdi, 1),
            "total_prompt_tokens_est": self.total_prompt_tokens_est,
            "bloated_skills_count": self.bloated_skills_count,
            "estimated_token_savings": self.estimated_token_savings,
            "session_roi": self.session_roi.to_dict() if self.session_roi else None,
            "skills": [s.to_dict() for s in self.skills_metrics],
        }

    def to_markdown(self) -> str:
        """Format economy audit into executive Markdown report."""
        lines = [
            "# 📈 CCBA Token Economy & Prompt Density Audit Report",
            "",
            "## 1. Executive Summary",
            "",
            f"- **Total Skills Audited:** {self.total_skills}",
            f"- **Average Prompt Density Index (PDI):** {self.avg_pdi:.1f} / 100.0",
            f"- **Total Estimated Prompt Tokens:** {self.total_prompt_tokens_est:,}",
            f"- **Overhead / Bloated Skills Count:** {self.bloated_skills_count}",
            f"- **Potential Token Savings Per Swarm Run:** ~{self.estimated_token_savings:,} tokens",
            "",
        ]

        if self.session_roi:
            roi = self.session_roi
            lines.extend(
                [
                    "## 2. Active Session Token ROI Analysis",
                    "",
                    f"- **Session ID:** `{roi.conversation_id}`",
                    f"- **Assigned Role:** `{roi.role}`",
                    f"- **Total Prompt Tokens:** {roi.prompt_tokens:,}",
                    f"- **Completion Tokens:** {roi.completion_tokens:,}",
                    f"- **Model Turns:** {roi.turns_count}",
                    f"- **Productive Output Score:** {roi.productive_score:.1f}",
                    f"- **Token ROI (Value / 100K prompt tokens):** **{roi.token_roi:.2f}**",
                    f"- **Efficiency Classification:** **{roi.efficiency_tier}**",
                    f"- **Assessment:** {roi.summary_notes}",
                    "",
                ]
            )

        lines.extend(
            [
                "## 3. Top Skills Requiring Prompt Pruning / Optimization",
                "",
                "| Skill Name | Tokens | Directives | PDI Score | Status | Recommendations |",
                "| :--- | :---: | :---: | :---: | :---: | :--- |",
            ]
        )

        # Sort by tokens descending
        sorted_skills = sorted(self.skills_metrics, key=lambda s: s.estimated_tokens, reverse=True)
        for s in sorted_skills[:15]:
            recs = "; ".join(s.recommendations) if s.recommendations else "Well structured"
            lines.append(
                f"| `{s.skill_name}` | {s.estimated_tokens:,} | {s.directive_count} | {s.pdi_score:.1f} | {s.overhead_status} | {recs} |"
            )

        lines.append("")
        return "\n".join(lines)


# ----------------------------------------------------------------------
# Internal Helpers for Prompt Density Analysis
# ----------------------------------------------------------------------


def _clean_sentence(text: str) -> str:
    """Normalize a sentence for duplicate hashing."""
    cleaned = re.sub(r"\s+", " ", text).strip().lower()
    # Remove markdown link URLs and inline formatting
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"[`*_#]", "", cleaned)
    return cleaned.strip()


def _hash_sentence(sentence: str) -> str:
    """Generate MD5 hash of normalized sentence."""
    return hashlib.md5(sentence.encode("utf-8")).hexdigest()[:12]


def _extract_sentences(markdown: str) -> list[str]:
    """Extract substantive sentences from markdown text, ignoring short items."""
    raw_sentences = re.split(r"[.\n!?]+", markdown)
    substantive = []
    for s in raw_sentences:
        clean = _clean_sentence(s)
        # Only check substantive sentences with at least 8 words
        if len(clean.split()) >= 8:
            substantive.append(clean)
    return substantive


def analyze_skill_prompt_density(skill_path: Path | str) -> SkillPromptMetrics:
    """Analyze a single SKILL.md file for prompt density and directives."""
    p = Path(skill_path)
    content = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
    skill_name = p.parent.name if p.name == "SKILL.md" else p.stem

    char_count = len(content)
    line_count = len(content.splitlines())
    estimated_tokens = TokenEstimator.estimate_text(content)

    # 1. Count actionable directives: code blocks, CLI invocations, bullet points, checklists
    code_blocks = len(re.findall(r"```[\w]*\n[\s\S]*?```", content))
    cli_commands = len(re.findall(r"`(?:python|ccba-|git|pytest|ruff) [^`]+`", content))
    checklists = len(re.findall(r"- \[[ xX]\]", content))
    subsections = len(re.findall(r"^#{2,4}\s+", content, re.MULTILINE))

    directive_count = (code_blocks * 3) + cli_commands + checklists + subsections

    # 2. Count code block characters vs prose characters
    code_chars = sum(len(m) for m in re.findall(r"```[\w]*\n[\s\S]*?```", content))
    code_block_ratio = code_chars / max(1, char_count)

    # 3. Count prose words
    # Strip code blocks to isolate prose
    prose_only = re.sub(r"```[\w]*\n[\s\S]*?```", "", content)
    prose_words = len(re.findall(r"\b\w+\b", prose_only))

    # 4. Calculate Prompt Density Index (PDI)
    # Formula balances directive density per 1,000 tokens while penalizing bloated wordiness
    tokens_k = max(0.2, estimated_tokens / 1000.0)
    directives_per_k = directive_count / tokens_k

    # Baseline PDI: 30 base + directives weight + code ratio bonus
    pdi_raw = 30.0 + (directives_per_k * 4.0) + (code_block_ratio * 30.0)

    # Penalize if tokens > 3,500 with low directive density
    if estimated_tokens > 3500:
        penalty = min(25.0, (estimated_tokens - 3500) / 200.0)
        pdi_raw -= penalty

    pdi_score = max(5.0, min(99.0, pdi_raw))

    # 5. Determine Overhead Status & Actionable Recommendations
    recommendations: list[str] = []
    if estimated_tokens > 4000:
        overhead_status = "Bloated / High Overhead"
        recommendations.append(
            f"Prompt is {estimated_tokens:,} tokens. Consider splitting into progressive reference files."
        )
    elif estimated_tokens > 2500:
        overhead_status = "Moderate Overhead"
        if directives_per_k < 6.0:
            recommendations.append(
                "Low directive density. Trim narrative explanations into bullet lists."
            )
    else:
        overhead_status = "Optimal"

    if code_block_ratio > 0.65:
        recommendations.append(
            "Excessive embedded code. Move large code examples to scripts/ or references/."
        )

    return SkillPromptMetrics(
        skill_name=skill_name,
        skill_path=str(p.as_posix()),
        char_count=char_count,
        line_count=line_count,
        estimated_tokens=estimated_tokens,
        directive_count=directive_count,
        prose_word_count=prose_words,
        code_block_ratio=code_block_ratio,
        pdi_score=pdi_score,
        duplicate_sentences=[],
        overhead_status=overhead_status,
        recommendations=recommendations,
    )


def detect_sentence_duplicates(skill_paths: list[Path]) -> dict[str, list[str]]:
    """Detect cross-skill duplicated sentences across multiple SKILL.md files.

    Uses sentence hashing for fast O(N*L) index matching (< 300ms for 67 skills).
    """
    sentence_map: dict[str, list[str]] = defaultdict(list)
    clean_to_raw: dict[str, str] = {}

    for path in skill_paths:
        if not path.exists():
            continue
        skill_name = path.parent.name if path.name == "SKILL.md" else path.stem
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            sentences = _extract_sentences(content)
            for s in sentences:
                h = _hash_sentence(s)
                if skill_name not in sentence_map[h]:
                    sentence_map[h].append(skill_name)
                    clean_to_raw[h] = s[:80] + "..." if len(s) > 80 else s
        except Exception:
            continue

    # Filter hashes shared by 2 or more distinct skills
    duplicates_by_skill: dict[str, list[str]] = defaultdict(list)
    for h, skills in sentence_map.items():
        if len(skills) >= 2:
            snippet = clean_to_raw[h]
            msg = f"Duplicated across [{', '.join(skills)}]: '{snippet}'"
            for sk in skills:
                duplicates_by_skill[sk].append(msg)

    return duplicates_by_skill


def scan_all_skills_economy(skills_dir: Path | None = None) -> list[SkillPromptMetrics]:
    """Scan and compute prompt economy metrics for all skills in monorepo."""
    root = skills_dir or Path(".agents/skills")
    skill_paths = sorted(root.glob("*/SKILL.md"))
    if not skill_paths:
        # Fallback to any SKILL.md found
        skill_paths = sorted(root.rglob("SKILL.md"))

    # 1. Compute density metrics
    metrics_list = [analyze_skill_prompt_density(p) for p in skill_paths]

    # 2. Compute cross-duplication
    dup_map = detect_sentence_duplicates(skill_paths)
    for m in metrics_list:
        if m.skill_name in dup_map:
            m.duplicate_sentences = dup_map[m.skill_name][:5]
            if len(m.duplicate_sentences) > 2 and "Bloated" not in m.overhead_status:
                m.overhead_status = "Moderate Overhead"
                m.recommendations.append(
                    f"Contains {len(m.duplicate_sentences)} duplicated sentences found in other skills."
                )

    return metrics_list


def calculate_role_aware_roi(
    session_metrics: SubagentSessionMetrics,
    role_override: str | None = None,
) -> TokenROIMetrics:
    """Calculate productive Token ROI for an agent execution trajectory based on its role."""
    conv_id = session_metrics.conversation_id
    prompt_tokens = max(1, session_metrics.prompt_tokens)
    completion_tokens = session_metrics.completion_tokens
    tool_counts = session_metrics.tool_counts
    turns = session_metrics.turns_count

    # 1. Infer or accept role
    role = role_override or "general"
    if not role_override:
        log_lower = session_metrics.log_file.lower()
        if any(w in log_lower for w in ["coder", "implement", "patch", "refactor"]):
            role = "coder"
        elif any(w in log_lower for w in ["investigator", "research", "audit", "search"]):
            role = "investigator"
        elif any(w in log_lower for w in ["review", "gate", "eval"]):
            role = "reviewer"

    # 2. Compute productive output score based on role specialization
    if role == "coder":
        # Coder value comes from write/edit tools, command runs, and completion output
        writes = tool_counts.get("write_to_file", 0) * 15.0
        edits = tool_counts.get("replace_file_content", 0) * 12.0
        cmds = tool_counts.get("run_command", 0) * 5.0
        code_tokens = (completion_tokens / 1000.0) * 2.0
        productive_score = writes + edits + cmds + code_tokens
        notes = "Assessed primarily on code mutations, file edits, and verification commands."

    elif role == "investigator":
        # Investigator value comes from file views, grep queries, and synthesis
        views = tool_counts.get("view_file", 0) * 4.0
        greps = tool_counts.get("grep_search", 0) * 4.0
        searches = tool_counts.get("search_web", 0) * 6.0
        synthesis_tokens = (completion_tokens / 1000.0) * 4.0
        productive_score = views + greps + searches + synthesis_tokens
        notes = "Assessed on investigation depth, file reading coverage, and diagnostic synthesis."

    elif role == "reviewer":
        # Reviewer value comes from verification checks and structured reports
        checks = tool_counts.get("run_command", 0) * 8.0
        views = tool_counts.get("view_file", 0) * 3.0
        critique_tokens = (completion_tokens / 1000.0) * 3.0
        productive_score = checks + views + critique_tokens
        notes = "Assessed on audit thoroughness, verification gate commands, and compliance checks."

    else:
        # General role: balanced formula across all tools
        total_tool_calls = sum(tool_counts.values()) * 5.0
        tokens_val = (completion_tokens / 1000.0) * 2.5
        productive_score = total_tool_calls + tokens_val
        notes = "Assessed on broad tool invocations and output balance."

    # 3. Calculate Token ROI: Productive Value per 100K prompt tokens
    token_roi = (productive_score / prompt_tokens) * 100000.0

    # 4. Classify efficiency tier
    if token_roi >= 25.0:
        efficiency_tier = "Tier A (High Efficiency)"
    elif token_roi >= 8.0:
        efficiency_tier = "Tier B (Standard Efficiency)"
    else:
        efficiency_tier = "Tier C (Low Efficiency / Prompt Overhead Alert)"

    return TokenROIMetrics(
        conversation_id=conv_id,
        role=role,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        turns_count=turns,
        productive_score=productive_score,
        token_roi=token_roi,
        efficiency_tier=efficiency_tier,
        summary_notes=notes,
    )


def audit_token_economy(
    skills_dir: Path | None = None,
    session_metrics: SubagentSessionMetrics | None = None,
) -> EconomyAuditReport:
    """Run full economy audit across all skills and optional active session."""
    skills = scan_all_skills_economy(skills_dir)
    total_skills = len(skills)
    avg_pdi = sum(s.pdi_score for s in skills) / max(1, total_skills)
    total_tokens = sum(s.estimated_tokens for s in skills)

    bloated = [s for s in skills if "Bloated" in s.overhead_status]
    bloated_count = len(bloated)

    # Estimate potential savings: if bloated skills are trimmed to 2,500 tokens
    token_savings = sum(max(0, s.estimated_tokens - 2500) for s in bloated)

    session_roi = calculate_role_aware_roi(session_metrics) if session_metrics else None

    return EconomyAuditReport(
        total_skills=total_skills,
        avg_pdi=avg_pdi,
        total_prompt_tokens_est=total_tokens,
        bloated_skills_count=bloated_count,
        skills_metrics=skills,
        session_roi=session_roi,
        estimated_token_savings=token_savings,
    )


def generate_prompt_pruning_report(
    report: EconomyAuditReport,
    output_path: Path | str | None = None,
) -> str:
    """Generate Markdown report with concrete pruning recommendations and optional file write."""
    md_content = report.to_markdown()

    # Append actionable diff suggestions
    diff_sections = [
        "",
        "## 4. Actionable HITL Prompt Pruning Recommendations",
        "",
        "> [!TIP]",
        "> Áp dụng nguyên tắc **Progressive Disclosure** (ADR-0030, ADR-0057): Kỹ năng `SKILL.md` chỉ giữ các chỉ dẫn điều phối cốt lõi. Các ví dụ chi tiết, template dài, hoặc cẩm nang hướng dẫn nên chuyển vào thư mục `references/*.md`.",
        "",
    ]

    bloated_skills = [
        s for s in report.skills_metrics if s.estimated_tokens > 3000 or s.duplicate_sentences
    ]
    if not bloated_skills:
        diff_sections.append(
            "✅ **Tất cả các kỹ năng đều đạt chuẩn mật độ chỉ dẫn tối ưu. Không có kỹ năng nào bị phình to bất thường.**"
        )
    else:
        for s in bloated_skills:
            diff_sections.extend(
                [
                    f"### 🔍 Skill `{s.skill_name}` ({s.estimated_tokens:,} tokens | PDI: {s.pdi_score:.1f})",
                    f"- **Đường dẫn:** `{s.skill_path}`",
                    f"- **Trạng thái:** `{s.overhead_status}`",
                ]
            )
            for r in s.recommendations:
                diff_sections.append(f"  - ⚠️ {r}")

            if s.duplicate_sentences:
                diff_sections.append("  - 🔄 **Trùng lặp cần khử (DRY Rule):**")
                for d in s.duplicate_sentences[:3]:
                    diff_sections.append(f"    * {d}")

            diff_sections.append("")

    full_markdown = md_content + "\n" + "\n".join(diff_sections)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(full_markdown, encoding="utf-8")

    return full_markdown
