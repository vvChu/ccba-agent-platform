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

<!-- Phân loại rủi ro khi merge để tối ưu hóa thời gian review của con người (ADR-0067 / Issue #519) -->
- **Door**:
  - [ ] **Two-way door** (Thuần tài liệu, dễ revert, không ảnh hưởng mã nguồn hay quy chuẩn)
  - [ ] **Paved Road** (Thay đổi mã nguồn cô lập $\le 200$ LOC, nằm ngoài 7 nhóm One-Way Door, 100% `verify-patch` xanh)
  - [ ] **One-way door** (Khó đảo ngược, chạm vào 1 trong 7 nhóm danh mục Cửa Một Chiều hoặc vượt ngân sách 200 LOC / chuỗi tích lũy $K \ge 3$)
  - *Lý do*: <!-- Giải thích ngắn gọn tại sao dễ đảo ngược hoặc khó đảo ngược -->
- **Blast Radius**:
  - [ ] **Localized** (Cục bộ 1 file hoặc hàm nội bộ, không đổi API public)
  - [ ] **Package-wide** (Ảnh hưởng toàn bộ 1 package trong monorepo)
  - [ ] **Monorepo-wide** (Chạm vào tooling dùng chung, scripts/, CI, hoặc cross-package)
  - [ ] **Spoke-affecting** (Thay đổi contract/interface mà các Spoke downstream đang phụ thuộc)
  - *Tác động tiềm tàng*: <!-- Điều gì có thể bị gãy nếu có sự cố xảy ra? -->

### Tradeoff Card (Required for One-Way Door PRs)

<!-- Bắt buộc điền đầy đủ 3 trường dưới đây khi PR thuộc nhóm One-way door (cấm điền TBD/N/A) -->
- **Core Invariant**: <!-- Bất biến kiến trúc cốt lõi cần bảo vệ là gì? -->
- **Invalidation Condition**: <!-- Điều kiện thực tế nào chứng minh thiết kế này sai hoặc cần rollback? -->
- **Git Hunk Reference**: <!-- Đường dẫn tệp + dải dòng <= 30 dòng (ví dụ: packages/ccba-harness/src/ccba_harness/door_policy.py#L35-L60) để Taste-Holder kiểm định trong 30s -->

---

## Architectural Governance & Two-Stage Granularity Check

<!-- If this PR introduces or modifies any Agent Skill (.agents/skills/*), complete this section per RES-2026-ARCH-001 v1.2 -->

### Stage 1: Structural Invariant Gates
- [ ] **Gate 0 — The Determinism Gate**: This capability **CANNOT** be resolved 100% by deterministic algorithms (AST parsing, regex, math, file I/O). If deterministic -> must reside in packages/*/src as a Deep Seam, NOT a Skill.
- [ ] **Gate 1 — The Orchestration Gate**: This capability is **NOT** a multi-step multi-agent coordinator with durable checkpoints or human-in-the-loop approvals. If orchestrated -> must be a Tier 3 Composite Orchestrator.

### Stage 2: Granularity & Placement Index (GPI) Evaluation
Run the automated GPI evaluation CLI:
```bash
ccba-harness evaluate-gpi --file .agents/skills/<skill-name>/SKILL.md
```
- [ ] **GPI Score Verified**: Attached CLI output below.
- [ ] **Placement Compliance**:
  - **GPI >= 12.0**: Qualified as **Tier 2B Standalone Kernel Skill** (.agents/skills/ccba-<name>/).
  - **GPI < 12.0**: Routed as **Tier 2A Progressive Reference** (`references/*.md` within parent Master Skill).

<details>
<summary>📋 Paste <code>ccba-harness evaluate-gpi</code> output here</summary>

```text
<!-- Paste output here -->
```
</details>

---

## Quality & CI Verification Checklist

- [ ] **Catalog Parity**: python scripts/governance/compile_catalog.py --check passes (100% in-sync).
- [ ] **Monorepo Seams**: python scripts/governance/check_dependency_contracts.py passes (Zero cross-package violations).
- [ ] **Static Analysis**: python -m ruff check packages/ passes with 0 errors and 0 warnings.
- [ ] **Type Safety**: python -m mypy passes on modified packages.
- [ ] **Automated Tests**: pytest passes 100% for all affected modules.
- [ ] **Hub-Spoke Compatibility**: Non-destructive merge and deprecation aliases preserved if renaming/retiring legacy skills.
