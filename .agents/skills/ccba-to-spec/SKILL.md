---
name: ccba-to-spec
description: Turn the current conversation into a spec and publish it to the project
  issue tracker — no interview, just synthesis of what you've already discussed.
disable-model-invocation: true
bundle: _core
tier: kernel
user-invocable: true
command: /ccba-to-spec
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
gpi:
  s: 4.0
  k: 2.0
  a: 1.0
  p: 1.0
triggers:
- ccba-to-spec
- spec
- soạn spec
- tạo spec
- đặc tả kỹ thuật
- ccba-to-tickets
- to-tickets
- ccba-to-questionnaire
- to-questionnaire
---

This skill takes the current conversation context and codebase understanding and produces a spec (you may know this document as a PRD). Do NOT interview the user — just synthesize what you already know.

The issue tracker and triage label vocabulary should have been provided to you — run `/ccba-setup-skills` if not.

---

## 🏛️ Platform-Aware Architecture Posture

- **Tư thế Kiến trúc (Architecture Posture):** `seam-exempt`
- **Lý do Miễn trừ Seam (Exemption Rationale):** Kỹ năng đóng vai trò quy trình thao tác chuẩn (SOP) kernel tổng hợp bối cảnh hội thoại và hiện trạng codebase thành tài liệu đặc tả kỹ thuật (Technical Specification / PRD), gán nhãn `ready-for-agent` và lưu trữ tại `.md/knowledge/specs/spec-{feature_slug}.md`. Khái niệm "seams" trong văn bản là phương pháp phân rã kiến trúc phần mềm và ranh giới kiểm thử tích hợp (testing seams), không sở hữu Seam đóng gói dữ liệu Python độc lập. Toàn bộ quy trình tuân thủ các nguyên tắc thiết kế tinh gọn và phân rã nhiệm vụ tất định.
- **Tuân thủ Thể chế Quản trị (Governance Compliance):** Đạt chuẩn thể chế Tier 2B Standalone Kernel Skill với chỉ số GPI (S: 4.0, K: 2.0, A: 1.0, P: 1.0) = 14.5 $\ge$ 12.0. Duy trì 2 tài liệu tham chiếu chuyên sâu tại tầng Level 3 (`references/spec_decomposition.md`, `references/interactive_questionnaire.md`).

---

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.

2. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one.

Check with the user that these seams match their expectations.

3. Write the spec using the template below, then publish it to the project issue tracker. Apply the `ready-for-agent` triage label - no need for additional triage.

If no tracker is configured or if using Local Markdown tracker, write the spec directly to a local Markdown file under `.md/knowledge/specs/spec-{feature_slug}.md` (using a safe kebab-case ASCII name, removing special characters and spaces).

<spec-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this spec.

## Further Notes

Any further notes about the feature.

</spec-template>

---

## Atomic Micro-Task Slicing Invariant (Sprint 1 Rule)

To maintain high development velocity and prevent review fatigue (per Cursor 2,500 PRs/month model and Decision Log), every spec decomposed into tickets MUST adhere to the following invariants:

1. **Strict Blast Radius Budget**:
   - Each individual ticket/micro-task must target a diff budget of **$\le 150-200$ lines of code** (excluding tests and markdown).
   - If a User Story requires > 200 LOC, it MUST be sliced into multiple sequential tracer-bullet tickets.
2. **Single Seam Anchor**:
   - A ticket should touch at most **1 Public Deep Seam** registered in `catalog.yaml`. Never span multiple unrelated seams in one ticket.
3. **Deterministic Acceptance Command**:
   - Every ticket description MUST declare an exact verification command that exits with code 0 upon completion (e.g. `pytest packages/<pkg>/tests/test_<feature>.py -v` or `python -m ccba_harness verify-patch --preset code`).
4. **Context Hygiene & Clean Agent Execution**:
   - Each ticket is designed to be executed in a brand-new, clean Agent context window (`/ccba-implement` or `/ccba-tdd`) to eliminate hallucination caused by context window bloating.




## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/spec_decomposition.md` | Kỹ thuật phân rã tài liệu đặc tả thành danh mục nhiệm vụ (tickets) chi tiết |
| `references/interactive_questionnaire.md` | Kỹ thuật xây dựng bảng khảo sát thu thập yêu cầu từ người dùng |

