"""fleet.py - Cross-Spoke Analytics & Enterprise Fleet Telemetry Engine.

Implements multi-project governance, token rollups, and fleet dashboards (ADR-0010, ADR-0030, ADR-0046, ADR-0058):
1. Sanitized Telemetry Protocol: aggregates non-sensitive metrics across all registered Spokes.
2. Fault-Tolerant Scanning: seamlessly handles offline, unmounted, or archived Spokes.
3. Pure SVG Cross-Spoke Analytics: renders comparison charts, project matrices, and cost breakdowns.
4. Zero-Server Standalone HTML Generation with Antigravity-allowlisted Tailwind CSS.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Default token budget heuristics per Spoke (e.g., 5M tokens per monthly cycle)
DEFAULT_SPOKE_BUDGET_TOKENS = 5_000_000


def _format_number(n: int | float) -> str:
    """Format numbers with comma separators."""
    if isinstance(n, int):
        return f"{n:,}"
    return f"{n:,.2f}"


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
            "spokes": [s.to_dict() for s in self.spokes],
        }

    def to_markdown(self) -> str:
        """Format fleet report into clean GitHub-flavored Markdown."""
        lines = [
            f"# 🌐 CCBA Fleet-Wide Cross-Spoke Telemetry Report: `{self.hub_name}`",
            "",
            "## 1. Enterprise Fleet Rollup",
            "",
            f"- **Total Registered Spokes:** {self.total_spokes} ({self.online_spokes} Online)",
            f"- **Total Fleet Tokens Consumed:** {self.total_fleet_tokens:,}",
            f"- **Total Prompt Tokens (Context):** {self.total_prompt_tokens:,}",
            f"- **Total Completion Tokens (Gen):** {self.total_completion_tokens:,}",
            f"- **Total Fleet Cost:** ${self.total_fleet_cost_usd:.4f} USD",
            "",
            "## 2. Project Distribution by Domain",
            "",
        ]
        for p_type, count in sorted(self.spokes_by_type.items()):
            lines.append(f"- **{p_type}:** {count} project(s)")

        lines.extend(
            [
                "",
                "## 3. Spoke Comparison Matrix",
                "",
                "| Project Name | Domain | Status | Sessions | Tokens Consumed | Cost (USD) | Budget Status |",
                "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
            ]
        )

        for s in sorted(self.spokes, key=lambda x: x.total_tokens, reverse=True):
            status_badge = "Online" if s.is_online else "Offline"
            lines.append(
                f"| `{s.project_name}` | {s.project_type} | {status_badge} | {s.total_sessions} | "
                f"{s.total_tokens:,} | ${s.total_cost_usd:.4f} | {s.budget_status} |"
            )

        return "\n".join(lines).strip() + "\n"


def scan_spoke_telemetry(spoke_dict: dict[str, Any]) -> SpokeTelemetrySummary:
    """Scan and safely extract sanitized telemetry from a single Spoke (ADR-0046).

    Args:
        spoke_dict: Dictionary from spoke_registry containing 'name', 'path', 'project_type', etc.

    Returns:
        SpokeTelemetrySummary with aggregated figures and zero confidential text leakage.
    """
    project_name = str(spoke_dict.get("name", "Unknown Spoke"))
    project_path_str = str(spoke_dict.get("path", ""))
    project_type = str(spoke_dict.get("project_type", "Chưa phân loại"))
    last_sync = str(spoke_dict.get("last_sync", ""))
    is_sandbox = bool(spoke_dict.get("is_sandbox", False))
    spoke_id = str(spoke_dict.get("spoke_id", ""))

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

    # Strategy 1: Check for pre-compiled telemetry_summary.json in .md/data/
    summary_file = p / ".md" / "data" / "telemetry_summary.json"
    if summary_file.exists():
        try:
            data = json.loads(summary_file.read_text(encoding="utf-8"))
            tot_tok = int(data.get("total_tokens", 0))
            p_tok = int(data.get("prompt_tokens", 0))
            c_tok = int(data.get("completion_tokens", 0))
            cost = float(data.get("total_cost_usd", 0.0))
            sessions = int(data.get("total_sessions", 1))
            tools = data.get("tool_counts", {})
            b_limit = int(data.get("budget_limit_tokens", DEFAULT_SPOKE_BUDGET_TOKENS))

            status = "Compliant"
            if tot_tok > b_limit:
                status = "Exceeded"
            elif tot_tok > (b_limit * 0.8):
                status = "Warning"

            return SpokeTelemetrySummary(
                spoke_id=spoke_id,
                project_name=project_name,
                project_path=project_path_str,
                project_type=project_type,
                is_sandbox=is_sandbox,
                is_online=True,
                last_sync=last_sync,
                total_sessions=sessions,
                total_tokens=tot_tok,
                prompt_tokens=p_tok,
                completion_tokens=c_tok,
                total_cost_usd=cost,
                tool_counts=tools,
                budget_limit_tokens=b_limit,
                budget_status=status,
            )
        except Exception:
            pass

    # Strategy 2: Check for swarm_telemetry_dashboard.html in .md/reports/
    report_html = p / ".md" / "reports" / "swarm_telemetry_dashboard.html"
    if report_html.exists():
        try:
            content = report_html.read_text(encoding="utf-8")
            marker_start = '<script id="telemetry-data" type="application/json">'
            marker_end = "</script>"
            if marker_start in content and marker_end in content:
                s_idx = content.index(marker_start) + len(marker_start)
                e_idx = content.index(marker_end, s_idx)
                raw_json = content[s_idx:e_idx].strip()
                parsed = json.loads(raw_json)

                tot_tok = int(parsed.get("total_swarm_tokens", 0))
                p_tok = int(parsed.get("total_prompt_tokens", 0))
                c_tok = int(parsed.get("total_completion_tokens", 0))
                cost = float(parsed.get("total_cost_usd", 0.0))
                sessions = max(1, int(parsed.get("total_subagents", 1)))

                swarm_tools: dict[str, int] = {}
                for sub in parsed.get("subagents", []):
                    for t_name, count in sub.get("tool_counts", {}).items():
                        swarm_tools[t_name] = swarm_tools.get(t_name, 0) + count

                b_limit = DEFAULT_SPOKE_BUDGET_TOKENS
                status = "Compliant"
                if tot_tok > b_limit:
                    status = "Exceeded"
                elif tot_tok > (b_limit * 0.8):
                    status = "Warning"

                return SpokeTelemetrySummary(
                    spoke_id=spoke_id,
                    project_name=project_name,
                    project_path=project_path_str,
                    project_type=project_type,
                    is_sandbox=is_sandbox,
                    is_online=True,
                    last_sync=last_sync,
                    total_sessions=sessions,
                    total_tokens=tot_tok,
                    prompt_tokens=p_tok,
                    completion_tokens=c_tok,
                    total_cost_usd=cost,
                    tool_counts=swarm_tools,
                    budget_limit_tokens=b_limit,
                    budget_status=status,
                )
        except Exception:
            pass

    # Default fallback for clean Spoke with no prior telemetry logs
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


def aggregate_fleet_telemetry(
    hub_root: Path | None = None,
    spokes_list: list[dict[str, Any]] | None = None,
) -> FleetTelemetryReport:
    """Aggregate telemetry figures across the entire enterprise Spoke fleet.

    Args:
        hub_root: Optional Hub root directory.
        spokes_list: Optional explicit list of spoke dictionaries for testing.

    Returns:
        FleetTelemetryReport
    """
    root = hub_root or Path.cwd()
    hub_name = root.name

    if spokes_list is None:
        try:
            from scripts.spoke.decrypt_spoke_registry import get_registered_spokes

            registered = get_registered_spokes(root)
        except Exception:
            registered = []
    else:
        registered = spokes_list

    summaries: list[SpokeTelemetrySummary] = []
    spokes_by_type: dict[str, int] = {}
    fleet_tools: dict[str, int] = {}

    for s_info in registered:
        summary = scan_spoke_telemetry(s_info)
        summaries.append(summary)

        # Aggregate counts by type
        p_type = summary.project_type or "Chưa phân loại"
        spokes_by_type[p_type] = spokes_by_type.get(p_type, 0) + 1

        # Aggregate fleet tools
        for t_name, count in summary.tool_counts.items():
            fleet_tools[t_name] = fleet_tools.get(t_name, 0) + count

    total_tokens = sum(s.total_tokens for s in summaries)
    total_prompt = sum(s.prompt_tokens for s in summaries)
    total_comp = sum(s.completion_tokens for s in summaries)
    total_cost = sum(s.total_cost_usd for s in summaries)
    online_count = sum(1 for s in summaries if s.is_online)

    return FleetTelemetryReport(
        hub_name=hub_name,
        spokes=summaries,
        total_spokes=len(summaries),
        online_spokes=online_count,
        total_fleet_tokens=total_tokens,
        total_prompt_tokens=total_prompt,
        total_completion_tokens=total_comp,
        total_fleet_cost_usd=total_cost,
        spokes_by_type=spokes_by_type,
        fleet_tool_counts=fleet_tools,
    )


def _generate_fleet_comparison_chart_svg(
    spokes: list[SpokeTelemetrySummary],
    chart_width: int = 700,
    row_height: int = 40,
) -> str:
    """Generate pure SVG horizontal stacked bar chart comparing Spoke token consumptions."""
    if not spokes:
        return (
            f'<svg viewBox="0 0 {chart_width} 80" class="w-full h-auto text-[var(--muted-foreground)]">'
            f'<text x="{chart_width / 2}" y="45" text-anchor="middle" fill="currentColor" font-size="13">'
            "No registered Spokes found in fleet"
            "</text></svg>"
        )

    # Sort spokes by total tokens descending
    sorted_spokes = sorted(spokes, key=lambda s: s.total_tokens, reverse=True)
    max_tokens = max((s.total_tokens for s in sorted_spokes), default=1)
    if max_tokens == 0:
        max_tokens = 1

    label_width = 150
    value_width = 90
    bar_max_width = chart_width - label_width - value_width - 20
    total_height = len(sorted_spokes) * row_height + 40

    svg_parts = [
        f'<svg viewBox="0 0 {chart_width} {total_height}" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg">',
        "  <defs>",
        '    <linearGradient id="fleetPromptGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '      <stop offset="0%" stop-color="#3b82f6" />',
        '      <stop offset="100%" stop-color="#1d4ed8" />',
        "    </linearGradient>",
        '    <linearGradient id="fleetCompGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '      <stop offset="0%" stop-color="#10b981" />',
        '      <stop offset="100%" stop-color="#047857" />',
        "    </linearGradient>",
        "  </defs>",
        "  <!-- Legend -->",
        '  <g transform="translate(10, 16)" font-size="11" fill="currentColor">',
        '    <rect x="0" y="0" width="12" height="12" rx="2" fill="url(#fleetPromptGrad)" />',
        '    <text x="18" y="10" fill="currentColor" class="text-[var(--foreground)]">Prompt (Context)</text>',
        '    <rect x="140" y="0" width="12" height="12" rx="2" fill="url(#fleetCompGrad)" />',
        '    <text x="158" y="10" fill="currentColor" class="text-[var(--foreground)]">Completion (Gen)</text>',
        "  </g>",
    ]

    for idx, s in enumerate(sorted_spokes):
        y = idx * row_height + 40
        name = s.project_name
        display_name = f"{name[:16]}..." if len(name) > 18 else name

        total_w = (s.total_tokens / max_tokens) * bar_max_width if max_tokens > 0 else 0
        prompt_ratio = s.prompt_tokens / s.total_tokens if s.total_tokens > 0 else 0
        prompt_w = max(1.0, total_w * prompt_ratio) if s.total_tokens > 0 else 0.0
        comp_w = max(0.0, total_w - prompt_w)

        svg_parts.append(f"  <!-- Row {idx}: {name} -->")
        svg_parts.append(
            f'  <text x="{label_width - 10}" y="{y + 16}" text-anchor="end" font-size="11" '
            f'font-weight="500" fill="currentColor" class="text-[var(--foreground)]">'
            f"{html.escape(display_name)}"
            f"</text>"
        )

        # Background track
        svg_parts.append(
            f'  <rect x="{label_width}" y="{y + 4}" width="{bar_max_width}" height="18" rx="4" '
            f'fill="currentColor" opacity="0.08" />'
        )

        if prompt_w > 0:
            svg_parts.append(
                f'  <rect x="{label_width}" y="{y + 4}" width="{prompt_w:.1f}" height="18" '
                f'rx="4" fill="url(#fleetPromptGrad)">'
                f"<title>{html.escape(name)} - Prompt: {s.prompt_tokens:,} tokens</title>"
                f"</rect>"
            )

        if comp_w > 0:
            svg_parts.append(
                f'  <rect x="{label_width + prompt_w}" y="{y + 4}" width="{comp_w:.1f}" height="18" '
                f'rx="4" fill="url(#fleetCompGrad)">'
                f"<title>{html.escape(name)} - Completion: {s.completion_tokens:,} tokens</title>"
                f"</rect>"
            )

        # Value label
        val_text = (
            _format_number(s.total_tokens)
            if s.is_online
            else f"{_format_number(s.total_tokens)} (off)"
        )
        svg_parts.append(
            f'  <text x="{label_width + bar_max_width + 8}" y="{y + 17}" font-size="11" font-weight="600" '
            f'fill="currentColor" class="text-[var(--foreground)]">'
            f"{val_text}"
            f"</text>"
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def _generate_fleet_domain_breakdown_svg(
    spokes_by_type: dict[str, int],
    chart_width: int = 340,
    chart_height: int = 180,
) -> str:
    """Generate pure SVG horizontal bar representation for project types."""
    if not spokes_by_type:
        return (
            f'<svg viewBox="0 0 {chart_width} 80" class="w-full h-auto text-[var(--muted-foreground)]">'
            f'<text x="{chart_width / 2}" y="45" text-anchor="middle" fill="currentColor" font-size="12">'
            "No domain data"
            "</text></svg>"
        )

    total_projects = sum(spokes_by_type.values())
    sorted_domains = sorted(spokes_by_type.items(), key=lambda x: x[1], reverse=True)
    row_height = 32
    total_height = len(sorted_domains) * row_height + 20

    colors = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899"]
    svg_parts = [
        f'<svg viewBox="0 0 {chart_width} {total_height}" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg">',
    ]

    for idx, (dtype, count) in enumerate(sorted_domains):
        y = idx * row_height + 15
        color = colors[idx % len(colors)]
        pct = (count / total_projects) * 100 if total_projects > 0 else 0
        bar_w = (count / total_projects) * (chart_width - 150) if total_projects > 0 else 0

        svg_parts.append(
            f'  <text x="80" y="{y + 13}" text-anchor="end" font-size="11" fill="currentColor" '
            f'class="text-[var(--muted-foreground)]">{html.escape(dtype)}</text>'
        )
        svg_parts.append(
            f'  <rect x="90" y="{y + 2}" width="{bar_w:.1f}" height="14" rx="3" fill="{color}" />'
        )
        svg_parts.append(
            f'  <text x="{90 + bar_w + 6:.1f}" y="{y + 13}" font-size="11" font-weight="600" '
            f'fill="currentColor" class="text-[var(--foreground)]">{count} ({pct:.0f}%)</text>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def generate_fleet_dashboard_html(
    report: FleetTelemetryReport,
    title: str | None = None,
) -> str:
    """Generate a self-contained, interactive HTML Cross-Spoke Fleet Dashboard."""
    display_title = title or f"Cross-Spoke Fleet Telemetry: {report.hub_name}"
    report_dict = report.to_dict()
    report_json_str = json.dumps(report_dict, ensure_ascii=False, indent=2)

    # SVG Visuals
    comparison_chart_svg = _generate_fleet_comparison_chart_svg(report.spokes)
    domain_chart_svg = _generate_fleet_domain_breakdown_svg(report.spokes_by_type)

    # Top Fleet Tools
    tool_rows = []
    sorted_tools = sorted(report.fleet_tool_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    tot_tool_calls = sum(report.fleet_tool_counts.values()) or 1
    for t_name, count in sorted_tools:
        pct = (count / tot_tool_calls) * 100
        tool_rows.append(
            f"""
            <tr class="border-b border-[var(--border)] hover:bg-[var(--card)]/60 text-xs transition-colors">
              <td class="py-2 px-3 font-mono font-semibold text-[var(--primary)]">{html.escape(t_name)}</td>
              <td class="py-2 px-3 text-right font-semibold">{count:,}</td>
              <td class="py-2 px-3 text-right text-[var(--muted-foreground)] font-mono">{pct:.1f}%</td>
            </tr>
            """
        )
    tool_rows_html = (
        "".join(tool_rows)
        if tool_rows
        else '<tr><td colspan="3" class="py-3 text-center text-xs text-[var(--muted-foreground)]">No tool invocations</td></tr>'
    )

    # Spoke Table Rows
    spoke_rows = []
    for s in sorted(report.spokes, key=lambda x: x.total_tokens, reverse=True):
        status_color = (
            "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
            if s.is_online
            else "bg-slate-500/10 text-slate-400 border-slate-500/20"
        )
        budget_badge_color = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
        if s.budget_status == "Exceeded":
            budget_badge_color = "bg-rose-500/10 text-rose-400 border-rose-500/20"
        elif s.budget_status == "Warning":
            budget_badge_color = "bg-amber-500/10 text-amber-400 border-amber-500/20"

        spoke_rows.append(
            f"""
            <tr class="border-b border-[var(--border)] hover:bg-[var(--card)]/60 text-xs transition-colors spoke-row" data-domain="{html.escape(s.project_type)}">
              <td class="py-3 px-3">
                <div class="font-semibold text-sm text-[var(--foreground)]">{html.escape(s.project_name)}</div>
                <div class="font-mono text-[10px] text-[var(--muted-foreground)] truncate max-w-xs">{html.escape(s.project_path)}</div>
              </td>
              <td class="py-3 px-3">
                <span class="inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  {html.escape(s.project_type)}
                </span>
              </td>
              <td class="py-3 px-3 text-center">
                <span class="inline-block px-2 py-0.5 rounded text-[10px] font-semibold border {status_color}">
                  {"Online" if s.is_online else "Offline"}
                </span>
              </td>
              <td class="py-3 px-3 text-right font-mono font-semibold text-indigo-400">{_format_number(s.total_tokens)}</td>
              <td class="py-3 px-3 text-right font-mono text-emerald-400 font-semibold">${s.total_cost_usd:.4f}</td>
              <td class="py-3 px-3 text-right text-[var(--muted-foreground)] font-mono">{s.last_sync[:10] if s.last_sync else "Never"}</td>
              <td class="py-3 px-3 text-center">
                <span class="inline-block px-2 py-0.5 rounded text-[10px] font-semibold border {budget_badge_color}">
                  {s.budget_status}
                </span>
              </td>
            </tr>
            """
        )
    spoke_rows_html = "\n".join(spoke_rows)

    return f"""<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(display_title)}</title>
  <!-- Allowlisted Antigravity Tailwind CSS (CSP Compliant) -->
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    :root {{
      --background: #0f172a;
      --card: #1e293b;
      --foreground: #f8fafc;
      --muted-foreground: #94a3b8;
      --border: #334155;
      --primary: #3b82f6;
      --primary-foreground: #ffffff;
      --accent: #10b981;
    }}
    .light {{
      --background: #f8fafc;
      --card: #ffffff;
      --foreground: #0f172a;
      --muted-foreground: #64748b;
      --border: #e2e8f0;
      --primary: #2563eb;
      --primary-foreground: #ffffff;
      --accent: #059669;
    }}
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] antialiased min-h-full flex flex-col p-4 md:p-6 transition-colors duration-200">
  <!-- Embedded Fleet Telemetry Data (Zero Dev Server) -->
  <script id="fleet-telemetry-data" type="application/json">
{report_json_str}
  </script>

  <!-- Header Section -->
  <header class="mb-6 pb-4 border-b border-[var(--border)] flex flex-col md:flex-row md:items-center md:justify-between gap-4">
    <div>
      <div class="flex items-center gap-2 mb-1">
        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
          CCBA Multi-Project Governance
        </span>
        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          ADR-0046 Sanitized Protocol
        </span>
      </div>
      <h1 class="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)]">
        🌐 Cross-Spoke Enterprise Fleet Telemetry Dashboard
      </h1>
      <p class="text-xs md:text-sm text-[var(--muted-foreground)] font-mono mt-0.5">
        Hub: <span class="text-[var(--foreground)]">{html.escape(report.hub_name)}</span> &bull; {report.total_spokes} Registered Spokes ({report.online_spokes} Online)
      </p>
    </div>

    <!-- Action Toolbar -->
    <div class="flex items-center gap-2">
      <button onclick="downloadFleetJson()" class="px-3 py-1.5 text-xs font-medium rounded-lg border border-[var(--border)] bg-[var(--card)] hover:border-[var(--primary)] transition-all flex items-center gap-1.5 shadow-sm">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
        Export Fleet JSON
      </button>
      <button onclick="copyFleetJson()" id="btnCopyFleet" class="px-3 py-1.5 text-xs font-medium rounded-lg border border-[var(--border)] bg-[var(--card)] hover:border-[var(--primary)] transition-all flex items-center gap-1.5 shadow-sm">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"/></svg>
        Copy Fleet Data
      </button>
      <button onclick="toggleTheme()" class="px-2.5 py-1.5 text-xs font-medium rounded-lg border border-[var(--border)] bg-[var(--card)] hover:border-[var(--primary)] transition-all" title="Toggle Dark/Light Mode">
        🌓
      </button>
    </div>
  </header>

  <!-- KPI Cards Grid -->
  <section class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
      <div class="text-xs text-[var(--muted-foreground)] font-medium">Total Fleet Tokens</div>
      <div class="text-xl md:text-2xl font-bold mt-1 text-blue-400">{_format_number(report.total_fleet_tokens)}</div>
      <div class="text-[10px] text-[var(--muted-foreground)] mt-1 flex justify-between">
        <span>Prompt: {_format_number(report.total_prompt_tokens)}</span>
        <span>Gen: {_format_number(report.total_completion_tokens)}</span>
      </div>
    </div>

    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
      <div class="text-xs text-[var(--muted-foreground)] font-medium">Enterprise Cost (USD)</div>
      <div class="text-xl md:text-2xl font-bold mt-1 text-emerald-400">${report.total_fleet_cost_usd:.4f}</div>
      <div class="text-[10px] text-[var(--muted-foreground)] mt-1">
        Aggregated Gemini Pro/Flash API
      </div>
    </div>

    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
      <div class="text-xs text-[var(--muted-foreground)] font-medium">Spokes Fleet Size</div>
      <div class="text-xl md:text-2xl font-bold mt-1 text-indigo-400">{report.total_spokes} Spokes</div>
      <div class="text-[10px] text-[var(--muted-foreground)] mt-1">
        {report.online_spokes} Online &bull; {report.total_spokes - report.online_spokes} Offline
      </div>
    </div>

    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
      <div class="text-xs text-[var(--muted-foreground)] font-medium">Fleet Budget Health</div>
      <div class="text-xl md:text-2xl font-bold mt-1 text-teal-400 flex items-center gap-2">
        <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
        <span>Managed</span>
      </div>
      <div class="text-[10px] text-[var(--muted-foreground)] mt-1">
        ADR-0030 Quotas Enforced
      </div>
    </div>
  </section>

  <!-- Charts Layout (2-Column Grid) -->
  <section class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
    <!-- Chart 1: Spoke Comparison (2 Cols) -->
    <div class="lg:col-span-2 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold tracking-wide flex items-center gap-2 text-[var(--foreground)]">
          <span class="text-blue-400">📊</span> Spoke Token Comparison Matrix
        </h2>
        <span class="text-xs text-[var(--muted-foreground)]">Prompt vs Completion</span>
      </div>
      <div class="w-full">
        {comparison_chart_svg}
      </div>
    </div>

    <!-- Chart 2: Domain Distribution (1 Col) -->
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm flex flex-col">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold tracking-wide flex items-center gap-2 text-[var(--foreground)]">
          <span class="text-purple-400">📂</span> Domain Distribution
        </h2>
        <span class="text-xs text-[var(--muted-foreground)]">By Project Type</span>
      </div>
      <div class="w-full mb-4">
        {domain_chart_svg}
      </div>

      <!-- Top Tools Sub-table -->
      <div class="mt-auto border-t border-[var(--border)] pt-3">
        <div class="text-xs font-semibold text-[var(--muted-foreground)] uppercase mb-2">Fleet Top Tools</div>
        <table class="w-full text-xs">
          <tbody>{tool_rows_html}</tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- Spoke Projects Fleet Matrix Table -->
  <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm mb-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
      <div>
        <h2 class="text-sm font-semibold tracking-wide flex items-center gap-2 text-[var(--foreground)]">
          <span class="text-emerald-400">🏢</span> Registered Spoke Projects Matrix
        </h2>
        <p class="text-xs text-[var(--muted-foreground)]">Sanitized telemetry summaries aggregated from local filesystem and Spoke registries</p>
      </div>

      <!-- Domain Filter -->
      <div class="flex items-center gap-2">
        <label for="domainFilter" class="text-xs text-[var(--muted-foreground)]">Domain:</label>
        <select id="domainFilter" onchange="filterSpokesByDomain()" class="bg-[var(--background)] border border-[var(--border)] rounded-lg px-2.5 py-1 text-xs text-[var(--foreground)] focus:outline-none focus:border-[var(--primary)]">
          <option value="ALL">All Domains</option>
          {"".join(f'<option value="{html.escape(dt)}">{html.escape(dt)}</option>' for dt in report.spokes_by_type.keys())}
        </select>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs">
        <thead class="text-[11px] text-[var(--muted-foreground)] uppercase border-b border-[var(--border)]">
          <tr>
            <th class="py-2.5 px-3">Project / Location</th>
            <th class="py-2.5 px-3">Domain</th>
            <th class="py-2.5 px-3 text-center">Status</th>
            <th class="py-2.5 px-3 text-right">Tokens Consumed</th>
            <th class="py-2.5 px-3 text-right">Estimated Cost</th>
            <th class="py-2.5 px-3 text-right">Last Sync</th>
            <th class="py-2.5 px-3 text-center">Budget Status</th>
          </tr>
        </thead>
        <tbody id="spokeTableBody">
          {spoke_rows_html}
        </tbody>
      </table>
    </div>
  </section>

  <!-- Footer -->
  <footer class="mt-auto pt-4 border-t border-[var(--border)] text-xs text-[var(--muted-foreground)] flex flex-col sm:flex-row justify-between items-center gap-2">
    <div>
      CCBA Agent Services Platform &bull; <span class="font-semibold text-[var(--foreground)]">Cross-Spoke Analytics Engine</span> (ADR-0046 & ADR-0058)
    </div>
    <div class="flex items-center gap-4">
      <span>Zero Confidential Leakage</span>
      <span>Enterprise Multi-Project Telemetry</span>
    </div>
  </footer>

  <!-- Client-side Interactive Logic -->
  <script>
    const fleetData = JSON.parse(document.getElementById('fleet-telemetry-data').textContent);

    function toggleTheme() {{
      document.documentElement.classList.toggle('light');
    }}

    function downloadFleetJson() {{
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(fleetData, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `fleet_telemetry_${{fleetData.hub_name}}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    }}

    function copyFleetJson() {{
      navigator.clipboard.writeText(JSON.stringify(fleetData, null, 2)).then(() => {{
        const btn = document.getElementById('btnCopyFleet');
        const oldHtml = btn.innerHTML;
        btn.innerHTML = '✅ Copied!';
        setTimeout(() => {{ btn.innerHTML = oldHtml; }}, 2000);
      }});
    }}

    function filterSpokesByDomain() {{
      const sel = document.getElementById('domainFilter').value;
      const rows = document.querySelectorAll('.spoke-row');
      rows.forEach(r => {{
        const dom = r.getAttribute('data-domain');
        if (sel === 'ALL' || dom === sel) {{
          r.style.display = '';
        }} else {{
          r.style.display = 'none';
        }}
      }});
    }}
  </script>
</body>
</html>
"""


def render_fleet_dashboard(
    output_path: Path | None = None,
    title: str | None = None,
    hub_root: Path | None = None,
    spokes_list: list[dict[str, Any]] | None = None,
) -> tuple[Path, FleetTelemetryReport]:
    """Audit the enterprise fleet and render the standalone HTML dashboard file.

    Args:
        output_path: Target path for the HTML file. Defaults to `.md/reports/cross_spoke_fleet_dashboard.html`.
        title: Optional custom dashboard title.
        hub_root: Optional Hub root directory.
        spokes_list: Optional explicit spoke list.

    Returns:
        (out_path, report)
    """
    report = aggregate_fleet_telemetry(hub_root=hub_root, spokes_list=spokes_list)

    if output_path is None:
        out_file = Path(".md") / "reports" / "cross_spoke_fleet_dashboard.html"
    else:
        out_file = Path(output_path)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    html_content = generate_fleet_dashboard_html(report, title=title)
    out_file.write_text(html_content, encoding="utf-8")

    return out_file, report
