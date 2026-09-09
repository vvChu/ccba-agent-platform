"""Academic writing compilation and stylistic verification engine.

Provides deterministic tools for academic papers:
- Audit argumentative microstructure (Swales CARS model, passive voice, nominalizations).
- Scaffold manuscript markdown templates.
- Compile academic Markdown papers to standardized publication-ready DOCX.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from pydantic import BaseModel, Field

# Style patterns
PASSIVE_VOICE_RE = re.compile(
    r"\b(was|were|is|are|be|been|being|am)\s+([a-z]+ed|shown|done|written|found|made|seen|built|taken|kept|given|run|spent|evaluated|utilized|analyzed|presented|discussed|extracted|created|implemented)\b",
    re.IGNORECASE,
)

INTENSIFIERS = {
    "clearly": "Clearly appeals to emotion and lowers objectivity.",
    "obviously": "Obviously assumes facts and reduces scientific tone.",
    "basically": "Basically is too informal for academic writing.",
    "really": "Really is an informal intensifier that should be omitted.",
    "very": "Very is a weak intensifier; select a stronger adjective instead.",
    "fairly": "Fairly reduces preciseness and authority.",
    "rather": "Rather weakens the assertiveness of the claim.",
    "quite": "Quite is vague and adds unnecessary wordiness.",
}

NOMINALIZATIONS = {
    r"\bthere\s+(is|are)\b": "Weak existential construction; use an active verb.",
    r"\bprovide\s+(an\s+)?argument\b": "Nominalization: use active verb 'argue'.",
    r"\bmake\s+(a\s+)?decision\b": "Nominalization: use active verb 'decide'.",
    r"\bcause\s+(a\s+)?disruption\b": "Nominalization: use active verb 'disrupt'.",
    r"\bperform\s+(an\s+)?analysis\b": "Nominalization: use active verb 'analyze'.",
}

VIETNAMESE_TYPOS = {
    r"\bbetong\b": "bê tông",
    r"\bthep\b": "thép",
    r"\bcua\s+di\b": "cửa đi",
    r"\bxay\s+dung\b": "xây dựng",
    r"\bcb\b": "cảm biến",
    r"\bdt\b": "dự toán",
    r"\bpccc\b": "phòng cháy chữa cháy",
    r"\bmep\b": "cơ điện (MEP)",
    r"\btk\b": "thiết kế",
    r"\btc\b": "thi công",
}

CARS_SIGNALS = {
    "Move 1 (Territory)": [
        "has been widely studied",
        "play a key role",
        "recent advances in",
        "traditionally",
        "important role",
        "critical issue",
        "widely used",
        "đã được nghiên cứu rộng rãi",
        "đóng vai trò quan trọng",
        "những tiến bộ gần đây",
        "áp dụng rộng rãi",
    ],
    "Move 2 (Niche)": [
        "however",
        "although",
        "yet",
        "little research",
        "remains unclear",
        "fails to",
        "is limited",
        "not fully understood",
        "tuy nhiên",
        "chưa được nghiên cứu",
        "vẫn chưa rõ ràng",
        "còn hạn chế",
    ],
    "Move 3 (Occupy)": [
        "in this paper",
        "we propose",
        "this study aims to",
        "we present",
        "in this study",
        "trong bài báo này",
        "chúng tôi đề xuất",
        "nghiên cứu này nhằm",
    ],
}


class AuditFinding(BaseModel):
    """Specific finding from academic writing microstructure audit."""

    category: str
    severity: str = "WARNING"
    message: str
    line: int | None = None
    suggestion: str | None = None


class MicrostructureReport(BaseModel):
    """Comprehensive report on the argumentative microstructure of a paper."""

    total_paragraphs: int
    overall_readability_score: float
    sections_found: list[str] = Field(default_factory=list)
    passive_voice_stats: dict[str, Any] = Field(default_factory=dict)
    cars_moves_found: list[str] = Field(default_factory=list)
    findings: list[AuditFinding] = Field(default_factory=list)


def parse_academic_sections(content: str) -> dict[str, list[str]]:
    """Parse Markdown content into academic sections based on heading keywords."""
    sections: dict[str, list[str]] = {
        "Introduction": [],
        "Methods": [],
        "Results": [],
        "Discussion": [],
        "Other": [],
    }
    current_section = "Other"

    for line in content.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("#"):
            lower_header = trimmed.lower()
            if any(k in lower_header for k in ["introduction", "mở đầu", "mở bài"]):
                current_section = "Introduction"
            elif any(k in lower_header for k in ["method", "material", "phương pháp", "vật liệu"]):
                current_section = "Methods"
            elif any(k in lower_header for k in ["result", "kết quả"]):
                current_section = "Results"
            elif any(k in lower_header for k in ["discussion", "thảo luận"]):
                current_section = "Discussion"
            elif trimmed.startswith("## "):
                current_section = "Other"

        sections[current_section].append(line)

    return sections


def audit_microstructure(paper_markdown: str | Path) -> MicrostructureReport:
    """Audit the argumentative microstructure of an academic manuscript.

    Args:
        paper_markdown: Raw Markdown string or path to Markdown file.

    Returns:
        MicrostructureReport containing passive voice ratios, CARS signals, and stylistic findings.
    """
    if isinstance(paper_markdown, Path) or (
        isinstance(paper_markdown, str)
        and "\n" not in paper_markdown
        and Path(paper_markdown).is_file()
    ):
        content = Path(paper_markdown).read_text(encoding="utf-8")
    else:
        content = str(paper_markdown)

    sections = parse_academic_sections(content)
    findings: list[AuditFinding] = []

    # 1. Passive voice analysis
    passive_stats: dict[str, Any] = {}
    thresholds = {
        "Introduction": (20.0, "max"),
        "Methods": (40.0, "min"),
        "Results": (25.0, "max"),
        "Discussion": (25.0, "max"),
    }

    for sec_name, lines in sections.items():
        if sec_name == "Other" or not lines:
            continue
        text = " ".join(lines)
        sentences = [s.strip() for s in re.split(r"\. |\? |\! ", text) if s.strip()]
        if not sentences:
            continue
        passive_count = sum(1 for s in sentences if PASSIVE_VOICE_RE.search(s))
        ratio = (passive_count / len(sentences)) * 100
        passive_stats[sec_name] = {
            "total_sentences": len(sentences),
            "passive_sentences": passive_count,
            "ratio_percent": round(ratio, 1),
        }

        if sec_name in thresholds:
            limit, direction = thresholds[sec_name]
            if direction == "max" and ratio > limit:
                findings.append(
                    AuditFinding(
                        category="Passive Voice",
                        severity="WARNING",
                        message=f"{sec_name} passive voice ratio {ratio:.1f}% exceeds threshold {limit:.1f}%",
                        suggestion="Rewrite sentences in active voice.",
                    )
                )
            elif direction == "min" and ratio < limit:
                findings.append(
                    AuditFinding(
                        category="Passive Voice",
                        severity="INFO",
                        message=f"{sec_name} passive voice ratio {ratio:.1f}% is below expected {limit:.1f}%",
                        suggestion="Consider using passive voice to maintain scientific objectivity.",
                    )
                )

    # 2. CARS signals in Introduction
    cars_found: list[str] = []
    intro_text = " ".join(sections.get("Introduction", [])).lower()
    for move_name, signals in CARS_SIGNALS.items():
        matched = [sig for sig in signals if sig in intro_text]
        if matched:
            cars_found.append(move_name)
        else:
            findings.append(
                AuditFinding(
                    category="CARS Model",
                    severity="WARNING",
                    message=f"Missing signal phrases for {move_name} in Introduction.",
                    suggestion=f"Include standard signaling phrases such as {signals[:2]}.",
                )
            )

    # 3. Intensifiers, nominalizations, typos
    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        line_lower = line.lower()
        for word, desc in INTENSIFIERS.items():
            if re.search(rf"\b{word}\b", line_lower):
                findings.append(
                    AuditFinding(
                        category="Intensifier",
                        severity="STYLE",
                        line=idx,
                        message=f"Avoid intensifier '{word}': {desc}",
                    )
                )
        for pattern, desc in NOMINALIZATIONS.items():
            if re.search(pattern, line_lower):
                findings.append(
                    AuditFinding(
                        category="Nominalization",
                        severity="STYLE",
                        line=idx,
                        message=f"Nominalization detected: {desc}",
                    )
                )
        for pattern, replacement in VIETNAMESE_TYPOS.items():
            if re.search(pattern, line_lower):
                findings.append(
                    AuditFinding(
                        category="Typo",
                        severity="WARNING",
                        line=idx,
                        message=f"Unstandardized or typo word: replace with '{replacement}'",
                    )
                )

    paragraphs = [p for p in content.split("\n\n") if p.strip()]
    readability = round(max(0.0, min(100.0, 100.0 - (len(findings) * 2.5))), 1)

    return MicrostructureReport(
        total_paragraphs=len(paragraphs),
        overall_readability_score=readability,
        sections_found=[k for k, v in sections.items() if v and k != "Other"],
        passive_voice_stats=passive_stats,
        cars_moves_found=cars_found,
        findings=findings,
    )


def scaffold_manuscript(
    output_path: Path | str,
    title: str = "Enter Your Research Paper Title Here",
) -> Path:
    """Generate a blank academic research paper template in Markdown.

    Args:
        output_path: Path to destination file.
        title: Title of the manuscript.

    Returns:
        Path to generated Markdown template.
    """
    out_file = Path(output_path)
    content = f"""---
title: "{title}"
authors:
  - name: "Author 1 Name"
    affiliation: "CCBA - Institute of Construction BIM, Vietnam"
    email: "author1@ccba.vn"
    corresponding: true
  - name: "Author 2 Name"
    affiliation: "Department of Construction IT, Vietnam"
---

# Abstract
Write a concise summary of your research, methodologies, and key findings here.

# Introduction
### 1.1. Bối cảnh nghiên cứu (Territory)
The application of modern engineering standards has been widely studied...

### 1.2. Khoảng trống nghiên cứu (Niche)
However, existing methods remain unclear regarding automated compliance verification...

### 1.3. Giải pháp đề xuất (Occupy)
In this paper, we propose a standardized framework to bridge this gap...

# Materials and Methods
The proposed methodology was implemented and evaluated using experimental datasets...

# Results
The empirical evaluation results demonstrate significant performance gains...

# Discussion
The implications of these findings are discussed in comparison with baseline benchmarks...

# References
- [1] Standard Guidelines for Construction Consulting.
"""
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(content, encoding="utf-8")
    return out_file


def export_paper_to_docx(
    markdown_path: Path | str,
    output_docx: Path | str | None = None,
) -> Path:
    """Compile academic Markdown into standard academic DOCX (IEEE/Elsevier layout).

    Args:
        markdown_path: Source markdown file path or markdown text.
        output_docx: Destination DOCX file path.

    Returns:
        Path to generated DOCX file.
    """
    path_obj = Path(markdown_path)
    if path_obj.exists() and path_obj.is_file():
        md_text = path_obj.read_text(encoding="utf-8")
        out_file = Path(output_docx) if output_docx is not None else path_obj.with_suffix(".docx")
    else:
        md_text = str(markdown_path)
        out_file = Path(output_docx) if output_docx is not None else Path("academic_paper.docx")

    doc = Document()

    # 1. Margins: 1 inch (72 pt) all sides
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # 2. Extract YAML Frontmatter if present
    frontmatter: dict[str, Any] = {}
    body_text = md_text
    if md_text.startswith("---"):
        parts = md_text.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                body_text = parts[2]
            except Exception:
                pass

    # Title page if frontmatter title is present
    if "title" in frontmatter:
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_title.paragraph_format.space_before = Pt(36)
        p_title.paragraph_format.space_after = Pt(18)
        run_title = p_title.add_run(str(frontmatter["title"]))
        run_title.font.name = "Times New Roman"
        run_title.font.size = Pt(16)
        run_title.font.bold = True

        authors = frontmatter.get("authors", [])
        if authors:
            p_auth = doc.add_paragraph()
            p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_auth.paragraph_format.space_after = Pt(24)
            for i, auth in enumerate(authors):
                name = auth.get("name", "") if isinstance(auth, dict) else str(auth)
                r_auth = p_auth.add_run(name)
                r_auth.font.name = "Times New Roman"
                r_auth.font.size = Pt(12)
                if i < len(authors) - 1:
                    p_auth.add_run(", ")

    # 3. Process Body Paragraphs
    for line in body_text.splitlines():
        trimmed = line.strip()
        if not trimmed:
            continue
        if trimmed.startswith("# "):
            p = doc.add_heading(trimmed[2:], level=1)
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
        elif trimmed.startswith("## "):
            p = doc.add_heading(trimmed[3:], level=2)
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
        elif trimmed.startswith("### "):
            p = doc.add_heading(trimmed[4:], level=3)
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)
        else:
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 2.0
            p.paragraph_format.first_line_indent = Inches(0.5)
            p.paragraph_format.space_after = Pt(6)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

            tokens = re.split(r"(\*\*.*?\*\*|\*.*?\*)", trimmed)
            for token in tokens:
                if not token:
                    continue
                if token.startswith("**") and token.endswith("**"):
                    r = p.add_run(token[2:-2])
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(12)
                    r.bold = True
                elif token.startswith("*") and token.endswith("*"):
                    r = p.add_run(token[1:-1])
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(12)
                    r.italic = True
                else:
                    r = p.add_run(token)
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(12)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_file))
    return out_file


__all__ = [
    "AuditFinding",
    "MicrostructureReport",
    "audit_microstructure",
    "scaffold_manuscript",
    "export_paper_to_docx",
]
