"""Sanitized cross-spoke telemetry scanning and aggregation helpers (ADR-0046)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Default token budget heuristics per Spoke (e.g., 5M tokens per monthly cycle)
DEFAULT_SPOKE_BUDGET_TOKENS = 5_000_000

# Standard agent built-ins and platform utilities excluded from Spoke domain innovations
STANDARD_BUILTIN_TOOLS: frozenset[str] = frozenset(
    {
        "run_command",
        "view_file",
        "write_to_file",
        "replace_file_content",
        "grep_search",
        "find_by_name",
        "list_dir",
        "manage_task",
        "send_message",
        "schedule",
        "invoke_subagent",
        "define_subagent",
        "manage_subagents",
        "generate_image",
        "read_url_content",
        "search_web",
        "ask_question",
        "call_mcp_tool",
        "list_resources",
        "read_resource",
        "gemini_search_docs",
        "gemini_get_doc",
    }
)


@dataclass
class SpokeTelemetrySummary:
    """Sanitized, aggregated telemetry metrics for a single Spoke project (ADR-0046)."""

    spoke_id: str
    project_name: str
    project_path: str
    project_type: str
    is_sandbox: bool = False
    is_online: bool = True
    last_sync: str = ""
    total_sessions: int = 0
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost_usd: float = 0.0
    tool_counts: dict[str, int] = field(default_factory=dict)
    budget_limit_tokens: int = DEFAULT_SPOKE_BUDGET_TOKENS
    budget_status: str = "Compliant"  # "Compliant", "Warning", "Exceeded", "Offline"

    def to_dict(self) -> dict[str, Any]:
        """Convert Spoke summary to dictionary."""
        return {
            "spoke_id": self.spoke_id,
            "project_name": self.project_name,
            "project_path": self.project_path,
            "project_type": self.project_type,
            "is_sandbox": self.is_sandbox,
            "is_online": self.is_online,
            "last_sync": self.last_sync,
            "total_sessions": self.total_sessions,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "tool_counts": self.tool_counts,
            "budget_limit_tokens": self.budget_limit_tokens,
            "budget_status": self.budget_status,
        }


def _collect_tool_innovations(
    spokes: list[SpokeTelemetrySummary],
    fleet_tool_counts: dict[str, int],
) -> tuple[dict[str, list[str]], dict[str, int]]:
    """Aggregate custom domain tool counts and source Spokes, excluding standard built-ins."""
    tool_spokes_map: dict[str, list[str]] = {}
    tool_total_calls: dict[str, int] = {}
    for spoke in spokes:
        spoke_label = spoke.project_name or spoke.spoke_id or "Unknown Spoke"
        for tool_name, count in spoke.tool_counts.items():
            if tool_name in STANDARD_BUILTIN_TOOLS:
                continue
            if tool_name not in tool_spokes_map:
                tool_spokes_map[tool_name] = []
                tool_total_calls[tool_name] = 0
            if spoke_label not in tool_spokes_map[tool_name]:
                tool_spokes_map[tool_name].append(spoke_label)
            tool_total_calls[tool_name] += count

    for tool_name, count in fleet_tool_counts.items():
        if tool_name not in STANDARD_BUILTIN_TOOLS and tool_name not in tool_total_calls:
            tool_total_calls[tool_name] = count
            tool_spokes_map[tool_name] = ["Fleet Aggregate"]
    return tool_spokes_map, tool_total_calls


def _classify_innovations(
    tool_spokes_map: dict[str, list[str]],
    tool_total_calls: dict[str, int],
    candidate_threshold: int,
) -> list[dict[str, Any]]:
    """Classify and deterministically sort domain innovation candidates for Hub ingestion."""
    innovations: list[dict[str, Any]] = []
    for tool_name, total_calls in tool_total_calls.items():
        spoke_sources = tool_spokes_map.get(tool_name, [])
        is_candidate = total_calls >= candidate_threshold or len(spoke_sources) >= 2
        promotion_status = (
            "Candidate for Hub Ingestion" if is_candidate else "Spoke Local Innovation"
        )
        recommendation = (
            "Recommend promoting to Hub Monorepo via ADR-0045 / ADR-0046 proposal "
            "(.agents/proposals/TEMPLATE.md)"
            if is_candidate
            else "Retain as Spoke local innovation until cross-project demand emerges"
        )
        innovations.append(
            {
                "tool_or_skill": tool_name,
                "total_calls": total_calls,
                "source_spokes": spoke_sources,
                "category": "Domain Innovation",
                "promotion_status": promotion_status,
                "recommendation": recommendation,
            }
        )
    innovations.sort(key=lambda x: (-x["total_calls"], x["tool_or_skill"]))
    return innovations


def _format_fleet_markdown_summary(report: FleetTelemetryReport) -> list[str]:
    """Render Markdown sections 1 & 2 (Fleet rollup and domain distribution)."""
    lines = [
        f"# 🌐 CCBA Fleet-Wide Cross-Spoke Telemetry Report: `{report.hub_name}`",
        "",
        "## 1. Enterprise Fleet Rollup",
        "",
        f"- **Total Registered Spokes:** {report.total_spokes} ({report.online_spokes} Online)",
        f"- **Total Fleet Tokens Consumed:** {report.total_fleet_tokens:,}",
        f"- **Total Prompt Tokens (Context):** {report.total_prompt_tokens:,}",
        f"- **Total Completion Tokens (Gen):** {report.total_completion_tokens:,}",
        f"- **Total Fleet Cost:** ${report.total_fleet_cost_usd:.4f} USD",
        "",
        "## 2. Project Distribution by Domain",
        "",
    ]
    for p_type, count in sorted(report.spokes_by_type.items()):
        lines.append(f"- **{p_type}:** {count} project(s)")
    return lines


def _format_fleet_markdown_spokes(report: FleetTelemetryReport) -> list[str]:
    """Render Markdown section 3 (Spoke comparison matrix)."""
    lines = [
        "",
        "## 3. Spoke Comparison Matrix",
        "",
        "| Project Name | Domain | Status | Sessions | Tokens Consumed | Cost (USD) | Budget Status |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for s in sorted(report.spokes, key=lambda x: (-x.total_tokens, x.project_name)):
        status_badge = "Online" if s.is_online else "Offline"
        lines.append(
            f"| `{s.project_name}` | {s.project_type} | {status_badge} | {s.total_sessions} | "
            f"{s.total_tokens:,} | ${s.total_cost_usd:.4f} | {s.budget_status} |"
        )
    return lines


def _format_fleet_markdown_innovations(report: FleetTelemetryReport) -> list[str]:
    """Render Markdown section 4 (Top Spoke innovations table)."""
    lines = [
        "",
        "## 4. Top Spoke Innovations & Candidates for Hub Ingestion (ADR-0045, ADR-0046)",
        "",
        "| Tool / Custom Skill | Invocations | Source Spokes | Status | Recommendation |",
        "| :--- | :---: | :--- | :---: | :--- |",
    ]
    innovations = report.get_top_spoke_innovations()
    if not innovations:
        lines.append(
            "| _None_ | 0 | _No Spoke-local domain innovations detected_ | Compliant | Retain standard catalog |"
        )
        return lines
    for item in innovations:
        spokes_str = ", ".join(item["source_spokes"])
        lines.append(
            f"| `{item['tool_or_skill']}` | {item['total_calls']} | {spokes_str} | "
            f"{item['promotion_status']} | {item['recommendation']} |"
        )
    return lines


@dataclass
class FleetTelemetryReport:
    """Aggregated enterprise fleet telemetry report across multiple Spoke projects."""

    hub_name: str
    spokes: list[SpokeTelemetrySummary] = field(default_factory=list)
    total_spokes: int = 0
    online_spokes: int = 0
    total_fleet_tokens: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_fleet_cost_usd: float = 0.0
    spokes_by_type: dict[str, int] = field(default_factory=dict)
    fleet_tool_counts: dict[str, int] = field(default_factory=dict)
    top_spoke_innovations: list[dict[str, Any]] = field(default_factory=list)

    def get_top_spoke_innovations(self, candidate_threshold: int = 5) -> list[dict[str, Any]]:
        """Extract, rank, and classify cross-spoke tools and local innovations (ADR-0045, ADR-0046)."""
        tool_spokes_map, tool_total_calls = _collect_tool_innovations(
            self.spokes, self.fleet_tool_counts
        )
        return _classify_innovations(tool_spokes_map, tool_total_calls, candidate_threshold)

    def to_dict(self) -> dict[str, Any]:
        """Convert fleet report to serializable dictionary."""
        return {
            "hub_name": self.hub_name,
            "total_spokes": self.total_spokes,
            "online_spokes": self.online_spokes,
            "total_fleet_tokens": self.total_fleet_tokens,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_fleet_cost_usd": round(self.total_fleet_cost_usd, 4),
            "spokes_by_type": self.spokes_by_type,
            "fleet_tool_counts": self.fleet_tool_counts,
            "top_spoke_innovations": self.get_top_spoke_innovations(),
            "spokes": [s.to_dict() for s in self.spokes],
        }

    def to_markdown(self) -> str:
        """Format fleet report into clean GitHub-flavored Markdown."""
        lines = [
            *_format_fleet_markdown_summary(self),
            *_format_fleet_markdown_spokes(self),
            *_format_fleet_markdown_innovations(self),
        ]
        return "\n".join(lines).strip() + "\n"


def _resolve_budget_status(tot_tok: int, budget_limit: int) -> str:
    """Resolve Compliant / Warning / Exceeded status for a token total vs budget."""
    if tot_tok > budget_limit:
        return "Exceeded"
    if tot_tok > (budget_limit * 0.8):
        return "Warning"
    return "Compliant"


def _parse_summary_json(
    summary_file: Path,
    meta: tuple[str, str, str, str, bool, str],
) -> SpokeTelemetrySummary | None:
    """Parse pre-compiled `.md/data/telemetry_summary.json` into a SpokeTelemetrySummary."""
    spoke_id, project_name, project_path_str, project_type, is_sandbox, last_sync = meta
    try:
        data = json.loads(summary_file.read_text(encoding="utf-8"))
        tot_tok = int(data.get("total_tokens", 0))
        b_limit = int(data.get("budget_limit_tokens", DEFAULT_SPOKE_BUDGET_TOKENS))
        return SpokeTelemetrySummary(
            spoke_id=spoke_id,
            project_name=project_name,
            project_path=project_path_str,
            project_type=project_type,
            is_sandbox=is_sandbox,
            is_online=True,
            last_sync=last_sync,
            total_sessions=int(data.get("total_sessions", 1)),
            total_tokens=tot_tok,
            prompt_tokens=int(data.get("prompt_tokens", 0)),
            completion_tokens=int(data.get("completion_tokens", 0)),
            total_cost_usd=float(data.get("total_cost_usd", 0.0)),
            tool_counts=data.get("tool_counts", {}),
            budget_limit_tokens=b_limit,
            budget_status=_resolve_budget_status(tot_tok, b_limit),
        )
    except Exception:
        return None


def _parse_swarm_dashboard_html(
    report_html: Path,
    meta: tuple[str, str, str, str, bool, str],
) -> SpokeTelemetrySummary | None:
    """Extract sanitized JSON metrics embedded in `.md/reports/swarm_telemetry_dashboard.html`."""
    spoke_id, project_name, project_path_str, project_type, is_sandbox, last_sync = meta
    try:
        content = report_html.read_text(encoding="utf-8")
        marker_start = '<script id="telemetry-data" type="application/json">'
        marker_end = "</script>"
        if marker_start not in content or marker_end not in content:
            return None
        s_idx = content.index(marker_start) + len(marker_start)
        e_idx = content.index(marker_end, s_idx)
        parsed = json.loads(content[s_idx:e_idx].strip())
        swarm_tools: dict[str, int] = {}
        for sub in parsed.get("subagents", []):
            for t_name, count in sub.get("tool_counts", {}).items():
                swarm_tools[t_name] = swarm_tools.get(t_name, 0) + count
        tot_tok = int(parsed.get("total_swarm_tokens", 0))
        b_limit = DEFAULT_SPOKE_BUDGET_TOKENS
        return SpokeTelemetrySummary(
            spoke_id=spoke_id,
            project_name=project_name,
            project_path=project_path_str,
            project_type=project_type,
            is_sandbox=is_sandbox,
            is_online=True,
            last_sync=last_sync,
            total_sessions=max(1, int(parsed.get("total_subagents", 1))),
            total_tokens=tot_tok,
            prompt_tokens=int(parsed.get("total_prompt_tokens", 0)),
            completion_tokens=int(parsed.get("total_completion_tokens", 0)),
            total_cost_usd=float(parsed.get("total_cost_usd", 0.0)),
            tool_counts=swarm_tools,
            budget_limit_tokens=b_limit,
            budget_status=_resolve_budget_status(tot_tok, b_limit),
        )
    except Exception:
        return None


def scan_spoke_telemetry(spoke_dict: dict[str, Any]) -> SpokeTelemetrySummary:
    """Scan and safely extract sanitized telemetry from a single Spoke (ADR-0046)."""
    project_name = str(spoke_dict.get("name", "Unknown Spoke"))
    project_path_str = str(spoke_dict.get("path", ""))
    project_type = str(spoke_dict.get("project_type", "Chưa phân loại"))
    last_sync = str(spoke_dict.get("last_sync", ""))
    is_sandbox = bool(spoke_dict.get("is_sandbox", False))
    spoke_id = str(spoke_dict.get("spoke_id", ""))
    meta = (spoke_id, project_name, project_path_str, project_type, is_sandbox, last_sync)

    p = Path(project_path_str)
    if not p.exists() or not p.is_dir():
        return SpokeTelemetrySummary(
            spoke_id=spoke_id,
            project_name=project_name,
            project_path=project_path_str,
            project_type=project_type,
            is_sandbox=is_sandbox,
            is_online=False,
            last_sync=last_sync,
            budget_status="Offline / Cached",
        )

    summary_file = p / ".md" / "data" / "telemetry_summary.json"
    if summary_file.exists():
        parsed_summary = _parse_summary_json(summary_file, meta)
        if parsed_summary is not None:
            return parsed_summary

    report_html = p / ".md" / "reports" / "swarm_telemetry_dashboard.html"
    if report_html.exists():
        parsed_html = _parse_swarm_dashboard_html(report_html, meta)
        if parsed_html is not None:
            return parsed_html

    return SpokeTelemetrySummary(
        spoke_id=spoke_id,
        project_name=project_name,
        project_path=project_path_str,
        project_type=project_type,
        is_sandbox=is_sandbox,
        is_online=True,
        last_sync=last_sync,
        budget_status="Compliant",
    )


def _load_registered_spokes(
    root: Path,
    spokes_list: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Resolve spoke metadata list either from explicit override or encrypted registry."""
    if spokes_list is not None:
        return spokes_list
    try:
        from scripts.spoke.decrypt_spoke_registry import get_registered_spokes

        return get_registered_spokes(root)
    except Exception:
        return []


def aggregate_fleet_telemetry(
    hub_root: Path | None = None,
    spokes_list: list[dict[str, Any]] | None = None,
) -> FleetTelemetryReport:
    """Aggregate telemetry figures across the entire enterprise Spoke fleet."""
    root = hub_root or Path.cwd()
    registered = _load_registered_spokes(root, spokes_list)
    summaries: list[SpokeTelemetrySummary] = []
    spokes_by_type: dict[str, int] = {}
    fleet_tools: dict[str, int] = {}

    for s_info in registered:
        summary = scan_spoke_telemetry(s_info)
        summaries.append(summary)
        p_type = summary.project_type or "Chưa phân loại"
        spokes_by_type[p_type] = spokes_by_type.get(p_type, 0) + 1
        for t_name, count in summary.tool_counts.items():
            fleet_tools[t_name] = fleet_tools.get(t_name, 0) + count

    report = FleetTelemetryReport(
        hub_name=root.name,
        spokes=summaries,
        total_spokes=len(summaries),
        online_spokes=sum(1 for s in summaries if s.is_online),
        total_fleet_tokens=sum(s.total_tokens for s in summaries),
        total_prompt_tokens=sum(s.prompt_tokens for s in summaries),
        total_completion_tokens=sum(s.completion_tokens for s in summaries),
        total_fleet_cost_usd=sum(s.total_cost_usd for s in summaries),
        spokes_by_type=spokes_by_type,
        fleet_tool_counts=fleet_tools,
    )
    report.top_spoke_innovations = report.get_top_spoke_innovations()
    return report
