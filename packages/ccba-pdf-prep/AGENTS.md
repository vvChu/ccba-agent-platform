# ccba-pdf-prep Package Guidance

High-performance PDF preprocessor for LLMs, vision segmenting, tiling, and title block extraction.

- **Public Deep Seams**: `ccba_pdf_prep.pipeline.PDFProcessingPipeline` (`pipeline.process(pdf_path, output_dir)`).
- **Contracts**: External callers must interact via `PDFProcessingPipeline`. Sub-modules (`PDFAnalyzer`, `VisionOptimizer`, etc.) are internal.
- **Scoped Tests**: `pytest packages/ccba-pdf-prep/tests`
