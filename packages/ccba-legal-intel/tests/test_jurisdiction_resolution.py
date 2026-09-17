from pathlib import Path

from ccba_legal import (
    expand_jurisdiction_queries,
    format_grounded_response,
    generate_jurisdiction_guardrail_card,
    get_active_delegation_document,
    normalize_jurisdiction,
    resolve_authority,
    validate_authority_naming,
    validate_tier_authority,
    verify_legal_grounding,
)


def test_normalize_jurisdiction():
    """Test normalization of regional names and abbreviations to ISO 3166-2:VN codes."""
    assert normalize_jurisdiction("Hà Nội") == "VN-HN"
    assert normalize_jurisdiction("TP. Hà Nội") == "VN-HN"
    assert normalize_jurisdiction("hà nội") == "VN-HN"
    assert normalize_jurisdiction("HN") == "VN-HN"
    assert normalize_jurisdiction("VN-HN") == "VN-HN"

    assert normalize_jurisdiction("Hồ Chí Minh") == "VN-HCM"
    assert normalize_jurisdiction("TP. Hồ Chí Minh") == "VN-HCM"
    assert normalize_jurisdiction("tphcm") == "VN-HCM"
    assert normalize_jurisdiction("VN-HCM") == "VN-HCM"

    assert normalize_jurisdiction("Đà Nẵng") == "VN-DN"
    assert normalize_jurisdiction("toàn quốc") == "VN"
    assert normalize_jurisdiction("TW") == "VN"
    assert normalize_jurisdiction(None) == "VN"


def test_resolve_authority_hanoi_merger():
    """Test resolution of merged/dissolved departments in Hanoi according to timeline."""
    # 1. Tra cứu Sở Quy hoạch - Kiến trúc sau ngày 10/08/2026 (đã sáp nhập)
    res_post_merger = resolve_authority(
        "Sở Quy hoạch - Kiến trúc TP. Hà Nội",
        jurisdiction="VN-HN",
        as_of_date="2026-09-01",
    )
    assert res_post_merger.current_authority == "Sở Xây dựng TP. Hà Nội"
    assert res_post_merger.is_deprecated is True
    assert res_post_merger.change_date == "2026-08-10"
    assert "HĐND TP. Hà Nội" in (res_post_merger.legal_basis or "")
    assert res_post_merger.warning is not None
    assert "sáp nhập" in res_post_merger.warning or "giải thể" in res_post_merger.warning

    # 2. Tra cứu trước ngày sáp nhập 10/08/2026 (thời điểm còn hiệu lực)
    res_pre_merger = resolve_authority(
        "Sở Quy hoạch - Kiến trúc TP. Hà Nội",
        jurisdiction="VN-HN",
        as_of_date="2025-01-01",
    )
    assert res_pre_merger.current_authority == "Sở Xây dựng TP. Hà Nội"
    assert res_pre_merger.is_deprecated is False

    # 3. Tra cứu Sở Giao thông vận tải đã hợp nhất từ 03/2025
    res_gtvt = resolve_authority(
        "Sở Giao thông vận tải",
        jurisdiction="VN-HN",
        as_of_date="2026-05-01",
    )
    assert res_gtvt.current_authority == "Sở Xây dựng TP. Hà Nội"
    assert res_gtvt.is_deprecated is True

    # 4. Tra cứu cơ quan đương nhiệm (Sở Xây dựng)
    res_current = resolve_authority(
        "Sở Xây dựng TP. Hà Nội",
        jurisdiction="VN-HN",
    )
    assert res_current.current_authority == "Sở Xây dựng TP. Hà Nội"
    assert res_current.is_deprecated is False
    assert res_current.warning is None


def test_validate_authority_naming_guardrail():
    """Test adversarial guardrail detecting dissolved agency names."""
    # Vi phạm: nhắc đến Sở Quy hoạch - Kiến trúc
    text_violation = (
        "Chủ đầu tư cần nộp hồ sơ xin chấp thuận tổng mặt bằng 1/500 lên "
        "Sở Quy hoạch - Kiến trúc TP. Hà Nội để thẩm định."
    )
    violations = validate_authority_naming(text_violation, jurisdiction="VN-HN")
    assert len(violations) >= 1
    v = violations[0]
    assert "Sở Quy hoạch - Kiến trúc" in v["found_entity"]
    assert v["replacement"] == "Sở Xây dựng TP. Hà Nội"
    assert "sáp nhập" in v["warning"].lower()

    # Hợp lệ: nhắc đến Sở Xây dựng TP. Hà Nội
    text_valid = (
        "Chủ đầu tư nộp hồ sơ xin chấp thuận tổng mặt bằng 1/500 lên "
        "Sở Xây dựng TP. Hà Nội để thực hiện theo cơ chế một cửa."
    )
    violations_clean = validate_authority_naming(text_valid, jurisdiction="VN-HN")
    assert len(violations_clean) == 0


def test_validate_tier_authority_guardrail():
    """Test adversarial guardrail detecting commune/ward authority boundary violations."""
    # Vi phạm: cho rằng UBND Phường có quyền phê duyệt quy hoạch tổng mặt bằng 1/500
    text_violation = (
        "UBND Phường Yên Hòa sẽ tiến hành thẩm định và phê duyệt quy hoạch tổng mặt bằng 1/500 "
        "cho công trình hỗn hợp."
    )
    violations = validate_tier_authority(text_violation, jurisdiction="VN-HN")
    assert len(violations) >= 1
    assert violations[0]["violation_type"] == "COMMUNE_AUTHORITY_EXCEEDED"
    assert "không có thẩm quyền" in violations[0]["warning"].lower()

    # Hợp lệ: UBND Phường chỉ lấy ý kiến cộng đồng dân cư
    text_valid = (
        "UBND Phường Yên Hòa chủ trì, phối hợp với chủ đầu tư tổ chức lấy ý kiến cộng đồng "
        "dân cư về đồ án quy hoạch tổng mặt bằng theo Điều 14 Quyết định 38/2026/QĐ-UBND."
    )
    violations_clean = validate_tier_authority(text_valid, jurisdiction="VN-HN")
    assert len(violations_clean) == 0


def test_expand_jurisdiction_queries():
    """Test query expansion with historical names and successors (Forward/Backward)."""
    # Mở rộng địa giới Hà Nội -> có Hà Tây
    queries_hn = expand_jurisdiction_queries(
        "quy hoạch xây dựng",
        jurisdiction="VN-HN",
    )
    assert any("Hà Tây" in q for q in queries_hn)

    # Mở rộng cơ quan đã giải thể -> có cơ quan kế thừa
    queries_agency = expand_jurisdiction_queries(
        "thủ tục xin thỏa thuận tại Sở Quy hoạch - Kiến trúc",
        jurisdiction="VN-HN",
    )
    assert any("Sở Xây dựng" in q for q in queries_agency)


def test_grounding_integration_blocks_hallucinations():
    """Test that verify_legal_grounding blocks authority naming and commune tier violations."""
    retrieved = [
        {"short_name": "QĐ 38/2026/QĐ-UBND", "document_number": "38/2026/QĐ-UBND", "id": "QD-38-2026", "territory": "VN-HN"}
    ]

    # 1. Có citation hợp lệ nhưng vi phạm danh xưng sở ngành giải thể -> Bị chặn
    response_with_dep_agency = (
        "Căn cứ quy định tại [QĐ 38/2026/QĐ-UBND], chủ đầu tư nộp hồ sơ tại "
        "Sở Quy hoạch - Kiến trúc TP. Hà Nội để thẩm định."
    )
    res1 = verify_legal_grounding(response_with_dep_agency, retrieved, jurisdiction="VN-HN")
    assert res1["is_grounded"] is False
    assert len(res1["authority_violations"]) > 0
    assert "Cảnh báo danh xưng cơ quan" in res1["warning_reason"]

    # 2. Có citation hợp lệ nhưng vi phạm thẩm quyền cấp phường -> Bị chặn
    response_with_commune_violation = (
        "Theo [QĐ 38/2026/QĐ-UBND], UBND Phường có thẩm quyền phê duyệt quy hoạch tổng mặt bằng 1/500."
    )
    res2 = verify_legal_grounding(response_with_commune_violation, retrieved, jurisdiction="VN-HN")
    assert res2["is_grounded"] is False
    assert len(res2["tier_violations"]) > 0
    assert "Cảnh báo thẩm quyền" in res2["warning_reason"]

    # 3. Chuẩn xác: trích dẫn đúng, dùng đúng Sở Xây dựng và đúng thẩm quyền -> Pass
    response_valid = (
        "Căn cứ [QĐ 38/2026/QĐ-UBND], Sở Xây dựng TP. Hà Nội là cơ quan đầu mối tiếp nhận và thẩm định "
        "đồ án quy hoạch tổng mặt bằng theo cơ chế một cửa."
    )
    res3 = verify_legal_grounding(response_valid, retrieved, jurisdiction="VN-HN")
    assert res3["is_grounded"] is True
    assert res3["warning_reason"] is None
    assert len(res3["valid_citations"]) == 1

    # Kiểm tra format_grounded_response gắn cảnh báo
    formatted = format_grounded_response(response_with_dep_agency, retrieved, jurisdiction="VN-HN")
    assert "⚠️ **[Cảnh báo danh xưng cơ quan:" in formatted


def test_dynamic_registry_discovery():
    """Test dynamic discovery of active delegation documents without hardcoding in YAML."""
    mock_reg_path = Path(__file__).parent / "fixtures" / "mock_registry.yaml"
    doc = get_active_delegation_document(territory="VN-HN", registry_path=mock_reg_path)
    assert doc is not None
    assert doc["document_number"] == "38/2026/QĐ-UBND"
    assert doc["territory"] == "VN-HN"
    assert doc["authority_type"] == "delegation"

    # Territory chưa đăng ký văn bản phân cấp -> Trả về None
    doc_none = get_active_delegation_document(territory="VN-TH", registry_path=mock_reg_path)
    assert doc_none is None


def test_national_fallback_and_disclaimer():
    """Test national fallback flag and disclaimer for ungrounded local jurisdictions."""
    retrieved = [
        {
            "short_name": "Luật Xây dựng 2024",
            "document_number": "55/2024/QH15",
            "id": "luat_55_2024",
            "territory": "VN",
        }
    ]
    response_text = (
        "Theo [Luật Xây dựng 2024], dự án phải thực hiện thẩm tra thiết kế theo quy chuẩn quốc gia."
    )
    res = verify_legal_grounding(response_text, retrieved, jurisdiction="VN-TH")
    assert res["is_grounded"] is True
    assert res["is_national_fallback"] is True

    formatted = format_grounded_response(response_text, retrieved, jurisdiction="VN-TH")
    assert "Lưu ý Lãnh thổ (National Fallback)" in formatted


def test_post_2025_district_abolition_guardrail():
    """Test detection of dissolved district-level authorities post-01/07/2025."""
    text_violation = (
        "Chủ đầu tư nộp hồ sơ xin cấp phép xây dựng công trình tại UBND Quận Cầu Giấy để được xem xét."
    )
    # Sau 01/07/2025: Vi phạm do cấp huyện đã giải thể
    violations_post = validate_authority_naming(
        text_violation, jurisdiction="VN-HN", as_of_date="2025-08-01"
    )
    assert len(violations_post) >= 1
    assert any(
        "cấp huyện" in v["warning"].lower() or "kết thúc hoạt động" in v["warning"].lower()
        for v in violations_post
    )

    # Trước 01/07/2025: Thời điểm cấp huyện còn hiệu lực -> Không vi phạm
    violations_pre = validate_authority_naming(
        text_violation, jurisdiction="VN-HN", as_of_date="2025-01-01"
    )
    assert len(violations_pre) == 0


def test_generate_jurisdiction_guardrail_card():
    """Test generation of dynamic guardrail markdown cards per territory."""
    mock_reg_path = Path(__file__).parent / "fixtures" / "mock_registry.yaml"

    # Thẻ Hà Nội
    card_hn = generate_jurisdiction_guardrail_card(
        jurisdiction="VN-HN", as_of_date="2026-09-01", registry_path=mock_reg_path
    )
    assert "VN-HN" in card_hn
    assert "mega_centralized" in card_hn
    assert "NQ 203/2025/QH15" in card_hn
    assert "Sở Quy hoạch - Kiến trúc" in card_hn
    assert "38/2026/QĐ-UBND" in card_hn

    # Thẻ TP.HCM
    card_hcm = generate_jurisdiction_guardrail_card(
        jurisdiction="VN-HCM", as_of_date="2026-09-01", registry_path=mock_reg_path
    )
    assert "VN-HCM" in card_hcm
    assert "mega_polycentric" in card_hcm

    # Thẻ Quốc gia (VN)
    card_vn = generate_jurisdiction_guardrail_card(jurisdiction="VN", as_of_date="2026-09-01")
    assert "VN" in card_vn

