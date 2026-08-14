"""Unit tests for ccba_legal grounding, registry search/citation, and appendix splitter seams."""

from pathlib import Path

from ccba_legal import (
    AppendixSplitter,
    LegalGroundingGate,
    LegalRegistryManager,
    format_citation,
    roman_to_decimal,
    search_legal_registry,
    verify_legal_grounding,
)


def test_verify_legal_grounding_valid_citation():
    retrieved = [
        {"short_name": "NĐ 207/2026", "document_number": "207/2026/NĐ-CP", "id": "ND-207-2026"}
    ]
    response = (
        "Theo quy định tại [NĐ 207/2026 - 207/2026/NĐ-CP], nghiệm thu công trình theo Điều 12."
    )
    res = verify_legal_grounding(response, retrieved)
    assert res["is_grounded"] is True
    assert len(res["valid_citations"]) == 1
    assert "NĐ 207/2026 - 207/2026/NĐ-CP" in res["valid_citations"][0]


def test_verify_legal_grounding_excludes_markdown_links():
    retrieved = [
        {"short_name": "NĐ 207/2026", "document_number": "207/2026/NĐ-CP", "id": "ND-207-2026"}
    ]
    # Link format [NĐ 207/2026](https://example.com) should not count as standalone citation
    response = "Vui lòng xem chi tiết tại [NĐ 207/2026](https://example.com) để biết thêm."
    res = verify_legal_grounding(response, retrieved)
    # The markdown link should be ignored by the negative lookahead
    assert res["is_grounded"] is False


def test_format_grounded_response_and_gate_class():
    retrieved = [
        {"short_name": "NĐ 207/2026", "document_number": "207/2026/NĐ-CP", "id": "ND-207-2026"}
    ]
    gate = LegalGroundingGate()

    # Ungrounded response gets warning banner + disclaimer
    ungrounded_resp = "Nghiệm thu theo thỏa thuận miệng giữa các bên."
    formatted = gate.format(ungrounded_resp, retrieved)
    assert "⚠️ **[" in formatted
    assert "Disclaimer" in formatted

    # Grounded response keeps text and appends disclaimer
    grounded_resp = "Theo [NĐ 207/2026], nghiệm thu đúng quy trình."
    formatted_g = gate.format(grounded_resp, retrieved)
    assert "⚠️ **[Cảnh báo" not in formatted_g
    assert "Disclaimer" in formatted_g


def test_format_citation_and_registry_search(tmp_path: Path):
    doc = {
        "short_name": "Luật XD 2025",
        "document_number": "135/2025/QH15",
        "title": "Luật Xây dựng 2025",
    }
    assert format_citation(doc) == "[Luật XD 2025 - 135/2025/QH15]"
    assert format_citation({"short_name": "QCVN 06"}) == "[QCVN 06]"

    # Test search with custom registry YAML
    reg_file = tmp_path / "legal_registry.yaml"
    reg_file.write_text(
        """
metadata:
  version: "1.0"
laws:
  - id: "luat-xd-2025"
    title: "Luật Xây dựng sửa đổi 2025"
    short_name: "Luật XD 2025"
    document_number: "135/2025/QH15"
    topics: ["xây dựng", "quy hoạch"]
decrees:
  - id: "nd-pccc-2026"
    title: "Nghị định quy định chi tiết PCCC"
    short_name: "NĐ PCCC 2026"
    document_number: "105/2025/NĐ-CP"
    topics: ["pccc", "chữa cháy"]
""",
        encoding="utf-8",
    )

    mgr = LegalRegistryManager(registry_path=reg_file)
    results = mgr.search("PCCC chữa cháy", top_k=2)
    assert len(results) >= 1
    assert results[0]["id"] == "nd-pccc-2026"

    # Test module-level search_legal_registry
    results_helper = search_legal_registry("quy hoạch", registry_path=reg_file, top_k=1)
    assert len(results_helper) == 1
    assert results_helper[0]["id"] == "luat-xd-2025"


def test_roman_to_decimal():
    assert roman_to_decimal("I") == 1
    assert roman_to_decimal("IV") == 4
    assert roman_to_decimal("IX") == 9
    assert roman_to_decimal("XII") == 12
    assert roman_to_decimal("15") == 15


def test_appendix_splitter_slice():
    raw_md = """---
type: Law
title: Nghị định 105
---

# Nghị định 105/2025/NĐ-CP

Nội dung điều khoản chính.

# PHỤ LỤC I
Biểu mẫu nghiệm thu PCCC
(Ban hành kèm theo Nghị định 105)

Nội dung chi tiết phụ lục 1...

# PHỤ LỤC II
Danh mục phương tiện PCCC

Nội dung chi tiết phụ lục 2...
"""

    splitter = AppendixSplitter()
    updated_parent, appendices = splitter.split_document_content(
        content=raw_md, parent_slug="nd_105_2025", parent_filename="nd_105.md"
    )

    assert "## DANH SÁCH PHỤ LỤC ĐÍNH KÈM" in updated_parent
    assert len(appendices) == 2
    assert appendices[0]["filename"] == "nd_105_2025-phu_luc_01.md"
    assert appendices[1]["filename"] == "nd_105_2025-phu_luc_02.md"
    assert "Biểu mẫu nghiệm thu PCCC" in appendices[0]["content"]
    assert "Danh mục phương tiện PCCC" in appendices[1]["content"]
    assert 'uniclass: "Fi_10_20"' in appendices[0]["content"]
