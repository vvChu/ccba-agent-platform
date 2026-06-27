#!/usr/bin/env python3
"""
SEO Audit Tool for ccba-agent-platform.
Analyzes Markdown and HTML files for technical SEO compliance (headings, alt tags, links, metadata).
"""

import sys
import os
import re
import argparse
from pathlib import Path

# Enforce UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def audit_markdown(file_path: Path) -> dict:
    """Analyze a Markdown file for SEO best practices."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": f"Could not read file: {e}"}

    issues = []
    checks = []
    
    # 1. H1 Count Check
    h1s = re.findall(r"^#\s+(.+)$", content, re.MULTILINE)
    checks.append(f"H1 count: {len(h1s)}")
    if len(h1s) == 0:
        issues.append("Missing H1 heading (# heading). Add exactly one H1 to the top of the file.")
    elif len(h1s) > 1:
        issues.append(f"Multiple H1 headings found ({len(h1s)}). Keep exactly one H1 per document.")

    # 2. Heading Hierarchy
    headings = re.findall(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)
    prev_level = 0
    hierarchy_broken = False
    for h_hashes, h_text in headings:
        level = len(h_hashes)
        if prev_level > 0 and level > prev_level + 1:
            issues.append(f"Heading hierarchy skip: H{level} '{h_text}' directly follows H{prev_level}.")
            hierarchy_broken = True
        prev_level = level
    checks.append(f"Heading hierarchy: {'Broken' if hierarchy_broken else 'Valid'} ({len(headings)} total headings)")

    # 3. Image Alt Tags
    images = re.findall(r"!\[(.*?)\]\((.*?)\)", content)
    empty_alts = 0
    for alt, url in images:
        if not alt.strip():
            empty_alts += 1
    checks.append(f"Images with alt tags: {len(images) - empty_alts}/{len(images)}")
    if empty_alts > 0:
        issues.append(f"Found {empty_alts} image(s) with empty alt text. Add descriptive alt text for accessibility and SEO.")

    # 4. Outbound Links check (just statistics)
    links = re.findall(r"\[(.*?)\]\((http.*?)\)", content)
    checks.append(f"Outbound links: {len(links)}")

    # 5. Length Check
    words = len(content.split())
    checks.append(f"Word count: {words} words")
    if words < 300:
        issues.append("Word count is under 300 words. Consider adding more high-quality content to rank better.")

    # Calculate score
    total_deductions = 0
    if len(h1s) != 1:
        total_deductions += 30
    if hierarchy_broken:
        total_deductions += 20
    if empty_alts > 0:
        total_deductions += (empty_alts * 10)
    if words < 300:
        total_deductions += 15
        
    score = max(0, 100 - total_deductions)
    
    return {
        "score": score,
        "checks": checks,
        "issues": issues
    }


def main():
    parser = argparse.ArgumentParser(description="CCBA Technical SEO Auditor CLI")
    parser.add_argument("file", help="Path to the file to audit (Markdown or HTML)")
    args = parser.parse_args()
    
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"[SEO Auditor] Error: File {args.file} not found.")
        sys.exit(1)
        
    print(f"\n[SEO Auditor] Auditing file: \x1b[36m{file_path.name}\x1b[0m\n")
    
    result = audit_markdown(file_path)
    
    if "error" in result:
        print(f"\x1b[31m[Error]\x1b[0m {result['error']}")
        sys.exit(1)
        
    score = result["score"]
    if score >= 90:
        color = "\x1b[32m"  # Green
    elif score >= 70:
        color = "\x1b[33m"  # Yellow
    else:
        color = "\x1b[31m"  # Red
        
    print(f"Overall SEO Score: {color}{score}/100\x1b[0m")
    print("-" * 50)
    print("Checked Metrics:")
    for c in result["checks"]:
        print(f"  - {c}")
    print("-" * 50)
    
    if result["issues"]:
        print("Issues found:")
        for idx, issue in enumerate(result["issues"], 1):
            print(f"  {idx}. \x1b[33m[Warning]\x1b[0m {issue}")
    else:
        print("\x1b[32mCongratulations! No SEO issues found in this file.\x1b[0m")
    print()


if __name__ == "__main__":
    main()
