---
name: ccba-update-legal-registry
description: Tự động đồng bộ các thay đổi pháp lý từ legal_registry.yaml lên Google NotebookLM (hỗ trợ lưu trữ qua Google Drive chung).
user-invocable: true
keywords: [legal, sync, update, notebooklm, drive]
---

# Lệnh Slash Command `/ccba-update-legal-registry`

Kích hoạt luồng đồng bộ hóa tự động tri thức pháp luật xây dựng (VBPL) từ máy cục bộ lên Google NotebookLM Cloud RAG.

## Cách thức Sử dụng

Kỹ sư hoặc Agent chạy lệnh trên Terminal hoặc yêu cầu Agent thực thi dưới dạng:

```bash
python scripts/legal_sync.py --notebook-id <notebook_id> [--use-drive] [--drive-folder <folder_id>] [--download-pdf]
```

## Các Bước thực thi của Agent

Khi lệnh này được kích hoạt, Agent tiếp nhận phải làm theo các bước sau:

1.  **Kiểm tra môi trường & Cấp quyền:**
    *   Đọc biến môi trường `NOTEBOOKLM_SESSION_COOKIE` hoặc `NOTEBOOKLM_COOKIES_JSON`.
    *   Nếu sử dụng `--use-drive`, kiểm tra xem kỹ sư đã xác thực ADC bằng lệnh sau chưa:
        `gcloud auth application-default login --scopes="https://www.googleapis.com/auth/drive"`
2.  **Chạy Script:** Thực thi lệnh Python ở trên để chạy đồng bộ.
3.  **Hậu xử lý:** 
    *   In kết quả thống kê (số nguồn đã nạp mới, số nguồn đã dọn dẹp).
    *   Đưa ra các cảnh báo (nếu có file thiếu không tải được).
    *   Chèn dòng Attribution và Disclaimer của CCBA ở cuối phản hồi.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
