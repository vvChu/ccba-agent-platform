from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from ccba_legal.sync import LegalSyncEngine, sync_legal_assets

pytestmark = [pytest.mark.fast, pytest.mark.unit]


@pytest.fixture
def mock_knowledge_corpus(tmp_path: Path) -> Path:
    """Create a temporary mock ccba-legal-knowledge repository structure."""
    corpus = tmp_path / "mock_ccba_legal_knowledge"
    corpus.mkdir(parents=True, exist_ok=True)

    # 1. OKF bundles in legal_docs/
    bundle_01 = corpus / "legal_docs" / "01_vbpl" / "luat_xay_dung_2025_so_135_2025_qh15"
    bundle_01.mkdir(parents=True, exist_ok=True)
    (bundle_01 / "luat_xay_dung_2025_so_135_2025_qh15.md").write_text(
        "# Luật Xây dựng 2025", encoding="utf-8"
    )
    (bundle_01 / "metadata.yaml").write_text(
        "id: LXD-2025\ndocument_number: 135/2025/QH15", encoding="utf-8"
    )
    (bundle_01 / "clauses.json").write_text('{"clauses": []}', encoding="utf-8")
    (bundle_01 / "sources").mkdir(exist_ok=True)
    (bundle_01 / "sources" / "dummy.docx").write_text("docx binary", encoding="utf-8")

    bundle_02 = corpus / "legal_docs" / "02_qcvn" / "qcvn_06_2022_bxd"
    bundle_02.mkdir(parents=True, exist_ok=True)
    (bundle_02 / "qcvn_06_2022_bxd.md").write_text("# QCVN 06:2022/BXD", encoding="utf-8")

    # 2. Master legal registry in .md/data/
    reg_dir = corpus / ".md" / "data"
    reg_dir.mkdir(parents=True, exist_ok=True)
    master_reg = {
        "laws": [
            {
                "id": "LXD-2025",
                "document_number": "135/2025/QH15",
                "short_name": "Luật XD 2025",
                "status": "ACTIVE",
            }
        ]
    }
    with open(reg_dir / "legal_registry.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(master_reg, f)

    return corpus


def test_find_local_knowledge_corpus_explicit_and_env(
    mock_knowledge_corpus: Path, tmp_path: Path
) -> None:
    """Verify discovery of local knowledge corpus via explicit path and environment variable."""
    spoke_root = tmp_path / "spoke_project"
    spoke_root.mkdir()

    engine = LegalSyncEngine(project_root=spoke_root)

    # 1. Explicit path
    found = engine.find_local_knowledge_corpus(mock_knowledge_corpus)
    assert found == mock_knowledge_corpus.resolve()

    # 2. Env variable
    os.environ["CCBA_LEGAL_KNOWLEDGE_PATH"] = str(mock_knowledge_corpus)
    try:
        found_env = engine.find_local_knowledge_corpus()
        assert found_env == mock_knowledge_corpus.resolve()
    finally:
        del os.environ["CCBA_LEGAL_KNOWLEDGE_PATH"]


def test_pull_latest_okf_bundles_tier_1(mock_knowledge_corpus: Path, tmp_path: Path) -> None:
    """Verify pull_latest_okf_bundles syncs OKF bundles and updates registry non-destructively."""
    spoke_root = tmp_path / "spoke_project"
    spoke_root.mkdir()

    # Setup initial local spoke registry
    local_reg_dir = spoke_root / ".md" / "data"
    local_reg_dir.mkdir(parents=True, exist_ok=True)
    local_reg = {
        "laws": [
            {
                "id": "LXD-2014",
                "document_number": "50/2014/QH13",
                "notes": "Custom note for spoke",
            }
        ]
    }
    with open(local_reg_dir / "legal_registry.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(local_reg, f)

    engine = LegalSyncEngine(project_root=spoke_root)
    result = engine.pull_latest_okf_bundles(
        target_dir=spoke_root / "legal_docs",
        source_corpus_dir=mock_knowledge_corpus,
        update_registry=True,
    )

    assert result["status"] == "success"
    assert result["tier"] == "tier_1_local_corpus"
    assert len(result["bundles_synced"]) == 2

    # Check that bundle was created in spoke target
    synced_doc = spoke_root / "legal_docs" / "01_vbpl" / "luat_xay_dung_2025_so_135_2025_qh15"
    assert synced_doc.exists()
    assert (synced_doc / "luat_xay_dung_2025_so_135_2025_qh15.md").exists()
    assert (synced_doc / "metadata.yaml").exists()
    assert (synced_doc / "sources" / "dummy.docx").exists()

    # Check registry merge
    with open(local_reg_dir / "legal_registry.yaml", encoding="utf-8") as f:
        merged = yaml.safe_load(f)

    assert any(law["id"] == "LXD-2025" for law in merged["laws"])
    law_2014 = next(law for law in merged["laws"] if law["id"] == "LXD-2014")
    assert law_2014["notes"] == "Custom note for spoke"


def test_sync_legal_assets_helper(mock_knowledge_corpus: Path, tmp_path: Path) -> None:
    """Verify top-level sync_legal_assets convenience function."""
    spoke_root = tmp_path / "spoke_helper_test"
    spoke_root.mkdir()

    res = sync_legal_assets(
        target_dir=spoke_root / "legal_docs",
        source_corpus_dir=mock_knowledge_corpus,
        project_root=spoke_root,
    )
    assert res["status"] == "success"
    assert len(res["bundles_synced"]) == 2


def test_cli_sync_subcommand(mock_knowledge_corpus: Path, tmp_path: Path) -> None:
    """Verify python -m ccba_legal sync --pull-latest works via CLI."""
    spoke_target = tmp_path / "cli_synced_docs"

    cmd = [
        sys.executable,
        "-m",
        "ccba_legal",
        "sync",
        "--pull-latest",
        "-o",
        str(spoke_target),
        "--source-corpus",
        str(mock_knowledge_corpus),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0, f"CLI stderr: {res.stderr}"
    assert "AUTOMATED LEGAL KNOWLEDGE SYNC" in res.stdout
    assert "1-Click Legal Sync Completed Successfully!" in res.stdout
    assert spoke_target.exists()
