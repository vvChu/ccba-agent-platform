"""Unit tests for DeltaPatchGenerator and apply_patch_dry_run in ccba_legal."""

from ccba_legal.ast_parser import (
    ASTParser,
    DeltaPatch,
    DeltaPatchItem,
    PatchAction,
)
from ccba_legal.patch_generator import DeltaPatchGenerator


def test_delta_patch_generator_dry_run_success() -> None:
    """Test apply_patch_dry_run returns True when all old_text_anchors match AST nodes."""
    md_content = """### Điều 1. Phạm vi điều chỉnh
1. Văn bản này quy định về an toàn phòng cháy và chữa cháy.
2. Các tổ chức, cá nhân có liên quan phải tuân thủ.
a) Đối với hộ gia đình phải có phương tiện PCCC.
b) Đối với cơ quan phải có phương án PCCC.
"""
    parser = ASTParser()
    nodes = parser.parse_markdown(md_content)

    patch_item = DeltaPatchItem(
        node_id="D1-K2-Pa",
        action=PatchAction.REPLACE,
        old_text_anchor="Đối với hộ gia đình phải có phương tiện PCCC.",
        new_content="Đối với hộ gia đình phải trang bị ít nhất 01 bình chữa cháy.",
        citation="Sửa đổi bởi Khoản 1 Điều 2 Luật 31/2024",
    )
    patch = DeltaPatch(
        target_doc_id="Luat-55-2024",
        amending_doc_id="Luat-31-2024",
        patches=[patch_item],
    )

    generator = DeltaPatchGenerator()
    is_valid, errors = generator.apply_patch_dry_run(nodes, patch)

    assert is_valid is True
    assert len(errors) == 0


def test_delta_patch_generator_dry_run_anchor_mismatch() -> None:
    """Test apply_patch_dry_run catches ANCHOR_MISMATCH when anchor text is not found."""
    md_content = """### Điều 1. Phạm vi điều chỉnh
1. Văn bản này quy định về an toàn phòng cháy và chữa cháy.
2. Các tổ chức, cá nhân có liên quan phải tuân thủ.
a) Đối với hộ gia đình phải có phương tiện PCCC.
"""
    parser = ASTParser()
    nodes = parser.parse_markdown(md_content)

    # Wrong anchor string
    patch_item = DeltaPatchItem(
        node_id="D1-K2-Pa",
        action=PatchAction.REPLACE,
        old_text_anchor="Chuỗi văn bản sai hoàn toàn không tồn tại trong node",
        new_content="Nội dung mới",
        citation="Sửa đổi bởi Luật 31",
    )
    patch = DeltaPatch(
        target_doc_id="Luat-55-2024",
        amending_doc_id="Luat-31-2024",
        patches=[patch_item],
    )

    generator = DeltaPatchGenerator()
    is_valid, errors = generator.apply_patch_dry_run(nodes, patch)

    assert is_valid is False
    assert len(errors) == 1
    assert "[ANCHOR_MISMATCH]" in errors[0]


def test_generate_patch_from_text_mock() -> None:
    """Test generating a DeltaPatch from raw text using mock LLM response."""
    mock_json = """{
        "target_doc_id": "Luat-55-2024",
        "amending_doc_id": "Luat-31-2024",
        "patches": [
            {
                "node_id": "D1-K1",
                "action": "REPLACE",
                "old_text_anchor": "quy định về an toàn phòng cháy",
                "new_content": "quy định về phòng cháy, chữa cháy và cứu nạn",
                "citation": "Khoản 1 Điều 1 Luật 31/2024"
            }
        ]
    }"""

    generator = DeltaPatchGenerator()
    patch = generator.generate_patch_from_text(
        target_doc_id="Luat-55-2024",
        amending_doc_id="Luat-31-2024",
        original_text="### Điều 1...",
        amending_text="Điều 1 Luật 31 sửa Điều 1...",
        mock_llm_response=mock_json,
    )

    assert patch.target_doc_id == "Luat-55-2024"
    assert len(patch.patches) == 1
    assert patch.patches[0].node_id == "D1-K1"
    assert patch.patches[0].action == PatchAction.REPLACE
