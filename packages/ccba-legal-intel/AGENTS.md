# ccba-legal-intel Package Guidance

Autonomous Vietnamese construction legal intelligence, TVPL crawl coordination, and AST checklist generation.

- **Public Deep Seams**:
  - Core Seams: `from ccba_legal import LegalKnowledgeEngine, LegalIntelPipeline, LegalProcessor, LegalSyncEngine, LegalRegistryManager, LegalGroundingGate, OKFBundlePackager, DocxCanonicalSanitizer`.
  - Cloud Ingestion Seam: `from ccba_legal.sync import GoogleDriveIngestor`.
- **Contracts**:
  - Chrome CDP crawlers MUST use `TVPLSessionMutex` and `CookieVault` to prevent session conflict and rate limits.
  - Google Drive operations MUST initialize API credentials through `ccba_legal.sync.drive_client.get_drive_service` factory, never directly instantiating client libraries.
- **Scoped Tests**: `pytest packages/ccba-legal-intel/tests`
