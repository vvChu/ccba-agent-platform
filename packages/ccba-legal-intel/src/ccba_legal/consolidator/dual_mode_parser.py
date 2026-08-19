"""Dual-Mode AST Parser for Vietnamese Legal Texts (QCVN/TCVN and Law/Decrees)."""

import re
from dataclasses import dataclass, field
from typing import Any
from .patch_manifest_schema import DocMode


@dataclass
class ASTNode:
    """Represents a structured node in the legal document syntax tree."""
    node_id: str
    node_type: str  # "chapter", "section", "clause", "article", "point", "table", "appendix", "header_block"
    title: str = ""
    content: str = ""
    clause_number: str = ""
    anchor: str = ""
    parent_id: str | None = None
    children: list["ASTNode"] = field(default_factory=list)
    heading_level: int = 3
    heading_prefix: str = "###"
    raw_header_line: str = ""
    
    # Metadata fields conforming to OKF v2.0
    jurisdiction: str | None = "CQXD"
    grace_period_end: str | None = None
    source_pdf_page: int | None = None
    cong_bao_number: str | None = None
    compliance_severity: str = "CRITICAL_DEFECT"
    normative_status: str = "MANDATORY"
    legal_enforceability: str = "DIRECTLY_ENFORCEABLE"
    citation: str | None = None
    is_amended: bool = False
    is_repealed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert ASTNode to dictionary representation."""
        res: dict[str, Any] = {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "title": self.title,
            "clause_number": self.clause_number,
            "anchor": self.anchor or self.node_id,
            "content": self.content,
            "parent_id": self.parent_id,
            "jurisdiction": self.jurisdiction or "CQXD",
            "compliance_severity": self.compliance_severity,
            "normative_status": self.normative_status,
            "legal_enforceability": self.legal_enforceability,
            "children": [c.to_dict() for c in self.children],
        }
        if self.grace_period_end:
            res["grace_period_end"] = self.grace_period_end
        if self.source_pdf_page:
            res["source_pdf_page"] = self.source_pdf_page
        if self.cong_bao_number:
            res["cong_bao_number"] = self.cong_bao_number
        return res

    def to_clause_dict(self) -> dict[str, Any]:
        """Convert to atomic clauses.json schema entry."""
        cid = self.anchor or self.node_id
        res: dict[str, Any] = {
            "id": cid,
            "clause_number": self.clause_number or self.title.split()[0] if self.title else "",
            "title": self.title,
            "content": self.content,
            "jurisdiction": self.jurisdiction or "CQXD",
            "compliance_severity": self.compliance_severity,
            "normative_status": self.normative_status,
            "legal_enforceability": self.legal_enforceability,
            "clause_id": cid,
            "anchor": cid,
        }
        if self.grace_period_end:
            res["grace_period_end"] = self.grace_period_end
        if self.source_pdf_page:
            res["source_pdf_page"] = self.source_pdf_page
        if self.cong_bao_number:
            res["cong_bao_number"] = self.cong_bao_number
        return res


class DualModeASTParser:
    """Parser converting normalized Markdown into an ASTNode tree for both QCVN and Laws."""

    # Regex for QCVN / TCVN Section Headings
    # Matches:
    # 1. <a id="muc-1-1-3" name="muc-1-1-3"></a>1.1.3 Tiêu đề
    # 2. ### <a id="muc-1-1-3" name="muc-1-1-3"></a>1.1.3 Tiêu đề
    # 3. ### 1.1.3 Tiêu đề (with previous <a id="muc-1-1-3"></a>)
    QCVN_HEADING_REGEX = re.compile(
        r"^(#{1,6})\s*(?:<a\s+id=[\"']([^\"']+)[\"'][^>]*></a>\s*)?([0-9]+(?:\.[0-9]+[a-z]?)*|[A-Z]\.[0-9]+(?:\.[0-9]+)*)\s*(.*?)$"
    )
    INLINED_ANCHOR_REGEX = re.compile(
        r"^(#{1,6})\s*<a\s+id=[\"']([^\"']+)[\"'](?:\s+name=[\"'][^\"']+[\"'])?[^>]*></a>\s*(.*?)$"
    )
    STANDALONE_ANCHOR_REGEX = re.compile(r"^<a\s+id=[\"']([^\"']+)[\"'][^>]*></a>$")

    # Regex for Law / Decree Headings
    ARTICLE_REGEX = re.compile(
        r"^(#{1,6})\s*(?:<a\s+id=[\"']([^\"']+)[\"'][^>]*></a>\s*)?(?:Điều|ĐIỀU)\s+(\d+[a-z]?)[\.\:]?\s*(.*?)$",
        re.IGNORECASE
    )
    CHAPTER_REGEX = re.compile(
        r"^(#{1,6})\s*(?:<a\s+id=[\"']([^\"']+)[\"'][^>]*></a>\s*)?(?:Chương|CHƯƠNG)\s+([IVXLCDM\d]+)[\.\:]?\s*(.*?)$",
        re.IGNORECASE
    )

    def parse(self, markdown_text: str, mode: DocMode = DocMode.QCVN) -> list[ASTNode]:
        """Parse markdown into a list of ASTNode trees."""
        lines = markdown_text.splitlines()
        root_nodes: list[ASTNode] = []

        pending_anchor: str | None = None
        current_node: ASTNode | None = None
        preamble_lines: list[str] = []
        in_body = False

        for line in lines:
            line_str = line.strip()

            # Check standalone anchor tag
            m_anchor = self.STANDALONE_ANCHOR_REGEX.match(line_str)
            if m_anchor:
                pending_anchor = m_anchor.group(1)
                continue

            # Check Heading according to mode
            node = self._parse_heading_line(line_str, pending_anchor, mode)
            if node:
                in_body = True
                if current_node:
                    current_node.content = current_node.content.strip()
                current_node = node
                root_nodes.append(node)
                pending_anchor = None
                continue

            if not in_body:
                preamble_lines.append(line)
            else:
                if current_node:
                    if current_node.content:
                        current_node.content += f"\n{line}"
                    else:
                        current_node.content = line

        if current_node:
            current_node.content = current_node.content.strip()

        # Wrap preamble if present
        if preamble_lines:
            preamble_content = "\n".join(preamble_lines).strip()
            if preamble_content:
                preamble_node = ASTNode(
                    node_id="preamble",
                    node_type="preamble",
                    title="Lời nói đầu & Mục lục",
                    content=preamble_content,
                    heading_level=1,
                    heading_prefix="#",
                )
                root_nodes.insert(0, preamble_node)

        return root_nodes

    def _parse_heading_line(self, line_str: str, pending_anchor: str | None, mode: DocMode) -> ASTNode | None:
        """Helper to match and construct an ASTNode from a heading line."""
        if not line_str.startswith("#"):
            return None

        # Mode QCVN / TCVN
        if mode in (DocMode.QCVN, DocMode.TCVN):
            # Check inlined anchor with clause number: ### <a id="muc-1-1"></a>1.1 Tiêu đề
            m_qcvn = self.QCVN_HEADING_REGEX.match(line_str)
            if m_qcvn:
                hashes, inlined_anchor, num, rest = m_qcvn.groups()
                level = len(hashes)
                anchor = inlined_anchor or pending_anchor or f"muc-{num.lower().replace('.', '-')}"
                clean_title = f"{num} {rest}".strip() if rest else num
                return ASTNode(
                    node_id=anchor,
                    node_type="section" if level <= 3 else "clause",
                    title=clean_title,
                    clause_number=num,
                    anchor=anchor,
                    heading_level=level,
                    heading_prefix=hashes,
                    raw_header_line=line_str,
                )

            # Check general inlined anchor: ### <a id="muc-1"></a>1  QUY ĐỊNH CHUNG
            m_inlined = self.INLINED_ANCHOR_REGEX.match(line_str)
            if m_inlined:
                hashes, inlined_anchor, title = m_inlined.groups()
                level = len(hashes)
                anchor = inlined_anchor or pending_anchor or "section"
                m_num = re.match(r"^([0-9]+(?:\.[0-9]+[a-z]?)*|[A-Z]\.[0-9]+(?:\.[0-9]+)*)", title)
                num = m_num.group(1) if m_num else ""
                return ASTNode(
                    node_id=anchor,
                    node_type="section" if level <= 3 else "clause",
                    title=title.strip(),
                    clause_number=num,
                    anchor=anchor,
                    heading_level=level,
                    heading_prefix=hashes,
                    raw_header_line=line_str,
                )

        # Mode LUAT / NGHI_DINH / THONG_TU
        else:
            m_art = self.ARTICLE_REGEX.match(line_str)
            if m_art:
                hashes, inlined_anchor, art_num, title = m_art.groups()
                level = len(hashes)
                anchor = inlined_anchor or pending_anchor or f"dieu-{art_num.lower()}"
                node_id = f"D{art_num}"
                clean_title = f"Điều {art_num}. {title}".strip()
                return ASTNode(
                    node_id=node_id,
                    node_type="article",
                    title=clean_title,
                    clause_number=art_num,
                    anchor=anchor,
                    heading_level=level,
                    heading_prefix=hashes,
                    raw_header_line=line_str,
                )

            m_chap = self.CHAPTER_REGEX.match(line_str)
            if m_chap:
                hashes, inlined_anchor, chap_num, title = m_chap.groups()
                level = len(hashes)
                anchor = inlined_anchor or pending_anchor or f"chuong-{chap_num.lower()}"
                clean_title = f"Chương {chap_num}. {title}".strip()
                return ASTNode(
                    node_id=f"C{chap_num}",
                    node_type="chapter",
                    title=clean_title,
                    clause_number=chap_num,
                    anchor=anchor,
                    heading_level=level,
                    heading_prefix=hashes,
                    raw_header_line=line_str,
                )

        return None

    def flatten_ast(self, nodes: list[ASTNode]) -> dict[str, ASTNode]:
        """Flatten ASTNode tree into dictionary indexed by node_id, anchor, and normalized forms."""
        flat: dict[str, ASTNode] = {}

        def _traverse(node: ASTNode) -> None:
            flat[node.node_id] = node
            if node.anchor:
                flat[node.anchor] = node
            if node.clause_number:
                flat[node.clause_number] = node
                flat[f"muc-{node.clause_number.replace('.', '-')}"] = node
            for child in node.children:
                _traverse(child)

        for n in nodes:
            _traverse(n)

        return flat
