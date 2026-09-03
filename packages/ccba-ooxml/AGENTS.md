# ccba-ooxml Package Guidance

Deep module for processing, styling, and generating Microsoft Office OpenXML documents (DOCX, PPTX, XLSX).

- **Public Deep Seams**: `from ccba_ooxml import pack_document, unpack_document, validate_document, OOXMLWorkspace, recalc_xlsx, DocxDocument, StructuredTable, TableReconstructor, make_descriptive_table_slug, DeckBuilder, SlideSpec, SlideType, CardItem, CCBAPresentationTheme, build_presentation_from_markdown`.
- **Contracts**: Follow CCBA Brand Identity Guidelines ver 3.4, WCAG 2.1 contrast rules, and Decree 30 administrative document formatting standards.
- **Scoped Tests**: `pytest packages/ccba-ooxml/tests`
