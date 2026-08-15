import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from ccba_legal.formatter import OKFStructureProcessor
from ccba_legal.packager import OKFBundlePackager
from ccba_legal.parser import LegalAnalysisEngine


def test_process_tables_large() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        bundle_dir = Path(temp_dir)
        processor = OKFStructureProcessor()

        # Construct a table with 52 rows (1 header + 51 data rows)
        table_rows = ["<tr><th>Header 1</th></tr>"]
        for i in range(51):
            table_rows.append(f"<tr><td>Row {i}</td></tr>")
        table_html = "<table>" + "".join(table_rows) + "</table>"

        sample_md = f"Before.\n{table_html}\nAfter."
        processed = processor.process_tables(sample_md, bundle_dir)

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


def test_standardize_formulas() -> None:
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


def test_frontmatter_inheritance_and_link_standardization() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root_dir = Path(temp_dir)
        processor = OKFStructureProcessor()
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
        processor.split_by_chapters(parent_content, sections_dir)

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
        apps = processor.split_concept_appendices(file_path)
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


def test_okf_v2_package_bundle_creates_metadata_yaml() -> None:
    """Test that OKFBundlePackager creates metadata.yaml according to OKF v2.0 (ADR 0038)."""
    import yaml

    with tempfile.TemporaryDirectory() as temp_dir:
        root_dir = Path(temp_dir)
        packager = OKFBundlePackager(root_dir)

        metadata = {
            "title": "Nghị định 217/2026/NĐ-CP",
            "type": "vbpl",
            "document_number": "217/2026/NĐ-CP",
            "issued_by": "Chính phủ",
            "issued_date": "2026-06-19",
            "effective_date": "2026-07-01",
            "source_url": "https://thuvienphapluat.vn/test",
            "sha256": "abc123sha",
        }

        bundle_dir = packager.package_bundle(
            doc_id="nghi_dinh_217_2026_nd_cp",
            content="Nội dung điều khoản nghị định 217...",
            metadata=metadata,
        )

        assert bundle_dir.exists()
        metadata_file = bundle_dir / "metadata.yaml"
        assert metadata_file.exists()

        meta = yaml.safe_load(metadata_file.read_text(encoding="utf-8"))
        assert meta["doc_id"] == "nghi_dinh_217_2026_nd_cp"
        assert meta["doc_number"] == "217/2026/NĐ-CP"
        assert meta["title"] == "Nghị định 217/2026/NĐ-CP"
        assert meta["issuer"] == "Chính phủ"
        assert meta["status"] == "effective"
        assert meta["sha256"] == "abc123sha"

