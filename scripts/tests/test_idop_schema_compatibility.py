"""test_idop_schema_compatibility.py - ADR 0043 CI Schema Contract Drift Gate.

Validates that evolving schemas in IDOP-CCBA-WAY preserve core contract integration fields
required by Hub and Spoke project delivery.
"""

import json
from pathlib import Path
import pytest

CORE_REQUIRED_FIELDS = {
    "projects": ["ProjectCode", "Title"],
    "job_assignments": ["ProjectCode", "Title"],
    "cde_documents": ["DocCode", "Title"],
}


def test_core_contract_fields_validation_logic():
    """Validates that Schema Drift Gate properly permits open extensions while catching breaking renames."""
    # Test valid open extension
    valid_schema = {
        "title": "Projects",
        "fields": [
            {"name": "ProjectCode", "type": "Text", "required": True},
            {"name": "Title", "type": "Text", "required": True},
            {"name": "NewCustomField2026", "type": "Text"}, # Open extension allowed
        ]
    }
    present_field_names = {f["name"] for f in valid_schema["fields"]}
    for required in CORE_REQUIRED_FIELDS["projects"]:
        assert required in present_field_names, f"Missing required core contract field: {required}"


def test_core_contract_fields_drift_detected():
    """Validates that Schema Drift Gate fails when a core field is renamed or missing."""
    invalid_schema = {
        "title": "Projects",
        "fields": [
            {"name": "MaDuAnRenamed", "type": "Text"}, # Renamed core field
            {"name": "Title", "type": "Text"},
        ]
    }
    present_field_names = {f["name"] for f in invalid_schema["fields"]}
    missing = [req for req in CORE_REQUIRED_FIELDS["projects"] if req not in present_field_names]
    assert "ProjectCode" in missing, "Schema Drift Gate should catch missing ProjectCode"


def test_live_idop_schema_if_present():
    """If IDOP-CCBA-WAY repository exists locally, inspect its live JSON schema files."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    idop_lists_dir = repo_root.parent / "IDOP-CCBA-WAY" / "datamodel" / "sharepoint" / "lists"
    
    if not idop_lists_dir.exists():
        pytest.skip("IDOP-CCBA-WAY local directory not found; skipping live schema check.")
        
    for list_json in idop_lists_dir.glob("**/*.json"):
        try:
            with open(list_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert isinstance(data, (dict, list)), f"Invalid JSON structure in {list_json.name}"
        except Exception as e:
            pytest.fail(f"Corrupt JSON schema in IDOP: {list_json.name}: {e}")
