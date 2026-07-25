"""
Service module for technical SEO compliance audits of Markdown and HTML files.
Provides structured compliance scoring and detailed validation reports via SEOAuditor.
"""

import re
from pathlib import Path
from typing import Any


class SEOAuditor:
    """Deep module providing unified technical SEO compliance audits.

    Hides content parsing, heading hierarchy checks, alt text validation, metadata checks,
    and scoring deductions behind a simple, high-leverage interface.
    """

    def audit_markdown(self, content: str) -> dict[str, Any]:
        """Analyze Markdown content for SEO best practices."""
        issues = []
        checks = []

        # 1. H1 Count Check
        h1s = re.findall(r"^#\s+(.+)$", content, re.MULTILINE)
        checks.append(f"H1 count: {len(h1s)}")
        if len(h1s) == 0:
            issues.append(
                "Missing H1 heading (# heading). Add exactly one H1 to the top of the file."
            )
        elif len(h1s) > 1:
            issues.append(
                f"Multiple H1 headings found ({len(h1s)}). Keep exactly one H1 per document."
            )

        # 2. Heading Hierarchy
        headings = re.findall(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)
        prev_level = 0
        hierarchy_broken = False
        for h_hashes, h_text in headings:
            level = len(h_hashes)
            if prev_level > 0 and level > prev_level + 1:
                issues.append(
                    f"Heading hierarchy skip: H{level} '{h_text}' directly follows H{prev_level}."
                )
                hierarchy_broken = True
            prev_level = level
        checks.append(
            f"Heading hierarchy: {'Broken' if hierarchy_broken else 'Valid'} ({len(headings)} total headings)"
        )

        # 3. Image Alt Tags
        images = re.findall(r"!\[(.*?)\]\((.*?)\)", content)
        empty_alts = 0
        for alt, _url in images:
            if not alt.strip():
                empty_alts += 1
        checks.append(f"Images with alt tags: {len(images) - empty_alts}/{len(images)}")
        if empty_alts > 0:
            issues.append(
                f"Found {empty_alts} image(s) with empty alt text. Add descriptive alt text for accessibility and SEO."
            )

        # 4. Outbound Links check
        links = re.findall(r"\[(.*?)\]\((http.*?)\)", content)
        checks.append(f"Outbound links: {len(links)}")

        # 5. Length Check
        words = len(content.split())
        checks.append(f"Word count: {words} words")
        if words < 300:
            issues.append(
                "Word count is under 300 words. Consider adding more high-quality content to rank better."
            )

        # Calculate score
        total_deductions = 0
        if len(h1s) != 1:
            total_deductions += 30
        if hierarchy_broken:
            total_deductions += 20
        if empty_alts > 0:
            total_deductions += empty_alts * 10
        if words < 300:
            total_deductions += 15

        score = max(0, 100 - total_deductions)

        return {"score": score, "checks": checks, "issues": issues}

    def audit_html(self, content: str) -> dict[str, Any]:
        """Analyze HTML content for SEO best practices."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return {"error": "beautifulsoup4 package is required for HTML SEO audits."}

        soup = BeautifulSoup(content, "html.parser")
        issues = []
        checks = []

        # 1. H1 Count Check
        h1s = soup.find_all("h1")
        checks.append(f"H1 count: {len(h1s)}")
        if len(h1s) == 0:
            issues.append("Missing H1 heading (<h1>). Add exactly one H1 to the page.")
        elif len(h1s) > 1:
            issues.append(f"Multiple H1 headings found ({len(h1s)}). Keep exactly one H1 per page.")

        # 2. Heading Hierarchy
        headings = soup.find_all(re.compile(r"^h[1-6]$"))
        prev_level = 0
        hierarchy_broken = False
        for h in headings:
            level = int(h.name[1])
            h_text = h.get_text().strip()
            if prev_level > 0 and level > prev_level + 1:
                issues.append(
                    f"Heading hierarchy skip: H{level} '{h_text}' directly follows H{prev_level}."
                )
                hierarchy_broken = True
            prev_level = level
        checks.append(
            f"Heading hierarchy: {'Broken' if hierarchy_broken else 'Valid'} ({len(headings)} total headings)"
        )

        # 3. Image Alt Tags
        images = soup.find_all("img")
        empty_alts = 0
        for img in images:
            alt_attr = img.get("alt")
            if not alt_attr or not str(alt_attr).strip():
                empty_alts += 1
        checks.append(f"Images with alt tags: {len(images) - empty_alts}/{len(images)}")
        if empty_alts > 0:
            issues.append(
                f"Found {empty_alts} image(s) with missing or empty alt text. Add alt text for accessibility."
            )

        # 4. Outbound Links Check
        links = soup.find_all("a", href=re.compile(r"^http"))
        checks.append(f"Outbound links: {len(links)}")

        # 5. Metadata checks (Title & Description)
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

        # 6. Length Check
        text_content = soup.get_text()
        words = len(text_content.split())
        checks.append(f"Word count: {words} words")
        if words < 300:
            issues.append("Word count is under 300 words. Consider adding more high-quality copy.")

        # Calculate score
        total_deductions = 0
        if len(h1s) != 1:
            total_deductions += 20
        if hierarchy_broken:
            total_deductions += 15
        if empty_alts > 0:
            total_deductions += empty_alts * 10
        if not title_tag:
            total_deductions += 20
        if not meta_desc:
            total_deductions += 15
        if words < 300:
            total_deductions += 10

        score = max(0, 100 - total_deductions)

        return {"score": score, "checks": checks, "issues": issues}

    def audit(
        self,
        target: str | Path | None = None,
        *,
        content: str | None = None,
        format_hint: str | None = None,
        workspace_root: Path | None = None,
    ) -> dict[str, Any]:
        """Unified audit entrypoint accepting file path or raw string content."""
        if content is not None:
            fmt = (format_hint or "md").lower()
            if fmt in ("html", "htm"):
                res = self.audit_html(content)
            else:
                res = self.audit_markdown(content)
            if "error" in res:
                raise RuntimeError(res["error"])
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

        if "error" in result:
            raise RuntimeError(result["error"])

        result["file_name"] = path.name
        return result


def audit_markdown(content: str) -> dict[str, Any]:
    """Analyze Markdown content for SEO best practices (backward compatibility wrapper)."""
    return SEOAuditor().audit_markdown(content)


def audit_html(content: str) -> dict[str, Any]:
    """Analyze HTML content for SEO best practices (backward compatibility wrapper)."""
    return SEOAuditor().audit_html(content)


def audit_file(file_path: str | Path, workspace_root: Path | None = None) -> dict[str, Any]:
    """Audit a file (Markdown or HTML) for SEO best practices (backward compatibility wrapper)."""
    return SEOAuditor().audit(target=file_path, workspace_root=workspace_root)
