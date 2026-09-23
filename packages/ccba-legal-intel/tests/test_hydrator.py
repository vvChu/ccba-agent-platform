"""test_hydrator.py - Unit tests for SpokeHydrator and Vault Hydration Engine."""

import hashlib
from pathlib import Path

import pytest
import yaml

from ccba_legal.hydrator import (
    AssetStatus,
    SpokeHydrator,
)


def compute_sha256(content: bytes) -> str:
    """Helper to compute sha256 of bytes."""
    return hashlib.sha256(content).hexdigest()


@pytest.fixture
def mock_spoke(tmp_path: Path):
    """Create a mock Spoke repository structure."""
    spoke_root = tmp_path / "mock_spoke"
    spoke_root.mkdir()
    legal_docs = spoke_root / "legal_docs"
    legal_docs.mkdir()

    # Create bundle 1: 02_qcvn/qcvn_test_01
    b1 = legal_docs / "02_qcvn" / "qcvn_test_01"
    b1.mkdir(parents=True)
    b1_sources = b1 / "sources"
    b1_sources.mkdir()

    pdf_content = b"%PDF-1.4 Mock PDF Content 01"
    pdf_sha = compute_sha256(pdf_content)
    (b1_sources / "qcvn_test_01.pdf").write_bytes(pdf_content)

    b1_meta = {
        "id": "QCVN-TEST-01",
        "doc_type": "qcvn",
        "pdf_sha256": pdf_sha,
        "pdf_path": "legal_docs/02_qcvn/qcvn_test_01/sources/qcvn_test_01.pdf",
        "source_assets": {
            "pdf": {
                "sha256": pdf_sha,
                "vault_path": "CCBA_Legal_Vault/02_qcvn/qcvn_test_01/qcvn_test_01.pdf",
            },
            "docx": {
                "sha256": "aaaa111122223333444455556666777788889999aaaabbbbccccddddeeeeffff",
                "vault_path": "CCBA_Legal_Vault/02_qcvn/qcvn_test_01/qcvn_test_01.docx",
            },
        },
    }
    (b1 / "metadata.yaml").write_text(yaml.dump(b1_meta), encoding="utf-8")

    # Create bundle 2: 01_vbpl/nd_test_02 (missing sources completely)
    b2 = legal_docs / "01_vbpl" / "nd_test_02"
    b2.mkdir(parents=True)
    b2_meta = {
        "id": "ND-TEST-02",
        "doc_type": "nghi_dinh",
        "source_assets": {
            "pdf": {
                "sha256": "bbbb111122223333444455556666777788889999aaaabbbbccccddddeeeeffff",
                "vault_path": "CCBA_Legal_Vault/01_vbpl/nd_test_02/nd_test_02.pdf",
            },
        },
    }
    (b2 / "metadata.yaml").write_text(yaml.dump(b2_meta), encoding="utf-8")

    return spoke_root


def test_find_bundles(mock_spoke: Path):
    """Test discovering bundles with category and cohort filtering."""
    hydrator = SpokeHydrator(spoke_root=mock_spoke)

    all_bundles = hydrator.find_bundles()
    assert len(all_bundles) == 2

    qcvn_bundles = hydrator.find_bundles(category="02_qcvn")
    assert len(qcvn_bundles) == 1
    assert qcvn_bundles[0].name == "qcvn_test_01"

    filtered = hydrator.find_bundles(cohorts=["nd_test_02"])
    assert len(filtered) == 1
    assert filtered[0].name == "nd_test_02"


def test_inspect_bundle_assets(mock_spoke: Path):
    """Test inspecting expected assets from metadata.yaml."""
    hydrator = SpokeHydrator(spoke_root=mock_spoke)
    b1_dir = mock_spoke / "legal_docs" / "02_qcvn" / "qcvn_test_01"

    assets = hydrator.inspect_bundle_assets(b1_dir)
    assert len(assets) == 2
    types = {a.asset_type for a in assets}
    assert types == {"pdf", "docx"}

    pdf_asset = next(a for a in assets if a.asset_type == "pdf")
    assert pdf_asset.file_name == "qcvn_test_01.pdf"
    assert len(pdf_asset.expected_sha256) == 64


def test_verify_asset_local(mock_spoke: Path):
    """Test verifying local files: up-to-date vs missing vs hash mismatch."""
    hydrator = SpokeHydrator(spoke_root=mock_spoke)
    b1_dir = mock_spoke / "legal_docs" / "02_qcvn" / "qcvn_test_01"
    assets = hydrator.inspect_bundle_assets(b1_dir)

    # PDF exists and matches
    pdf_asset = next(a for a in assets if a.asset_type == "pdf")
    hydrator.verify_asset_local(b1_dir, pdf_asset)
    assert pdf_asset.status == AssetStatus.UP_TO_DATE

    # DOCX is missing
    docx_asset = next(a for a in assets if a.asset_type == "docx")
    hydrator.verify_asset_local(b1_dir, docx_asset)
    assert docx_asset.status == AssetStatus.MISSING

    # Create a corrupted DOCX file (hash mismatch)
    (b1_dir / "sources" / "qcvn_test_01.docx").write_bytes(b"corrupted docx content")
    hydrator.verify_asset_local(b1_dir, docx_asset)
    assert docx_asset.status == AssetStatus.HASH_MISMATCH


def test_hydrate_all_verify_only(mock_spoke: Path):
    """Test hydrate_all in verify_only mode."""
    hydrator = SpokeHydrator(spoke_root=mock_spoke)
    summary = hydrator.hydrate_all(verify_only=True)

    assert summary.total_bundles == 2
    assert summary.fully_hydrated == 0
    assert summary.partially_hydrated == 1  # qcvn_test_01 has PDF
    assert summary.unhydrated == 1  # nd_test_02 has no files
    assert summary.up_to_date_assets == 1
    assert summary.missing_assets == 2
