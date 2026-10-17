"""ccba_harness.backpressure - Backpressure Circuit-Breaker & Tradeoff Card Validator (Issue #519).

Enforces cognitive load limits for Taste-Holder review queues (pending > 5 or age > 24h)
with anti-deadlock bypasses for hotfixes and existing PR updates, and validates structured
Tradeoff Cards on One-Way Door pull requests.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from .door_policy import DoorType

_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_PLACEHOLDER_VALUES = {"tbd", "todo", "n/a", "na", "none", "-", "..."}
_LINE_RANGE_RE = re.compile(
    r"[A-Za-z0-9_./-]+\.[A-Za-z0-9]+(?:#L(?P<s1>\d+)(?:-L?(?P<e1>\d+))?|:(?P<s2>\d+)(?:-(?P<e2>\d+))?)"
)
_FENCED_BLOCK_RE = re.compile(r"```(?:diff|python|yaml|json|bash|text)?\s*\n(.*?)```", re.DOTALL)


class TradeoffCard(BaseModel):
    """Structured architectural Tradeoff Card required for One-Way Door PRs."""

    model_config = ConfigDict(extra="forbid")

    core_invariant: str
    invalidation_condition: str
    git_hunk_ref: str


class PendingReviewItem(BaseModel):
    """Represents an open pull request awaiting Taste-Holder review."""

    model_config = ConfigDict(extra="forbid")

    pr_number: int
    age_hours: float
    door_type: DoorType = "ONE_WAY_DOOR"


class BackpressureStatus(BaseModel):
    """Circuit-breaker evaluation state for the Taste-Holder review queue."""

    model_config = ConfigDict(extra="forbid")

    is_tripped: bool
    bypass_active: bool = False
    pending_count: int
    oldest_age_hours: float
    reason: str | None = None


def _extract_card_field(clean_body: str, label: str) -> str:
    """Extracts a named field value from markdown supporting bullets, bold keys, or headings."""
    inline_pat = re.compile(
        rf"(?:^|\n)\s*(?:[-*]\s*)?(?:\*\*|`)*{re.escape(label)}(?:\*\*|`)*\s*:\s*(?:\*\*)*\s*(.+?)(?=\n\s*(?:[-*]\s*)?(?:\*\*|`)*(?:Core Invariant|Invalidation Condition|Git Hunk Reference)|(?:\n#+\s)|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    match = inline_pat.search(clean_body)
    if match:
        return match.group(1).strip()

    heading_pat = re.compile(
        rf"(?:^|\n)#{{2,4}}\s*{re.escape(label)}\s*\n+(.+?)(?=\n#{{2,4}}\s|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    h_match = heading_pat.search(clean_body)
    return h_match.group(1).strip() if h_match else ""


def parse_tradeoff_card(pr_body: str) -> TradeoffCard | None:
    """Parses a TradeoffCard from a pull request markdown description.

    Args:
        pr_body: Raw pull request markdown body.

    Returns:
        TradeoffCard if at least one field is present, otherwise None.
    """
    if not pr_body or not pr_body.strip():
        return None
    clean = _HTML_COMMENT_RE.sub("", pr_body)
    core = _extract_card_field(clean, "Core Invariant")
    inval = _extract_card_field(clean, "Invalidation Condition")
    hunk = _extract_card_field(clean, "Git Hunk Reference")
    if not (core or inval or hunk):
        return None
    return TradeoffCard(
        core_invariant=core,
        invalidation_condition=inval,
        git_hunk_ref=hunk,
    )


def _validate_git_hunk(hunk_ref: str, max_lines: int = 30) -> str | None:
    """Validates that Git Hunk Reference has a valid line anchor or code block <= max_lines."""
    fenced = _FENCED_BLOCK_RE.search(hunk_ref)
    if fenced:
        lines = [ln for ln in fenced.group(1).splitlines() if ln.strip()]
        if not lines:
            return "Git Hunk Reference code block cannot be empty."
        if len(lines) > max_lines:
            return f"Git Hunk Reference diff block exceeds {max_lines} lines ({len(lines)} lines)."
        return None

    m = _LINE_RANGE_RE.search(hunk_ref)
    if not m:
        return "Git Hunk Reference must include a file line link (e.g. path/file.py#L10-L35) or fenced diff block."
    start_s = m.group("s1") or m.group("s2")
    end_s = m.group("e1") or m.group("e2")
    if start_s and end_s:
        span = int(end_s) - int(start_s) + 1
        if span <= 0:
            return "Git Hunk Reference line range end must be >= start line."
        if span > max_lines:
            return f"Git Hunk Reference line span exceeds {max_lines} lines ({span} lines)."
    return None


def validate_tradeoff_card(pr_body: str, max_hunk_lines: int = 30) -> list[str]:
    """Validates that a PR body contains a complete, non-placeholder Tradeoff Card.

    Args:
        pr_body: Raw markdown string of the pull request description.
        max_hunk_lines: Maximum permitted lines in the referenced git hunk (default 30).

    Returns:
        List of validation error messages (empty list if valid).
    """
    card = parse_tradeoff_card(pr_body)
    if card is None:
        return [
            "Missing Tradeoff Card section (requires Core Invariant, Invalidation Condition, and Git Hunk Reference)."
        ]

    errors: list[str] = []
    fields = [
        ("Core Invariant", card.core_invariant),
        ("Invalidation Condition", card.invalidation_condition),
        ("Git Hunk Reference", card.git_hunk_ref),
    ]
    for label, val in fields:
        norm = val.strip().lower()
        if not norm or norm in _PLACEHOLDER_VALUES:
            errors.append(f"Tradeoff Card field '{label}' is missing or contains a placeholder.")

    if card.git_hunk_ref.strip() and card.git_hunk_ref.strip().lower() not in _PLACEHOLDER_VALUES:
        hunk_err = _validate_git_hunk(card.git_hunk_ref, max_lines=max_hunk_lines)
        if hunk_err:
            errors.append(hunk_err)
    return errors


def evaluate_backpressure_queue(
    pending_items: Sequence[PendingReviewItem],
    max_pending: int = 5,
    max_age_hours: float = 24.0,
    is_existing_pr_update: bool = False,
    is_hotfix: bool = False,
) -> BackpressureStatus:
    """Evaluates whether the Taste-Holder review queue should trip the backpressure circuit-breaker.

    Args:
        pending_items: Open review items in the queue.
        max_pending: Maximum allowed pending One-Way Door items before tripping (default 5).
        max_age_hours: Maximum age in hours of oldest One-Way Door item before tripping (default 24.0).
        is_existing_pr_update: True if action updates an already-open PR in the queue.
        is_hotfix: True if action is an emergency hotfix/fix branch.

    Returns:
        BackpressureStatus describing queue load and circuit state.
    """
    one_way = [item for item in pending_items if item.door_type == "ONE_WAY_DOOR"]
    count = len(one_way)
    oldest = round(max((item.age_hours for item in one_way), default=0.0), 2)

    reasons: list[str] = []
    if count > max_pending:
        reasons.append(f"pending One-Way Door count ({count}) exceeds limit ({max_pending})")
    if oldest > max_age_hours:
        reasons.append(f"oldest One-Way Door age ({oldest}h) exceeds limit ({max_age_hours}h)")

    if not reasons:
        return BackpressureStatus(is_tripped=False, pending_count=count, oldest_age_hours=oldest)

    bypass = bool(is_existing_pr_update or is_hotfix)
    prefix = (
        "Bypass active (hotfix/existing PR update) despite queue overload"
        if bypass
        else "Backpressure circuit tripped"
    )
    return BackpressureStatus(
        is_tripped=not bypass,
        bypass_active=bypass,
        pending_count=count,
        oldest_age_hours=oldest,
        reason=f"{prefix}: {'; '.join(reasons)}",
    )
