# ccba-update-legal-registry — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Quy trình đồng bộ định kỳ legal registry và cập nhật cơ sở dữ liệu văn bản pháp lý
> **Mô tả gốc:** Tự động đồng bộ các thay đổi pháp lý từ legal_registry.yaml lên Google NotebookLM (hỗ trợ lưu trữ qua Google Drive chung).

---

# Lệnh Slash Command `/ccba-update-legal-registry`

Đồng bộ hóa tự động tri thức pháp luật xây dựng (VBPL) từ máy cục bộ lên Google NotebookLM Cloud RAG.

## Các Bước thực thi của Agent

Khi lệnh này được kích hoạt, Agent thực hiện theo quy trình sau:

### Bước 1: Tra cứu Notebook ID (Context Lookup)
1. Đọc tệp cấu hình cục bộ tại `.md/workspace_context.yaml` để tìm giá trị `notebook_id`.
2. Nếu không tìm thấy hoặc tệp không tồn tại, kiểm tra biến môi trường hệ thống `NOTEBOOKLM_ID`. Chỉ hỏi người dùng làm phương án dự phòng cuối cùng nếu cả hai nguồn đều trống.

**Tiêu chí hoàn thành:** Xác định được Notebook ID hợp lệ.

### Bước 2: Kiểm tra môi trường & Cấp quyền
1. Xác nhận sự tồn tại của biến cookie `NOTEBOOKLM_SESSION_COOKIE` hoặc tệp cấu hình `NOTEBOOKLM_COOKIES_JSON` trong môi trường hệ thống.
2. Nếu người dùng chỉ định đồng bộ qua Google Drive (`--use-drive`), kiểm tra xác thực Google Drive qua Application Default Credentials (ADC):
   ```bash
   gcloud auth application-default login --scopes="https://www.googleapis.com/auth/drive"
   ```

**Tiêu chí hoàn thành:** Xác nhận session cookie và quyền môi trường đầy đủ.

### Bước 3: Chạy Script Đồng bộ
Thực thi lệnh Python đồng bộ với Notebook ID đã xác định:
```bash
python scripts/sync_notebooklm_knowledge.py --notebook-id <notebook_id> [--upload-drive]
```

**Tiêu chí hoàn thành:** Script sync chạy trả về Exit Code 0.

## Tiêu chí Hoàn thành (Completion Criteria)
- **Kiểm chứng thành công**: Script chạy trả về mã thoát `Exit Code 0` (hoặc thông báo `Sync completed successfully` trên console output).
- **Attribution & Disclaimer**: Kết quả đầu ra hiển thị bảng thống kê số lượng nguồn được nạp mới/xóa bỏ, đồng thời bắt buộc đính kèm dòng bản quyền CCBA và Disclaimer pháp lý ở cuối tệp/tin nhắn phản hồi.
- **Xử lý lỗi**: Nếu gặp lỗi xác thực cookie (401/403) hoặc lỗi kết nối, in rõ thông báo lỗi chi tiết và hướng dẫn người dùng cập nhật lại Token môi trường thay vì im lặng kết thúc.
