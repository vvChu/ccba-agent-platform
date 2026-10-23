"""Unit tests for CCILF ImmutableSpanMasker and FacetedDisambiguationEngine (COND-15, COND-16, COND-17)."""

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from ccba_legal.lexicon import (
    FacetedDisambiguationEngine,
    ImmutableSpanMasker,
    compile_taxonomy_to_py,
    get_canonical_terms,
    load_canonical_taxonomy,
)


def test_immutable_span_masker_statutory_citations() -> None:
    """Tests that statutory citations and standards are preserved verbatim."""
    masker = ImmutableSpanMasker()
    text = (
        "Căn cứ Điều 2 Khoản 17 Luật PCCC 2024 và QCVN 06:2022/BXD, "
        "chủ đầu tư phải tiến hành thẩm định thiết kế."
    )
    masked_text, span_registry = masker.mask(text)

    assert "__CCBA_MASK_SPAN_0__" in masked_text
    assert "Điều 2 Khoản 17 Luật PCCC 2024" in span_registry.values()
    assert "QCVN 06:2022/BXD" in span_registry.values()

    # Restoration verification
    restored = masker.unmask(masked_text, span_registry)
    assert restored == text


def test_immutable_span_masker_quotes_and_code_blocks() -> None:
    """Tests masking of quotes, code blocks, and markdown links."""
    masker = ImmutableSpanMasker()
    text = (
        'Hồ sơ bao gồm "báo cáo thẩm tra thiết kế" và link [chi tiết](https://ccba.vn/doc/1) '
        "kèm đoạn mã `SELECT * FROM terms;`."
    )
    masked_text, span_registry = masker.mask(text)

    assert '"báo cáo thẩm tra thiết kế"' in span_registry.values()
    assert "`SELECT * FROM terms;`" in span_registry.values()
    assert "[chi tiết](https://ccba.vn/doc/1)" in span_registry.values()

    restored = masker.unmask(masked_text, span_registry)
    assert restored == text


def test_immutable_span_masker_brand_entities() -> None:
    """Tests that official brand names are protected from unwanted regex mutations."""
    masker = ImmutableSpanMasker()
    text = "Đơn vị tư vấn chủ trì là IBST - CCBA theo quy định IDOP-CCBA-WAY."
    masked_text, span_registry = masker.mask(text)

    assert "IBST - CCBA" in span_registry.values()
    assert "IDOP-CCBA-WAY" in span_registry.values()

    restored = masker.unmask(masked_text, span_registry)
    assert restored == text


def test_faceted_disambiguation_investor_domains() -> None:
    """Tests multi-law polysemy resolution for 'Chủ đầu tư' (COND-16)."""
    engine = FacetedDisambiguationEngine()

    # Construction context
    ctx_xd = "Chủ đầu tư phê duyệt thiết kế bản vẽ thi công và nghiệm thu công trình xây dựng."
    res_xd = engine.disambiguate_term("Chủ đầu tư", ctx_xd)
    assert res_xd is not None
    assert res_xd.domain == "xay_dung"
    assert res_xd.facet_id == "FACET-CHỦ-ĐẦU-TƯ-XD"
    assert "Luật Xây dựng 2014" in (res_xd.statutory_ref or "")

    # Procurement context
    ctx_dt = (
        "Bên mời thầu trình Chủ đầu tư phê duyệt hồ sơ mời thầu và kết quả đấu thầu gói thầu số 5."
    )
    res_dt = engine.disambiguate_term("Chủ đầu tư", ctx_dt)
    assert res_dt is not None
    assert res_dt.domain == "dau_thau"
    assert res_dt.facet_id == "FACET-CHỦ-ĐẦU-TƯ-ĐT"
    assert "Luật Đấu thầu 2023" in (res_dt.statutory_ref or "")

    # Land context
    ctx_dd = "Ủy ban nhân dân tỉnh giao đất, cho thuê đất và cấp sổ đỏ cho Chủ đầu tư để thực hiện dự án."
    res_dd = engine.disambiguate_term("Chủ đầu tư", ctx_dd)
    assert res_dd is not None
    assert res_dd.domain == "dat_dai"
    assert res_dd.facet_id == "FACET-CHỦ-ĐẦU-TƯ-ĐĐ"
    assert "Luật Đất đai 2024" in (res_dd.statutory_ref or "")

    # Housing context
    ctx_no = "Chủ đầu tư bàn giao căn hộ chung cư cho cư dân và nộp 2% kinh phí quỹ bảo trì nhà chung cư."
    res_no = engine.disambiguate_term("Chủ đầu tư", ctx_no)
    assert res_no is not None
    assert res_no.domain == "nha_o"
    assert res_no.facet_id == "FACET-CHỦ-ĐẦU-TƯ-NO"
    assert "Luật Nhà ở 2023" in (res_no.statutory_ref or "")


def test_faceted_disambiguation_pccc_appraisal_warning() -> None:
    """Tests grandfathering warning and mapping for 'thẩm duyệt PCCC' -> 'thẩm định thiết kế PCCC'."""
    engine = FacetedDisambiguationEngine()
    ctx = (
        "Hồ sơ xin thẩm duyệt thiết kế PCCC cho công trình cao 25 tầng đối với hạng mục thoát nạn."
    )
    res = engine.disambiguate_term("thẩm duyệt thiết kế PCCC", ctx)

    assert res is not None
    assert res.canonical_term == "Thẩm định thiết kế PCCC"
    assert res.statutory_ref == "Điều 2 Khoản 17 Luật PCCC 2024"
    assert res.warning is not None
    assert "Luật PCCC 2024" in res.warning


def test_faceted_disambiguation_height() -> None:
    """Tests disambiguation between H_PCCC (QCVN 06) and building height (QCVN 01)."""
    engine = FacetedDisambiguationEngine()

    # PCCC Height
    ctx_pccc = "Xác định chiều cao PCCC phục vụ bố trí xe thang và gian lánh nạn theo quy định."
    res_pccc = engine.disambiguate_term("chiều cao", ctx_pccc)
    assert res_pccc is not None
    assert "PCCC" in res_pccc.canonical_term
    assert "QCVN 06:2022" in (res_pccc.statutory_ref or "")

    # Building Height
    ctx_bldg = "Kiểm tra chiều cao công trình so với cốt quy hoạch và chỉ giới đường đỏ."
    res_bldg = engine.disambiguate_term("chiều cao", ctx_bldg)
    assert res_bldg is not None
    assert res_bldg.canonical_term == "Chiều cao công trình"
    assert "QCVN 01:2021" in (res_bldg.statutory_ref or "")


def test_taxonomy_loader_and_static_compilation() -> None:
    """Tests static Python generator and fallback loader (COND-17)."""
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mock_yaml = tmp_path / "test_tax.yaml"
        mock_py = tmp_path / "_test_gen.py"

        data = {
            "taxonomy_version": "2026.10.1-test",
            "statutory_definitions": [
                {
                    "canonical_id": "TEST-001",
                    "canonical_vi": "Chủ đầu tư",
                    "domain": "xay_dung",
                    "is_faceted": False,
                }
            ],
        }
        mock_yaml.write_text(yaml.safe_dump(data), encoding="utf-8")

        compiled_py = compile_taxonomy_to_py(yaml_path=mock_yaml, output_path=mock_py)
        assert compiled_py.is_file()
        assert "2026.10.1-test" in compiled_py.read_text(encoding="utf-8")

        # Test loader with mock YAML
        loaded = load_canonical_taxonomy(resource_path=mock_yaml)
        assert loaded.get("taxonomy_version") == "2026.10.1-test"

    # Test get_canonical_terms on production taxonomy
    terms = get_canonical_terms()
    assert len(terms) >= 3
    ids = {t.canonical_id for t in terms}
    assert "STAT-CDT-001" in ids
    assert "STAT-001" in ids
    assert "INT-GOV-001" in ids
