import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.adversarial]


from bs4 import BeautifulSoup
from ccba_legal.formatter import OKFStructureProcessor
from ccba_legal.parser import LegalAnalysisEngine

from mdconverter.plugins.vn_legal.linter import VNLegalLinter  # type: ignore[import-untyped]


def test_anchor_injection_edge_cases() -> None:
    processor = OKFStructureProcessor()

    # Case 1: Hierarchy with no prior Điều (should not inject khoan/diem anchors)
    text_no_dieu = """Chương I
QUY ĐỊNH CHUNG
1. Phạm vi điều chỉnh
a) Hoạt động đầu tư xây dựng;
2. Đối tượng áp dụng"""
    processed = processor.inject_anchors(text_no_dieu)
    assert '<a id="' not in processed

    # Case 2: Hierarchy with Điều but Khoản is not yet parsed (should not inject diem anchors)
    text_no_khoan = """Điều 1. Phạm vi điều chỉnh
a) Hoạt động đầu tư xây dựng;"""
    processed = processor.inject_anchors(text_no_khoan)
    assert '<a id="d1"></a>Điều 1. Phạm vi điều chỉnh' in processed
    assert '<a id="d1k' not in processed

    # Case 3: Character cases in diem matching
    text_diem_casing = """Điều 1. Phạm vi điều chỉnh
1. Luật này quy định về:
đ) Các hoạt động khác."""
    processed = processor.inject_anchors(text_diem_casing)
    assert '<a id="d1k1dđ"></a>đ) Các hoạt động khác.' in processed


def test_table_flattening_edge_cases() -> None:
    processor = OKFStructureProcessor()

    # Case 1: Empty table
    html_empty = "<table></table>"
    soup = BeautifulSoup(html_empty, "html.parser").find("table")
    grid, is_complex, num_rows = processor.flatten_html_table(soup)
    assert grid == []
    assert is_complex is False
    assert num_rows == 0
    assert processor.grid_to_markdown(grid) == ""

    # Case 2: Table with no cells
    html_no_cells = "<table><tr></tr><tr></tr></table>"
    soup = BeautifulSoup(html_no_cells, "html.parser").find("table")
    grid, is_complex, num_rows = processor.flatten_html_table(soup)
    assert grid == [[], []]
    assert is_complex is False
    assert num_rows == 2
    assert processor.grid_to_markdown(grid) == ""
    assert processor.grid_to_markdown([[]]) == ""

    # Case 3: Table with no headers (only td)
    html_no_headers = """<table>
      <tr>
        <td>Val 1</td>
        <td>Val 2</td>
      </tr>
    </table>"""
    soup = BeautifulSoup(html_no_headers, "html.parser").find("table")
    grid, is_complex, num_rows = processor.flatten_html_table(soup)
    assert grid == [["Val 1", "Val 2"]]
    assert is_complex is False
    assert num_rows == 1
    assert processor.grid_to_markdown(grid) == "| Val 1 | Val 2 |\n| --- | --- |"

    # Case 4: Malformed rowspan / colspan values
    html_malformed_span = """<table>
      <tr>
        <td rowspan="abc">Val 1</td>
        <td colspan="">Val 2</td>
      </tr>
    </table>"""
    soup = BeautifulSoup(html_malformed_span, "html.parser").find("table")
    grid, is_complex, num_rows = processor.flatten_html_table(soup)
    assert grid == [["Val 1", "Val 2"]]
    assert is_complex is False
    assert num_rows == 1


def test_standardize_formulas_edge_cases() -> None:
    # Setup mock LLM client
    mock_ai = MagicMock()
    engine = LegalAnalysisEngine(ai_client=mock_ai)

    # Case 1: Text without formula keywords should bypass LLM call entirely
    text_no_formula = "Đây là văn bản quy phạm pháp luật bình thường."
    processed = engine.standardize_formulas(text_no_formula)
    assert processed == text_no_formula
    mock_ai.chat.assert_not_called()

    # Case 2: Text with keywords but no matching formula patterns (no LLM call)
    text_keyword_only = "Chi phí xây dựng được quy định rất cụ thể trong văn bản."
    processed = engine.standardize_formulas(text_keyword_only)
    assert processed == text_keyword_only
    mock_ai.chat.assert_not_called()

    # Case 3: Text that triggers formula LLM call but receives malformed response
    # We want to ensure it completes and returns whatever the LLM returned or original.
    mock_ai.chat.return_value = "Malformed LLM response with no markdown fences."
    text_trigger = "Phương pháp tính chi phí: C_XD = V * G."
    processed = engine.standardize_formulas(text_trigger)
    assert "Malformed LLM response" in processed
    mock_ai.chat.assert_called_once()


def test_linter_vn_legal_rules() -> None:
    linter = VNLegalLinter()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Case 1: VN001 - Merged list items
        # We need to make sure the content satisfies is_legal_document detector (e.g. contains 'Điều 1', 'Nghị định')
        content_vn001 = """Nghị định 06/2021
Điều 1. Phạm vi
a) Hoạt động đầu tư xây dựng; b) Phát triển đô thị."""
        file_vn001 = temp_path / "vn001.md"
        file_vn001.write_text(content_vn001, encoding="utf-8")
        issues = linter.lint_file(file_vn001)
        vn001_issues = [iss for iss in issues if iss.rule_id == "VN001"]
        assert len(vn001_issues) == 1
        assert "Merged list items detected" in vn001_issues[0].message

        # Case 2: VN002 - Suspicious numbering reset
        # Having more than five "1." but no "2." at start of lines.
        content_vn002 = """Nghị định 06/2021
Điều 1. Danh sách
1. Thứ nhất
1. Thứ hai
1. Thứ ba
1. Thứ tư
1. Thứ năm
1. Thứ sáu"""
        file_vn002 = temp_path / "vn002.md"
        file_vn002.write_text(content_vn002, encoding="utf-8")
        issues = linter.lint_file(file_vn002)
        vn002_issues = [iss for iss in issues if iss.rule_id == "VN002"]
        assert len(vn002_issues) == 1
        assert "Suspicious numbering" in vn002_issues[0].message

        # Case 3: VN003 - Missing blank line before 'Điều' headers
        content_vn003 = """Nghị định 06/2021

### Điều 1. Phạm vi
Nội dung Điều 1.
### Điều 2. Đối tượng"""  # Missing blank line before '### Điều 2'
        file_vn003 = temp_path / "vn003.md"
        file_vn003.write_text(content_vn003, encoding="utf-8")
        issues = linter.lint_file(file_vn003)
        vn003_issues = [iss for iss in issues if iss.rule_id == "VN003"]
        assert len(vn003_issues) == 1
        assert vn003_issues[0].line == 5
        assert "Missing blank line" in vn003_issues[0].message

        # Case 4: VN004 - Incorrect 'Điểm' format
        content_vn004 = """Nghị định 06/2021
Điều 1. Phạm vi
- a) Sai định dạng điểm.
- b) Cũng sai.
- đ) Định dạng điểm với đ.
- e) Định dạng điểm với e.
- Đ) Định dạng điểm với Đ hoa."""
        file_vn004 = temp_path / "vn004.md"
        file_vn004.write_text(content_vn004, encoding="utf-8")
        issues = linter.lint_file(file_vn004)
        vn004_issues = [iss for iss in issues if iss.rule_id == "VN004"]
        assert len(vn004_issues) == 5
        assert "Incorrect 'Điểm' format" in vn004_issues[0].message


def test_validate_docs_linter_logic(tmp_path: Path) -> None:
    # Import validation functions from scripts/validate_docs.py
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
    import validate_docs  # type: ignore[import-not-found]

    # Case 1: Malformed frontmatter
    # Must place it under a "legal_docs" folder structure to make is_okf True
    legal_docs_dir = tmp_path / "legal_docs" / "test_bundle"
    legal_docs_dir.mkdir(parents=True, exist_ok=True)

    malformed_fm = """---
type: InvalidType
resource: ""
timestamp: "2026-07-05T14:00:00Z"
---
Nghị định 06/2021
Điều 1. Nội dung
"""
    file_fm = legal_docs_dir / "malformed_fm.md"
    file_fm.write_text(malformed_fm, encoding="utf-8")
    issues = validate_docs.validate_markdown_file(
        file_fm, search_dirs=[], env_example_vars=set(), project_root=tmp_path
    )
    assert len(issues["okf_frontmatter"]) > 0
    assert "Invalid type" in issues["okf_frontmatter"][0][2]

    # Case 2: Absolute file links and resolution
    # Create target file
    target_file = tmp_path / "target.md"
    target_file.touch()

    # Link referencing target file using an absolute file:// path
    abs_link_content = f"""---
type: Law
resource: "http://example.com"
status: "current"
timestamp: "2026-07-05T14:00:00Z"
---
[Link to target]({target_file.as_uri()})
"""
    file_link = legal_docs_dir / "link.md"
    file_link.write_text(abs_link_content, encoding="utf-8")

    issues_link = validate_docs.validate_markdown_file(
        file_link, search_dirs=[], env_example_vars=set(), project_root=tmp_path, fix=False
    )
    # It should detect absolute link warning
    assert len(issues_link["links"]) > 0
    assert "Absolute file link inside workspace" in issues_link["links"][0][2]

    # Run again with fix=True to verify relative path resolution
    issues_link_fixed = validate_docs.validate_markdown_file(
        file_link, search_dirs=[], env_example_vars=set(), project_root=tmp_path, fix=True
    )
    assert "AUTO-FIXED" in issues_link_fixed["links"][0][2]

    # Verify that file has been rewritten with a relative path
    fixed_content = file_link.read_text(encoding="utf-8")
    assert "target.md" in fixed_content
    assert "file://" not in fixed_content

    # Case 3: Frontmatter validation outside legal_docs directory
    outside_dir = tmp_path / "outside_docs"
    outside_dir.mkdir(parents=True, exist_ok=True)
    malformed_fm_outside = """---
type: InvalidType
resource: "http://example.com"
status: "current"
timestamp: "2026-07-05T14:00:00Z"
---
Nghị định 06/2021
Điều 1. Nội dung
"""
    file_fm_outside = outside_dir / "malformed_fm_outside.md"
    file_fm_outside.write_text(malformed_fm_outside, encoding="utf-8")
    issues_outside = validate_docs.validate_markdown_file(
        file_fm_outside, search_dirs=[], env_example_vars=set(), project_root=tmp_path
    )
    assert len(issues_outside["okf_frontmatter"]) > 0
    assert "Invalid type" in issues_outside["okf_frontmatter"][0][2]
