---
proposal_id: "2026-07-02_ccba-local-to-notebooklm-sync"
type: "skill"
name: "ccba-local-to-notebooklm-sync"
status: "open"
priority: "Cao"
proposed_by_project: "CCBA Agent Platform (Hub)"
proposed_date: "2026-07-02"
applies_to:
  - "Tất cả"
---

## Mô tả
Kỹ năng cung cấp khả năng tự động quét cơ sở tri thức sạch cục bộ (dạng file `.docx`/`.md`), dọn dẹp Drive chung, tải lên và tự động chuyển đổi thành Google Docs trực tuyến trên Drive chung, đồng thời gán quyền chia sẻ công khai và kéo sang Google NotebookLM Cloud RAG để phục vụ hỏi đáp với độ chính xác cao và hỗ trợ đồng bộ thời gian thực (Real-time Sync).

## Vấn đề giải quyết
1.  **Lỗi phân quyền Drive:** Tránh lỗi bảo mật `API returned no data for Drive source` của API NotebookLM khi kéo tệp tin từ Google Drive cá nhân sang Cloud RAG.
2.  **Đồng bộ thủ công rườm rà:** Loại bỏ việc phải tải lên/tải xuống và chạy script đồng bộ thủ công mỗi khi thay đổi file luật gốc. Chuyển sang cơ chế Google Docs trực tuyến giúp NotebookLM tự động làm tươi ngữ cảnh.
3.  **Tách biệt tri thức sạch:** Giúp các dự án Spoke dễ dàng đóng gói và nạp tri thức chuyên môn đã biên soạn cục bộ lên RAG thay vì nạp bản thô cào từ Web.

## Giải pháp / Cấu trúc đề xuất
Tạo một Skill mới tại Hub `<hub_path>/.agents/skills/ccba-local-to-notebooklm-sync/`:
*   `SKILL.md`: Hướng dẫn cấu hình.
*   `scripts/sync_processed_docs.py`: Script tự động hóa luồng API Google Drive (với convert Google Docs và set permission `anyone/reader`) và API NotebookLM (`add_drive` có tham số `title`).

## Nội dung mẫu / Code mẫu
Mã nguồn Python thực thi cốt lõi:
```python
# Upload & convert docx sang Google Doc trên Drive
file_metadata = {
    "name": doc_title,
    "parents": [folder_id],
    "mimeType": "application/vnd.google-apps.document"
}
media = MediaFileUpload(str(file_path), mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document", resumable=True)
file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
file_id = file.get("id")

# Cấp quyền chia sẻ Anyone with link can view cho file Drive
service.permissions().create(
    fileId=file_id,
    body={"type": "anyone", "role": "reader"}
).execute()

# Kéo từ Drive sang NotebookLM
source = await client.sources.add_drive(
    notebook_id=NOTEBOOK_ID,
    file_id=file_id,
    title=doc_title,
    wait=True
)
```
