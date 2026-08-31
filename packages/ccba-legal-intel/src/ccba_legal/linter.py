"""linter.py - Visual Parity & Cross-Link Linter for OKF Markdown Bundles (ADR 0029 & ADR 0030)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def lint_markdown_file(md_path: Path) -> list[str]:
    """Lint a single Markdown file for visual formatting issues (ADR 0029, ADR 0030)."""
    errors: list[str] = []
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()

        # 1. Check redundant bullet before CHÚ THÍCH / GHI CHÚ
        if re.match(
            r"^[-*+]\s+(?:\*\*)?(?:CHÚ THÍCH|GHI CHÚ|Chú thích|Ghi chú)\s*\d*[:\.]?", stripped
        ):
            if re.search(r"^[-*+]\s+(?:\*\*)?CHÚ THÍCH\s+\d+:", stripped):
                errors.append(
                    f"Line {idx}: Redundant bullet before footnote header: '{stripped}'"
                )

        # 2. Check raw HTML table tags (unless exempted)
        if re.search(r"<(?:table|thead|tbody|tr|th|td)\b", stripped, re.IGNORECASE):
            errors.append(f"Line {idx}: Unclean raw HTML table tag found: '{stripped}'")

    return errors


def lint_bundle_links(bundle_dir: Path) -> list[str]:
    """Verify internal anchors and relative markdown links across an OKF bundle."""
    errors: list[str] = []
    md_files = list(bundle_dir.rglob("*.md"))

    file_anchors: dict[str, set[str]] = {}
    file_contents: dict[str, str] = {}

    for md_f in md_files:
        rel_key = str(md_f.relative_to(bundle_dir)).replace("\\", "/")
        text = md_f.read_text(encoding="utf-8")
        anchors = set(re.findall(r'<a\s+(?:id|name)="([^"]+)"', text))
        file_anchors[rel_key] = anchors
        file_contents[rel_key] = text

    for rel_key, text in file_contents.items():
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)
        for link_text, target in links:
            target_clean = target.strip()
            if target_clean.startswith("http://") or target_clean.startswith("https://"):
                continue

            # Anchor in same or other bundle file
            if target_clean.startswith("#"):
                anchor = target_clean[1:]
                if anchor not in file_anchors[rel_key]:
                    found = any(anchor in anc_set for anc_set in file_anchors.values())
                    if not found:
                        errors.append(
                            f"[{rel_key}] Broken anchor link '{target}': anchor not found"
                        )
            else:
                parts = target_clean.split("#", 1)
                target_rel_path = parts[0]
                target_anchor = parts[1] if len(parts) > 1 else None

                current_dir = (bundle_dir / rel_key).parent
                target_file_path = (current_dir / target_rel_path).resolve()

                if not target_file_path.exists():
                    errors.append(
                        f"[{rel_key}] Broken relative link '{target}': target file does not exist"
                    )
                elif target_anchor:
                    try:
                        target_rel_key = str(target_file_path.relative_to(bundle_dir)).replace(
                            "\\", "/"
                        )
                        if (
                            target_rel_key in file_anchors
                            and target_anchor not in file_anchors[target_rel_key]
                        ):
                            errors.append(
                                f"[{rel_key}] Broken anchor '#{target_anchor}' in target file '{target_rel_key}'"
                            )
                    except ValueError:
                        pass

    return errors


def lint_target_path(target_path: Path, check_links: bool = True) -> dict[str, Any]:
    """Lint a file or directory for visual parity and link integrity."""
    result: dict[str, Any] = {
        "files_scanned": 0,
        "format_errors": 0,
        "link_errors": 0,
        "details": [],
    }

    if target_path.is_file() and target_path.suffix == ".md":
        result["files_scanned"] = 1
        errs = lint_markdown_file(target_path)
        if errs:
            result["format_errors"] += len(errs)
            result["details"].append({"file": str(target_path), "errors": errs})
    elif target_path.is_dir():
        md_files = sorted(target_path.rglob("*.md"))
        result["files_scanned"] = len(md_files)
        for md_f in md_files:
            errs = lint_markdown_file(md_f)
            if errs:
                result["format_errors"] += len(errs)
                result["details"].append({"file": str(md_f), "errors": errs})

        if check_links:
            # If target_path is an OKF bundle or contains bundles
            link_errs = lint_bundle_links(target_path)
            if link_errs:
                result["link_errors"] += len(link_errs)
                result["details"].append(
                    {"file": str(target_path), "link_errors": link_errs}
                )

    result["total_errors"] = result["format_errors"] + result["link_errors"]
    return result
