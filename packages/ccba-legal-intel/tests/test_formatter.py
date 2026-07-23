import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from ccba_legal.formatter import OKFStructureProcessor, inject_warning_block


def test_inject_anchors() -> None:
    processor = OKFStructureProcessor()
    raw_markdown = """
Chương I
QUY ĐỊNH CHUNG
Điều 1. Phạm vi điều chỉnh
1. Luật này quy định về hoạt động xây dựng.
a) Công trình dân dụng.
b) Công trình công nghiệp.
2. Quy định khác.
Điều 2. Đối tượng áp dụng
1. Cơ quan, tổ chức.
"""
    result = processor.inject_anchors(raw_markdown)
    assert '<a id="d1"></a>Điều 1. Phạm vi điều chỉnh' in result
    assert '<a id="d1k1"></a>1. Luật này quy định' in result
    assert '<a id="d1k1da"></a>a) Công trình dân dụng.' in result
    assert '<a id="d1k1db"></a>b) Công trình công nghiệp.' in result
    assert '<a id="d1k2"></a>2. Quy định khác.' in result
    assert '<a id="d2"></a>Điều 2. Đối tượng áp dụng' in result
    assert '<a id="d2k1"></a>1. Cơ quan, tổ chức.' in result


def test_format_content_with_formula_callback() -> None:
    mock_callback = MagicMock(return_value="Standardized equation content")
    processor = OKFStructureProcessor(formula_standardizer=mock_callback)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        content = "Some cost formula text here."
        result = processor.format_content(content, temp_path)

        mock_callback.assert_called_once_with(content)
        assert "Standardized equation content" in result


def test_split_by_chapters() -> None:
    processor = OKFStructureProcessor()
    content = """---
document_number: "123"
---
Chương I
Điều 1
Nội dung 1
Chương II
Điều 2
Nội dung 2
"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        sections_dir = temp_path / "sections"
        processor.split_by_chapters(content, sections_dir)

        assert (sections_dir / "chuong_01.md").exists()
        assert (sections_dir / "chuong_02.md").exists()

        c1 = (sections_dir / "chuong_01.md").read_text(encoding="utf-8")
        assert "Chương I" in c1
        assert "Điều 1" in c1
        assert 'document_number: "123"' in c1

        c2 = (sections_dir / "chuong_02.md").read_text(encoding="utf-8")
        assert "Chương II" in c2
        assert "Điều 2" in c2


def test_generate_chunks() -> None:
    processor = OKFStructureProcessor()
    content = "\n\n".join(
        [f"Paragraph number {i} contains some words that we can chunk." for i in range(20)]
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        processor.generate_chunks(content, temp_path)

        chunks_file = temp_path / "chunks.json"
        assert chunks_file.exists()

        chunks = json.loads(chunks_file.read_text(encoding="utf-8"))
        assert len(chunks) > 0
        assert chunks[0]["chunk_id"] == 1
        assert "Paragraph number" in chunks[0]["content"]


def test_process_tables_simple() -> None:
    processor = OKFStructureProcessor()
    html_table = """
    <table>
        <tr>
            <th>Header 1</th>
            <th>Header 2</th>
        </tr>
        <tr>
            <td>Val 1</td>
            <td>Val 2</td>
        </tr>
    </table>
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        result = processor.process_tables(html_table, temp_path)
        assert "| Header 1 | Header 2 |" in result
        assert "| Val 1 | Val 2 |" in result


def test_inject_warning_block() -> None:
    markdown = """
Some text here.
<a id="d15k2"></a>2. Điều khoản này quan trọng.
Some other text.
"""
    updated = inject_warning_block(
        markdown,
        target_anchor="d15k2",
        amendment_source="Điều 1 Thông tư B",
        source_doc_path="guiding_docs/tt_b.md",
    )

    assert "Khoản này đã bị sửa đổi/bổ sung bởi Điều 1 Thông tư B" in updated
    assert "[Thông tư B](guiding_docs/tt_b.md)" in updated

    # Test idempotent (no duplicate warning block injected)
    twice = inject_warning_block(
        updated,
        target_anchor="d15k2",
        amendment_source="Điều 1 Thông tư B",
        source_doc_path="guiding_docs/tt_b.md",
    )
    assert twice == updated
