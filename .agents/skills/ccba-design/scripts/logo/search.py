#!/usr/bin/env python3
"""
Logo Design Search - CLI for searching logo design guidelines
Usage: python search.py "<query>" [--domain <domain>] [--max-results 3]
       python search.py "<query>" --design-brief [-p "Brand Name"]

Domains: style, color, industry
"""

import argparse

from core import CSV_CONFIG, MAX_RESULTS, search, search_all


def format_output(result):
    """Format results for Claude consumption (token-optimized)"""
    if "error" in result:
        return f"Error: {result['error']}"

    output = []
    output.append("## Logo Design Search Results")
    output.append(f"**Domain:** {result['domain']} | **Query:** {result['query']}")
    output.append(f"**Source:** {result['file']} | **Found:** {result['count']} results\n")

    for i, row in enumerate(result["results"], 1):
        output.append(f"### Result {i}")
        for key, value in row.items():
            value_str = str(value)
            if len(value_str) > 300:
                value_str = value_str[:300] + "..."
            output.append(f"- **{key}:** {value_str}")
        output.append("")

    return "\n".join(output)


def _append_industry_and_style(output, results):
    if "industry" in results:
        output.append("## INDUSTRY ANALYSIS")
        for r in results["industry"]:
            output.extend([
                f"**Industry:** {r.get('Industry', 'N/A')}",
                f"- Recommended Styles: {r.get('Recommended Styles', 'N/A')}",
                f"- Colors: {r.get('Primary Colors', 'N/A')}",
                f"- Typography: {r.get('Typography', 'N/A')}",
                f"- Symbols: {r.get('Common Symbols', 'N/A')}",
                f"- Mood: {r.get('Mood', 'N/A')}",
                f"- Best Practices: {r.get('Best Practices', 'N/A')}",
                f"- Avoid: {r.get('Avoid', 'N/A')}",
                "",
            ])
    if "style" in results:
        output.append("## STYLE RECOMMENDATIONS")
        for r in results["style"]:
            output.extend([
                f"**{r.get('Style Name', 'N/A')}** ({r.get('Category', 'N/A')})",
                f"- Colors: {r.get('Primary Colors', 'N/A')} | {r.get('Secondary Colors', 'N/A')}",
                f"- Typography: {r.get('Typography', 'N/A')}",
                f"- Effects: {r.get('Effects', 'N/A')}",
                f"- Best For: {r.get('Best For', 'N/A')}",
                f"- Complexity: {r.get('Complexity', 'N/A')}",
                "",
            ])


def generate_design_brief(query, brand_name=None):
    """Generate a comprehensive logo design brief based on query"""
    results = search_all(query, max_results=2)
    title = f"  LOGO DESIGN BRIEF: {brand_name.upper()}" if brand_name else "  LOGO DESIGN BRIEF"
    output = ["=" * 60, title, "=" * 60, f"  Query: {query}", "=" * 60, ""]
    _append_industry_and_style(output, results)
    if "color" in results:
        output.append("## COLOR PALETTE OPTIONS")
        for r in results["color"]:
            output.extend([
                f"**{r.get('Palette Name', 'N/A')}**",
                f"- Primary: {r.get('Primary Hex', 'N/A')}",
                f"- Secondary: {r.get('Secondary Hex', 'N/A')}",
                f"- Accent: {r.get('Accent Hex', 'N/A')}",
                f"- Background: {r.get('Background Hex', 'N/A')}",
                f"- Psychology: {r.get('Psychology', 'N/A')}",
                "",
            ])
    output.append("=" * 60)
    return "\n".join(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Logo Design Search")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()), help="Search domain")
    parser.add_argument(
        "--max-results", "-n", type=int, default=MAX_RESULTS, help="Max results (default: 3)"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--design-brief", "-db", action="store_true", help="Generate comprehensive design brief"
    )
    parser.add_argument(
        "--brand-name", "-p", type=str, default=None, help="Brand name for design brief"
    )

    args = parser.parse_args()

    if args.design_brief:
        result = generate_design_brief(args.query, args.brand_name)
        print(result)
    else:
        result = search(args.query, args.domain, args.max_results)
        if args.json:
            import json

            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))
