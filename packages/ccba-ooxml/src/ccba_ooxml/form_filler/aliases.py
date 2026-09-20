# packages/ccba-ooxml/src/ccba_ooxml/form_filler/aliases.py
"""Administrative field aliases and label normalization for automatic form filling."""

from __future__ import annotations

import re
from typing import Any

from ..tables import vietnamese_to_ascii

# Canonical mapping of administrative form fields to common Vietnamese/English aliases
ADMINISTRATIVE_FIELD_ALIASES: dict[str, list[str]] = {
    "ho_va_ten": [
        "họ và tên",
        "họ tên",
        "ho va ten",
        "ho ten",
        "full name",
        "fullname",
        "name",
        "họ và tên khai sinh",
        "họ và tên người khai",
        "tên",
    ],
    "ho": [
        "họ",
        "ho",
        "surname",
        "last name",
        "family name",
    ],
    "ten": [
        "tên",
        "ten",
        "first name",
        "given name",
    ],
    "ten_dem": [
        "tên đệm",
        "ten dem",
        "tên lót",
        "ten lot",
        "middle name",
    ],
    "gioi_tinh": [
        "giới tính",
        "gioi tinh",
        "gender",
        "sex",
        "nam/nữ",
        "nam / nữ",
    ],
    "ngay_sinh": [
        "ngày sinh",
        "ngay sinh",
        "ngày tháng năm sinh",
        "ngay thang nam sinh",
        "date of birth",
        "dob",
        "sinh ngày",
        "năm sinh",
        "nam sinh",
    ],
    "noi_sinh": [
        "nơi sinh",
        "noi sinh",
        "place of birth",
        "pob",
    ],
    "que_quan": [
        "quê quán",
        "que quan",
        "nguyên quán",
        "nguyen quan",
        "hometown",
        "native place",
    ],
    "dan_toc": [
        "dân tộc",
        "dan toc",
        "ethnic",
        "ethnicity",
    ],
    "ton_giao": [
        "tôn giáo",
        "ton giao",
        "religion",
    ],
    "quoc_tich": [
        "quốc tịch",
        "quoc tich",
        "nationality",
    ],
    "so_cmnd_cccd": [
        "số cmnd/cccd",
        "số cccd",
        "số cmnd",
        "cmnd/cccd",
        "so_cccd_cmnd",
        "cccd",
        "cmnd",
        "so cmnd",
        "so cccd",
        "số định danh cá nhân",
        "so dinh danh ca nhan",
        "id number",
        "identity card no",
        "national id",
        "số căn cước công dân",
    ],
    "ngay_cap_cccd": [
        "ngày cấp cccd",
        "ngày cấp",
        "ngay cap",
        "date of issue",
        "ngay cap cccd",
    ],
    "noi_cap_cccd": [
        "nơi cấp cccd",
        "nơi cấp",
        "noi cap",
        "place of issue",
        "noi cap cccd",
    ],
    "ho_chieu_so": [
        "hộ chiếu số",
        "số hộ chiếu",
        "ho chieu so",
        "so ho chieu",
        "passport no",
        "passport number",
        "hộ chiếu",
        "ho chieu",
    ],
    "ngay_cap_ho_chieu": [
        "ngày cấp hộ chiếu",
        "ngay cap ho chieu",
        "passport date of issue",
    ],
    "noi_cap_ho_chieu": [
        "nơi cấp hộ chiếu",
        "noi cap ho chieu",
        "passport place of issue",
    ],
    "ngay_het_han_ho_chieu": [
        "ngày hết hạn",
        "ngay het han",
        "có giá trị đến ngày",
        "co gia tri den ngay",
        "expiry date",
        "expiration date",
    ],
    "dia_chi_thuong_tru": [
        "địa chỉ thường trú",
        "dia chi thuong tru",
        "nơi đăng ký hộ khẩu thường trú",
        "hộ khẩu thường trú",
        "ho khau thuong tru",
        "thường trú",
        "thuong tru",
        "permanent address",
        "registered address",
    ],
    "noi_o_hien_nay": [
        "nơi ở hiện nay",
        "noi o hien nay",
        "chỗ ở hiện nay",
        "cho o hien nay",
        "địa chỉ hiện tại",
        "dia chi hien tai",
        "địa chỉ hiện nay",
        "dia chi hien nay",
        "nơi ở",
        "noi o",
        "chỗ ở",
        "cho o",
        "địa chỉ",
        "dia chi",
        "hiện trú",
        "hien tru",
        "current address",
        "residential address",
    ],
    "so_dien_thoai": [
        "số điện thoại",
        "so dien thoai",
        "điện thoại",
        "dien thoai",
        "phone",
        "telephone",
        "phone number",
        "mobile",
        "tel",
        "sđt",
        "sdt",
    ],
    "email": [
        "email",
        "e-mail",
        "thư điện tử",
        "thu dien tu",
    ],
    "nghe_nghiep": [
        "nghề nghiệp",
        "nghe nghiep",
        "chức vụ",
        "chuc vu",
        "nghề nghiệp hiện nay",
        "occupation",
        "profession",
        "job",
        "position",
    ],
    "noi_lam_viec": [
        "nơi làm việc",
        "noi lam viec",
        "cơ quan",
        "co quan",
        "đơn vị công tác",
        "don vi cong tac",
        "employer",
        "workplace",
        "company",
        "công tác tại",
    ],
    "dia_chi_co_quan": [
        "địa chỉ cơ quan",
        "dia chi co quan",
        "địa chỉ nơi làm việc",
        "work address",
    ],
    "dien_thoai_co_quan": [
        "điện thoại cơ quan",
        "dien thoai co quan",
        "work phone",
    ],
    "tinh_trang_hon_nhan": [
        "tình trạng hôn nhân",
        "tinh trang hon nhan",
        "hôn nhân",
        "hon nhan",
        "marital status",
    ],
    "trinh_do_hoc_van": [
        "trình độ học vấn",
        "trinh do hoc van",
        "trình độ chuyên môn",
        "học vấn",
        "trinh do chuyen mon",
        "hoc van",
        "education",
    ],
    "chuyen_mon": [
        "chuyên môn",
        "chuyen mon",
        "ngành đào tạo",
        "major",
        "field of study",
    ],
    "muc_dich_chuyen_di": [
        "mục đích chuyến đi",
        "muc dich chuyen di",
        "lý do xuất cảnh",
        "purpose of visit",
    ],
    "thoi_gian_luu_tru": [
        "thời gian lưu trú",
        "thoi gian luu tru",
        "duration of stay",
    ],
    "ngay_nhap_canh_du_kien": [
        "ngày nhập cảnh dự kiến",
        "ngay nhap canh du kien",
        "expected arrival date",
    ],
    "ngay_xuat_canh_du_kien": [
        "ngày xuất cảnh dự kiến",
        "ngay xuat canh du kien",
        "expected departure date",
    ],
    "nguoi_bao_lanh": [
        "người bảo lãnh",
        "nguoi bao lanh",
        "đơn vị bảo lãnh",
        "sponsor",
    ],
    "dia_chi_nguoi_bao_lanh": [
        "địa chỉ người bảo lãnh",
        "dia chi nguoi bao lanh",
        "sponsor address",
    ],
    "ghi_chu": [
        "ghi chú",
        "ghi chu",
        "note",
        "remarks",
    ],
}

ADMINISTRATIVE_TABLE_ALIASES: dict[str, list[str]] = {
    "thanh_vien_gia_dinh": [
        "thân nhân",
        "than nhan",
        "gia đình",
        "gia dinh",
        "thành viên gia đình",
        "quan hệ gia đình",
        "family members",
        "family",
        "quan hệ nhân thân",
    ],
    "qua_trinh_cong_tac": [
        "quá trình công tác",
        "qua trinh cong tac",
        "lịch sử làm việc",
        "lich su lam viec",
        "employment history",
        "work experience",
        "quá trình làm việc",
    ],
    "qua_trinh_hoc_tap": [
        "quá trình học tập",
        "qua trinh hoc tap",
        "lịch sử học tập",
        "education history",
        "học tập",
    ],
    "lich_su_du_lich": [
        "lịch sử du lịch",
        "lich su du lich",
        "các nước đã đến",
        "travel history",
    ],
    "tre_em_di_cung": [
        "trẻ em đi cùng",
        "người đi cùng",
        "tre em di cung",
        "nguoi di cung",
        "accompanying persons",
    ],
}


def normalize_label(label: str) -> str:
    """Normalizes a form label for comparison with canonical keys.

    Strips numbering prefixes (e.g., '1.', '1.1.', '(1)', 'a.', 'a)'), trailing/leading punctuation,
    converts Vietnamese accented characters to ASCII lowercase, and converts spaces to underscores.
    """
    if not label:
        return ""
    s = label.strip()
    # Strip numbering / bullet prefixes like '1.', '1.1.', '(1)', '(a)', 'a.', 'a)', 'I.', etc.
    s = re.sub(
        r"^(?:\([0-9a-zA-Z]+\)|[0-9]+(?:\.[0-9]+)*\.?|[a-zA-Z][\.\)]|[IVXLCDM]+\.)\s*", "", s
    )
    # Strip trailing punctuation often found in form labels: ':', '...', '___', etc.
    s = re.sub(r"[:\.\-_–—\s\?]+$", "", s)
    # Strip leading punctuation if any
    s = re.sub(r"^[:\.\-_–—\s]+", "", s)
    # Convert Vietnamese to ASCII
    s = vietnamese_to_ascii(s).lower()
    # Replace non-alphanumeric with single underscore
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def _build_reverse_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical, aliases in ADMINISTRATIVE_FIELD_ALIASES.items():
        norm_canonical = normalize_label(canonical)
        lookup[norm_canonical] = canonical
        for alias in aliases:
            norm_alias = normalize_label(alias)
            if norm_alias:
                lookup[norm_alias] = canonical
    return lookup


_ALIAS_REVERSE_LOOKUP = _build_reverse_lookup()


def flatten_data(data: dict[str, Any]) -> dict[str, Any]:
    """Flattens nested dictionaries while preserving list structures.

    This allows hierarchical schemas (such as personal_profile.yaml with sections
    like 'thong_tin_co_ban', 'dinh_danh_phap_ly') to be matched directly.
    """
    flat: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, dict):
            flat.update(flatten_data(v))
        else:
            flat[k] = v
    return flat


def resolve_field_value(label: str, flat_data: dict[str, Any]) -> tuple[bool, Any, str | None]:
    """Resolves a raw form label to a value in flat_data using canonical alias matching.

    Returns:
        tuple[bool, Any, str | None]: (found, value, resolved_key)
    """
    if not label or not flat_data:
        return False, None, None

    # 1. Exact raw key match
    if label in flat_data:
        return True, flat_data[label], label

    norm_label = normalize_label(label)
    if not norm_label:
        return False, None, None

    # 2. Direct normalized match against flat_data keys
    for k, v in flat_data.items():
        if normalize_label(k) == norm_label:
            return True, v, k

    # 3. Canonical alias reverse lookup
    canonical_key = _ALIAS_REVERSE_LOOKUP.get(norm_label)
    if canonical_key:
        if canonical_key in flat_data:
            return True, flat_data[canonical_key], canonical_key

        # Check if any key in flat_data maps to the same canonical key
        for k, v in flat_data.items():
            if _ALIAS_REVERSE_LOOKUP.get(normalize_label(k)) == canonical_key:
                return True, v, k

    return False, None, None
