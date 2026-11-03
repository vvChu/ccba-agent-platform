# CCBA Release Gate & Opt-In Advisory AI Audit — Dynamic Rule

> **Tài liệu chuẩn gốc (SSOT):** Mục 13.B.3 (*Zero-Red-Merge*) và Mục 19.2 (*Opt-In Read-Only Advisory AI Review*) trong `docs/rules/execution_coordination_guardrails.md`, kết hợp `.github/bugbot-rules.md`.

## 1. Cổng Merge Tất Định Mặc Định (Default Deterministic Merge Gate)
* Trước khi thực hiện merge bất kỳ Pull Request nào (bao gồm cả PR nâng cấp thư viện từ `dependabot`), Agent **bắt buộc** phải đảm bảo:
  1. **100% Deterministic CI Checks xanh (`PASS`)**: Kiểm tra qua `gh pr checks <id> --watch`. Tuyệt đối không merge khi còn bất kỳ check nào ở trạng thái `FAIL` hoặc `PENDING` (*Zero-Red-Merge*).
  2. **Không còn `reviewRequests` đang chờ**: Trường `reviewRequests` trên PR phải rỗng.

## 2. Cổng Kiểm Toán AI Review Tùy Chọn (Opt-In Read-Only Advisory Gate)
* Theo Mục 19.2 của `docs/rules/execution_coordination_guardrails.md`, các trình duyệt mã nguồn AI (GitHub Copilot, Cursor Bugbot) vận hành ở chế độ **Read-Only Advisory (Chỉ đọc & Tư vấn)** và chỉ kích hoạt **opt-in** để chống bão quota.
* Khi PR có kích hoạt opt-in AI Review (được gắn nhãn `ai-review-requested`, gọi qua `/ccba-ai-review`, hoặc có `copilot-pull-request-reviewer` trong `reviewRequests` / `reviews`), Agent chạy công cụ đối soát:
  ```bash
  python scripts/validation/audit_pr_comments.py
  ```
* **Xử lý theo Mã thoát thực tế của `audit_pr_comments.py`**:
  - **`Exit Code 0` (`CLEAN`)**: Không có nhận xét tồn đọng hoặc toàn bộ đã được đối soát; đủ điều kiện tiếp tục merge.
  - **`Exit Code 2` (`PENDING`)**: `copilot-pull-request-reviewer` đang nằm trong `reviewRequests`. Agent sử dụng công cụ `schedule` hẹn giờ kiểm tra lại sau mỗi `30s-60s` (tối đa 3 phút); nếu quá thời hạn mà Copilot vẫn treo, gỡ yêu cầu review hoặc báo cáo người dùng.
  - **`Exit Code 1` (`CHANGES_RECOMMENDED`)**: Có nhận xét trong `reviews` (`Changes recommended` / `🟡` / `CHANGES_REQUESTED`), `inline_comments` hoặc `pr_comments` chưa được đối soát. Agent đánh giá từng nhận xét theo chế độ **Read-Only Advisory**:
    1. Nếu **`VALID`** (lỗi thực tế trong phạm vi PR): Sửa mã nguồn, bổ sung regression test và đẩy commit mới.
    2. Nếu **`INVALID` / Out-of-Scope**: Ghi nhận phản biện kèm dẫn chứng `file:line` và mã định danh (`review_id` hoặc comment `id`) vào tài liệu bàn giao `walkthrough.md` (hoặc `.md/walkthrough.md`) để `check_if_resolved_in_code_or_walkthrough()` xác nhận đã giải quyết.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
