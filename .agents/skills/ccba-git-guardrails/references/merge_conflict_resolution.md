# ccba-resolving-merge-conflicts — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Cẩm nang giải quyết xung đột mã nguồn Git merge an toàn
> **Mô tả gốc:** Use when you need to resolve an in-progress git merge/rebase conflict.

---

# Quy Trình Xử Lý Xung Đột Git (/ccba-resolving-merge-conflicts)

Quy trình chuẩn hóa xử lý xung đột phân nhánh (merge/rebase conflict) bảo toàn tính toàn vẹn của mã nguồn, tuân thủ nguyên tắc không làm mất mát dữ liệu và không tự ý thay đổi ý định thiết kế.

## Quy tắc an toàn bắt buộc (Safety Invariants)
- **Tuyệt đối không sử dụng `git merge --abort` hoặc `git rebase --abort`** khi chưa có yêu cầu rõ ràng từ người dùng.
- **Không tự ý đẩy mã nguồn (`git push`)**: Sau khi giải quyết xong conflict ở local, phải báo cáo cho người dùng phê duyệt trước khi push.
- **Bảo toàn Single Source of Truth (SSOT)**: Nếu có xung đột về tài liệu quy chuẩn hoặc kiến trúc, luôn ưu tiên phiên bản có ADR hoặc RFC bảo trợ.

---

## Các bước thực hiện

### Bước 1: Khảo sát trạng thái và phạm vi xung đột
1. Kiểm tra trạng thái git hiện tại bằng `git status` để xác định danh sách các tệp đang gặp xung đột (unmerged paths).
2. Phân loại các tệp xung đột thành: mã nguồn (`.py`, `.ts`), tài liệu (`.md`), hoặc tệp cấu hình (`.yaml`, `.toml`).
3. Đối chiếu sơ bộ các vùng xung đột bằng `git diff --check`.
- **Tiêu chí hoàn thành:** Lập danh sách đầy đủ các tệp xung đột kèm phân loại loại tệp.

### Bước 2: Truy vết nguồn gốc và ý định thay đổi (Root Intent Analysis)
1. Đọc lịch sử commit gần nhất của cả 2 nhánh thông qua `git log -n 5 --oneline` để nắm bắt mục tiêu của từng nhánh.
2. Kiểm tra Pull Request hoặc ticket liên quan nếu có để hiểu bối cảnh nghiệp vụ.
3. Xác định rõ ràng: phần mã nguồn nào là của nhánh hiện tại (`ours` / `HEAD`), phần nào đến từ nhánh đang tích hợp (`theirs` / incoming).
- **Tiêu chí hoàn thành:** Xác định được ý định thiết kế của cả 2 phía cho từng tệp xung đột.

### Bước 3: Hòa giải chi tiết từng khối xung đột (Hunk Resolution)
1. Mở từng tệp xung đột và định vị toàn bộ các thẻ đánh dấu (`<<<<<<<`, `=======`, `>>>>>>>`).
2. Kết hợp hợp lý logic của cả 2 bên nếu chúng bổ trợ cho nhau (additive changes).
3. Nếu hai thay đổi triệt tiêu hoặc mâu thuẫn trực tiếp, ưu tiên nhánh mục tiêu chính và ghi nhận lý do đánh đổi (trade-off).
4. Xóa sạch 100% các ký hiệu xung đột của Git trước khi lưu file.
- **Tiêu chí hoàn thành:** Toàn bộ conflict markers được gỡ bỏ hoàn toàn, logic hợp nhất mạch lạc.

### Bước 4: Kiểm thử và xác thực tự động (Automated Verification)
1. Chạy công cụ kiểm tra cú pháp và định dạng: `ruff check` hoặc `flake8`.
2. Chạy kiểm tra kiểu tĩnh: `mypy` trên các file bị ảnh hưởng.
3. Chạy bộ kiểm thử tự động của dự án: `pytest` cho các test suite liên quan.
- **Tiêu chí hoàn thành:** 100% các bài kiểm thử và kiểm tra tĩnh vượt qua không lỗi.

### Bước 5: Đóng gói commit và báo cáo giải trình
1. Đưa các tệp đã giải quyết vào khu vực chờ: `git add <file>`.
2. Tạo commit giải quyết xung đột ở local (ví dụ: `git commit -m "fix(merge): resolve conflicts between branch-a and branch-b"`).
3. Lập báo cáo tóm tắt gửi người dùng: danh sách file đã sửa, giải pháp dung hòa đã chọn, kết quả kiểm thử tự động.
- **Tiêu chí hoàn thành:** Commit hoàn tất tại local, báo cáo chi tiết được gửi và chờ phê duyệt push từ người dùng.
