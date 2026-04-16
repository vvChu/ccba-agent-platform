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

## 📋 Session Retrospective Summary

### Phiên làm việc
- **Ngày**: 2026-04-16
- **Mục tiêu**: Tích hợp AI-powered Engineering QC Pipeline vào tài liệu thiết kế phức tạp (BV NTP)
- **Kết quả**: ✅ Thành công. Batch Multi-Level QC Quad-View hoàn thành trong ~60s.

### Kiến thức mới
- [x] 2 patterns mới (Quad-View, Concurrent UI)
- [x] 1 solutions mới (OpenAI Vision proxy)

### Đề xuất cập nhật
- [x] Cập nhật user_global: Có - Thêm quy định luôn check legal-registry cho mảng PCCC (QCVN 06).
- [ ] Tạo workflow mới: Không
- [ ] Cập nhật workflow: Không

### 🚀 Đề xuất Skills mới cho Platform
- [x] **ccba-ai-qc-batch-orchestrator**: Có thể tách luồng batch processing của `run_batch_audit_khoib.py` đưa vào SDK gốc để hỗ trợ vòng lặp Automation Pipeline một cách native, giúp các Spoke/Dự án khác gọi lệnh dễ dàng không cần build file script dài.

### Ghi chú cho phiên tiếp theo
Dùng báo cáo QCVN 06 để trao đổi với PCCC và chờ bản vẽ PCCC Update để Audit lại Tầng 1-Tầng Nội Trú.

