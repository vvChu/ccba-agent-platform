# Project: CCBA Legal Intel OKF Upgrade

## Architecture
The `ccba-legal-intel` package is responsible for crawling, parsing, packaging, and managing Vietnamese legal documents under the Open Knowledge Format (OKF).
- `ccba_legal/packager.py`: OKFBundlePackager creates and structures the OKF bundles.
- `ccba_legal/parser.py`: LegalAnalysisEngine parses and analyzes Vietnamese legal text.
- `ccba_legal/cleaners.py`: Text cleaning and JSON extraction helpers.
- `ccba_legal/registry.py`: LegalRegistryManager manages `legal_registry.yaml`.
- `ccba_legal/crawler.py`: ChromeCDP wrapper for downloading TVPL docs.
- `ccba_legal/monitor.py`: TokenMonitor for monitoring context window usage.
- `ccba_legal/adr.py`: Architectural Decision Record generator.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|--------------|--------|
| 1 | M1_EXPLORE | Codebase exploration and implementation strategy | None | PLANNED |
| 2 | M2_CORE_IMPLEMENT | Implement OKF core parser and packager changes (R1, R2, R4, R5, R7) | M1_EXPLORE | PLANNED |
| 3 | M3_VALIDITY_IMPLEMENT | Implement validity control, amendment warning, registry updates (R3) | M2_CORE_IMPLEMENT | PLANNED |
| 4 | M4_LINTER_UPGRADE | Upgrade the OKF Linter (R6) to validate frontmatter, links, and validity | M3_VALIDITY_IMPLEMENT | PLANNED |
| 5 | M5_VERIFY_AUDIT | E2E Testing, Reviewer validation, Challenger checks, and Forensic Audit | M4_LINTER_UPGRADE | PLANNED |

## Code Layout
- `packages/ccba-legal-intel/ccba_legal/` - Core library modules.
- `packages/ccba-legal-intel/tests/` - Unit and integration tests.
- `scripts/validate_docs.py` - Knowledge base validation and OKF linter script.

## Interface Contracts
### `OKFBundlePackager` (in `packager.py`)
- Standardized methods for creating the 3-resolution storage (`full_text.md`, `sections/`, `chunks.json`).
- Anchor insertion mechanism during packaging or text post-processing.
- Advanced table extraction, saving raw table HTMLs in `tables/`, splitting long tabular data to JSON/CSV files.
- LaTeX formula formatting and embedding Python executable code blocks.

### `LegalRegistryManager` (in `registry.py`)
- Handling status changes and tracking validity/amendment relations.
