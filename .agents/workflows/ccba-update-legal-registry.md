---
name: ccba-update-legal-registry
description: Tự động đồng bộ các thay đổi pháp lý từ legal_registry.yaml lên Google NotebookLM (hỗ trợ lưu trữ qua Google Drive chung).
disable-model-invocation: true
keywords: [legal, sync, update, notebooklm, drive]
---

# Lệnh Slash Command `/ccba-update-legal-registry`

Kích hoạt luồng đồng bộ hóa tự động tri thức pháp luật xây dựng (VBPL) từ máy cục bộ lên Google NotebookLM Cloud RAG. Do là lệnh chạy theo yêu cầu trực tiếp, nó được thiết lập `disable-model-invocation: true` để tối ưu hóa context load.

## Cách thức Sử dụng

Agent thực thi lệnh đồng bộ hóa thông qua script của Platform:

```bash
python [hub_path]/scripts/legal_sync.py --notebook-id <notebook_id> [--use-drive] [--drive-folder <folder_id>] [--download-pdf]
```

## Các Bước thực thi của Agent

Khi lệnh này được kích hoạt, Agent tiếp nhận thực hiện theo các bước:

1. **Kiểm tra môi trường & Cấp quyền:**
   - Kiểm tra xem các biến cookie `NOTEBOOKLM_SESSION_COOKIE` hoặc `NOTEBOOKLM_COOKIES_JSON` đã được khai báo chưa.
   - Nếu sử dụng tùy chọn `--use-drive`, kiểm tra xác thực Google Drive qua ADC:
     ```bash
     gcloud auth application-default login --scopes="https://www.googleapis.com/auth/drive"
     ```
2. **Chạy Script:** Thực thi lệnh python đồng bộ.
3. **Hậu xử lý:** Thống kê số nguồn nạp mới/dọn dẹp, in dòng Attribution và Disclaimer của CCBA ở cuối.
