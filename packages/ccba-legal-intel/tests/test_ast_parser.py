import pytest
import yaml

from ccba_legal.ast_parser import (
    ASTParser,
    DeltaPatch,
    DeltaPatchItem,
    PatchAction,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_ast_parser_parse_markdown() -> None:
    """Test parsing a structured legal document into an AST node tree."""
    md_content = """# Phần 1. QUY ĐỊNH CHUNG

## Chương I. ĐIỀU KHOẢN CHUNG

### Điều 1. Phạm vi điều chỉnh
1. Văn bản này quy định về an toàn phòng cháy và chữa cháy.
2. Các tổ chức, cá nhân có liên quan phải tuân thủ.
a) Đối với hộ gia đình phải có phương tiện PCCC.
b) Đối với cơ quan phải có phương án PCCC.

### Điều 2. Đối tượng áp dụng
Văn bản này áp dụng cho mọi cơ quan, tổ chức, cá nhân trên lãnh thổ Việt Nam.
"""
    parser = ASTParser()
    nodes = parser.parse_markdown(md_content)

    assert len(nodes) > 0
    flat_nodes = parser.flatten_ast(nodes)
    assert len(flat_nodes) > 0

    # Verify Article 1 Node
    d1 = parser.find_node(nodes, "D1")
    assert d1 is not None
    assert d1.node_type == "article"
    assert "Phạm vi điều chỉnh" in d1.title

    # Verify Clause 1 & Clause 2 Nodes
    d1_k1 = parser.find_node(nodes, "D1-K1")
    assert d1_k1 is not None
    assert "Văn bản này quy định" in d1_k1.content

    d1_k2 = parser.find_node(nodes, "D1-K2")
    assert d1_k2 is not None

    # Verify Point a under Clause 2
    d1_k2_pa = parser.find_node(nodes, "D1-K2-Pa")
    assert d1_k2_pa is not None
    assert "hộ gia đình" in d1_k2_pa.content


def test_delta_patch_yaml_serialization() -> None:
    """Test serializing and deserializing a DeltaPatch object to/from YAML."""
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

    patch_dict = patch.to_dict()
    yaml_str = yaml.dump(patch_dict, allow_unicode=True)

    loaded_dict = yaml.safe_load(yaml_str)
    restored_patch = DeltaPatch.from_dict(loaded_dict)

    assert restored_patch.target_doc_id == "Luat-55-2024"
    assert len(restored_patch.patches) == 1
    assert restored_patch.patches[0].node_id == "D1-K2-Pa"
    assert restored_patch.patches[0].action == PatchAction.REPLACE
