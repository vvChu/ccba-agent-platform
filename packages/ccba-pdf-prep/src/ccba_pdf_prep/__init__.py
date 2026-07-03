from .composite import CompositeBuilder
from .core import (
    PageDetail,
    PDFAnalyzer,
    PDFCategory,
    PDFReport,
    Segment,
    get_blind_chunks,
    split_pdf,
    render_page_to_image,
)
from .document_skills.pdf_forms import fill_pdf_fields, get_field_info
from .document_skills.xlsx_recalc import recalc_xlsx
from .pipeline import PDFProcessingError, PDFProcessingPipeline, ProcessingResult
from .vision import TileResult, TitleBlockDetector, TitleBlockRegion, VisionOptimizer

__all__ = [
    # pipeline (primary entry point)
    "PDFProcessingPipeline",
    "ProcessingResult",
    "PDFProcessingError",
    # core
    "PDFAnalyzer",
    "PDFCategory",
    "PDFReport",
    "Segment",
    "PageDetail",
    "split_pdf",
    "get_blind_chunks",
    "render_page_to_image",

    # vision
    "VisionOptimizer",
    "TileResult",
    "TitleBlockRegion",
    "TitleBlockDetector",
    # composite
    "CompositeBuilder",
    # document_skills
    "get_field_info",
    "fill_pdf_fields",
    "recalc_xlsx",
]
