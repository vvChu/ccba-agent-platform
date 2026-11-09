#!/usr/bin/env python3
"""UI/UX & Web Portal Design Core — Deterministic BM25 search, Design Dials, WCAG 2.2 Contrast & Slop Auditor."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from bm25_engine import BM25  # type: ignore[import-not-found]  # noqa: E402
from bm25_engine import search_csv as _search_csv  # noqa: E402

__all__ = [
    "BM25",
    "CSV_CONFIG",
    "DATA_DIR",
    "DOMAIN_KEYWORDS",
    "MAX_RESULTS",
    "UI_SLOP_PATTERNS",
    "audit_ui_code",
    "compute_contrast_ratio",
    "compute_design_dials",
    "detect_domain",
    "search",
    "search_all",
]

DATA_DIR: Path = _SCRIPTS_ROOT.parent / "data" / "ui"
MAX_RESULTS: int = 3

CSV_CONFIG: dict[str, dict[str, Any]] = {
    "style": {
        "file": "styles.csv",
        "search_cols": ["Style Name", "Category", "Surface Mode", "Keywords", "Best For"],
        "output_cols": [
            "Style Name",
            "Category",
            "Surface Mode",
            "Control Height",
            "Radius",
            "Spacing Scale",
            "Primary Palette",
            "Typography",
            "RTL Support",
            "Best For",
            "Avoid For",
        ],
    },
    "ux": {
        "file": "ux-guidelines.csv",
        "search_cols": ["Rule ID", "Priority", "Category", "Rule Name", "Keywords", "Do"],
        "output_cols": [
            "Rule ID",
            "Priority",
            "Category",
            "Rule Name",
            "Do",
            "Dont",
        ],
    },
    "chart": {
        "file": "charts.csv",
        "search_cols": ["Chart Type", "Category", "Keywords", "Best For"],
        "output_cols": [
            "Chart Type",
            "Category",
            "Best For",
            "Avoid When",
            "CVD-Safe Encoding",
            "Portal Density Fit",
        ],
    },
    "product": {
        "file": "products.csv",
        "search_cols": ["Product Type", "Surface Mode", "Keywords", "Recommended Style"],
        "output_cols": [
            "Product Type",
            "Surface Mode",
            "Recommended Style",
            "Recommended Density",
            "Primary Tokens",
            "Core Layout Pattern",
            "Recommended Charts",
            "Anti-Patterns",
        ],
    },
    "typography": {
        "file": "typography.csv",
        "search_cols": [
            "Pairing ID",
            "Pairing Name",
            "Heading Font",
            "Body Font",
            "Keywords",
            "Best For",
        ],
        "output_cols": [
            "Pairing ID",
            "Pairing Name",
            "Heading Font",
            "Body Font",
            "Monospace Font",
            "Vietnamese Support",
            "Tabular Nums",
            "Best For",
            "CSS Import / Font Stack",
            "Typography Rules & Guardrails",
        ],
    },
    "stack": {
        "file": "stacks.csv",
        "search_cols": [
            "Stack ID",
            "Stack Name",
            "Target Environment",
            "Core Libraries",
            "Keywords",
        ],
        "output_cols": [
            "Stack ID",
            "Stack Name",
            "Target Environment",
            "Core Libraries",
            "State & Routing Rules",
            "Styling & Token Rules",
            "Anti-Patterns to Ban",
        ],
    },
}

DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "ux": (
        "wcag",
        "a11y",
        "focus",
        "keyboard",
        "tab",
        "paste",
        "slop",
        "eyebrow",
        "url",
        "virtualization",
        "form",
        "cwv",
        "lcp",
        "inp",
        "cls",
        "state",
        "sidebar",
        "modal",
        "detail",
        "markdown",
        "deep-link",
        "spine",
        "nowrap",
        "anchor",
        "stepper",
        "llms",
        "delegation",
        "commandbarprops",
        "customcardprops",
        "showcard",
        "togglevisibility",
    ),
    "chart": (
        "chart",
        "graph",
        "heatmap",
        "gantt",
        "sankey",
        "radar",
        "pareto",
        "treemap",
        "sparkline",
        "bullet",
        "kpi",
        "visualization",
    ),
    "product": (
        "portal",
        "dashboard",
        "workspace",
        "cockpit",
        "console",
        "vbpl",
        "legal",
        "pccc",
        "qc",
        "bim",
        "cde",
        "hsht",
        "intranet",
        "landing",
    ),
    "style": (
        "mira",
        "nova",
        "fluent",
        "polaris",
        "swiss",
        "bento",
        "lyra",
        "maia",
        "hairline",
        "minimalist",
        "dark",
        "token",
    ),
    "typography": (
        "font",
        "typography",
        "typeface",
        "serif",
        "monospace",
        "vietnamese",
        "diacritics",
        "be vietnam",
        "inter",
        "jetbrains",
        "jakarta",
        "lexend",
        "tabular",
    ),
    "stack": (
        "nextjs",
        "react",
        "shadcn",
        "tailwind",
        "sharepoint",
        "spfx",
        "fluent ui",
        "fastapi",
        "htmx",
        "streamlit",
        "gradio",
        "threejs",
        "webgl",
        "tanstack",
        "powerapps",
        "power apps",
        "power automate",
        "canvas",
        "pa.yaml",
        "list-formatting",
        "adaptive cards",
        "m365",
    ),
}

UI_SLOP_PATTERNS: tuple[tuple[str, str, re.Pattern[str], str], ...] = (
    (
        "SLOP-01",
        "Operate Mode Typography",
        re.compile(r"\bclamp\s*\("),
        "Avoid fluid clamp() typography in Operate mode portals; use a fixed rem scale (1.125-1.2 ratio).",
    ),
    (
        "SLOP-02",
        "Tailwind Spacing Guardrail",
        re.compile(r"(?<![\w-])space-[xy]-\d+"),
        "Avoid space-x-* / space-y-* utilities; use flex gap-* or grid gap-* for RTL and wrapping safety.",
    ),
    (
        "SLOP-03",
        "Semantic Token Guardrail",
        re.compile(
            r"(?<![\w-])(?:bg|text|border)-(?:slate|gray|zinc|neutral|indigo|purple)-\d{2,3}"
        ),
        "Avoid raw Tailwind palette classes; use semantic tokens (bg-background, bg-card, text-muted-foreground).",
    ),
    (
        "SLOP-04",
        "WCAG 2.2 Accessible Auth (3.3.8)",
        re.compile(r"onPaste\s*=\s*\{[^}]*preventDefault"),
        "Never block paste on inputs (violates WCAG 2.2 3.3.8 Accessible Authentication).",
    ),
    (
        "SLOP-05",
        "Anti-Slop Craft Floor",
        re.compile(r"(?<![\w-])border-l-(?:4|8)\b|border-left\s*:\s*[3-9]px"),
        "Avoid thick colored left borders (>1px) on cards/callouts; use 1px semantic borders + icon badge.",
    ),
    (
        "SLOP-07",
        "Vietnamese Diacritic Font Guardrail",
        re.compile(
            r"(?i)\b(?:Clash[ \t]+Display|Cabinet[ \t]+Grotesk|Satoshi|General[ \t]+Sans|Monument[ \t]+Extended)\b"
        ),
        "Non-Vietnamese-safe font detected; use Be Vietnam Pro, Inter, Plus Jakarta Sans, Public Sans, or Lexend.",
    ),
    (
        "SLOP-08",
        "Unsafe Portal Link / XSS Protocol Guardrail",
        re.compile(
            r"""(?is)(?:(?:\bhref\s*=\s*(?:\{\s*)?|(?:location(?:\.href)?|\.href)\s*=\s*|setAttribute\s*\(\s*["']href["']\s*,\s*)["'`]?\s*(?:javascript|vbscript|data):|\.innerHTML\s*=\s*(?:marked|remarkable|showdown|markdownIt)\b)"""
        ),
        "Avoid unsafe javascript:, data:, or vbscript: URLs in href attributes or DOM sinks, and never pipe unescaped Markdown into innerHTML (UX-22).",
    ),
    (
        "SLOP-09",
        "M365 Sharing Link & Legacy Connector Guardrail",
        re.compile(
            r"""(?is)(?:https?://[^\s"'`<>]+/:[fbwxu]:/[grs]/|\b(?:ApiConnection|Invoker)\b["']?\s*:\s*["']?shared_)"""
        ),
        "Avoid temporary SharePoint/OneDrive sharing links (/:f:/g/, /:b:/g/) or legacy ApiConnection/Invoker bindings; use canonical driveId+itemId links and OpenApiConnection (UX-23, STK-08).",
    ),
)

_TABLE_TAG_RE = re.compile(r"(?is)<table\b[^>]*>")
_GLOBAL_TABLE_TABULAR_RE = re.compile(
    r"(?is)(?:^|[},;\s])(?:table|\.[a-z0-9_-]*table[a-z0-9_-]*)\s*\{[^}]*tabular-nums"
)


def detect_domain(query: str) -> str:
    """Auto-detect the most relevant UI/UX domain from a search query."""
    query_lower = query.lower()
    domain_order = ("product", "ux", "chart", "style", "typography", "stack")
    scored = [
        (dom, sum(1 for kw in DOMAIN_KEYWORDS[dom] if kw in query_lower)) for dom in domain_order
    ]
    ranked = sorted(scored, key=lambda item: (-item[1], domain_order.index(item[0])))
    return ranked[0][0] if ranked[0][1] > 0 else "product"


def search(query: str, domain: str | None = None, max_results: int = MAX_RESULTS) -> dict[str, Any]:
    """Search a specific UI/UX domain or auto-detect from query keywords."""
    resolved_domain = domain if domain in CSV_CONFIG else detect_domain(query)
    config = CSV_CONFIG[resolved_domain]
    filepath = DATA_DIR / str(config["file"])
    if not filepath.exists():
        return {"error": f"File not found: {filepath}", "domain": resolved_domain}
    results = _search_csv(
        filepath,
        list(config["search_cols"]),
        list(config["output_cols"]),
        query,
        max_results,
    )
    return {
        "domain": resolved_domain,
        "query": query,
        "file": str(config["file"]),
        "count": len(results),
        "results": results,
    }


def search_all(query: str, max_results: int = 2) -> dict[str, list[dict[str, str]]]:
    """Search across all 6 UI/UX domains (product, style, ux, chart, typography, stack)."""
    combined: dict[str, list[dict[str, str]]] = {}
    for domain in ("product", "style", "ux", "chart", "typography", "stack"):
        res = search(query, domain=domain, max_results=max_results)
        if res.get("results"):
            combined[domain] = list(res["results"])
    return combined


def compute_design_dials(
    density: int = 8,
    variance: int = 4,
    motion: int = 3,
) -> dict[str, str]:
    """Compute quantitative CSS & layout tokens from the 3 UI/UX Design Dials (1-10)."""
    d_val = max(1, min(10, int(density)))
    v_val = max(1, min(10, int(variance)))
    m_val = max(1, min(10, int(motion)))

    if d_val >= 8:
        density_spec = "Dense Portal / Cockpit (--space: 4px/8px/12px/16px/24px, control: 28px-32px, tabular-nums)"
        surface_mode = "Operate"
    elif d_val >= 4:
        density_spec = "Balanced Workspace (--space: 8px/16px/24px/32px/48px, control: 34px-38px)"
        surface_mode = "Operate / Read"
    else:
        density_spec = (
            "Spacious Editorial / Marketing (--space: 16px/24px/48px/64px/96px, control: 40px-48px)"
        )
        surface_mode = "Persuade"

    if v_val <= 3:
        variance_spec = "Strict Symmetrical Swiss / 12-Col Enterprise Grid (radius: 2px-4px)"
    elif v_val <= 7:
        variance_spec = "Balanced Modular Split / Docked Inspector Panels (radius: 6px-8px)"
    else:
        variance_spec = "Asymmetric Bento / Editorial Showcase (radius: 12px-16px)"

    if m_val <= 3:
        motion_spec = "Restrained State-Only Micro-Transitions (150ms-200ms ease-out, zero page-load choreography)"
    elif m_val <= 7:
        motion_spec = (
            "Standard Semantic View Transitions (200ms-250ms shared-element & Suspense reveal)"
        )
    else:
        motion_spec = "High-Craft Interactive Choreography (1 core effect + 1 supporting effect, prefers-reduced-motion guard)"

    return {
        "surface_mode": surface_mode,
        "density_dial": f"{d_val}/10 -> {density_spec}",
        "variance_dial": f"{v_val}/10 -> {variance_spec}",
        "motion_dial": f"{m_val}/10 -> {motion_spec}",
    }


def _relative_luminance(hex_color: str) -> float:
    """Compute WCAG 2.x relative luminance from a 6-digit hex color string."""
    clean = hex_color.strip().lstrip("#")
    if len(clean) == 3:
        clean = "".join(ch * 2 for ch in clean)
    if len(clean) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    channels: list[float] = []
    for i in (0, 2, 4):
        srgb = int(clean[i : i + 2], 16) / 255.0
        lin = srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4
        channels.append(lin)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def compute_contrast_ratio(fg_hex: str, bg_hex: str) -> dict[str, Any]:
    """Calculate WCAG 2.1/2.2 contrast ratio and AA/AAA pass status between two hex colors."""
    lum1 = _relative_luminance(fg_hex)
    lum2 = _relative_luminance(bg_hex)
    lighter, darker = max(lum1, lum2), min(lum1, lum2)
    ratio = round((lighter + 0.05) / (darker + 0.05), 2)
    return {
        "foreground": fg_hex,
        "background": bg_hex,
        "ratio": ratio,
        "ratio_label": f"{ratio:.2f}:1",
        "wcag_aa_normal": ratio >= 4.5,
        "wcag_aa_large": ratio >= 3.0,
        "wcag_aaa_normal": ratio >= 7.0,
        "wcag_aaa_large": ratio >= 4.5,
    }


def audit_ui_code(content: str) -> list[dict[str, Any]]:
    """Scan HTML/JSX/TSX/CSS source content for deterministic UI slop and portal anti-patterns."""
    findings: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    for rule_id, category, pattern, message in UI_SLOP_PATTERNS:
        for match in pattern.finditer(content):
            line_no = content.count("\n", 0, match.start()) + 1
            if (line_no, rule_id) not in seen:
                seen.add((line_no, rule_id))
                findings.append(
                    {
                        "rule_id": rule_id,
                        "category": category,
                        "line": line_no,
                        "message": message,
                    }
                )
    if not _GLOBAL_TABLE_TABULAR_RE.search(content):
        for match in _TABLE_TAG_RE.finditer(content):
            if "tabular-nums" not in match.group(0).lower():
                line_no = content.count("\n", 0, match.start()) + 1
                if (line_no, "SLOP-06") not in seen:
                    seen.add((line_no, "SLOP-06"))
                    findings.append(
                        {
                            "rule_id": "SLOP-06",
                            "category": "Operate Mode Numeric Alignment",
                            "line": line_no,
                            "message": "Data <table> detected without tabular-nums class or font-variant-numeric: tabular-nums.",
                        }
                    )
    findings.sort(key=lambda item: (int(item["line"]), str(item["rule_id"])))
    return findings
