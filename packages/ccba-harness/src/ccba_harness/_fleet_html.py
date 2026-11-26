"""Standalone HTML dashboard generator for Cross-Spoke Fleet Telemetry."""

from __future__ import annotations

import html
import json
from typing import Any

from ._fleet_charts import (
    format_number,
    generate_fleet_comparison_chart_svg,
    generate_fleet_domain_breakdown_svg,
)
from ._fleet_scanner import FleetTelemetryReport, SpokeTelemetrySummary, sanitize_telemetry_text


def _render_tool_rows_html(fleet_tool_counts: dict[str, int]) -> str:
    """Render HTML `<tr>` rows for the Fleet Top Tools summary table."""
    sorted_tools = sorted(fleet_tool_counts.items(), key=lambda x: (-x[1], x[0]))[:8]
    if not sorted_tools:
        return (
            '<tr><td colspan="3" class="py-3 text-center text-xs '
            'text-[var(--muted-foreground)]">No tool invocations</td></tr>'
        )
    tot_tool_calls = sum(fleet_tool_counts.values()) or 1
    rows: list[str] = []
    for t_name, count in sorted_tools:
        pct = (count / tot_tool_calls) * 100
        rows.append(
            f"""
            <tr class="border-b border-[var(--border)] hover:bg-[var(--card)]/60 text-xs transition-colors">
              <td class="py-2 px-3 font-mono font-semibold text-[var(--primary)]">{html.escape(t_name)}</td>
              <td class="py-2 px-3 text-right font-semibold">{count:,}</td>
              <td class="py-2 px-3 text-right text-[var(--muted-foreground)] font-mono">{pct:.1f}%</td>
            </tr>
            """
        )
    return "".join(rows)


def _spoke_row_html(spoke: SpokeTelemetrySummary) -> str:
    """Render a single Spoke table row with status and budget badges."""
    status_color = (
        "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
        if spoke.is_online
        else "bg-slate-500/10 text-slate-400 border-slate-500/20"
    )
    budget_color = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
    if spoke.budget_status in ("Exceeded", "PARSE_ERROR"):
        budget_color = "bg-rose-500/10 text-rose-400 border-rose-500/20"
    elif spoke.budget_status in ("Warning", "NO_DATA"):
        budget_color = "bg-amber-500/10 text-amber-400 border-amber-500/20"
    sync_date = spoke.last_sync[:10] if spoke.last_sync else "Never"
    spoke_label = html.escape(spoke.anonymized_spoke_id)
    return f"""
            <tr class="border-b border-[var(--border)] hover:bg-[var(--card)]/60 text-xs transition-colors spoke-row" data-domain="{html.escape(spoke.project_type)}">
              <td class="py-3 px-3">
                <div class="font-mono font-semibold text-sm text-[var(--foreground)]">{spoke_label}</div>
                <div class="font-mono text-[10px] text-[var(--muted-foreground)]">SHA-256 anonymized</div>
              </td>
              <td class="py-3 px-3">
                <span class="inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  {html.escape(spoke.project_type)}
                </span>
              </td>
              <td class="py-3 px-3 text-center">
                <span class="inline-block px-2 py-0.5 rounded text-[10px] font-semibold border {status_color}">
                  {"Online" if spoke.is_online else "Offline"}
                </span>
              </td>
              <td class="py-3 px-3 text-right font-mono font-semibold text-indigo-400">{format_number(spoke.total_tokens)}</td>
              <td class="py-3 px-3 text-right font-mono text-emerald-400 font-semibold">${spoke.total_cost_usd:.4f}</td>
              <td class="py-3 px-3 text-right text-[var(--muted-foreground)] font-mono">{sync_date}</td>
              <td class="py-3 px-3 text-center">
                <span class="inline-block px-2 py-0.5 rounded text-[10px] font-semibold border {budget_color}">
                  {spoke.budget_status}
                </span>
              </td>
            </tr>
            """


def _render_spoke_rows_html(spokes: list[SpokeTelemetrySummary]) -> str:
    """Render all Spoke matrix rows sorted by token consumption."""
    ordered = sorted(spokes, key=lambda x: (-x.total_tokens, x.anonymized_spoke_id))
    return "\n".join(_spoke_row_html(spoke) for spoke in ordered)


def _render_innovation_rows_html(innovations: list[dict[str, Any]]) -> str:
    """Render HTML `<tr>` rows for the Top Spoke Innovations table."""
    if not innovations:
        return (
            '<tr><td colspan="5" class="py-3 text-center text-xs '
            'text-[var(--muted-foreground)]">No unique Spoke-local domain innovations '
            "detected in current fleet telemetry cycle.</td></tr>"
        )
    rows: list[str] = []
    for inn in innovations:
        status_color = (
            "bg-purple-500/10 text-purple-400 border-purple-500/20"
            if inn["promotion_status"] == "Candidate for Hub Ingestion"
            else "bg-slate-500/10 text-slate-400 border-slate-500/20"
        )
        spokes_badges = " ".join(
            f'<span class="inline-block px-1.5 py-0.5 rounded text-[10px] '
            f'bg-blue-500/10 text-blue-400 border border-blue-500/20">{html.escape(spk)}</span>'
            for spk in inn["source_spokes"]
        )
        rows.append(
            f"""
            <tr class="border-b border-[var(--border)] hover:bg-[var(--card)]/60 text-xs transition-colors">
              <td class="py-2.5 px-3 font-mono font-semibold text-purple-400">{html.escape(inn["tool_or_skill"])}</td>
              <td class="py-2.5 px-3">{spokes_badges}</td>
              <td class="py-2.5 px-3 text-right font-mono font-semibold">{inn["total_calls"]:,}</td>
              <td class="py-2.5 px-3 text-center">
                <span class="inline-block px-2 py-0.5 rounded text-[10px] font-semibold border {status_color}">
                  {inn["promotion_status"]}
                </span>
              </td>
              <td class="py-2.5 px-3 text-[var(--muted-foreground)]">{html.escape(inn["recommendation"])}</td>
            </tr>
            """
        )
    return "".join(rows)


def _render_html_head(display_title: str) -> str:
    """Render HTML `<head>` with Tailwind CDN and theme CSS variables."""
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
</head>"""


def _render_html_header(report: FleetTelemetryReport, report_json_str: str) -> str:
    """Render embedded JSON payload and top header bar with export toolbar."""
    return f"""  <!-- Embedded Fleet Telemetry Data (Zero Dev Server) -->
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
  </header>"""


def _render_html_kpi_cards(report: FleetTelemetryReport) -> str:
    """Render the 4 KPI summary cards row."""
    return f"""  <!-- KPI Cards Grid -->
  <section class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
      <div class="text-xs text-[var(--muted-foreground)] font-medium">Total Fleet Tokens</div>
      <div class="text-xl md:text-2xl font-bold mt-1 text-blue-400">{format_number(report.total_fleet_tokens)}</div>
      <div class="text-[10px] text-[var(--muted-foreground)] mt-1 flex justify-between">
        <span>Prompt: {format_number(report.total_prompt_tokens)}</span>
        <span>Gen: {format_number(report.total_completion_tokens)}</span>
      </div>
    </div>
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
      <div class="text-xs text-[var(--muted-foreground)] font-medium">Enterprise Cost (USD)</div>
      <div class="text-xl md:text-2xl font-bold mt-1 text-emerald-400">${report.total_fleet_cost_usd:.4f}</div>
      <div class="text-[10px] text-[var(--muted-foreground)] mt-1">Aggregated Gemini Pro/Flash API</div>
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
      <div class="text-[10px] text-[var(--muted-foreground)] mt-1">ADR-0030 Quotas Enforced</div>
    </div>
  </section>"""


def _render_html_charts_section(
    comparison_chart_svg: str,
    domain_chart_svg: str,
    tool_rows_html: str,
) -> str:
    """Render the 2-column SVG chart and top-tools grid."""
    return f"""  <!-- Charts Layout (2-Column Grid) -->
  <section class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
    <div class="lg:col-span-2 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold tracking-wide flex items-center gap-2 text-[var(--foreground)]">
          <span class="text-blue-400">📊</span> Spoke Token Comparison Matrix
        </h2>
        <span class="text-xs text-[var(--muted-foreground)]">Prompt vs Completion</span>
      </div>
      <div class="w-full">{comparison_chart_svg}</div>
    </div>
    <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm flex flex-col">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold tracking-wide flex items-center gap-2 text-[var(--foreground)]">
          <span class="text-purple-400">📂</span> Domain Distribution
        </h2>
        <span class="text-xs text-[var(--muted-foreground)]">By Project Type</span>
      </div>
      <div class="w-full mb-4">{domain_chart_svg}</div>
      <div class="mt-auto border-t border-[var(--border)] pt-3">
        <div class="text-xs font-semibold text-[var(--muted-foreground)] uppercase mb-2">Fleet Top Tools</div>
        <table class="w-full text-xs"><tbody>{tool_rows_html}</tbody></table>
      </div>
    </div>
  </section>"""


def _render_html_spokes_table(report: FleetTelemetryReport, spoke_rows_html: str) -> str:
    """Render the Registered Spoke Projects Matrix section with domain filter."""
    domain_options = "".join(
        f'<option value="{html.escape(dt)}">{html.escape(dt)}</option>'
        for dt in report.spokes_by_type.keys()
    )
    return f"""  <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm mb-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
      <div>
        <h2 class="text-sm font-semibold tracking-wide flex items-center gap-2 text-[var(--foreground)]">
          <span class="text-emerald-400">🏢</span> Registered Spoke Projects Matrix
        </h2>
        <p class="text-xs text-[var(--muted-foreground)]">Sanitized telemetry summaries aggregated from local filesystem and Spoke registries</p>
      </div>
      <div class="flex items-center gap-2">
        <label for="domainFilter" class="text-xs text-[var(--muted-foreground)]">Domain:</label>
        <select id="domainFilter" onchange="filterSpokesByDomain()" class="bg-[var(--background)] border border-[var(--border)] rounded-lg px-2.5 py-1 text-xs text-[var(--foreground)] focus:outline-none focus:border-[var(--primary)]">
          <option value="ALL">All Domains</option>
          {domain_options}
        </select>
      </div>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs">
        <thead class="text-[11px] text-[var(--muted-foreground)] uppercase border-b border-[var(--border)]">
          <tr>
            <th class="py-2.5 px-3">Spoke ID</th><th class="py-2.5 px-3">Domain</th>
            <th class="py-2.5 px-3 text-center">Status</th><th class="py-2.5 px-3 text-right">Tokens Consumed</th>
            <th class="py-2.5 px-3 text-right">Estimated Cost</th><th class="py-2.5 px-3 text-right">Last Sync</th>
            <th class="py-2.5 px-3 text-center">Budget Status</th>
          </tr>
        </thead>
        <tbody id="spokeTableBody">{spoke_rows_html}</tbody>
      </table>
    </div>
  </section>"""


def _render_html_innovations_table(innov_rows_html: str) -> str:
    """Render the Top Spoke Innovations & Hub Ingestion candidates section."""
    return f"""  <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm mb-6">
    <div class="mb-4">
      <div class="flex items-center gap-2 mb-1">
        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">Knowledge Diffusion</span>
        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">ADR-0045 Upstream Loop</span>
      </div>
      <h2 class="text-sm font-semibold tracking-wide flex items-center gap-2 text-[var(--foreground)]">
        <span class="text-purple-400">🚀</span> Top Spoke Innovations & Candidates for Hub Ingestion
      </h2>
      <p class="text-xs text-[var(--muted-foreground)] mt-0.5">
        Autonomous cross-spoke knowledge diffusion: highlights domain tools developed locally across Spokes. Tools with &ge;5 invocations or active across &ge;2 Spokes qualify as candidates for Hub Monorepo ingestion via <code class="font-mono text-[11px] text-[var(--primary)]">.agents/proposals/TEMPLATE.md</code>.
      </p>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs">
        <thead class="text-[11px] text-[var(--muted-foreground)] uppercase border-b border-[var(--border)]">
          <tr>
            <th class="py-2.5 px-3">Tool / Innovation Name</th><th class="py-2.5 px-3">Source Spokes</th>
            <th class="py-2.5 px-3 text-right">Invocations</th><th class="py-2.5 px-3 text-center">Promotion Status</th>
            <th class="py-2.5 px-3">Recommendation / Next Step</th>
          </tr>
        </thead>
        <tbody>{innov_rows_html}</tbody>
      </table>
    </div>
  </section>"""


def _render_html_footer_and_scripts() -> str:
    """Render footer and client-side interactive JSON export and domain filter JS."""
    return """  <footer class="mt-auto pt-4 border-t border-[var(--border)] text-xs text-[var(--muted-foreground)] flex flex-col sm:flex-row justify-between items-center gap-2">
    <div>
      CCBA Agent Services Platform &bull; <span class="font-semibold text-[var(--foreground)]">Cross-Spoke Analytics Engine</span> (ADR-0046 & ADR-0058)
    </div>
    <div class="flex items-center gap-4">
      <span>Zero Confidential Leakage</span>
      <span>Enterprise Multi-Project Telemetry</span>
    </div>
  </footer>
  <script>
    const fleetData = JSON.parse(document.getElementById('fleet-telemetry-data').textContent);
    function toggleTheme() { document.documentElement.classList.toggle('light'); }
    function downloadFleetJson() {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(fleetData, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `fleet_telemetry_${fleetData.hub_name}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    }
    function copyFleetJson() {
      navigator.clipboard.writeText(JSON.stringify(fleetData, null, 2)).then(() => {
        const btn = document.getElementById('btnCopyFleet');
        const oldHtml = btn.innerHTML;
        btn.innerHTML = '✅ Copied!';
        setTimeout(() => { btn.innerHTML = oldHtml; }, 2000);
      });
    }
    function filterSpokesByDomain() {
      const sel = document.getElementById('domainFilter').value;
      document.querySelectorAll('.spoke-row').forEach(r => {
        const dom = r.getAttribute('data-domain');
        r.style.display = (sel === 'ALL' || dom === sel) ? '' : 'none';
      });
    }
  </script>
</body>
</html>
"""


def generate_fleet_dashboard_html(
    report: FleetTelemetryReport,
    title: str | None = None,
) -> str:
    """Generate a self-contained, interactive HTML Cross-Spoke Fleet Dashboard."""
    display_title = title or f"Cross-Spoke Fleet Telemetry: {report.hub_name}"
    report_json_str = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    comparison_chart_svg = generate_fleet_comparison_chart_svg(report.spokes)
    domain_chart_svg = generate_fleet_domain_breakdown_svg(report.spokes_by_type)
    tool_rows_html = _render_tool_rows_html(report.fleet_tool_counts)
    spoke_rows_html = _render_spoke_rows_html(report.spokes)
    innov_rows_html = _render_innovation_rows_html(report.get_top_spoke_innovations())

    return sanitize_telemetry_text(
        "\n".join(
            [
                _render_html_head(display_title),
                '<body class="bg-[var(--background)] text-[var(--foreground)] antialiased min-h-full flex flex-col p-4 md:p-6 transition-colors duration-200">',
                _render_html_header(report, report_json_str),
                _render_html_kpi_cards(report),
                _render_html_charts_section(comparison_chart_svg, domain_chart_svg, tool_rows_html),
                _render_html_spokes_table(report, spoke_rows_html),
                _render_html_innovations_table(innov_rows_html),
                _render_html_footer_and_scripts(),
            ]
        )
    )
