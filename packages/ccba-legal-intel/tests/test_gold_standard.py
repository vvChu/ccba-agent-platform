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


def test_dieu_pattern_amendment_articles() -> None:
    """Verify dieu_pattern supports alphanumeric article numbers and optional quotes."""
    profile = get_doc_profile("vbpl")
    samples = [
        ("Điều 1. Phạm vi", "1"),
        ("Điều 1a. Bổ sung quy định", "1a"),
        ("“Điều 1a. Trích dẫn sửa đổi", "1a"),
        ('"Điều 2b. Trích dẫn kép', "2b"),
        ("Điều 15đ. Quy định bổ sung", "15đ"),
    ]
    for text, expected_num in samples:
        m = profile.dieu_pattern.match(text)
        assert m is not None, f"Failed to match: {text}"
        assert m.group(2) == expected_num, f"Expected {expected_num}, got {m.group(2)}"


def test_generate_bundle_ast_multiline_spans_and_clean_markdown(tmp_path: Path) -> None:
    """Verify line_start and line_end span multiple lines and clean markdown bold syntax."""
    bundle_dir = tmp_path / "sample_bundle"
    bundle_dir.mkdir()

    md_content = """# __Chương I__

__QUY ĐỊNH CHUNG__

<a id="dieu-1"></a>
### Điều 1. Phạm vi điều chỉnh

<a id="dieu-1-khoan-1"></a>
**1.** **Nội dung** khoản một dòng một.
Dòng thứ hai của khoản một.

<a id="dieu-1-khoan-2"></a>
**2.** Nội dung khoản hai.

# __Chương II__
"""
    (bundle_dir / "sample_doc.md").write_text(md_content, encoding="utf-8")
    (bundle_dir / "metadata.yaml").write_text("title: **Nghị định 01/2026**\n", encoding="utf-8")

    res = GoldStandardProcessor.process_bundle(bundle_dir, doc_type="vbpl")
    assert res["status"] == "success"

    clauses_file = bundle_dir / "clauses.json"
    qa_file = bundle_dir / "qa_benchmark.json"
    clauses = json.loads(clauses_file.read_text(encoding="utf-8"))
    qa_list = json.loads(qa_file.read_text(encoding="utf-8"))

    # Check dieu-1
    c1 = next(c for c in clauses if c["clause_id"] == "dieu-1")
    assert c1["title"] == "Điều 1. Phạm vi điều chỉnh"
    assert c1["line_start"] == 5
    assert c1["line_end"] == 6

    # Check dieu-1-khoan-1 multi-line span
    c1_k1 = next(c for c in clauses if c["clause_id"] == "dieu-1-khoan-1")
    assert c1_k1["line_start"] == 8
    assert c1_k1["line_end"] == 10
    # Check title has no **
    assert "**" not in c1_k1["title"]
    assert c1_k1["title"].startswith("1. Nội dung khoản một")

    # Check dieu-1-khoan-2 bounded by next section
    c1_k2 = next(c for c in clauses if c["clause_id"] == "dieu-1-khoan-2")
    assert c1_k2["line_start"] == 12
    assert c1_k2["line_end"] == 13

    # Check QA benchmark questions have no ** or __
    for qa in qa_list:
        assert "**" not in qa["question"]
        assert "__" not in qa["question"]
        assert "**" not in qa["answer"]
        assert "__" not in qa["answer"]


def test_federated_rag_bare_html_safeguard(tmp_path: Path) -> None:
    """Verify FederatedLegalEngine does not index bare HTML tag as chunk text."""
    from ccba_legal.federated_rag import FederatedLegalEngine

    bundle_dir = tmp_path / "legal_docs" / "01_vbpl" / "bare_html_bundle"
    bundle_dir.mkdir(parents=True)

    md_content = """<a id="dieu-1"></a>
<a id="dieu-2"></a>
Nội dung điều hai.
"""
    (bundle_dir / "doc.md").write_text(md_content, encoding="utf-8")
    (bundle_dir / "metadata.yaml").write_text(
        "doc_id: test_bare\ntitle: Test Doc\n", encoding="utf-8"
    )
    clauses = [
        {
            "clause_id": "dieu-1",
            "title": "Điều 1. Tiêu đề điều một",
            "line_start": 1,
            "line_end": 1,  # Bare HTML line
        },
        {
            "clause_id": "dieu-2",
            "title": "Điều 2. Tiêu đề điều hai",
            "line_start": 2,
            "line_end": 3,
        },
    ]
    (bundle_dir / "clauses.json").write_text(json.dumps(clauses), encoding="utf-8")

    engine = FederatedLegalEngine(corpus_paths=[bundle_dir], embedding_enabled=False)
    chunks = {c["clause_id"]: c for c in engine._chunks}

    assert "dieu-1" in chunks
    # Must fallback to title instead of bare HTML tag
    assert chunks["dieu-1"]["text"] == "Điều 1. Tiêu đề điều một"
    assert not chunks["dieu-1"]["text"].startswith("<a id=")


def test_generate_clauses_ast_direct() -> None:
    """Verify generate_clauses_ast handles multi-line spans, markdown bold cleaning, and fallback."""
    from ccba_legal.gold_standard.ast_qa_generator import generate_clauses_ast

    md_text = """<a id="dieu-1"></a>
### **Điều 1.** **Phạm vi điều chỉnh**
Dòng thứ nhất nội dung điều một.
Dòng thứ hai nội dung điều một.

<a id="dieu-2"></a>

<a id="dieu-3"></a>
Nội dung điều 3 không tiêu đề.
"""
    clauses = generate_clauses_ast(md_text)
    assert len(clauses) == 3

    # dieu-1 spans lines 1 to 4
    c1 = clauses[0]
    assert c1["clause_id"] == "dieu-1"
    assert c1["title"] == "Điều 1. Phạm vi điều chỉnh"
    assert c1["line_start"] == 1
    assert c1["line_end"] == 4

    # dieu-2 has no content, title falls back to anc_id
    c2 = clauses[1]
    assert c2["clause_id"] == "dieu-2"
    assert c2["title"] == "dieu-2"
    assert c2["line_start"] == 6
    assert c2["line_end"] == 6

    # dieu-3 has body content
    c3 = clauses[2]
    assert c3["clause_id"] == "dieu-3"
    assert c3["title"] == "Nội dung điều 3 không tiêu đề."
    assert c3["line_start"] == 8
    assert c3["line_end"] == 9


def test_federated_rag_safeguard_extended(tmp_path: Path) -> None:
    """Verify FederatedLegalEngine handles <a name=>, tag with whitespace, and None line spans."""
    from ccba_legal.federated_rag import FederatedLegalEngine

    bundle_dir = tmp_path / "legal_docs" / "01_vbpl" / "extended_bundle"
    bundle_dir.mkdir(parents=True)

    md_content = """<a name="dieu-name"></a>
<a id="dieu-ws"> </a>
Nội dung điều ba.
"""
    (bundle_dir / "doc.md").write_text(md_content, encoding="utf-8")
    (bundle_dir / "metadata.yaml").write_text(
        "doc_id: test_ext\ntitle: Extended Doc\n", encoding="utf-8"
    )
    clauses = [
        {
            "clause_id": "dieu-name",
            "title": "Điều Name. Tiêu đề",
            "line_start": 1,
            "line_end": 1,
        },
        {
            "clause_id": "dieu-ws",
            "title": "Điều WS. Tiêu đề khoảng trắng",
            "line_start": 2,
            "line_end": 2,
        },
        {
            "clause_id": "dieu-corrupted-spans",
            "title": "Điều Lỗi Spans",
            "line_start": None,
            "line_end": None,
        },
    ]
    (bundle_dir / "clauses.json").write_text(json.dumps(clauses), encoding="utf-8")

    engine = FederatedLegalEngine(corpus_paths=[bundle_dir], embedding_enabled=False)
    chunks = {c["clause_id"]: c for c in engine._chunks}

    # <a name> should fall back to title
    assert chunks["dieu-name"]["text"] == "Điều Name. Tiêu đề"
    # <a id="dieu-ws"> </a> should fall back to title
    assert chunks["dieu-ws"]["text"] == "Điều WS. Tiêu đề khoảng trắng"
    # Corrupted None spans should not crash and should fall back safely
    assert chunks["dieu-corrupted-spans"]["text"] == "Điều Lỗi Spans"
