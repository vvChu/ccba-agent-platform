"""TDD Unit Tests for Constitution-Driven Cross-Reference Validator."""

from pathlib import Path

import yaml
from scripts.governance.cross_ref_validator import (
    CrossRefValidationReport,
    CrossRefValidator,
    extract_markdown_headings,
    find_closest_heading,
    validate_cross_references,
)


def create_mock_project(tmp_path: Path) -> tuple[Path, Path]:
    """Helper to create a mock project structure with specs, constitution, and cross_references.yaml."""
    # Create directories
    specs_dir = tmp_path / "specs" / "modules" / "cash_data" / "allocations"
    specs_dir.mkdir(parents=True)
    constitution_dir = tmp_path / ".md" / "governance_constitution"
    constitution_dir.mkdir(parents=True)
    blueprint_dir = tmp_path / ".md" / "system_blueprint"
    blueprint_dir.mkdir(parents=True)

    # Create spec file
    spec_content = """# Spec: Allocations
## 1.1 Mục tiêu & Phạm vi
Đặc tả phân bổ 3 tầng.
### 2.1 User Stories
- US-01: Phân bổ hợp đồng.
"""
    (specs_dir / "spec.md").write_text(spec_content, encoding="utf-8")

    # Create constitution doc
    const_content = """# QCTK 2815
## Điều 11 - Nghiệm thu và Quyết toán
Quy định quyết toán hợp đồng.
## Điều 12 - Phân bổ tài chính
Tỷ lệ phân bổ 3 tầng.
"""
    (constitution_dir / "01_qctk_2815.md").write_text(const_content, encoding="utf-8")

    # Create cross_references.yaml
    cross_refs_data = {
        "metadata": {
            "project": "MOCK-SPOKE",
            "milestone": "M1",
            "total_spec_modules": 1,
            "total_mapped_references": 2,
        },
        "modules": [
            {
                "module_id": "cash_data_allocations",
                "domain": "cash_data",
                "spec_file": "specs/modules/cash_data/allocations/spec.md",
                "spec_title": "Allocations Spec",
                "governance_constitution_references": [
                    {
                        "document": "01_qctk_2815.md",
                        "document_title": "QCTK 2815",
                        "article_clause": "Điều 11",
                        "section_context": "1.1 Mục tiêu & Phạm vi",
                        "topic": "Quyết toán",
                        "excerpt": "Quy định quyết toán hợp đồng.",
                    },
                    {
                        "document": "01_qctk_2815.md",
                        "document_title": "QCTK 2815",
                        "article_clause": "Điều 12",
                        "section_context": "1.1 Mục tiêu & Phạm vi",
                        "topic": "Phân bổ",
                        "excerpt": "Tỷ lệ phân bổ 3 tầng.",
                    },
                ],
            }
        ],
    }

    yaml_file = tmp_path / ".md" / "cross_references.yaml"
    yaml_file.write_text(yaml.safe_dump(cross_refs_data, allow_unicode=True), encoding="utf-8")
    return tmp_path, yaml_file


def test_extract_markdown_headings():
    content = """# Main Title
## Section 1: Intro
### 1.1 Detailed Goal & Scope
#### Sub-item A
"""
    headings = extract_markdown_headings(content)
    assert "Main Title" in headings
    assert "Section 1: Intro" in headings
    assert "1.1 Detailed Goal & Scope" in headings


def test_find_closest_heading():
    available = ["1.1 Mục tiêu & Phạm vi", "2.1 User Stories", "3.1 Quy trình"]
    closest = find_closest_heading("1.1 Mục tiêu", available)
    assert closest == "1.1 Mục tiêu & Phạm vi"


def test_validate_valid_cross_references(tmp_path: Path):
    project_root, yaml_path = create_mock_project(tmp_path)
    validator = CrossRefValidator(project_root)
    report: CrossRefValidationReport = validator.validate(yaml_path)

    assert report.is_valid is True
    assert report.total_modules == 1
    assert report.total_references == 2
    assert len(report.errors) == 0


def test_validate_missing_spec_file(tmp_path: Path):
    project_root, yaml_path = create_mock_project(tmp_path)
    # Delete spec.md
    (project_root / "specs" / "modules" / "cash_data" / "allocations" / "spec.md").unlink()

    validator = CrossRefValidator(project_root)
    report = validator.validate(yaml_path)

    assert report.is_valid is False
    assert any("Không tìm thấy tệp spec" in err.message for err in report.errors)


def test_validate_missing_constitution_doc(tmp_path: Path):
    project_root, yaml_path = create_mock_project(tmp_path)
    # Delete constitution doc
    (project_root / ".md" / "governance_constitution" / "01_qctk_2815.md").unlink()

    validator = CrossRefValidator(project_root)
    report = validator.validate(yaml_path)

    assert report.is_valid is False
    assert any("Không tìm thấy tệp quy chế" in err.message for err in report.errors)


def test_validate_broken_heading_suggestion_and_fix(tmp_path: Path):
    project_root, yaml_path = create_mock_project(tmp_path)

    # Edit yaml to use an obsolete heading
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    data["modules"][0]["governance_constitution_references"][0]["section_context"] = "1.1 Mục tiêu cũ"
    yaml_path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

    validator = CrossRefValidator(project_root)
    report = validator.validate(yaml_path)

    # Check that warning/suggestion is generated
    assert len(report.warnings) > 0
    assert report.warnings[0].suggestion == "1.1 Mục tiêu & Phạm vi"

    # Test auto-fix
    exit_code = validate_cross_references(yaml_path, project_root, auto_fix=True)
    assert exit_code == 0

    # Verify YAML content after fix
    reloaded_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    fixed_context = reloaded_data["modules"][0]["governance_constitution_references"][0]["section_context"]
    assert fixed_context == "1.1 Mục tiêu & Phạm vi"


def test_warn_only_returns_zero(tmp_path: Path):
    project_root, yaml_path = create_mock_project(tmp_path)
    # Delete spec file to cause an error
    (project_root / "specs" / "modules" / "cash_data" / "allocations" / "spec.md").unlink()

    # Without warn_only -> returns 1
    code_strict = validate_cross_references(yaml_path, project_root, warn_only=False)
    assert code_strict == 1

    # With warn_only -> returns 0
    code_warn = validate_cross_references(yaml_path, project_root, warn_only=True)
    assert code_warn == 0
