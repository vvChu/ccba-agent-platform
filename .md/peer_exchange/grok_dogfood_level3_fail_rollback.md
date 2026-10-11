---
request_id: req-dogfood-l3-rollback-001
verdict: HANDOFF
conditions: []
summary: Generated intentional failure AnchorPatchPayload for test_telemetry.py to
  verify Level-3 automatic rollback.
telemetry:
  session_id: 14e52caf-06a3-4a0c-ad16-8d757216fbd3
  primary_model: gemini-3.8-flash-high
  input_tokens: 34776
  output_tokens: 490
  reasoning_tokens: 3473
  cached_read_tokens: 14781
  total_tokens: 35266
  model_calls: 2
  turn_count: 1
  cost_usd: 0.0459
  cost_mode: estimated
  duration_seconds: 25.01
---
```json
{
  "files": [
    {
      "path": "packages/ccba-harness/tests/test_telemetry.py",
      "blob_sha256": "de40d00f4e924dd8ab081b34f520bf36d824339b37d42afbbcd7792b73dbef58",
      "replacements": [
        {
          "old": "    code_fail = run_telemetry_cli([\"audit-swarm\", str(swarm_dir), \"--max-swarm-tokens\", \"10\"])\n    assert code_fail == 1\n    err = capsys.readouterr().err\n    assert \"[FAIL] Swarm budget violation\" in err",
          "new": "    code_fail = run_telemetry_cli([\"audit-swarm\", str(swarm_dir), \"--max-swarm-tokens\", \"10\"])\n    assert code_fail == 1\n    err = capsys.readouterr().err\n    assert \"[FAIL] Swarm budget violation\" in err\n\n\ndef test_resolve_model_token_rates_edge_cases_failing():\n    \"\"\"Intentional test failure for Level-3 rollback verification.\"\"\"\n    from ccba_harness.telemetry import resolve_model_token_rates\n\n    assert resolve_model_token_rates(\"\") == (999.0, 999.0)"
        }
      ]
    }
  ]
}
```
