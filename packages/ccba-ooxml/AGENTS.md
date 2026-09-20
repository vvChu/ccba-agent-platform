# ccba-ooxml Package Guidance

Deep module for processing, styling, and generating Microsoft Office OpenXML documents (DOCX, PPTX, XLSX).

- **Public Deep Seams**: `from ccba_ooxml import pack_document, unpack_document, validate_document, OOXMLWorkspace, recalc_xlsx, DocxDocument, StructuredTable, TableReconstructor, make_descriptive_table_slug, DeckBuilder, SlideSpec, SlideType, CardItem, CCBAPresentationTheme, build_presentation_from_markdown, WordFormFiller, FormFillConfig, TableRule, TemplateProtectionError`.
- **Contracts**: Follow CCBA Brand Identity Guidelines ver 3.4, WCAG 2.1 contrast rules, and Decree 30 administrative document formatting standards.
- **Schema & Parser Invariants**: XML schema validation operates 100% offline via `OfflineSchemaResolver` and local schemas (`schemas/dublincore/`). All parsers MUST enforce `no_network=True` and `resolve_entities=False`. Compiled `XMLSchema` instances are cached in `_COMPILED_SCHEMA_CACHE`.
- **Scoped Tests**: `pytest packages/ccba-ooxml/tests`
