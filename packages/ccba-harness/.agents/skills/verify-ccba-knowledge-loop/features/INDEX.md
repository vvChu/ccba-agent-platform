# Application Features Map & Verification Matrix (`ccba-knowledge-loop`)

| Mã Tính Năng | Tên Tính Năng | Endpoint / CLI / Module | Verification Script | Trạng Thái | Last Verified |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `FEAT-KL-001` | Frontmatter, Orchestrator Tier & Slash Command Contract | `.agents/skills/ccba-knowledge-loop/SKILL.md` | `.agents/skills/ccba-knowledge-loop/harness/test_knowledge_loop_suite.py` | `stable` | 2026-11-03 |
| `FEAT-KL-002` | Single-Writer Protocol (ADR-0053) & 4-Phase Orchestration (`Recon` $\to$ `Brainstorm` $\to$ `Wayfinder` $\to$ `Exec`) | `.agents/skills/ccba-knowledge-loop/SKILL.md` | `.agents/skills/ccba-knowledge-loop/harness/test_knowledge_loop_suite.py` | `stable` | 2026-11-03 |
| `FEAT-KL-003` | Phase 2 Hybrid Rhythm (`Prompt`, `User first`, `AI Build`, `Return floor`) & Party Mode | `.agents/skills/ccba-knowledge-loop/SKILL.md` | `.agents/skills/ccba-knowledge-loop/harness/test_knowledge_loop_suite.py` | `stable` | 2026-11-03 |
| `FEAT-KL-004` | Tier 2A `llm-wiki.md`: `.md/knowledge/wiki/` Namespace Isolation (`COND-02`), `Ingest`/`Query`/`Lint` & SHA Provenance | `.agents/skills/ccba-knowledge-loop/references/llm-wiki.md` | `.agents/skills/ccba-knowledge-loop/harness/test_knowledge_loop_suite.py` | `stable` | 2026-11-03 |
| `FEAT-KL-005` | Simulator & Archetype Catalog Registration (`platform_tooling`) | `ccba_harness.evals.simulators.platform_tooling` | `.agents/skills/ccba-knowledge-loop/harness/test_knowledge_loop_suite.py` | `stable` | 2026-11-03 |
| `FEAT-KL-006` | 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes | `.agents/skills/ccba-knowledge-loop/harness/run_verify_knowledge_loop.py` | `.agents/skills/ccba-knowledge-loop/harness/test_knowledge_loop_suite.py` | `stable` | 2026-11-03 |
| `FEAT-KL-007` | Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer | `ccba_harness.evals.tuner.GitRatchetOptimizer` | `.agents/skills/ccba-knowledge-loop/harness/test_knowledge_loop_suite.py` | `stable` | 2026-11-03 |
