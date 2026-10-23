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
