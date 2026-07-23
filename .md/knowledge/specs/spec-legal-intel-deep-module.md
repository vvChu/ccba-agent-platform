# Spec: Legal Intelligence Deep Module Refactor (Cải Tiến Kiến Trúc Seam Sâu LegalIntelPipeline)

## Problem Statement

The `ccba-legal-intel` domain logic (crawling Vietnamese legal documents, managing Chrome CDP debug sessions, document intake, parsing, and OKF bundle packaging) is currently fragmented across multiple helper modules in `packages/ccba-legal-intel/ccba_legal` and top-level scripts (`scripts/legal_intelligence.py` & `scripts/legal_sync.py`).

Callers—including AI Agents, automated workflows, and CLI scripts—must explicitly orchestrate low-level operations such as checking Chrome debug port 9222, spawning Chrome subprocesses, managing 3-tier document retrieval fallbacks, and handling raw JSON output formatting. This shallow module structure creates architectural friction, lowers code locality, forces maintainers to edit multiple files when updating crawling policies, and makes unit testing difficult due to the need to mock multiple disconnected helper functions.

## Solution

Consolidate the entire legal document processing lifecycle into a single **Deep Module Seam**: `LegalIntelPipeline` located within `ccba_legal.coordinator`.

1. **Deep Seam (`LegalIntelPipeline`)**: Encapsulates Chrome CDP port detection, auto-launching, `TVPLSessionMutex` lock management, 3-tier document retrieval fallback, parsing, OKF bundle packaging, and registry updates behind a single high-level interface: `process_document(url_or_id)`.
2. **Thin CLI Adapters**: Refactor `scripts/legal_intelligence.py` and `scripts/legal_sync.py` into thin entry points (5-10 lines) that delegate argument parsing and execution directly to `LegalIntelPipeline`.
3. **Locality & Testability**: Centralize all CDP session locking, retry policies, and error recovery within `ccba_legal.coordinator`, enabling clean behavioral unit testing through a single, mockable seam.

## User Stories

1. As a legal AI agent, I want a single high-level `process_document(url_or_id)` method to crawl and package legal documents, so that I do not need to manage Chrome CDP debug ports or subprocess lifecycle logic.
2. As a platform developer, I want Chrome CDP port detection and browser auto-launch logic to be encapsulated inside `LegalIntelPipeline`, so that changes to debugging endpoints do not break top-level scripts.
3. As a maintainer, I want retry policies and 3-tier document retrieval fallbacks concentrated in one module, so that fixing crawling or parsing issues requires modifying only one file.
4. As a test engineer, I want to test the complete legal processing pipeline by mocking a single `LegalIntelPipeline` interface, so that test setups are simple, fast, and resilient to internal refactoring.
5. As a CLI user, I want `scripts/legal_intelligence.py` to provide consistent console and JSON output while delegating all execution logic to the underlying package.
6. As a system administrator, I want `TVPLSessionMutex` locking automatically enforced inside the deep seam, so that concurrent crawling attempts never cause duplicate VIP login errors on Thư viện Pháp luật (TVPL).
7. As a downstream Spoke developer, I want to import `from ccba_legal import LegalIntelPipeline` directly, so that legal intelligence capabilities can be easily embedded into custom project tools.

## Implementation Decisions

- **Deep Module Architecture**:
  - Class: `LegalIntelPipeline` defined in `packages/ccba-legal-intel/ccba_legal/coordinator.py`.
  - Interface: `process_document(url_or_doc_id: str, force_refresh: bool = False) -> LegalProcessResult`
  - Encapsulated components: Internal instances of `ChromeCDP`, `intake`, `crawler`, `parser`, `packager`, and `registry`.
- **CLI Thin Adapters**:
  - `scripts/legal_intelligence.py`: Refactored to parse CLI arguments and pass them to `LegalIntelPipeline().run_cli()`.
  - `scripts/legal_sync.py`: Updated to use `LegalIntelPipeline` for document synchronization.
- **Mutex & Session Safety**:
  - `TVPLSessionMutex` lock acquisition and cleanup are managed via a standard Python context manager inside `LegalIntelPipeline`.
- **Data Shapes**:
  - `LegalProcessResult`: A structured dataclass containing `doc_id`, `bundle_path`, `status`, and `metadata`.

## Testing Decisions

- **Seam Selection**:
  - Test at the highest seam available: the `LegalIntelPipeline` interface.
  - Tests will verify external behavior (`process_document` given a valid URL produces a valid OKF bundle file on disk) without making assertions about internal private helper methods.
- **Mocking Strategy**:
  - Provide an in-memory or fixture-based mock for `ChromeCDP` that can be passed to `LegalIntelPipeline` during testing, eliminating network and browser dependencies in offline test environments.
- **Prior Art**:
  - Follows the deep seam pattern used by `AIClient` in `packages/ccba-ai` and `NotebookLMClient` in `packages/ccba-notebooklm`.

## Out of Scope

- Rewriting the underlying HTML DOM parsing algorithms or changing the OKF bundle file format schema.
- Modifying third-party Chrome CDP network protocol implementations.

## Further Notes

- Aligns 100% with the architectural review and visual report generated in `architecture-review-20260722_162600.html`.
- Preserves full backward compatibility for all existing command-line arguments in `scripts/legal_intelligence.py`.
