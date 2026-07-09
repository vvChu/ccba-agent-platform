# CCBA Release Gate & Copilot Audit — Dynamic Rule

## 1. Rào chắn đối soát PR (Release Gate Audit)
* Trước khi thực hiện merge bất kỳ Pull Request nào (trừ các PR nâng cấp thư viện tự động dependabot/chore đã pass CI và không có phản biện ngoài), Agent **bắt buộc** phải chạy công cụ đối soát `python scripts/audit_pr_comments.py` để quét toàn bộ inline review và PR-level comments từ Copilot hoặc các reviewers khác.
* **Quy tắc dừng chờ Copilot**: Khi kiểm tra trạng thái PR qua `gh pr view <PR>`, nếu thấy người đánh giá `copilot-pull-request-reviewer` ở trạng thái `(Requested)` (chưa hoàn thành review), Agent **bắt buộc phải dừng lại và chờ** (sử dụng công cụ `schedule` để hẹn giờ kiểm tra lại sau mỗi 30s-60s). Thời gian chờ tối đa (timeout) là 3 phút; nếu quá thời gian này mà Copilot vẫn chưa chạy xong, Agent mới được báo cáo người dùng xin ý kiến bypass.
* Phải tiến hành sửa lỗi đối với các góp ý hợp lý (VALID), hoặc viết giải trình đối với các góp ý sai lệch (INVALID) vào tài liệu bàn giao `walkthrough.md` và nhận được sự đồng thuận tường minh của người dùng trước khi merge.
* Ghi nhận chi tiết kết quả xử lý bình luận của Copilot vào tài liệu bàn giao `walkthrough.md`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
