"""Seam LexiconHarvester for CCBA Canonical Construction & Internal Lexicon Framework (CCILF).

Harvests statutory definitions from ccba-legal-knowledge, corporate taxonomies
from IDOP-CCBA-WAY, and compiles the Hub SSOT taxonomy (ADR-0059, ADR-0061, COND-11..18).
"""

from __future__ import annotations

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
    ProvenanceRecord,
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


def compute_sha256(text: str) -> str:
    """Computes SHA-256 hash of verbatim definition text (ADR-0059)."""
    clean_text = text.strip()
    return hashlib.sha256(clean_text.encode("utf-8")).hexdigest()


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

    def build_seed_canonical_taxonomy(self) -> dict[str, Any]:
        """Compiles the complete Seed Taxonomy SSOT according to COND-11 to COND-18."""
        seed_terms = self._get_pillar1_core_statutory_terms()
        seed_terms.update(self._get_pillar2_international_terms())
        seed_terms.update(self._get_pillar3_internal_governance_terms())

        # Merge harvested IDOP taxonomies if available
        idop_terms = self.harvest_idop_taxonomies()
        for t in idop_terms[:30]:  # Seed core top-30 governance terms
            slug = re.sub(r"[^\w]+", "_", t.canonical_vi.lower()).strip("_")
            if slug and slug not in seed_terms:
                seed_terms[slug] = t.to_dict()

        return {
            "schema_version": "2.0.0",
            "governance_authority": "IBST - CCBA Core Architecture Council",
            "last_updated": "2026-10-23",
            "governance_basis": [
                "ADR-0046",
                "ADR-0059",
                "ADR-0061",
                "RULE-6.1",
                "COND-11..18",
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

    def save_canonical_taxonomy_yaml(
        self,
        taxonomy: dict[str, Any] | None = None,
        output_path: Path | None = None,
    ) -> Path:
        """Saves canonical taxonomy dictionary to YAML SSOT file."""
        data = taxonomy or self.build_seed_canonical_taxonomy()
        target_path = output_path or DEFAULT_RESOURCE_PATH
        target_path.parent.mkdir(parents=True, exist_ok=True)

        class CleanDumper(yaml.SafeDumper):
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
