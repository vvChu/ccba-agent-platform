"""
Tests for SEOAuditor deep module interface and legacy functions in ccba_ai.services.seo.
"""

from pathlib import Path

from ccba_ai.services.seo import SEOAuditor, audit_markdown


def test_seo_auditor_markdown_content():
    auditor = SEOAuditor()
    content = (
        """# Test Title

This is a paragraph with more than 300 words. Let us generate enough text for word count testing.
![Alt text](http://example.com/image.png)
[Example Link](http://example.com)
"""
        + " word" * 300
    )

    result = auditor.audit(content=content, format_hint="markdown")
    assert result["score"] == 100
    assert any("H1 count: 1" in check for check in result["checks"])
    assert len(result["issues"]) == 0


def test_seo_auditor_markdown_issues():
    auditor = SEOAuditor()
    content = """# H1 First
# H1 Second

### Heading 3 without Heading 2

![](image.jpg)
Short text.
"""
    result = auditor.audit(content=content, format_hint="md")
    assert result["score"] < 100
    assert len(result["issues"]) >= 3
    assert any("Multiple H1 headings" in issue for issue in result["issues"])
    assert any("Heading hierarchy skip" in issue for issue in result["issues"])
    assert any("empty alt text" in issue for issue in result["issues"])


def test_seo_auditor_file_audit(tmp_path: Path):
    doc_path = tmp_path / "sample.md"
    doc_path.write_text(
        "# Unique Title\n\n![Valid alt](img.png)\n\n" + " word" * 310, encoding="utf-8"
    )

    auditor = SEOAuditor()
    result = auditor.audit(target=doc_path)
    assert result["score"] == 100
    assert result["file_name"] == "sample.md"


def test_legacy_wrappers_compatibility():
    content = "# Title\n\nParagraph text here."
    res_md = audit_markdown(content)
    assert "score" in res_md

    res_auditor = SEOAuditor().audit_markdown(content)
    assert res_md == res_auditor
