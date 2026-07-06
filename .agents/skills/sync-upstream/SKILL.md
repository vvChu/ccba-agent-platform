---
name: sync-upstream
description: Kiểm tra cập nhật và đồng bộ tri thức từ các repository claudekit và mattpocock thượng nguồn.
disable-model-invocation: true
category: utilities
keywords: [sync, upstream, update, porting]
metadata:
  author: CCBA
  version: "1.1.0"
---

# Kỹ năng: Đồng bộ hóa Thượng nguồn (Upstream Sync)

Kỹ năng này thực hiện việc kiểm tra, tải về các bản cập nhật mới từ các kho chứa thượng nguồn (`claudekit-engineer`, `claudekit-marketing`, và `mattpocock/skills`) trên remote GitHub, tiến hành phân tích sự thay đổi bằng AI Gateway để tự động cập nhật báo cáo khuyến nghị di chuyển tính năng.

## Quy trình Thực hiện (Process)

### 1. Đồng bộ hóa mã nguồn Upstream
- Chạy script Python để tự động clone/fetch các repository thượng nguồn về thư mục tạm cục bộ `.md/scratch/repos/` ở chế độ kiểm tra:
  ```powershell
  python scripts/check_claudekit_updates.py --check-only
  ```
- **Tiêu chí hoàn thành:** Script chạy thành công với exit code 0. Toàn bộ mã nguồn các repo đích được cập nhật đầy đủ và in ra danh sách các cập nhật có sẵn kèm các SHA tương ứng.
- **Cơ chế tự chữa lành (Self-Healing):** Nếu script thất bại do lỗi Git corruption (chỉ số index lỗi) hoặc lỗi đường truyền mạng ngắt quãng, Agent phải thực hiện xóa sạch thư mục tạm tương ứng `.md/scratch/repos/<repo-name>` và chạy lại lệnh để clone mới (Clean Clone). Nếu vẫn lỗi sau 2 lần thử, báo cáo lại người dùng.

### 2. Nghiên cứu và Phân tích Khuyến nghị
- Liệt kê danh sách các tệp tin mới/nâng cấp được phát hiện bằng cách so sánh hiệu số giữa Local SHA và Remote SHA (ví dụ chạy lệnh: `git diff --name-only <local-sha>..<remote-sha>` trên repository tương ứng) và trình bày ngắn gọn cho người dùng.
- Hỏi ý kiến người dùng trước khi thực thi quét sâu: *"Tôi tìm thấy N file mới. Bạn có muốn phân tích chi tiết bằng AI Gateway để cập nhật báo cáo khuyến nghị không?"*
- Nếu người dùng đồng ý, chạy script phân tích cấu trúc của các repository thượng nguồn bằng AI Gateway mà không kèm flag `--check-only`:
  ```powershell
  python scripts/check_claudekit_updates.py
  ```
- **Tiêu chí hoàn thành:** Script chạy hoàn tất, tự động gọi trình đánh giá cập nhật dữ liệu mới vào vùng được chỉ định tại tệp báo cáo khuyến nghị.

### 3. Đối soát và Trình bày Kết quả (Parse-Protection)
- Đọc nội dung tệp tin báo cáo khuyến nghị tại [port_recommendations.md](../../../.md/knowledge/port_recommendations.md).
- **Quy tắc bảo vệ dữ liệu (Parse-Protection):** Chỉ ghi đè dữ liệu phân tích tự động vào khu vực đánh dấu `<!-- AUTO-GENERATED-START -->...<!-- AUTO-GENERATED-END -->`. Tuyệt đối giữ nguyên vẹn khu vực ghi chú thủ công của kỹ sư tại `<!-- DEVELOPER-NOTES-START -->...<!-- DEVELOPER-NOTES-END -->`.
- Trình bày tóm tắt kết quả phân tích cập nhật cho người dùng.
- **Tiêu chí hoàn thành:** Bảng tóm tắt kết quả hiển thị chính xác trên chat và tệp `port_recommendations.md` được ghi nhận cập nhật mà không làm mất mát vùng ghi chú thủ công của kỹ sư.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
