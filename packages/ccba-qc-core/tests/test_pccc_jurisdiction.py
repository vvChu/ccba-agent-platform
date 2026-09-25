"""Unit tests for PCCC Deterministic Jurisdiction Router (ADR-0035 & ADR-0059)."""

from __future__ import annotations

import pytest

from ccba_qc_core.jurisdiction import (
    PROVENANCE_SHA256_ND105_2025,
    PcccJurisdictionResult,
    PcccJurisdictionRouter,
    PcccProjectSpec,
    PcccProjectType,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_high_rise_condominium_dual_pathway_c07_and_bxd() -> None:
    """Case 1: 35-floor high-rise condominium (120m, 3 basements, Nhom A).

    Expectations:
    - Annex III item 1 (floors >= 7).
    - CQCMVXD: BO_XAY_DUNG (height >= 75m, floors >= 25, Nhom A).
    - Police: C07 (height >= 100m, floors >= 30, basements >= 3).
    - Investor self-appraisal: False (both state pathways active).
    """
    spec = PcccProjectSpec(
        project_type=PcccProjectType.CHUNG_CU,
        height_m=120.0,
        floors=35,
        basement_floors=3,
        floor_area_m2=45000.0,
        volume_m3=150000.0,
        investment_tier="NHOM_A",
    )
    res = PcccJurisdictionRouter.evaluate(spec)

    assert res.is_annex_iii is True
    assert res.annex_iii_item == 1
    assert res.cqcmvxd_required is True
    assert res.cqcmvxd_tier == "BO_XAY_DUNG"
    assert res.cqcmvxd_scope == ["a", "b", "c", "d", "dd"]

    assert res.police_required is True
    assert res.police_tier == "C07"
    assert res.police_scope == ["e", "g"]
    assert res.police_forms == ["PC12", "PC14"]

    assert res.investor_self_appraisal is False
    assert res.provenance_hash == PROVENANCE_SHA256_ND105_2025
    assert any("Luật Phòng cháy" in c for c in res.statutory_citations)
    assert any("Mục 1" in c for c in res.statutory_citations)


def test_medium_condominium_pc07_and_sxd() -> None:
    """Case 2: 9-floor residential building (28m, 1 basement, floor area 3,500 m2, Nhom B).

    Expectations:
    - Annex III item 1 (floors >= 7).
    - CQCMVXD: SO_XAY_DUNG.
    - Police: PC07.
    - Investor self-appraisal: False.
    """
    spec = PcccProjectSpec(
        project_type="Nhà chung cư cao tầng",
        height_m=28.0,
        floors=9,
        basement_floors=1,
        floor_area_m2=3500.0,
        investment_tier="NHOM_B",
    )
    res = PcccJurisdictionRouter.evaluate(spec)

    assert res.is_annex_iii is True
    assert res.annex_iii_item == 1
    assert res.police_required is True
    assert res.police_tier == "PC07"
    assert res.cqcmvxd_tier == "SO_XAY_DUNG"
    assert res.investor_self_appraisal is False


def test_small_apartment_outside_annex_iii_investor_self_appraisal() -> None:
    """Case 3: Small 4-floor collective apartment (< 7 floors, area 1,800 m2, volume 6,000 m3).

    Expectations:
    - Annex III: False.
    - Police: NONE (police_required=False).
    - Investor self-appraisal: True (Form PC13 under Dieu 8 ND 105/2025).
    """
    spec = PcccProjectSpec(
        project_type=PcccProjectType.CHUNG_CU,
        height_m=14.0,
        floors=4,
        basement_floors=0,
        floor_area_m2=1800.0,
        volume_m3=6000.0,
        investment_tier="NHOM_C",
    )
    res = PcccJurisdictionRouter.evaluate(spec)

    assert res.is_annex_iii is False
    assert res.annex_iii_item is None
    assert res.police_required is False
    assert res.police_tier == "NONE"
    assert res.investor_self_appraisal is True
    assert "PC13" in res.investor_forms


def test_kindergarten_thresholds() -> None:
    """Case 4: Preschool education boundary testing (Mục 2 Phụ lục III)."""
    # Over capacity (>= 150 children)
    spec_large = PcccProjectSpec(
        project_type="Trường mầm non tư thục",
        capacity_persons=160,
        floors=2,
        floor_area_m2=1200.0,
    )
    res_large = PcccJurisdictionRouter.evaluate(spec_large)
    assert res_large.is_annex_iii is True
    assert res_large.annex_iii_item == 2
    assert res_large.police_required is True

    # Under capacity (< 150 children, area < 2000m2, volume < 5000m3)
    spec_small = PcccProjectSpec(
        project_type=PcccProjectType.MAM_NON,
        capacity_persons=80,
        floors=2,
        floor_area_m2=800.0,
        volume_m3=2400.0,
    )
    res_small = PcccJurisdictionRouter.evaluate(spec_small)
    assert res_small.is_annex_iii is False
    assert res_small.investor_self_appraisal is True
    assert "PC13" in res_small.investor_forms


def test_hospital_medical_facility_thresholds() -> None:
    """Case 5: Hospital / Medical center boundary testing (Mục 3 Phụ lục III)."""
    # Hospital >= 5 floors or area >= 2000m2 or >= 50 beds
    spec_hosp = PcccProjectSpec(
        project_type="Bệnh viện đa khoa quốc tế",
        floors=6,
        floor_area_m2=8000.0,
        capacity_persons=200,  # 200 beds
    )
    res_hosp = PcccJurisdictionRouter.evaluate(spec_hosp)
    assert res_hosp.is_annex_iii is True
    assert res_hosp.annex_iii_item == 3
    assert res_hosp.police_required is True

    # Small clinic: 2 floors, 300 m2, 10 beds
    spec_clinic = PcccProjectSpec(
        project_type=PcccProjectType.BENH_VIEN_Y_TE,
        floors=2,
        floor_area_m2=300.0,
        volume_m3=1000.0,
        capacity_persons=10,
    )
    res_clinic = PcccJurisdictionRouter.evaluate(spec_clinic)
    assert res_clinic.is_annex_iii is False
    assert res_clinic.investor_self_appraisal is True


def test_hotel_and_office_thresholds() -> None:
    """Case 6: Hotel / Commercial office boundary testing (Mục 7 Phụ lục III)."""
    # Office >= 7 floors or area >= 3000 m2
    spec_office = PcccProjectSpec(
        project_type="Tòa nhà văn phòng CCBA Tower",
        floors=8,
        floor_area_m2=4000.0,
    )
    res_office = PcccJurisdictionRouter.evaluate(spec_office)
    assert res_office.is_annex_iii is True
    assert res_office.annex_iii_item == 7

    # Small boutique hotel 4 floors, 600 m2
    spec_hotel_small = PcccProjectSpec(
        project_type=PcccProjectType.KHACH_SAN_LUU_TRU,
        floors=4,
        floor_area_m2=600.0,
        volume_m3=2000.0,
    )
    res_hotel_small = PcccJurisdictionRouter.evaluate(spec_hotel_small)
    assert res_hotel_small.is_annex_iii is False
    assert res_hotel_small.investor_self_appraisal is True


def test_industrial_manufacturing_category_d_e() -> None:
    """Case 7: Industrial manufacturing category D, E (Mục 9 Phụ lục III).

    Threshold: Volume >= 30,000 m3 OR floor area >= 10,000 m2.
    """
    # Over volume threshold
    spec_ind_large = PcccProjectSpec(
        project_type=PcccProjectType.CONG_NGHIEP_D_E,
        floors=1,
        floor_area_m2=8000.0,
        volume_m3=36000.0,
    )
    res_ind_large = PcccJurisdictionRouter.evaluate(spec_ind_large)
    assert res_ind_large.is_annex_iii is True
    assert res_ind_large.annex_iii_item == 9

    # Below volume & area threshold
    spec_ind_small = PcccProjectSpec(
        project_type="Nhà xưởng sản xuất hạng D",
        floors=1,
        floor_area_m2=5000.0,
        volume_m3=22000.0,
    )
    res_ind_small = PcccJurisdictionRouter.evaluate(spec_ind_small)
    assert res_ind_small.is_annex_iii is False
    assert res_ind_small.investor_self_appraisal is True


def test_private_residential_dwelling() -> None:
    """Case 8: Single family individual house (3 floors, 250 m2).

    Expectations:
    - Not in Annex III.
    - CQCMVXD exempt (NONE).
    - Police exempt (NONE).
    - Investor self-appraisal: True (PC13).
    """
    spec_house = PcccProjectSpec(
        project_type=PcccProjectType.NHA_O_RIENG_LE,
        height_m=11.5,
        floors=3,
        floor_area_m2=250.0,
        volume_m3=800.0,
    )
    res_house = PcccJurisdictionRouter.evaluate(spec_house)

    assert res_house.is_annex_iii is False
    assert res_house.cqcmvxd_required is False
    assert res_house.cqcmvxd_tier == "NONE"
    assert res_house.police_required is False
    assert res_house.investor_self_appraisal is True
    assert "PC13" in res_house.investor_forms


def test_underground_multilevel_basement() -> None:
    """Case 9: Project with 2 or more basement floors (Mục 12 Phụ lục III)."""
    spec_underground = PcccProjectSpec(
        project_type=PcccProjectType.THUONG_MAI_DICH_VU,
        floors=3,
        basement_floors=2,
        floor_area_m2=2500.0,
    )
    res_ug = PcccJurisdictionRouter.evaluate(spec_underground)
    assert res_ug.is_annex_iii is True
    assert res_ug.annex_iii_item == 12
    assert res_ug.police_required is True


def test_serialization_and_summary() -> None:
    """Case 10: Serialization and summary text check."""
    spec = PcccProjectSpec(
        project_type=PcccProjectType.CHUNG_CU,
        height_m=50.0,
        floors=15,
        floor_area_m2=12000.0,
    )
    res = PcccJurisdictionRouter.evaluate(spec)
    assert isinstance(res, PcccJurisdictionResult)
    d = res.to_dict()

    assert isinstance(d, dict)
    assert d["is_annex_iii"] is True
    assert d["annex_iii_item"] == 1
    assert d["provenance_hash"] == PROVENANCE_SHA256_ND105_2025

    summary_text = res.summary()
    assert "PHÂN ĐỊNH THẨM QUYỀN THẨM ĐỊNH THIẾT KẾ PCCC" in summary_text
    assert "Mục 1" in summary_text


def test_string_enum_resolution() -> None:
    """Case 11: All canonical PcccProjectType string enum names resolve cleanly."""
    for member in PcccProjectType:
        spec = PcccProjectSpec(project_type=member.value)
        assert spec.get_canonical_type() == member


def test_pccc_jurisdiction_industrial_warehouse_category_d_e() -> None:
    """Case 12: Industrial warehouse category D/E threshold testing (Mục 10 Phụ lục III).

    Threshold for warehouse category D, E: Volume >= 30,000 m3 OR floor area >= 10,000 m2.
    """
    # Over threshold (12,000 m2, 108,000 m3) -> Annex III Item 10, PC07
    spec_large = PcccProjectSpec(
        project_type="Công trình Nhà kho chứa hàng hóa thông thường (hạng nguy hiểm cháy nổ D/E)",
        floors=1,
        floor_area_m2=12000.0,
        volume_m3=108000.0,
    )
    res_large = PcccJurisdictionRouter.evaluate(spec_large)
    assert res_large.is_annex_iii is True
    assert res_large.annex_iii_item == 10
    assert res_large.police_required is True
    assert res_large.police_tier == "PC07"
    assert any("Mục 10" in c for c in res_large.statutory_citations)

    # Below threshold for category D/E (5,000 m2, 20,000 m3) -> Outside Annex III
    spec_small = PcccProjectSpec(
        project_type="Nhà kho chứa hàng hạng D",
        floors=1,
        floor_area_m2=5000.0,
        volume_m3=20000.0,
    )
    res_small = PcccJurisdictionRouter.evaluate(spec_small)
    assert res_small.is_annex_iii is False
    assert res_small.annex_iii_item is None
    assert res_small.police_required is False
    assert res_small.investor_self_appraisal is True
    assert "PC13" in res_small.investor_forms
    assert any("Mẫu PC13" in c for c in res_small.statutory_citations)


def test_underground_structure_threshold() -> None:
    """Case 13: Specialized underground facility threshold (Mục 12 Phụ lục III).

    Threshold: Area >= 500 m2 OR Volume >= 1,000 m3 OR Basements >= 2.
    """
    # Small underground structure (50 m2, 150 m3, 1 level) -> Outside Annex III
    spec_small = PcccProjectSpec(
        project_type=PcccProjectType.CONG_TRINH_NGAM,
        floor_area_m2=50.0,
        volume_m3=150.0,
        basement_floors=1,
    )
    res_small = PcccJurisdictionRouter.evaluate(spec_small)
    assert res_small.is_annex_iii is False
    assert res_small.annex_iii_item is None

    # Large underground structure (600 m2, 1 level) -> Annex III Item 12
    spec_large = PcccProjectSpec(
        project_type=PcccProjectType.CONG_TRINH_NGAM,
        floor_area_m2=600.0,
        volume_m3=2000.0,
        basement_floors=1,
    )
    res_large = PcccJurisdictionRouter.evaluate(spec_large)
    assert res_large.is_annex_iii is True
    assert res_large.annex_iii_item == 12
    assert res_large.police_required is True


def test_fuzzy_normalization_edge_cases() -> None:
    """Case 14: Disambiguation of compound phrases and word boundaries."""
    # Restaurant Grade 1 must not match CONG_NGHIEP_C via 'hang c'
    assert _normalize_project_type_test("Nhà hàng cấp 1") == PcccProjectType.THUONG_MAI_DICH_VU

    # Children entertainment center must not match THUONG_MAI_DICH_VU via 'cho' in 'choi'
    assert _normalize_project_type_test("Khu vui chơi giải trí trẻ em") == PcccProjectType.VUI_CHOI_GIAI_TRI

    # Traditional market matches THUONG_MAI_DICH_VU via word boundary 'cho'
    assert _normalize_project_type_test("Chợ truyền thống") == PcccProjectType.THUONG_MAI_DICH_VU

    # Category D warehouse matches KHO_HANG_D_E
    assert _normalize_project_type_test("Nhà kho chứa hàng hạng D") == PcccProjectType.KHO_HANG_D_E


def _normalize_project_type_test(name: str) -> PcccProjectType:
    return PcccProjectSpec(project_type=name).get_canonical_type()

