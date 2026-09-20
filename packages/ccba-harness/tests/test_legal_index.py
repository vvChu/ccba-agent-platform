"""test_legal_index.py - Unit tests for Legal Flat Index and Statutory Provenance (ADR-0059)."""

from __future__ import annotations

import json

from ccba_harness.evals.legal_index import (
    DEFAULT_FLAT_INDEX_PATH,
    LegalFlatIndex,
    StatutoryDocument,
    load_legal_flat_index,
)


def test_legal_flat_index_file_exists_and_valid_json():
    """Verify legal_clauses_flat.json exists inside package and conforms to ADR-0059 schema."""
    assert DEFAULT_FLAT_INDEX_PATH.exists(), f"Missing {DEFAULT_FLAT_INDEX_PATH}"
    size_kb = DEFAULT_FLAT_INDEX_PATH.stat().st_size / 1024
    assert 50 <= size_kb <= 600, f"File size {size_kb:.1f} KB outside expected bounds [50, 600] KB"

    with open(DEFAULT_FLAT_INDEX_PATH, encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("schema_version") == "1.0.0"
    assert "ADR-0059" in data.get("standard", "")
    assert data.get("total_documents", 0) >= 50
    assert "documents" in data
    assert "replaces_map" in data


def test_load_legal_flat_index_structure():
    """Verify load_legal_flat_index loads and memoizes StatutoryDocument models correctly."""
    index = load_legal_flat_index()
    assert isinstance(index, LegalFlatIndex)
    assert index.total_documents >= 50

    # Look up QCVN 06:2022/BXD
    doc = index.get_document("QCVN 06:2022/BXD")
    assert doc is not None
    assert isinstance(doc, StatutoryDocument)
    assert doc.document_number == "QCVN 06:2022/BXD"
    assert len(doc.pdf_sha256) == 64
    assert doc.status in ("current", "active")
    assert len(doc.statutory_keys) > 50

    # Verify clause containment
    assert doc.has_clause("muc-1") or doc.has_clause("1.1") or doc.has_clause("mục 1")


def test_legal_flat_index_replaces_map_expired_checks():
    """Verify index accurately detects expired/superseded statutes and returns replacement."""
    index = load_legal_flat_index()

    # Trap 1: 136/2020 -> replaced by 105/2025
    is_exp, rep = index.is_expired_or_replaced("Nghị định 136/2020/NĐ-CP")
    assert is_exp is True
    assert rep == "105/2025/NĐ-CP"

    # Trap 2: 50/2014 -> replaced by 135/2025
    is_exp, rep = index.is_expired_or_replaced("Luật Xây dựng số 50/2014/QH13")
    assert is_exp is True
    assert rep == "135/2025/QH15"

    # Trap 3: QCVN 06:2020 -> replaced by QCVN 06:2022/BXD
    is_exp, rep = index.is_expired_or_replaced("QCVN 06:2020/BXD")
    assert is_exp is True
    assert rep == "QCVN 06:2022/BXD"

    # Active statute: QCVN 06:2022/BXD is not expired
    is_exp, rep = index.is_expired_or_replaced("QCVN 06:2022/BXD")
    assert is_exp is False
    assert rep is None


def test_legal_flat_index_get_document_lookups():
    """Verify get_document supports exact number, alias, and returns None for unknown."""
    index = load_legal_flat_index()

    # Case-insensitive / partial match
    doc = index.get_document("qcvn 06:2022/bxd")
    assert doc is not None
    assert doc.id == "QCVN-06-2022-BXD"

    # Decree 105/2025 lookup
    doc_105 = index.get_document("105/2025/NĐ-CP")
    assert doc_105 is not None
    assert "105" in doc_105.document_number

    # Unknown document
    assert index.get_document("NonExistentLaw-999/2099") is None
