# ccba-notebooklm Package Guidance

Unified NotebookLM client and deep service seam for source orchestration, RAG, and artifact retrieval.

- **Public Deep Seams**: `from ccba_notebooklm import CCBANotebookLMClient, NotebookLMClient, get_client, query_rag, handle_artifact_flow, extract_and_summarize`.
- **Contracts**: Use flat deep seam API, SHA-256 registry caching for source deduplication, and dynamic notebook ID overrides.
- **Scoped Tests**: `pytest packages/ccba-notebooklm/tests`
