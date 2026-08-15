# ccba-legal-intel Package Guidance

Autonomous Vietnamese construction legal intelligence, TVPL crawl coordination, and AST checklist generation.

- **Public Deep Seams**: `from ccba_legal import LegalIntelPipeline, LegalProcessor, LegalSyncEngine, LegalRegistryManager, LegalGroundingGate, OKFBundlePackager`.
- **Contracts**: Chrome CDP crawlers MUST use `TVPLSessionMutex` and `CookieVault` to prevent session conflict and rate limits.
- **Scoped Tests**: `pytest packages/ccba-legal-intel/tests`
