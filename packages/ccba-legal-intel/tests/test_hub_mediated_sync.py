"""Test Hub-mediated discovery and Hard Completion Lock in ccba_legal."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from ccba_legal.cli import handle_sync
from ccba_legal.federated_rag import FederatedLegalEngine
from ccba_legal.sync import LegalSyncEngine

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_find_local_knowledge_corpus_via_hub_path(tmp_path: Path) -> None:
    """Xác minh LegalSyncEngine tự động tìm ccba-legal-knowledge qua hub_path trong workspace_context.yaml."""
    # 1. Tạo mock ccba-legal-knowledge
    knowledge_dir = tmp_path / "isolated_drive" / "my_legal_knowledge"
    (knowledge_dir / "legal_docs").mkdir(parents=True, exist_ok=True)

    # 2. Tạo mock Hub
    hub_dir = tmp_path / "my_hub"
    (hub_dir / ".md" / "data").mkdir(parents=True, exist_ok=True)
    spoke_reg = {
        "spokes": [
            {
                "name": "ccba-legal-knowledge",
                "archetype": "knowledge_corpus",
                "path": str(knowledge_dir),
            }
        ]
    }
    with open(
        hub_dir / ".md" / "data" / "spoke_registry_decrypted.yaml", "w", encoding="utf-8"
    ) as f:
        yaml.safe_dump(spoke_reg, f)

    # 3. Tạo mock Spoke chỉ chứa workspace_context.yaml có hub_path
    spoke_dir = tmp_path / "my_spoke"
    (spoke_dir / ".md").mkdir(parents=True, exist_ok=True)
    ctx_data = {
        "project": {
            "name": "my-project",
            "hub_path": str(hub_dir),
        }
    }
    with open(spoke_dir / ".md" / "workspace_context.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(ctx_data, f)

    # 4. Kiểm tra discovery
    engine = LegalSyncEngine(project_root=spoke_dir)
    discovered = engine.find_local_knowledge_corpus()
    assert discovered is not None
    assert discovered.resolve() == knowledge_dir.resolve()


def test_cli_handle_sync_fails_when_zero_bundles(capsys) -> None:
    """Xác minh handle_sync trả về exit code 1 khi không có bundle nào được kéo về máy (ADR-0058)."""
    fake_args = argparse.Namespace(
        output_dir=None,
        doc=None,
        source_corpus=None,
        skip_registry_merge=False,
        to_notebooklm=False,
        notebook_id=None,
        clean_drive=False,
        download_pdf=False,
        use_drive=False,
        drive_folder_id=None,
    )

    with patch("ccba_legal.sync.LegalSyncEngine") as mock_engine_cls:
        mock_instance = MagicMock()
        # Giả lập trả về fallback_cloud_vault với 0 bundles
        mock_instance.pull_latest_okf_bundles.return_value = {
            "status": "fallback_cloud_vault",
            "tier": "tier_2_cloud_vault",
            "message": "Không tìm thấy kho tri thức cục bộ",
            "bundles_synced": [],
        }
        mock_engine_cls.return_value = mock_instance

        exit_code = handle_sync(fake_args)
        assert exit_code == 1

        captured = capsys.readouterr()
        assert "CHƯA hoàn tất" in captured.out or "CHƯA hoàn tất" in captured.err


def test_federated_rag_discovers_spoke_cwd(tmp_path: Path, monkeypatch) -> None:
    """Xác minh FederatedLegalEngine phát hiện .md/legal_docs từ thư mục làm việc hiện tại (Spoke)."""
    fake_spoke = tmp_path / "active_spoke"
    bundle_dir = fake_spoke / ".md" / "legal_docs" / "01_vbpl" / "test_law"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "metadata.yaml").write_text("id: TEST\n", encoding="utf-8")

    monkeypatch.chdir(fake_spoke)

    engine = FederatedLegalEngine(embedding_enabled=False)
    discovered_bundles = engine._resolve_corpus_paths()
    assert any(b.resolve() == bundle_dir.resolve() for b in discovered_bundles)
