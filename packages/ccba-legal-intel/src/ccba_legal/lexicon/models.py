"""Data models for CCBA Canonical Construction & Internal Lexicon Framework (CCILF).

Defines Faceted Super-Entity schemas, temporal validity, and cryptographic provenance
tracking as required by ADR-0059, ADR-0061, and COND-11 to COND-18.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProvenanceRecord(BaseModel):
    """Cryptographic provenance record anchoring term to legal gazette source."""

    source_type: str = Field(
        ...,
        description="Source type: statutory, international_fidic, iso_bim, or internal_governance",
    )
    doc_id: str = Field(..., description="Document identifier or filename")
    clause_anchor: str | None = Field(default=None, description="HTML / Markdown clause anchor tag")
    line_anchor: int | None = Field(default=None, description="Line number anchor in markdown file")
    verbatim_definition: str | None = Field(
        default=None, description="Original verbatim statutory definition"
    )
    verbatim_sha256: str | None = Field(
        default=None, description="SHA-256 cryptographic hash of verbatim definition"
    )


class TermTemporal(BaseModel):
    """Temporal validity and historical grandfathering metadata."""

    effective_from: str | None = Field(
        default=None, description="Effective start date (YYYY-MM-DD)"
    )
    superseded_by: str | None = Field(
        default=None, description="Term ID or legal basis superseding this definition"
    )
    status: str = Field(default="active", description="Status: active, superseded, or legacy")
    grandfathering_legacy_term: str | None = Field(
        default=None, description="Legacy grandfathering term used for historical projects"
    )


class DataDictionarySpec(BaseModel):
    """Technical schema binding and closed-world enum contract from 1812/QĐ-BXD (COND-02)."""

    section_namespace: str = Field(
        ...,
        description="Section namespace (e.g. I_QH, II_A_DA, II_B_CT_TD, II_C_CT_GPXD, II_D_CT_GPXD, II_E_CCHN, II_G_NLTC, II_H_NLCN)",
    )
    stt: str = Field(..., description="Row ordinal or hierarchical number (e.g. '16', '16.1')")
    technical_code: str = Field(
        ..., description="Sanitized camelCase technical field key (whitespace stripped)"
    )
    raw_technical_code: str = Field(
        ..., description="Original verbatim cell value from gazette table for ADR-0059 provenance"
    )
    data_type_spec: str = Field(
        default="", description="Data type and length specification from 'Mô tả dữ liệu' column"
    )
    enum_values: dict[str, str] = Field(
        default_factory=dict,
        description="Closed-world enum code -> canonical Vietnamese label mapping",
    )
    example_value: str = Field(default="", description="Example value from 'Ví dụ' column")
    parent_group: str | None = Field(
        default=None, description="Parent object group name if nested under a grouping row"
    )
    is_parent_group: bool = Field(
        default=False, description="True if row is a parent object grouping header"
    )


class TermFacet(BaseModel):
    """Facet representing domain-specific statutory definition for polysemous terms."""

    domain: str = Field(..., description="Legal domain: xay_dung, dau_thau, dat_dai, nha_o")
    legal_basis: str = Field(..., description="Legal source reference (e.g. Điều 9 Luật XD 2025)")
    clause_anchor: str | None = Field(default=None, description="Anchor ID in source document")
    verbatim_definition: str | None = Field(
        default=None, description="Verbatim definition in this specific legal domain"
    )
    verbatim_sha256: str | None = Field(
        default=None, description="SHA-256 hash of verbatim definition"
    )
    effective_from: str | None = Field(default=None, description="Effective date in this domain")
    key_distinction: str | None = Field(
        default=None, description="Core legal distinction distinguishing this facet"
    )
    schema_spec: DataDictionarySpec | None = Field(
        default=None, description="Technical data dictionary schema specification (1812/QĐ-BXD)"
    )
    enum_values: dict[str, str] = Field(
        default_factory=dict, description="Closed-world enum mapping if applicable"
    )


class CanonicalTerm(BaseModel):
    """Canonical term entity supporting multilingual translations and faceted resolution."""

    canonical_id: str = Field(..., description="Unique canonical term ID (e.g. STAT-001)")
    canonical_vi: str = Field(..., description="Official canonical Vietnamese terminology")
    domain: str = Field(..., description="Primary domain of the term")
    is_faceted: bool = Field(
        default=False, description="True if term has cross-cutting multi-law facets"
    )
    facets: dict[str, TermFacet] = Field(
        default_factory=dict, description="Domain facets for disambiguation"
    )
    translations: dict[str, str] = Field(
        default_factory=dict, description="Multilingual translations (en, ja, ko)"
    )
    vi_forbidden: list[str] = Field(
        default_factory=list, description="List of prohibited literal translations"
    )
    legacy_aliases: list[str] = Field(
        default_factory=list,
        description="Backward-compatible legacy aliases or deprecated slugs (ADR-0059)",
    )
    temporal: TermTemporal | None = Field(default=None, description="Temporal validity record")
    provenance: ProvenanceRecord | None = Field(
        default=None, description="Statutory provenance and SHA-256 stamp"
    )
    context_notes: str | None = Field(
        default=None, description="Engineering or consulting usage context notes"
    )
    schema_spec: DataDictionarySpec | None = Field(
        default=None, description="Technical data dictionary schema specification (1812/QĐ-BXD)"
    )
    enum_values: dict[str, str] = Field(
        default_factory=dict, description="Closed-world enum mapping if applicable"
    )

    def to_dict(self) -> dict[str, Any]:
        """Serializes entity to dictionary compatible with YAML taxonomy SSOT."""
        return self.model_dump(exclude_none=True)
