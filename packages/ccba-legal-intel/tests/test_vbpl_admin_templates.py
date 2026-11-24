# Copyright (c) 2026 CCBA. All rights reserved.
"""Unit tests verifying vbpl_admin template extraction, natural sort, and legal basis graph."""

from __future__ import annotations

import io
import re
from pathlib import Path

import yaml
from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from ccba_legal.converters.archetype_scanner import DocumentArchetype, FullDocStructuralScanner
from ccba_legal.converters.unit_normalizer import normalize_docx_markdown
from ccba_legal.converters.vbpl_admin import (
    _build_pure_normative_body,
    _convert_docx_to_clean_markdown,
    _extract_and_export_templates,
    _generate_vbpl_frontmatter,
    _write_bundle_metadata_and_index,
    extract_legal_basis_graph,
)


def test_form_sort_key_alphanumeric():
    """Verify that form numbers with alphanumeric suffixes sort naturally without ValueError."""
    forms = ["02", "01b", "10a", "01a", "01"]

    def _form_sort_key(tag: str) -> tuple[int, str]:
        m = re.match(r"^(\d+)(.*)$", tag)
        if m:
            return (int(m.group(1)), m.group(2))
        return (999, tag)

    sorted_result = sorted(forms, key=_form_sort_key)
    assert sorted_result == ["01", "01a", "01b", "02", "10a"]


def test_extract_and_export_templates_alphanumeric(tmp_path: Path):
    """Verify that templates with alphanumeric form numbers (01a, 01b) export without crashing."""
    sample_md = """
# Điều 1. Phạm vi điều chỉnh
Nội dung điều khoản...

# __PHỤ LỤC I__ BIỂU MẪU QUẢN LÝ DỰ ÁN

# __Mẫu số 01a.__ Tờ trình thẩm định báo cáo nghiên cứu khả thi
Kính gửi: Cơ quan chuyên môn về xây dựng.

# __Mẫu số 01b.__ Tờ trình thẩm định thiết kế xây dựng triển khai sau thiết kế cơ sở
Kính gửi: Người quyết định đầu tư.
"""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    pure_body, created_templates = _extract_and_export_templates(
        sample_md, templates_dir, doc_num_str="15/2021/NĐ-CP"
    )

    assert "Điều 1" in pure_body
    assert "PHỤ LỤC I" not in pure_body
    assert len(created_templates) == 2
    # Verify both templates were created successfully
    filenames = [t.name for t in created_templates]
    assert any("01a" in fn for fn in filenames)
    assert any("01b" in fn for fn in filenames)


def test_extract_legal_basis_graph():
    """Verify that legal basis citations are parsed and mapped to canonical doc_ids."""
    sample_text = """
CĂN CỨ:
Căn cứ Luật Xây dựng số 50/2014/QH13;
Căn cứ Luật sửa đổi, bổ sung một số điều của Luật Xây dựng số 62/2020/QH14;
Căn cứ Nghị định số 15/2021/NĐ-CP ngày 03 tháng 3 năm 2021 của Chính phủ;
"""
    registry_lookup = {
        "50/2014/QH13": "luat_50_2014_qh13",
        "62/2020/QH14": "luat_62_2020_qh14",
        "15/2021/NĐ-CP": "nghi_dinh_15_2021_nd_cp",
    }
    graph = extract_legal_basis_graph(sample_text, registry_lookup)
    assert len(graph) >= 3
    doc_ids = [item["doc_id"] for item in graph]
    assert "luat_50_2014_qh13" in doc_ids
    assert "nghi_dinh_15_2021_nd_cp" in doc_ids


def test_vbpl_bundle_exports_backward_compatibility():
    """Verify that SSoT constants and both canonical and legacy functions are exported and identical."""
    from ccba_legal.constants import CURRENT_OKF_SPEC, CURRENT_OKF_VERSION
    from ccba_legal.converters.vbpl_admin import (
        process_vbpl_bundle,
        process_vbpl_bundle_okf_v22,
        process_vbpl_bundle_okf_v24,
    )

    assert CURRENT_OKF_VERSION == "2.4"
    assert "v2.4" in CURRENT_OKF_SPEC
    assert callable(process_vbpl_bundle)
    assert process_vbpl_bundle_okf_v24 is process_vbpl_bundle
    assert process_vbpl_bundle_okf_v22 is process_vbpl_bundle


def test_archetype_scanner_vbpl_admin_short_circular_and_cost_norm(tmp_path: Path):
    """Short administrative circulars with >=10 decimal sections stay VBPL_ADMIN unless norm codes >= 5."""
    docx_short = tmp_path / "tt_31.docx"
    doc = Document()
    doc.add_paragraph("Điều 1. Ban hành sửa đổi QCVN")
    doc.add_paragraph("Điều 2. Hiệu lực thi hành")
    for idx in range(1, 17):
        doc.add_paragraph(f"1.{idx} Quy định kỹ thuật mục {idx}")
    doc.save(str(docx_short))

    assert (
        FullDocStructuralScanner(docx_short, "31/2026/TT-BXD", "Thông tư").scan()
        == DocumentArchetype.VBPL_ADMIN
    )
    assert (
        FullDocStructuralScanner(docx_short, "14/VBHN-BGDĐT", "Văn bản hợp nhất").scan()
        == DocumentArchetype.VBPL_ADMIN
    )
    assert (
        FullDocStructuralScanner(docx_short, "QCVN 04:2021/BXD", "").scan()
        == DocumentArchetype.TECHNICAL_QCVN
    )

    docx_norm = tmp_path / "tt_dinh_muc.docx"
    norm_doc = Document()
    for idx in range(6):
        norm_doc.add_paragraph(f"Mã hiệu AA.1000{idx} công tác đào đất")
    norm_doc.save(str(docx_norm))
    assert (
        FullDocStructuralScanner(docx_norm, "12/2021/TT-BXD", "Thông tư").scan()
        == DocumentArchetype.CIRCULAR_COST_NORM
    )


def test_build_pure_normative_body_strips_orphan_noi_nhan_and_preserves_annex():
    """Forward signature matching removes orphan emphasis/Nơi nhận: and trailing WMF while keeping attached QCVN."""
    raw_decree = (
        "__Điều 1.__ Phạm vi điều chỉnh.\n\n"
        "__Điều 2.__ Thi hành Nghị định này.\n\n"
        "__  \n"
        "*Nơi nhận:  \n"
        "*__- Thủ tướng Chính phủ;\n- Lưu: VT.\n\n"
        "__TM. CHÍNH PHỦ__\n__Nguyễn Chí Dũng__\n\n"
        "__FILE ĐƯỢC ĐÍNH KÈM THEO VĂN BẢN__\n__![](data:image/x-wmf;base64,AAAA)__"
    )
    cleaned = _build_pure_normative_body(raw_decree)
    assert "Nơi nhận" not in cleaned
    assert "Nguyễn Chí Dũng" not in cleaned
    assert "FILE ĐƯỢC ĐÍNH KÈM" not in cleaned
    assert cleaned.rstrip().endswith("Thi hành Nghị định này.")

    raw_tt_qcvn = (
        "__Điều 1.__ Ban hành kèm theo Thông tư này Sửa đổi QCVN.\n\n"
        "__*  \nNơi nhận:  \n*__- Văn phòng Chính phủ;\n\n"
        "__KT. BỘ TRƯỞNG__\n\n"
        "SỬA ĐỔI 01:2026 QCVN 04:2021/BXD\n"
        "__1. QUY ĐỊNH CHUNG__\n__3.5__ Giám sát 24/24 giờ."
    )
    cleaned_qcvn = _build_pure_normative_body(raw_tt_qcvn)
    assert "QUY ĐỊNH CHUNG" in cleaned_qcvn
    assert "Giám sát 24/24 giờ." in cleaned_qcvn


def test_extract_legal_basis_graph_stops_at_body_and_preserves_dotted_numbers():
    """extract_legal_basis_graph stops at Chương I/Điều 1 and preserves decimal doc numbers like 66.18."""
    sample = (
        "*Căn cứ Nghị quyết số **66.18/2026/NQ-CP của Chính phủ quy định cắt giảm TTHC;*\n\n"
        "# __Chương I__\n"
        "## __Điều 1.__ Sửa đổi khoản 1\n"
        "“1. Căn cứ Nghị định số 99/2025/NĐ-CP và Thông báo kế hoạch, tổ chức gửi hồ sơ.”\n"
    )
    basis = extract_legal_basis_graph(sample, {"66.18/2026/NQ-CP": "nghi_quyet_66_18_2026_nq_cp"})
    assert len(basis) == 1
    assert basis[0]["doc_id"] == "nghi_quyet_66_18_2026_nq_cp"
    assert "66.18/2026/NQ-CP" in basis[0]["title"]


def test_metadata_and_frontmatter_no_yaml_aliases_and_infers_type(tmp_path: Path):
    """Metadata and frontmatter avoid &id001/*id001 YAML aliases and infer doc type from document_number."""
    shared_replaces = ["08/2014/NĐ-CP", "70/2018/NĐ-CP"]
    for slug, doc_num, expected_type in [
        ("thong_tu_20_2026_tt_bkhcn", "20/2026/TT-BKHCN", "Thông tư"),
        ("luat_93_2025_qh15", "93/2025/QH15", "Luật"),
        ("quyet_dinh_258_qd_ttg", "258/QĐ-TTg", "Quyết định"),
        ("14_vbhn_bgddt", "14/VBHN-BGDĐT", "Văn bản hợp nhất"),
    ]:
        bdir = tmp_path / slug
        bdir.mkdir(parents=True, exist_ok=True)
        doc_meta = {
            "id": slug,
            "document_number": doc_num,
            "type": "",
            "relations": {"replaces": shared_replaces},
            "replaces": shared_replaces,
        }
        _write_bundle_metadata_and_index(
            bundle_dir=bdir,
            target_md_name=f"{slug}.md",
            doc_meta=doc_meta,
            legal_basis=[],
            clauses_cnt=1,
            qa_cnt=0,
            templates_cnt=0,
            tables_cnt=0,
        )
        raw_meta = (bdir / "metadata.yaml").read_text(encoding="utf-8")
        assert "&id" not in raw_meta and "*id" not in raw_meta
        loaded = yaml.safe_load(raw_meta)
        assert loaded["type"] == expected_type

        fm = _generate_vbpl_frontmatter(doc_meta, bdir, f"{slug}.md")
        assert "&id" not in fm and "*id" not in fm
        assert f"document_type: {expected_type}" in fm


def test_normalize_docx_markdown_merges_split_bold_glue_and_preserves_blanks():
    """Bookmark anchors splitting bold/italic runs merge cleanly while form blanks stay intact."""
    assert (
        normalize_docx_markdown('__Sửa đổi __<a id="dieu_14"></a>__Điều 14\\. Quy định__')
        == "__Sửa đổi Điều 14. Quy định__"
    )
    assert (
        normalize_docx_markdown('__Sửa đổi __<a id="bm1"></a><a id="bm2"></a>__khoản 4__')
        == "__Sửa đổi khoản 4__"
    )
    assert (
        normalize_docx_markdown('__*Sửa đổi *__<a id="bm1"></a>__*khoản 4*__')
        == "__*Sửa đổi khoản 4*__"
    )
    assert normalize_docx_markdown('**Sửa đổi **<a id="s1"></a>**Điều 1**') == "**Sửa đổi Điều 1**"
    assert (
        normalize_docx_markdown('*Ghi chú *<a id="i1"></a>*quan trọng*') == "*Ghi chú quan trọng*"
    )
    assert normalize_docx_markdown('__Kh__<a id="_GoBack"></a>__oản 4__') == "__Khoản 4__"
    assert normalize_docx_markdown('<a id="d1"></a>__Điều 1__') == "__Điều 1__"
    assert (
        normalize_docx_markdown(r"Tên cơ quan: \_\_\_\_\_ [ghi tên cơ quan]")
        == "Tên cơ quan: _____ [ghi tên cơ quan]"
    )
    assert (
        normalize_docx_markdown("Tên cơ quan: _____ [ghi tên cơ quan]")
        == "Tên cơ quan: _____ [ghi tên cơ quan]"
    )


def test_convert_docx_to_clean_markdown_avoids_bold_glue_on_bookmarks():
    """End-to-end Mammoth DOCX conversion produces zero ____ bold-glue on split bold bookmarks."""
    w_ns = nsdecls("w")
    doc = Document()
    doc.element.body.append(
        parse_xml(
            f"""
            <w:p {w_ns}>
              <w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">Sửa đổi </w:t></w:r>
              <w:bookmarkStart w:id="0" w:name="dieu_14"/><w:bookmarkEnd w:id="0"/>
              <w:r><w:rPr><w:b/></w:rPr><w:t>Điều 14. Quy định</w:t></w:r>
            </w:p>
            """
        )
    )
    doc.element.body.append(
        parse_xml(
            f"""
            <w:p {w_ns}>
              <w:r><w:rPr><w:b/><w:i/></w:rPr><w:t xml:space="preserve">Sửa đổi </w:t></w:r>
              <w:bookmarkStart w:id="1" w:name="khoan_4"/><w:bookmarkEnd w:id="1"/>
              <w:r><w:rPr><w:b/><w:i/></w:rPr><w:t>khoản 4</w:t></w:r>
            </w:p>
            """
        )
    )
    doc.element.body.append(
        parse_xml(
            f"""
            <w:p {w_ns}>
              <w:r><w:t>Tên cơ quan: _____ [ghi tên cơ quan]</w:t></w:r>
            </w:p>
            """
        )
    )

    buf = io.BytesIO()
    doc.save(buf)
    cleaned = _convert_docx_to_clean_markdown(buf)

    assert "____Điều" not in cleaned
    assert "____khoản" not in cleaned
    assert "__Sửa đổi Điều 14. Quy định__" in cleaned
    assert "__*Sửa đổi khoản 4*__" in cleaned
    assert r"Tên cơ quan: _____ \[ghi tên cơ quan\]" in cleaned
