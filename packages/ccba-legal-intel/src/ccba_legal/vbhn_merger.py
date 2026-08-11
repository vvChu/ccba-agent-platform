"""VBHN Merger Engine and Visual Diff Exporter."""

from pathlib import Path

from .ast_parser import ASTNode, ASTParser, DeltaPatch, PatchAction


class VBHNMerger:
    """Engine executing Patch instructions on legal AST trees and exporting VBHN markdown."""

    def apply_patch(
        self,
        nodes: list[ASTNode],
        patch: DeltaPatch,
    ) -> list[ASTNode]:
        """Apply a DeltaPatch onto an ASTNode tree and return updated nodes."""
        parser = ASTParser()
        flat_nodes = parser.flatten_ast(nodes)

        for item in patch.patches:
            target_node = flat_nodes.get(item.node_id)
            if not target_node:
                continue

            citation_str = f"\n\n> *[Chú thích: {item.citation}]*" if item.citation else ""

            if item.action == PatchAction.REPLACE:
                target_node.content = f"{item.new_content}{citation_str}"

            elif item.action == PatchAction.ABROGATE:
                target_node.content = f"~~{target_node.content}~~\n\n> *[Đã bị bãi bỏ: {item.citation or 'Theo quy định mới'}]*"

            elif item.action == PatchAction.SUSPEND:
                target_node.content = f"{target_node.content}\n\n> *[Tạm ngưng hiệu lực: {item.citation or 'Theo quy định chuyển tiếp'}]*"

            elif item.action in (PatchAction.INSERT_AFTER, PatchAction.INSERT_BEFORE):
                new_node_id = f"{item.node_id}-new"
                inserted_node = ASTNode(
                    node_id=new_node_id,
                    node_type=target_node.node_type,
                    title=f"{target_node.title} (Bổ sung)",
                    content=f"{item.new_content}{citation_str}",
                    parent_id=target_node.parent_id,
                )
                if target_node.parent_id:
                    parent = flat_nodes.get(target_node.parent_id)
                    if parent:
                        idx = parent.children.index(target_node)
                        insert_pos = idx + 1 if item.action == PatchAction.INSERT_AFTER else idx
                        parent.children.insert(insert_pos, inserted_node)
                        flat_nodes[new_node_id] = inserted_node

        return nodes

    def export_visual_diff_markdown(self, nodes: list[ASTNode]) -> str:
        """Render ASTNode tree into Markdown string."""
        lines: list[str] = []

        def _render(node: ASTNode) -> None:
            if node.node_type == "part":
                lines.append(f"# {node.content}")
            elif node.node_type == "chapter":
                lines.append(f"## {node.content}")
            elif node.node_type == "article":
                lines.append(f"### {node.title}\n{node.content}")
            else:
                lines.append(node.content)

            for child in node.children:
                _render(child)

        for n in nodes:
            _render(n)

        return "\n\n".join(lines)

    def merge_and_save(
        self,
        original_markdown: str,
        patch: DeltaPatch,
        output_dir: Path,
        slug: str,
    ) -> Path:
        """Parse markdown -> apply patch -> export visual diff -> save VBHN_{slug}.md."""
        parser = ASTParser()
        nodes = parser.parse_markdown(original_markdown)

        updated_nodes = self.apply_patch(nodes, patch)
        merged_md = self.export_visual_diff_markdown(updated_nodes)

        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / f"VBHN_{slug}.md"
        out_file.write_text(merged_md, encoding="utf-8")
        return out_file
