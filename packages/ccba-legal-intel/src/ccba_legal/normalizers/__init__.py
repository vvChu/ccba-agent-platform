"""Vietnamese legal document text normalizers.

Sub-modules:
  ocr_fixes   — OCR spacing, typos, stuck words, syllable boundaries
  boilerplate — Header/footer noise removal
  structure   — Paragraph rejoining, section splitting, legal formatting
  tables      — Table detection and normalization
  text_normalizer — Composite multi-pass TextNormalizer pipeline
"""

from ccba_legal.normalizers.boilerplate import (
    strip_date_page_noise,
    strip_digital_signature,
    strip_document_boilerplate,
    strip_noi_nhan_block,
    strip_signer_block,
    strip_template_dots,
)
from ccba_legal.normalizers.ocr_fixes import (
    fix_common_ocr_typos,
    fix_generic_stuck_words,
    fix_stuck_vietnamese_words,
    fix_vietnamese_syllable_boundaries,
    normalize_ocr_spacing,
)
from ccba_legal.normalizers.structure import (
    format_legal_structure,
    normalize_section_headings,
    rejoin_broken_headings,
    rejoin_cross_page_paragraphs,
    rejoin_paragraphs,
    validate_article_sequence,
)
from ccba_legal.normalizers.tables import (
    detect_garbled_table,
    fix_raw_pipe_tables,
    is_table_chunk,
)
from ccba_legal.normalizers.text_normalizer import (
    NormalizerConfig,
    TextNormalizer,
    get_text_normalizer,
    normalize_chunk_text,
)

__all__ = [
    # Facade & Config
    "TextNormalizer",
    "NormalizerConfig",
    "get_text_normalizer",
    "normalize_chunk_text",
    # OCR fixes
    "normalize_ocr_spacing",
    "fix_common_ocr_typos",
    "fix_stuck_vietnamese_words",
    "fix_generic_stuck_words",
    "fix_vietnamese_syllable_boundaries",
    # Boilerplate
    "strip_document_boilerplate",
    "strip_noi_nhan_block",
    "strip_signer_block",
    "strip_digital_signature",
    "strip_date_page_noise",
    "strip_template_dots",
    # Structure
    "rejoin_broken_headings",
    "rejoin_paragraphs",
    "rejoin_cross_page_paragraphs",
    "validate_article_sequence",
    "normalize_section_headings",
    "format_legal_structure",
    # Tables
    "detect_garbled_table",
    "is_table_chunk",
    "fix_raw_pipe_tables",
]
