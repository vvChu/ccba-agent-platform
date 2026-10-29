"""Seam LexiconHarvester for CCBA Canonical Construction & Internal Lexicon Framework (CCILF).

Harvests statutory definitions from ccba-legal-knowledge, corporate taxonomies
from IDOP-CCBA-WAY, and compiles the Hub SSOT taxonomy (ADR-0059, ADR-0061, COND-11..18).
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.gold_standard import get_doc_profile
from ccba_legal.lexicon.models import (
    CanonicalTerm,
    DataDictionarySpec,
    ProvenanceRecord,
    TermFacet,
)

logger = logging.getLogger(__name__)

DEFAULT_RESOURCE_PATH = (
    Path(__file__).resolve().parent.parent / "resources" / "canonical_construction_taxonomy.yaml"
)

# Pattern recognizing Vietnamese statutory definition sentences:
# e.g., "1. Thẩm tra là việc..." or "1.* Bên mời thầu* là cơ quan..."
DEFINITION_PATTERN = re.compile(
    r"^\s*(?:\*{0,2}_*(\d+)[\.\*\_]{1,3}\*{0,2}_*)\s+\*?([^*:\n]+?)\*?\s+(?:là|được hiểu là|gồm|bao gồm)\s+(.+)$",
    re.IGNORECASE,
)

SECTION_NAMESPACE_MAP: dict[str, str] = {
    "I": "I_QH",
    "A": "II_A_DA",
    "B": "II_B_CT_TD",
    "C": "II_C_CT_GPXD",
    "D": "II_D_CT_KTKT",
    "E": "II_E_CCHN",
    "G": "II_G_NLTC",
    "H": "II_H_NLCN",
}

_ENUM_ITEM_PATTERN = re.compile(r"(\d+)\s*-\s*([^\d]+?)(?=\s+\d+\s*-|$)")


def compute_sha256(text: str) -> str:
    """Computes SHA-256 hash of verbatim definition text (ADR-0059)."""
    clean_text = text.strip()
    return hashlib.sha256(clean_text.encode("utf-8")).hexdigest()


def _detect_section_namespace(stt_cell: str, current_ns: str) -> tuple[str, bool]:
    """Detects section header transitions in 1812/QĐ-BXD data dictionary table."""
    token = stt_cell.strip().lstrip("\ufeff")
    if token in SECTION_NAMESPACE_MAP:
        return SECTION_NAMESPACE_MAP[token], True
    if token == "II":
        return "II_A_DA", True
    return current_ns, False


def _sanitize_technical_code(raw_cell: str, name_cell: str) -> tuple[str, str, bool]:
    """Sanitizes broken camelCase keys while preserving raw gazette text (COND-02)."""
    raw_clean = raw_cell.strip()
    name_clean = name_cell.strip()
    if not raw_clean or raw_clean == name_clean or not raw_clean.isascii():
        slug = re.sub(r"[^\w]+", "_", (raw_clean or name_clean).lower()).strip("_")
        return f"group_{slug}", raw_clean, True
    cleaned = re.sub(r"\s+", "", raw_clean)
    if cleaned and cleaned[0].isupper() and not cleaned.isupper():
        cleaned = cleaned[0].lower() + cleaned[1:]
    return cleaned, raw_clean, False


def _extract_enum_mapping(text_cell: str) -> dict[str, str]:
    """Extracts closed-world enum code->label pairs from Danh mục specification."""
    mapping: dict[str, str] = {}
    if not text_cell or "Danh mục" not in text_cell:
        return mapping
    body = text_cell.split("Danh mục", 1)[-1].lstrip(": ")
    for match in _ENUM_ITEM_PATTERN.finditer(body):
        code, label = match.group(1).strip(), match.group(2).strip().rstrip(".;,")
        if label:
            mapping[code] = label
    return mapping


def _build_row_term(
    row: list[str],
    section_ns: str,
    parent_group: str | None,
    doc_id: str,
) -> CanonicalTerm:
    """Builds a CanonicalTerm from a single 1812/QĐ-BXD CSV data row."""
    stt = row[0].strip()
    raw_tech = row[1].strip() if len(row) > 1 else ""
    biz_name = row[2].strip() if len(row) > 2 else raw_tech
    definition = row[3].strip() if len(row) > 3 else ""
    example = row[4].strip() if len(row) > 4 else ""
    data_spec = row[6].strip() if len(row) > 6 else ""
    notes_col = row[7].strip() if len(row) > 7 else ""

    tech_code, raw_preserved, is_group = _sanitize_technical_code(raw_tech, biz_name)
    enums = _extract_enum_mapping(notes_col or data_spec)
    verbatim_text = definition or biz_name
    spec = DataDictionarySpec(
        section_namespace=section_ns,
        stt=stt,
        technical_code=tech_code,
        raw_technical_code=raw_preserved,
        data_type_spec=data_spec,
        enum_values=enums,
        example_value=example,
        parent_group=parent_group,
        is_parent_group=is_group,
    )
    return CanonicalTerm(
        canonical_id=f"STAT-1812-{section_ns}-{stt.replace('.', '_')}",
        canonical_vi=biz_name,
        domain=f"data_dictionary.{section_ns.lower()}",
        context_notes=notes_col or None,
        schema_spec=spec,
        enum_values=enums,
        provenance=ProvenanceRecord(
            source_type="statutory",
            doc_id=doc_id,
            clause_anchor=f"{section_ns.lower()}-{stt.replace('.', '-')}",
            verbatim_definition=verbatim_text,
            verbatim_sha256=compute_sha256(verbatim_text),
        ),
    )


def _merge_polysemous_terms(raw_terms: list[CanonicalTerm]) -> list[CanonicalTerm]:
    """Merges rows sharing the same technical_code across sections into faceted terms."""
    by_code: dict[str, list[CanonicalTerm]] = {}
    for term in raw_terms:
        key = (
            term.schema_spec.technical_code
            if term.schema_spec and not term.schema_spec.is_parent_group
            else term.canonical_id
        )
        by_code.setdefault(key, []).append(term)

    merged: list[CanonicalTerm] = []
    for code, group in by_code.items():
        if len(group) == 1:
            merged.append(group[0])
            continue
        primary = group[0]
        facets: dict[str, TermFacet] = {}
        for item in group:
            spec = item.schema_spec
            ns = spec.section_namespace if spec else item.domain
            facet_key = ns if ns not in facets else f"{ns}_{spec.stt if spec else len(facets)}"
            facets[facet_key] = TermFacet(
                domain=ns.lower(),
                legal_basis="Quyết định 1812/QĐ-BXD",
                clause_anchor=item.provenance.clause_anchor if item.provenance else None,
                verbatim_definition=item.provenance.verbatim_definition
                if item.provenance
                else item.canonical_vi,
                verbatim_sha256=item.provenance.verbatim_sha256
                if item.provenance
                else compute_sha256(item.canonical_vi),
                key_distinction=f"{item.canonical_vi} ({spec.data_type_spec if spec else ''})",
                schema_spec=spec,
                enum_values=item.enum_values,
            )
        merged.append(
            primary.model_copy(
                update={
                    "canonical_id": f"STAT-1812-POLY-{code}",
                    "is_faceted": True,
                    "facets": facets,
                }
            )
        )
    return merged


class LexiconHarvester:
    """Harvester for statutory definitions and internal institutional taxonomies."""

    def __init__(
        self,
        legal_corpus_dir: Path | None = None,
        idop_taxonomy_dir: Path | None = None,
    ) -> None:
        """Initializes harvester with discoverable paths for Hub and Spokes."""
        self.legal_corpus_dir = legal_corpus_dir or self._discover_legal_corpus()
        self.idop_taxonomy_dir = idop_taxonomy_dir or self._discover_idop_taxonomy()
        self.vbpl_profile = get_doc_profile("vbpl")

    def _discover_legal_corpus(self) -> Path:
        """Discovers legal_docs directory path from env or workspace siblings."""
        env_path = os.getenv("CCBA_LEGAL_KNOWLEDGE_PATH")
        if env_path and Path(env_path).exists():
            return Path(env_path) / "legal_docs"

        # Check sibling directories in workspace
        cwd = Path.cwd().resolve()
        candidates = [
            cwd / "legal_docs",
            cwd.parent / "ccba-legal-knowledge" / "legal_docs",
            Path("/home/vvc/ccba/ccba-legal-knowledge/legal_docs"),
        ]
        for cand in candidates:
            if cand.exists():
                return cand
        return cwd / "legal_docs"

    def _discover_idop_taxonomy(self) -> Path:
        """Discovers IDOP-CCBA-WAY taxonomy directory path."""
        cwd = Path.cwd().resolve()
        candidates = [
            cwd.parent / "IDOP-CCBA-WAY" / "datamodel" / "sharepoint" / "taxonomy",
            Path("/home/vvc/ccba/IDOP-CCBA-WAY/datamodel/sharepoint/taxonomy"),
        ]
        for cand in candidates:
            if cand.exists():
                return cand
        return cwd / "taxonomy"

    def harvest_statutory_file(self, file_path: Path) -> list[CanonicalTerm]:
        """Harvests definitions from a single legal markdown file."""
        terms: list[CanonicalTerm] = []
        if not file_path.exists():
            return terms

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning(f"Could not read statutory file {file_path}: {exc}")
            return terms

        lines = content.splitlines()
        current_dieu: str | None = None
        in_definition_dieu = False

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            dieu_match = self.vbpl_profile.dieu_pattern.match(stripped)
            if dieu_match:
                current_dieu = dieu_match.group(2)
                title = dieu_match.group(1).lower()
                in_definition_dieu = (
                    "từ ngữ" in title or "định nghĩa" in title or "giải thích" in title
                )
                continue

            if in_definition_dieu and current_dieu:
                term = self._parse_definition_line(stripped, file_path.name, current_dieu, idx)
                if term:
                    terms.append(term)
        return terms

    def _parse_definition_line(
        self,
        line: str,
        doc_name: str,
        dieu_num: str,
        line_idx: int,
    ) -> CanonicalTerm | None:
        """Parses a candidate definition clause line."""
        match = DEFINITION_PATTERN.match(line)
        if not match:
            return None

        khoan_num = match.group(1)
        term_lemma = match.group(2).strip().strip("*_").strip()
        definition_body = match.group(3).strip()

        # Filter out numbers, punctuation, or generic headings
        if len(term_lemma) < 2 or term_lemma.isdigit():
            return None

        sha256_hash = compute_sha256(definition_body)
        term_id = f"STAT-{doc_name[:12].upper()}-D{dieu_num}K{khoan_num}"

        return CanonicalTerm(
            canonical_id=term_id,
            canonical_vi=term_lemma,
            domain="statutory",
            provenance=ProvenanceRecord(
                source_type="statutory",
                doc_id=doc_name,
                clause_anchor=f"dieu-{dieu_num}-khoan-{khoan_num}",
                line_anchor=line_idx,
                verbatim_definition=definition_body,
                verbatim_sha256=sha256_hash,
            ),
        )

    def harvest_idop_taxonomies(self) -> list[CanonicalTerm]:
        """Harvests internal governance categories from 21 IDOP JSON files."""
        terms: list[CanonicalTerm] = []
        if not self.idop_taxonomy_dir.exists():
            return terms

        for json_file in sorted(self.idop_taxonomy_dir.glob("*.json"), key=lambda p: p.name):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning(f"Failed to read taxonomy JSON {json_file.name}: {exc}")
                continue

            term_set_name = data.get("TermSetInfo", {}).get("Name", json_file.stem)
            for item in data.get("Terms", []):
                term_name = item.get("Name", "").strip()
                if not term_name:
                    continue
                term_id = f"INT-GOV-{term_set_name[:12].upper()}-{item.get('Id', '')[:8]}"
                terms.append(
                    CanonicalTerm(
                        canonical_id=term_id,
                        canonical_vi=term_name,
                        domain="internal_governance",
                        provenance=ProvenanceRecord(
                            source_type="internal_governance",
                            doc_id=json_file.name,
                            verbatim_definition=f"Thuộc nhóm phân loại thể chế {term_set_name}",
                            verbatim_sha256=compute_sha256(term_name),
                        ),
                    )
                )
        return terms

    def harvest_data_dictionary_csv(
        self,
        csv_path: Path | None = None,
        doc_id: str = "quyet_dinh_1812_qd_bxd_2026.md",
        merge_polysemous: bool = True,
    ) -> list[CanonicalTerm]:
        """Harvests 2D tabular data dictionary rows from Decision 1812/QĐ-BXD (COND-02, COND-03)."""
        target_csv = csv_path or (
            self.legal_corpus_dir
            / "01_vbpl"
            / "quyet_dinh_1812_qd_bxd_2026"
            / "tables"
            / "csv"
            / "bang_01.csv"
        )
        if not target_csv.exists():
            return []

        raw_terms: list[CanonicalTerm] = []
        current_ns = "I_QH"
        current_parent: str | None = None
        with open(target_csv, encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header row
            for row in reader:
                if not row or not row[0].strip():
                    continue
                current_ns, is_header = _detect_section_namespace(row[0], current_ns)
                if is_header:
                    current_parent = None
                    continue
                stt = row[0].strip()
                if "." not in stt:
                    current_parent = None
                term = _build_row_term(row, current_ns, current_parent, doc_id)
                if term.schema_spec and term.schema_spec.is_parent_group:
                    current_parent = term.canonical_vi
                raw_terms.append(term)

        return _merge_polysemous_terms(raw_terms) if merge_polysemous else raw_terms

    def build_seed_canonical_taxonomy(self) -> dict[str, Any]:
        """Compiles the complete Seed Taxonomy SSOT according to COND-11 to COND-18."""
        seed_terms = self._get_pillar1_core_statutory_terms()
        seed_terms.update(self._get_pillar2_international_terms())
        seed_terms.update(self._get_pillar3_internal_governance_terms())
        seed_terms.update(self._get_pillar4_lead_role_terms())
        seed_terms.update(self._get_pillar4_national_schema_terms())

        # Merge harvested IDOP taxonomies if available
        idop_terms = self.harvest_idop_taxonomies()
        for t in idop_terms[:30]:  # Seed core top-30 governance terms
            slug = re.sub(r"[^\w]+", "_", t.canonical_vi.lower()).strip("_")
            if slug and slug not in seed_terms:
                seed_terms[slug] = t.to_dict()

        return {
            "schema_version": "2.0.0",
            "dictionary_version": "1812/QĐ-BXD-v1.0",
            "governance_authority": "IBST - CCBA Core Architecture Council",
            "last_updated": "2026-10-28",
            "governance_basis": [
                "ADR-0046",
                "ADR-0059",
                "ADR-0061",
                "RULE-6.1",
                "COND-11..18",
                "1812/QĐ-BXD",
            ],
            "terms": seed_terms,
        }

    def _get_pillar1_core_statutory_terms(self) -> dict[str, Any]:
        """Compiles Pillar I core statutory definitions and faceted super-entities."""
        return {
            "chu_dau_tu": {
                "canonical_id": "STAT-CDT-001",
                "canonical_vi": "Chủ đầu tư",
                "domain": "governance",
                "is_faceted": True,
                "translations": {
                    "en": "Employer / Client / Project Owner",
                    "ja": "発注者 / 事業主",
                    "ko": "발주처 / 사업시행자",
                },
                "vi_forbidden": ["Người sử dụng lao động", "Bên thuê", "Chủ tiền"],
                "facets": {
                    "xay_dung": {
                        "domain": "xay_dung",
                        "legal_basis": "Điều 9 Luật Xây dựng số 135/2025/QH15",
                        "clause_anchor": "dieu-9",
                        "verbatim_definition": "Chủ đầu tư phân thành 4 nhóm theo tính chất nguồn vốn.",
                        "verbatim_sha256": compute_sha256("Chủ đầu tư Luật Xây dựng 2025 Điều 9"),
                        "effective_from": "2026-07-01",
                        "key_distinction": "Chủ thể trực tiếp quản lý, sử dụng vốn và chịu trách nhiệm trước Người QĐĐT",
                    },
                    "dau_thau": {
                        "domain": "dau_thau",
                        "legal_basis": "Khoản 2 Điều 4 Luật Đấu thầu số 22/2023/QH15",
                        "clause_anchor": "dieu-4-khoan-2",
                        "verbatim_definition": "Cơ quan, tổ chức sở hữu vốn hoặc vay vốn trực tiếp quản lý sử dụng vốn.",
                        "verbatim_sha256": compute_sha256(
                            "Chủ đầu tư Luật Đấu thầu 2023 Điều 4 Khoản 2"
                        ),
                        "effective_from": "2024-01-01",
                        "key_distinction": "Chủ thể phê duyệt kế hoạch lựa chọn nhà thầu và ký hợp đồng thầu",
                    },
                    "dat_dai": {
                        "domain": "dat_dai",
                        "legal_basis": "Khoản 10 Điều 3 Luật Đất đai số 31/2024/QH15",
                        "clause_anchor": "dieu-3-khoan-10",
                        "verbatim_definition": "Nhà đầu tư được lựa chọn và được giao đất, cho thuê đất.",
                        "verbatim_sha256": compute_sha256(
                            "Chủ đầu tư Luật Đất đai 2024 Điều 3 Khoản 10"
                        ),
                        "effective_from": "2024-08-01",
                        "key_distinction": "Chủ thể được cấp quyền sử dụng đất để triển khai dự án",
                    },
                },
            },
            "tham_tra": {
                "canonical_id": "STAT-001",
                "canonical_vi": "Thẩm tra",
                "domain": "consulting",
                "translations": {
                    "en": "Design Verification / Engineering Review",
                    "ja": "第三者照査 / 技術審査",
                    "ko": "설계적격성검토",
                },
                "vi_forbidden": [
                    "Thẩm định độc lập",
                    "Thẩm duyệt thiết kế xây dựng",
                    "Kiểm định thiết kế",
                ],
                "temporal": {"status": "active", "effective_from": "2026-07-01"},
                "provenance": {
                    "source_type": "statutory",
                    "doc_id": "luat_xay_dung_2025_135_2025_qh15.md",
                    "clause_anchor": "dieu-3-khoan-15",
                    "line_anchor": 84,
                    "verbatim_definition": "Thẩm tra là việc tổ chức, cá nhân thực hiện kiểm tra, đánh giá, kết luận đối với những nội dung cần thiết về chuyên môn trong quá trình chuẩn bị và thực hiện dự án đầu tư xây dựng.",
                    "verbatim_sha256": compute_sha256(
                        "Thẩm tra là việc tổ chức, cá nhân thực hiện kiểm tra, đánh giá, kết luận đối với những nội dung cần thiết về chuyên môn trong quá trình chuẩn bị và thực hiện dự án đầu tư xây dựng."
                    ),
                },
            },
            "tham_dinh_thiet_ke_pccc": {
                "canonical_id": "STAT-002",
                "canonical_vi": "Thẩm định thiết kế về phòng cháy và chữa cháy",
                "domain": "fire_safety",
                "translations": {
                    "en": "Fire Safety Design Appraisal",
                    "ja": "消防設計審査",
                    "ko": "소방설계심사",
                },
                "vi_forbidden": ["Thẩm duyệt thiết kế PCCC", "Phê duyệt PCCC", "Cấp phép PCCC"],
                "temporal": {
                    "status": "active",
                    "effective_from": "2025-07-01",
                    "grandfathering_legacy_term": "Thẩm duyệt thiết kế về PCCC (Nghị định 136/2020)",
                },
                "provenance": {
                    "source_type": "statutory",
                    "doc_id": "luat_phong_chay_chua_chay_va_cuu_nan_cuu_ho_2024_55_2024_qh1.md",
                    "clause_anchor": "dieu-2-khoan-17",
                    "line_anchor": 104,
                    "verbatim_definition": "Thẩm định thiết kế về phòng cháy và chữa cháy là việc xem xét, đánh giá sự tuân thủ các quy định của pháp luật, tiêu chuẩn, quy chuẩn kỹ thuật áp dụng đối với thiết kế về PCCC.",
                    "verbatim_sha256": compute_sha256(
                        "Thẩm định thiết kế về phòng cháy và chữa cháy là việc xem xét, đánh giá sự tuân thủ các quy định của pháp luật, tiêu chuẩn, quy chuẩn kỹ thuật áp dụng đối với thiết kế về PCCC."
                    ),
                },
            },
            "chieu_cao_pccc": {
                "canonical_id": "STAT-003",
                "canonical_vi": "Chiều cao PCCC (HPCCC)",
                "domain": "fire_safety",
                "translations": {
                    "en": "Fire Rescue Height (HPCCC)",
                    "ja": "消防活動上有効な高さ",
                    "ko": "소방구조높이",
                },
                "vi_forbidden": ["Chiều cao công trình PCCC", "Độ cao dập lửa"],
                "provenance": {
                    "source_type": "statutory",
                    "doc_id": "qcvn_06_2022_bxd.md",
                    "clause_anchor": "muc-1-4-9",
                    "verbatim_definition": "Đo từ mặt đường xe chữa cháy tiếp cận đến mép dưới của lỗ cửa sổ mở trên tường ngoài tầng trên cùng.",
                    "verbatim_sha256": compute_sha256(
                        "Đo từ mặt đường xe chữa cháy tiếp cận đến mép dưới của lỗ cửa sổ mở trên tường ngoài tầng trên cùng."
                    ),
                },
            },
        }

    def _get_pillar2_international_terms(self) -> dict[str, Any]:
        """Compiles Pillar II FDI and ISO 19650 international terminology."""
        return {
            "concept_design": {
                "canonical_id": "INTL-001",
                "canonical_vi": "Thiết kế ý tưởng",
                "domain": "design_stages",
                "translations": {
                    "en": "Concept Design",
                    "ja": "構想設計 / 企画設計",
                    "ko": "기본구상 / 기획설계",
                },
                "vi_forbidden": [
                    "Thiết kế khái niệm",
                    "Khái niệm thiết kế",
                    "Bản vẽ ý niệm",
                ],
                "provenance": {
                    "source_type": "international_fidic",
                    "doc_id": "FIDIC White Book / RIBA Stage 1",
                },
            },
            "schematic_design": {
                "canonical_id": "INTL-002",
                "canonical_vi": "Thiết kế sơ bộ / Phương án",
                "domain": "design_stages",
                "translations": {
                    "en": "Schematic Design",
                    "ja": "基本計画 / 概略設計",
                    "ko": "계획설계",
                },
                "vi_forbidden": ["Thiết kế sơ đồ", "Thiết kế lược đồ"],
            },
            "detailed_design": {
                "canonical_id": "INTL-003",
                "canonical_vi": "Thiết kế bản vẽ thi công (TKBVTC)",
                "domain": "design_stages",
                "translations": {
                    "en": "Detailed Design / Construction Drawings",
                    "ja": "実施設計 / 施工図面",
                    "ko": "실시설계 / 시공도면",
                },
                "vi_forbidden": ["Thiết kế chi tiết", "Bản vẽ xây dựng"],
            },
            "as_built_drawings": {
                "canonical_id": "INTL-004",
                "canonical_vi": "Bản vẽ hoàn công",
                "domain": "project_documentation",
                "translations": {
                    "en": "As-Built Drawings",
                    "ja": "竣工図 / 完成図",
                    "ko": "준공도면",
                },
                "vi_forbidden": ["Bản vẽ như xây dựng", "Bản vẽ như đã xây"],
            },
            "project_coordinator": {
                "canonical_id": "INTL-005",
                "canonical_vi": "Điều phối dự án (PIC)",
                "domain": "project_management",
                "translations": {
                    "en": "Project Coordinator (PIC)",
                    "ja": "プロジェクトコーディネーター (担当)",
                    "ko": "프로젝트 코디네이터 (담당)",
                },
                "vi_forbidden": ["Kỹ sư Điều phối Dự án", "Người điều phối"],
            },
            "iso19650_capability": {
                "canonical_id": "INTL-BIM-001",
                "canonical_vi": "Năng lực (Capability)",
                "domain": "bim_iso19650",
                "translations": {"en": "Capability", "ja": "能力 (Capability)"},
                "context_notes": "Thước đo kỹ năng, hiểu biết và trình độ chuyên môn của nhân sự (ISO 19650 Mục 3.3.17)",
            },
            "iso19650_capacity": {
                "canonical_id": "INTL-BIM-002",
                "canonical_vi": "Khả năng (Capacity)",
                "domain": "bim_iso19650",
                "translations": {"en": "Capacity", "ja": "リソース・キャパシティ"},
                "context_notes": "Thước đo phương tiện, nguồn lực và thời gian sẵn có của tổ chức (ISO 19650 Mục 3.3.18)",
            },
            "grandfathering_clause": {
                "canonical_id": "INTL-006",
                "canonical_vi": "Nguyên tắc bảo lưu công trình hiện hữu",
                "domain": "compliance",
                "translations": {
                    "en": "Grandfathering Clause",
                    "ja": "既存不適格条項 / 祖父条項",
                    "ko": "기득권 보호 조항",
                },
                "vi_forbidden": ["Điều khoản ông nội", "Khoản mục ông cố"],
            },
        }

    def _get_pillar3_internal_governance_terms(self) -> dict[str, Any]:
        """Compiles Pillar III corporate governance and RULE-6.1 brand terms."""
        return {
            "brand_institute": {
                "canonical_id": "INT-GOV-001",
                "canonical_vi": "Viện Khoa học công nghệ xây dựng (IBST)",
                "domain": "brand_nomenclature",
                "vi_forbidden": ["Viện IBST"],
                "context_notes": "Cấp Viện gọi là Viện, Viện KHCN hoặc IBST theo RULE-6.1",
            },
            "brand_center": {
                "canonical_id": "INT-GOV-002",
                "canonical_vi": "Trung tâm Tư vấn và Ứng dụng BIM trong xây dựng (CCBA)",
                "domain": "brand_nomenclature",
                "vi_forbidden": ["Trung tâm CCBA"],
                "context_notes": "Cấp Trung tâm gọi là Trung tâm hoặc CCBA theo RULE-6.1",
            },
            "brand_dispatch_header": {
                "canonical_id": "INT-GOV-003",
                "canonical_vi": "IBST - CCBA",
                "domain": "brand_nomenclature",
                "vi_forbidden": ["IBST / CCBA"],
                "context_notes": "Giao tiếp dự án dùng dấu gạch ngang IBST - CCBA",
            },
            "qc_gate_5_levels": {
                "canonical_id": "INT-GOV-004",
                "canonical_vi": "Hệ thống Kiểm soát Chất lượng Nội bộ 05 Cấp",
                "domain": "quality_control",
                "context_notes": "Quy trình kiểm soát theo Điều 13 CCBA Charter 2026: Level 1 Technical Check -> Level 2 Management Approval -> Level 3 Department Review -> Level 4 Compliance QA -> Level 5 Final Approval",
            },
        }

    def _get_pillar4_lead_role_terms(self) -> dict[str, Any]:
        """Compiles Pillar IV canonical lead role titles per Decision 1812/QĐ-BXD (Mục I.21 & II.C.11)."""
        role_specs = [
            ("01", "Chủ nhiệm đồ án quy hoạch xây dựng", "Urban Planning Project Director", []),
            ("02", "Chủ trì đồ án quy hoạch xây dựng", "Urban Planning Discipline Lead", []),
            ("03", "Chủ nhiệm khảo sát xây dựng", "Construction Survey Manager", []),
            ("04", "Chủ trì khảo sát xây dựng", "Construction Survey Lead", []),
            ("05", "Chủ nhiệm thiết kế xây dựng", "Chief Design Manager", []),
            ("06", "Chủ trì thiết kế xây dựng", "Design Discipline Lead", []),
            ("07", "Chủ nhiệm thẩm tra thiết kế xây dựng", "Chief Design Verification Manager", []),
            (
                "08",
                "Giám đốc quản lý dự án",
                "Project Management Director",
                ["Trưởng ban quản lý dự án", "Trưởng dự án QLDA"],
            ),
            (
                "09",
                "Chỉ huy trưởng công trường",
                "Site Commander / Construction Site Manager",
                ["Chỉ huy trưởng thi công", "Quản lý công trường"],
            ),
        ]
        terms: dict[str, Any] = {}
        for idx, vi_label, en_label, forbidden in role_specs:
            key = f"vai_tro_chu_tri_{idx}"
            terms[key] = {
                "canonical_id": f"STAT-1812-ROLE-{idx}",
                "canonical_vi": vi_label,
                "domain": "professional_capacity",
                "translations": {"en": en_label},
                "vi_forbidden": forbidden,
                "enum_values": {str(int(idx)): vi_label},
                "provenance": {
                    "source_type": "statutory",
                    "doc_id": "quyet_dinh_1812_qd_bxd_2026.md",
                    "clause_anchor": f"ii-c-11-3-role-{idx}",
                    "verbatim_definition": f"Danh mục chức danh chủ trì mã {int(idx)}: {vi_label} theo Quyết định 1812/QĐ-BXD.",
                    "verbatim_sha256": compute_sha256(vi_label),
                },
            }
        return terms

    def _get_pillar4_national_schema_terms(self) -> dict[str, Any]:
        """Compiles Pillar IV national database schema terms & 2-tier geography (1812/QĐ-BXD)."""
        return {
            "quy_hoach_chi_tiet_rut_gon": {
                "canonical_id": "STAT-1812-QH-04",
                "canonical_vi": "Quy hoạch chi tiết được lập theo quy trình rút gọn (quy hoạch tổng mặt bằng)",
                "domain": "urban_planning",
                "translations": {"en": "Abbreviated Detailed Master Plan"},
                "vi_forbidden": ["Quy hoạch tổng mặt bằng 1/500 rút gọn"],
                "enum_values": {
                    "1": "Quy hoạch chung",
                    "2": "Quy hoạch phân khu",
                    "3": "Quy hoạch chi tiết",
                    "4": "Quy hoạch chi tiết được lập theo quy trình rút gọn (quy hoạch tổng mặt bằng)",
                },
            },
            "nguon_von_dau_tu_1812": {
                "canonical_id": "STAT-1812-VON",
                "canonical_vi": "Nguồn vốn đầu tư",
                "domain": "project_investment",
                "enum_values": {
                    "1": "Dự án sử dụng vốn đầu tư công",
                    "2": "Dự án PPP",
                    "3": "Dự án đầu tư kinh doanh",
                    "4": "Dự án sử dụng nguồn vốn khác",
                    "5": "Dự án sử dụng hỗn hợp nhiều nguồn vốn",
                },
            },
            "dia_gioi_hanh_chinh_2_cap": {
                "canonical_id": "STAT-1812-GEO-2TIER",
                "canonical_vi": "Địa giới hành chính 2 cấp (Tỉnh/Thành phố - Phường/Xã/Đặc khu)",
                "domain": "administrative_geography",
                "context_notes": "Theo Quyết định 19/2025/QĐ-TTg và Quyết định 1812/QĐ-BXD: Địa điểm xây dựng gồm maTinh (2 số) và maXa (5 số: Phường/Xã/Đặc khu), không còn cấp Quận/Huyện trung gian.",
            },
            "kich_ban_thu_tuc_cong_trinh_1812": {
                "canonical_id": "STAT-1812-PROC-SCENARIOS",
                "canonical_vi": "Phân nhóm thủ tục dự án và công trình xây dựng",
                "domain": "administrative_procedure",
                "enum_values": {
                    "II_A_DA": "Dự án đầu tư xây dựng thuộc đối tượng thẩm định BCNCKT",
                    "II_B_CT_TD": "Công trình thuộc dự án thẩm định BCNCKT được miễn GPXD",
                    "II_C_CT_GPXD": "Công trình thuộc đối tượng đề nghị cấp Giấy phép xây dựng",
                    "II_D_CT_KTKT": "Công trình chỉ yêu cầu lập Báo cáo kinh tế - kỹ thuật và miễn GPXD",
                },
            },
        }

    def save_canonical_taxonomy_yaml(
        self,
        taxonomy: dict[str, Any] | None = None,
        output_path: Path | None = None,
    ) -> Path:
        """Saves canonical taxonomy dictionary to YAML SSOT file."""
        data = taxonomy or self.build_seed_canonical_taxonomy()
        target_path = output_path or DEFAULT_RESOURCE_PATH
        target_path.parent.mkdir(parents=True, exist_ok=True)

        class CleanDumper(yaml.SafeDumper):  # type: ignore[misc]
            """Clean YAML dumper preserving unicode and indenting lists."""

        CleanDumper.add_representer(
            str,
            lambda dumper, value: dumper.represent_scalar(
                "tag:yaml.org,2002:str", value, style=None
            ),
        )

        with open(target_path, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                Dumper=CleanDumper,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
        logger.info(f"Saved canonical taxonomy SSOT to {target_path}")
        return target_path
