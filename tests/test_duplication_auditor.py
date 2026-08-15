"""TDD Unit Tests for Automated Hub Anti-Duplication Auditor."""

from pathlib import Path

from scripts.governance.duplication_auditor import (
    FORBIDDEN_DIRECTORIES,
    FORBIDDEN_RAW_SCRAPE_PATTERNS,
    DuplicationAuditor,
)


def test_clean_hub_passes_duplication_audit(tmp_path: Path):
    """Clean Hub directory with legitimate files should have zero duplication issues."""
    md_dir = tmp_path / ".md"
    md_dir.mkdir(parents=True)
    extracted_dir = md_dir / "extracted_docs"
    extracted_dir.mkdir(parents=True)

    # Add legitimate research files
    (extracted_dir / "01_Chien_luoc_dam_phan_hop_dong.md").write_text(
        "# Research", encoding="utf-8"
    )
    (extracted_dir / "notes_concept.md").write_text("# Notes", encoding="utf-8")
    (extracted_dir / "fb_academic_research_post.md").write_text("# Post", encoding="utf-8")

    auditor = DuplicationAuditor(tmp_path)
    issues = auditor.audit()
    assert len(issues) == 0


def test_forbidden_legal_docs_directory_detected(tmp_path: Path):
    """Adding .md/legal_docs directory on Hub must raise a hard duplication error."""
    legal_dir = tmp_path / ".md" / "legal_docs" / "01_vbpl"
    legal_dir.mkdir(parents=True)
    (legal_dir / "qcvn_06_2022.md").write_text("# QCVN 06", encoding="utf-8")

    auditor = DuplicationAuditor(tmp_path)
    issues = auditor.audit()

    assert len(issues) > 0
    assert any("legal_knowledge_path" in issue.message for issue in issues)
    assert any("ccba-legal-knowledge" in issue.message for issue in issues)


def test_forbidden_governance_constitution_detected(tmp_path: Path):
    """Adding .md/governance_constitution directory on Hub must raise a hard duplication error."""
    gov_dir = tmp_path / ".md" / "governance_constitution"
    gov_dir.mkdir(parents=True)
    (gov_dir / "01_qctk_2815.md").write_text("# QCTK 2815", encoding="utf-8")

    auditor = DuplicationAuditor(tmp_path)
    issues = auditor.audit()

    assert len(issues) > 0
    assert any("idop_path" in issue.message for issue in issues)
    assert any("idop-ccba-way" in issue.message for issue in issues)


def test_raw_scraped_law_text_file_detected(tmp_path: Path):
    """Adding raw scraped law .txt files in .md/extracted_docs must be blocked."""
    extracted_dir = tmp_path / ".md" / "extracted_docs"
    extracted_dir.mkdir(parents=True)
    (extracted_dir / "nghi_dinh_207_2026_nd_cp_toan_van.txt").write_text(
        "Raw text", encoding="utf-8"
    )

    auditor = DuplicationAuditor(tmp_path)
    issues = auditor.audit()

    assert len(issues) > 0
    assert any("nghi_dinh_207_2026_nd_cp_toan_van.txt" in issue.file_path for issue in issues)


def test_legitimate_hub_research_files_allowed(tmp_path: Path):
    """Ensure legitimate markdown and report files are never falsely flagged."""
    extracted_dir = tmp_path / ".md" / "extracted_docs"
    extracted_dir.mkdir(parents=True)
    (extracted_dir / "hows_to_write_your_first_research_paper_2011.md").write_text(
        "Guide", encoding="utf-8"
    )
    (extracted_dir / "new_dossier_comparison_report.md").write_text("Report", encoding="utf-8")

    auditor = DuplicationAuditor(tmp_path)
    issues = auditor.audit()
    assert len(issues) == 0


def test_constants_definitions():
    """Verify forbidden patterns include key rules."""
    assert ".md/legal_docs" in FORBIDDEN_DIRECTORIES
    assert ".md/governance_constitution" in FORBIDDEN_DIRECTORIES
    assert len(FORBIDDEN_RAW_SCRAPE_PATTERNS) > 0
