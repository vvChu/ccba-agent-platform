"""Deterministic Legal Document Patcher and Triple Output Generator."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .patch_manifest_schema import (
    DefectSeverity,
    DocMode,
    PatchAction,
    PatchItem,
    PatchManifest,
    load_manifest,
)
from .dual_mode_parser import (
    ASTNode,
    DualModeASTParser,
)


@dataclass
class ConsolidationResult:
    """Result container of the consolidation pipeline."""
    success: bool
    consolidated_md_path: Path
    clauses_json_path: Path
    diff_matrix_path: Path
    total_clauses: int
    modified_clauses: int
    added_clauses: int
    repealed_clauses: int
    errors: list[str]


class LegislativeConsolidator:
    """Deterministic Patcher Engine executing PatchManifest onto legal document AST."""

    def __init__(self, manifest: PatchManifest, base_dir: Path | None = None):
        self.manifest = manifest
        self.base_dir = base_dir or Path(".")
        self.parser = DualModeASTParser()

    @classmethod
    def from_manifest_file(cls, manifest_path: Path | str) -> "LegislativeConsolidator":
        mpath = Path(manifest_path)
        manifest = load_manifest(mpath)
        return cls(manifest=manifest, base_dir=mpath.parent)

    def consolidate(
        self,
        base_md_path: Path | str,
        output_dir: Path | str,
        amending_md_path: Path | str | None = None,
    ) -> ConsolidationResult:
        """Execute consolidation and generate all 3 OKF v2.0 artifacts."""
        base_path = Path(base_md_path)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        if not base_path.exists():
            raise FileNotFoundError(f"Base markdown file not found: {base_path}")

        base_text = base_path.read_text(encoding="utf-8")
        nodes = self.parser.parse(base_text, mode=self.manifest.doc_mode)

        # Load amending document text if needed for resolving content sources
        amending_text = ""
        if amending_md_path:
            am_path = Path(amending_md_path)
            if am_path.exists():
                amending_text = am_path.read_text(encoding="utf-8")

        # Apply patches
        modified_count = 0
        added_count = 0
        repealed_count = 0
        diff_records: list[dict[str, Any]] = []
        errors: list[str] = []

        for p_idx, patch in enumerate(self.manifest.patches):
            success, msg, rec = self._apply_single_patch(nodes, patch, amending_text)
            if not success:
                errors.append(f"Patch #{p_idx+1} ({patch.action.value} on {patch.target_anchor}) failed: {msg}")
            else:
                if patch.action in (PatchAction.INSERT_AFTER, PatchAction.INSERT_BEFORE, PatchAction.INSERT_RANGE_AFTER):
                    added_count += (len(patch.new_anchors) if patch.new_anchors else 1)
                elif patch.action == PatchAction.REPEAL:
                    repealed_count += 1
                else:
                    modified_count += 1
                if rec:
                    diff_records.append(rec)

        # Render outputs
        # 1. Consolidated Markdown
        consolidated_md = self._render_consolidated_markdown(nodes)
        
        # File naming convention
        base_slug = base_path.stem
        out_md_name = f"{base_slug}_hop_nhat.md"
        if "qcvn_04_2021" in base_slug:
            out_md_name = "qcvn_04_2021_bxd_hop_nhat_2026.md"
        elif "qcvn_06_2022" in base_slug:
            out_md_name = "qcvn_06_2022_bxd_hop_nhat_2023.md"

        consolidated_md_path = out_dir / out_md_name
        consolidated_md_path.write_text(consolidated_md, encoding="utf-8")

        # 2. Rich clauses.json
        clauses_data = self._render_clauses_json(nodes)
        clauses_json_path = out_dir / "clauses.json"
        clauses_json_path.write_text(json.dumps(clauses_data, ensure_ascii=False, indent=2), encoding="utf-8")

        # 2b. Sync qa_benchmark.json
        qa_list = []
        for c in clauses_data:
            num = c.get("clause_number", "")
            title = c.get("title", "")
            qa_list.append({
                "question": f"Quy định kỹ thuật tại mục {num} ({title}) của {self.manifest.title} quy định như thế nào?",
                "ground_truth_clause": num,
                "ground_truth_id": c["id"],
                "expected_keywords": [w for w in title.split() if len(w) > 3][:4]
            })
        qa_benchmark_path = out_dir / "qa_benchmark.json"
        qa_benchmark_path.write_text(json.dumps(qa_list, ensure_ascii=False, indent=2), encoding="utf-8")

        # 3. Diff Matrix Markdown
        diff_matrix_md = self._render_diff_matrix(diff_records)
        diff_matrix_path = out_dir / "bang_so_sanh_thay_doi.md"
        diff_matrix_path.write_text(diff_matrix_md, encoding="utf-8")

        return ConsolidationResult(
            success=(len(errors) == 0),
            consolidated_md_path=consolidated_md_path,
            clauses_json_path=clauses_json_path,
            diff_matrix_path=diff_matrix_path,
            total_clauses=len(clauses_data),
            modified_clauses=modified_count,
            added_clauses=added_count,
            repealed_clauses=repealed_count,
            errors=errors,
        )

    def _apply_single_patch(
        self,
        nodes: list[ASTNode],
        patch: PatchItem,
        amending_text: str,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        """Apply a single patch item to the ASTNode tree."""
        flat = self.parser.flatten_ast(nodes)
        target_node = flat.get(patch.target_anchor)
        if not target_node:
            return False, f"Target anchor '{patch.target_anchor}' not found in AST", None

        # Resolve content
        new_content = patch.new_content_inline or ""
        if patch.new_content_source and amending_text:
            new_content = self._extract_source_content(patch.new_content_source, amending_text)

        old_content_snippet = target_node.content[:150] + "..." if len(target_node.content) > 150 else target_node.content

        rec: dict[str, Any] = {
            "clause_id": patch.new_anchor or patch.target_anchor,
            "title": target_node.title,
            "action": patch.action.value,
            "citation": patch.citation,
            "severity": patch.defect_severity.value,
            "old_content": old_content_snippet,
            "new_content": new_content[:150] + "..." if len(new_content) > 150 else new_content,
        }

        # Apply Action Token
        if patch.action == PatchAction.REPLACE:
            callout = f"> [!NOTE]\n> **{patch.citation}:**\n" + "\n".join(f"> {line}" for line in new_content.splitlines())
            target_node.content = callout
            target_node.is_amended = True
            if patch.jurisdiction:
                target_node.jurisdiction = patch.jurisdiction
            if patch.grace_period_end:
                target_node.grace_period_end = patch.grace_period_end
            if patch.source_pdf_page:
                target_node.source_pdf_page = patch.source_pdf_page

        elif patch.action == PatchAction.APPEND:
            callout = f"\n\n> [!NOTE]\n> **{patch.citation}:**\n" + "\n".join(f"> {line}" for line in new_content.splitlines())
            target_node.content += callout
            target_node.is_amended = True

        elif patch.action == PatchAction.REPEAL:
            target_node.content = f"> [!WARNING]\n> **Đã bãi bỏ theo {patch.citation}**\n\n~~{target_node.content}~~"
            target_node.is_repealed = True

        elif patch.action == PatchAction.SUBSTITUTE_PHRASE:
            if patch.old_phrase and patch.new_phrase:
                target_node.content = target_node.content.replace(patch.old_phrase, patch.new_phrase)
                target_node.is_amended = True

        elif patch.action in (PatchAction.INSERT_AFTER, PatchAction.INSERT_BEFORE):
            idx = nodes.index(target_node)
            insert_idx = idx + 1 if patch.action == PatchAction.INSERT_AFTER else idx
            new_anchor = patch.new_anchor or f"{patch.target_anchor}-new"
            
            # Extract number from new_anchor if available
            m_num = re.search(r"(\d+(?:\.\d+)*)", new_anchor)
            cnum = m_num.group(1) if m_num else ""

            # Check if content has heading
            first_line = new_content.splitlines()[0] if new_content else ""
            clean_title = f"{cnum} (Bổ sung)"
            if first_line.startswith("#"):
                clean_title = re.sub(r"^#+\s*", "", first_line)
                new_content = "\n".join(new_content.splitlines()[1:]).strip()

            new_node = ASTNode(
                node_id=new_anchor,
                node_type=target_node.node_type,
                title=clean_title,
                clause_number=cnum,
                anchor=new_anchor,
                content=new_content,
                heading_level=target_node.heading_level,
                heading_prefix=target_node.heading_prefix,
                jurisdiction=patch.jurisdiction or target_node.jurisdiction,
                grace_period_end=patch.grace_period_end,
                source_pdf_page=patch.source_pdf_page,
                is_amended=True,
                citation=patch.citation,
            )
            nodes.insert(insert_idx, new_node)

        elif patch.action == PatchAction.INSERT_RANGE_AFTER:
            idx = nodes.index(target_node)
            insert_idx = idx + 1
            for na in patch.new_anchors:
                m_num = re.search(r"(\d+(?:\.\d+)*)", na)
                cnum = m_num.group(1) if m_num else ""
                child_node = ASTNode(
                    node_id=na,
                    node_type=target_node.node_type,
                    title=f"{cnum} (Bổ sung)",
                    clause_number=cnum,
                    anchor=na,
                    content=new_content,
                    heading_level=target_node.heading_level,
                    heading_prefix=target_node.heading_prefix,
                    jurisdiction=patch.jurisdiction,
                    grace_period_end=patch.grace_period_end,
                    source_pdf_page=patch.source_pdf_page,
                    is_amended=True,
                    citation=patch.citation,
                )
                nodes.insert(insert_idx, child_node)
                insert_idx += 1

        return True, "Success", rec

    def _extract_source_content(self, source_expr: str, text: str) -> str:
        """Extract section from source document using anchor pattern file#anchor."""
        anchor_part = source_expr.split("#")[-1] if "#" in source_expr else source_expr
        
        # Range match e.g. sd1-muc-1-4-31..sd1-muc-1-4-34
        if ".." in anchor_part:
            start_a, end_a = anchor_part.split("..")
            patt = rf'<a\s+id=[\"\']{re.escape(start_a)}[\"\'][\s\S]*?(?=<a\s+id=[\"\']{re.escape(end_a)}[\"\']|\Z)'
            m = re.search(patt, text)
            if m:
                return m.group(0).strip()
        else:
            patt = rf'<a\s+id=[\"\']{re.escape(anchor_part)}[\"\'][\s\S]*?(?=\n<a\s+id=|\n#{{1,6}}\s+|\Z)'
            m = re.search(patt, text)
            if m:
                return m.group(0).strip()

        return ""

    def _render_consolidated_markdown(self, nodes: list[ASTNode]) -> str:
        """Render modified ASTNode tree back into clean GFM Markdown with canonical anchors."""
        lines: list[str] = []

        for node in nodes:
            if node.node_type == "preamble":
                lines.append(node.content)
                lines.append("")
                continue

            # Standard Heading with Canonical Anchor
            hashes = node.heading_prefix or "###"
            anchor = node.anchor or node.node_id
            
            # Format header line: #### <a id="muc-1-1-3" name="muc-1-1-3"></a>1.1.3 Tiêu đề
            citation_note = f" *({node.citation})*" if node.citation and node.citation not in node.title else ""
            h_line = f"{hashes} <a id=\"{anchor}\" name=\"{anchor}\"></a>{node.title}{citation_note}"
            lines.append(h_line)
            lines.append("")

            if node.content:
                lines.append(node.content)
                lines.append("")

        return "\n".join(lines).strip() + "\n"

    def _render_clauses_json(self, nodes: list[ASTNode]) -> list[dict[str, Any]]:
        """Export AST nodes into rich atomic clauses array."""
        clauses: list[dict[str, Any]] = []
        for node in nodes:
            if node.node_type == "preamble":
                continue
            c_dict = node.to_clause_dict()
            if not c_dict.get("cong_bao_number"):
                c_dict["cong_bao_number"] = self.manifest.default_cong_bao_number
            if not c_dict.get("jurisdiction"):
                c_dict["jurisdiction"] = self.manifest.default_jurisdiction
            if not c_dict.get("compliance_severity"):
                c_dict["compliance_severity"] = "CRITICAL_DEFECT"
            clauses.append(c_dict)
        return clauses

    def _render_diff_matrix(self, diff_records: list[dict[str, Any]]) -> str:
        """Generate comparative diff table in Markdown."""
        lines = [
            f"# BẢNG MA TRẬN ĐỐI CHIẾU SỬA ĐỔI — {self.manifest.title}",
            "",
            f"> **Văn bản Gốc:** `{self.manifest.target_doc_id}`  ",
            f"> **Văn bản Sửa đổi:** `{self.manifest.amending_doc_id}` ({self.manifest.official_citation})  ",
            f"> **Ngày hiệu lực:** `{self.manifest.effective_date}`  ",
            "",
            "| STT | Mã Điều Khoản | Thao Tác | Căn Cứ Sửa Đổi | Mức Độ Rủi Ro Kiểm Toán | Tóm Tắt Quy Định Mới |",
            "|:---:|:---|:---:|:---|:---:|:---|",
        ]

        for i, rec in enumerate(diff_records, 1):
            sev_badge = "🔴 Critical Defect" if rec["severity"] == "CRITICAL_DEFECT" else ("🟡 Warning Notice" if rec["severity"] == "WARNING_NOTICE" else "🔵 Informative")
            action_badge = f"`{rec['action']}`"
            clean_new = rec["new_content"].replace("\n", " ").replace("|", "\\|")[:80] + "..."
            lines.append(
                f"| {i} | `{rec['clause_id']}` | {action_badge} | {rec['citation']} | {sev_badge} | {clean_new} |"
            )

        lines.append("")
        return "\n".join(lines)
