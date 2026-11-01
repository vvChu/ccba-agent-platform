"""Unit tests for CCILF LexiconHarvester and taxonomy models (COND-11..18)."""

from pathlib import Path

import yaml

from ccba_legal.lexicon import (
    CanonicalTerm,
    LexiconHarvester,
    ProvenanceRecord,
    TermFacet,
    TermTemporal,
    compute_sha256,
)


def test_lexicon_models_serialization() -> None:
    """Verifies that CanonicalTerm entity serializes correctly with facets and provenance."""
    facet = TermFacet(
        domain="xay_dung",
        legal_basis="Điều 9 Luật Xây dựng 2025",
        verbatim_definition="Định nghĩa chủ đầu tư xây dựng",
        verbatim_sha256=compute_sha256("Định nghĩa chủ đầu tư xây dựng"),
    )
    term = CanonicalTerm(
        canonical_id="STAT-TEST-001",
        canonical_vi="Chủ đầu tư",
        domain="governance",
        is_faceted=True,
        facets={"xay_dung": facet},
        translations={"en": "Employer", "ja": "発注者"},
        vi_forbidden=["Người sử dụng lao động"],
        temporal=TermTemporal(status="active", effective_from="2026-07-01"),
        provenance=ProvenanceRecord(
            source_type="statutory",
            doc_id="luat_xay_dung_2025.md",
            verbatim_definition="Định nghĩa gốc",
            verbatim_sha256=compute_sha256("Định nghĩa gốc"),
        ),
    )

    data = term.to_dict()
    assert data["canonical_id"] == "STAT-TEST-001"
    assert data["canonical_vi"] == "Chủ đầu tư"
    assert data["is_faceted"] is True
    assert "xay_dung" in data["facets"]
    assert data["translations"]["ja"] == "発注者"
    assert "Người sử dụng lao động" in data["vi_forbidden"]
    assert data["provenance"]["verbatim_sha256"] == compute_sha256("Định nghĩa gốc")


def test_harvest_statutory_definition_line() -> None:
    """Tests parsing statutory definition clauses with SHA-256 verbatim hash."""
    harvester = LexiconHarvester()
    line = "15. Thẩm tra là việc tổ chức, cá nhân thực hiện kiểm tra, đánh giá đối với thiết kế."
    term = harvester._parse_definition_line(line, "luat_xay_dung_2025.md", "3", 84)

    assert term is not None
    assert term.canonical_vi == "Thẩm tra"
    assert term.provenance is not None
    assert term.provenance.clause_anchor == "dieu-3-khoan-15"
    assert term.provenance.line_anchor == 84
    assert term.provenance.verbatim_sha256 == compute_sha256(
        "việc tổ chức, cá nhân thực hiện kiểm tra, đánh giá đối với thiết kế."
    )


def test_seed_canonical_taxonomy_three_pillars() -> None:
    """Verifies that seed taxonomy compiles all 3 pillars and required metadata."""
    harvester = LexiconHarvester()
    taxonomy = harvester.build_seed_canonical_taxonomy()

    assert taxonomy["schema_version"] == "2.0.0"
    assert "COND-11..18" in taxonomy["governance_basis"]
    terms = taxonomy["terms"]

    # Pillar I: Core Statutory Terms
    assert "chu_dau_tu" in terms
    assert terms["chu_dau_tu"]["is_faceted"] is True
    assert "xay_dung" in terms["chu_dau_tu"]["facets"]
    assert "dau_thau" in terms["chu_dau_tu"]["facets"]
    assert "dat_dai" in terms["chu_dau_tu"]["facets"]
    assert "tham_tra" in terms
    assert "tham_dinh_thiet_ke_pccc" in terms
    assert "chieu_cao_pccc" in terms

    # Pillar II: International & BIM Terms
    assert "concept_design" in terms
    assert terms["concept_design"]["canonical_vi"] == "Thiết kế ý tưởng"
    assert "Thiết kế khái niệm" in terms["concept_design"]["vi_forbidden"]
    assert terms["concept_design"]["translations"]["ja"] == "構想設計 / 企画設計"
    assert "as_built_drawings" in terms
    assert "iso19650_capability" in terms
    assert "iso19650_capacity" in terms

    # Pillar III: Internal Governance Terms
    assert "brand_institute" in terms
    assert "brand_center" in terms
    assert "brand_dispatch_header" in terms
    assert terms["brand_dispatch_header"]["canonical_vi"] == "IBST - CCBA"
    assert "IBST / CCBA" in terms["brand_dispatch_header"]["vi_forbidden"]
    assert "qc_gate_5_levels" in terms


def test_save_canonical_taxonomy_yaml(tmp_path: Path) -> None:
    """Tests saving taxonomy to a valid YAML file and round-tripping."""
    harvester = LexiconHarvester()
    out_file = tmp_path / "test_taxonomy.yaml"
    saved_path = harvester.save_canonical_taxonomy_yaml(output_path=out_file)

    assert saved_path.exists()
    content = saved_path.read_text(encoding="utf-8")
    loaded = yaml.safe_load(content)

    assert loaded["schema_version"] == "2.0.0"
    assert "chu_dau_tu" in loaded["terms"]
    assert loaded["terms"]["chu_dau_tu"]["canonical_vi"] == "Chủ đầu tư"
    assert "vai_tro_chu_tri_08" in loaded["terms"]
    assert (
        loaded["terms"]["vai_tro_chu_tri_08"]["canonical_vi"]
        == "Giám sát trưởng của đơn vị giám sát"
    )
    assert "Giám đốc quản lý dự án" in loaded["terms"]["vai_tro_chu_tri_08"]["legacy_aliases"]
    assert "quy_hoach_chi_tiet_rut_gon" in loaded["terms"]
    assert "dia_gioi_hanh_chinh_2_cap" in loaded["terms"]


def test_harvest_data_dictionary_csv_sanitization_and_polysemy(tmp_path: Path) -> None:
    """Verifies 1812/QĐ-BXD 2D CSV harvesting, camelCase cleanup (COND-02), and polysemy facets."""
    csv_file = tmp_path / "bang_01.csv"
    csv_content = (
        "TT — I,Tên trường kỹ thuật,Tên nghiệp vụ,Định nghĩa,Ví dụ,Căn cứ,Đặc tả,Ghi chú\n"
        "1,maThongTinQH,Mã định danh quy hoạch,Gồm 12 ký tự số,012611088888,NĐ 212/2026,String- 12,\n"
        "4,capDoQuyHoach,Cấp độ quy hoạch,Cấp độ quy hoạch,1,TT 39/2026,Object,Danh mục: 1- Quy hoạch chung 2- Quy hoạch phân khu 3- Quy hoạch chi tiết 4- Quy hoạch chi tiết được lập theo quy trình rút gọn (quy hoạch tổng mặt bằng)\n"
        "9,coQuanTCLapN VQH,Cơ quan tổ chức lập nhiệm vụ quy hoạch,Cơ quan lập NVQH,,TT 39/2026,,\n"
        "11,Cơ quan thẩm định quy hoạch,Cơ quan thẩm định quy hoạch,,,TT 39/2026,,\n"
        "11.1,tenCoQuanTham DinhQH,Tên tổ chức thẩm định quy hoạch,Tên cơ quan,SXD,TT 39/2026,String - 150,\n"
        "A,Dự án đầu tư xây dựng,Dự án đầu tư xây dựng,,,,,\n"
        "2,maThongTin,Mã định danh dự án,Gồm 13 ký tự số,0125215364201,NĐ 212/2026,String - 13,\n"
        "B,Công trình thuộc dự án,Công trình thuộc dự án,,,,,\n"
        "2,maThongTin,Mã định danh công trình xây dựng,Gồm 15 ký tự số,0125215364201,NĐ 212/2026,String - 15,\n"
    )
    csv_file.write_text(csv_content, encoding="utf-8")

    harvester = LexiconHarvester()
    terms = harvester.harvest_data_dictionary_csv(csv_path=csv_file)
    by_code = {t.schema_spec.technical_code: t for t in terms if t.schema_spec is not None}

    # COND-02: Sanitized camelCase + preserved raw_technical_code
    assert "coQuanTCLapNVQH" in by_code
    assert by_code["coQuanTCLapNVQH"].schema_spec is not None
    assert by_code["coQuanTCLapNVQH"].schema_spec.raw_technical_code == "coQuanTCLapN VQH"

    # Parent group inheritance
    assert "tenCoQuanThamDinhQH" in by_code
    assert by_code["tenCoQuanThamDinhQH"].schema_spec is not None
    assert by_code["tenCoQuanThamDinhQH"].schema_spec.parent_group == "Cơ quan thẩm định quy hoạch"

    # Enum extraction
    assert "capDoQuyHoach" in by_code
    assert (
        by_code["capDoQuyHoach"]
        .enum_values["4"]
        .startswith("Quy hoạch chi tiết được lập theo quy trình rút gọn")
    )

    # Polysemous key facet merging across II_A_DA and II_B_CT_TD
    assert "maThongTin" in by_code
    poly_term = by_code["maThongTin"]
    assert poly_term.is_faceted is True
    assert "II_A_DA" in poly_term.facets
    assert "II_B_CT_TD" in poly_term.facets


def test_two_pass_density_enum_extraction_and_false_positive_rejection(tmp_path: Path) -> None:
    """Verifies Two-Pass Density Parser for A/B/C, uppercase, Roman, colon/semicolon enums and false-positive rejection."""
    csv_file = tmp_path / "bang_01_enums.csv"
    csv_content = (
        "TT — I,Tên trường kỹ thuật,Tên nghiệp vụ,Định nghĩa,Ví dụ,Căn cứ,Đặc tả,Ghi chú\n"
        "A,Dự án đầu tư xây dựng,Dự án đầu tư xây dựng,,,,,\n"
        "4,nhomDuAn,Nhóm dự án,Chọn trong các nhóm dự án,A,TT 39/2026,Object,"
        "Danh mục: A- Nhóm A B- Nhóm B C- Nhóm C\n"
        "12,nguonVonDauTu,Nguồn vốn đầu tư,Nguồn vốn,VONDAUTUCONG,Luật XD,Object,"
        "Danh mục: VONDAUTUCONG - Vốn đầu tư công VONNHANUOC - Vốn nhà nước ngoài đầu tư công PPP - Dự án PPP KHAC - Vốn khác HONHOP - Vốn hỗn hợp\n"
        "15,trangThai,Trạng thái công khai,Trạng thái,1,NĐ 212/2026,Integer,0: Không công khai 1: Công khai\n"
        "C,Công trình cấp GPXD,Công trình cấp GPXD,,,,,\n"
        "5,capCongTrinh,Cấp công trình,Cấp công trình,I,TT 06/2021,Object,"
        "Danh mục cấp công trình: DACBIET - Đặc biệt I - Cấp I II - Cấp II III - Cấp III IV - Cấp IV\n"
        "11,vaiTroChuTri,Vai trò chủ trì,Vai trò,8,TT 39/2026,Object,"
        "1- Chủ nhiệm lập quy hoạch; 8- Giám sát trưởng của đơn vị giám sát; 9- Chỉ huy trưởng của nhà thầu thi công xây dựng công trình\n"
        "30,ngayPheDuyet,Ngày phê duyệt,Ngày ký,2026-10-21,NĐ 175/2024,Date,Ghi chú ngày 2026-10-21 hoặc String - 500\n"
    )
    csv_file.write_text(csv_content, encoding="utf-8")

    harvester = LexiconHarvester()
    terms = harvester.harvest_data_dictionary_csv(csv_path=csv_file)
    by_code = {t.schema_spec.technical_code: t for t in terms if t.schema_spec is not None}

    assert by_code["nhomDuAn"].enum_values == {"A": "Nhóm A", "B": "Nhóm B", "C": "Nhóm C"}
    assert by_code["nguonVonDauTu"].enum_values["VONDAUTUCONG"] == "Vốn đầu tư công"
    assert by_code["nguonVonDauTu"].enum_values["VONNHANUOC"] == "Vốn nhà nước ngoài đầu tư công"
    assert by_code["capCongTrinh"].enum_values["DACBIET"] == "Đặc biệt"
    assert by_code["capCongTrinh"].enum_values["IV"] == "Cấp IV"
    assert by_code["trangThai"].enum_values == {"0": "Không công khai", "1": "Công khai"}
    assert by_code["vaiTroChuTri"].enum_values["8"] == "Giám sát trưởng của đơn vị giám sát"
    assert by_code["ngayPheDuyet"].enum_values == {}

    taxonomy = harvester.build_seed_canonical_taxonomy()["terms"]
    assert (
        taxonomy["nguon_von_dau_tu_1812"]["enum_values"]["VONNHANUOC"]
        == "Vốn nhà nước ngoài đầu tư công"
    )
    assert taxonomy["cap_cong_trinh_1812"]["enum_values"]["DACBIET"] == "Cấp đặc biệt"
    proc_term = taxonomy["kich_ban_thu_tuc_cong_trinh_1812"]
    assert (
        proc_term["enum_values"]["II_D_CT_GPXD"]
        == "Công trình xây dựng không yêu cầu lập dự án đầu tư xây dựng, chỉ yêu cầu cấp giấy phép xây dựng"
    )
    assert "II_D_CT_KTKT" in proc_term["legacy_aliases"]
