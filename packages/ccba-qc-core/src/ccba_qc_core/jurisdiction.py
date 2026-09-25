"""PCCC Deterministic Jurisdiction Router — Dual-Pathway Architecture (ADR-0035 & ADR-0059).

Implements statutory jurisdiction routing under:
- Luật Phòng cháy, chữa cháy và cứu nạn, cứu hộ số 55/2024/QH15 (Điều 16, Điều 17).
- Nghị định số 105/2025/NĐ-CP (Điều 8, Phụ lục I, II, III).
- SHA-256 Provenance: 6808c77f7438e0a15d7fc688726be181f476d958cf5f907ebc184afc0dc87262.
"""

from __future__ import annotations

import unicodedata
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

PROVENANCE_SHA256_ND105_2025 = (
    "6808c77f7438e0a15d7fc688726be181f476d958cf5f907ebc184afc0dc87262"
)


class PcccProjectType(str, Enum):
    """Canonical building occupancy classifications under Phụ lục III Nghị định 105/2025/NĐ-CP."""

    CHUNG_CU = "CHUNG_CU"
    NHA_O_RIENG_LE = "NHA_O_RIENG_LE"
    MAM_NON = "MAM_NON"
    TRUONG_PHO_THONG = "TRUONG_PHO_THONG"
    DAI_HOC_CAO_DANG = "DAI_HOC_CAO_DANG"
    BENH_VIEN_Y_TE = "BENH_VIEN_Y_TE"
    TRU_SO_CO_QUAN = "TRU_SO_CO_QUAN"
    KHACH_SAN_LUU_TRU = "KHACH_SAN_LUU_TRU"
    NHA_VAN_PHONG = "NHA_VAN_PHONG"
    THUONG_MAI_DICH_VU = "THUONG_MAI_DICH_VU"
    VUI_CHOI_GIAI_TRI = "VUI_CHOI_GIAI_TRI"
    KARAOKE_BAR = "KARAOKE_BAR"
    CONG_NGHIEP_A_B = "CONG_NGHIEP_A_B"
    CONG_NGHIEP_C = "CONG_NGHIEP_C"
    CONG_NGHIEP_D_E = "CONG_NGHIEP_D_E"
    KHO_HANG = "KHO_HANG"
    GARA_OTO = "GARA_OTO"
    CONG_TRINH_NGAM = "CONG_TRINH_NGAM"
    XANG_DAU_KHI_DOT = "XANG_DAU_KHI_DOT"
    NANG_LUONG = "NANG_LUONG"
    OTHER = "OTHER"


@dataclass
class PcccProjectSpec:
    """Project technical specification parameters required for statutory jurisdiction routing."""

    project_type: str | PcccProjectType
    height_m: float = 0.0
    floors: int = 1
    basement_floors: int = 0
    floor_area_m2: float = 0.0
    volume_m3: float = 0.0
    capacity_persons: int = 0
    investment_tier: str = "NHOM_B"
    is_renovation: bool = False

    def get_canonical_type(self) -> PcccProjectType:
        """Resolve project type into canonical PcccProjectType."""
        if isinstance(self.project_type, PcccProjectType):
            return self.project_type
        return _normalize_project_type(str(self.project_type))


@dataclass
class PcccJurisdictionResult:
    """Diagnostic outcome of dual-pathway PCCC jurisdiction determination."""

    # Pathway 1: Cơ quan Chuyên môn về Xây dựng (CQCMVXD)
    cqcmvxd_required: bool
    cqcmvxd_tier: str  # "BO_XAY_DUNG" | "SO_XAY_DUNG" | "NONE"
    cqcmvxd_scope: list[str] = field(default_factory=list)

    # Pathway 2: Cơ quan Cảnh sát PCCC & CNCH (Cơ quan Công an)
    police_required: bool = False
    police_tier: str = "NONE"  # "C07" | "PC07" | "NONE"
    police_scope: list[str] = field(default_factory=list)
    police_forms: list[str] = field(default_factory=list)

    # Pathway 3: Chủ đầu tư tự thẩm định (Điều 8 NĐ 105/2025)
    investor_self_appraisal: bool = False
    investor_forms: list[str] = field(default_factory=list)

    # Grounding & Citations
    is_annex_iii: bool = False
    annex_iii_item: int | None = None
    statutory_citations: list[str] = field(default_factory=list)
    provenance_hash: str = PROVENANCE_SHA256_ND105_2025

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to dictionary."""
        return asdict(self)

    def summary(self) -> str:
        """Generate human-readable summary of jurisdiction diagnosis."""
        lines = [
            "=== PHÂN ĐỊNH THẨM QUYỀN THẨM ĐỊNH THIẾT KẾ PCCC ===",
            f"- Phụ lục III Nghị định 105/2025/NĐ-CP: {'THUỘC' if self.is_annex_iii else 'KHÔNG THUỘC'}"
            + (f" (Mục {self.annex_iii_item})" if self.annex_iii_item else ""),
            f"- Kênh CQCMVXD: {'BẮT BUỘC' if self.cqcmvxd_required else 'KHÔNG'} ({self.cqcmvxd_tier})"
            + (f" — Nội dung: {', '.join(self.cqcmvxd_scope)}" if self.cqcmvxd_scope else ""),
            f"- Kênh Công an (C07/PC07): {'BẮT BUỘC' if self.police_required else 'KHÔNG'} ({self.police_tier})"
            + (f" — Mẫu: {', '.join(self.police_forms)}" if self.police_forms else ""),
            f"- Chủ đầu tư tự thẩm định (Điều 8): {'ÁP DỤNG' if self.investor_self_appraisal else 'KHÔNG'}"
            + (f" — Mẫu: {', '.join(self.investor_forms)}" if self.investor_forms else ""),
        ]
        return "\n".join(lines)


def _strip_accents(text: str) -> str:
    """Normalize and strip diacritics for deterministic matching."""
    norm = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in norm if unicodedata.category(ch) != "Mn").lower()


def _normalize_project_type(raw_type: str) -> PcccProjectType:
    """Fuzzy normalize project string into canonical PcccProjectType."""
    norm = _strip_accents(raw_type)

    if any(k in norm for k in ["chung cu", "tap the", "ky tuc xa", "condominium"]):
        return PcccProjectType.CHUNG_CU
    if any(k in norm for k in ["rieng le", "nha pho", "biet thu"]):
        return PcccProjectType.NHA_O_RIENG_LE
    if any(k in norm for k in ["mam non", "mau giao", "nha tre"]):
        return PcccProjectType.MAM_NON
    if any(k in norm for k in ["pho thong", "tieu hoc", "thcs", "thpt", "truong cap"]):
        return PcccProjectType.TRUONG_PHO_THONG
    if any(k in norm for k in ["dai hoc", "cao dang", "trung cap", "day nghe"]):
        return PcccProjectType.DAI_HOC_CAO_DANG
    if any(k in norm for k in ["benh vien", "y te", "phong kham", "dieu duong"]):
        return PcccProjectType.BENH_VIEN_Y_TE
    if any(k in norm for k in ["tru so", "uy ban", "co quan", "hanh chinh"]):
        return PcccProjectType.TRU_SO_CO_QUAN
    if any(k in norm for k in ["khach san", "nha nghi", "resort", "hotel"]):
        return PcccProjectType.KHACH_SAN_LUU_TRU
    if any(k in norm for k in ["van phong", "office"]):
        return PcccProjectType.NHA_VAN_PHONG
    if any(k in norm for k in ["thuong mai", "sieu thi", "trung tam tm", "cho"]):
        return PcccProjectType.THUONG_MAI_DICH_VU
    if any(k in norm for k in ["karaoke", "vu truong", "bar", "pub"]):
        return PcccProjectType.KARAOKE_BAR
    if any(k in norm for k in ["rap chieu", "nha hat", "hoi nghi", "thi dau", "giai tri"]):
        return PcccProjectType.VUI_CHOI_GIAI_TRI
    if any(k in norm for k in ["hang a", "hang b"]):
        return PcccProjectType.CONG_NGHIEP_A_B
    if "hang c" in norm:
        return PcccProjectType.CONG_NGHIEP_C
    if any(k in norm for k in ["hang d", "hang e", "nha xuong", "nha may", "cong nghiep"]):
        return PcccProjectType.CONG_NGHIEP_D_E
    if any(k in norm for k in ["kho", "kho hang", "warehouse"]):
        return PcccProjectType.KHO_HANG
    if any(k in norm for k in ["gara", "bai do xe", "nha de xe"]):
        return PcccProjectType.GARA_OTO
    if any(k in norm for k in ["ngam", "ham duong bo", "ham duong sat"]):
        return PcccProjectType.CONG_TRINH_NGAM
    if any(k in norm for k in ["xang dau", "khi dot", "gas", "lpg"]):
        return PcccProjectType.XANG_DAU_KHI_DOT
    if any(k in norm for k in ["dien luc", "thuy dien", "nhiet dien", "tram bien ap"]):
        return PcccProjectType.NANG_LUONG

    return PcccProjectType.OTHER


class PcccJurisdictionRouter:
    """Deterministic routing engine for PCCC statutory jurisdiction."""

    @classmethod
    def evaluate(cls, spec: PcccProjectSpec) -> PcccJurisdictionResult:
        """Route technical specification to appropriate statutory appraisal authority."""
        canonical_type = spec.get_canonical_type()
        is_annex_iii, annex_item = cls._check_annex_iii(canonical_type, spec)

        # 1. Police Authority Channel (PC07 / C07)
        police_required = is_annex_iii
        police_tier = "NONE"
        police_scope: list[str] = []
        police_forms: list[str] = []

        if police_required:
            police_scope = ["e", "g"]
            police_forms = ["PC12", "PC14"]
            inv_tier = spec.investment_tier.upper()
            if (
                inv_tier in {"QUOC_GIA", "NHOM_A"}
                or spec.height_m >= 100.0
                or spec.floors >= 30
                or spec.basement_floors >= 3
            ):
                police_tier = "C07"
            else:
                police_tier = "PC07"

        # 2. Construction Specialized Agency Channel (CQCMVXD)
        cqcmvxd_required, cqcmvxd_tier, cqcmvxd_scope = cls._evaluate_cqcmvxd(canonical_type, spec)

        # 3. Investor Self-Appraisal Channel (Điều 8 Nghị định 105/2025)
        investor_self_appraisal = (not police_required) or (not cqcmvxd_required)
        investor_forms = ["PC13"] if investor_self_appraisal else []

        # 4. Citations Assembly
        citations = cls._build_citations(is_annex_iii, annex_item, cqcmvxd_required)

        return PcccJurisdictionResult(
            cqcmvxd_required=cqcmvxd_required,
            cqcmvxd_tier=cqcmvxd_tier,
            cqcmvxd_scope=cqcmvxd_scope,
            police_required=police_required,
            police_tier=police_tier,
            police_scope=police_scope,
            police_forms=police_forms,
            investor_self_appraisal=investor_self_appraisal,
            investor_forms=investor_forms,
            is_annex_iii=is_annex_iii,
            annex_iii_item=annex_item,
            statutory_citations=citations,
            provenance_hash=PROVENANCE_SHA256_ND105_2025,
        )

    @staticmethod
    def _check_annex_iii(
        pt: PcccProjectType, spec: PcccProjectSpec
    ) -> tuple[bool, int | None]:
        """Check verbatim statutory thresholds of Phụ lục III Nghị định 105/2025/NĐ-CP."""
        # Check specific occupancy thresholds
        matched_item = None
        if pt == PcccProjectType.CHUNG_CU:
            if spec.floors >= 7 or spec.floor_area_m2 >= 3000.0 or spec.volume_m3 >= 10000.0:
                matched_item = 1
        elif pt == PcccProjectType.MAM_NON:
            if spec.capacity_persons >= 150 or spec.floor_area_m2 >= 2000.0 or spec.volume_m3 >= 5000.0:
                matched_item = 2
        elif pt in {PcccProjectType.TRUONG_PHO_THONG, PcccProjectType.DAI_HOC_CAO_DANG}:
            if spec.floors >= 5 or spec.floor_area_m2 >= 3000.0 or spec.volume_m3 >= 10000.0:
                matched_item = 2
        elif pt == PcccProjectType.BENH_VIEN_Y_TE:
            if (
                spec.floors >= 5
                or spec.floor_area_m2 >= 2000.0
                or spec.volume_m3 >= 5000.0
                or spec.capacity_persons >= 50
            ):
                matched_item = 3
        elif pt == PcccProjectType.TRU_SO_CO_QUAN:
            if spec.floors >= 5 or spec.floor_area_m2 >= 2500.0 or spec.volume_m3 >= 7500.0:
                matched_item = 4
        elif pt == PcccProjectType.KARAOKE_BAR:
            if spec.floors >= 3 or spec.floor_area_m2 >= 300.0 or spec.volume_m3 >= 1000.0:
                matched_item = 5
        elif pt == PcccProjectType.VUI_CHOI_GIAI_TRI:
            if (
                spec.capacity_persons >= 300
                or spec.floors >= 5
                or spec.floor_area_m2 >= 3000.0
                or spec.volume_m3 >= 10000.0
            ):
                matched_item = 5
        elif pt == PcccProjectType.THUONG_MAI_DICH_VU:
            if spec.floors >= 5 or spec.floor_area_m2 >= 3000.0 or spec.volume_m3 >= 10000.0:
                matched_item = 6
        elif pt in {PcccProjectType.KHACH_SAN_LUU_TRU, PcccProjectType.NHA_VAN_PHONG}:
            if spec.floors >= 7 or spec.floor_area_m2 >= 3000.0 or spec.volume_m3 >= 10000.0:
                matched_item = 7
        elif pt == PcccProjectType.GARA_OTO:
            if spec.capacity_persons >= 50 or spec.floor_area_m2 >= 1200.0:
                matched_item = 8
        elif pt == PcccProjectType.CONG_NGHIEP_A_B:
            if spec.volume_m3 >= 5000.0 or spec.floor_area_m2 >= 2000.0:
                matched_item = 9
        elif pt == PcccProjectType.CONG_NGHIEP_C:
            if spec.volume_m3 >= 15000.0 or spec.floor_area_m2 >= 5000.0:
                matched_item = 9
        elif pt == PcccProjectType.CONG_NGHIEP_D_E:
            if spec.volume_m3 >= 30000.0 or spec.floor_area_m2 >= 10000.0:
                matched_item = 9
        elif pt == PcccProjectType.KHO_HANG:
            if spec.volume_m3 >= 10000.0 or spec.floor_area_m2 >= 3000.0:
                matched_item = 10
        elif pt == PcccProjectType.XANG_DAU_KHI_DOT:
            matched_item = 11
        elif pt == PcccProjectType.CONG_TRINH_NGAM:
            matched_item = 12
        elif pt == PcccProjectType.NANG_LUONG:
            matched_item = 13

        if matched_item is not None:
            return True, matched_item

        # Cross-cutting: Underground structure or >= 2 basements (Mục 12 Phụ lục III)
        if spec.basement_floors >= 2 or (
            pt == PcccProjectType.CONG_TRINH_NGAM and spec.floor_area_m2 >= 500.0
        ):
            return True, 12

        return False, None

    @staticmethod
    def _evaluate_cqcmvxd(
        pt: PcccProjectType, spec: PcccProjectSpec
    ) -> tuple[bool, str, list[str]]:
        """Evaluate Construction Specialized Agency (CQCMVXD) jurisdiction."""
        # Single family small dwellings are exempt from CQCMVXD appraisal
        if pt == PcccProjectType.NHA_O_RIENG_LE and spec.height_m < 28.0 and spec.floors < 7:
            return False, "NONE", []

        inv_tier = spec.investment_tier.upper()
        full_scope = ["a", "b", "c", "d", "dd"]

        # Central Ministry of Construction (BXD)
        if (
            inv_tier == "QUOC_GIA"
            or (inv_tier == "NHOM_A" and (spec.height_m >= 75.0 or spec.floors >= 25))
            or spec.height_m >= 75.0
            or spec.floors >= 25
        ):
            return True, "BO_XAY_DUNG", full_scope

        # Provincial Department of Construction (SXD)
        if (
            spec.height_m >= 28.0
            or spec.floors >= 5
            or spec.floor_area_m2 >= 2000.0
            or inv_tier in {"NHOM_A", "NHOM_B", "NHOM_C"}
        ):
            return True, "SO_XAY_DUNG", full_scope

        return False, "NONE", []

    @staticmethod
    def _build_citations(
        is_annex_iii: bool, annex_item: int | None, cqcmvxd_required: bool
    ) -> list[str]:
        """Assemble formal legal citations for statutory provenance."""
        citations = [
            "Luật Phòng cháy, chữa cháy và cứu nạn, cứu hộ số 55/2024/QH15 (Điều 16, Điều 17)",
            "Nghị định số 105/2025/NĐ-CP (Điều 8, Phụ lục I, II, III)",
            "QCVN 06:2022/BXD và Sửa đổi 1:2023 (An toàn cháy cho nhà và công trình)",
        ]
        if is_annex_iii and annex_item is not None:
            citations.append(
                f"Phụ lục III Nghị định 105/2025/NĐ-CP (Mục {annex_item}) - Cơ quan Công an thẩm định"
            )
        else:
            citations.append(
                "Khoản 1 Điều 8 Nghị định 105/2025/NĐ-CP - Chủ đầu tư tự thẩm định thiết kế PCCC (Mẫu PC13)"
            )
        if cqcmvxd_required:
            citations.append(
                "Luật Xây dựng số 135/2025/QH15 (Điều 16 Khoản 1 điểm a, b, c, d, đ Luật 55/2024/QH15)"
            )
        return citations
