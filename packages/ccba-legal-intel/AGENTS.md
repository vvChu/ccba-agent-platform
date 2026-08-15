# ccba-legal-intel Package Guidance

Autonomous Vietnamese construction legal intelligence, TVPL crawl coordination, and AST checklist generation.

- **Public Deep Seams**: `ccba_legal.pipeline.LegalIntelPipeline`, `ccba_legal.adr.LegalProcessor`, `ccba_legal.sync.LegalSyncEngine`.
- **Contracts**: Chrome CDP crawlers MUST use `TVPLSessionMutex` and `CookieVault` to prevent session conflict and rate limits.
- **Scoped Tests**: `pytest packages/ccba-legal-intel/tests`
