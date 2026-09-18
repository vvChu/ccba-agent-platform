# Ticket 04: Xây Dựng Bộ Đề Thi & Scorer Chuyên Biệt Cho Coordination V2 & Orchestration

- **Type:** Research / Prototype (AFK & HITL)
- **Status:** open
- **Assignee:** Unassigned
- **Target Seam:** `.agents/skills/ccba-eval-gate/test_cases/eval_bigbim_risk.json`, `packages/ccba-harness/src/ccba_harness/evals/scorers.py`
- **Reference:** Báo cáo nghiên cứu `/boost` ngày 18/09/2026 (REC-07), `bigbim-risk/SKILL.md`

---

## 🎯 Mục Tiêu
Chấm dứt việc ép kỹ năng `bigbim-risk` thi đề phân loại Uniclass; đồng thời bổ sung bộ Scorer chuyên biệt cho các kỹ năng điều phối đa tác tử (Orchestration Domain) để loại bỏ hiện tượng đỗ 100% hình thức.

---

## 📋 Đặc Tả Kỹ Thuật Chi Tiết
- [ ] **Xây dựng `eval_bigbim_risk.json`:**
  - Thiết kế 10-15 câu hỏi trắc nghiệm và tình huống thực tế bám sát `bigbim-risk/SKILL.md`:
    * Khoảng cách bảo trì kỹ thuật (Maintenance Clearance $\ge 900\text{mm}$).
    * Xung đột phi hình học: Cao độ lắp đặt van ngăn cháy, hướng mở cửa thoát nạn và hành lang đệm.
    * Mâu thuẫn thông tin V2 giữa bản vẽ 2D và mô hình IFC4X3.
- [ ] **Xây dựng `OrchestrationScorers` trong `scorers.py`:**
  - Bổ sung bộ Scorer kiểm tra các thuộc tính cốt lõi của agent coordination:
    * Single-Writer Pattern Invariants.
    * AST Markdown Link Integrity & Progressive Disclosure.
    * Handoff Protocol & RACI Matrix alignment.
- [ ] **Cập nhật `get_default_domain_scorers` trong `tuner.py`:**
  - Thêm nhánh nhận diện từ khóa `["teamwork", "orchestrat", "platform-loader", "handoff", "issue-tree"]` trả về `OrchestrationScorers`.

---

## ✅ Tiêu Chí Nghiệm Thu (Acceptance Criteria)
1. Kỹ năng `bigbim-risk` được định tuyến chính xác vào `eval_bigbim_risk.json` và đạt điểm $\ge 85\%$ dựa trên tiêu chuẩn chuyên môn của nó.
2. 4 kỹ năng Orchestration được chấm điểm bằng `OrchestrationScorers` thay vì regex mặc định chung chung.
