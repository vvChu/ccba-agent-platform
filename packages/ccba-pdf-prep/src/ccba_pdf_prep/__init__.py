"""ccba-pdf-prep — Unified PDF Preprocessor for AI Vision Pipelines.

Primary Deep Seam:
    PDFProcessingPipeline — Segment, tile, and analyze PDF drawings end-to-end.
                            Call: pipeline.process(pdf_path, output_dir)

Document Skills (standalone utilities for PDF forms):
    fill_pdf_fields  — Fill interactive PDF form fields programmatically.
    get_field_info   — Inspect PDF form field metadata.
"""

from .composite import CompositeBuilder as CompositeBuilder
from .core import (
    PageDetail as PageDetail,
)
from .core import (
    PDFAnalyzer as PDFAnalyzer,
)
from .core import (
    PDFCategory as PDFCategory,
)
from .core import (
    PDFReport as PDFReport,
)
from .core import (
    Segment as Segment,
)
from .core import (
    get_blind_chunks as get_blind_chunks,
)
from .core import (
    render_page_to_image as render_page_to_image,
)
from .core import (
    split_pdf as split_pdf,
)
from .detector import TitleBlockDetector as TitleBlockDetector
from .detector import TitleBlockRegion as TitleBlockRegion
from .document_skills.pdf_forms import (
    fill_pdf_fields as fill_pdf_fields,
)
from .document_skills.pdf_forms import (
    get_field_info as get_field_info,
)
from .manipulation import (
    extract_text_from_pdf as extract_text_from_pdf,
)
from .manipulation import (
    merge_pdfs as merge_pdfs,
)
from .manipulation import (
    parse_pages as parse_pages,
)
from .manipulation import (
    split_pdf_pages as split_pdf_pages,
)
from .media import (
    compute_frame_hash as compute_frame_hash,
)
from .media import (
    dedup_frames as dedup_frames,
)
from .media import (
    extract_video_frames as extract_video_frames,
)
from .media import (
    extract_youtube_video_id as extract_youtube_video_id,
)
from .media import (
    fetch_youtube_transcript as fetch_youtube_transcript,
)
from .media import (
    find_ffmpeg_bin as find_ffmpeg_bin,
)
from .media import (
    format_lesson_notes as format_lesson_notes,
)
from .media import (
    format_whisper_transcript as format_whisper_transcript,
)
from .media import (
    group_transcript_segments as group_transcript_segments,
)
from .pipeline import (
    PDFProcessingError as PDFProcessingError,
)
from .pipeline import (
    PDFProcessingPipeline as PDFProcessingPipeline,
)
from .pipeline import (
    ProcessingResult as ProcessingResult,
)
from .vision import TileResult as TileResult
from .vision import VisionOptimizer as VisionOptimizer

__all__ = [
    # === PRIMARY DEEP SEAM (recommended entry point) ===
    # Use PDFProcessingPipeline.process(pdf_path, output_dir) for all PDF prep tasks.
    # Sub-modules (PDFAnalyzer, VisionOptimizer, etc.) are internal implementation
    # details and should NOT be imported directly by callers outside this package.
    "PDFProcessingPipeline",
    "ProcessingResult",
    "PDFProcessingError",
    # === PUBLIC DTOs (returned by PDFProcessingPipeline.process()) ===
    # These are stable data types needed to read the pipeline output.
    "PDFReport",
    "PDFCategory",
    "Segment",
    "PageDetail",
    # === DOCUMENT SKILLS (standalone utilities for PDF forms) ===
    "get_field_info",
    "fill_pdf_fields",
    # === PDF MANIPULATION DEEP SEAMS (Merge, Split, Extract) ===
    "merge_pdfs",
    "split_pdf_pages",
    "extract_text_from_pdf",
    "parse_pages",
    # === MEDIA DEEP SEAMS (YouTube & Video extraction) ===
    "extract_youtube_video_id",
    "format_whisper_transcript",
    "group_transcript_segments",
    "fetch_youtube_transcript",
    "compute_frame_hash",
    "dedup_frames",
    "find_ffmpeg_bin",
    "extract_video_frames",
    "format_lesson_notes",
]

# ---------------------------------------------------------------------------
# Internals still importable for backward compatibility — but not part of the
# public API. Prefer using PDFProcessingPipeline instead of reaching into:
#   PDFAnalyzer, VisionOptimizer, TitleBlockDetector, CompositeBuilder,
#   TitleBlockRegion, TileResult, split_pdf, get_blind_chunks,
#   render_page_to_image
# ---------------------------------------------------------------------------
