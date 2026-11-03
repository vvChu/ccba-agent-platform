# Báo Cáo Nghiệm Thu Hoàn Thành (Walkthrough) — PR #593 (Bounded Tool Audit, Explore-Then-Synthesize Auto-Recovery & 3-Way Triage Gate)
## Feature: `feat(ccba-harness): enable bounded tool exploration, auto-resume synthesis, and 3-way peer triage gate`

> **Nguồn Kiểm Toán:** Đối soát 287 phiên lịch sử trong `~/.grok/sessions/` & Phiên thảo luận trực tiếp với `grok-4.7-build` (`Session: c10398b2-d405-47fa-9a16-3316cd2832c6`, kế thừa từ `64859e18-e701-4186-bef1-b0ad5af3ac9c` $\to$ `91ef4dda-76c2-4580-a067-eceaa9131248`)  
> **Pull Requests Liên Quan:** [#592](https://github.com/vvChu/ccba-agent-platform/pull/592) (`2d0a3381`), [#591](https://github.com/vvChu/ccba-agent-platform/pull/591) (`8c731731`)  
> **Branch:** `feat/peer-bounded-tool-audit-and-triage-gate`  
> **Trạng thái:** ✅ **96/96 PEER & GOVERNANCE TESTS PASS — 8/8 HISTORICAL REJECTED VERDICTS RESCUED, `verify-patch --preset ci` 6/6 PASS**

---

## 1. Tổng Kết Thay Đổi Kiến Trúc & Quản Trị (`COND-01`..`COND-04`)

| Hạng Mục / Component | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **`COND-01`: Media-Tool Disallow & `VERDICT_RESERVE_TURNS = 2`** | `packages/ccba-harness/src/ccba_harness/_peer_watchdog.py` | Bổ sung 4 công cụ media (`image_gen`, `image_edit`, `image_to_video`, `reference_to_video`) vào `READ_ONLY_DISALLOW_LIST`, `NO_TOOLS_DISALLOW_LIST`, và `PROFILE_SPECS["agentic_code"]["disallowed_tools"]`. Thêm `system_prompt` cho `audit_plan` và chuẩn hóa `BOUNDED_TOOL_BUDGET_PROMPT` + `SYNTHESIS_FALLBACK_PROMPT` cho 5 profiles Read-Only (`audit_plan`, `arch_audit`, `deep_spec_audit`, `code_review`, `signoff_diff`) cùng `audit_direct`. | Verified |
| **`COND-02`: `PeerVerdictBlock` Condition & Risk Score Normalization** | `packages/ccba-harness/src/ccba_harness/_peer_models.py` | Mở rộng `_normalize_conditions` ánh xạ các khóa alias `("text", "statement", "condition", "summary")` sang `"description"` và tự điền `"id": f"COND-{i + 1:02d}"` khi thiếu `"id"`. Mở rộng `_normalize_risk_score` quy đổi `<= 0` $\to$ `1`, `(5, 10]` $\to$ `round(v / 2)`, `(10, 100]` $\to$ `round(v / 20)`, `> 100` $\to$ `5` (bảo toàn nhánh `bool` và `[0, 1)`). | Verified |
| **`COND-03`: Explore-Then-Synthesize Auto-Recovery (`max_turns=1`)** | `packages/ccba-harness/src/ccba_harness/peer.py`, `_peer_watchdog.py` | Bổ sung `is_max_turns_exhausted()` và `_build_synthesis_opts()`: khi phiên có bật `tools` chạm `max_turns_reached` trong `events.jsonl`, `_dispatch_grok_candidate()` tự động kích hoạt 1 lượt `--resume <eff_sid> --fork-session` (`max_turns=1`, `SYNTHESIS_FALLBACK_PROMPT`, `tools=None`) để thu hoạch phán quyết YAML từ ngữ cảnh mã nguồn đã đọc. | Verified |
| **`COND-04`: Section 20.3 3-Way Triage Gate & `RULE-4.17` Scope** | `docs/rules/execution_coordination_guardrails.md`, `.md/knowledge/session_learnings.md` | Khóa cứng Mục `20.3` (`[ADOPT_AS_IS]`, `[ADOPT_ADAPTED]`, `[REBUT_WITH_EVIDENCE]` kèm bắt buộc trích dẫn `file:line`), xóa chú thích `--no-tools` khỏi `signoff_diff` tại dòng 138, và cập nhật `RULE-4.17` liệt kê đầy đủ 5 profiles bật tools + 2 profiles `--no-tools` (`7,193` bytes = `7.02 KB <= 10.0 KB`). | Verified |

---

## 2. Bằng Chứng Kiểm Chứng Thực Nghiệm & Tự Động (`ADR-0058`)

- **Đối soát hồi quy trên 8 phiên lịch sử từng bị đánh trượt trong `~/.grok/sessions/`**:
  - Cả **8/8 phiên** (`01a106d7`, `01a106e2`, `bcae120e`, `ba58a786`, `01a111f4`, `332ae19c`, `6f3b0103`, `91ef4dda`) đều được `PeerVerdictBlock` giải mã thành công (`[RESCUED] 8/8`).
- **Bộ kiểm thử đơn vị & hợp đồng CLI (`96/96 passed in 9.60s`)**:
  - `packages/ccba-harness/tests/test_peer.py`: `37 passed` (bao gồm `test_bounded_tool_budget_and_explore_then_synthesize_recovery`).
  - `packages/ccba-harness/tests/test_peer_dispatch_cli.py`: `8 passed`.
  - `packages/ccba-harness/tests/test_cli_contract_parity.py`: `26 passed`.
  - `tests/governance/test_compact_session_learnings.py`: `8 passed`.
  - `scripts/tests/test_doc_refactor_daemon.py`: `15 passed`.
  - `tests/test_agent_execution_guardrails.py`: `2 passed`.
- **Cổng kiểm định `verify-patch --preset ci` (`6/6 passed in 17.80s`)**:
  - `ruff check`, `ruff format --check`, `pytest`, `validate_skills.py --enforce-gpi`, `compile_catalog.py --check`, `sync_hub_adr_matrix.py --check`: **ALL PASS**.
