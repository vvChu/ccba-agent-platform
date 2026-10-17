"""Unit tests for ccba_harness.backpressure (Issue #519 — Slice 2)."""

from __future__ import annotations

from ccba_harness.backpressure import (
    PendingReviewItem,
    evaluate_backpressure_queue,
    parse_tradeoff_card,
    validate_tradeoff_card,
)


def test_backpressure_normal_below_limits() -> None:
    """Verifies that queue below 5 items and <= 24h does not trip circuit-breaker."""
    items = [
        PendingReviewItem(pr_number=501, age_hours=4.5, door_type="ONE_WAY_DOOR"),
        PendingReviewItem(pr_number=502, age_hours=18.0, door_type="ONE_WAY_DOOR"),
        PendingReviewItem(pr_number=503, age_hours=36.0, door_type="PAVED_ROAD"),
    ]
    status = evaluate_backpressure_queue(items)
    assert status.is_tripped is False
    assert status.bypass_active is False
    assert status.pending_count == 2
    assert status.oldest_age_hours == 18.0
    assert status.reason is None


def test_backpressure_trips_when_pending_count_exceeds_5() -> None:
    """Verifies circuit-breaker trips when more than 5 One-Way Door PRs are pending."""
    items = [
        PendingReviewItem(pr_number=500 + i, age_hours=2.0, door_type="ONE_WAY_DOOR")
        for i in range(6)
    ]
    status = evaluate_backpressure_queue(items)
    assert status.is_tripped is True
    assert status.pending_count == 6
    assert status.reason is not None
    assert "exceeds limit (5)" in status.reason


def test_backpressure_trips_when_oldest_age_exceeds_24h() -> None:
    """Verifies circuit-breaker trips when any pending One-Way Door PR is older than 24 hours."""
    items = [
        PendingReviewItem(pr_number=501, age_hours=26.5, door_type="ONE_WAY_DOOR"),
    ]
    status = evaluate_backpressure_queue(items)
    assert status.is_tripped is True
    assert status.oldest_age_hours == 26.5
    assert status.reason is not None
    assert "exceeds limit (24.0h)" in status.reason


def test_backpressure_anti_deadlock_bypass_for_hotfix_and_existing_pr() -> None:
    """Verifies that hotfixes and updates to existing open PRs bypass an overloaded queue."""
    items = [
        PendingReviewItem(pr_number=501, age_hours=30.0, door_type="ONE_WAY_DOOR"),
    ]
    hotfix_status = evaluate_backpressure_queue(items, is_hotfix=True)
    assert hotfix_status.is_tripped is False
    assert hotfix_status.bypass_active is True

    update_status = evaluate_backpressure_queue(items, is_existing_pr_update=True)
    assert update_status.is_tripped is False
    assert update_status.bypass_active is True


def test_validate_tradeoff_card_valid_bullet_and_heading_formats() -> None:
    """Verifies resilient extraction and validation for bulleted and heading Tradeoff Cards."""
    pr_body_bullets = """
## Merge Danger Assessment
### Tradeoff Card
- **Core Invariant**: Every One-Way Door mutation must be signed off by a Taste-Holder.
- **Invalidation Condition**: False-positive rate on Paved Road PRs exceeds 15% over 7 days.
- **Git Hunk Reference**: `packages/ccba-harness/src/ccba_harness/door_policy.py#L40-L65`
"""
    assert validate_tradeoff_card(pr_body_bullets) == []
    card = parse_tradeoff_card(pr_body_bullets)
    assert card is not None
    assert "Taste-Holder" in card.core_invariant

    pr_body_headings = """
### Core Invariant
Deterministic SHA-256 sampling must remain idempotent across CI re-runs.

### Invalidation Condition
Modulo hash collisions skew sampling outside 8-12% over 500 PRs.

### Git Hunk Reference
```diff
+def is_sampled_for_audit(repo: str, pr_number: int, modulo: int = 10) -> bool:
+    return int(hashlib.sha256(f"{repo}:{pr_number}".encode()).hexdigest(), 16) % modulo == 0
```
"""
    assert validate_tradeoff_card(pr_body_headings) == []


def test_validate_tradeoff_card_rejects_missing_or_oversized_hunk() -> None:
    """Verifies that missing fields, placeholders, or hunks > 30 lines fail validation."""
    assert len(validate_tradeoff_card("")) == 1

    placeholder_body = """
- **Core Invariant**: TBD
- **Invalidation Condition**: N/A
- **Git Hunk Reference**: `packages/ccba-harness/src/ccba_harness/door_policy.py#L10-L85`
"""
    errors = validate_tradeoff_card(placeholder_body)
    assert len(errors) == 3
    assert any("Core Invariant" in e for e in errors)
    assert any("Invalidation Condition" in e for e in errors)
    assert any("exceeds 30 lines" in e for e in errors)
