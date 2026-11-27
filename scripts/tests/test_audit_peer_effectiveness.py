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

    def test_timestamp_fallback_prompt_and_session_events_never_mtime(self):
        """Fallback order: verdict.timestamp -> prompt.timestamp -> events.jsonl ts; never mtime."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            sessions = Path(tmp) / "sessions"
            _write_md(
                root / ".md" / "peer_exchange" / "prompt_post.md",
                (
                    "---\nrequest_id: req-post\nfrom_agent: antigravity\nto_agent: grok\n"
                    "request_type: plan\nsubject: Post\ntimestamp: '2026-11-25T08:00:00+07:00'\n"
                    "output_path: .md/peer_exchange/grok_post.md\n---\nPrompt"
                ),
            )
            _write_md(
                root / ".md" / "peer_exchange" / "grok_post.md",
                (
                    "---\nrequest_id: req-post\nverdict: APPROVE_PLAN\nconditions: []\n"
                    "telemetry:\n  session_id: s-post\n  cost_usd: 0.2\n  duration_seconds: 80.0\n"
                    "---\nNo verdict ts"
                ),
            )
            _write_md(
                root / ".md" / "peer_exchange" / "grok_sess_only.md",
                (
                    "---\nrequest_id: req-sess\nverdict: APPROVE_PLAN\nconditions: []\n"
                    "telemetry:\n  session_id: s-pre\n  cost_usd: 0.1\n  duration_seconds: 50.0\n"
                    "---\nSession ts only"
                ),
            )
            ev_pre = sessions / "proj" / "s-pre" / "events.jsonl"
            ev_pre.parent.mkdir(parents=True, exist_ok=True)
            ev_pre.write_text(
                '{"ts":"2026-11-24T12:00:00Z","type":"turn_ended","outcome":"completed"}\n',
                encoding="utf-8",
            )
            _write_md(
                root / ".md" / "peer_exchange" / "grok_truly_undated.md",
                "---\nrequest_id: req-none\nverdict: APPROVE_PLAN\nconditions: []\n---\nStill undated",
            )

            rep = evaluate_peer_effectiveness(
                [root],
                cutoff="2026-11-25T07:08:00+07:00",
                sessions_dir=sessions,
                use_git=False,
            )
            self.assertEqual(rep["post_v26"]["runs"], 1)
            self.assertEqual(rep["pre_v26"]["runs"], 1)
            self.assertEqual(rep["undated_excluded"], 1)

    def test_verdict_timestamp_overrides_prompt_and_session(self):
        """Dated verdict on post side overrides pre-cutoff prompt and session event timestamps."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            sessions = Path(tmp) / "sessions"
            _write_md(
                root / ".md" / "peer_exchange" / "prompt_p.md",
                (
                    "---\nrequest_id: req-verdict-wins\nfrom_agent: antigravity\nto_agent: grok\n"
                    "request_type: plan\nsubject: V\ntimestamp: '2026-11-24T10:00:00+07:00'\n"
                    "output_path: .md/peer_exchange/grok_v.md\n---\nPrompt"
                ),
            )
            _write_md(
                root / ".md" / "peer_exchange" / "grok_v.md",
                (
                    "---\nrequest_id: req-verdict-wins\nverdict: APPROVE_PLAN\nconditions: []\n"
                    "timestamp: '2026-11-25T08:00:00+07:00'\n"
                    "telemetry:\n  session_id: s-v\n  cost_usd: 0.2\n  duration_seconds: 60.0\n"
                    "---\nVerdict wins"
                ),
            )
            ev = sessions / "proj" / "s-v" / "events.jsonl"
            ev.parent.mkdir(parents=True, exist_ok=True)
            ev.write_text('{"ts":"2026-11-24T09:00:00Z","type":"turn_ended"}\n', encoding="utf-8")

            rep = evaluate_peer_effectiveness(
                [root], cutoff="2026-11-25T07:08:00+07:00", sessions_dir=sessions, use_git=False
            )
            self.assertEqual(rep["post_v26"]["runs"], 1)
            self.assertEqual(rep["pre_v26"]["runs"], 0)
            self.assertEqual(rep["undated_excluded"], 0)

    def test_prompt_timestamp_overrides_session(self):
        """Dated prompt overrides pre-cutoff session event timestamp when verdict is undated."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            sessions = Path(tmp) / "sessions"
            _write_md(
                root / ".md" / "peer_exchange" / "prompt_p.md",
                (
                    "---\nrequest_id: req-prompt-wins\nfrom_agent: antigravity\nto_agent: grok\n"
                    "request_type: plan\nsubject: P\ntimestamp: '2026-11-25T08:00:00+07:00'\n"
                    "output_path: .md/peer_exchange/grok_p.md\n---\nPrompt"
                ),
            )
            _write_md(
                root / ".md" / "peer_exchange" / "grok_p.md",
                (
                    "---\nrequest_id: req-prompt-wins\nverdict: APPROVE_PLAN\nconditions: []\n"
                    "telemetry:\n  session_id: s-p\n  cost_usd: 0.2\n  duration_seconds: 60.0\n"
                    "---\nPrompt wins"
                ),
            )
            ev = sessions / "proj" / "s-p" / "events.jsonl"
            ev.parent.mkdir(parents=True, exist_ok=True)
            ev.write_text('{"ts":"2026-11-24T09:00:00Z","type":"turn_ended"}\n', encoding="utf-8")

            rep = evaluate_peer_effectiveness(
                [root], cutoff="2026-11-25T07:08:00+07:00", sessions_dir=sessions, use_git=False
            )
            self.assertEqual(rep["post_v26"]["runs"], 1)
            self.assertEqual(rep["pre_v26"]["runs"], 0)
            self.assertEqual(rep["undated_excluded"], 0)

    def test_baseline_since_filtering_all_and_invalid_raises(self):
        """baseline_since filters legacy pre-v2.5 rows, supports 'all', and rejects invalid ISO."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            _write_md(
                root / ".md" / "peer_exchange" / "grok_legacy.md",
                (
                    "---\nrequest_id: req-legacy\nverdict: APPROVE_PLAN\nconditions: []\n"
                    "timestamp: '2026-10-15T10:00:00+07:00'\n"
                    "telemetry:\n  session_id: s-old\n  cost_usd: 0.05\n  duration_seconds: 30.0\n"
                    "---\nOld run"
                ),
            )
            _write_md(
                root / ".md" / "peer_exchange" / "grok_v25.md",
                (
                    "---\nrequest_id: req-v25\nverdict: APPROVE_PLAN\nconditions: []\n"
                    "timestamp: '2026-11-20T10:00:00+07:00'\n"
                    "telemetry:\n  session_id: s-v25\n  cost_usd: 0.25\n  duration_seconds: 200.0\n"
                    "---\nv2.5 run"
                ),
            )
            rep_default = evaluate_peer_effectiveness([root], use_git=False)
            self.assertIsNone(rep_default["baseline_since_utc"])
            self.assertEqual(rep_default["pre_baseline_excluded"], 0)
            self.assertEqual(rep_default["pre_v26"]["runs"], 2)

            rep_v25 = evaluate_peer_effectiveness(
                [root], baseline_since="2026-11-11T00:00:00+07:00", use_git=False
            )
            self.assertEqual(rep_v25["pre_baseline_excluded"], 1)
            self.assertEqual(rep_v25["pre_v26"]["runs"], 1)
            self.assertEqual(rep_v25["pre_v26"]["median_chain_s"], 200.0)
            self.assertIsInstance(rep_v25["baseline_since_utc"], str)
            json.dumps(rep_v25)

            rep_all = evaluate_peer_effectiveness([root], baseline_since="all", use_git=False)
            self.assertEqual(rep_all["pre_baseline_excluded"], 0)
            self.assertEqual(rep_all["pre_v26"]["runs"], 2)

            with self.assertRaises(ValueError):
                evaluate_peer_effectiveness([root], baseline_since="not-a-timestamp", use_git=False)

    def test_inferred_pass2_chain_respects_opt_out_repo_isolation_and_plan_code_boundary(self):
        """Infer CLI-resumed Pass 2 in same repo <=12h; block opt-out, cross-repo, and Plan->Code."""
        with TemporaryDirectory() as tmp:
            repo_a = Path(tmp) / "repo_a"
            repo_b = Path(tmp) / "repo_b"
            # Pass 1 plan in repo_a
            _write_md(
                repo_a / ".md" / "peer_exchange" / "prompt_grok_feature_alpha_plan.md",
                (
                    "---\nrequest_id: req-20261126-plan-feature-alpha-001\nfrom_agent: antigravity\n"
                    "to_agent: grok\nrequest_type: plan\nprofile: audit_plan\nsubject: Alpha P1\n"
                    "timestamp: '2026-11-26T09:00:00+07:00'\n"
                    "output_path: .md/peer_exchange/grok_feature_alpha_plan.md\n---\nPlan"
                ),
            )
            _write_md(
                repo_a / ".md" / "peer_exchange" / "grok_feature_alpha_plan.md",
                (
                    "---\nrequest_id: req-20261126-plan-feature-alpha-001\nverdict: REVISE_PLAN\n"
                    "conditions:\n  - id: C1\n    description: fix\n    blocking: true\n"
                    "timestamp: '2026-11-26T09:05:00+07:00'\n"
                    "telemetry:\n  session_id: sess-p1\n  cost_usd: 0.20\n  duration_seconds: 300.0\n"
                    "---\nP1"
                ),
            )
            # Pass 2 signoff_diff in repo_a missing resume_session_id -> MUST link to sess-p1
            _write_md(
                repo_a / ".md" / "peer_exchange" / "prompt_grok_feature_alpha_plan_signoff_p2.md",
                (
                    "---\nrequest_id: req-20261126-plan-feature-alpha-002\nfrom_agent: antigravity\n"
                    "to_agent: grok\nrequest_type: verify\nprofile: signoff_diff\nsubject: Alpha P2\n"
                    "timestamp: '2026-11-26T09:15:00+07:00'\n"
                    "output_path: .md/peer_exchange/grok_feature_alpha_plan_signoff_p2.md\n---\nP2"
                ),
            )
            _write_md(
                repo_a / ".md" / "peer_exchange" / "grok_feature_alpha_plan_signoff_p2.md",
                (
                    "---\nrequest_id: req-20261126-plan-feature-alpha-002\nverdict: APPROVE_PLAN\n"
                    "conditions: []\ntimestamp: '2026-11-26T09:18:00+07:00'\n"
                    "telemetry:\n  session_id: sess-p2\n  cost_usd: 0.12\n  duration_seconds: 100.0\n"
                    "---\nP2 ok"
                ),
            )
            # Post-impl code_review in repo_a (same stem, round marker -003) -> MUST NOT link to Plan parent
            _write_md(
                repo_a / ".md" / "peer_exchange" / "prompt_grok_feature_alpha_impl_003.md",
                (
                    "---\nrequest_id: req-20261126-feature-alpha-003\nfrom_agent: antigravity\n"
                    "to_agent: grok\nrequest_type: review\nprofile: code_review\nsubject: Alpha Impl\n"
                    "timestamp: '2026-11-26T10:00:00+07:00'\n"
                    "output_path: .md/peer_exchange/grok_feature_alpha_impl_003.md\n---\nImpl"
                ),
            )
            _write_md(
                repo_a / ".md" / "peer_exchange" / "grok_feature_alpha_impl_003.md",
                (
                    "---\nrequest_id: req-20261126-feature-alpha-003\nverdict: APPROVE\n"
                    "conditions: []\ntimestamp: '2026-11-26T10:05:00+07:00'\n"
                    "telemetry:\n  session_id: sess-code\n  cost_usd: 0.18\n  duration_seconds: 250.0\n"
                    "---\nCode ok"
                ),
            )
            # Explicit opt-out resume_session_id: "new" -> MUST NOT link
            _write_md(
                repo_a / ".md" / "peer_exchange" / "prompt_grok_feature_alpha_plan_signoff_p4.md",
                (
                    "---\nrequest_id: req-20261126-plan-feature-alpha-004\nfrom_agent: antigravity\n"
                    "to_agent: grok\nrequest_type: verify\nprofile: signoff_diff\nresume_session_id: new\n"
                    "subject: Alpha Fresh\ntimestamp: '2026-11-26T10:20:00+07:00'\n"
                    "output_path: .md/peer_exchange/grok_feature_alpha_plan_signoff_p4.md\n---\nFresh"
                ),
            )
            _write_md(
                repo_a / ".md" / "peer_exchange" / "grok_feature_alpha_plan_signoff_p4.md",
                (
                    "---\nrequest_id: req-20261126-plan-feature-alpha-004\nverdict: APPROVE_PLAN\n"
                    "conditions: []\ntimestamp: '2026-11-26T10:22:00+07:00'\n"
                    "telemetry:\n  session_id: sess-optout\n  cost_usd: 0.10\n  duration_seconds: 90.0\n"
                    "---\nFresh ok"
                ),
            )
            # Same stem signoff in repo_b -> MUST NOT link across repos
            _write_md(
                repo_b / ".md" / "peer_exchange" / "prompt_grok_feature_alpha_plan_signoff_p2.md",
                (
                    "---\nrequest_id: req-20261126-plan-feature-alpha-b-002\nfrom_agent: antigravity\n"
                    "to_agent: grok\nrequest_type: verify\nprofile: signoff_diff\nsubject: RepoB\n"
                    "timestamp: '2026-11-26T09:30:00+07:00'\n"
                    "output_path: .md/peer_exchange/grok_feature_alpha_plan_signoff_p2.md\n---\nRepoB"
                ),
            )
            _write_md(
                repo_b / ".md" / "peer_exchange" / "grok_feature_alpha_plan_signoff_p2.md",
                (
                    "---\nrequest_id: req-20261126-plan-feature-alpha-b-002\nverdict: APPROVE_PLAN\n"
                    "conditions: []\ntimestamp: '2026-11-26T09:32:00+07:00'\n"
                    "telemetry:\n  session_id: sess-b2\n  cost_usd: 0.11\n  duration_seconds: 80.0\n"
                    "---\nRepoB ok"
                ),
            )

            rep = evaluate_peer_effectiveness([repo_a, repo_b], use_git=False)
            self.assertEqual(rep["inferred_chain_links"], 1)
            self.assertEqual(rep["post_v26"]["runs"], 5)
            # 5 runs -> 4 chains because only repo_a P2 linked to repo_a P1
            self.assertEqual(rep["post_v26"]["chains"], 4)
            # Pass 1 runs: P1 (blocking=1), impl (0), opt-out (0), repo_b (0) => 1/4 = 0.25
            self.assertEqual(rep["post_v26"]["pass1_blocking_rate"], 0.25)
            # Pass 2 runs: repo_a P2 (blocking=0) => 0.0
            self.assertEqual(rep["post_v26"]["pass2_blocking_rate"], 0.0)
            json.dumps(rep)


if __name__ == "__main__":
    unittest.main()
