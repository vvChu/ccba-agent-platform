"""Pure SVG cross-spoke comparison and domain distribution chart generators."""

from __future__ import annotations

import html

from ._fleet_scanner import SpokeTelemetrySummary


def format_number(n: int | float) -> str:
    """Format numbers with comma separators."""
    if isinstance(n, int):
        return f"{n:,}"
    return f"{n:,.2f}"


def _empty_svg(chart_width: int, message: str, font_size: int) -> str:
    """Return a placeholder SVG banner when no data points exist."""
    return (
        f'<svg viewBox="0 0 {chart_width} 80" class="w-full h-auto text-[var(--muted-foreground)]">'
        f'<text x="{chart_width / 2}" y="45" text-anchor="middle" fill="currentColor" '
        f'font-size="{font_size}">{html.escape(message)}</text></svg>'
    )


def _comparison_svg_header(chart_width: int, total_height: int) -> list[str]:
    """Build SVG defs and legend header lines for the Spoke token comparison chart."""
    return [
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


def _render_comparison_row(
    idx: int,
    spoke: SpokeTelemetrySummary,
    max_tokens: int,
    label_width: int,
    bar_max_width: int,
    row_height: int,
) -> list[str]:
    """Render one horizontal stacked SVG bar row for a single Spoke."""
    y = idx * row_height + 40
    name = spoke.project_name
    display_name = f"{name[:16]}..." if len(name) > 18 else name
    total_w = (spoke.total_tokens / max_tokens) * bar_max_width if max_tokens > 0 else 0.0
    prompt_ratio = spoke.prompt_tokens / spoke.total_tokens if spoke.total_tokens > 0 else 0.0
    prompt_w = max(1.0, total_w * prompt_ratio) if spoke.total_tokens > 0 else 0.0
    comp_w = max(0.0, total_w - prompt_w)

    parts = [
        f"  <!-- Row {idx}: {name} -->",
        f'  <text x="{label_width - 10}" y="{y + 16}" text-anchor="end" font-size="11" '
        f'font-weight="500" fill="currentColor" class="text-[var(--foreground)]">'
        f"{html.escape(display_name)}</text>",
        f'  <rect x="{label_width}" y="{y + 4}" width="{bar_max_width}" height="18" rx="4" '
        f'fill="currentColor" opacity="0.08" />',
    ]
    if prompt_w > 0:
        parts.append(
            f'  <rect x="{label_width}" y="{y + 4}" width="{prompt_w:.1f}" height="18" '
            f'rx="4" fill="url(#fleetPromptGrad)"><title>{html.escape(name)} - Prompt: '
            f"{spoke.prompt_tokens:,} tokens</title></rect>"
        )
    if comp_w > 0:
        parts.append(
            f'  <rect x="{label_width + prompt_w}" y="{y + 4}" width="{comp_w:.1f}" height="18" '
            f'rx="4" fill="url(#fleetCompGrad)"><title>{html.escape(name)} - Completion: '
            f"{spoke.completion_tokens:,} tokens</title></rect>"
        )
    val_text = (
        format_number(spoke.total_tokens)
        if spoke.is_online
        else f"{format_number(spoke.total_tokens)} (off)"
    )
    parts.append(
        f'  <text x="{label_width + bar_max_width + 8}" y="{y + 17}" font-size="11" '
        f'font-weight="600" fill="currentColor" class="text-[var(--foreground)]">{val_text}</text>'
    )
    return parts


def generate_fleet_comparison_chart_svg(
    spokes: list[SpokeTelemetrySummary],
    chart_width: int = 700,
    row_height: int = 40,
) -> str:
    """Generate pure SVG horizontal stacked bar chart comparing Spoke token consumptions."""
    if not spokes:
        return _empty_svg(chart_width, "No registered Spokes found in fleet", 13)

    sorted_spokes = sorted(spokes, key=lambda s: (-s.total_tokens, s.project_name))
    max_tokens = max((s.total_tokens for s in sorted_spokes), default=1) or 1
    label_width, value_width = 150, 90
    bar_max_width = chart_width - label_width - value_width - 20
    total_height = len(sorted_spokes) * row_height + 40

    svg_parts = _comparison_svg_header(chart_width, total_height)
    for idx, spoke in enumerate(sorted_spokes):
        svg_parts.extend(
            _render_comparison_row(idx, spoke, max_tokens, label_width, bar_max_width, row_height)
        )
    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def generate_fleet_domain_breakdown_svg(
    spokes_by_type: dict[str, int],
    chart_width: int = 340,
    chart_height: int = 180,
) -> str:
    """Generate pure SVG horizontal bar representation for project types."""
    del chart_height
    if not spokes_by_type:
        return _empty_svg(chart_width, "No domain data", 12)

    total_projects = sum(spokes_by_type.values())
    sorted_domains = sorted(spokes_by_type.items(), key=lambda x: (-x[1], x[0]))
    row_height = 32
    total_height = len(sorted_domains) * row_height + 20
    colors = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899"]
    svg_parts = [
        f'<svg viewBox="0 0 {chart_width} {total_height}" class="w-full h-auto" xmlns="http://www.w3.org/2000/svg">'
    ]
    for idx, (dtype, count) in enumerate(sorted_domains):
        y = idx * row_height + 15
        pct = (count / total_projects) * 100 if total_projects > 0 else 0.0
        bar_w = (count / total_projects) * (chart_width - 150) if total_projects > 0 else 0.0
        svg_parts.extend(
            [
                f'  <text x="80" y="{y + 13}" text-anchor="end" font-size="11" fill="currentColor" '
                f'class="text-[var(--muted-foreground)]">{html.escape(dtype)}</text>',
                f'  <rect x="90" y="{y + 2}" width="{bar_w:.1f}" height="14" rx="3" fill="{colors[idx % len(colors)]}" />',
                f'  <text x="{90 + bar_w + 6:.1f}" y="{y + 13}" font-size="11" font-weight="600" '
                f'fill="currentColor" class="text-[var(--foreground)]">{count} ({pct:.0f}%)</text>',
            ]
        )
    svg_parts.append("</svg>")
    return "\n".join(svg_parts)
