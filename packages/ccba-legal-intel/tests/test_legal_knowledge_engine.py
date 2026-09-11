"""test_legal_knowledge_engine.py - Unit and contract tests for LegalKnowledgeEngine."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from ccba_legal.engine import (
    LegalKnowledgeEngine,
    canonicalize_clause_id,
    csv_to_markdown,
)


@pytest.fixture
def temp_knowledge_setup():
    """Create a temporary mock knowledge corpus and registry for isolated testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        corpus_dir = root / "legal_docs"
        corpus_dir.mkdir(parents=True)
        data_dir = root / ".md" / "data"
        data_dir.mkdir(parents=True)
        registry_path = data_dir / "legal_registry.yaml"

        # Mock registry with active and superseded docs
        registry_data = {
            "metadata": {"version": "2.4"},
            "laws": [
                {
                    "id": "Luat-Xay-dung-2025",
                    "document_number": "135/2025/QH15",
                    "title": "Luật Xây dựng 2025",
                    "short_name": "Luật XD 2025",
                    "status": "active",
                    "effective_date": "2026-07-01",
                    "replaces": ["50/2014/QH13"],
                    "topics": ["xây dựng", "quy hoạch"],
                    "notes": "Văn bản chủ đạo quản lý xây dựng",
                },
                {
                    "id": "Luat-Xay-dung-2014",
                    "document_number": "50/2014/QH13",
                    "title": "Luật Xây dựng 2014",
                    "short_name": "Luật XD 2014",
                    "status": "superseded",
                    "superseded_date": "2026-07-01",
                    "superseded_by": "Luat-Xay-dung-2025",
                    "topics": ["xây dựng"],
                },
            ],
            "decrees": [],
            "circulars": [],
            "standards": [],
            "seminars": [],
        }
        with open(registry_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(registry_data, f, allow_unicode=True)

        # Mock OKF bundle: 01_vbpl/luat_xay_dung_2025
        bundle_dir = corpus_dir / "01_vbpl" / "luat_xay_dung_2025"
        bundle_dir.mkdir(parents=True)
        tables_csv_dir = bundle_dir / "tables" / "csv"
        tables_csv_dir.mkdir(parents=True)

        # metadata.yaml
        bundle_meta = {
            "id": "Luat-Xay-dung-2025",
            "doc_id": "Luat-Xay-dung-2025",
            "document_number": "135/2025/QH15",
            "status": "active",
        }
        with open(bundle_dir / "metadata.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(bundle_meta, f, allow_unicode=True)

        # Main markdown text with tier-aware anchors
        md_content = """---
okf_version: '2.4'
id: Luat-Xay-dung-2025
---

# Chương I - QUY ĐỊNH CHUNG

<a id="dieu-1"></a>
### Điều 1. Phạm vi điều chỉnh
Luật này quy định về hoạt động đầu tư xây dựng.

<a id="dieu-2"></a>
### Điều 2. Giải thích từ ngữ
Trong Luật này, các từ ngữ dưới đây được hiểu như sau:
<a id="dieu-2-khoan-1"></a>
1. Hoạt động đầu tư xây dựng là quá trình tiến hành xây dựng.
<a id="dieu-2-khoan-2"></a>
2. Công trình xây dựng là sản phẩm được tạo thành bởi sức lao động.
<a id="dieu-2-khoan-3"></a>
3. Giới hạn chịu lửa được quy định chi tiết tại:
<a id="bang-inline"></a>
| Bảng | Giá trị |
| --- | --- |
| 1 | 120 min |
<a id="footnote-1"></a>
Ghi chú footnote điều khoản.

<a id="dieu-3"></a>
### Điều 3. Nguyên tắc cơ bản
Bảo đảm tuân thủ quy chuẩn kỹ thuật quốc gia.

<a id="dieu-6"></a>
### Điều 6. Loại và cấp công trình
<a id="dieu-6-khoan-1"></a>
1. Phân loại theo công năng.
<a id="dieu-6-khoan-2"></a>
2. Cấp công trình được xác định:
<a id="dieu-6-khoan-2-diem-a"></a>
a) Cấp công trình phục vụ quản lý xây dựng.
<a id="dieu-6-khoan-2-diem-b"></a>
b) Cấp công trình phục vụ thiết kế xây dựng.

<a id="dieu-65a"></a>
### Điều 65a. Quy định chuyển tiếp đặc thù
Nội dung quy định bổ sung của luật sửa đổi.
"""
        (bundle_dir / "luat_xay_dung_2025.md").write_text(md_content, encoding="utf-8")

        # Table: bang_01.csv
        csv_content = "Vật liệu,Giới hạn chịu lửa,Ghi chú\nBê tông,REI 120,Chống cháy cao\nThép,REI 30,Cần bọc bảo vệ\n"
        (tables_csv_dir / "bang_01.csv").write_text(csv_content, encoding="utf-8")

        # Table with pipes: bang_pipes.csv
        csv_pipes = "Vật liệu,Tiêu chuẩn | Ghi chú\nBê tông cốt thép,TCVN 5574:2018 | Mác 300\n"
        (tables_csv_dir / "bang_pipes.csv").write_text(csv_pipes, encoding="utf-8")

        # Mock QCVN bundle: 02_qcvn/qcvn_06_2022_bxd
        qcvn_bundle = corpus_dir / "02_qcvn" / "qcvn_06_2022_bxd"
        qcvn_bundle.mkdir(parents=True)
        (qcvn_bundle / "metadata.yaml").write_text(
            "id: qcvn_06_2022_bxd\ndoc_id: qcvn_06_2022_bxd\nstatus: active\n", encoding="utf-8"
        )
        qcvn_md = """---
okf_version: '2.4'
id: qcvn_06_2022_bxd
---

# 1. QUY ĐỊNH CHUNG

<a id="muc-1-1"></a>
### 1.1 Phạm vi điều chỉnh
<a id="muc-1-1-1"></a>
### 1.1.1 Quy chuẩn này quy định về an toàn cháy.
Nội dung chi tiết của tiểu mục 1.1.1.
<a id="muc-1-1-2"></a>
### 1.1.2 Đối tượng áp dụng.
Nội dung chi tiết của tiểu mục 1.1.2.

<a id="muc-1-2"></a>
### 1.2 Tài liệu viện dẫn
Nội dung tài liệu viện dẫn.
"""
        (qcvn_bundle / "qcvn_06_2022_bxd.md").write_text(qcvn_md, encoding="utf-8")

        # Mock QCVN Amendment bundle: 02_qcvn/qcvn_06_2022_bxd_sd1_2023
        qcvn_amend = corpus_dir / "02_qcvn" / "qcvn_06_2022_bxd_sd1_2023"
        qcvn_amend.mkdir(parents=True)
        (qcvn_amend / "metadata.yaml").write_text(
            "id: qcvn_06_2022_bxd_sd1_2023\ndoc_id: qcvn_06_2022_bxd_sd1_2023\nstatus: active\n",
            encoding="utf-8",
        )

        yield {
            "root": root,
            "registry_path": registry_path,
            "corpus_dir": corpus_dir,
            "bundle_dir": bundle_dir,
            "qcvn_bundle": qcvn_bundle,
            "qcvn_amend": qcvn_amend,
        }


def test_canonicalize_clause_id():
    """Verify alias parsing maps shorthand to gold standard anchor IDs."""
    assert canonicalize_clause_id("d1") == "dieu-1"
    assert canonicalize_clause_id("d01") == "dieu-1"
    assert canonicalize_clause_id("d15") == "dieu-15"
    assert canonicalize_clause_id("d15k2") == "dieu-15-khoan-2"
    assert canonicalize_clause_id("d15-k2") == "dieu-15-khoan-2"
    assert canonicalize_clause_id("d15_k2") == "dieu-15-khoan-2"
    assert canonicalize_clause_id("d6k2a") == "dieu-6-khoan-2-diem-a"
    assert canonicalize_clause_id("d6k2da") == "dieu-6-khoan-2-diem-a"
    assert canonicalize_clause_id("d6k2-a") == "dieu-6-khoan-2-diem-a"
    assert canonicalize_clause_id("dieu-15-khoan-2") == "dieu-15-khoan-2"
    assert canonicalize_clause_id("dieu_15_khoan_2") == "dieu-15-khoan-2"
    assert canonicalize_clause_id("dieu-6-khoan-2-diem-a") == "dieu-6-khoan-2-diem-a"
    assert canonicalize_clause_id("dieu_6_khoan_2_diem_a") == "dieu-6-khoan-2-diem-a"
    assert canonicalize_clause_id("d65a") == "dieu-65a"
    assert canonicalize_clause_id("dieu-65a") == "dieu-65a"
    assert canonicalize_clause_id("dieu-1") == "dieu-1"
    assert canonicalize_clause_id("dieu_1") == "dieu-1"
    assert canonicalize_clause_id("k3") == "khoan-3"
    assert canonicalize_clause_id("1.1") == "muc-1-1"
    assert canonicalize_clause_id("1.1.1") == "muc-1-1-1"
    assert canonicalize_clause_id("m1.1") == "muc-1-1"
    assert canonicalize_clause_id("muc-1-1") == "muc-1-1"


def test_csv_to_markdown():
    """Verify CSV string conversion to valid markdown table with pipe escaping."""
    csv_text = "Cột A,Cột B\nGiá trị 1,Giá trị 2"
    md = csv_to_markdown(csv_text)
    assert "| Cột A | Cột B |" in md
    assert "| --- | --- |" in md
    assert "| Giá trị 1 | Giá trị 2 |" in md

    # Pipe in cell content must be escaped
    csv_pipe = "Tên,Mô tả\nBê tông,TCVN 5574 | Cốt thép"
    md_pipe = csv_to_markdown(csv_pipe)
    assert r"TCVN 5574 \| Cốt thép" in md_pipe


def test_engine_search_and_metadata(temp_knowledge_setup):
    """Verify search enriches documents with lifecycle status, warnings, and replacements."""
    engine = LegalKnowledgeEngine(
        registry_path=temp_knowledge_setup["registry_path"],
        corpus_dir=temp_knowledge_setup["corpus_dir"],
    )

    # Search for active law
    results = engine.search("xây dựng", top_k=5)
    assert len(results) >= 1
    top_doc = results[0]
    assert "Luật XD" in top_doc.get("short_name", "")

    # Search superseded law directly
    doc_old = engine.get_document("50/2014/QH13")
    assert doc_old is not None
    assert doc_old["status"] == "SUPERSEDED"
    assert doc_old["is_superseded"] is True
    assert doc_old.get("lifecycle_warning") is not None
    assert "HẾT HIỆU LỰC" in doc_old["lifecycle_warning"]
    assert doc_old.get("suggested_replacement") is not None
    assert doc_old["suggested_replacement"]["document_number"] == "135/2025/QH15"


def test_engine_get_clause_tier_aware_slicing(temp_knowledge_setup):
    """Verify Tier-Aware Slicing captures all sub-clauses of an Article without premature truncation."""
    engine = LegalKnowledgeEngine(
        registry_path=temp_knowledge_setup["registry_path"],
        corpus_dir=temp_knowledge_setup["corpus_dir"],
    )

    # 1. Query Article (Điều 2) using alias 'd2'
    clause_d2 = engine.get_clause("Luat-Xay-dung-2025", "d2")
    assert clause_d2 is not None
    assert clause_d2["clause_id"] == "dieu-2"
    content = clause_d2["content"]

    # CRITICAL: Slicing Article 2 must NOT cut off at Khoản 1 or Khoản 2!
    assert "Điều 2. Giải thích từ ngữ" in content
    assert '<a id="dieu-2-khoan-1"></a>' in content
    assert "1. Hoạt động đầu tư xây dựng là quá trình" in content
    assert '<a id="dieu-2-khoan-2"></a>' in content
    assert "2. Công trình xây dựng là sản phẩm" in content

    # Slicing Article 2 MUST stop before Article 3
    assert "Điều 3" not in content
    assert "Nguyên tắc cơ bản" not in content

    # 2. Query Clause (Khoản 1 of Điều 2) using alias 'd2k1'
    clause_k1 = engine.get_clause("Luat-Xay-dung-2025", "d2k1")
    assert clause_k1 is not None
    assert clause_k1["clause_id"] == "dieu-2-khoan-1"
    k1_content = clause_k1["content"]

    assert "1. Hoạt động đầu tư xây dựng là quá trình" in k1_content
    # MUST NOT include Khoản 2 or Điều 3
    assert "2. Công trình xây dựng là sản phẩm" not in k1_content
    assert "Điều 3" not in k1_content


def test_engine_alias_and_canonical_slug(temp_knowledge_setup):
    """Verify engine handles canonical slugs (hyphen vs underscore) and clause aliases."""
    engine = LegalKnowledgeEngine(
        registry_path=temp_knowledge_setup["registry_path"],
        corpus_dir=temp_knowledge_setup["corpus_dir"],
    )

    # Query with hyphenated doc ID and alias 'd1'
    c1 = engine.get_clause("Luat-Xay-dung-2025", "d1")
    assert c1 is not None
    assert "Điều 1. Phạm vi điều chỉnh" in c1["content"]

    # Query with underscored doc ID and full clause ID
    c2 = engine.get_clause("luat_xay_dung_2025", "dieu-1")
    assert c2 is not None
    assert "Điều 1. Phạm vi điều chỉnh" in c2["content"]


def test_engine_get_table_csv_and_markdown(temp_knowledge_setup):
    """Verify table extraction returns both raw CSV and formatted Markdown."""
    engine = LegalKnowledgeEngine(
        registry_path=temp_knowledge_setup["registry_path"],
        corpus_dir=temp_knowledge_setup["corpus_dir"],
    )

    # 1. Markdown format (default)
    md_table = engine.get_table("Luat-Xay-dung-2025", "bang_01", format="markdown")
    assert md_table is not None
    assert "| Vật liệu | Giới hạn chịu lửa | Ghi chú |" in md_table
    assert "| Bê tông | REI 120 | Chống cháy cao |" in md_table

    # 2. CSV format
    csv_table = engine.get_table("Luat-Xay-dung-2025", "bang_01", format="csv")
    assert csv_table is not None
    assert "Bê tông,REI 120,Chống cháy cao" in csv_table

    # 3. Non-existent table returns None
    assert engine.get_table("Luat-Xay-dung-2025", "bang_99") is None


def test_engine_path_traversal_sanitization(temp_knowledge_setup):
    """Verify Two-Tier CWE-22 protection blocks path traversal in doc, clause, and table arguments."""
    engine = LegalKnowledgeEngine(
        registry_path=temp_knowledge_setup["registry_path"],
        corpus_dir=temp_knowledge_setup["corpus_dir"],
    )

    # 1. Unsafe doc_id with path traversal
    with pytest.raises(ValueError, match="[Pp]ath traversal"):
        engine.get_clause("../../../etc/passwd", "d1")

    with pytest.raises(ValueError, match="[Pp]ath traversal"):
        engine.get_clause("Luat/Xay/dung", "d1")

    with pytest.raises(ValueError, match="[Pp]ath traversal"):
        engine.get_clause("Luat\\Xay\\dung", "d1")

    # 2. Unsafe clause_id
    with pytest.raises(ValueError, match="[Pp]ath traversal"):
        engine.get_clause("Luat-Xay-dung-2025", "../d1")

    with pytest.raises(ValueError, match="[Pp]ath traversal"):
        engine.get_clause("Luat-Xay-dung-2025", "d1;rm -rf")

    # 3. Unsafe table_id
    with pytest.raises(ValueError, match="[Pp]ath traversal"):
        engine.get_table("../../../etc", "bang_01")

    with pytest.raises(ValueError, match="[Pp]ath traversal"):
        engine.get_table("Luat-Xay-dung-2025", "../bang_01")

    with pytest.raises(ValueError, match="[Pp]ath traversal"):
        engine.get_table("Luat-Xay-dung-2025", "bang_01/secret")


def test_engine_get_point_and_letter_article(temp_knowledge_setup):
    """Verify engine extracts sub-points (Điểm) and letter-suffixed articles (Điều 65a)."""
    engine = LegalKnowledgeEngine(
        registry_path=temp_knowledge_setup["registry_path"],
        corpus_dir=temp_knowledge_setup["corpus_dir"],
    )

    # 1. Sub-point extraction via alias 'd6k2a'
    res_a = engine.get_clause("Luat-Xay-dung-2025", "d6k2a")
    assert res_a is not None
    assert res_a["clause_id"] == "dieu-6-khoan-2-diem-a"
    assert "Cấp công trình phục vụ quản lý xây dựng." in res_a["content"]
    assert "Cấp công trình phục vụ thiết kế xây dựng." not in res_a["content"]

    # 2. Sub-point extraction via alias 'd6k2b'
    res_b = engine.get_clause("Luat-Xay-dung-2025", "d6k2b")
    assert res_b is not None
    assert res_b["clause_id"] == "dieu-6-khoan-2-diem-b"
    assert "Cấp công trình phục vụ thiết kế xây dựng." in res_b["content"]

    # 3. Letter-suffixed article (Điều 65a) via alias 'd65a'
    res_65a = engine.get_clause("Luat-Xay-dung-2025", "d65a")
    assert res_65a is not None
    assert res_65a["clause_id"] == "dieu-65a"
    assert "Điều 65a. Quy định chuyển tiếp đặc thù" in res_65a["content"]
    assert "Nội dung quy định bổ sung của luật sửa đổi." in res_65a["content"]


def test_engine_clause_with_inline_anchor_not_truncated(temp_knowledge_setup):
    """Verify Khoản containing inline table/footnote anchors is NOT prematurely truncated."""
    engine = LegalKnowledgeEngine(
        registry_path=temp_knowledge_setup["registry_path"],
        corpus_dir=temp_knowledge_setup["corpus_dir"],
    )

    res_k3 = engine.get_clause("Luat-Xay-dung-2025", "d2k3")
    assert res_k3 is not None
    assert res_k3["clause_id"] == "dieu-2-khoan-3"
    # Ensure inline table and footnote are preserved in Khoản 3
    assert "| Bảng | Giá trị |" in res_k3["content"]
    assert "Ghi chú footnote điều khoản." in res_k3["content"]
    # Must not leak into Điều 3
    assert "Điều 3" not in res_k3["content"]


def test_engine_qcvn_section_extraction(temp_knowledge_setup):
    """Verify QCVN decimal section slicing captures sub-sections and stops before next section."""
    engine = LegalKnowledgeEngine(
        registry_path=temp_knowledge_setup["registry_path"],
        corpus_dir=temp_knowledge_setup["corpus_dir"],
    )

    # Query section 1.1 (should include 1.1.1 and 1.1.2, but stop before 1.2)
    res_11 = engine.get_clause("qcvn_06_2022_bxd", "1.1")
    assert res_11 is not None
    assert res_11["clause_id"] == "muc-1-1"
    content = res_11["content"]
    assert "### 1.1 Phạm vi điều chỉnh" in content
    assert "### 1.1.1 Quy chuẩn này quy định về an toàn cháy." in content
    assert "### 1.1.2 Đối tượng áp dụng." in content
    # MUST NOT include section 1.2
    assert "### 1.2 Tài liệu viện dẫn" not in content

    # Query specific sub-section 1.1.1
    res_111 = engine.get_clause("qcvn_06_2022_bxd", "1.1.1")
    assert res_111 is not None
    assert res_111["clause_id"] == "muc-1-1-1"
    assert "### 1.1.1 Quy chuẩn này quy định về an toàn cháy." in res_111["content"]
    assert "### 1.1.2 Đối tượng áp dụng." not in res_111["content"]


def test_engine_find_bundle_dir_precedence(temp_knowledge_setup):
    """Verify exact match takes precedence over base document prefix matching."""
    engine = LegalKnowledgeEngine(
        registry_path=temp_knowledge_setup["registry_path"],
        corpus_dir=temp_knowledge_setup["corpus_dir"],
    )

    # Base document query
    b_base = engine.find_bundle_dir("qcvn_06_2022_bxd")
    assert b_base is not None
    assert b_base.name == "qcvn_06_2022_bxd"

    # Amendment document query must NOT be hijacked by base document!
    b_amend = engine.find_bundle_dir("qcvn_06_2022_bxd_sd1_2023")
    assert b_amend is not None
    assert b_amend.name == "qcvn_06_2022_bxd_sd1_2023"


def test_engine_table_with_pipes(temp_knowledge_setup):
    """Verify table extraction escapes pipes in cell text."""
    engine = LegalKnowledgeEngine(
        registry_path=temp_knowledge_setup["registry_path"],
        corpus_dir=temp_knowledge_setup["corpus_dir"],
    )

    md_table = engine.get_table("Luat-Xay-dung-2025", "bang_pipes", format="markdown")
    assert md_table is not None
    assert r"TCVN 5574:2018 \| Mác 300" in md_table
