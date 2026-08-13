"""
Service layer for CCBA NotebookLM integration.
Provides high-level orchestration for sources, SHA-256 caching, security gating, and RAG/Artifact flows.
"""

from pathlib import Path

from ._client import CCBANotebookLMClient
from ._registry import get_file_sha256, normalize_to_relative, read_registry, update_registry
from ._security import run_maskara_gate


class NotebookLMService:
    """High-level service orchestrator for NotebookLM workflows."""

    def __init__(self, client: CCBANotebookLMClient) -> None:
        self.client = client

    async def ensure_source(self, notebook_id: str, source_path: str) -> str:
        """Ensure a local file or URL source exists in the given cloud notebook and is up to date.

        Calculates SHA-256 hash, checks registry cache, removes outdated cloud source if SHA-256 mismatched,
        runs Maskara security gate lazily if upload is required, uploads the new source, and updates registry.

        Args:
            notebook_id: Target cloud notebook ID.
            source_path: Local file path or URL.

        Returns:
            The registered or newly uploaded source ID.
        """
        sha256 = get_file_sha256(source_path)
        registry = read_registry()
        norm_path = normalize_to_relative(source_path)
        sources = await self.client.list_sources(notebook_id)

        if norm_path in registry:
            registered_info = registry[norm_path]
            if registered_info.get("notebook_id") == notebook_id:
                existing_id = registered_info.get("source_id")
                matched = next(
                    (src for src in sources if getattr(src, "id", None) == existing_id), None
                )
                if matched:
                    if registered_info.get("sha256") == sha256:
                        # Cache HIT — return existing source ID directly (Lazy Maskara & no re-upload)
                        return str(existing_id)
                    else:
                        # Cache MISMATCH — delete outdated source on cloud
                        await self.client.delete_source(notebook_id, str(existing_id))

        # Lazy Maskara Security Gate (called ONLY when upload is needed)
        upload_path, is_temp = run_maskara_gate(source_path)
        try:
            if source_path.startswith(("http://", "https://")):
                new_source = await self.client.add_url_source(notebook_id, upload_path, wait=True)
            else:
                new_source = await self.client.add_file_source(notebook_id, upload_path)

            source_id = str(getattr(new_source, "id", new_source))
            update_registry(source_path, source_id, sha256, notebook_id)
            return source_id
        finally:
            # Clean up temp redacted file if Maskara created one
            if is_temp:
                try:
                    p = Path(upload_path)
                    if p.exists() and "redacted_" in p.name:
                        p.unlink()
                except Exception:
                    pass
