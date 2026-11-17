# Application Features Map & Verification Matrix (`ccba-ai`)

| Mã Tính Năng | Tên Tính Năng | Endpoint / CLI / Module | Verification Script | Trạng Thái | Last Verified |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `FEAT-AI-001` | PEP 562 Lazy Public Seams & Exports (`AIClient`, `AsyncAIClient`, `choose_model`, `CircuitBreaker`) | `ccba_ai.__all__` | `packages/ccba-harness/.agents/skills/verify-ccba-ai/harness/test_ai_suite.py` | `stable` | 2026-11-16 |
| `FEAT-AI-002` | Model Archetypes, Virtual Tiers (`tier-ocr`, `tier-fast`, `tier-reasoning`, `tier-local`), `choose_model()` & `resolve_max_tokens()` | `ccba_ai.routing` | `packages/ccba-harness/.agents/skills/verify-ccba-ai/harness/test_ai_suite.py` | `stable` | 2026-11-16 |
| `FEAT-AI-003` | Circuit Breaker State Machine (`CLOSED` $\to$ `OPEN` $\to$ `HALF_OPEN` $\to$ `CLOSED` / `OPEN`) & `CircuitBreakerOpenError` | `ccba_ai.circuit_breaker` | `packages/ccba-harness/.agents/skills/verify-ccba-ai/harness/test_ai_suite.py` | `stable` | 2026-11-16 |
| `FEAT-AI-004` | Multi-Tier Failover Cascade, Model-Family CLI Affinity & Adaptive Timeout Clamp | `ccba_ai.fallback` / `ccba_ai.client` | `packages/ccba-harness/.agents/skills/verify-ccba-ai/harness/test_ai_suite.py` | `stable` | 2026-11-16 |
| `FEAT-AI-005` | 5-Block Lifecycle, Statechart Bug-Path Replay & Anti-Lie Validation | `run_verify_ai.py` / `verify_statechart_anti_lie` | `packages/ccba-harness/.agents/skills/verify-ccba-ai/harness/test_ai_suite.py` | `stable` | 2026-11-16 |
| `FEAT-AI-006` | Surface Diff Parity, LF SHA-256 Git Provenance Lock & 4-State Drift Classifier | `run_verify_ai.verify_surface_diff` | `packages/ccba-harness/.agents/skills/verify-ccba-ai/harness/test_ai_suite.py` | `stable` | 2026-11-16 |
