# Ticket 04: Xây Dựng Bộ Đề Thi & Scorer Chuyên Biệt Cho Coordination V2 & Orchestration

- **Type:** Research / Prototype (AFK & HITL)
- **Status:** closed
- **Assignee:** Antigravity
- **Target Seam:** `.agents/skills/ccba-eval-gate/test_cases/eval_bigbim_risk.json`, `packages/ccba-harness/src/ccba_harness/evals/scorers.py`, `packages/ccba-harness/src/ccba_harness/evals/tuner.py`, `scripts/eval/nightly_tuner_daemon.py`
- **Reference:** Báo cáo nghiên cứu `/boost` ngày 18/09/2026 (REC-07), `bigbim-risk/SKILL.md`

---

## 🎯 Mục Tiêu
Chấm dứt việc ép kỹ năng `bigbim-risk` thi đề phân loại Uniclass; đồng thời bổ sung bộ Scorer chuyên biệt cho các kỹ năng điều phối đa tác tử (Orchestration Domain) để loại bỏ hiện tượng đỗ 100% hình thức.

---

## 📋 Đặc Tả Kỹ Thuật Chi Tiết
- [x] **Xây dựng `eval_bigbim_risk.json`:**
  - Thiết kế 12 câu hỏi trắc nghiệm và tình huống thực tế bám sát `bigbim-risk/SKILL.md`:
    * Khoảng cách bảo trì kỹ thuật (Maintenance Clearance $\ge 900\text{mm}$).
    * Khoảng hở ống trần đến dầm/sàn $\ge 150\text{mm}$ cho siết đai ốc.
    * Xung đột phi hình học: Cao độ lắp đặt van ngăn cháy, hướng mở cửa thoát nạn và hành lang đệm.
    * Mâu thuẫn logic thuộc tính BBP (công suất chiller BBP-B1 vs BBP-B2, Unique ID drift).
    * Mâu thuẫn thông tin V2 giữa bản vẽ 2D và mô hình IFC4X3 (`IfcDistributionFlowElement`).
- [x] **Xây dựng `OrchestrationScorers` trong `scorers.py`:**
  - Bổ sung bộ Scorer kiểm tra các thuộc tính cốt lõi của agent coordination:
    * `SingleWriterInvariantScorer`: Single-Writer Pattern Invariants & Isolated Sandbox.
    * `ProgressiveDisclosureScorer`: AST Markdown Link Integrity & Progressive Disclosure Level 1/2/3.
    * `HandoffProtocolScorer`: Handoff Protocol, parent send_message & RACI Matrix alignment.
    * `get_orchestration_scorers()` factory function.
- [x] **Cập nhật `get_default_domain_scorers` trong `tuner.py`:**
  - Thêm nhánh nhận diện `["risk", "conflict"]` / `bigbim-risk` với bộ chấm mâu thuẫn thông tin V2 (`risk_conflict_audit`, `risk_anti_trap_hard_floor`, `risk_mitigation_guard`).
  - Thêm nhánh nhận diện từ khóa `["teamwork", "orchestrat", "platform", "handoff", "issue-tree"]` trả về `get_orchestration_scorers()`.
- [x] **Cập nhật `nightly_tuner_daemon.py`:**
  - Định tuyến tự động `bigbim-risk` về `eval_bigbim_risk.json` qua `_resolve_dataset_file` và `skill_dataset_map`.

---

## ✅ Tiêu Chí Nghiệm Thu (Acceptance Criteria)
1. [x] Kỹ năng `bigbim-risk` được định tuyến chính xác vào `eval_bigbim_risk.json` và đạt điểm $100.0\% \ge 85\%$ dựa trên tiêu chuẩn chuyên môn của nó.
2. [x] 4 kỹ năng Orchestration được chấm điểm bằng `OrchestrationScorers` thay vì regex mặc định chung chung (đạt 94.1% cho `ccba-teamwork`).
3. [x] 100% test suite vượt qua (495 passed), pass `verify-patch --preset code` và `verify-patch --preset eval`.
