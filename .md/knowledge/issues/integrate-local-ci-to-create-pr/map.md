# Wayfinder Map: Tích hợp Local CI Evaluation Gates vào Workflow /ccba-create-pr

## Điểm đích (Destination)
Tích hợp bắt buộc quy trình chạy Local CI Evaluation Gates (`.venv\Scripts\python scripts/run_harness_evals.py`) vào Bước 1 của workflow `/ccba-create-pr` (Shift-Left Gate). Đảm bảo mã nguồn ĐÃ PASS 100% tại local TRƯỚC KHI thực hiện `git push` và tạo Pull Request.

---

## Ghi chú (Notes)
- Tuân thủ Hiến pháp CCBA Layer 1 (`.agents/AGENTS.md`).
- Áp dụng nguyên tắc Reuse-First Gate (tái sử dụng 100% `scripts/run_harness_evals.py` và `validate_skills.py`).
- Mọi thay đổi workflow phải qua phê duyệt `implementation_plan.md`.

---

## Quyết định đã chốt (Decisions so far)
- **[Ticket 1: Nghiên cứu Vị trí Tích hợp Tối ưu](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/integrate-local-ci-to-create-pr/map.md#ticket-1)** — *Đã hoàn thành*  
  Xác định tích hợp vào Bước 1 của `/ccba-create-pr` (Shift-Left Execution: Local CI Check $\rightarrow$ Push $\rightarrow$ PR Create).
- **[Ticket 2: Cập nhật Workflow ccba-create-pr.md](file:///d:/GitHubProjects/ccba-agent-platform/.agents/workflows/ccba-create-pr.md)** — *Đã hoàn thành*  
  Đã đưa bước chạy Local CI Eval Gates (`run_harness_evals.py`) lên Bước 1 trước khi push.
- **[Ticket 3: Bổ sung Test Suite Kiểm tra Quy trình ccba-create-pr (test_create_pr_workflow.py)](file:///d:/GitHubProjects/ccba-agent-platform/tests/test_create_pr_workflow.py)** — *Đã hoàn thành*  
  Đã viết unit test `tests/test_create_pr_workflow.py` kiểm định thành công (1 passed in 0.02s).

---

## Sương mù chiến trận / Chưa xác định rõ (Not yet specified)
- *Tất cả các ticket trong lộ trình Wayfinder đã được giải quyết hoàn tất 100%.*

---

## Ngoài phạm vi (Out of scope)
- Thay đổi logic nội bộ của `scripts/run_harness_evals.py` (do script harness đã hoạt động ổn định).
