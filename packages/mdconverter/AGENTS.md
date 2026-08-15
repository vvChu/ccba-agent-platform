# mdconverter Package Guidance

High-fidelity document-to-markdown converter supporting multiple OCR/Vision backends with table reconstruction.

- **Public Deep Seams**: `from mdconverter import ConversionPipeline, ConverterRegistry, BaseConverter, ConversionResult, get_settings`.
- **Contracts**: Table reconstruction and relative link patching are automatically dispatched on raw markdown outputs.
- **Scoped Tests**: `pytest packages/mdconverter/tests`
