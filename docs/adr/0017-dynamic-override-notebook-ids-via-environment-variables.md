# 17. Dynamic Override of Notebook IDs via Environment Variables

We decided to support dynamic overriding of Google Notebook IDs via system environment variables, using the naming convention `NOTEBOOKLM_<BUNDLE_NAME_UPPER>_ID` (e.g., `NOTEBOOKLM_CORE_ID`, `NOTEBOOKLM_QC_ID`). 

This approach decouples our configuration from hardcoded IDs in git-tracked files like `catalog.yaml`. In multi-developer or CI/CD pipelines where different Google accounts (or Workspaces) are used, developers can seamlessly redirect RAG processes to different notebooks without modifying the codebase. The engine will dynamically detect the environment variables first, falling back to the default values specified in `catalog.yaml` if not found.
