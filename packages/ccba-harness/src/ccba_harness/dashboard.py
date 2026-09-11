"""dashboard.py - Interactive Swarm Telemetry Dashboard Generator.

Generates self-contained, zero-dependency HTML dashboards for Swarm Multi-Agent sessions (ADR-0030, ADR-0058):
1. Embeds OpenTelemetry and token metrics directly into static JSON payload.
2. Renders high-fidelity, resolution-independent Pure SVG charts (Token Bar Chart, Gantt Timeline, Tool Breakdown).
3. Uses Antigravity-allowlisted Tailwind CSS and host semantic theme variables.
4. Provides interactive Turn-by-Turn Trajectory Inspector and JSON Export capabilities.
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from .telemetry import (
    SubagentSessionMetrics,
    SwarmSessionTelemetryReport,
    audit_swarm_session,
    parse_iso_datetime,
)


def _format_number(n: int | float) -> str:
    """Format numbers with comma separators."""
    if isinstance(n, int):
        return f"{n:,}"
    return f"{n:,.2f}"


def _generate_token_bar_chart_svg(
    subagents: list[SubagentSessionMetrics],
    chart_width: int = 680,
    row_height: int = 38,
) -> str:
    """Generate a clean, pure SVG horizontal stacked bar chart for token consumption."""
    if not subagents:
        return (
            f'<svg viewBox="0 0 {chart_width} 80" class="w-full h-auto text-[var(--muted-foreground)]">'
            f'<text x="{chart_width / 2}" y="45" text-anchor="middle" fill="currentColor" font-size="13">'
            "No subagent token data available"
            "</text></svg>"
        )

    sorted_subs = sorted(subagents, key=lambda s: s.total_tokens, reverse=True)[:10]
    max_tokens = max((s.total_tokens for s in sorted_subs), default=1)
    if max_tokens == 0:
        max_tokens = 1

    label_width = 130
    value_width = 80
    bar_max_width = chart_width - label_width - value_width - 20
    total_height = len(sorted_subs) * row_height + 40

    svg_parts = [
        f'<svg viewBox="0 0 {chart_width} {total_height}" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg">',
        "  <defs>",
        '    <linearGradient id="promptGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '      <stop offset="0%" stop-color="#6366f1" />',
        '      <stop offset="100%" stop-color="#4f46e5" />',
        "    </linearGradient>",
        '    <linearGradient id="compGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '      <stop offset="0%" stop-color="#10b981" />',
        '      <stop offset="100%" stop-color="#059669" />',
        "    </linearGradient>",
        "  </defs>",
        "  <!-- Legend -->",
        '  <g transform="translate(10, 16)" font-size="11" fill="currentColor">',
        '    <rect x="0" y="0" width="12" height="12" rx="2" fill="url(#promptGrad)" />',
        '    <text x="18" y="10" fill="currentColor" class="text-[var(--foreground)]">Prompt (Context)</text>',
        '    <rect x="130" y="0" width="12" height="12" rx="2" fill="url(#compGrad)" />',
        '    <text x="148" y="10" fill="currentColor" class="text-[var(--foreground)]">Completion (Gen)</text>',
        "  </g>",
    ]

    for idx, s in enumerate(sorted_subs):
        y = idx * row_height + 40
        cid = s.conversation_id
        short_id = f"{cid[:8]}...{cid[-4:]}" if len(cid) > 16 else cid

        total_w = (s.total_tokens / max_tokens) * bar_max_width
        prompt_ratio = s.prompt_tokens / s.total_tokens if s.total_tokens > 0 else 0
        prompt_w = max(1.0, total_w * prompt_ratio) if s.total_tokens > 0 else 0.0
        comp_w = max(0.0, total_w - prompt_w)

        svg_parts.append(f"  <!-- Row {idx}: {cid} -->")
        svg_parts.append(
            f'  <text x="{label_width - 10}" y="{y + 16}" text-anchor="end" font-size="11" '
            f'font-family="monospace" fill="currentColor" class="text-[var(--muted-foreground)]">'
            f"{html.escape(short_id)}"
            f"</text>"
        )

        svg_parts.append(
            f'  <rect x="{label_width}" y="{y + 4}" width="{bar_max_width}" height="18" rx="4" '
            f'fill="currentColor" opacity="0.08" />'
        )

        if prompt_w > 0:
            svg_parts.append(
                f'  <rect x="{label_width}" y="{y + 4}" width="{prompt_w:.1f}" height="18" '
                f'rx="4" fill="url(#promptGrad)">'
                f"<title>{html.escape(cid)} - Prompt: {s.prompt_tokens:,} tokens</title>"
                f"</rect>"
            )

        if comp_w > 0:
            svg_parts.append(
                f'  <rect x="{label_width + prompt_w}" y="{y + 4}" width="{comp_w:.1f}" height="18" '
                f'rx="4" fill="url(#compGrad)">'
                f"<title>{html.escape(cid)} - Completion: {s.completion_tokens:,} tokens</title>"
                f"</rect>"
            )

        svg_parts.append(
            f'  <text x="{label_width + bar_max_width + 8}" y="{y + 17}" font-size="11" font-weight="600" '
            f'fill="currentColor" class="text-[var(--foreground)]">'
            f"{_format_number(s.total_tokens)}"
            f"</text>"
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def _generate_gantt_chart_svg(
    subagents: list[SubagentSessionMetrics],
    chart_width: int = 680,
    row_height: int = 42,
) -> str:
    """Generate a Gantt-style timeline visualization of subagents."""
    if not subagents:
        return (
            f'<svg viewBox="0 0 {chart_width} 80" class="w-full h-auto text-[var(--muted-foreground)]">'
            f'<text x="{chart_width / 2}" y="45" text-anchor="middle" fill="currentColor" font-size="13">'
            "No subagent execution timeline data"
            "</text></svg>"
        )

    times: list[tuple[SubagentSessionMetrics, datetime, float]] = []
    global_min: datetime | None = None

    for s in subagents:
        if s.turns and s.turns[0].created_at:
            dt = parse_iso_datetime(s.turns[0].created_at)
        else:
            dt = datetime.now()
        dur = max(s.total_duration_sec, 0.5)
        times.append((s, dt, dur))

        if global_min is None or dt < global_min:
            global_min = dt

    timeline_items: list[tuple[SubagentSessionMetrics, float, float]] = []
    max_span_end: float = 1.0
    for s, dt, dur in times:
        offset_sec = (dt - (global_min or dt)).total_seconds() if global_min else 0.0
        offset_sec = max(0.0, offset_sec)
        end_sec = offset_sec + dur
        if end_sec > max_span_end:
            max_span_end = end_sec
        timeline_items.append((s, offset_sec, dur))

    label_width = 130
    timeline_width = chart_width - label_width - 60
    total_height = len(timeline_items) * row_height + 50

    svg_parts = [
        f'<svg viewBox="0 0 {chart_width} {total_height}" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg">',
        "  <defs>",
        '    <linearGradient id="ganttGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '      <stop offset="0%" stop-color="#06b6d4" />',
        '      <stop offset="100%" stop-color="#0284c7" />',
        "    </linearGradient>",
        "  </defs>",
        "  <!-- Time Axis Grid Lines -->",
    ]

    for tick_pct in (0.0, 0.25, 0.50, 0.75, 1.0):
        x = label_width + (tick_pct * timeline_width)
        time_label = f"{tick_pct * max_span_end:.1f}s"
        svg_parts.append(
            f'  <line x1="{x:.1f}" y1="25" x2="{x:.1f}" y2="{total_height - 15}" '
            f'stroke="currentColor" stroke-dasharray="3 3" opacity="0.15" />'
        )
        svg_parts.append(
            f'  <text x="{x:.1f}" y="18" text-anchor="middle" font-size="10" fill="currentColor" '
            f'class="text-[var(--muted-foreground)]">{time_label}</text>'
        )

    for idx, (s, offset, dur) in enumerate(timeline_items):
        y = idx * row_height + 35
        cid = s.conversation_id
        short_id = f"{cid[:8]}...{cid[-4:]}" if len(cid) > 16 else cid

        x_start = label_width + (offset / max_span_end) * timeline_width
        bar_w = max(4.0, (dur / max_span_end) * timeline_width)

        svg_parts.append(f"  <!-- Gantt Row {idx}: {cid} -->")
        svg_parts.append(
            f'  <text x="{label_width - 10}" y="{y + 15}" text-anchor="end" font-size="11" '
            f'font-family="monospace" fill="currentColor" class="text-[var(--muted-foreground)]">'
            f"{html.escape(short_id)}"
            f"</text>"
        )

        svg_parts.append(
            f'  <rect x="{x_start:.1f}" y="{y + 2}" width="{bar_w:.1f}" height="20" rx="6" '
            f'fill="url(#ganttGrad)">'
            f"<title>{html.escape(cid)} - Offset: {offset:.1f}s, Duration: {dur:.1f}s, Turns: {s.turns_count}</title>"
            f"</rect>"
        )

        dur_label = f"{dur:.1f}s"
        if bar_w > 45:
            svg_parts.append(
                f'  <text x="{x_start + bar_w / 2:.1f}" y="{y + 16}" text-anchor="middle" font-size="10" '
                f'font-weight="600" fill="#ffffff">{dur_label}</text>'
            )
        else:
            svg_parts.append(
                f'  <text x="{x_start + bar_w + 6:.1f}" y="{y + 16}" text-anchor="start" font-size="10" '
                f'font-weight="500" fill="currentColor" class="text-[var(--foreground)]">{dur_label}</text>'
            )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def _generate_tool_metrics_table_html(subagents: list[SubagentSessionMetrics]) -> str:
    """Generate an aggregated tool calls metrics HTML table."""
    tool_counts: dict[str, int] = {}
    tool_durations: dict[str, float] = {}

    for s in subagents:
        for tool_name, count in s.tool_counts.items():
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + count
        for tool_name, dur in s.tool_durations_ms.items():
            tool_durations[tool_name] = tool_durations.get(tool_name, 0.0) + dur

    if not tool_counts:
        return '<p class="text-sm text-[var(--muted-foreground)] py-4 text-center">No tool invocations recorded.</p>'

    total_tool_calls = sum(tool_counts.values())
    total_tool_duration = sum(tool_durations.values())

    rows = []
    for name, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
        dur = tool_durations.get(name, 0.0)
        avg = dur / count if count > 0 else 0.0
        pct = (count / total_tool_calls * 100) if total_tool_calls > 0 else 0.0

        rows.append(
            f"""
            <tr class="border-b border-[var(--border)] hover:bg-[var(--card)]/60 transition-colors">
              <td class="py-2.5 px-3 font-mono text-xs font-semibold text-[var(--primary)]">{html.escape(name)}</td>
              <td class="py-2.5 px-3 text-right font-semibold text-xs">{count:,}</td>
              <td class="py-2.5 px-3 text-right text-xs text-[var(--muted-foreground)]">{pct:.1f}%</td>
              <td class="py-2.5 px-3 text-right text-xs font-mono">{dur:,.1f}ms</td>
              <td class="py-2.5 px-3 text-right text-xs font-mono text-[var(--muted-foreground)]">{avg:,.1f}ms</td>
            </tr>
            """
        )

    return f"""
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead class="text-xs text-[var(--muted-foreground)] uppercase border-b border-[var(--border)]">
          <tr>
            <th class="py-2 px-3">Tool Name</th>
            <th class="py-2 px-3 text-right">Invocations</th>
            <th class="py-2 px-3 text-right">Share</th>
            <th class="py-2 px-3 text-right">Total Latency</th>
            <th class="py-2 px-3 text-right">Avg Latency</th>
          </tr>
        </thead>
        <tbody>
          {"".join(rows)}
        </tbody>
        <tfoot class="border-t border-[var(--border)] font-semibold text-xs">
          <tr>
            <td class="py-2.5 px-3">Total / Aggregate</td>
            <td class="py-2.5 px-3 text-right">{total_tool_calls:,}</td>
            <td class="py-2.5 px-3 text-right">100%</td>
            <td class="py-2.5 px-3 text-right font-mono">{total_tool_duration:,.1f}ms</td>
            <td class="py-2.5 px-3 text-right font-mono">-</td>
          </tr>
        </tfoot>
      </table>
    </div>
    """


def generate_swarm_dashboard_html(
    report: SwarmSessionTelemetryReport,
    title: str | None = None,
) -> str:
    """Generate a self-contained, interactive HTML Swarm Telemetry Dashboard."""
    display_title = title or f"Swarm Telemetry Dashboard: {report.parent_conversation_id}"
    report_dict = report.to_dict()
    report_json_str = json.dumps(report_dict, ensure_ascii=False, indent=2)

    # Budget calculations (ADR-0030 default limit heuristics: 10M tokens)
    max_budget_tokens = 10_000_000
    token_usage_pct = min(100.0, (report.total_swarm_tokens / max_budget_tokens) * 100)
    budget_status = "Compliant"
    budget_badge_class = "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"

    if report.total_swarm_tokens > max_budget_tokens:
        budget_status = "Exceeded"
        budget_badge_class = "bg-rose-500/10 text-rose-500 border-rose-500/20"
    elif report.total_swarm_tokens > (max_budget_tokens * 0.8):
        budget_status = "Warning"
        budget_badge_class = "bg-amber-500/10 text-amber-500 border-amber-500/20"

    token_chart_svg = _generate_token_bar_chart_svg(report.subagents)
    gantt_chart_svg = _generate_gantt_chart_svg(report.subagents)
    tool_table_html = _generate_tool_metrics_table_html(report.subagents)

    subagent_options = []
    for s in report.subagents:
        cid = s.conversation_id
        short = f"{cid[:8]}...{cid[-4:]}" if len(cid) > 16 else cid
        subagent_options.append(
            f'<option value="{html.escape(cid)}">{html.escape(short)} ({s.total_tokens:,} tokens, {s.turns_count} turns)</option>'
        )
    subagent_options_html = (
        "\n".join(subagent_options)
        if subagent_options
        else '<option value="">No subagents found</option>'
    )

    return f"""<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(display_title)}</title>
  <!-- Allowlisted Antigravity Tailwind CSS (CSP Compliant) -->
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    /* Antigravity Theme Fallbacks */
    :root {{
      --background: #0f172a;
      --card: #1e293b;
      --foreground: #f8fafc;
      --muted-foreground: #94a3b8;
      --border: #334155;
      --primary: #6366f1;
      --primary-foreground: #ffffff;
      --accent: #06b6d4;
    }}
    .light {{
      --background: #f8fafc;
      --card: #ffffff;
      --foreground: #0f172a;
      --muted-foreground: #64748b;
      --border: #e2e8f0;
      --primary: #4f46e5;
      --primary-foreground: #ffffff;
      --accent: #0284c7;
    }}
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] antialiased min-h-full flex flex-col p-4 md:p-6 transition-colors duration-200">
  <!-- Embedded Telemetry Data (Zero Dev Server) -->
  <script id="telemetry-data" type="application/json">
{report_json_str}
  </script>

  <!-- Header Section -->
  <header class="mb-6 pb-4 border-b border-[var(--border)] flex flex-col md:flex-row md:items-center md:justify-between gap-4">
    <div>
      <div class="flex items-center gap-2 mb-1">
        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
          CCBA Agent Services Platform v2.0
        </span>
        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border {budget_badge_class}">
          ADR-0030 Budget: {budget_status}
        </span>
      </div>
      <h1 class="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)]">
        🐝 Swarm Telemetry & Token Runtime Dashboard
      </h1>
      <p class="text-xs md:text-sm text-[var(--muted-foreground)] font-mono mt-0.5">
        Session: <span class="text-[var(--foreground)]">{html.escape(report.parent_conversation_id)}</span> &bull; {report.total_subagents} Subagents Active
      </p>
    </div>

    <!-- Action Toolbar -->
    <div class="flex items-center gap-2">
      <button onclick="downloadJson()" class="px-3 py-1.5 text-xs font-medium rounded-lg border border-[var(--border)] bg-[var(--card)] hover:border-[var(--primary)] transition-all flex items-center gap-1.5 shadow-sm">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
        Export JSON
      </button>
      <button onclick="copyRawJson()" id="btnCopy" class="px-3 py-1.5 text-xs font-medium rounded-lg border border-[var(--border)] bg-[var(--card)] hover:border-[var(--primary)] transition-all flex items-center gap-1.5 shadow-sm">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"/></svg>
        Copy Data
      </button>
      <button onclick="toggleTheme()" class="px-2.5 py-1.5 text-xs font-medium rounded-lg border border-[var(--border)] bg-[var(--card)] hover:border-[var(--primary)] transition-all" title="Toggle Dark/Light Mode">
        🌓
      </button>
    </div>
  </header>

  <!-- KPI Cards Grid -->
  <section class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 md:gap-4 mb-6">
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
      <div class="text-xs text-[var(--muted-foreground)] font-medium">Total Swarm Tokens</div>
      <div class="text-lg md:text-xl font-bold mt-1 text-indigo-400">{_format_number(report.total_swarm_tokens)}</div>
      <div class="text-[10px] text-[var(--muted-foreground)] mt-1 flex justify-between">
        <span>Prompt: {_format_number(report.total_prompt_tokens)}</span>
      </div>
    </div>

    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
      <div class="text-xs text-[var(--muted-foreground)] font-medium">Estimated Cost (USD)</div>
      <div class="text-lg md:text-xl font-bold mt-1 text-emerald-400">${report.total_cost_usd:.4f}</div>
      <div class="text-[10px] text-[var(--muted-foreground)] mt-1">
        Gemini Pro/Flash Rates
      </div>
    </div>

    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
      <div class="text-xs text-[var(--muted-foreground)] font-medium">Active Subagents</div>
      <div class="text-lg md:text-xl font-bold mt-1 text-cyan-400">{report.total_subagents}</div>
      <div class="text-[10px] text-[var(--muted-foreground)] mt-1">
        Isolated Trajectories
      </div>
    </div>

    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
      <div class="text-xs text-[var(--muted-foreground)] font-medium">Total Execution Time</div>
      <div class="text-lg md:text-xl font-bold mt-1 text-amber-400">{report.total_duration_sec:.1f}s</div>
      <div class="text-[10px] text-[var(--muted-foreground)] mt-1">
        Aggregated Run Duration
      </div>
    </div>

    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
      <div class="text-xs text-[var(--muted-foreground)] font-medium">Completion Ratio</div>
      <div class="text-lg md:text-xl font-bold mt-1 text-purple-400">
        {(report.total_completion_tokens / report.total_swarm_tokens * 100) if report.total_swarm_tokens > 0 else 0.0:.1f}%
      </div>
      <div class="text-[10px] text-[var(--muted-foreground)] mt-1">
        Gen vs Context Tokens
      </div>
    </div>

    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
      <div class="text-xs text-[var(--muted-foreground)] font-medium">Budget Status</div>
      <div class="text-lg md:text-xl font-bold mt-1 flex items-center gap-1.5">
        <span class="inline-block w-2.5 h-2.5 rounded-full {"bg-emerald-500" if budget_status == "Compliant" else ("bg-amber-500" if budget_status == "Warning" else "bg-rose-500")}"></span>
        <span class="text-sm md:text-base">{budget_status}</span>
      </div>
      <div class="text-[10px] text-[var(--muted-foreground)] mt-1">
        {token_usage_pct:.1f}% of 10M Limit
      </div>
    </div>
  </section>

  <!-- Charts Layout (2-Column Grid) -->
  <section class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
    <!-- Chart 1: Token Distribution -->
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold tracking-wide flex items-center gap-2 text-[var(--foreground)]">
          <span class="text-indigo-400">📊</span> Token Breakdown by Subagent
        </h2>
        <span class="text-xs text-[var(--muted-foreground)]">Prompt vs Completion</span>
      </div>
      <div class="w-full">
        {token_chart_svg}
      </div>
    </div>

    <!-- Chart 2: Gantt Timeline -->
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold tracking-wide flex items-center gap-2 text-[var(--foreground)]">
          <span class="text-cyan-400">⏱️</span> Swarm Execution Timeline (Gantt)
        </h2>
        <span class="text-xs text-[var(--muted-foreground)]">Runtime Spans</span>
      </div>
      <div class="w-full">
        {gantt_chart_svg}
      </div>
    </div>
  </section>

  <!-- Tool Latency & Invocations Table -->
  <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm mb-6">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-sm font-semibold tracking-wide flex items-center gap-2 text-[var(--foreground)]">
        <span class="text-amber-400">🛠️</span> Tool Invocations & Latency Matrix
      </h2>
      <span class="text-xs text-[var(--muted-foreground)]">Aggregated Across Fleet</span>
    </div>
    {tool_table_html}
  </section>

  <!-- Turn-by-Turn Trajectory Inspector -->
  <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm mb-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
      <div>
        <h2 class="text-sm font-semibold tracking-wide flex items-center gap-2 text-[var(--foreground)]">
          <span class="text-purple-400">🔍</span> Turn-by-Turn Trajectory Inspector
        </h2>
        <p class="text-xs text-[var(--muted-foreground)]">Examine prompt/generation tokens and tool calls per model turn</p>
      </div>

      <!-- Subagent Selector -->
      <div class="flex items-center gap-2">
        <label for="subagentSelect" class="text-xs text-[var(--muted-foreground)]">Subagent:</label>
        <select id="subagentSelect" onchange="renderSelectedSubagentTurns()" class="bg-[var(--background)] border border-[var(--border)] rounded-lg px-3 py-1.5 text-xs text-[var(--foreground)] focus:outline-none focus:border-[var(--primary)] font-mono">
          {subagent_options_html}
        </select>
      </div>
    </div>

    <!-- Inspector Dynamic Container -->
    <div id="inspectorContainer" class="overflow-x-auto">
      <p class="text-xs text-[var(--muted-foreground)] py-4 text-center">Select a subagent above to inspect turns.</p>
    </div>
  </section>

  <!-- Footer -->
  <footer class="mt-auto pt-4 border-t border-[var(--border)] text-xs text-[var(--muted-foreground)] flex flex-col sm:flex-row justify-between items-center gap-2">
    <div>
      Generated autonomously by <span class="font-semibold text-[var(--foreground)]">ccba-harness v2.0</span> &bull; OpenTelemetry GenAI v1.28.0+
    </div>
    <div class="flex items-center gap-4">
      <span>ADR-0030 Instruction Budget</span>
      <span>ADR-0058 Hard Completion Lock</span>
    </div>
  </footer>

  <!-- Client-side Interactive Logic -->
  <script>
    const telemetryData = JSON.parse(document.getElementById('telemetry-data').textContent);

    function toggleTheme() {{
      document.documentElement.classList.toggle('light');
    }}

    function downloadJson() {{
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(telemetryData, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `swarm_telemetry_${{telemetryData.parent_conversation_id}}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    }}

    function copyRawJson() {{
      navigator.clipboard.writeText(JSON.stringify(telemetryData, null, 2)).then(() => {{
        const btn = document.getElementById('btnCopy');
        const oldHtml = btn.innerHTML;
        btn.innerHTML = '✅ Copied!';
        setTimeout(() => {{ btn.innerHTML = oldHtml; }}, 2000);
      }});
    }}

    function renderSelectedSubagentTurns() {{
      const select = document.getElementById('subagentSelect');
      if (!select) return;
      const cid = select.value;
      const container = document.getElementById('inspectorContainer');
      if (!cid || !telemetryData.subagents) return;

      const sub = telemetryData.subagents.find(s => s.conversation_id === cid);
      if (!sub || !sub.turns_summary || sub.turns_summary.length === 0) {{
        container.innerHTML = '<p class="text-xs text-[var(--muted-foreground)] py-4 text-center">No turns recorded for this subagent.</p>';
        return;
      }}

      let rows = '';
      sub.turns_summary.forEach(t => {{
        rows += `
          <tr class="border-b border-[var(--border)] hover:bg-[var(--card)]/60 text-xs">
            <td class="py-2 px-3 font-semibold text-indigo-400">Turn ${{t.turn}}</td>
            <td class="py-2 px-3 text-right font-mono">${{t.prompt_tokens.toLocaleString()}}</td>
            <td class="py-2 px-3 text-right font-mono text-emerald-400">${{t.completion_tokens.toLocaleString()}}</td>
            <td class="py-2 px-3 text-right font-mono">${{(t.prompt_tokens + t.completion_tokens).toLocaleString()}}</td>
            <td class="py-2 px-3 text-right text-[var(--muted-foreground)] font-mono">${{t.duration_sec}}s</td>
            <td class="py-2 px-3 text-right font-semibold">${{t.tool_calls}} call(s)</td>
          </tr>
        `;
      }});

      container.innerHTML = `
        <table class="w-full text-left text-xs">
          <thead class="text-xs text-[var(--muted-foreground)] uppercase border-b border-[var(--border)]">
            <tr>
              <th class="py-2 px-3">Turn #</th>
              <th class="py-2 px-3 text-right">Prompt Tokens</th>
              <th class="py-2 px-3 text-right">Completion Tokens</th>
              <th class="py-2 px-3 text-right">Total Tokens</th>
              <th class="py-2 px-3 text-right">Duration</th>
              <th class="py-2 px-3 text-right">Tool Invocations</th>
            </tr>
          </thead>
          <tbody>${{rows}}</tbody>
        </table>
      `;
    }}

    document.addEventListener('DOMContentLoaded', () => {{
      renderSelectedSubagentTurns();
    }});
  </script>
</body>
</html>
"""


def render_swarm_dashboard(
    target: str | Path,
    output_path: Path | None = None,
    title: str | None = None,
) -> tuple[Path, SwarmSessionTelemetryReport]:
    """Audit swarm metrics from target and render the standalone dashboard HTML file.

    Args:
        target: Parent conversation ID, transcript path, or directory containing subagents.
        output_path: Target path for the HTML file. Defaults to `.md/reports/swarm_telemetry_dashboard.html`.
        title: Optional custom dashboard title.

    Returns:
        (out_path, report)
    """
    report, _passed, _msg = audit_swarm_session(target)

    if output_path is None:
        out_file = Path(".md") / "reports" / "swarm_telemetry_dashboard.html"
    else:
        out_file = Path(output_path)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    html_content = generate_swarm_dashboard_html(report, title=title)
    out_file.write_text(html_content, encoding="utf-8")

    return out_file, report
