"""Unit tests for Tier 2 Remote Streaming Sync for Zero-Clone Thin Clients (Issue #457 / ADR-0026 / ADR-0050)."""

from __future__ import annotations

import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from ccba_legal.sync.engine import (
    LegalSyncEngine,
    _fetch_remote_file_atomic,
)


@pytest.fixture
def mock_remote_registry_content() -> bytes:
    """Mock canonical legal_registry.yaml content."""
    reg = {
        "decrees": [
            {
                "id": "ND-207-2026",
                "slug": "nd_207_2026_quan_ly_chat_luong",
                "document_number": "207/2026/ND-CP",
                "title": "Nghi dinh 207/2026/ND-CP",
                "status": "ACTIVE",
            }
        ]
    }
    return yaml.safe_dump(reg).encode("utf-8")


def test_fetch_remote_file_atomic_success(tmp_path: Path) -> None:
    """Test _fetch_remote_file_atomic downloads and renames file atomically."""
    dest = tmp_path / "subdir" / "test_file.txt"
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b"sample content"
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        ok = _fetch_remote_file_atomic("https://example.com/test_file.txt", dest)

    assert ok is True
    assert dest.is_file()
    assert dest.read_bytes() == b"sample content"
    # Ensure no tmp files remain
    tmp_files = list(dest.parent.glob("*.tmp*"))
    assert len(tmp_files) == 0


def test_fetch_remote_file_atomic_cleanup_on_error(tmp_path: Path) -> None:
    """Test _fetch_remote_file_atomic cleans up temporary file on failure."""
    dest = tmp_path / "broken.txt"

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        ok = _fetch_remote_file_atomic("https://example.com/broken.txt", dest)

    assert ok is False
    assert not dest.exists()
    tmp_files = list(tmp_path.glob("*.tmp*"))
    assert len(tmp_files) == 0


def test_remote_streaming_sync_success(tmp_path: Path, mock_remote_registry_content: bytes) -> None:
    """Test pull_latest_okf_bundles downloads remote registry and bundles when local corpus is absent."""
    project_root = tmp_path / "thin_spoke"
    project_root.mkdir()

    engine = LegalSyncEngine(project_root=project_root)

    def mock_urlopen(req, timeout=5.0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp

        if "legal_registry.yaml" in url:
            mock_resp.read.return_value = mock_remote_registry_content
        elif "metadata.yaml" in url:
            mock_resp.read.return_value = b"id: ND-207-2026\ntables: [table_1.md]\n"
        elif "clauses.json" in url:
            mock_resp.read.return_value = b'{"clauses": []}'
        elif "document_normative.md" in url:
            mock_resp.read.return_value = b"# Nghi dinh 207/2026\n"
        elif "table_1.md" in url:
            mock_resp.read.return_value = b"| Table 1 |\n|---|---|\n"
        else:
            mock_resp.read.return_value = b"generic asset"
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        res = engine.pull_latest_okf_bundles(
            doc_ids=["ND-207-2026"],
            update_registry=True,
            pull_assets=True,
        )

    assert res["status"] == "success"
    assert res["tier"] == "tier_2_remote_streaming"
    assert "01_vbpl/nd_207_2026_quan_ly_chat_luong" in res["bundles_synced"]

    target_bundle = (
        project_root / ".md" / "legal_docs" / "01_vbpl" / "nd_207_2026_quan_ly_chat_luong"
    )
    assert (target_bundle / "metadata.yaml").is_file()
    assert (target_bundle / "clauses.json").is_file()
    assert (target_bundle / "document_normative.md").is_file()
    assert (target_bundle / "tables" / "table_1.md").is_file()

    # Local registry merged
    local_reg = project_root / ".md" / "data" / "legal_registry.yaml"
    assert local_reg.is_file()
    reg_data = yaml.safe_load(local_reg.read_text(encoding="utf-8"))
    assert any(d.get("id") == "ND-207-2026" for d in reg_data.get("decrees", []))


def test_remote_streaming_cache_hit_zero_latency(
    tmp_path: Path, mock_remote_registry_content: bytes
) -> None:
    """Test pull_latest_okf_bundles achieves 0s cache hit when bundle files already exist."""
    project_root = tmp_path / "cached_spoke"
    project_root.mkdir()

    # Pre-populate bundle cache
    bundle_dir = project_root / ".md" / "legal_docs" / "01_vbpl" / "nd_207_2026_quan_ly_chat_luong"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "metadata.yaml").write_text("id: ND-207-2026\n", encoding="utf-8")
    (bundle_dir / "clauses.json").write_text("{}", encoding="utf-8")

    engine = LegalSyncEngine(project_root=project_root)

    download_calls = []

    def mock_urlopen(req, timeout=5.0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        download_calls.append(url)
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = mock_remote_registry_content
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        res = engine.pull_latest_okf_bundles(
            doc_ids=["ND-207-2026"],
            update_registry=False,
            pull_assets=True,
        )

    assert res["status"] == "success"
    assert "01_vbpl/nd_207_2026_quan_ly_chat_luong" in res["bundles_synced"]
    # Only legal_registry.yaml should have been requested, no individual bundle files
    assert all("legal_docs" not in call for call in download_calls)


def test_remote_streaming_degraded_offline(tmp_path: Path) -> None:
    """Test pull_latest_okf_bundles returns degraded_offline status on network error without unhandled exception."""
    project_root = tmp_path / "offline_spoke"
    project_root.mkdir()

    engine = LegalSyncEngine(project_root=project_root)

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Network unreachable")):
        res = engine.pull_latest_okf_bundles(
            doc_ids=["ND-207-2026"],
            update_registry=True,
            pull_assets=True,
        )

    assert res["status"] == "degraded_offline"
    assert res["tier"] == "tier_3_cloud_rag_fallback"
    assert "CCBA_LEGAL_KNOWLEDGE_PATH" in res["message"]
    assert res["bundles_synced"] == []
