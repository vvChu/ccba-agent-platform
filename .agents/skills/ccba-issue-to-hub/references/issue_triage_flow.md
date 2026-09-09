# ccba-triage — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Quy trình phân loại, gắn nhãn và sàng lọc sự cố kỹ thuật (issues)
> **Mô tả gốc:** Sàng lọc sự cố và yêu cầu (Issues/PRs) qua các trạng thái phân loại và soạn thảo brief cho Agent.

---

# Quy trình Sàng lọc Sự cố và Yêu cầu (Triage)

Kỹ năng này giúp điều phối và sàng lọc các sự cố hoặc yêu cầu tính năng mới (Issues/PRs) trên Issue Tracker (hoặc danh sách file cục bộ), chuyển đổi trạng thái của chúng qua các phân vai kiểm soát chất lượng, và soạn thảo tài liệu tóm tắt kỹ thuật (Agent Brief) cho phiên làm việc tiếp theo.

## Các tài liệu bổ trợ (References)

- [agent-brief.md](./agent-brief.md) — Hướng dẫn soạn thảo Agent Brief bền vững.
- [out-of-scope.md](./out-of-scope.md) — Hướng dẫn ghi nhận và đối chiếu các tính năng đã bị từ chối trong `.out-of-scope/`.

---

## Phân vai Trạng thái (Roles & States)

**2 Phân loại chính (Categories):**
- `bug`: Sự cố/lỗi hệ thống cần sửa đổi.
- `enhancement`: Yêu cầu nâng cấp hoặc tính năng mới.

**5 Trạng thái điều phối (States):**
- `needs-triage`: Mới tiếp nhận, cần đánh giá sơ bộ.
- `needs-info`: Cần người báo cáo bổ sung thêm thông tin.
- `ready-for-agent`: Đã đặc tả đầy đủ thông tin, kèm Agent Brief, sẵn sàng để Agent AFK thực thi.
- `ready-for-human`: Cần lập trình viên (người thật) xử lý (do tính phức tạp hoặc yêu cầu bảo mật).
- `wontfix`: Đã bị từ chối hoặc không được thực hiện.

---

## Quy trình thực hiện (Process)

1. **Hiển thị danh sách cần chú ý:**
   - Truy vấn danh sách sự cố từ Issue Tracker hoặc thư mục cục bộ `.md/knowledge/issues/` (nếu chạy offline, đảm bảo tự động tạo thư mục này nếu chưa tồn tại). Hiển thị các sự cố chưa được phân loại, đang ở trạng thái `needs-triage` hoặc `needs-info` đã có phản hồi mới từ người báo cáo.
   - **Tiêu chí hoàn thành:** In ra danh sách sự cố phân nhóm rõ ràng kèm tiêu đề và mã định danh tương ứng.

2. **Khảo sát ngữ cảnh của Sự cố/PR cụ thể:**
   - Đọc chi tiết nội dung sự cố, lịch sử thảo luận và mã nguồn liên quan. 
   - Đối chiếu với cơ sở tri thức `.out-of-scope/` (hoặc thư mục tri thức tương đương cục bộ của dự án tại `.md/knowledge/out-of-scope/` nếu chạy offline, đảm bảo tạo thư mục này nếu chưa có) để phát hiện trùng lặp với các yêu cầu đã bị từ chối trong quá trình lịch sử. Khảo sát codebase để đảm bảo tính năng chưa từng được triển khai.
   - **Tiêu chí hoàn thành:** Đưa ra khuyến nghị phân loại (category) và trạng thái (state) đề xuất kèm theo lý do kỹ thuật chi tiết.

3. **Xác thực và Tái lập lỗi (Verification):**
   - Đối với lỗi (`bug`): Tái lập lỗi dựa trên mô tả của người báo cáo. Đối với PR: Checkout mã nguồn của PR và chạy các bộ kiểm thử tương ứng.
   - **Tiêu chí hoàn thành:** Ghi nhận báo cáo xác thực chi tiết (lỗi tái lập thành công hay thất bại, kèm đường dẫn dòng code gây lỗi).

4. **Áp dụng kết quả điều phối:**
   - Cập nhật nhãn trạng thái tương ứng qua GitHub CLI hoặc cập nhật tệp cục bộ.
   - Nếu chuyển sang `ready-for-agent`, bắt buộc đăng tải Agent Brief theo cấu trúc chuẩn tại [agent-brief.md](./agent-brief.md), bao gồm việc đánh giá độ phức tạp và đề xuất định tuyến thực thi phù hợp (`/ccba-implement`, `/boost`, hoặc `/ccba-teamwork` / `/teamwork-preview`).
   - **Quy chuẩn đăng tải bình luận an toàn (Safe Input Invariant):** Khi đăng tải Agent Brief hoặc bình luận lên GitHub qua `gh issue comment`, bắt buộc ghi nội dung vào tệp tạm thời trong `.md/scratch/comment_<id>.md` và dùng cờ `-F` (`gh issue comment <id> -F .md/scratch/comment_<id>.md`) thay vì truyền chuỗi trực tiếp qua `--body "..."` để bảo toàn định dạng và tránh bị bộ lọc command-line chặn.
   - Nếu chuyển sang `wontfix` do bị từ chối, cập nhật lý do và lưu trữ khái niệm vào thư mục `.out-of-scope/` (hoặc thư mục cục bộ `.md/knowledge/out-of-scope/`) theo tài liệu hướng dẫn [out-of-scope.md](./out-of-scope.md).
   - **Tiêu chí hoàn thành:** Trạng thái sự cố được cập nhật thành công, bổ sung Agent Brief (kèm đề xuất thực thi) hoặc tài liệu lưu trữ từ chối tương ứng.


---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
