"""
PDF and Content Utilities for mdconverter.
Refactored to use ccba_pdf_prep.
"""

import logging
from collections.abc import Sequence

from ccba_pdf_prep import get_blind_chunks, split_pdf

logger = logging.getLogger(__name__)

# Re-export
__all__ = ["split_pdf", "get_blind_chunks", "merge_markdown", "int_to_roman", "roman_to_int"]


def merge_markdown(parts: Sequence[str], separator: str = "\n\n---\n\n") -> str:
    """Merge multiple markdown strings into one."""
    # Filter out empty parts
    valid_parts = [p.strip() for p in parts if p and p.strip()]
    return separator.join(valid_parts)


def int_to_roman(num: int) -> str:
    """Convert integer to Roman numeral string."""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ""
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num


def roman_to_int(roman: str) -> int:
    """Convert Roman numeral string to integer."""
    roman = roman.upper().strip()
    roman_map = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    num = 0
    for i in range(len(roman)):
        if roman[i] not in roman_map:
            raise ValueError(f"Invalid Roman numeral character: {roman[i]}")
        if i > 0 and roman_map[roman[i]] > roman_map[roman[i - 1]]:
            num += roman_map[roman[i]] - 2 * roman_map[roman[i - 1]]
        else:
            num += roman_map[roman[i]]
    return num
