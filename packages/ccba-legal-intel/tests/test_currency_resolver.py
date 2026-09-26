"""Unit tests for Dynamic Statutory Resolver — Hybrid Engine (ADR-0035, ADR-0050, ADR-0059)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from ccba_legal.currency_resolver import (
    StatutoryDocInfo,
    StatutoryRole,
    clear_resolver_cache,
    resolve_statutory_doc,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_statutory_roles_resolution_active_2026() -> None:
    """Verify modern statutory resolution for all roles after July 1, 2026."""
    eval_date = "2026-09-26"

    grading = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_GRADING, eval_date)
    assert grading.doc_number == "34/2026/TT-BXD"
    assert "cấp công trình" in grading.title.lower()
    assert grading.status == "active"
    assert grading.source_origin in {"master_registry", "local_registry", "currency_card"}
    assert "34/2026/TT-BXD" in grading.citation_str

    law = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_LAW, eval_date)
    assert law.doc_number == "135/2025/QH15"
    assert "135/2025/QH15" in law.title

    pccc_law = resolve_statutory_doc(StatutoryRole.PCCC_LAW, eval_date)
    assert pccc_law.doc_number == "55/2024/QH15"

    pccc_decree = resolve_statutory_doc(StatutoryRole.PCCC_DECREE, eval_date)
    assert pccc_decree.doc_number == "105/2025/NĐ-CP"

    pm_decree = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_PROJECT_MANAGEMENT, eval_date)
    assert pm_decree.doc_number == "217/2026/NĐ-CP"

    qm_decree = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_QUALITY_MANAGEMENT, eval_date)
    assert qm_decree.doc_number == "207/2026/NĐ-CP"

    fire_safety = resolve_statutory_doc(StatutoryRole.TECHNICAL_FIRE_SAFETY, eval_date)
    assert fire_safety.doc_number == "QCVN 06:2022/BXD"
    assert "QCVN 06:2022/BXD" in fire_safety.title


def test_statutory_roles_resolution_historical_2024() -> None:
    """Verify historical temporal resolution for older projects (before July 1, 2026)."""
    eval_date = "2024-05-01"

    grading = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_GRADING, eval_date)
    assert grading.doc_number == "06/2021/TT-BXD"
    assert "06/2021/TT-BXD" in grading.citation_str

    law = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_LAW, eval_date)
    assert law.doc_number == "50/2014/QH13"

    pccc_law = resolve_statutory_doc(StatutoryRole.PCCC_LAW, eval_date)
    assert pccc_law.doc_number == "27/2001/QH10"

    pccc_decree = resolve_statutory_doc(StatutoryRole.PCCC_DECREE, eval_date)
    assert pccc_decree.doc_number == "136/2020/NĐ-CP"

    pm_decree = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_PROJECT_MANAGEMENT, eval_date)
    assert pm_decree.doc_number == "15/2021/NĐ-CP"

    qm_decree = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_QUALITY_MANAGEMENT, eval_date)
    assert qm_decree.doc_number == "06/2021/NĐ-CP"

    fire_safety = resolve_statutory_doc(StatutoryRole.TECHNICAL_FIRE_SAFETY, eval_date)
    assert fire_safety.doc_number == "QCVN 06:2022/BXD"


def test_statutory_roles_transitional_period_2025() -> None:
    """Verify transitional date where PCCC 55/2024 is active, but Construction Law 135 is not yet."""
    eval_date = "2025-08-15"

    # PCCC law active since 2025-07-01
    pccc_law = resolve_statutory_doc(StatutoryRole.PCCC_LAW, eval_date)
    assert pccc_law.doc_number == "55/2024/QH15"

    # Construction Law 135 only active from 2026-07-01
    const_law = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_LAW, eval_date)
    assert const_law.doc_number == "50/2014/QH13"

    # Grading 34 only active from 2026-07-01
    grading = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_GRADING, eval_date)
    assert grading.doc_number == "06/2021/TT-BXD"


def test_string_role_input_and_cache_clear() -> None:
    """Verify string role coercion and cache flushing."""
    doc = resolve_statutory_doc("CONSTRUCTION_GRADING", "2026-09-01")
    assert isinstance(doc, StatutoryDocInfo)
    assert doc.doc_number == "34/2026/TT-BXD"

    clear_resolver_cache()
    # Ensure cache clear doesn't break subsequent calls
    doc2 = resolve_statutory_doc("CONSTRUCTION_GRADING", "2026-09-01")
    assert doc2.doc_number == "34/2026/TT-BXD"


def test_offline_fallback_isolation() -> None:
    """Verify zero-crash guarantee when both master registry and currency card are missing."""
    with patch("ccba_legal.currency_resolver.discover_master_registry_path", return_value=None):
        with patch("pathlib.Path.is_file", return_value=False):
            doc = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_GRADING, "2026-09-01")
            assert doc.doc_number == "34/2026/TT-BXD"
            assert doc.source_origin == "fallback"

            doc_old = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_GRADING, "2024-01-01")
            assert doc_old.doc_number == "06/2021/TT-BXD"
            assert doc_old.source_origin == "fallback"


def test_vietnamese_date_format_and_invalid_date_validation() -> None:
    """Verify Vietnamese DD/MM/YYYY date parsing and validation errors."""
    doc = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_GRADING, "01/05/2024")
    assert doc.doc_number == "06/2021/TT-BXD"

    doc_modern = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_GRADING, "15/08/2026")
    assert doc_modern.doc_number == "34/2026/TT-BXD"

    with pytest.raises(ValueError, match="Invalid evaluation_date format"):
        resolve_statutory_doc(StatutoryRole.CONSTRUCTION_GRADING, "invalid-random-date")


def test_currency_card_discovery_outside_repo_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify Tier 2 currency card resolves properly even when working directory is outside repo."""
    monkeypatch.chdir("/tmp")
    # Resolve historical doc using currency card
    doc = resolve_statutory_doc(StatutoryRole.CONSTRUCTION_LAW, "2024-05-01")
    assert doc.doc_number == "50/2014/QH13"
    assert doc.source_origin == "currency_card"
