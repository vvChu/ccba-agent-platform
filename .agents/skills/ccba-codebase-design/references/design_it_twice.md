# Design It Twice

> **Điều kiện kích hoạt (Targeted Activation Gate):** Chỉ sử dụng khi **1 ứng viên `ONE_WAY_DOOR` / Public Seam** có **`>= 2` hình thái interface cạnh tranh thực sự**. Không chạy nhân bản song song cho toàn bộ 3 ứng viên trong một đợt quét; với chiến dịch đa ứng viên, dùng `/ccba-wayfinder` + `/ccba-grilling`.

When exploring alternative interfaces for a chosen deepening candidate, use this parallel sub-agent pattern. Based on "Design It Twice" (John Ousterhout) — your first idea is rarely the best.

Uses the vocabulary in [SKILL.md](../SKILL.md) — **module**, **interface**, **seam**, **adapter**, **leverage**.

## Two-Layer Sub-Agent Guardrail & Concurrency Limit (ADR-0035, ADR-0053)

- **Hard Limit & Read-Only Type:** Maximum 3 `type_name="research"` subagents (`workspace="inherit"`) running in parallel. Spawning more than 3 subagents concurrently or using write-enabled subagents is strictly prohibited.
- **Two-Layer Sub-Agent Guardrail:** Every subagent prompt must include the mandatory delegation prohibition:
  `"CRITICAL CONSTRAINT: You are a dedicated read-only design exploration subagent. Do NOT spawn child subagents, do NOT edit or write any files, and do NOT execute modifying commands. Use read-only inspection tools and return your complete design variant directly in your response."`
- **Single-Writer Protocol:** Subagents return design drafts in their response payload; only the Coordinator reads, compares, and updates project design documents.

## Process

### 1. Frame the problem space

Before spawning sub-agents, write a user-facing explanation of the problem space for the chosen candidate:

- The constraints any new interface would need to satisfy
- The dependencies it would rely on, and which category they fall into (see [deepening.md](deepening.md))
- A rough illustrative code sketch to ground the constraints — not a proposal, just a way to make the constraints concrete

Show this to the user, then immediately proceed to Step 2. The user reads and thinks while the sub-agents work in parallel.

### 2. Spawn read-only `research` sub-agents (Max 3 Parallel)

Spawn at most 3 parallel sub-agents using `invoke_subagent` with `TypeName="research"` and `Workspace="inherit"`. Each must produce a **radically different** interface for the deepened module.

Prompt each sub-agent with a separate technical brief (file paths, coupling details, dependency category from [deepening.md](deepening.md), what sits behind the seam) plus the mandatory Two-Layer Sub-Agent Guardrail above. Give each agent a distinct design constraint:

- **Agent 1 (Minimal Surface):** "Minimize the interface — aim for 1–3 entry points max. Maximise leverage per entry point."
- **Agent 2 (Extensibility):** "Maximise flexibility and extensibility — design clean seams for varying implementations."
- **Agent 3 (Ergonomics):** "Optimise for the most common caller — make the default path zero-boilerplate and trivial."

Include both [SKILL.md](../SKILL.md) vocabulary and domain terms from `CONTEXT.md` in the brief.

**Required Subagent Response:**
Each subagent returns its variant directly in its response covering:
1. Interface (types, protocols/ABCs, methods, params, error modes)
2. Usage example showing how callers interact across the seam
3. What the implementation hides behind the seam
4. Dependency strategy and adapters (see [deepening.md](deepening.md))
5. Trade-offs — where leverage is high, where it is thin

### 3. Present and compare

Coordinator collects the returned variants and presents designs sequentially so the user can absorb each one, then compares them in prose. Contrast by:
- **Depth:** Leverage at the interface (functionality gained vs interface complexity)
- **Locality:** Where changes, bugs, and knowledge concentrate
- **Seam placement:** Where the seam lives and how natural testing is

After comparing, give your own recommendation: which design you think is strongest and why. If elements from different designs would combine well, propose a hybrid. Be opinionated — the user wants a strong technical evaluation, not a cafeteria menu.
