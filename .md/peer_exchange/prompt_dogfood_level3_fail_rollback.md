---
request_id: "req-dogfood-l3-rollback-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "review"
profile: "patch_fast"
subject: "Level-3 Dogfooding Phase 2A: Intentional Failure for Rollback Verification"
timestamp: "2026-10-11T15:26:00+07:00"
source_documents:
  - "packages/ccba-harness/tests/test_telemetry.py"
output_path: ".md/peer_exchange/grok_dogfood_level3_fail_rollback.md"
context: "Generate an AnchorPatchPayload inserting an intentionally failing test assertion to verify Level-3 automatic rollback."
---

# Level-3 Dogfooding Phase 2A: Generate Intentional Failure Anchor Patch

Output YAML frontmatter followed directly by a ```json code block containing the exact schema:

```json
{
  "files": [
    {
      "path": "packages/ccba-harness/tests/test_telemetry.py",
      "blob_sha256": "de40d00f4e924dd8ab081b34f520bf36d824339b37d42afbbcd7792b73dbef58",
      "replacements": [
        {
          "old": "...",
          "new": "..."
        }
      ]
    }
  ]
}
```

Where:
- `old` must be:
    code_fail = run_telemetry_cli(["audit-swarm", str(swarm_dir), "--max-swarm-tokens", "10"])
    assert code_fail == 1
    err = capsys.readouterr().err
    assert "[FAIL] Swarm budget violation" in err

- `new` must be:
    code_fail = run_telemetry_cli(["audit-swarm", str(swarm_dir), "--max-swarm-tokens", "10"])
    assert code_fail == 1
    err = capsys.readouterr().err
    assert "[FAIL] Swarm budget violation" in err


def test_resolve_model_token_rates_edge_cases_failing():
    """Intentional test failure for Level-3 rollback verification."""
    from ccba_harness.telemetry import resolve_model_token_rates

    assert resolve_model_token_rates("") == (999.0, 999.0)

DO NOT use "patches" or "hunks". The schema MUST have "files" and "replacements" with "old" and "new".
