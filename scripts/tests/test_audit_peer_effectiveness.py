"""Offline unit tests for scripts.governance.audit_peer_effectiveness."""

from __future__ import annotations

import datetime
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.governance.audit_peer_effectiveness import (
    _analyze_escaped_defects,
    evaluate_peer_effectiveness,
    parse_utc_timestamp,
    render_markdown_report,
)


def _write_md(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class TestAuditPeerEffectiveness(unittest.TestCase):
    """Verify cohort UTC split, telemetry union, max_turns_reached, and escaped defects."""

    def test_parse_utc_timestamp_python310_z_and_rejects_naive(self):
        """Normalize Z to UTC and reject naive/malformed timestamps."""
        dt_z = parse_utc_timestamp("2026-11-25T00:08:00Z")
        dt_ict = parse_utc_timestamp("2026-11-25T07:08:00+07:00")
        self.assertIsNotNone(dt_z)
        self.assertEqual(dt_z, dt_ict)
        self.assertIsNone(parse_utc_timestamp("2026-11-25T07:08:00"))
        self.assertIsNone(parse_utc_timestamp("not-a-date"))

    def test_cohort_dedup_telemetry_union_and_autosynth_events(self):
        """Verify verdict wins per request_id, CombinedTelemetry.wall_seconds, and events.jsonl."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            sessions = Path(tmp) / "sessions"
            _write_md(
                root / ".md" / "peer_exchange" / "prompt_p1.md",
                (
                    "---\nrequest_id: req-1\nfrom_agent: antigravity\nto_agent: grok\n"
                    "request_type: plan\nsubject: S1\ntimestamp: '2026-11-24T10:00:00+07:00'\n"
                    "output_path: .md/peer_exchange/grok_p1.md\n---\nPrompt [ADOPT_AS_IS]"
                ),
            )
            _write_md(
                root / ".md" / "peer_exchange" / "grok_p1.md",
                (
                    "---\nrequest_id: req-1\nverdict: APPROVE_WITH_CONDITIONS\n"
                    "conditions:\n  - id: C1\n    description: fix\n    blocking: true\n"
                    "timestamp: '2026-11-25T00:05:00Z'\n"
                    "telemetry:\n  session_id: sess-pre\n  primary_model: grok-4.7\n"
                    "  input_tokens: 1000\n  cached_read_tokens: 800\n  turn_count: 2\n"
                    "  cost_usd: 0.40\n  cost_mode: exact\n  duration_seconds: 120.0\n"
                    "---\nBody [ADOPT_ADAPTED]"
                ),
            )
            ev_pre = sessions / "proj" / "sess-pre" / "events.jsonl"
            ev_pre.parent.mkdir(parents=True, exist_ok=True)
            ev_pre.write_text(
                '{"type":"turn_ended","cancellation_context":{"reason":"max_turns_reached"}}\n',
                encoding="utf-8",
            )
            _write_md(
                root / ".md" / "peer_exchange" / "grok_post_corev.md",
                (
                    "---\nrequest_id: req-2\nverdict: APPROVE_PLAN\nconditions: []\n"
                    "timestamp: '2026-11-25T08:00:00+07:00'\n"
                    "telemetry:\n  total_tokens: 2000\n  input_tokens: 1500\n"
                    "  cached_read_tokens: 1200\n  cost_usd: 0.30\n  wall_seconds: 95.5\n"
                    "  sum_agent_seconds: 140.0\n  cost_mode: exact\n"
                    "---\nCo-review [REBUT_WITH_EVIDENCE]"
                ),
            )
            _write_md(
                root / ".md" / "peer_exchange" / "grok_undated.md",
                "---\nrequest_id: req-3\nverdict: APPROVE_PLAN\nconditions: []\n---\nNo ts",
            )

            rep = evaluate_peer_effectiveness(
                [root],
                cutoff="2026-11-25T07:08:00+07:00",
                sessions_dir=sessions,
                use_git=False,
            )
            self.assertEqual(rep["undated_excluded"], 1)
            self.assertEqual(rep["prompt_only_count"], 0)
            self.assertEqual(rep["pre_v26"]["runs"], 1)
            self.assertEqual(rep["pre_v26"]["median_chain_s"], 120.0)
            self.assertEqual(rep["pre_v26"]["auto_synthesis_rate"], 1.0)
            self.assertEqual(rep["pre_v26"]["auto_synthesis_sources"], {"session_events": 1})
            self.assertEqual(rep["post_v26"]["runs"], 1)
            self.assertEqual(rep["post_v26"]["median_chain_s"], 95.5)
            self.assertEqual(rep["post_v26"]["auto_synthesis_rate"], 0.0)
            self.assertEqual(rep["triage_counts"]["[ADOPT_AS_IS]"], 1)
            self.assertEqual(rep["triage_counts"]["[ADOPT_ADAPTED]"], 1)
            self.assertEqual(rep["triage_counts"]["[REBUT_WITH_EVIDENCE]"], 1)
            md = render_markdown_report(rep)
            self.assertIn("Median Chain Duration (s)", md)
            json.dumps(rep)

    def test_escaped_defects_tagged_guard_and_churn_exclusion(self):
        """Separate confirmed Escaped-From-PR + guard warn from 14d churn-filtered candidates."""
        cutoff = datetime.datetime(2026, 11, 25, 0, 8, tzinfo=datetime.timezone.utc)
        commits = [
            {
                "sha": "aaaa1111bbbb",
                "ts": cutoff + datetime.timedelta(hours=2),
                "subject": "fix(peer): resolve parser edge case",
                "body": "Escaped-From-PR: #904\nPrior-Reviewed-By: grok+coderabbit\n",
                "files": ["scripts/validation/audit_pr_comments.py"],
            },
            {
                "sha": "abab3333cdcd",
                "ts": cutoff + datetime.timedelta(hours=3),
                "subject": "fix(peer): resolve second edge case with test",
                "body": "Escaped-From-PR: #902\nPrior-Reviewed-By: coderabbit\n",
                "files": [
                    "scripts/validation/audit_pr_comments.py",
                    "scripts/tests/test_audit_pr_comments.py",
                ],
            },
            {
                "sha": "cccc2222dddd",
                "ts": cutoff - datetime.timedelta(days=1),
                "subject": "fix(docs): routine AGENTS update",
                "body": "",
                "files": ["AGENTS.md"],
            },
            {
                "sha": "eeee3333ffff",
                "ts": cutoff - datetime.timedelta(days=2),
                "subject": "fix(harness): patch bug",
                "body": "",
                "files": ["packages/ccba-harness/src/ccba_harness/peer.py"],
            },
            {
                "sha": "99990000aaaa",
                "ts": cutoff - datetime.timedelta(days=5),
                "subject": "feat(harness): initial peer feature",
                "body": "",
                "files": ["AGENTS.md", "packages/ccba-harness/src/ccba_harness/peer.py"],
            },
        ]
        res = _analyze_escaped_defects(commits, cutoff, 14)
        self.assertEqual(len(res["confirmed_tagged"]), 2)
        self.assertEqual(res["confirmed_tagged"][0]["escaped_from_pr"], "#904")
        self.assertEqual(res["confirmed_tagged"][0]["prior_reviewed_by"], "grok+coderabbit")
        self.assertFalse(res["confirmed_tagged"][0]["has_regression_guard"])
        self.assertTrue(res["confirmed_tagged"][1]["has_regression_guard"])
        self.assertEqual(res["confirmed_missing_regression_test"], 1)
        self.assertEqual(res["candidate_untagged_count"], 1)


if __name__ == "__main__":
    unittest.main()
