"""
Service module for technical SEO compliance audits of Markdown and HTML files.
Provides structured compliance scoring and detailed validation reports via SEOAuditor.
"""

import re
from pathlib import Path
from typing import Any

from ccba_ai.models import SEOAuditResult


def _check_h1_count(count: int, *, is_html: bool, checks: list[str], issues: list[str]) -> None:
    """Validate single H1 rule and append check/issue messages."""
    checks.append(f"H1 count: {count}")
    if count == 0:
        issues.append(
            "Missing H1 heading (<h1>). Add exactly one H1 to the page."
            if is_html
            else "Missing H1 heading (# heading). Add exactly one H1 to the top of the file."
        )
    elif count > 1:
        scope = "page" if is_html else "document"
        issues.append(f"Multiple H1 headings found ({count}). Keep exactly one H1 per {scope}.")


def _check_heading_hierarchy(
    headings: list[tuple[int, str]], checks: list[str], issues: list[str]
) -> bool:
    """Validate sequential heading levels and append check/issue messages."""
    prev_level = 0
    hierarchy_broken = False
    for level, h_text in headings:
        if prev_level > 0 and level > prev_level + 1:
            issues.append(
                f"Heading hierarchy skip: H{level} '{h_text}' directly follows H{prev_level}."
            )
            hierarchy_broken = True
        prev_level = level
    checks.append(
        f"Heading hierarchy: {'Broken' if hierarchy_broken else 'Valid'} ({len(headings)} total headings)"
    )
    return hierarchy_broken


def _check_html_metadata(soup: Any, checks: list[str], issues: list[str]) -> tuple[bool, bool]:
    """Validate HTML <title> and <meta name='description'> tags; return (has_title, has_desc)."""
    title_tag = soup.find("title")
    if not title_tag or not title_tag.get_text().strip():
        issues.append("Missing or empty <title> tag in the HTML head.")
        checks.append("Title tag: Missing")
    else:
        checks.append(f"Title tag: Present ('{title_tag.get_text().strip()}')")

    meta_desc = soup.find("meta", attrs={"name": "description"})
    desc_attr = meta_desc.get("content") if meta_desc else None
    if not meta_desc or not desc_attr or not str(desc_attr).strip():
        issues.append(
            'Missing or empty meta description (<meta name="description">) in the HTML head.'
        )
        checks.append("Meta description: Missing")
    else:
        checks.append("Meta description: Present")
    return bool(title_tag), bool(meta_desc)


class SEOAuditor:
    """Deep module providing unified technical SEO compliance audits.

    Hides content parsing, heading hierarchy checks, alt text validation, metadata checks,
    and scoring deductions behind a simple, high-leverage interface.
    """

    def audit_markdown(self, content: str) -> SEOAuditResult:
        """Analyze Markdown content for SEO best practices."""
        issues: list[str] = []
        checks: list[str] = []

        h1s = re.findall(r"^#\s+(.+)$", content, re.MULTILINE)
        _check_h1_count(len(h1s), is_html=False, checks=checks, issues=issues)

        raw_headings = re.findall(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)
        hierarchy_broken = _check_heading_hierarchy(
            [(len(h), text) for h, text in raw_headings], checks, issues
        )

        images = re.findall(r"!\[(.*?)\]\((.*?)\)", content)
        empty_alts = sum(1 for alt, _url in images if not alt.strip())
        checks.append(f"Images with alt tags: {len(images) - empty_alts}/{len(images)}")
        if empty_alts > 0:
            issues.append(
                f"Found {empty_alts} image(s) with empty alt text. Add descriptive alt text for accessibility and SEO."
            )

        links = re.findall(r"\[(.*?)\]\((http.*?)\)", content)
        checks.append(f"Outbound links: {len(links)}")

        words = len(content.split())
        checks.append(f"Word count: {words} words")
        if words < 300:
            issues.append(
                "Word count is under 300 words. Consider adding more high-quality content to rank better."
            )

        deductions = (
            (30 if len(h1s) != 1 else 0)
            + (20 if hierarchy_broken else 0)
            + (empty_alts * 10)
            + (15 if words < 300 else 0)
        )
        return SEOAuditResult(score=max(0, 100 - deductions), checks=checks, issues=issues)

    def audit_html(self, content: str) -> SEOAuditResult:
        """Analyze HTML content for SEO best practices."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return SEOAuditResult(
                score=0, error="beautifulsoup4 package is required for HTML SEO audits."
            )

        soup = BeautifulSoup(content, "html.parser")
        issues: list[str] = []
        checks: list[str] = []

        h1s = soup.find_all("h1")
        _check_h1_count(len(h1s), is_html=True, checks=checks, issues=issues)

        raw_headings = soup.find_all(re.compile(r"^h[1-6]$"))
        hierarchy_broken = _check_heading_hierarchy(
            [(int(h.name[1]), h.get_text().strip()) for h in raw_headings], checks, issues
        )

        images = soup.find_all("img")
        empty_alts = sum(
            1 for img in images if not img.get("alt") or not str(img.get("alt")).strip()
        )
        checks.append(f"Images with alt tags: {len(images) - empty_alts}/{len(images)}")
        if empty_alts > 0:
            issues.append(
                f"Found {empty_alts} image(s) with missing or empty alt text. Add alt text for accessibility."
            )

        checks.append(f"Outbound links: {len(soup.find_all('a', href=re.compile(r'^http')))}")
        has_title, has_desc = _check_html_metadata(soup, checks, issues)

        words = len(soup.get_text().split())
        checks.append(f"Word count: {words} words")
        if words < 300:
            issues.append("Word count is under 300 words. Consider adding more high-quality copy.")

        deductions = (
            (20 if len(h1s) != 1 else 0)
            + (15 if hierarchy_broken else 0)
            + (empty_alts * 10)
            + (0 if has_title else 20)
            + (0 if has_desc else 15)
            + (10 if words < 300 else 0)
        )
        return SEOAuditResult(score=max(0, 100 - deductions), checks=checks, issues=issues)

    def audit(
        self,
        target: str | Path | None = None,
        *,
        content: str | None = None,
        format_hint: str | None = None,
        workspace_root: Path | None = None,
    ) -> SEOAuditResult:
        """Unified audit entrypoint accepting file path or raw string content."""
        if content is not None:
            fmt = (format_hint or "md").lower()
            if fmt in ("html", "htm"):
                res = self.audit_html(content)
            else:
                res = self.audit_markdown(content)
            if res.error:
                raise RuntimeError(res.error)
            return res

        if target is None:
            raise ValueError("Either target file path or content must be provided.")

        root = workspace_root or Path.cwd()
        path = Path(target)
        if not path.is_absolute():
            path = root / path

        if not path.exists():
            raise FileNotFoundError(f"File {target} not found.")

        try:
            file_content = path.read_text(encoding="utf-8")
        except Exception as e:
            raise OSError(f"Could not read file: {e}") from e

        ext = path.suffix.lower()
        if ext in (".html", ".htm"):
            result = self.audit_html(file_content)
        else:
            result = self.audit_markdown(file_content)

        if result.error:
            raise RuntimeError(result.error)

        result.file_name = path.name
        return result


def audit_markdown(content: str) -> SEOAuditResult:
    """Analyze Markdown content for SEO best practices (backward compatibility wrapper)."""
    return SEOAuditor().audit_markdown(content)


def audit_html(content: str) -> SEOAuditResult:
    """Analyze HTML content for SEO best practices (backward compatibility wrapper)."""
    return SEOAuditor().audit_html(content)


def audit_file(file_path: str | Path, workspace_root: Path | None = None) -> SEOAuditResult:
    """Audit a file (Markdown or HTML) for SEO best practices (backward compatibility wrapper)."""
    return SEOAuditor().audit(target=file_path, workspace_root=workspace_root)
