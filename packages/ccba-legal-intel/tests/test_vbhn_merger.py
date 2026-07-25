"""Unit tests for VBHNMerger in ccba_legal."""

from pathlib import Path

from ccba_legal.ast_parser import (
    ASTParser,
    DeltaPatch,
    DeltaPatchItem,
    PatchAction,
)
from ccba_legal.vbhn_merger import VBHNMerger


def test_vbhn_merger_apply_patch_replace_and_abrogate() -> None:
    """Test applying REPLACE and ABROGATE patch actions to AST nodes."""
    md_content = """### Điều 1. Phạm vi điều chỉnh
1. Văn bản này quy định về an toàn phòng cháy và chữa cháy.
2. Các tổ chức, cá nhân có liên quan phải tuân thủ.
a) Đối với hộ gia đình phải có phương tiện PCCC.
b) Đối với cơ quan phải có phương án PCCC.
"""
    parser = ASTParser()
    nodes = parser.parse_markdown(md_content)

    # 1. REPLACE item for D1-K2-Pa
    p1 = DeltaPatchItem(
        node_id="D1-K2-Pa",
        action=PatchAction.REPLACE,
        old_text_anchor="Đối với hộ gia đình phải có phương tiện PCCC.",
        new_content="a) Đối với hộ gia đình phải trang bị ít nhất 01 bình chữa cháy.",
        citation="Sửa đổi bởi Điều 1 Luật 31/2024",
    )
    # 2. ABROGATE item for D1-K2-Pb
    p2 = DeltaPatchItem(
        node_id="D1-K2-Pb",
        action=PatchAction.ABROGATE,
        old_text_anchor="Đối với cơ quan phải có phương án PCCC.",
        citation="Bãi bỏ bởi Điều 2 Luật 31/2024",
    )

    patch = DeltaPatch(
        target_doc_id="Luat-55-2024",
        amending_doc_id="Luat-31-2024",
        patches=[p1, p2],
    )

    merger = VBHNMerger()
    updated_nodes = merger.apply_patch(nodes, patch)

    d1_k2_pa = parser.find_node(updated_nodes, "D1-K2-Pa")
    assert d1_k2_pa is not None
    assert "01 bình chữa cháy" in d1_k2_pa.content
    assert "Luật 31/2024" in d1_k2_pa.content

    d1_k2_pb = parser.find_node(updated_nodes, "D1-K2-Pb")
    assert d1_k2_pb is not None
    assert "~~" in d1_k2_pb.content or "bãi bỏ" in d1_k2_pb.content.lower()


def test_vbhn_merger_merge_and_save(tmp_path: Path) -> None:
    """Test merge_and_save generates VBHN_{slug}.md file."""
    md_content = """### Điều 1. Phạm vi điều chỉnh
1. Văn bản này quy định về an toàn PCCC.
"""
    p1 = DeltaPatchItem(
        node_id="D1-K1",
        action=PatchAction.REPLACE,
        old_text_anchor="Văn bản này quy định về an toàn PCCC.",
        new_content="1. Văn bản này quy định về an toàn PCCC và CNCH.",
        citation="Khoản 1 Điều 1 Luật 31/2024",
    )
    patch = DeltaPatch(
        target_doc_id="Luat-55-2024",
        amending_doc_id="Luat-31-2024",
        patches=[p1],
    )

    merger = VBHNMerger()
    out_file = merger.merge_and_save(
        original_markdown=md_content,
        patch=patch,
        output_dir=tmp_path,
        slug="luat_55_2024",
    )

    assert out_file.exists()
    assert out_file.name == "VBHN_luat_55_2024.md"

    text = out_file.read_text(encoding="utf-8")
    assert "PCCC và CNCH" in text
    assert "Luật 31/2024" in text
