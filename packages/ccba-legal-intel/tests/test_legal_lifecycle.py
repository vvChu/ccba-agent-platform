from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from ccba_legal.models import (
    LegalDocStatus,
    normalize_doc_status,
)
from ccba_legal.registry import (
    LegalRegistryManager,
    get_lifecycle,
    query,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_normalize_doc_status() -> None:
    """Verify normalize_doc_status accurately handles legacy and localized status strings."""
    assert normalize_doc_status("current") == LegalDocStatus.ACTIVE
    assert normalize_doc_status("enacted") == LegalDocStatus.ACTIVE
    assert normalize_doc_status("ACTIVE") == LegalDocStatus.ACTIVE
    assert normalize_doc_status("Hiệu lực") == LegalDocStatus.ACTIVE

    assert normalize_doc_status("superseded") == LegalDocStatus.SUPERSEDED
    assert normalize_doc_status("expired") == LegalDocStatus.SUPERSEDED
    assert normalize_doc_status("Hết hiệu lực") == LegalDocStatus.SUPERSEDED

    assert normalize_doc_status("partially_amended") == LegalDocStatus.PARTIALLY_AMENDED
    assert normalize_doc_status("amended") == LegalDocStatus.PARTIALLY_AMENDED

    assert normalize_doc_status("pending_effective") == LegalDocStatus.PENDING_EFFECTIVE
    assert normalize_doc_status("draft") == LegalDocStatus.DRAFT
    assert normalize_doc_status(None) == LegalDocStatus.ACTIVE


def test_get_lifecycle_superseded_warning() -> None:
    """Verify get_lifecycle attaches prominent warning and replacement for superseded documents."""
    sample_data = {
        "laws": [
            {
                "id": "LXD-2014",
                "document_number": "50/2014/QH13",
                "short_name": "Luật XD 2014",
                "title": "Luật Xây dựng 2014",
                "status": "SUPERSEDED",
                "superseded_date": "2026-07-01",
                "superseded_by": "135/2025/QH15",
            },
            {
                "id": "LXD-2025",
                "document_number": "135/2025/QH15",
                "short_name": "Luật XD 2025",
                "title": "Luật Xây dựng 2025",
                "status": "ACTIVE",
                "effective_date": "2026-07-01",
                "supersedes": ["50/2014/QH13"],
            },
        ]
    }

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w", encoding="utf-8") as f:
        yaml.safe_dump(sample_data, f)
        temp_path = Path(f.name)

    try:
        mgr = LegalRegistryManager(registry_path=temp_path)
        info_2014 = mgr.get_lifecycle("50/2014/QH13")

        assert info_2014["status"] == LegalDocStatus.SUPERSEDED.value
        assert "HẾT HIỆU LỰC" in info_2014["warning"]
        assert "135/2025/QH15" in info_2014["warning"]
        assert info_2014["suggested_replacement"] is not None
        assert info_2014["suggested_replacement"]["document_number"] == "135/2025/QH15"

        info_2025 = mgr.get_lifecycle("LXD-2025")
        assert info_2025["status"] == LegalDocStatus.ACTIVE.value
        assert info_2025["warning"] is None

        # Test top-level get_lifecycle helper
        direct_info = get_lifecycle("LXD-2014", registry_path=temp_path)
        assert direct_info["status"] == LegalDocStatus.SUPERSEDED.value
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_search_and_query_enriches_lifecycle() -> None:
    """Verify search and query annotate search results with lifecycle status and warnings."""
    sample_data = {
        "laws": [
            {
                "id": "LXD-2014",
                "document_number": "50/2014/QH13",
                "short_name": "Luật XD 2014",
                "title": "Luật Xây dựng 2014",
                "status": "SUPERSEDED",
                "superseded_by": "135/2025/QH15",
                "topics": ["construction"],
            },
        ]
    }

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w", encoding="utf-8") as f:
        yaml.safe_dump(sample_data, f)
        temp_path = Path(f.name)

    try:
        # Without include_expired, superseded document is excluded by default
        assert len(query("50/2014", registry_path=temp_path)) == 0

        # With include_expired=True, superseded document is returned and enriched
        results = query("50/2014", registry_path=temp_path, include_expired=True)
        assert len(results) >= 1
        res = results[0]
        assert res["status"] == LegalDocStatus.SUPERSEDED.value
        assert res["is_superseded"] is True
        assert "lifecycle_warning" in res
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_non_destructive_registry_merge() -> None:
    """Verify merge_with_master_registry updates SSOT metadata while preserving local custom notes."""
    local_data = {
        "metadata": {"project": "Spoke Project A"},
        "laws": [
            {
                "id": "LXD-2014",
                "document_number": "50/2014/QH13",
                "short_name": "Luật XD 2014",
                "status": "current",
                "notes": "Custom Spoke Note: Verified with Client 2026-05",
                "custom_project_tag": "tag_alpha",
            }
        ],
        "decrees": [
            {
                "id": "ND-LOCAL-CUSTOM",
                "document_number": "99/2026/ND-CP",
                "title": "Local Custom Project Decree",
            }
        ],
    }

    master_data = {
        "laws": [
            {
                "id": "LXD-2014",
                "document_number": "50/2014/QH13",
                "short_name": "Luật XD 2014",
                "status": "SUPERSEDED",
                "superseded_by": "135/2025/QH15",
                "superseded_date": "2026-07-01",
            },
            {
                "id": "LXD-2025",
                "document_number": "135/2025/QH15",
                "short_name": "Luật XD 2025",
                "status": "ACTIVE",
                "effective_date": "2026-07-01",
            },
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        reg_path = Path(tmpdir) / ".md" / "data" / "legal_registry.yaml"
        reg_path.parent.mkdir(parents=True, exist_ok=True)
        with open(reg_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(local_data, f)

        mgr = LegalRegistryManager(registry_path=reg_path)
        summary = mgr.merge_with_master_registry(master_data, backup=True)

        assert summary["updated"] == 1
        assert summary["added"] == 1

        merged = mgr.load()
        laws = merged["laws"]
        law_2014 = next(law for law in laws if law["id"] == "LXD-2014")
        assert law_2014["status"] == "SUPERSEDED"
        assert law_2014["superseded_by"] == "135/2025/QH15"
        assert law_2014["notes"] == "Custom Spoke Note: Verified with Client 2026-05"
        assert law_2014["custom_project_tag"] == "tag_alpha"

        # Verify added doc
        assert any(law["id"] == "LXD-2025" for law in laws)

        # Verify local-only custom decree was preserved
        assert any(d["id"] == "ND-LOCAL-CUSTOM" for d in merged["decrees"])

        # Verify backup was created
        backup_dir = Path(tmpdir) / ".md" / "backups"
        assert backup_dir.exists()
        bak_files = list(backup_dir.glob("legal_registry.yaml.bak_*"))
        assert len(bak_files) == 1
