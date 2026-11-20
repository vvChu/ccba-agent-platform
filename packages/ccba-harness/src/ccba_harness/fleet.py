"""fleet.py - Cross-Spoke Analytics & Enterprise Fleet Telemetry Engine.

Implements multi-project governance, token rollups, and fleet dashboards (ADR-0010, ADR-0030, ADR-0046, ADR-0058):
1. Sanitized Telemetry Protocol: aggregates non-sensitive metrics across all registered Spokes.
2. Fault-Tolerant Scanning: seamlessly handles offline, unmounted, or archived Spokes.
3. Pure SVG Cross-Spoke Analytics: renders comparison charts, project matrices, and cost breakdowns.
4. Zero-Server Standalone HTML Generation with Antigravity-allowlisted Tailwind CSS.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._fleet_charts import (
    format_number as _format_number,
)
from ._fleet_charts import (
    generate_fleet_comparison_chart_svg as _generate_fleet_comparison_chart_svg,
)
from ._fleet_charts import (
    generate_fleet_domain_breakdown_svg as _generate_fleet_domain_breakdown_svg,
)
from ._fleet_html import generate_fleet_dashboard_html
from ._fleet_scanner import (
    DEFAULT_SPOKE_BUDGET_TOKENS,
    STANDARD_BUILTIN_TOOLS,
    FleetTelemetryReport,
    SpokeTelemetrySummary,
    aggregate_fleet_telemetry,
    scan_spoke_telemetry,
)


def render_fleet_dashboard(
    output_path: Path | None = None,
    title: str | None = None,
    hub_root: Path | None = None,
    spokes_list: list[dict[str, Any]] | None = None,
) -> tuple[Path, FleetTelemetryReport]:
    """Audit the enterprise fleet and render the standalone HTML dashboard file."""
    report = aggregate_fleet_telemetry(hub_root=hub_root, spokes_list=spokes_list)
    out_file = (
        Path(".md") / "reports" / "cross_spoke_fleet_dashboard.html"
        if output_path is None
        else Path(output_path)
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    html_content = generate_fleet_dashboard_html(report, title=title)
    out_file.write_text(html_content, encoding="utf-8")
    return out_file, report


__all__ = [
    "DEFAULT_SPOKE_BUDGET_TOKENS",
    "STANDARD_BUILTIN_TOOLS",
    "FleetTelemetryReport",
    "SpokeTelemetrySummary",
    "_format_number",
    "_generate_fleet_comparison_chart_svg",
    "_generate_fleet_domain_breakdown_svg",
    "aggregate_fleet_telemetry",
    "generate_fleet_dashboard_html",
    "render_fleet_dashboard",
    "scan_spoke_telemetry",
]
