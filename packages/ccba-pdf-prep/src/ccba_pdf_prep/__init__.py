"""ccba-pdf-prep — Unified PDF Preprocessor for AI Vision Pipelines.

Primary Deep Seam:
    PDFProcessingPipeline — Segment, tile, and analyze PDF drawings end-to-end.
                            Call: pipeline.process(pdf_path, output_dir)

Document Skills (standalone utilities):
    fill_pdf_fields  — Fill interactive PDF form fields programmatically.
    get_field_info   — Inspect PDF form field metadata.
    recalc_xlsx      — Recalculate Excel formulas headlessly via LibreOffice.
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
from .document_skills.xlsx_recalc import recalc_xlsx as recalc_xlsx
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
    # === DOCUMENT SKILLS (standalone utilities, unrelated to PDF pipeline) ===
    "get_field_info",
    "fill_pdf_fields",
    "recalc_xlsx",
]

# ---------------------------------------------------------------------------
# Internals still importable for backward compatibility — but not part of the
# public API. Prefer using PDFProcessingPipeline instead of reaching into:
#   PDFAnalyzer, VisionOptimizer, TitleBlockDetector, CompositeBuilder,
#   TitleBlockRegion, TileResult, split_pdf, get_blind_chunks,
#   render_page_to_image
# ---------------------------------------------------------------------------
