"""Tests for Lex Conflict Engine & Risk Scoring Component."""

import pytest
from ccba_legal.conflict import LexConflictEngine, RiskAssessmentScore, RiskLabel


def test_lex_superior_conflict() -> None:
    """Test Lex Superior rule: Law hierarchy overrides lower circulars."""
    engine = LexConflictEngine()
    
    law_doc = {
        "doc_type": "Luật",
        "doc_number": "Luật 55/2024/QH15",
        "enactment_date": "2024-06-01",
        "domain": "PCCC",
    }
    circular_doc = {
        "doc_type": "Thông tư",
        "doc_number": "Thông tư 12/2021/TT-BXD",
        "enactment_date": "2021-05-01",
        "domain": "Kiến trúc",
    }
    
    score = engine.evaluate_conflict(law_doc, circular_doc, event_date="2026-01-01")
    
    assert isinstance(score, RiskAssessmentScore)
    assert score.risk_label == RiskLabel.YELLOW
    assert any("Lex Superior" in r for r in score.conflict_rules_applied)
    assert score.score >= 50 and score.score < 80


def test_no_conflict_aligned_docs() -> None:
    """Test green score when documents are fully aligned without conflict."""
    engine = LexConflictEngine()
    
    doc_a = {
        "doc_type": "Nghị định",
        "doc_number": "Nghị định 105/2025/NĐ-CP",
        "enactment_date": "2025-01-01",
        "status": "effective",
    }
    doc_b = {
        "doc_type": "Thông tư",
        "doc_number": "Thông tư 05/2025/TT-BXD",
        "enactment_date": "2025-02-01",
        "status": "effective",
    }
    
    score = engine.evaluate_conflict(doc_a, doc_b, event_date="2026-01-01")
    
    assert score.risk_label == RiskLabel.GREEN
    assert score.score >= 80


def test_expired_or_gray_area_red_score() -> None:
    """Test red score when document is expired or has major unguided gray area."""
    engine = LexConflictEngine()
    
    expired_doc = {
        "doc_type": "Thông tư",
        "doc_number": "Thông tư 06/2010/TT-BXD",
        "status": "expired",
    }
    draft_doc = {
        "doc_type": "Dự thảo",
        "doc_number": "Dự thảo QCVN 2026",
        "status": "draft",
    }
    
    score = engine.evaluate_conflict(expired_doc, draft_doc, event_date="2026-07-01")
    
    assert score.risk_label == RiskLabel.RED
    assert score.score < 50
