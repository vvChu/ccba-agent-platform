"""packages/ccba-harness/tests/test_peer.py - Unit tests for Structured Peer Exchange Protocol.

Validates Pydantic v2 schemas, YAML frontmatter extraction, and fail-safe handling (Issue #458).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ccba_harness.peer import (
    PeerCondition,
    PeerPromptEnvelope,
    PeerVerdictBlock,
    extract_frontmatter,
    parse_envelope_from_md,
    parse_verdict_from_md,
    render_prompt_header,
    render_verdict_header,
)


def test_roundtrip_prompt_envelope():
    envelope = PeerPromptEnvelope(
        request_id="test-req-001",
        from_agent="antigravity",
        to_agent="grok",
        request_type="review",
        subject="Test Code Review",
        timestamp="2026-10-04T16:00:00+07:00",
        source_documents=["docs/adr/0007.md"],
        output_path=".md/peer_exchange/grok_review.md",
        context="Additional notes",
    )
    rendered = render_prompt_header(envelope)
    body = "## Instruction\nPlease review the patch carefully.\n"
    full_content = rendered + body

    parsed = parse_envelope_from_md(full_content)
    assert parsed is not None
    assert parsed.request_id == "test-req-001"
    assert parsed.from_agent == "antigravity"
    assert parsed.to_agent == "grok"
    assert parsed.request_type == "review"
    assert parsed.source_documents == ["docs/adr/0007.md"]


def test_roundtrip_verdict_block():
    verdict = PeerVerdictBlock(
        request_id="test-req-001",
        verdict="GATE_PASS",
        conditions=[
            PeerCondition(id="C1", description="100% tests pass", blocking=True),
            PeerCondition(id="C2", description="Flake8 clean", blocking=False),
        ],
        risk_score=1,
        effort="S",
        summary="All automated checks passed cleanly.",
    )
    rendered = render_verdict_header(verdict)
    body = "### Verification Details\nEverything looks good."
    full_content = rendered + body

    parsed = parse_verdict_from_md(full_content)
    assert parsed is not None
    assert parsed.verdict == "GATE_PASS"
    assert len(parsed.conditions) == 2
    assert parsed.conditions[0].id == "C1"
    assert parsed.conditions[0].blocking is True
    assert parsed.risk_score == 1
    assert parsed.effort == "S"


def test_extra_forbidden_in_envelope():
    data = {
        "request_id": "req-1",
        "from_agent": "antigravity",
        "to_agent": "grok",
        "request_type": "review",
        "subject": "Test",
        "timestamp": "2026-10-04",
        "output_path": "out.md",
        "unknown_extra_field": "disallowed",
    }
    with pytest.raises(ValidationError):
        PeerPromptEnvelope.model_validate(data)


def test_invalid_and_missing_frontmatter_handled_gracefully():
    # 1. Plain markdown without frontmatter
    plain_md = "# Title\n\nJust normal prose text."
    assert parse_envelope_from_md(plain_md) is None
    assert parse_verdict_from_md(plain_md) is None

    data, body = extract_frontmatter(plain_md)
    assert data is None
    assert body == plain_md

    # 2. Malformed frontmatter (syntax error)
    bad_yaml = "---\n: bad: yaml: [}\n---\nBody here"
    assert parse_envelope_from_md(bad_yaml) is None
    assert parse_verdict_from_md(bad_yaml) is None

    # 3. Empty string
    assert parse_envelope_from_md("") is None
    assert parse_verdict_from_md("") is None
