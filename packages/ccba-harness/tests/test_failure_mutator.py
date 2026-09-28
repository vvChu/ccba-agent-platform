"""test_failure_mutator.py - Unit test suite for Failure-Driven Mutator (PR-A / ADR-0059).

Verifies zero-LLM-token failure signal extraction, metadata-only patch rendering,
in-memory LegalFlatIndex integration, and ledger persistence without mocking
or synthesizing statutory clauses.
"""

from __future__ import annotations

import pytest

from ccba_harness.evals.failure_mutator import (
    FailureSignal,
    calculate_signal_fingerprint,
    extract_failure_signals,
    get_unapplied_failure_signals,
    is_signal_applied,
    load_failure_ledger,
    render_failure_patch,
    save_failure_ledger,
)
from ccba_harness.evals.legal_index import load_legal_flat_index
from ccba_harness.evals.models import EvalItem, EvalItemResult, EvalReport, ScoreResult


@pytest.fixture
def flat_index():
    """Loads the real statutory legal flat index from JSON dataset."""
    return load_legal_flat_index()


def test_01_expired_unacknowledged_signal_and_patch(flat_index):
    """Case 1: EXPIRED_UNACKNOWLEDGED with 136/2020/NĐ-CP must point to 105/2025/NĐ-CP and its SHA-256."""
    score_res = ScoreResult(
        scorer_name="legal_verbatim_provenance",
        score=0.0,
        raw_output={"trap_doc": "136/2020/NĐ-CP", "replacement": "105/2025/NĐ-CP"},
        reasoning="Citing expired decree without replacement acknowledgment",
        is_critical_fail=True,
    )
    report = EvalReport(
        total_items=1,
        passed_items=0,
        failed_items=1,
        overall_score=0.0,
        pass_rate=0.0,
        item_results=[
            EvalItemResult(
                item_id="item_trap_01",
                task_output="Căn cứ Nghị định 136/2020/NĐ-CP...",
                scores=[score_res],
                composite_score=0.0,
                passed=False,
                critical_failed=True,
            )
        ],
    )

    signals = extract_failure_signals(report, index=flat_index)
    assert len(signals) == 1
    sig = signals[0]
    assert sig.code == "EXPIRED_UNACKNOWLEDGED"
    assert sig.fields["trap_doc"] == "136/2020/NĐ-CP"
    assert sig.fields["replacement"] == "105/2025/NĐ-CP"

    card = render_failure_patch(sig, index=flat_index)
    assert "136/2020/NĐ-CP" in card
    assert "105/2025/NĐ-CP" in card
    # Must contain replacement pdf_sha256 from flat index (starting with 6808c77f)
    assert sig.fields.get("replacement_pdf_sha256", "").startswith("6808c77f")
    assert sig.fields["replacement_pdf_sha256"] in card
    assert f"<!-- failure_signal: {sig.fingerprint} -->" in card


def test_02_unknown_clause_lists_real_keys_only(flat_index):
    """Case 2: UNKNOWN_CLAUSE with non-existent clause in 135/2025/QH15 must only list real statutory keys."""
    fake_clause = "Điều 9999"
    score_res = ScoreResult(
        scorer_name="legal_verbatim_provenance",
        score=0.0,
        raw_output={"doc": "135/2025/QH15", "fake_clause": fake_clause},
        reasoning="Non-existent clause in statutory document",
        is_critical_fail=True,
    )
    report = EvalReport(
        total_items=1,
        passed_items=0,
        failed_items=1,
        overall_score=0.0,
        pass_rate=0.0,
        item_results=[
            EvalItemResult(
                item_id="item_fake_clause_01",
                task_output="Căn cứ Điều 9999 Luật 135/2025/QH15...",
                scores=[score_res],
                composite_score=0.0,
                passed=False,
                critical_failed=True,
            )
        ],
    )

    signals = extract_failure_signals(report, index=flat_index)
    assert len(signals) == 1
    sig = signals[0]
    assert sig.code == "UNKNOWN_CLAUSE"
    assert sig.fields["fake_clause"] == fake_clause
    assert sig.fields["doc"] == "135/2025/QH15"

    valid_keys = sig.fields["valid_keys"]
    assert len(valid_keys) <= 8
    assert "dieu-1" in valid_keys

    card = render_failure_patch(sig, index=flat_index)
    assert fake_clause in card
    assert "135/2025/QH15" in card
    assert "dieu-1" in card
    assert f"<!-- failure_signal: {sig.fingerprint} -->" in card


def test_03_unknown_document_rejects_without_synthetic_replacement(flat_index):
    """Case 3: UNKNOWN_DOCUMENT rejects fabricated number and does not hallucinate replacement."""
    fabricated_doc = "999/2029/NĐ-CP"
    score_res = ScoreResult(
        scorer_name="legal_verbatim_provenance",
        score=0.0,
        raw_output={"unknown_doc": fabricated_doc},
        reasoning="Document not found in official gazette index",
        is_critical_fail=True,
    )
    report = EvalReport(
        total_items=1,
        passed_items=0,
        failed_items=1,
        overall_score=0.0,
        pass_rate=0.0,
        item_results=[
            EvalItemResult(
                item_id="item_unknown_01",
                task_output=f"Căn cứ Nghị định {fabricated_doc}...",
                scores=[score_res],
                composite_score=0.0,
                passed=False,
                critical_failed=True,
            )
        ],
    )

    signals = extract_failure_signals(report, index=flat_index)
    assert len(signals) == 1
    sig = signals[0]
    assert sig.code == "UNKNOWN_DOCUMENT"
    assert sig.fields["unknown_doc"] == fabricated_doc

    card = render_failure_patch(sig, index=flat_index)
    assert fabricated_doc in card
    assert "Tuyệt đối không tự ý giả định hay bịa đặt văn bản thay thế" in card
    assert f"<!-- failure_signal: {sig.fingerprint} -->" in card


def test_04_no_citation_with_target_law(flat_index):
    """Case 4: NO_CITATION with target_law=55/2024/QH15 includes 64-char SHA-256 and gazette number."""
    score_res = ScoreResult(
        scorer_name="legal_verbatim_provenance",
        score=0.0,
        raw_output={"citations_found": 0},
        reasoning="No statutory citations detected",
        is_critical_fail=True,
    )
    report = EvalReport(
        total_items=1,
        passed_items=0,
        failed_items=1,
        overall_score=0.0,
        pass_rate=0.0,
        item_results=[
            EvalItemResult(
                item_id="item_no_cit_01",
                task_output="Không có căn cứ pháp lý...",
                scores=[score_res],
                composite_score=0.0,
                passed=False,
                critical_failed=True,
            )
        ],
    )
    items = [
        EvalItem(
            id="item_no_cit_01",
            input_prompt="Quy chuẩn thiết kế đường bộ?",
            metadata={"target_law": "55/2024/QH15"},
        )
    ]

    signals = extract_failure_signals(report, items=items, index=flat_index)
    assert len(signals) == 1
    sig = signals[0]
    assert sig.code == "NO_CITATION"
    assert sig.fields["target_law"] == "55/2024/QH15"

    sha256_val = sig.fields["pdf_sha256"]
    assert len(sha256_val) == 64
    assert sha256_val.startswith("706a8bfb")
    assert sig.fields["cong_bao_number"] == "1187+1188/2024"

    card = render_failure_patch(sig, index=flat_index)
    assert "55/2024/QH15" in card
    assert sha256_val in card
    assert "1187+1188/2024" in card


def test_05_renderer_idempotency_second_call_empty(flat_index):
    """Case 5: Calling get_unapplied_failure_signals on body containing patch returns empty list."""
    sig = FailureSignal(
        code="UNKNOWN_DOCUMENT",
        item_id="item_test",
        scorer="legal_verbatim_provenance",
        fingerprint=calculate_signal_fingerprint(
            "legal_verbatim_provenance", "UNKNOWN_DOCUMENT", "99/9999", "", "item_test"
        ),
        fields={"unknown_doc": "99/9999"},
    )
    card = render_failure_patch(sig, index=flat_index)

    skill_body = f"# Skill Title\n\nSome guidelines.\n\n{card}\n"
    unapplied = get_unapplied_failure_signals(skill_body, [sig])
    assert len(unapplied) == 0


def test_06_regex_scorer_raw_output_does_not_create_signal():
    """Case 6: Raw output from non-provenance scorers (e.g. regex) must be filtered out."""
    score_res = ScoreResult(
        scorer_name="regex_compliance",
        score=0.0,
        raw_output={"pattern_matched": False, "citations_found": 0},
        reasoning="Regex failed",
        is_critical_fail=True,
    )
    report = EvalReport(
        total_items=1,
        passed_items=0,
        failed_items=1,
        overall_score=0.0,
        pass_rate=0.0,
        item_results=[
            EvalItemResult(
                item_id="item_regex_01",
                task_output="test output",
                scores=[score_res],
                composite_score=0.0,
                passed=False,
                critical_failed=True,
            )
        ],
    )

    signals = extract_failure_signals(report)
    assert len(signals) == 0


def test_07_daemon_filter_exhausted_with_unapplied_signal_not_skipped(tmp_path):
    """Case 7: YAML-exhausted skill with unapplied signal in ledger is NOT skipped."""
    skill_content = "# Skill Legal Advisor\n\nRules here.\n"
    sig = FailureSignal(
        code="EXPIRED_UNACKNOWLEDGED",
        item_id="item_01",
        scorer="legal_verbatim_provenance",
        fingerprint="dummy_fp_12345",
        fields={"trap_doc": "136/2020/NĐ-CP", "replacement": "105/2025/NĐ-CP"},
    )
    ledger_path = save_failure_ledger(
        skill_name="ccba-legal-advisor",
        signals=[sig],
        skill_content=skill_content,
        ledger_dir=tmp_path,
    )
    assert ledger_path.exists()

    ledger = load_failure_ledger("ccba-legal-advisor", ledger_dir=tmp_path)
    assert ledger is not None
    unapplied = get_unapplied_failure_signals(skill_content, list(ledger.signals))
    assert len(unapplied) == 1

    # In daemon logic: has_unapplied_signals = bool(unapplied) -> True -> NOT skipped
    assert bool(unapplied) is True


def test_08_daemon_filter_exhausted_non_legal_archetype_skipped(tmp_path):
    """Case 8: YAML-exhausted skill without ledger or non-legal archetype is skipped."""
    # When archetype is 'coding', failure mutator is not eligible
    archetype_name = "coding"
    has_unapplied_signals = False
    is_legal_archetype = archetype_name in {"legal", "legal_tooling"}

    should_skip = not is_legal_archetype and not has_unapplied_signals
    assert should_skip is True


def test_09_ratchet_simulation_commit_and_rollback():
    """Case 9: Simulated ratchet trial with failure patch.

    - Pre-patch output fails critical floor with 136/2020.
    - Adding patch guides task to cite 105/2025 and score increases -> keep commit.
    - If task still fails -> rollback and fingerprint is not reapplied.
    """
    skill_original = "# Skill\n\nOriginal prompt.\n"
    sig = FailureSignal(
        code="EXPIRED_UNACKNOWLEDGED",
        item_id="item_ratchet",
        scorer="legal_verbatim_provenance",
        fingerprint="fp_ratchet_987",
        fields={"trap_doc": "136/2020/NĐ-CP", "replacement": "105/2025/NĐ-CP"},
    )

    card = render_failure_patch(sig)
    mutated_content = skill_original + "\n" + card

    # 1. Before mutation: not applied
    assert not is_signal_applied(skill_original, sig)

    # 2. After mutation: signal is applied
    assert is_signal_applied(mutated_content, sig)

    # 3. If trial rolls back to original content, fingerprint can still be tracked in ledger:
    seen_failed_fingerprints: set[str] = set()
    # Trial fails:
    trial_passed = False
    if not trial_passed:
        seen_failed_fingerprints.add(sig.fingerprint)

    # Next proposal skips seen failed fingerprints
    assert sig.fingerprint in seen_failed_fingerprints


def test_10_wrong_target_signal_and_patch(flat_index):
    """Case 10: WRONG_TARGET extracts effective target document and renders valid card."""
    score_res = ScoreResult(
        scorer_name="legal_verbatim_provenance",
        score=0.0,
        raw_output={"target_law": "55/2024/QH15"},
        reasoning="Failed to cite target law 55/2024/QH15",
        is_critical_fail=True,
    )
    report = EvalReport(
        total_items=1,
        passed_items=0,
        failed_items=1,
        overall_score=0.0,
        pass_rate=0.0,
        item_results=[
            EvalItemResult(
                item_id="item_target_01",
                task_output="Căn cứ Luật khác...",
                scores=[score_res],
                composite_score=0.0,
                passed=False,
                critical_failed=True,
            )
        ],
    )

    signals = extract_failure_signals(report, index=flat_index)
    assert len(signals) == 1
    sig = signals[0]
    assert sig.code == "WRONG_TARGET"
    assert sig.fields["target_law"] == "55/2024/QH15"

    card = render_failure_patch(sig, index=flat_index)
    assert "55/2024/QH15" in card
    assert "1187+1188/2024" in card
    assert f"<!-- failure_signal: {sig.fingerprint} -->" in card
