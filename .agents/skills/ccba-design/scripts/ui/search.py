#!/usr/bin/env python3
"""UI/UX & Web Portal Design Search CLI — Query styles, UX rules, charts, products, dials, contrast & slop audit."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from core import (  # noqa: E402
    CSV_CONFIG,
    MAX_RESULTS,
    audit_ui_code,
    compute_contrast_ratio,
    compute_design_dials,
    search,
    search_all,
)


def format_output(result: dict[str, Any]) -> str:
    """Format single-domain BM25 search results for compact LLM consumption."""
    if "error" in result:
        return f"Error: {result['error']}"
    lines: list[str] = [
        "## UI/UX & Portal Design Search Results",
        f"**Domain:** {result['domain']} | **Query:** {result['query']}",
        f"**Source:** {result['file']} | **Found:** {result['count']} results\n",
    ]
    for idx, row in enumerate(result.get("results", []), 1):
        lines.append(f"### Result {idx}")
        for key, value in row.items():
            val_str = str(value)
            if len(val_str) > 320:
                val_str = val_str[:320] + "..."
            lines.append(f"- **{key}:** {val_str}")
        lines.append("")
    return "\n".join(lines)


def _append_domain_section(lines: list[str], title: str, rows: list[dict[str, str]]) -> None:
    """Append a formatted multi-domain section to the design system brief."""
    if not rows:
        return
    lines.append(f"## {title}")
    for row in rows:
        for key, val in row.items():
            lines.append(f"- **{key}:** {val}")
        lines.append("")


def generate_design_system_brief(
    query: str,
    project_name: str | None = None,
    density: int = 8,
    variance: int = 4,
    motion: int = 3,
    stack_query: str | None = None,
) -> str:
    """Generate a complete Portal/Web Design System specification combining BM25 datasets and Design Dials."""
    dials = compute_design_dials(density=density, variance=variance, motion=motion)
    results = search_all(query, max_results=2)
    stack_rows = (
        list(search(stack_query, domain="stack", max_results=1).get("results", []))
        if stack_query
        else results.get("stack", [])
    )
    header = (
        f"  UI/UX & PORTAL DESIGN SYSTEM: {project_name.upper()}"
        if project_name
        else "  UI/UX & PORTAL DESIGN SYSTEM BRIEF"
    )
    lines: list[str] = [
        "=" * 68,
        header,
        "=" * 68,
        f"  Query: {query}",
        f"  Surface Mode: {dials['surface_mode']}",
        f"  Density Dial: {dials['density_dial']}",
        f"  Variance Dial: {dials['variance_dial']}",
        f"  Motion Dial: {dials['motion_dial']}",
        "=" * 68,
        "",
    ]
    _append_domain_section(lines, "1. PRODUCT & PORTAL ARCHETYPE", results.get("product", []))
    _append_domain_section(lines, "2. RECOMMENDED UI STYLE & GEOMETRY", results.get("style", []))
    _append_domain_section(lines, "3. CRITICAL UX & WCAG 2.2 GUARDRAILS", results.get("ux", []))
    _append_domain_section(lines, "4. DATA VISUALIZATION & CHARTS", results.get("chart", []))
    _append_domain_section(
        lines, "5. VIETNAMESE-SAFE TYPOGRAPHY & PAIRING", results.get("typography", [])
    )
    _append_domain_section(lines, "6. STACK IMPLEMENTATION GUARDRAILS", stack_rows)
    lines.append("=" * 68)
    return "\n".join(lines)


def persist_design_system(
    brief_text: str,
    base_dir: Path,
    project_name: str | None = None,
    page_slug: str | None = None,
) -> Path:
    """Persist MASTER.md or pages/<page-slug>.md under base_dir/<project-slug>/."""
    slug = re.sub(r"[^a-z0-9-]+", "-", (project_name or "default-portal").lower()).strip("-")
    target_root = base_dir / (slug or "default-portal")
    if page_slug:
        clean_page = re.sub(r"[^a-z0-9-]+", "-", page_slug.lower()).strip("-")
        out_path = target_root / "pages" / f"{clean_page}.md"
    else:
        out_path = target_root / "MASTER.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(brief_text + "\n", encoding="utf-8")
    return out_path


def _build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser for UI/UX search, persistence, contrast, and code audit."""
    parser = argparse.ArgumentParser(description="UI/UX & Web Portal Design Search Engine")
    parser.add_argument("query", nargs="?", default="portal", help="Search query")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()), help="Target domain")
    parser.add_argument("--stack", "-s", type=str, default=None, help="Target implementation stack")
    parser.add_argument("--max-results", "-n", type=int, default=MAX_RESULTS, help="Max results")
    parser.add_argument("--design-system", "-ds", action="store_true", help="Generate full brief")
    parser.add_argument("--project", "-p", type=str, default=None, help="Project name")
    parser.add_argument("--density", type=int, default=8, help="Density dial 1-10 (default: 8)")
    parser.add_argument("--variance", type=int, default=4, help="Variance dial 1-10 (default: 4)")
    parser.add_argument("--motion", type=int, default=3, help="Motion dial 1-10 (default: 3)")
    parser.add_argument("--persist", type=str, default=None, help="Directory to save MASTER.md")
    parser.add_argument("--page", type=str, default=None, help="Optional page override slug")
    parser.add_argument("--contrast", type=str, default=None, help="Check FG,BG hex pair")
    parser.add_argument("--audit-file", type=str, default=None, help="Audit UI file for slop")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    return parser


def _handle_special_modes(args: argparse.Namespace) -> bool:
    """Handle --contrast, --audit-file, and --design-system modes; return True if handled."""
    if args.contrast:
        parts = [p.strip() for p in args.contrast.split(",") if p.strip()]
        if len(parts) != 2:
            raise SystemExit("Error: --contrast requires 'FG_HEX,BG_HEX' (e.g. '#FFFFFF,#363883')")
        print(json.dumps(compute_contrast_ratio(parts[0], parts[1]), indent=2, ensure_ascii=False))
        return True
    if args.audit_file:
        target = Path(args.audit_file)
        findings = audit_ui_code(target.read_text(encoding="utf-8"))
        print(
            json.dumps(
                {"file": str(target), "count": len(findings), "findings": findings}, indent=2
            )
        )
        return True
    if args.design_system:
        brief = generate_design_system_brief(
            args.query, args.project, args.density, args.variance, args.motion, args.stack
        )
        if args.persist:
            saved = persist_design_system(brief, Path(args.persist), args.project, args.page)
            print(f"[OK] Persisted design system to: {saved}")
        print(brief)
        return True
    return False


def main() -> None:
    """Execute CLI entrypoint for UI/UX search, design system brief, contrast, or code audit."""
    args = _build_parser().parse_args()
    if _handle_special_modes(args):
        return
    query = args.stack if args.stack and args.domain is None else args.query
    domain = "stack" if args.stack and args.domain is None else args.domain
    res = search(query, domain, args.max_results)
    print(json.dumps(res, indent=2, ensure_ascii=False) if args.json else format_output(res))


if __name__ == "__main__":
    main()
