"""Deterministic parser and validator for National Construction Database IDs (1812/QĐ-BXD).

Implements zero-LLM structural decoding and validation for:
- maThongTinQH (12-digit Urban & Rural Planning ID)
- maThongTin (13-digit Project ID & 13/15-digit Construction Work ID per COND-01)
- maKhoiTao (Administrative Procedure TTHC Dossier ID per Decree 118/2025/NĐ-CP)
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass

PLANNING_LEVEL_LABELS: dict[int, str] = {
    1: "Quy hoạch chung",
    2: "Quy hoạch phân khu",
    3: "Quy hoạch chi tiết",
    4: "Quy hoạch chi tiết được lập theo quy trình rút gọn (quy hoạch tổng mặt bằng)",
}

PLANNING_TYPE_LABELS: dict[int, str] = {
    1: "Quy hoạch đô thị",
    2: "Quy hoạch nông thôn",
    3: "Quy hoạch khu chức năng",
    4: "Quy hoạch HTKT đối với thành phố trực thuộc TW",
    5: "Quy hoạch không gian ngầm đối với thành phố trực thuộc TW",
}

ADJUSTMENT_TYPE_LABELS: dict[int, str] = {
    1: "Quy hoạch lập mới",
    2: "Điều chỉnh tổng thể quy hoạch",
    3: "Điều chỉnh cục bộ quy hoạch",
}

PROJECT_TYPE_LABELS: dict[int, str] = {
    1: "Dự án đầu tư xây dựng công trình chỉ cần lập Báo cáo kinh tế - kỹ thuật đầu tư xây dựng",
    2: "Dự án đầu tư xây dựng công trình (trừ dự án chỉ cần lập Báo cáo kinh tế - kỹ thuật)",
    3: "Dự án đầu tư xây dựng khu đô thị; dự án đầu tư xây dựng khu nhà ở",
    4: "Dự án đầu tư xây dựng hạ tầng kỹ thuật khu chức năng",
    5: "Dự án đầu tư xây dựng công trình có công năng phục vụ hỗn hợp",
}

PROCEDURE_TYPE_LABELS: dict[int, str] = {
    1: "Thẩm định Báo cáo nghiên cứu khả thi đầu tư xây dựng",
    2: "Cấp Giấy phép xây dựng",
    3: "Lập Báo cáo kinh tế - kỹ thuật đầu tư xây dựng",
}

_MA_KHOI_TAO_PATTERN = re.compile(r"^H(\d{2}\.\d{2})-(\d{2})(\d{2})(\d{2})-(\d{4,6})$")


@dataclass(frozen=True)
class NationalConstructionIdInfo:
    """Immutable decoded representation of a National Construction Database identifier."""

    raw_id: str
    kind: str  # "PLANNING" | "PROJECT" | "CONSTRUCTION" | "PROCEDURE" | "UNKNOWN"
    is_valid: bool
    province_code: str = ""
    year: int | None = None
    sequence_number: str = ""
    planning_level: int | None = None
    planning_level_label: str | None = None
    planning_type: int | None = None
    planning_type_label: str | None = None
    adjustment_type: int | None = None
    adjustment_type_label: str | None = None
    project_type: int | None = None
    project_type_label: str | None = None
    procedure_type: int | None = None
    procedure_type_label: str | None = None
    design_adjustment_count: str | None = None
    submission_date: str | None = None
    is_canonical_length: bool = True
    validation_errors: tuple[str, ...] = ()
    provenance_note: str = ""


def _parse_planning_id(cleaned: str) -> NationalConstructionIdInfo:
    """Decodes a 12-digit maThongTinQH planning identifier."""
    errors: list[str] = []
    province_code = cleaned[0:2]
    year = 2000 + int(cleaned[2:4])
    p_level = int(cleaned[4:5])
    p_type = int(cleaned[5:6])
    adj_type = int(cleaned[6:7])
    seq = cleaned[7:12]

    if p_level not in PLANNING_LEVEL_LABELS:
        errors.append(f"Invalid planning_level '{p_level}' (expected 1..4)")
    if p_type not in PLANNING_TYPE_LABELS:
        errors.append(f"Invalid planning_type '{p_type}' (expected 1..3)")
    if adj_type not in ADJUSTMENT_TYPE_LABELS:
        errors.append(f"Invalid adjustment_type '{adj_type}' (expected 1..3)")

    return NationalConstructionIdInfo(
        raw_id=cleaned,
        kind="PLANNING",
        is_valid=len(errors) == 0,
        province_code=province_code,
        year=year,
        sequence_number=seq,
        planning_level=p_level,
        planning_level_label=PLANNING_LEVEL_LABELS.get(p_level),
        planning_type=p_type,
        planning_type_label=PLANNING_TYPE_LABELS.get(p_type),
        adjustment_type=adj_type,
        adjustment_type_label=ADJUSTMENT_TYPE_LABELS.get(adj_type),
        validation_errors=tuple(errors),
    )


def _parse_project_or_construction_id(
    cleaned: str, expected_kind: str | None
) -> NationalConstructionIdInfo:
    """Decodes a 13-digit or 15-digit maThongTin project/construction work identifier (COND-01)."""
    errors: list[str] = []
    province_code = cleaned[0:2]
    year = 2000 + int(cleaned[2:4])
    proj_type = int(cleaned[4:5])
    proc_type = int(cleaned[5:6])

    if proj_type not in PROJECT_TYPE_LABELS:
        errors.append(f"Invalid project_type '{proj_type}' (expected 1..5)")
    if proc_type not in PROCEDURE_TYPE_LABELS:
        errors.append(f"Invalid procedure_type '{proc_type}' (expected 1..3)")

    norm_expected = (expected_kind or "").upper()
    if len(cleaned) == 15:
        kind = "CONSTRUCTION"
        seq = cleaned[6:13]
        adj_count: str | None = cleaned[13:15]
        note = "full_15_digit_construction_id"
    elif norm_expected in ("CONSTRUCTION", "MATHONGTIN_CONGTRINH"):
        kind = "CONSTRUCTION"
        seq = cleaned[6:11]
        adj_count = cleaned[11:13]
        note = "gazette_13_digit_sample_compatibility"
    else:
        kind = "PROJECT"
        seq = cleaned[6:13]
        adj_count = None
        note = "canonical_13_digit_project_id"

    return NationalConstructionIdInfo(
        raw_id=cleaned,
        kind=kind,
        is_valid=len(errors) == 0,
        province_code=province_code,
        year=year,
        sequence_number=seq,
        project_type=proj_type,
        project_type_label=PROJECT_TYPE_LABELS.get(proj_type),
        procedure_type=proc_type,
        procedure_type_label=PROCEDURE_TYPE_LABELS.get(proc_type),
        design_adjustment_count=adj_count,
        is_canonical_length=True,
        validation_errors=tuple(errors),
        provenance_note=note,
    )


def _parse_procedure_dossier_id(cleaned: str) -> NationalConstructionIdInfo:
    """Decodes an administrative procedure dossier ID (maKhoiTao per Decree 118/2025/NĐ-CP)."""
    match = _MA_KHOI_TAO_PATTERN.match(cleaned)
    if not match:
        return NationalConstructionIdInfo(
            raw_id=cleaned,
            kind="PROCEDURE",
            is_valid=False,
            is_canonical_length=False,
            validation_errors=("Invalid maKhoiTao format (expected Hxx.xx-YYMMDD-xxxx)",),
        )

    agency_prefix, yy_str, mm_str, dd_str, seq = match.groups()
    errors: list[str] = []
    year = 2000 + int(yy_str)
    sub_date: str | None = None
    try:
        dt = datetime.date(year, int(mm_str), int(dd_str))
        sub_date = dt.isoformat()
    except ValueError as exc:
        errors.append(f"Invalid submission date in maKhoiTao: {exc}")

    return NationalConstructionIdInfo(
        raw_id=cleaned,
        kind="PROCEDURE",
        is_valid=len(errors) == 0,
        province_code=agency_prefix,
        year=year,
        sequence_number=seq,
        submission_date=sub_date,
        validation_errors=tuple(errors),
        provenance_note="decree_118_2025_tthc_dossier_id",
    )


def parse_national_construction_id(
    raw_id: str,
    expected_kind: str | None = None,
) -> NationalConstructionIdInfo:
    """Parses and validates a National Construction Database ID per Decision 1812/QĐ-BXD.

    Args:
        raw_id: Raw identifier string (e.g. '012511153271', '0125215364201', 'H26.17-250112-0938').
        expected_kind: Optional hint ('PLANNING', 'PROJECT', 'CONSTRUCTION', 'PROCEDURE').

    Returns:
        NationalConstructionIdInfo containing decoded fields and validation status.
    """
    cleaned = raw_id.strip()
    if cleaned.startswith("H") or (expected_kind and expected_kind.upper() == "PROCEDURE"):
        return _parse_procedure_dossier_id(cleaned)

    if cleaned.isdigit():
        if len(cleaned) == 12:
            return _parse_planning_id(cleaned)
        if len(cleaned) in (13, 15):
            return _parse_project_or_construction_id(cleaned, expected_kind)

    return NationalConstructionIdInfo(
        raw_id=cleaned,
        kind="UNKNOWN",
        is_valid=False,
        is_canonical_length=False,
        validation_errors=(
            f"Unsupported ID format or length ({len(cleaned)} chars); expected 12, 13, 15 digits or Hxx.xx-YYMMDD-xxxx",
        ),
    )
