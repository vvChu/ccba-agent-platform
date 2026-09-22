"""Legal document structure formatting utilities.

Handles paragraph rejoining, heading detection, section number splitting,
cross-page text flow joining, and conversion of Vietnamese legal markers
to Markdown headings.
"""

import logging
import re

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Broken Heading Rejoin
# ---------------------------------------------------------------------------


def rejoin_broken_headings(text: str) -> str:
    """Rejoin ALL-CAPS headings broken across lines."""
    if not text:
        return text

    lines = text.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.endswith("**") and i + 1 < len(lines):
            next_stripped = lines[i + 1].strip()
            alpha_next = [c for c in next_stripped if c.isalpha()]
            if alpha_next and sum(1 for c in alpha_next if c.isupper()) / len(alpha_next) > 0.7:
                merged = stripped[:-2].rstrip() + " " + next_stripped
                if not merged.endswith("**"):
                    merged += "**"
                result.append(merged)
                i += 2
                continue

        result.append(line)
        i += 1

    return "\n".join(result)


# ---------------------------------------------------------------------------
# Paragraph Rejoining
# ---------------------------------------------------------------------------

_BLOCK_START_PATTERNS = [
    re.compile(r"^\s*[ĐÐ]iều\s+\d+"),
    re.compile(r"^\s*(?:Chương|CHƯƠNG)\s+[IVX\d]+"),
    re.compile(r"^\s*(?:Mục|MỤC)\s+[IVX\d]+"),
    re.compile(r"^\s*(?:Phần|PHẦN)\s+[IVX\d]+"),
    re.compile(r"^\s*(?:Bảng|BẢNG)\s+\S+"),
    re.compile(r"^\s*(?:Phụ lục|PHỤ LỤC)\s+\S+"),
    re.compile(r"^\s*\d+\.\s"),
    re.compile(r"^\s*[a-zđ]\)\s"),
    re.compile(r"^\s*-\s"),
    re.compile(r"^\s*\+\s"),
    re.compile(r"^\s*\*\s"),
    re.compile(r"^\s*[IVX]+\.\s"),
    re.compile(r"^\s*#{1,4}\s"),
    re.compile(r"^\s*\|"),
    re.compile(r"^\s*>"),
]


def _is_block_start(line: str) -> bool:
    """Check if a line starts a new structural block."""
    return any(p.match(line) for p in _BLOCK_START_PATTERNS)


_CONTINUATION_END_RE = re.compile(
    r"""[a-zàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệ"""
    r"""ìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữự"""
    r"""ỳýỷỹỵ0-9,;:\-–²³]\s*$""",
    re.UNICODE,
)

_CONTINUATION_START_RE = re.compile(
    r"^[a-zàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệ"
    r"ìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữự"
    r"ỳýỷỹỵ]",
    re.UNICODE,
)


def rejoin_paragraphs(text: str) -> str:
    """Merge hard-wrapped lines back into flowing paragraphs."""
    if not text:
        return ""

    lines = text.split("\n")
    result: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            result.append("")
            i += 1
            continue

        paragraph_parts = [line.rstrip()]
        i += 1

        while i < len(lines):
            next_line = lines[i]
            if not next_line.strip():
                break
            if _is_block_start(next_line):
                break
            current_tail = paragraph_parts[-1]
            ends_continuation = _CONTINUATION_END_RE.search(current_tail)
            starts_continuation = _CONTINUATION_START_RE.match(next_line.strip())
            if ends_continuation or starts_continuation:
                paragraph_parts.append(next_line.strip())
                i += 1
            else:
                break

        result.append(" ".join(paragraph_parts))

    return "\n".join(result)


# ---------------------------------------------------------------------------
# Section Number Splitting
# ---------------------------------------------------------------------------

_SECTION_NUM_INLINE_RE = re.compile(
    r"(?<=\S)"
    r"(?<![,.\d])"
    r"\s+"
    r"(\d{1,2}\.\d{1,2}(?:\.\d{1,2}){0,3}\.?)"
    r"(\s+)"
    r"(?=[A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴa-zđàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ])",
)

_SECTION_NUM_LINE_START_RE = re.compile(
    r"^(\d{1,2}\.\d{1,2}(?:\.\d{1,2}){0,3}\.?)\s+", re.MULTILINE
)

_NON_SECTION_WORDS = {
    "mm",
    "cm",
    "m",
    "km",
    "kg",
    "kn",
    "kpa",
    "mpa",
    "ha",
    "triệu",
    "tỷ",
    "nghìn",
    "tấn",
    "lít",
    "giây",
    "phút",
    "giờ",
    "ngày",
    "tháng",
    "năm",
    "lần",
    "%",
    "đến",
    "hoặc",
    "và",
    "hay",
    "thì",
    "là",
}


def normalize_section_headings(text: str) -> str:
    """Split inline QCVN section numbers onto separate lines."""
    if not text or "." not in text:
        return text

    lines = text.split("\n")
    result_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("|") or stripped.startswith("#"):
            result_lines.append(line)
            continue
        if _SECTION_NUM_LINE_START_RE.match(stripped) and "\n" not in stripped:
            rest_after_first = _SECTION_NUM_LINE_START_RE.sub("", stripped, count=1)
            if not re.search(r"\d{1,2}\.\d{1,2}(?:\.\d{1,2}){0,3}\.?\s+", rest_after_first):
                result_lines.append(line)
                continue
        new_line = _split_inline_sections(stripped)
        result_lines.append(new_line)

    return "\n".join(result_lines)


def _split_inline_sections(text: str) -> str:
    """Split a single line containing multiple inline section numbers."""
    _ref_prefix_re = re.compile(
        r"(?:Bảng|bảng|BẢNG|Phụ lục|phụ lục|PHỤ LỤC|Hình|hình|HÌNH|"
        r"mục|Mục|MỤC|điều|Điều|ĐIỀU|Điểm|điểm|khoản|Khoản|"
        r"trang|Trang|TRANG|Biểu|biểu|BIỂU)\s*$"
    )
    sec_pattern = re.compile(
        r"(?:^|\s+)"
        r"(\d{1,2}\.\d{1,2}(?:\.\d{1,2}){0,3}\.?)"
        r"\s+"
    )

    split_positions = []
    for match in sec_pattern.finditer(text):
        sec_num_start = match.start(1)
        if sec_num_start == 0:
            continue
        after_pos = match.end()
        if after_pos >= len(text):
            continue
        next_word_match = re.match(r"(\S+)", text[after_pos:])
        if not next_word_match:
            continue
        next_word = next_word_match.group(1).lower().rstrip(".,;:")
        if next_word in _NON_SECTION_WORDS:
            continue
        preceding = text[:sec_num_start].rstrip()
        if _ref_prefix_re.search(preceding):
            continue
        split_positions.append(sec_num_start)

    if not split_positions:
        return text

    segments = []
    prev = 0
    for pos in split_positions:
        seg = text[prev:pos].rstrip()
        if seg:
            segments.append(seg)
        prev = pos
    last_seg = text[prev:].strip()
    if last_seg:
        segments.append(last_seg)

    return "\n".join(segments)


# ---------------------------------------------------------------------------
# Legal Structure Formatting
# ---------------------------------------------------------------------------


def format_legal_structure(text: str) -> str:
    """Convert Vietnamese legal structure markers into Markdown headings."""
    if not text:
        return ""

    lines = text.split("\n")
    result: list[str] = []

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("#"):
            result.append(lines[i])
            i += 1
            continue

        # --- Section headers: Chương / Mục / Phần ---
        # Vietnamese legal docs often have the section number on one line
        # and the UPPERCASE title on the next line:
        #   Mục 4
        #   QUY HOẠCH XÂY DỰNG NÔNG THÔN
        # We merge them into: ## Mục 4 QUY HOẠCH XÂY DỰNG NÔNG THÔN
        section_match = re.match(r"^(?:Chương|CHƯƠNG|Mục|MỤC|Phần|PHẦN)\s+[IVX\d]+", stripped)
        if section_match:
            heading = stripped
            # Look ahead: merge next non-empty line if it's uppercase title
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                next_line = lines[j].strip()
                # Check if next line is all-uppercase title (or mostly uppercase)
                alpha_chars = [c for c in next_line if c.isalpha()]
                if (
                    alpha_chars
                    and len(next_line) >= 3
                    and sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars) > 0.7
                    and not re.match(r"^[ĐÐ]iều\s", next_line)
                ):
                    heading = f"{heading} {next_line}"
                    i = j + 1  # Skip the merged title line
                else:
                    i += 1
            else:
                i += 1
            result.append(f"\n## {heading}")
            continue
        if re.match(r"^[ĐÐ]iều\s+\d+[\.\\s:]", stripped):
            # Try to split heading from inline body text
            # Pattern: "Điều X. Short Title Body sentence..." → split into heading + body
            # Vietnamese legal titles are typically short noun phrases (< 60 chars)
            # Body text starts with common sentence-starting words
            #
            # SAFETY: Skip split for amendment/reference article titles
            # These are naturally long and contain law references that include
            # sentence-starter words (e.g., "Luật Quy hoạch", "Quy định...")
            _AMENDMENT_KEYWORDS = (
                "sửa đổi",
                "bổ sung",
                "ban hành",
                "thay thế",
                "hướng dẫn",
                "quy định chi tiết",
            )
            _is_amendment = any(kw in stripped.lower() for kw in _AMENDMENT_KEYWORDS)

            split_match = None
            if not _is_amendment:
                _SENTENCE_STARTERS = (
                    r"(?:Trong|Nhà|Theo|Căn|Các|Cơ|Việc|Đất|Mọi|Không|Tổ|Chính|"
                    r"Quốc|Người|Hội|Ủy|Chủ|Bao|Trên|Khi|Nếu|Sau|Trước|Tại|Nơi|Để|"
                    r"Nội|Hoạt|Nguyên|Đối|Thẩm|Trình|Thủ|"
                    r"Tổng|Đơn|Thời|Trách|Diện|Đền|"
                    r"Một|Hai|Ba|Bốn|Năm|Sáu)"
                )
                split_match = re.match(
                    rf"^([ĐÐ]iều\s+\d+\.?\s*.{{5,80}}?)\s+({_SENTENCE_STARTERS}\s.+)$", stripped
                )

            if split_match and len(stripped) >= 60:
                result.append(f"\n### {split_match.group(1)}")
                result.append(split_match.group(2))
            else:
                result.append(f"\n### {stripped}")
            i += 1
            continue

        num_match = re.match(r"^(\d{1,2}\.\d{1,2}(?:\.\d{1,2}){0,3}\.?)\s+(.*)", stripped)
        if num_match:
            sec_num = num_match.group(1).rstrip(".")
            sec_rest = num_match.group(2).strip()
            depth = sec_num.count(".")
            if sec_rest and len(sec_rest) >= 2:
                if depth == 1:
                    hashes = "###"
                elif depth == 2:
                    hashes = "####"
                else:
                    hashes = "#####"
                result.append(f"\n{hashes} {sec_num}. {sec_rest}")
                i += 1
                continue

        caps_chapter = re.match(
            r"^(\d{1,2})\.\s+([A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ]"
            r"[A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ\s,]+)$",
            stripped,
        )
        if caps_chapter:
            sec_num = caps_chapter.group(1)
            sec_title = caps_chapter.group(2).strip()
            result.append(f"\n## {sec_num}. {sec_title}")
            i += 1
            continue

        if re.match(r"^[IVX]+\.\s+[A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆ]", stripped):
            alpha_chars = [c for c in stripped if c.isalpha()]
            if alpha_chars:
                upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
                if upper_ratio > 0.6:
                    result.append(f"\n**{stripped}**")
                    i += 1
                    continue

        result.append(lines[i])
        i += 1

    return "\n".join(result)


# ---------------------------------------------------------------------------
# Cross-Page Text Flow Joining
# ---------------------------------------------------------------------------

# Signals that a page's text ends mid-sentence
_CROSS_PAGE_CONT_END_RE = re.compile(
    r"""[a-zàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệ"""
    r"""ìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữự"""
    r"""ỳýỷỹỵ0-9,;:\-–]\s*$""",
    re.UNICODE,
)

# Signals that the next page's text starts as a continuation
_CROSS_PAGE_CONT_START_RE = re.compile(
    r"^[a-zàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệ"
    r"ìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữự"
    r"ỳýỷỹỵ]",
    re.UNICODE,
)


def rejoin_cross_page_paragraphs(page_texts: list[str]) -> list[str]:
    """Join text that was broken across page boundaries.

    When a page ends with a continuation signal (lowercase letter, comma,
    semicolon, digit) AND the next page starts with a lowercase letter,
    the broken sentence is merged.

    Args:
        page_texts: List of extracted text per page (index = page number).

    Returns:
        List of text per page, with cross-page breaks healed.
        Joined text is appended to the earlier page; later page has the
        joined portion removed.

    Examples:
        Page N ends:  "...quy định về việc xây dựng công trình có"
        Page N+1 starts: "chiều cao trên 15 tầng..."
        → Merged: Page N gets "...có chiều cao trên 15 tầng"

    Safety:
        - Does NOT join if next page starts with a structural marker
          (Điều, Chương, numbered list, heading, table)
        - Only joins the FIRST line of the next page
        - Preserves all remaining content on both pages
    """
    if not page_texts or len(page_texts) < 2:
        return page_texts

    result = list(page_texts)  # Copy to avoid mutating input

    for i in range(len(result) - 1):
        current = result[i]
        next_page = result[i + 1]

        if not current or not next_page:
            continue

        # Get last non-empty line of current page
        current_lines = current.rstrip().split("\n")
        last_line = ""
        for line in reversed(current_lines):
            if line.strip():
                last_line = line
                break

        if not last_line:
            continue

        # Get first non-empty line of next page
        next_lines = next_page.lstrip().split("\n")
        first_line = ""
        first_line_idx = 0
        for idx, line in enumerate(next_lines):
            if line.strip():
                first_line = line.strip()
                first_line_idx = idx
                break

        if not first_line:
            continue

        # Check: current page ends with continuation signal
        if not _CROSS_PAGE_CONT_END_RE.search(last_line):
            continue

        # Check: next page starts with continuation (lowercase)
        if not _CROSS_PAGE_CONT_START_RE.match(first_line):
            continue

        # Safety: don't join if next page starts with structural element
        if _is_block_start(first_line):
            continue

        # Merge: append first line of next page to current page
        merged_line = last_line.rstrip() + " " + first_line
        current_lines_clean = [line for line in current_lines if line.strip()]
        if current_lines_clean:
            current_lines_clean[-1] = merged_line
        result[i] = "\n".join(current_lines_clean)

        # Remove the joined line from next page
        remaining = next_lines[first_line_idx + 1 :]
        result[i + 1] = "\n".join(remaining).lstrip()

        logger.debug(
            f"[CROSS-PAGE] Joined p{i + 1}→p{i + 2}: ...{last_line[-30:]} + {first_line[:30]}..."
        )

    return result


# ---------------------------------------------------------------------------
# Article Sequence Validator (Fix duplicate Điều numbers from OCR)
# ---------------------------------------------------------------------------

# Matches both raw "Điều N." and markdown "### Điều N." headings
_DIEU_LINE_RE = re.compile(
    r"^(#{0,4}\s*)[ĐÐ]iều\s+(\d+)\.?\s*(.*)",
    re.MULTILINE,
)


def validate_article_sequence(page_texts: list[str]) -> list[str]:
    """Fix duplicate Điều numbers caused by OCR hallucination.

    Vietnamese legal articles have strictly monotonically increasing numbers.
    When OCR processes pages independently, it may hallucinate article numbers,
    causing duplicate Điều N markers.

    Algorithm:
      1. Scan all page texts for Điều N markers.
      2. Build the article sequence across the entire document.
      3. Detect duplicates (same Điều number appears 2+ times).
      4. For each duplicate: keep the occurrence that fits the sequential
         position (appears between Điều N-1 and Điều N+1).
      5. Downgrade the misplaced occurrence: remove the Điều heading but
         KEEP the content (it's still part of the document).

    Args:
        page_texts: List of page text strings (index = page number).

    Returns:
        List of page texts with duplicate article headings fixed.
    """
    if not page_texts or len(page_texts) < 2:
        return page_texts

    # 1. Collect ALL Điều markers with their document-level position
    all_articles = []  # (article_num, page_idx, char_offset, full_match, title)
    for page_idx, ptext in enumerate(page_texts):
        for m in _DIEU_LINE_RE.finditer(ptext):
            num = int(m.group(2))
            title = m.group(3).strip()[:60]
            all_articles.append((num, page_idx, m.start(), m.group(0), title))

    if len(all_articles) < 3:
        return page_texts

    # 2. Detect duplicates
    from collections import defaultdict

    num_to_occurrences = defaultdict(list)
    for art in all_articles:
        num_to_occurrences[art[0]].append(art)

    duplicates = {n: occs for n, occs in num_to_occurrences.items() if len(occs) > 1}

    if not duplicates:
        return page_texts

    logger.info(
        f"[ARTICLE-SEQ] Found {len(duplicates)} duplicate Điều numbers: {sorted(duplicates.keys())}"
    )

    # 3. Build document-order position map for sequence analysis
    ordered = sorted(all_articles, key=lambda a: (a[1], a[2]))  # by page, offset
    art_positions = {}  # article_num -> list of positions in ordered
    for pos, art in enumerate(ordered):
        art_positions.setdefault(art[0], []).append(pos)

    result = list(page_texts)  # Copy

    # 4. For each duplicate, determine which to keep
    for dup_num, occurrences in sorted(duplicates.items()):
        # Find positions of neighbors in the ordered sequence
        positions = art_positions.get(dup_num, [])
        if len(positions) < 2:
            continue

        # Score each occurrence: how well does it fit the sequence?
        best_score = -1
        best_idx = -1
        for i, _occ in enumerate(occurrences):
            pos = positions[i]
            score = 0

            # Check predecessor: Điều before this should be dup_num - 1
            # (skip other duplicates of the same number)
            if pos > 0:
                prev_num = ordered[pos - 1][0]
                if prev_num == dup_num - 1:
                    score += 2  # Strong signal
                elif prev_num < dup_num and prev_num != dup_num:
                    score += 1

            # Check successor: Điều after this should be dup_num + 1
            # This is the STRONGEST signal — the correct Điều N flows into N+1
            if pos < len(ordered) - 1:
                next_num = ordered[pos + 1][0]
                if next_num == dup_num + 1:
                    score += 3  # Strongest signal
                elif next_num > dup_num and next_num != dup_num:
                    score += 1

            # Tiebreaker: prefer later occurrence (last before N+1)
            if score > best_score or (score == best_score and i > best_idx):
                best_score = score
                best_idx = i

        # Downgrade all except the best one
        for i, occ in enumerate(occurrences):
            if i == best_idx:
                continue

            num, page_idx, char_off, full_match, title = occ
            old_text = result[page_idx]

            # Replace "Điều N. Title" or "### Điều N. Title" with plain text
            # Keep the content but remove the article heading marker
            # This prevents it from being treated as a structural heading
            downgraded = full_match.lstrip("#").strip()
            # Prefix with a note for transparency
            replacement = f"**[↓ OCR gán nhầm]** {downgraded}"

            result[page_idx] = old_text.replace(full_match, replacement, 1)

            # Only warn when we're confident it's a real OCR error (high score neighbor)
            # Low score = Mục lục / table-of-contents false positive — just debug log
            log_fn = logger.warning if best_score > 3 else logger.debug
            log_fn(
                f"[ARTICLE-SEQ] Duplicate Điều {num} downgraded on page "
                f"{page_idx + 1}: '{title}' (score={best_score} vs this)"
            )

    return result
