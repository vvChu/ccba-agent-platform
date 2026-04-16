## Session Learnings - Kiến thức tích lũy

## Cập nhật gần nhất: 2026-04-16

---

## Patterns (Mẫu tốt)

### Quad-View Generative Audit
- **Ngữ cảnh**: Khi cần kiểm tra đụng độ giữa nhiều bản vẽ (Arch, KC, MEP, PCCC) với nhau mà không có mô hình 3D.
- **Vấn đề giải quyết**: LLMs xử lý rất kém số liệu kích thước và text trải trên 4 pdf khác nhau.
- **Giải pháp**: 
  1. Render từng trang PDF ra ảnh PNG (dpi 150-300).
  2. Gộp 4 ảnh thành 1 mảng 2x2 (Quad-View) với nhãn tên rõ ràng bằng hàm `CompositeBuilder`.
  3. Đẩy 1 ảnh duy nhất (Quad-view) vào multimodal API. AI có khả năng liên kết không gian (Spatial Reasoning) giữa 4 góc nhìn cực kỳ xuất sắc.
- **Nguồn**: QC Audit Khối B BV NTP

### Concurrent Batch AI Processing
- **Ngữ cảnh**: Chạy LLM audit trên quy mô lớn nhiều object/level.
- **Vấn đề giải quyết**: Thời gian chạy tuần tự quá lâu.
- **Giải pháp**: Xây dựng hàm `async` tạo array mapping và gọi `asyncio.gather(*tasks)` để đẩy 5 request lên LiteLLM Gateway đồng thời.
- **Nguồn**: Chạy Batch Audit cho Tầng 1, 2, 3, Mái Khối B.

### Context-Aware Workflow Commands
- **Ngữ cảnh**: Xây dựng Slash Command Workflow (như `/run-qc-pipeline`) yêu cầu truyền đường dẫn project hiện tại.
- **Vấn đề giải quyết**: User phải gõ thủ công đường dẫn rất dài, dễ sai sót.
- **Giải pháp**: Hướng dẫn Agent phân tích `<ADDITIONAL_METADATA>` để trích xuất `TARGET_PROJECT` tự động dựa trên file/cửa sổ đang mở, tự động chèn vào chuỗi lệnh bọc `// turbo`.
- **Nguồn**: Thiết kế workflow `/run-qc-pipeline`.

### Data Hand-off Automation (Zero-Touch UX)
- **Ngữ cảnh**: Chuyển giao dữ liệu từ bước Discovery (OCR Text) sang bước Batch Orchestrator (Render API).
- **Vấn đề giải quyết**: Tránh để con người chạm vào file map dữ liệu như CSV, sinh ra Human Error (gõ nhầm mã bản vẽ).
- **Giải pháp**: Buộc Output chuẩn của Skill 1 (e.g. `Coordination_Matrix.csv`) phải là Input chuẩn của Skill 2. Xóa bỏ hoàn toàn Hardcode mapping.
- **Nguồn**: SDK `ccba-ai-qc-batch-orchestrator`.

---

## Solutions (Giải pháp tham chiếu)

### Multimodal Call qua AI Gateway
- **Vấn đề**: Hàm `ai.chat` (LiteLLM wrapper chung) bị lỗi kwargs `images` khi model endpoint chối từ.
- **Giải pháp**: Sử dụng client wrapper của `openai.OpenAI` và đưa chuỗi base64 vào format của Vision API:
```text
messages=[{
    "role": "user",
    "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": { "url": f"data:image/png;base64,{b64}" }},
    ]
}]
```
- **Liên kết**: `audit_engine.py`

---

## Configurations (Cấu hình tối ưu)

| Setting | Value | Lý do | Áp dụng khi |
| --------- | ------- | ------- | ------------- |
| Render DPI | 150 | Giảm thời gian load Quad-View nhưng vẫn đủ nét text nhỏ | AI OCR / Vision |
| Concurrency | 4-5 reqs | AI Gateway local DGX Server chịu tải tốt | Xử lý đa tầng |

## 📋 Session Retrospective Summary (Updated)

### Phiên làm việc
- **Ngày**: 2026-04-16
- **Mục tiêu**: Tích hợp AI-powered Engineering QC Pipeline vào Hub Platform và cấu trúc hóa dưới dạng tự động hóa khép kín (Workflow Command).
- **Kết quả**: ✅ Thành công. Batch Multi-Level QC hoàn thành trong ~60s; ra mắt SDK Orchestrator và `/run-qc-pipeline`.

### Kiến thức mới
- [x] 4 patterns mới (Quad-View, Concurrent UI, Context-Aware Workflow, Data Hand-off)
- [x] 1 solutions mới (OpenAI Vision proxy)

### Đề xuất cập nhật đã hoàn thành
- [x] Cập nhật user_global: Có - Thêm quy định luật PCCC (QCVN 06).
- [x] Tạo workflow mới: **Có** - Đã tạo `run-qc-pipeline.md`.
- [x] Đề xuất/Tạo Skills mới: **Có** - Đã tạo `ccba-ai-qc-batch-orchestrator`.

### Ghi chú cho phiên tiếp theo
Dùng báo cáo tự động QCVN 06 để trao đổi với PCCC và chạy lại `/run-qc-pipeline` ngay khi file thiết kế mới cập bến mà không cần chỉnh sửa code.
