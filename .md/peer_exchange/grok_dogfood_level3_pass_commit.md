---
request_id: req-dogfood-l3-pass-001
verdict: HANDOFF
conditions: []
summary: Anchor patch inserting test_resolve_model_token_rates_edge_cases into packages/ccba-harness/tests/test_telemetry.py
telemetry:
  session_id: 01a83376-3d0f-44be-9c6e-9fe5ea50daef
  primary_model: gemini-3.8-flash-high
  input_tokens: 34048
  output_tokens: 564
  reasoning_tokens: 3339
  cached_read_tokens: 0
  total_tokens: 34612
  model_calls: 2
  turn_count: 1
  cost_usd: 0.0454
  cost_mode: estimated
  duration_seconds: 26.01
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
          "new": "    code_fail = run_telemetry_cli([\"audit-swarm\", str(swarm_dir), \"--max-swarm-tokens\", \"10\"])\n    assert code_fail == 1\n    err = capsys.readouterr().err\n    assert \"[FAIL] Swarm budget violation\" in err\n\n\ndef test_resolve_model_token_rates_edge_cases():\n    \"\"\"Verifies that empty string or None safely falls back to default rates.\"\"\"\n    from ccba_harness.telemetry import (\n        PRICE_PER_M_INPUT,\n        PRICE_PER_M_OUTPUT,\n        resolve_model_token_rates,\n    )\n\n    assert resolve_model_token_rates(\"\") == (PRICE_PER_M_INPUT, PRICE_PER_M_OUTPUT)\n    assert resolve_model_token_rates(None) == (PRICE_PER_M_INPUT, PRICE_PER_M_OUTPUT)"
        }
      ]
    }
  ]
}
```
