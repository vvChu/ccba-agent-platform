# Copyright (c) 2026 CCBA. All rights reserved.
"""Comprehensive unit test suite for DocxCanonicalSanitizer (ADR 0042)."""

from __future__ import annotations

import io
import unicodedata
import zipfile

from lxml import etree

from ccba_legal.converters.docx_sanitizer import (
    NAMESPACES,
    QN_W_T,
    DocxCanonicalSanitizer,
)


def make_docx_bytes(document_xml_body: str) -> bytes:
    """Create a minimal valid DOCX archive in-memory with given body XML."""
    full_doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:v="urn:schemas-microsoft-com:vml" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">\n'
        f"<w:body>{document_xml_body}</w:body>\n"
        "</w:document>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            b'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            b'<Default Extension="xml" ContentType="application/xml"/>'
            b'<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            b"</Types>",
        )
        z.writestr(
            "_rels/.rels",
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            b"</Relationships>",
        )
        z.writestr("word/document.xml", full_doc_xml.encode("utf-8"))
    return buf.getvalue()


def get_sanitized_xml(sanitizer: DocxCanonicalSanitizer, docx_bytes: bytes) -> str:
    """Run sanitizer on in-memory docx bytes and return sanitized word/document.xml."""
    out_io = sanitizer.sanitize(docx_bytes)
    assert isinstance(out_io, io.BytesIO)
    with zipfile.ZipFile(out_io, "r") as z:
        return z.read("word/document.xml").decode("utf-8")


def test_purge_rsid_and_proof_err():
    """Verify that 100% of rsid attributes and proofErr elements are removed."""
    body = (
        '<w:p w:rsidR="001A2B3C" w:rsidRPr="004D5E6F" w:rsidP="00789ABC">'
        '  <w:proofErr w:type="spellStart"/>'
        '  <w:r w:rsidR="001A2B3C">'
        "    <w:t>Nội dung quy chuẩn</w:t>"
        "  </w:r>"
        '  <w:proofErr w:type="spellEnd"/>'
        "  <w:lastRenderedPageBreak/>"
        "</w:p>"
    )
    docx_bytes = make_docx_bytes(body)
    sanitizer = DocxCanonicalSanitizer()
    xml_out = get_sanitized_xml(sanitizer, docx_bytes)

    # Assert no rsid attributes remain
    assert "rsidR" not in xml_out
    assert "rsidRPr" not in xml_out
    assert "rsidP" not in xml_out
    assert "proofErr" not in xml_out
    assert "lastRenderedPageBreak" not in xml_out
    assert "Nội dung quy chuẩn" in xml_out


def test_run_consolidation_with_xml_space():
    """Verify merging 3 runs: 'Điều ', '1', ': Phạm vi' into single run with xml:space='preserve'."""
    body = (
        "<w:p>"
        "  <w:r>"
        "    <w:rPr><w:b/></w:rPr>"
        '    <w:t xml:space="preserve">Điều </w:t>'
        "  </w:r>"
        "  <w:r>"
        "    <w:rPr><w:b/></w:rPr>"
        "    <w:t>1</w:t>"
        "  </w:r>"
        "  <w:r>"
        "    <w:rPr><w:b/></w:rPr>"
        "    <w:t>: Phạm vi</w:t>"
        "  </w:r>"
        "</w:p>"
    )
    docx_bytes = make_docx_bytes(body)
    sanitizer = DocxCanonicalSanitizer()
    xml_out = get_sanitized_xml(sanitizer, docx_bytes)

    root = etree.fromstring(xml_out.encode("utf-8"))
    paras = root.xpath(".//w:p", namespaces=NAMESPACES)
    assert len(paras) == 1
    runs = paras[0].xpath("./w:r", namespaces=NAMESPACES)
    assert len(runs) == 1, f"Expected 1 consolidated run, got {len(runs)}"

    t_elem = runs[0].find(QN_W_T)
    assert t_elem is not None
    assert t_elem.text == "Điều 1: Phạm vi"


def test_unicode_nfc_normalization():
    """Verify converting decomposed Unicode (NFD) to precomposed (NFC) during consolidation."""
    # NFD: "Điều" with decomposed 'e' + combining circumflex + combining acute
    nfd_text = unicodedata.normalize("NFD", "Điều khoản áp dụng")
    assert unicodedata.is_normalized("NFD", nfd_text)
    assert not unicodedata.is_normalized("NFC", nfd_text)

    body = f"<w:p><w:r><w:t>{nfd_text}</w:t></w:r></w:p>"
    docx_bytes = make_docx_bytes(body)
    sanitizer = DocxCanonicalSanitizer()
    xml_out = get_sanitized_xml(sanitizer, docx_bytes)

    root = etree.fromstring(xml_out.encode("utf-8"))
    t_elem = root.xpath(".//w:t", namespaces=NAMESPACES)[0]
    assert unicodedata.is_normalized("NFC", t_elem.text)
    assert t_elem.text == "Điều khoản áp dụng"


def test_whitelist_protection_for_mathtype_and_drawings():
    """Verify strict whitelist protection: w:object and w:drawing are never altered or removed."""
    body = (
        "<w:p>"
        "  <w:r>"
        "    <w:t>Công thức tính:</w:t>"
        "  </w:r>"
        "  <w:r>"
        "    <w:object>"
        '      <v:shape id="_x0000_i1025"/>'
        "    </w:object>"
        "  </w:r>"
        "  <w:r>"
        "    <w:drawing>"
        '      <wp:inline><wp:extent cx="100" cy="100"/></wp:inline>'
        "    </w:drawing>"
        "  </w:r>"
        "</w:p>"
    )
    docx_bytes = make_docx_bytes(body)
    sanitizer = DocxCanonicalSanitizer()
    xml_out = get_sanitized_xml(sanitizer, docx_bytes)

    root = etree.fromstring(xml_out.encode("utf-8"))
    assert len(root.xpath(".//w:object", namespaces=NAMESPACES)) == 1
    assert len(root.xpath(".//w:drawing", namespaces=NAMESPACES)) == 1
    assert "Công thức tính:" in xml_out


def test_unwrap_borderless_layout_table():
    """Verify that a borderless administrative table is unwrapped into flat paragraphs."""
    body = (
        "<w:tbl>"
        "  <w:tblPr>"
        "    <w:tblBorders>"
        '      <w:top w:val="none"/>'
        '      <w:left w:val="none"/>'
        '      <w:bottom w:val="none"/>'
        '      <w:right w:val="none"/>'
        "    </w:tblBorders>"
        "  </w:tblPr>"
        "  <w:tr>"
        "    <w:tc>"
        "      <w:p><w:r><w:t>BỘ XÂY DỰNG</w:t></w:r></w:p>"
        "    </w:tc>"
        "    <w:tc>"
        "      <w:p><w:r><w:t>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</w:t></w:r></w:p>"
        "      <w:p><w:r><w:t>Độc lập - Tự do - Hạnh phúc</w:t></w:r></w:p>"
        "    </w:tc>"
        "  </w:tr>"
        "</w:tbl>"
    )
    docx_bytes = make_docx_bytes(body)
    sanitizer = DocxCanonicalSanitizer()
    xml_out = get_sanitized_xml(sanitizer, docx_bytes)

    root = etree.fromstring(xml_out.encode("utf-8"))
    # Table must be completely unwrapped (no w:tbl elements remain)
    assert len(root.xpath(".//w:tbl", namespaces=NAMESPACES)) == 0
    # All paragraphs from table must be preserved in body
    paras = root.xpath(".//w:p", namespaces=NAMESPACES)
    assert len(paras) == 3
    texts = ["".join(p.itertext()).strip() for p in paras]
    assert "BỘ XÂY DỰNG" in texts
    assert "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" in texts
    assert "Độc lập - Tự do - Hạnh phúc" in texts


def test_in_memory_zero_disk_roundtrip(tmp_path):
    """Confirm that the entire sanitization roundtrip happens in-memory with zero disk temporary files."""
    body = "<w:p><w:r><w:t>Kiểm tra in-memory</w:t></w:r></w:p>"
    docx_bytes = make_docx_bytes(body)
    input_io = io.BytesIO(docx_bytes)

    # Record disk state
    files_before = set(tmp_path.rglob("*"))

    sanitizer = DocxCanonicalSanitizer()
    out_io = sanitizer.sanitize(input_io)

    files_after = set(tmp_path.rglob("*"))
    assert files_before == files_after, "Temporary files were erroneously written to disk!"

    assert isinstance(out_io, io.BytesIO)
    assert out_io.tell() == 0
    # Ensure it can be read as a valid zip archive
    with zipfile.ZipFile(out_io, "r") as z:
        assert "word/document.xml" in z.namelist()


def test_promote_structural_headings():
    """Verify that unstyled bold paragraphs matching legal heading patterns get standard w:pStyle."""
    body = (
        "<w:p>"
        "  <w:r>"
        "    <w:rPr><w:b/></w:rPr>"
        "    <w:t>Điều 1. Phạm vi điều chỉnh</w:t>"
        "  </w:r>"
        "</w:p>"
        "<w:p>"
        "  <w:r>"
        "    <w:rPr><w:b/></w:rPr>"
        "    <w:t>1.1.2 Quy chuẩn này áp dụng</w:t>"
        "  </w:r>"
        "</w:p>"
    )
    docx_bytes = make_docx_bytes(body)
    sanitizer = DocxCanonicalSanitizer()
    xml_out = get_sanitized_xml(sanitizer, docx_bytes)

    root = etree.fromstring(xml_out.encode("utf-8"))
    paras = root.xpath(".//w:p", namespaces=NAMESPACES)
    pstyle_dieu = paras[0].xpath(".//w:pStyle/@w:val", namespaces=NAMESPACES)
    assert pstyle_dieu == ["Heading2"]

    pstyle_sub = paras[1].xpath(".//w:pStyle/@w:val", namespaces=NAMESPACES)
    assert pstyle_sub == ["Heading3"]


def test_unwrap_borderless_table_without_layout_keywords():
    """Verify that a borderless table with val='none' and NO administrative keywords is unwrapped."""
    body = (
        "<w:tbl>"
        "  <w:tblPr>"
        "    <w:tblBorders>"
        '      <w:top w:val="none"/>'
        '      <w:left w:val="none"/>'
        '      <w:bottom w:val="none"/>'
        '      <w:right w:val="none"/>'
        "    </w:tblBorders>"
        "  </w:tblPr>"
        "  <w:tr>"
        "    <w:tc>"
        "      <w:p><w:r><w:t>Công thức F = m * a</w:t></w:r></w:p>"
        "    </w:tc>"
        "    <w:tc>"
        "      <w:p><w:r><w:t>(1)</w:t></w:r></w:p>"
        "    </w:tc>"
        "  </w:tr>"
        "</w:tbl>"
    )
    docx_bytes = make_docx_bytes(body)
    sanitizer = DocxCanonicalSanitizer()
    xml_out = get_sanitized_xml(sanitizer, docx_bytes)

    root = etree.fromstring(xml_out.encode("utf-8"))
    assert len(root.xpath(".//w:tbl", namespaces=NAMESPACES)) == 0
    paras = root.xpath(".//w:p", namespaces=NAMESPACES)
    assert len(paras) == 2
    texts = ["".join(p.itertext()).strip() for p in paras]
    assert "Công thức F = m * a" in texts
    assert "(1)" in texts


def test_promote_top_level_section_heading():
    """Verify that top-level standard sections like '1. QUY ĐỊNH CHUNG' are promoted to Heading1."""
    body = "<w:p>  <w:r>    <w:rPr><w:b/></w:rPr>    <w:t>1. QUY ĐỊNH CHUNG</w:t>  </w:r></w:p>"
    docx_bytes = make_docx_bytes(body)
    sanitizer = DocxCanonicalSanitizer()
    xml_out = get_sanitized_xml(sanitizer, docx_bytes)

    root = etree.fromstring(xml_out.encode("utf-8"))
    paras = root.xpath(".//w:p", namespaces=NAMESPACES)
    pstyle = paras[0].xpath(".//w:pStyle/@w:val", namespaces=NAMESPACES)
    assert pstyle == ["Heading1"]


def test_normalize_tabs_into_spaces():
    """Verify that w:tab elements in simple text runs are converted into spaces with xml:space='preserve'."""
    body = "<w:p>  <w:r>    <w:tab/>    <w:t>- Nội dung quy định</w:t>  </w:r></w:p>"
    docx_bytes = make_docx_bytes(body)
    sanitizer = DocxCanonicalSanitizer()
    xml_out = get_sanitized_xml(sanitizer, docx_bytes)

    root = etree.fromstring(xml_out.encode("utf-8"))
    tabs = root.xpath(".//w:tab", namespaces=NAMESPACES)
    assert len(tabs) == 0, "All w:tab elements should be normalized into text spaces"
    t_nodes = root.xpath(".//w:t", namespaces=NAMESPACES)
    assert len(t_nodes) == 1
    assert t_nodes[0].text == "    - Nội dung quy định"
    assert t_nodes[0].attrib.get(f"{{{NAMESPACES['xml']}}}space") == "preserve"


def test_unwrap_multi_row_signature_table_in_boundary_zone():
    """Verify that a 5-row borderless signature table in the boundary zone is unwrapped (ADR 0042 Extension)."""
    dummy_paras = "".join(f"<w:p><w:r><w:t>Đoạn văn quy chuẩn {i}</w:t></w:r></w:p>" for i in range(15))
    sig_table = (
        "<w:tbl>"
        "  <w:tblPr>"
        "    <w:tblBorders>"
        '      <w:top w:val="none"/>'
        '      <w:left w:val="none"/>'
        '      <w:bottom w:val="none"/>'
        '      <w:right w:val="none"/>'
        "    </w:tblBorders>"
        "  </w:tblPr>"
        "  <w:tr><w:tc><w:p><w:r><w:t>Nơi nhận:</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>TM. CHÍNH PHỦ</w:t></w:r></w:p></w:tc></w:tr>"
        "  <w:tr><w:tc><w:p><w:r><w:t>- Như Điều 3;</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>THỦ TƯỚNG</w:t></w:r></w:p></w:tc></w:tr>"
        "  <w:tr><w:tc><w:p><w:r><w:t>- Ban Bí thư;</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>(Đã ký)</w:t></w:r></w:p></w:tc></w:tr>"
        "  <w:tr><w:tc><w:p><w:r><w:t>- Văn phòng TW;</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Ký, ghi rõ họ tên</w:t></w:r></w:p></w:tc></w:tr>"
        "  <w:tr><w:tc><w:p><w:r><w:t>Lưu: VT</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Phạm Minh Chính</w:t></w:r></w:p></w:tc></w:tr>"
        "</w:tbl>"
    )
    docx_bytes = make_docx_bytes(dummy_paras + sig_table)
    sanitizer = DocxCanonicalSanitizer()
    xml_out = get_sanitized_xml(sanitizer, docx_bytes)

    root = etree.fromstring(xml_out.encode("utf-8"))
    assert len(root.xpath(".//w:tbl", namespaces=NAMESPACES)) == 0
    paras = root.xpath(".//w:p", namespaces=NAMESPACES)
    texts = ["".join(p.itertext()).strip() for p in paras]
    assert "TM. CHÍNH PHỦ" in texts
    assert "Lưu: VT" in texts


def test_preserve_minimal_numeric_normative_table():
    """Verify that a 2-row borderless table with numeric density >= 30% is preserved (Zero-Loss Invariant)."""
    table = (
        "<w:tbl>"
        "  <w:tblPr>"
        "    <w:tblBorders>"
        '      <w:top w:val="none"/>'
        '      <w:left w:val="none"/>'
        '      <w:bottom w:val="none"/>'
        '      <w:right w:val="none"/>'
        "    </w:tblBorders>"
        "  </w:tblPr>"
        "  <w:tr>"
        "    <w:tc><w:p><w:r><w:t>Cấp công trình</w:t></w:r></w:p></w:tc>"
        "    <w:tc><w:p><w:r><w:t>Áp lực tiêu chuẩn (kN/m2)</w:t></w:r></w:p></w:tc>"
        "  </w:tr>"
        "  <w:tr>"
        "    <w:tc><w:p><w:r><w:t>Cấp I</w:t></w:r></w:p></w:tc>"
        "    <w:tc><w:p><w:r><w:t>1.25 kN/m2</w:t></w:r></w:p></w:tc>"
        "  </w:tr>"
        "</w:tbl>"
    )
    docx_bytes = make_docx_bytes(table)
    sanitizer = DocxCanonicalSanitizer()
    xml_out = get_sanitized_xml(sanitizer, docx_bytes)

    root = etree.fromstring(xml_out.encode("utf-8"))
    assert len(root.xpath(".//w:tbl", namespaces=NAMESPACES)) == 1
