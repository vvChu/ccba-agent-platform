## Summary

<!-- Briefly describe the purpose of this PR and what problem it solves. -->

## Type of Change

- [ ] feat: A new feature or capability
- [ ] fix: A bug fix
- [ ] docs: Documentation updates or research reports
- [ ] refactor: Code restructuring without changing behavior
- [ ] test: Adding or updating test suites
- [ ] chore: Maintenance or dependency updates
- [ ] ci: CI/CD pipeline or governance workflow changes

---

## Merge Danger Assessment

<!-- Phân loại rủi ro khi merge để tối ưu hóa thời gian review của con người -->
- **Door**:
  - [ ] **Two-way door** (Dễ revert, thay đổi cô lập/nội bộ, không ảnh hưởng behavior/contract dùng chung)
  - [ ] **One-way door** (Khó đảo ngược, breaking change, thay đổi schema/contract hoặc migration tốn kém)
  - *Lý do*: <!-- Giải thích ngắn gọn tại sao dễ đảo ngược hoặc khó đảo ngược -->
- **Blast Radius**:
  - [ ] **Localized** (Cục bộ 1 file hoặc hàm nội bộ, không đổi API public)
  - [ ] **Package-wide** (Ảnh hưởng toàn bộ 1 package trong monorepo)
  - [ ] **Monorepo-wide** (Chạm vào tooling dùng chung, scripts/, CI, hoặc cross-package)
  - [ ] **Spoke-affecting** (Thay đổi contract/interface mà các Spoke downstream đang phụ thuộc)
  - *Tác động tiềm tàng*: <!-- Điều gì có thể bị gãy nếu có sự cố xảy ra? -->

---

## Architectural Governance & Two-Stage Granularity Check

<!-- If this PR introduces or modifies any Agent Skill (.agents/skills/*), complete this section per RES-2026-ARCH-001 v1.2 -->

### Stage 1: Structural Invariant Gates
- [ ] **Gate 0 — The Determinism Gate**: This capability **CANNOT** be resolved 100% by deterministic algorithms (AST parsing, regex, math, file I/O). If deterministic -> must reside in packages/*/src as a Deep Seam, NOT a Skill.
- [ ] **Gate 1 — The Orchestration Gate**: This capability is **NOT** a multi-step multi-agent coordinator with durable checkpoints or human-in-the-loop approvals. If orchestrated -> must be a Tier 3 Composite Orchestrator.

### Stage 2: Granularity & Placement Index (GPI) Evaluation
Run the automated GPI evaluation CLI:
`ash
ccba-harness evaluate-gpi --file .agents/skills/<skill-name>/SKILL.md
`
- [ ] **GPI Score Verified**: Attached CLI output below.
- [ ] **Placement Compliance**:
  - **GPI >= 12.0**: Qualified as **Tier 2B Standalone Kernel Skill** (.agents/skills/ccba-<name>/).
  - **GPI < 12.0**: Routed as **Tier 2A Progressive Reference** (
eferences/*.md within parent Master Skill).

<details>
<summary>📋 Paste <code>ccba-harness evaluate-gpi</code> output here</summary>

`	ext
<!-- Paste output here -->
`
</details>

---

## Quality & CI Verification Checklist

- [ ] **Catalog Parity**: python scripts/governance/compile_catalog.py --check passes (100% in-sync).
- [ ] **Monorepo Seams**: python scripts/governance/check_dependency_contracts.py passes (Zero cross-package violations).
- [ ] **Static Analysis**: python -m ruff check packages/ passes with 0 errors and 0 warnings.
- [ ] **Type Safety**: python -m mypy passes on modified packages.
- [ ] **Automated Tests**: pytest passes 100% for all affected modules.
- [ ] **Hub-Spoke Compatibility**: Non-destructive merge and deprecation aliases preserved if renaming/retiring legacy skills.
