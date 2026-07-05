import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from bs4 import BeautifulSoup
from ccba_legal.packager import OKFBundlePackager
from ccba_legal.parser import LegalAnalysisEngine


def test_anchor_injection():
    packager = OKFBundlePackager(Path())
    sample_text = """Chương I
QUY ĐỊNH CHUNG
Điều 1. Phạm vi điều chỉnh
1. Luật này quy định về...
a) Hoạt động đầu tư xây dựng;
b) Phát triển đô thị.
2. Các hoạt động khác.
Điều 2. Đối tượng áp dụng
1. Cơ quan, tổ chức..."""

    processed = packager.inject_anchors(sample_text)
    assert '<a id="d1"></a>Điều 1. Phạm vi điều chỉnh' in processed
    assert '<a id="d1k1"></a>1. Luật này quy định về...' in processed
    assert '<a id="d1k1da"></a>a) Hoạt động đầu tư xây dựng;' in processed
    assert '<a id="d1k1db"></a>b) Phát triển đô thị.' in processed
    assert '<a id="d1k2"></a>2. Các hoạt động khác.' in processed
    assert '<a id="d2"></a>Điều 2. Đối tượng áp dụng' in processed
    assert '<a id="d2k1"></a>1. Cơ quan, tổ chức...' in processed


def test_table_flattening():
    packager = OKFBundlePackager(Path())
    html = """<table>
  <tr>
    <th colspan="2">Header 1-2</th>
    <th>Header 3</th>
  </tr>
  <tr>
    <td rowspan="2">Row 1-2 Col 1</td>
    <td>Row 1 Col 2</td>
    <td>Row 1 Col 3</td>
  </tr>
  <tr>
    <td>Row 2 Col 2</td>
    <td>Row 2 Col 3</td>
  </tr>
</table>"""
    soup = BeautifulSoup(html, "html.parser").find("table")
    grid, is_complex, num_rows = packager.flatten_html_table(soup)

    assert is_complex is True
    assert num_rows == 3
    assert grid[0] == ["Header 1-2", "Header 1-2", "Header 3"]
    assert grid[1] == ["Row 1-2 Col 1", "Row 1 Col 2", "Row 1 Col 3"]
    assert grid[2] == ["Row 1-2 Col 1", "Row 2 Col 2", "Row 2 Col 3"]


def test_process_tables_small():
    with tempfile.TemporaryDirectory() as temp_dir:
        bundle_dir = Path(temp_dir)
        packager = OKFBundlePackager(bundle_dir)

        sample_md = """Some text before.
<table>
  <tr>
    <th>Header 1</th>
    <th>Header 2</th>
  </tr>
  <tr>
    <td>Value 1</td>
    <td>Value 2</td>
  </tr>
</table>
Some text after."""

        processed = packager.process_tables(sample_md, bundle_dir)

        assert "| Header 1 | Header 2 |" in processed
        assert "| --- | --- |" in processed
        assert "| Value 1 | Value 2 |" in processed
        assert "<table>" not in processed


def test_process_tables_large():
    with tempfile.TemporaryDirectory() as temp_dir:
        bundle_dir = Path(temp_dir)
        packager = OKFBundlePackager(bundle_dir)

        # Construct a table with 52 rows (1 header + 51 data rows)
        table_rows = ["<tr><th>Header 1</th></tr>"]
        for i in range(51):
            table_rows.append(f"<tr><td>Row {i}</td></tr>")
        table_html = "<table>" + "".join(table_rows) + "</table>"

        sample_md = f"Before.\n{table_html}\nAfter."
        processed = packager.process_tables(sample_md, bundle_dir)

        assert "Before." in processed
        assert "After." in processed
        assert "tệp CSV" in processed
        assert "tệp JSON" in processed
        assert "<table>" not in processed

        # Verify files were saved
        csv_file = bundle_dir / "tables" / "table_01.csv"
        json_file = bundle_dir / "tables" / "table_01.json"

        assert csv_file.exists()
        assert json_file.exists()

        csv_content = csv_file.read_text(encoding="utf-8")
        assert "Row 0" in csv_content
        assert "Row 50" in csv_content


def test_split_by_chapters():
    with tempfile.TemporaryDirectory() as temp_dir:
        sections_dir = Path(temp_dir) / "sections"
        packager = OKFBundlePackager(Path())

        content = """Chương I
QUY ĐỊNH CHUNG
Điều 1. ...
Chương II
ĐIỀU KHOẢN THI HÀNH
Điều 2. ..."""

        packager.split_by_chapters(content, sections_dir)

        ch1 = sections_dir / "chuong_01.md"
        ch2 = sections_dir / "chuong_02.md"

        assert ch1.exists()
        assert ch2.exists()

        ch1_content = ch1.read_text(encoding="utf-8")
        assert 'parent_document: "../full_text.md"' in ch1_content
        assert "Chương I" in ch1_content
        assert "QUY ĐỊNH CHUNG" in ch1_content
        assert "Chương II" not in ch1_content


def test_generate_chunks():
    with tempfile.TemporaryDirectory() as temp_dir:
        bundle_dir = Path(temp_dir)
        packager = OKFBundlePackager(bundle_dir)

        # Construct content with enough words to trigger chunking
        content_parts = []
        for i in range(10):
            content_parts.append(f"Paragraph {i} " + "word " * 50)  # 50 words per paragraph
        content = "\n\n".join(content_parts)

        packager.generate_chunks(content, bundle_dir)

        chunks_file = bundle_dir / "chunks.json"
        assert chunks_file.exists()

        chunks = json.loads(chunks_file.read_text(encoding="utf-8"))
        assert len(chunks) > 1
        for chunk in chunks:
            assert "chunk_id" in chunk
            assert "content" in chunk
            assert "word_count" in chunk
            assert "token_count" in chunk
            assert 200 <= chunk["word_count"] <= 400


def test_standardize_formulas():
    mock_ai = MagicMock()
    mock_ai.chat.return_value = """
$$C_{XD} = V \\times G \\times (1 + G_{dp})$$

| Ký hiệu | Ý nghĩa |
| --- | --- |
| $C_{XD}$ | Chi phí xây dựng |

```python
def calculate_c_xd(V, G, G_dp):
    return V * G * (1 + G_dp)
```
"""
    engine = LegalAnalysisEngine(ai_client=mock_ai)

    text = "Chi phí xây dựng được tính theo công thức: C_XD = V * G * (1 + G_dp)."
    processed = engine.standardize_formulas(text)

    mock_ai.chat.assert_called_once()
    assert "$$C_{XD} = V \\times G \\times (1 + G_{dp})$$" in processed
    assert "calculate_c_xd" in processed


def test_frontmatter_inheritance_and_link_standardization():
    with tempfile.TemporaryDirectory() as temp_dir:
        root_dir = Path(temp_dir)
        packager = OKFBundlePackager(root_dir)

        # 1. Create a parent document content with full OKF frontmatter
        parent_content = """---
type: Law
resource: "http://moc.gov.vn/luat-xaydung"
status: "current"
document_number: "50/2014/QH13"
timestamp: "2026-07-05T12:00:00Z"
---

# Luật Xây dựng

Chương I
QUY ĐỊNH CHUNG
Điều 1. Phạm vi điều chỉnh
Đây là nội dung Điều 1.

Chương II
QUYỀN VÀ NGHĨA VỤ
Điều 2. Quyền của chủ đầu tư
Đây là nội dung Điều 2. Xem thêm chi tiết tại [Phụ lục I](appendices/test-phu_luc_01.md).

PHỤ LỤC I
BẢNG PHÂN CẤP CÔNG TRÌNH
Nội dung chi tiết phụ lục I.
"""
        # Save it as the primary file to split appendices from it
        primary_slug = "test_law"
        file_path = root_dir / f"{primary_slug}.md"
        file_path.write_text(parent_content, encoding="utf-8")

        # 2. Test split_by_chapters
        sections_dir = root_dir / "sections"
        packager.split_by_chapters(parent_content, sections_dir)

        ch1 = sections_dir / "chuong_01.md"
        ch2 = sections_dir / "chuong_02.md"
        assert ch1.exists()
        assert ch2.exists()

        ch1_content = ch1.read_text(encoding="utf-8")
        assert "type: Section" in ch1_content
        assert 'resource: "http://moc.gov.vn/luat-xaydung"' in ch1_content
        assert 'status: "current"' in ch1_content
        assert 'document_number: "50/2014/QH13"' in ch1_content
        assert 'timestamp: "2026-07-05T12:00:00Z"' in ch1_content

        # 3. Test split_concept_appendices
        apps = packager.split_concept_appendices(file_path)
        assert len(apps) > 0
        app_file = root_dir / apps[0]
        assert app_file.exists()

        app_content = app_file.read_text(encoding="utf-8")
        assert "type: Appendix" in app_content
        assert 'resource: "http://moc.gov.vn/luat-xaydung"' in app_content
        assert 'status: "current"' in app_content
        assert 'document_number: "50/2014/QH13"' in app_content
        assert 'timestamp: "2026-07-05T12:00:00Z"' in app_content

        # 4. Test link standardization
        # Create a sibling file in the bundle
        bundle_dir = root_dir / "legal_docs" / primary_slug
        bundle_dir.mkdir(parents=True, exist_ok=True)

        # Write some files with relative links inside the bundle_dir to test standardize_bundle_links
        doc_with_rel_links = bundle_dir / "doc.md"
        doc_with_rel_links.write_text(
            "Xem [Chương I](sections/chuong_01.md) và [Phụ lục I](appendices/test_law-phu_luc_01.md).",
            encoding="utf-8",
        )
        # Sibling link
        doc_in_sections = bundle_dir / "sections" / "chuong_01.md"
        doc_in_sections.parent.mkdir(parents=True, exist_ok=True)
        doc_in_sections.write_text(
            "Xem [Trang chủ](../index.md) hoặc [Full text](../full_text.md) và [Phụ lục](../appendices/test_law-phu_luc_01.md).",
            encoding="utf-8",
        )

        packager.standardize_bundle_links(bundle_dir)

        # Verify links were standardized to bundle-absolute paths
        doc_content_fixed = doc_with_rel_links.read_text(encoding="utf-8")
        assert "[Chương I](/sections/chuong_01.md)" in doc_content_fixed
        assert "[Phụ lục I](/appendices/test_law-phu_luc_01.md)" in doc_content_fixed

        sections_content_fixed = doc_in_sections.read_text(encoding="utf-8")
        assert "[Trang chủ](/index.md)" in sections_content_fixed
        assert "[Full text](/full_text.md)" in sections_content_fixed
        assert "[Phụ lục](/appendices/test_law-phu_luc_01.md)" in sections_content_fixed
