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
from ._client import (
    HAS_NOTEBOOKLM,
    CCBANotebookLMClient,
    check_auth,
    get_client,
)

# Alias for backward compatibility
NotebookLMClient = CCBANotebookLMClient

from ._gc import (
    check_quota_and_warn,
    run_garbage_collection,
)
from ._registry import (
    get_file_sha256,
    get_notebook_id_from_context,
    read_registry,
    save_notebook_id_to_context,
    update_registry,
)
from ._security import (
    run_maskara_gate,
)

__all__ = [
    "HAS_NOTEBOOKLM",
    "CCBANotebookLMClient",
    "NotebookLMClient",
    "check_auth",
    "get_client",
    "get_file_sha256",
    "get_notebook_id_from_context",
    "save_notebook_id_to_context",
    "read_registry",
    "update_registry",
    "check_quota_and_warn",
    "run_garbage_collection",
    "run_maskara_gate",
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
