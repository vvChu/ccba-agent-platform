# ccba-notebooklm Package Guidance

Unified NotebookLM client and deep service seam for source orchestration, RAG, and artifact retrieval.

- **Public Deep Seams**: `ccba_notebooklm._service.NotebookLMService`, `ccba_notebooklm.client.NotebookLMClient`.
- **Contracts**: Use flat deep seam API, SHA-256 registry caching for source deduplication, and dynamic notebook ID overrides.
- **Scoped Tests**: `pytest packages/ccba-notebooklm/tests`
