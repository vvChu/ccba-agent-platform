"""test_router.py - Unit tests for dynamic RAG routing logic."""

import tempfile
from pathlib import Path

import pytest
import yaml  # type: ignore

# We will import the routing functions from ccba_notebooklm._registry
from ccba_notebooklm._registry import get_notebook_id_for_workflow, route_session_to_workflow


@pytest.fixture
def mock_catalog() -> tuple[Path, dict]:
    """Create a temporary mock catalog.yaml for testing."""
    catalog_data = {
        "notebook_ids": {
            "_core": "nb-mock-core",
            "_software": "nb-mock-software",
            "_qc": "nb-mock-qc",
        },
        "workflows": [
            {"name": "ccba-new-feature", "bundle": "_core"},
            {"name": "ccba-ai-qc-pccc-audit", "bundle": "_qc"},
            {"name": "ccba-invalid-wf"},  # No bundle field
        ],
    }
    with tempfile.TemporaryDirectory() as temp_dir:
        catalog_path = Path(temp_dir) / "catalog.yaml"
        with open(catalog_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(catalog_data, f)
        yield catalog_path, catalog_data


def test_get_notebook_id_for_workflow(mock_catalog) -> None:
    """Verify that the correct notebook_id is retrieved based on workflow bundle."""
    catalog_path, _ = mock_catalog

    # Case 1: Core workflow
    nb_id = get_notebook_id_for_workflow("ccba-new-feature", catalog_path)
    assert nb_id == "nb-mock-core"

    # Case 2: QC workflow
    nb_id = get_notebook_id_for_workflow("ccba-ai-qc-pccc-audit", catalog_path)
    assert nb_id == "nb-mock-qc"

    # Case 3: Workflow without bundle (should fallback to _core)
    nb_id = get_notebook_id_for_workflow("ccba-invalid-wf", catalog_path)
    assert nb_id == "nb-mock-core"

    # Case 4: Non-existent workflow (should fallback to _core)
    nb_id = get_notebook_id_for_workflow("non-existent-wf", catalog_path)
    assert nb_id == "nb-mock-core"


def test_route_session_to_workflow(mock_catalog, monkeypatch) -> None:
    """Verify that route_session_to_workflow saves the correct ID to context."""
    catalog_path, _ = mock_catalog

    with tempfile.TemporaryDirectory() as temp_dir:
        context_file = Path(temp_dir) / "workspace_context.yaml"
        # Monkeypatch the CONTEXT_FILE constant in _registry
        monkeypatch.setattr("ccba_notebooklm._registry.CONTEXT_FILE", context_file)

        # Route to QC workflow
        nb_id = route_session_to_workflow("ccba-ai-qc-pccc-audit", catalog_path)
        assert nb_id == "nb-mock-qc"

        # Verify context file was updated
        assert context_file.exists()
        with open(context_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            assert data["project"]["notebook_id"] == "nb-mock-qc"
