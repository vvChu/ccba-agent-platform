"""Boilerplate and noise removal for Vietnamese legal documents.

Removes government document headers, distribution lists, signer blocks,
digital signatures, date/page noise, and template dots.
"""

import logging
import re

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Boilerplate / Header Noise Removal
# ---------------------------------------------------------------------------

_BOILERPLATE_EXACT = [
    "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
    "CONG HOA XA HOI CHU NGHIA VIET NAM",
    "ĐỘC LẬP - TỰ DO - HẠNH PHÚC",
    "Độc lập - Tự do - Hạnh phúc",
    "DOC LAP - TU DO - HANH PHUC",
    "---oOo---",
    "———",
    "----",
]
_BOILERPLATE_UPPER = [s.upper() for s in _BOILERPLATE_EXACT]

_BOILERPLATE_REGEX = [
    re.compile(r"(?i)^\s*Số\s*:\s*\d+.*$"),
    re.compile(r"(?i)^\s*V/v\s*:.*$"),
    re.compile(r"(?i)^\s*(?:Hà Nội|Đà Nẵng|TP\.?\s*Hồ Chí Minh|Thành phố\s+\w+),?\s*ngày.*$"),
    re.compile(r"(?i)^\s*Kính gửi\s*:.*$"),
    re.compile(r"(?i)^\s*Nơi nhận\s*:.*$"),
    re.compile(
        r"(?i)^\s*(?:BỘ|UBND|ỦY BAN|SỞ|PHÒNG|HỘI ĐỒNG)\s+[A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ\s]+$"
    ),
    re.compile(r"(?i)^\s*CHÍNH PHỦ\s*$"),
    re.compile(r"(?i)^\s*THỦ TƯỚNG CHÍNH PHỦ\s*$"),
    re.compile(r"(?i)^\s*QUỐC HỘI\s*$"),
    re.compile(r"(?i)^\s*Người ký\s*:.*$"),
    re.compile(r"(?i)^\s*Thời gian ký\s*:.*$"),
    re.compile(r"(?i)^\s*Email\s*:.*@.*$"),
    re.compile(r"(?i)^\s*Cơ quan\s*:.*$"),
    re.compile(
        r"^\s*-\s*(?:UBND|Văn phòng|Hội đồng|Viện|Ủy ban|Ngân hàng|Cơ quan|VPCP|Các Vụ|Cổng|Lưu).*[;,:]\\s*$"
    ),
    re.compile(r"(?i)^.*CỔNG\s+THÔNG\s+TIN\s+ĐIỆN\s+TỬ.*$"),
    re.compile(r"(?i)^.*chinhphu\.vn.*$"),
    re.compile(r"(?i)^.*thongtinchinhphu@.*$"),
    re.compile(r"(?i)^\s*VGP\s*$"),
    re.compile(r"(?i)^.*CHINHPHU\.VN.*$"),
    re.compile(r"^\s*[A-ZĐTTBHCN]{2,8}\s*\(\s*\d+\s*\)\s*$"),
    re.compile(r"(?i)^\s*-?\s*Lưu\s*:.*$"),
    re.compile(r"(?i)^.*ngày.*(?:KT\.|TM\.|Ký thay)\s*(?:THỦ TƯỚNG|BỘ TRƯỞNG|CHỦ TỊCH).*$"),
    re.compile(r"(?i)^\s*(?:Ký bởi|Người ký)\s*:.*(?:Email|Cơ quan|Thời gian ký).*$"),
    re.compile(r"^\s*(?:QCVN|TCVN|TCCS)\s+\d+[:\-]\d{4}(?:\/[A-ZĐ]+)?\s*$"),
]


def strip_document_boilerplate(text: str) -> str:
    """Remove Vietnamese government document header boilerplate from text.

    Only processes the first ~600 chars to avoid stripping legitimate content.
    """
    if not text or len(text) < 20:
        return text

    lines = text.split("\n")
    cleaned_lines = []
    chars_seen = 0
    boilerplate_zone = True

    for line in lines:
        stripped = line.strip()
        chars_seen += len(line) + 1

        if chars_seen > 600:
            boilerplate_zone = False

        if boilerplate_zone and stripped:
            upper = stripped.upper()
            if any(bp in upper for bp in _BOILERPLATE_UPPER):
                continue
            if any(rx.match(stripped) for rx in _BOILERPLATE_REGEX):
                continue
            if (
                len(stripped) < 60
                and stripped == stripped.upper()
                and not any(c.isdigit() for c in stripped)
            ):
                if not re.match(r"^[ĐÐ]iều|^Chương|^Mục|^Phần", stripped):
                    continue

        if not stripped and boilerplate_zone:
            continue

        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines).strip()
    return result if result else text


def strip_noi_nhan_block(text: str) -> str:
    """Remove 'Nơi nhận:' distribution list block from anywhere in text."""
    if not text or "Nơi nhận" not in text and "nơi nhận" not in text.lower():
        return text

    lines = text.split("\n")
    result = []
    in_noi_nhan = False

    for line in lines:
        stripped = line.strip()
        if re.match(r"(?i)^\s*Nơi nhận\s*:", stripped):
            in_noi_nhan = True
            continue
        if in_noi_nhan:
            if re.match(r"^\s*-\s+", stripped) and (
                stripped.endswith(";")
                or stripped.endswith(",")
                or stripped.endswith(".")
                or "Lưu" in stripped
            ):
                continue
            if len(stripped) < 80 and stripped.endswith(";"):
                continue
            if len(stripped) < 80 and re.match(r"^\s*-\s+", stripped):
                continue
            in_noi_nhan = False
        result.append(line)

    return "\n".join(result)


def strip_signer_block(text: str) -> str:
    """Remove signer block (KT./TM./PHÓ THỦ TƯỚNG + name) from end of text.

    SAFETY: Only operates on the LAST 500 chars.
    """
    if not text or len(text) < 100:
        return text

    TAIL_SIZE = 500
    if len(text) <= TAIL_SIZE:
        head = ""
        tail = text
    else:
        split_pos = text.rfind("\n", len(text) - TAIL_SIZE, len(text) - 200)
        if split_pos == -1:
            split_pos = len(text) - TAIL_SIZE
        head = text[:split_pos]
        tail = text[split_pos:]

    _SIGNER_START = re.compile(
        r"^\s*(?:KT\.|TM\.|Ký thay\.?|Q\.)\s*"
        r"(?:TH\s*Ủ\s*T\s*Ư\s*Ớ\s*NG|CH\s*Ủ\s*T\s*Ị\s*CH|B\s*Ộ\s*TR\s*Ư\s*Ở\s*NG|CH\s*Í\s*NH\s*PH\s*Ủ|"
        r"THỦ TƯỚNG|CHỦ TỊCH|BỘ TRƯỞNG|CHÍNH PHỦ)",
        re.MULTILINE | re.IGNORECASE,
    )

    match = _SIGNER_START.search(tail)
    if match:
        tail = tail[: match.start()].rstrip()
        logger.info(
            f"  Stripped signer block from end of text ({len(text) - len(head) - len(tail)} chars removed)"
        )

    return (head + tail).strip()


_DIGITAL_SIGNATURE_RE = re.compile(
    r"(?:Ký bởi|Người ký)\s*:.+?(?:\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}\s*[+\-]\d{2}:\d{2})",
    re.IGNORECASE | re.DOTALL,
)


def strip_digital_signature(text: str) -> str:
    """Strip combined digital signature metadata from anywhere in text."""
    if not text:
        return text
    cleaned = _DIGITAL_SIGNATURE_RE.sub("", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip() if cleaned.strip() else text


# ---------------------------------------------------------------------------
# Date/Page Metadata Noise
# ---------------------------------------------------------------------------

_DATE_PAGE_NOISE_PATTERNS = [
    re.compile(r"\n\s*\d{2}\s+\d{2}\s+\d{2}\s+\d{4}\s+\d{4}\s*$"),
    re.compile(r"\n\s*\d{2}\s+\d{2}\s+\d{2}\s*$"),
    re.compile(r"^\s*\d{1,3}\s*$", re.MULTILINE),
]


def strip_date_page_noise(text: str) -> str:
    """Strip fragmented date/page number metadata from chunk text."""
    if not text:
        return text
    for pat in _DATE_PAGE_NOISE_PATTERNS:
        text = pat.sub("", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Template Dotted Line Stripping
# ---------------------------------------------------------------------------


def strip_template_dots(text: str) -> str:
    """Strip form template fill patterns (repeated dots/periods)."""
    if not text:
        return text
    text = re.sub(r"(?:\.\s*){20,}", "", text)
    text = re.sub(r"(?:\.\s){10,}", "", text)
    return text
