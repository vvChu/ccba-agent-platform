# Copyright (c) 2026 CCBA. All rights reserved.
"""Canonical OpenXML DOM Pre-Sanitization Engine (ADR 0042).

Performs 100% in-memory structural normalization on DOCX archives using lxml:
- Purges revision markup (w:rsid*) and proofing/rendering noise (w:proofErr, w:smartTag, w:lastRenderedPageBreak).
- Consolidates adjacent fragmented runs (w:r) with identical formatting properties (w:rPr).
- Normalizes text to Unicode NFC and injects xml:space="preserve" on boundary whitespace.
- Strictly whitelists multimodal elements (w:object MathType OLE, m:oMath, w:drawing).
- Unwraps borderless layout tables into flat sequential paragraphs.
- Promotes structural headings (Chương, Mục, Điều, decimal sections) with standard w:pStyle.
"""

from __future__ import annotations

import io
import re
import unicodedata
import zipfile
from pathlib import Path
from typing import BinaryIO

from lxml import etree

# OpenXML Namespaces
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
XML_NS = "http://www.w3.org/XML/1998/namespace"
V_NS = "urn:schemas-microsoft-com:vml"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

NAMESPACES = {
    "w": W_NS,
    "m": M_NS,
    "xml": XML_NS,
    "v": V_NS,
    "wp": WP_NS,
    "a": A_NS,
    "r": R_NS,
}

# Qualified Tag Names
QN_W_P = f"{{{W_NS}}}p"
QN_W_R = f"{{{W_NS}}}r"
QN_W_T = f"{{{W_NS}}}t"
QN_W_RPR = f"{{{W_NS}}}rPr"
QN_W_PPR = f"{{{W_NS}}}pPr"
QN_W_PSTYLE = f"{{{W_NS}}}pStyle"
QN_W_VAL = f"{{{W_NS}}}val"
QN_W_B = f"{{{W_NS}}}b"
QN_W_BCS = f"{{{W_NS}}}bCs"
QN_W_TBL = f"{{{W_NS}}}tbl"
QN_W_TBLBORDERS = f"{{{W_NS}}}tblBorders"
QN_W_TR = f"{{{W_NS}}}tr"
QN_W_TC = f"{{{W_NS}}}tc"
QN_W_TAB = f"{{{W_NS}}}tab"
QN_W_BR = f"{{{W_NS}}}br"
QN_W_OBJECT = f"{{{W_NS}}}object"
QN_W_DRAWING = f"{{{W_NS}}}drawing"
QN_M_OMATH = f"{{{M_NS}}}oMath"
QN_M_OMATHPARA = f"{{{M_NS}}}oMathPara"
QN_XML_SPACE = f"{{{XML_NS}}}space"

# Layout keywords for borderless table detection
LAYOUT_KEYWORDS = [
    "cộng hòa xã hội chủ nghĩa",
    "độc lập - tự do",
    "nơi nhận:",
    "tm. chính phủ",
    "kt. thủ tướng",
    "phó thủ tướng",
    "bộ trưởng",
    "chủ tịch ủy ban",
    "ký, ghi rõ họ tên",
    "ký, đóng dấu",
    "lưu: vt",
]

NORMATIVE_KEYWORDS = [
    "nguy cơ",
    "phân loại",
    "phụ lục",
    "quy định",
    "mã hiệu",
    "định mức",
    "công năng",
    "tải trọng",
    "chi phí",
    "áp lực",
    "lưu lượng",
    "khoảng cách",
    "nhiệt độ",
    "cường độ",
    "đơn vị",
    "đường kính",
    "loại ống",
    "bội số",
]


def _calculate_numeric_density(tbl: etree._Element) -> float:
    """Calculate ratio of cells containing numbers, mathematical formulas, or technical units."""
    cells = tbl.xpath(".//w:tc", namespaces=NAMESPACES)
    if not cells:
        return 0.0
    numeric_cells = 0
    numeric_pattern = re.compile(
        r"(?:^\s*[\+\-]?\d+(?:[\.,]\d+)?\s*$)|"
        r"(?:\d+\s*(?:%|m|cm|mm|km|kg|tấn|kN|MPa|daN|ha|°C|s|h|W|kW|kVA|V|A|dB)\b)|"
        r"(?:[\=\<\>\±\×\÷\≤\≥])"
    )
    for c in cells:
        text = "".join(c.itertext()).strip()
        has_math = bool(c.xpath(".//m:oMath | .//w:object", namespaces=NAMESPACES))
        if has_math or numeric_pattern.search(text):
            numeric_cells += 1
    return numeric_cells / len(cells)


def _is_simple_text_run(r: etree._Element) -> bool:
    """Check whether a run contains only rPr, t, or tab elements (no drawings, OLE objects, or math)."""
    for child in r:
        tag = child.tag
        if tag in (QN_W_OBJECT, QN_W_DRAWING, QN_M_OMATH, QN_M_OMATHPARA):
            return False
        if tag not in (QN_W_RPR, QN_W_T, QN_W_TAB):
            return False
    return True


def _rpr_canonical(r: etree._Element) -> str:
    """Compute canonical string representation of run properties for exact comparison."""
    rpr = r.find(QN_W_RPR)
    if rpr is None:
        return ""
    try:
        return str(etree.tostring(rpr, method="c14n").decode("utf-8"))
    except Exception:
        return str(etree.tostring(rpr).decode("utf-8"))


def _is_run_bold(r: etree._Element) -> bool:
    """Check whether a run has bold formatting."""
    rpr = r.find(QN_W_RPR)
    if rpr is None:
        return False
    b = rpr.find(QN_W_B)
    b_cs = rpr.find(QN_W_BCS)
    if b is not None and b.get(QN_W_VAL, "1") not in ("0", "false", "none"):
        return True
    if b_cs is not None and b_cs.get(QN_W_VAL, "1") not in ("0", "false", "none"):
        return True
    return False


def _is_paragraph_bold(p: etree._Element) -> bool:
    """Check whether the paragraph is predominantly bold."""
    ppr = p.find(QN_W_PPR)
    if ppr is not None:
        rpr = ppr.find(QN_W_RPR)
        if rpr is not None and rpr.find(QN_W_B) is not None:
            return True
    # Check text runs
    runs = p.findall(QN_W_R)
    if not runs:
        return False
    text_runs = [
        r for r in runs if r.find(QN_W_T) is not None and (r.find(QN_W_T).text or "").strip()
    ]
    if not text_runs:
        return False
    return all(_is_run_bold(r) for r in text_runs)


class DocxCanonicalSanitizer:
    """Canonical OpenXML DOM Pre-Sanitization Engine (ADR 0042)."""

    def sanitize(self, docx_input: Path | str | bytes | BinaryIO) -> io.BytesIO:
        """Sanitize OpenXML DOM of a DOCX document 100% in-memory.

        Args:
            docx_input: Path to file, raw bytes, or readable BinaryIO stream.

        Returns:
            io.BytesIO positioned at 0 containing the clean canonical DOCX archive.
        """
        in_buffer: io.BytesIO
        if isinstance(docx_input, (str, Path)):
            with open(docx_input, "rb") as f:
                in_buffer = io.BytesIO(f.read())
        elif isinstance(docx_input, bytes):
            in_buffer = io.BytesIO(docx_input)
        elif hasattr(docx_input, "read"):
            data = docx_input.read()
            in_buffer = io.BytesIO(data)
        else:
            raise TypeError(f"Unsupported docx_input type: {type(docx_input)}")

        out_buffer = io.BytesIO()
        with zipfile.ZipFile(in_buffer, "r") as in_zip:
            with zipfile.ZipFile(out_buffer, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
                for item in in_zip.infolist():
                    content = in_zip.read(item.filename)
                    if item.filename == "word/document.xml":
                        content = self._sanitize_document_xml(content)
                    out_zip.writestr(item, content)

        out_buffer.seek(0)
        return out_buffer

    def _sanitize_document_xml(self, xml_bytes: bytes) -> bytes:
        """Apply all 4 canonical sanitization passes to word/document.xml."""
        parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False)
        root = etree.fromstring(xml_bytes, parser=parser)

        self._purge_markup_and_consolidate_runs(root)
        self._unwrap_borderless_layout_tables(root)
        self._normalize_whitespace_and_tabs(root)
        self._promote_structural_headings(root)

        return bytes(
            etree.tostring(
                root,
                xml_declaration=True,
                encoding="utf-8",
                standalone="yes",
            )
        )

    def _purge_markup_and_consolidate_runs(self, root: etree._Element) -> None:
        """Pass 1: Purge revision/proof markup, strip w:rsid*, and consolidate identical runs."""
        # 1. Strip all w:rsid* attributes everywhere in the tree
        for el in root.iter():
            for attr in list(el.attrib.keys()):
                if "rsid" in attr.lower():
                    del el.attrib[attr]

        # 2. Remove proofErr and lastRenderedPageBreak tags
        for tag_name in ("proofErr", "lastRenderedPageBreak"):
            for el in root.xpath(f".//w:{tag_name}", namespaces=NAMESPACES):
                parent = el.getparent()
                if parent is not None:
                    parent.remove(el)

        # 3. Unwrap smartTag elements (preserve inner text/runs)
        for el in root.xpath(".//w:smartTag", namespaces=NAMESPACES):
            parent = el.getparent()
            if parent is not None:
                idx = parent.index(el)
                for child in list(el):
                    parent.insert(idx, child)
                    idx += 1
                parent.remove(el)

        # 4. Consolidate adjacent simple text runs with identical rPr
        for p in root.xpath(".//w:p", namespaces=NAMESPACES):
            self._consolidate_runs_in_paragraph(p)

    def _consolidate_runs_in_paragraph(self, p: etree._Element) -> None:
        """Consolidate adjacent simple text runs in a paragraph if their rPr matches."""
        children = list(p)
        i = 0
        while i < len(children) - 1:
            curr = children[i]
            nxt = children[i + 1]

            if (
                curr.tag == QN_W_R
                and nxt.tag == QN_W_R
                and _is_simple_text_run(curr)
                and _is_simple_text_run(nxt)
                and _rpr_canonical(curr) == _rpr_canonical(nxt)
            ):
                curr_t = curr.find(QN_W_T)
                nxt_t = nxt.find(QN_W_T)

                txt1 = curr_t.text if (curr_t is not None and curr_t.text) else ""
                txt2 = nxt_t.text if (nxt_t is not None and nxt_t.text) else ""

                combined_txt = unicodedata.normalize("NFC", txt1 + txt2)

                if curr_t is None:
                    curr_t = etree.SubElement(curr, QN_W_T)
                curr_t.text = combined_txt

                # Inject xml:space="preserve" if text has leading/trailing whitespace or tab
                if (
                    combined_txt.startswith(" ")
                    or combined_txt.endswith(" ")
                    or "\t" in combined_txt
                ):
                    curr_t.set(QN_XML_SPACE, "preserve")
                elif QN_XML_SPACE in curr_t.attrib:
                    del curr_t.attrib[QN_XML_SPACE]

                p.remove(nxt)
                children.pop(i + 1)
                # Keep i unchanged to allow chaining with subsequent runs
            else:
                # Normalize Unicode NFC and space preserve for single run
                if curr.tag == QN_W_R and _is_simple_text_run(curr):
                    curr_t = curr.find(QN_W_T)
                    if curr_t is not None and curr_t.text:
                        norm_t = unicodedata.normalize("NFC", curr_t.text)
                        curr_t.text = norm_t
                        if norm_t.startswith(" ") or norm_t.endswith(" ") or "\t" in norm_t:
                            curr_t.set(QN_XML_SPACE, "preserve")
                i += 1

        # Check last child
        if children and children[-1].tag == QN_W_R and _is_simple_text_run(children[-1]):
            last_t = children[-1].find(QN_W_T)
            if last_t is not None and last_t.text:
                norm_t = unicodedata.normalize("NFC", last_t.text)
                last_t.text = norm_t
                if norm_t.startswith(" ") or norm_t.endswith(" ") or "\t" in norm_t:
                    last_t.set(QN_XML_SPACE, "preserve")

    def _unwrap_borderless_layout_tables(self, root: etree._Element) -> None:
        """Pass 2: Detect borderless layout tables and unwrap into sequential paragraphs (Multi-Factor Scoring Engine)."""
        body = root.find(f".//{{{W_NS}}}body")
        body_children = list(body) if body is not None else list(root)
        total_elements = len(body_children)

        tables = root.xpath(".//w:tbl", namespaces=NAMESPACES)
        for tbl in tables:
            tbl_idx_in_body = 0
            try:
                tbl_idx_in_body = body_children.index(tbl)
            except ValueError:
                tbl_idx_in_body = 0

            if not self._is_layout_table(tbl, tbl_index=tbl_idx_in_body, total_elements=total_elements):
                continue

            parent = tbl.getparent()
            if parent is None:
                continue

            tbl_idx = parent.index(tbl)
            paras = tbl.xpath(".//w:p", namespaces=NAMESPACES)
            for p in paras:
                parent.insert(tbl_idx, p)
                tbl_idx += 1
            parent.remove(tbl)

    def _is_layout_table(
        self, tbl: etree._Element, tbl_index: int = 0, total_elements: int = 1
    ) -> bool:
        """Determine whether a table is an administrative layout or signature table (Multi-Factor Scoring Engine)."""
        rows = tbl.findall(f".//{QN_W_TR}")
        if not rows:
            return False

        max_cols = 0
        for r in rows:
            cells = r.findall(f"./{QN_W_TC}")
            max_cols = max(max_cols, len(cells))
        if max_cols > 3:
            return False

        tbl_text = "".join(tbl.itertext()).lower().strip()
        if not tbl_text:
            return True

        has_norm_kw = any(k in tbl_text for k in NORMATIVE_KEYWORDS)
        if has_norm_kw:
            return False

        # 1. Borderless check
        borders = tbl.xpath(".//w:tblBorders", namespaces=NAMESPACES)
        is_borderless = False
        if borders:
            border_children = list(borders[0])
            if border_children and all(
                b.get(QN_W_VAL) in ("none", "nil", "0") for b in border_children
            ):
                is_borderless = True

        # 2. Formula frame tables: borderless 1-2 rows, max 2 cols, with formula tag (e.g. '(1)', '(B.1)')
        if is_borderless and len(rows) <= 2 and max_cols == 2:
            cell_texts = [
                "".join(c.itertext()).strip() for r in rows for c in r.findall(f"./{QN_W_TC}")
            ]
            has_tag = any(re.match(r"^\(\d+[a-z]?\)$|^\([A-Z]\.\d+\)$", t) for t in cell_texts)
            if has_tag:
                return True

        # 3. Zero-Loss Guard: Numeric & Engineering unit density >= 30% -> ALWAYS a data table!
        num_density = _calculate_numeric_density(tbl)
        if num_density >= 0.30:
            return False

        # 4. Document Boundary Topology: Header (first 12%) or Signature (last 12%) allows rows <= 8
        relative_pos = tbl_index / max(1, total_elements)
        is_boundary_zone = (relative_pos <= 0.12) or (relative_pos >= 0.88)
        max_allowed_rows = 8 if is_boundary_zone else 3

        if len(rows) > max_allowed_rows:
            return False

        has_layout_kw = any(k in tbl_text for k in LAYOUT_KEYWORDS)

        # Administrative layout keyword in table
        if has_layout_kw:
            return True

        # Borderless in boundary zone with low numeric density (< 10%)
        if is_borderless and is_boundary_zone and num_density < 0.10:
            return True

        return False

    def _normalize_whitespace_and_tabs(self, root: etree._Element) -> None:
        """Pass 3: Normalize tabs and spaces, preserving normative bullet characters."""
        for p in root.xpath(".//w:p", namespaces=NAMESPACES):
            runs = p.findall(QN_W_R)
            for r in runs:
                # Normalize <w:tab/> inside simple runs into 4-space indent with xml:space="preserve"
                tabs = r.findall(QN_W_TAB)
                if tabs and _is_simple_text_run(r):
                    t = r.find(QN_W_T)
                    if t is None:
                        t = etree.SubElement(r, QN_W_T)
                        t.text = "    " * len(tabs)
                    else:
                        t.text = ("    " * len(tabs)) + (t.text or "")
                    t.set(QN_XML_SPACE, "preserve")
                    for tab_el in tabs:
                        r.remove(tab_el)

                t = r.find(QN_W_T)
                if t is not None and t.text:
                    text = t.text
                    # Ensure leading/trailing spaces are preserved
                    if text.startswith(" ") or text.endswith(" ") or "\t" in text:
                        t.set(QN_XML_SPACE, "preserve")

    def _promote_structural_headings(self, root: etree._Element) -> None:
        """Pass 4: Detect unstyled structural headings and promote to standard w:pStyle."""
        heading_patterns = [
            (re.compile(r"^(?:PHẦN|CHƯƠNG)\s+[IVXLCDM0-9]+", re.IGNORECASE), "Heading1"),
            (re.compile(r"^\d+\.\s+[A-ZÀ-Ỹ\s]{3,}", re.UNICODE), "Heading1"),
            (re.compile(r"^(?:MỤC|ĐIỀU)\s+[0-9]+", re.IGNORECASE), "Heading2"),
            (re.compile(r"^\d+\.\d+\s+[A-ZÀ-Ỹ]", re.UNICODE), "Heading2"),
            (re.compile(r"^\d+\.\d+\.\d+\s+[A-ZÀ-Ỹ]", re.UNICODE), "Heading3"),
        ]

        for p in root.xpath(".//w:p", namespaces=NAMESPACES):
            text = "".join(p.itertext()).strip()
            if not text:
                continue

            for pattern, target_style in heading_patterns:
                if pattern.match(text):
                    # Check if paragraph is bold
                    if _is_paragraph_bold(p) or pattern.pattern.startswith("^(?:PHẦN|CHƯƠNG|ĐIỀU)"):
                        ppr = p.find(QN_W_PPR)
                        if ppr is None:
                            ppr = etree.Element(QN_W_PPR)
                            p.insert(0, ppr)

                        pstyle = ppr.find(QN_W_PSTYLE)
                        curr_style = pstyle.get(QN_W_VAL, "") if pstyle is not None else ""
                        if not curr_style or curr_style.lower() in ("normal", "bodytext", "text"):
                            if pstyle is None:
                                pstyle = etree.SubElement(ppr, QN_W_PSTYLE)
                            pstyle.set(QN_W_VAL, target_style)
                    break
