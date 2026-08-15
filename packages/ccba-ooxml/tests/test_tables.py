"""Unit tests for TableReconstructor & StructuredTable in ccba_ooxml."""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import pytest
from docx import Document

from ccba_ooxml.tables import StructuredTable, TableReconstructor


@pytest.fixture
def sample_table_dto() -> StructuredTable:
    """Fixture providing a standard StructuredTable instance."""
    return StructuredTable(
        table_id="bang_01_gioi_han_chiu_lua",
        num="1",
        title="Bảng 1 - Giới hạn chịu lửa của bộ phận ngăn cháy",
        headers=["Bộ phận ngăn cháy", "Loại", "Giới hạn chịu lửa"],
        rows=[
            ["Tường ngăn cháy", "Loại 1", "REI 150"],
            ["Tường ngăn cháy", "Loại 2", "REI 45"],
            ["Vách ngăn cháy", "Loại 1", "EI 45"],
        ],
        footnotes=["CHÚ THÍCH 1: Đối với nhà nhóm F1.1 áp dụng loại 1."],
    )


def test_structured_table_to_markdown(sample_table_dto: StructuredTable) -> None:
    """Test converting StructuredTable to GFM Markdown Pipe Table."""
    md = sample_table_dto.to_markdown(anchor=True)
    assert '<a id="bang-1"></a>' in md
    assert "### Bảng 1 - Giới hạn chịu lửa của bộ phận ngăn cháy" in md
    assert "| Bộ phận ngăn cháy | Loại | Giới hạn chịu lửa |" in md
    assert "| --- | --- | --- |" in md
    assert "| Tường ngăn cháy | Loại 1 | REI 150 |" in md
    assert "_CHÚ THÍCH 1: Đối với nhà nhóm F1.1 áp dụng loại 1._" in md


def test_structured_table_to_json_and_csv(sample_table_dto: StructuredTable) -> None:
    """Test JSON and CSV serialization of StructuredTable."""
    data = sample_table_dto.to_json()
    assert data["table_id"] == "bang_01_gioi_han_chiu_lua"
    assert data["num"] == "1"
    assert len(data["rows"]) == 3
    assert data["footnotes"] == ["CHÚ THÍCH 1: Đối với nhà nhóm F1.1 áp dụng loại 1."]

    csv_text = sample_table_dto.to_csv()
    reader = list(csv.reader(csv_text.strip().splitlines()))
    assert reader[0] == ["Bộ phận ngăn cháy", "Loại", "Giới hạn chịu lửa"]
    assert reader[1] == ["Tường ngăn cháy", "Loại 1", "REI 150"]


def test_save_table_exports(sample_table_dto: StructuredTable) -> None:
    """Test saving table exports to json and csv directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tables_dir = Path(tmpdir) / "tables"
        jpath, cpath = TableReconstructor.save_table_exports(sample_table_dto, tables_dir)

        assert jpath.exists()
        assert cpath.exists()
        assert jpath.name == "bang_01_gioi_han_chiu_lua.json"
        assert cpath.name == "bang_01_gioi_han_chiu_lua.csv"

        loaded_json = json.loads(jpath.read_text(encoding="utf-8"))
        assert loaded_json["num"] == "1"


def test_extract_docx_tables_with_merged_cells_and_footnotes() -> None:
    """Test extracting tables from an actual .docx file with unmerged cells."""
    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = Path(tmpdir) / "test_table_doc.docx"
        doc = Document()
        doc.add_paragraph("Bảng 2 - Phân loại bậc chịu lửa của nhà")

        table = doc.add_table(rows=4, cols=3)
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Bậc chịu lửa"
        hdr_cells[1].text = "Cột chịu lực"
        hdr_cells[2].text = "Sàn giữa các tầng"

        row1 = table.rows[1].cells
        row1[0].text = "Bậc I"
        row1[1].text = "R 120"
        row1[2].text = "REI 60"

        row2 = table.rows[2].cells
        row2[0].text = "Bậc II"
        row2[1].text = "R 90"
        row2[2].text = "REI 45"

        # Footnote row (spanning all cells)
        row3 = table.rows[3].cells
        for c in row3:
            c.text = "CHÚ THÍCH: Xem thêm Phụ lục E cho chi tiết."

        doc.save(str(docx_path))

        tables = TableReconstructor.extract_docx_tables(docx_path)
        assert len(tables) == 1
        t = tables[0]
        assert t.num == "2"
        assert "Bảng 2 - Phân loại bậc chịu lửa" in t.title
        assert t.headers == ["Bậc chịu lửa", "Cột chịu lực", "Sàn giữa các tầng"]
        assert len(t.rows) == 2
        assert t.rows[0] == ["Bậc I", "R 120", "REI 60"]
        assert t.footnotes == ["CHÚ THÍCH: Xem thêm Phụ lục E cho chi tiết."]


def test_replace_markdown_tables(sample_table_dto: StructuredTable) -> None:
    """Test replacing unformatted markdown table blocks with GFM pipe tables."""
    raw_md = """# Quy chuẩn kỹ thuật

### Bảng 1 - Giới hạn chịu lửa của bộ phận ngăn cháy
Tường ngăn cháy Loại 1 REI 150
Tường ngăn cháy Loại 2 REI 45
Vách ngăn cháy Loại 1 EI 45

### 1.2 Điều khoản tiếp theo
Nội dung điều khoản...
"""
    updated_md = TableReconstructor.replace_markdown_tables(raw_md, [sample_table_dto])
    assert '<a id="bang-1"></a>' in updated_md
    assert "| Bộ phận ngăn cháy | Loại | Giới hạn chịu lửa |" in updated_md
    assert "### 1.2 Điều khoản tiếp theo" in updated_md
