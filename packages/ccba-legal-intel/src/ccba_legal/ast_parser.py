"""AST Parser & Delta Patch Schema for Vietnamese Legal Documents."""

import re
from dataclasses import dataclass, field
from typing import Any

from .models import ASTNode, PatchAction


@dataclass
class DeltaPatchItem:
    """Individual patch instruction for a single AST node."""

    node_id: str
    action: PatchAction
    old_text_anchor: str = ""
    new_content: str = ""
    citation: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize patch item to dictionary."""
        return {
            "node_id": self.node_id,
            "action": self.action.value
            if isinstance(self.action, PatchAction)
            else str(self.action),
            "old_text_anchor": self.old_text_anchor,
            "new_content": self.new_content,
            "citation": self.citation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeltaPatchItem":
        """Instantiate patch item from dictionary."""
        return cls(
            node_id=data["node_id"],
            action=PatchAction(data["action"]),
            old_text_anchor=data.get("old_text_anchor", ""),
            new_content=data.get("new_content", ""),
            citation=data.get("citation", ""),
        )


@dataclass
class DeltaPatch:
    """Container for a legal delta patch document."""

    target_doc_id: str
    amending_doc_id: str
    patches: list[DeltaPatchItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize DeltaPatch to dictionary."""
        return {
            "target_doc_id": self.target_doc_id,
            "amending_doc_id": self.amending_doc_id,
            "patches": [p.to_dict() for p in self.patches],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeltaPatch":
        """Instantiate DeltaPatch from dictionary."""
        patches = [DeltaPatchItem.from_dict(p) for p in data.get("patches", [])]
        return cls(
            target_doc_id=data["target_doc_id"],
            amending_doc_id=data["amending_doc_id"],
            patches=patches,
        )


class ASTParser:
    """Parser converting normalized Markdown legal text into ASTNode tree."""

    # Regex patterns matching legal headers and items
    PART_PATTERN = re.compile(r"^#\s+(Phần\s+\d+|Phần\s+[IVXLCDM]+)[\.\:]?\s*(.*)$", re.IGNORECASE)
    CHAPTER_PATTERN = re.compile(
        r"^##\s+(Chương\s+\d+|Chương\s+[IVXLCDM]+)[\.\:]?\s*(.*)$", re.IGNORECASE
    )
    ARTICLE_PATTERN = re.compile(r"^###\s+Điều\s+(\d+)[\.\:]?\s*(.*)$", re.IGNORECASE)
    CLAUSE_PATTERN = re.compile(r"^(\d+)[\.\)]\s*(.*)$")
    POINT_PATTERN = re.compile(r"^([a-zđ])[\.\)]\s*(.*)$", re.IGNORECASE)

    def parse_markdown(self, markdown_text: str) -> list[ASTNode]:
        """Parse normalized markdown into a list of root ASTNodes."""
        lines = markdown_text.splitlines()
        root_nodes: list[ASTNode] = []

        current_article: ASTNode | None = None
        current_clause: ASTNode | None = None

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Check Article (Điều)
            art_match = self.ARTICLE_PATTERN.match(line_str)
            if art_match:
                art_num = art_match.group(1)
                art_title = art_match.group(2)
                node_id = f"D{art_num}"
                current_article = ASTNode(
                    node_id=node_id,
                    node_type="article",
                    title=art_title,
                    content=line_str,
                )
                root_nodes.append(current_article)
                current_clause = None
                continue

            # Check Clause (Khoản)
            clause_match = self.CLAUSE_PATTERN.match(line_str)
            if clause_match and current_article:
                clause_num = clause_match.group(1)
                clause_text = line_str
                node_id = f"{current_article.node_id}-K{clause_num}"
                current_clause = ASTNode(
                    node_id=node_id,
                    node_type="clause",
                    title=f"Khoản {clause_num}",
                    content=clause_text,
                    parent_id=current_article.node_id,
                )
                current_article.children.append(current_clause)
                continue

            # Check Point (Điểm)
            point_match = self.POINT_PATTERN.match(line_str)
            if point_match and current_clause:
                point_char = point_match.group(1).lower()
                point_text = line_str
                node_id = f"{current_clause.node_id}-P{point_char}"

                point_node = ASTNode(
                    node_id=node_id,
                    node_type="point",
                    title=f"Điểm {point_char}",
                    content=point_text,
                    parent_id=current_clause.node_id,
                )
                current_clause.children.append(point_node)
                continue

            # Fallback text appending to current node
            if current_clause:
                current_clause.content += f"\n{line_str}"
            elif current_article:
                current_article.content += f"\n{line_str}"

        return root_nodes

    def flatten_ast(self, nodes: list[ASTNode]) -> dict[str, ASTNode]:
        """Flatten ASTNode tree into a key-value dictionary by node_id."""
        flat: dict[str, ASTNode] = {}

        def _traverse(node: ASTNode) -> None:
            flat[node.node_id] = node
            for child in node.children:
                _traverse(child)

        for n in nodes:
            _traverse(n)

        return flat

    def find_node(self, nodes: list[ASTNode], node_id: str) -> ASTNode | None:
        """Find a node by node_id in the AST tree."""
        flat = self.flatten_ast(nodes)
        return flat.get(node_id)
