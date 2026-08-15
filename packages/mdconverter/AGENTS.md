# mdconverter Package Guidance

High-fidelity document-to-markdown converter supporting multiple OCR/Vision backends with table reconstruction.

- **Public Deep Seams**: `mdconverter.convert`, `mdconverter.providers`.
- **Contracts**: Table reconstruction and relative link patching are automatically dispatched on raw markdown outputs.
- **Scoped Tests**: `pytest packages/mdconverter/tests`
