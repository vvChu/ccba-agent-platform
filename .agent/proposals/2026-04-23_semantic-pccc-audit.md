---
proposal_id: "2026-04-23_semantic-pccc-audit"
type: "skill"
name: "Semantic PCCC Audit"
status: "open"
priority: "Cao"
proposed_by_project: "2024-04 Ban DD HCM - BV NTP (Spoke)"
proposed_date: "2026-04-23"
applies_to:
  - "Thẩm tra thiết kế"
  - "Quản lý chất lượng"
---
## Mô tả

Hệ thống Thẩm tra/Audit lỗi thiết kế đa bộ môn (PCCC, MEP, Kiến trúc) thông qua cơ chế Semantic Map-Reduce. Sử dụng LLM cục bộ để tự động băm nhỏ, phân tích chéo và gộp kết quả đánh giá kỹ thuật quy mô lớn.

## Vấn đề giải quyết

Khi phân tích hồ sơ kỹ thuật lớn (hàng chục file, trăm nghìn token), LLM thường xuyên gặp giới hạn Context Window, sinh ảo giác (hallucination) hoặc bị lỗi timeout do Gateway Proxy giới hạn. Kỹ sư cũng gặp khó khăn khi phát hiện các lỗi "lệch pha" số liệu giữa thuyết minh và bản vẽ (như dung tích bồn chứa, công suất bơm).

## Giải pháp đề xuất

1. **Semantic Parsing:** Trích xuất Text/Markdown thay vì Pure Vision để tiết kiệm Token.
2. **Map Phase:** Đóng gói thông tin thành các chuyên đề logic (Ví dụ: Package Legal, Package Water MEP, Package Alarm MEP).
3. **Reduce Phase:** LLM xử lý song song/tuần tự từng gói, sau đó gom toàn bộ lỗi và xuất Báo cáo Đánh giá (Mẫu PC13 theo NĐ 105/2025).

## Code/Script mẫu (nếu có)

```python
# Mẫu code lõi map_reduce_pccc.py đã được test thành công
# Gói 1: Pháp lý & Thuyết minh (ThuyetMinh + PC07)
# Gói 2: MEP Nước & Bơm vs Thuyết minh
# Gói 3: MEP Báo cháy vs Kiến trúc
# Reduce: Tổng hợp lại, loại bỏ các lỗi trùng lặp, chấm điểm hồ sơ
```

## Tác động dự kiến

- Tiết kiệm thời gian: Giảm 80% thời gian rà soát chéo số liệu giữa Bản vẽ và Thuyết minh.
- Có thể áp dụng cho: Thẩm tra thiết kế PCCC, Kiểm định chất lượng hồ sơ, Tư vấn Chủ đầu tư tự thẩm định theo Luật 55/2024.

## Notes

Skill này hoạt động hoàn hảo với `qwen-local-primary` via LiteLLM Gateway và đã phát hiện thành công lỗi thiết kế bể nước chữa cháy (45m3 vs 54m3) và lỗi thiếu Firestopping tại dự án BV NTP.
