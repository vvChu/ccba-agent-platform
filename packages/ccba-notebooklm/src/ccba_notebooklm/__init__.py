"""CCBA NotebookLM — Deep Seam wrapper cho Google NotebookLM.

Public Interface (2 tầng):

Tier 1 — Transport & Auth:
    CCBANotebookLMClient, NotebookLMClient (alias), get_client, check_auth,
    HAS_NOTEBOOKLM

Tier 2 — Orchestration Workflows (entry points cho CLI và scripts):
    handle_artifact_flow, extract_and_summarize, query_rag,
    get_or_create_project_notebook, get_source_id_by_path,
    list_notebooks, list_sources, delete_notebook, delete_source,
    share_notebook

Internal modules (import trực tiếp khi cần):
    ccba_notebooklm._registry  — state persistence, context, routing
    ccba_notebooklm._security  — maskara privacy gate
    ccba_notebooklm._gc        — quota check, garbage collection
"""

# --- Tier 1: Transport & Auth ---
from ._client import (
    HAS_NOTEBOOKLM,
    CCBANotebookLMClient,
    check_auth,
    get_client,
)

# --- Tier 2: Orchestration Workflows ---
from ._artifacts import (
    delete_notebook,
    delete_source,
    extract_and_summarize,
    get_or_create_project_notebook,
    get_source_id_by_path,
    handle_artifact_flow,
    list_notebooks,
    list_sources,
    query_rag,
    share_notebook,
)

# Alias for backward compatibility
NotebookLMClient = CCBANotebookLMClient

# ---------------------------------------------------------------------------
# Public API — only these symbols are part of the stable interface.
# Internal utilities (_registry, _security, _gc) are accessible via their
# full module path (e.g. ``from ccba_notebooklm._registry import read_registry``)
# but are NOT part of __all__ and may change without notice.
# ---------------------------------------------------------------------------
__all__ = [
    # Tier 1 — Transport & Auth
    "HAS_NOTEBOOKLM",
    "CCBANotebookLMClient",
    "NotebookLMClient",
    "check_auth",
    "get_client",
    # Tier 2 — Orchestration Workflows
    "delete_notebook",
    "delete_source",
    "extract_and_summarize",
    "get_or_create_project_notebook",
    "get_source_id_by_path",
    "handle_artifact_flow",
    "list_notebooks",
    "list_sources",
    "query_rag",
    "share_notebook",
]
