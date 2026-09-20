# ccba-pdf-prep Package Guidance

High-performance PDF preprocessor for LLMs, vision segmenting, tiling, and title block extraction.

- **Public Deep Seams**: `from ccba_pdf_prep import PDFProcessingPipeline, ProcessingResult, render_page_to_image_stream, extract_pdf_pages_stream` (`pipeline.process(pdf_path, output_dir)`).
- **Contracts**: External callers must interact via `PDFProcessingPipeline`. Sub-modules (`PDFAnalyzer`, `VisionOptimizer`, etc.) are internal.
- **Scoped Tests**: `pytest packages/ccba-pdf-prep/tests`
