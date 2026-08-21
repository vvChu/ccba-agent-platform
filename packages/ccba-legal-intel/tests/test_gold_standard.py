"""Unit tests for Gold Standard Processor in ccba-legal-intel."""

import json
from pathlib import Path

from ccba_legal.gold_standard import (
    GoldStandardProcessor,
    clean_html_tables,
    clean_table_footnotes_and_superscripts,
    get_doc_profile,
    inject_semantic_anchors,
    normalize_notes_and_lists,
)


def test_clean_html_tables() -> None:
    html = "<table><tr><th>Header 1</th><th>Header 2</th></tr><tr><td>Row 1</td><td>Data 1</td></tr></table>"
    md = clean_html_tables(html)
    assert "| Header 1 | Header 2 |" in md
    assert "| --- | --- |" in md
    assert "| Row 1 | Data 1 |" in md


def test_clean_table_footnotes_and_superscripts() -> None:
    table_text = (
        "| Loại nhà | Giới hạn chịu lửa |\n"
        "| --- | --- |\n"
        "| Nhà công nghiệp | REI 60 1) |\n"
        "| _1) Áp dụng cho cột chịu lực chính |"
    )
    cleaned = clean_table_footnotes_and_superscripts(table_text)
    assert "REI 60<sup>1)</sup>" in cleaned
    assert "_GHI CHÚ CHỈ SỐ PHỤ:_" in cleaned
    assert "- **1)** Áp dụng cho cột chịu lực chính" in cleaned


def test_normalize_notes_and_lists() -> None:
    raw_notes = (
        "_CHÚ THÍCH:_\n"
        "- **CHÚ THÍCH 1:**\n"
        "  a) Điều kiện A\n"
        "  b) Điều kiện B\n"
        "\n"
        "_CHÚ THÍCH:_\n"
        "- **CHÚ THÍCH 2:** Nội dung chú thích 2\n"
    )
    normalized = normalize_notes_and_lists(raw_notes)
    # Consecutive _CHÚ THÍCH:_ should be deduplicated
    assert normalized.count("_CHÚ THÍCH:_") == 1
    assert "  a) Điều kiện A" in normalized


def test_inject_semantic_anchors() -> None:
    raw_law = "Điều 12. Trách nhiệm của chủ đầu tư\n1. Lập hồ sơ thiết kế."
    anchored = inject_semantic_anchors(raw_law, profile=get_doc_profile("vbpl"))
    assert '<a id="dieu-12"></a>' in anchored
    assert '<a id="dieu-12-khoan-1"></a>' in anchored
    assert "**1.** Lập hồ sơ thiết kế." in anchored


def test_gold_standard_processor_bundle(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "test_bundle"
    bundle_dir.mkdir()

    # Create dummy core markdown
    core_md = bundle_dir / "test_doc.md"
    core_md.write_text(
        '<a id="muc-1-1"></a>\n### 1.1 Phạm vi áp dụng\nNội dung quy định.\n',
        encoding="utf-8",
    )

    # Create dummy metadata
    meta_yaml = bundle_dir / "metadata.yaml"
    meta_yaml.write_text("title: QCVN 99:2026/BXD — Thử nghiệm\n", encoding="utf-8")

    res = GoldStandardProcessor.process_bundle(bundle_dir, doc_type="qcvn")
    assert res["status"] == "success"
    assert res["clauses_count"] == 1
    assert res["qa_count"] == 1

    # Verify generated files
    clauses_file = bundle_dir / "clauses.json"
    qa_file = bundle_dir / "qa_benchmark.json"
    assert clauses_file.exists()
    assert qa_file.exists()

    clauses_data = json.loads(clauses_file.read_text(encoding="utf-8"))
    assert clauses_data[0]["clause_id"] == "muc-1-1"
