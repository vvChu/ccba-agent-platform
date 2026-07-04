---
name: ccba-ai-qc-integrated-audit
description: Sử dụng AI Vision để đối soát đồng thời 4 bộ môn (Arch-KC-MEP-PCCC) qua hình ảnh Quad-View.
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_qc"
---

# CCBA AI QC Integrated Audit Skill

Skill này thực hiện kiểm tra xung đột đa bộ môn (Multi-disciplinary Clash Check) thông qua AI Vision đối với hình ảnh collage ghép từ 4 bản vẽ (Kiến trúc, Kết cấu, MEP, PCCC) trên cùng một cao độ/tầng.

---

## Tiêu chí hoàn thành (Completion Criteria)

1. **Tìm kiếm & Trích xuất Bản vẽ:**
   - **Xác nhận:** Đã định vị và trích xuất thành công 4 tệp tin ảnh bản vẽ tương ứng của tầng được chỉ định dựa trên dữ liệu ma trận.
2. **Ghép ảnh Quad-View:**
   - **Xác nhận:** Sinh thành công tệp ảnh collage `quad_view.png` với bố cục lưới 2x2 rõ nét.
3. **Phân tích AI:**
   - **Xác nhận:** Nhận được phản hồi HTTP 200 từ AI Gateway sử dụng model hỗ trợ vision để cào lỗi thiết kế.
4. **Lưu trữ kết quả:**
   - **Xác nhận:** Kết quả phân tích (findings) được lưu trữ thành công dưới dạng JSON hoặc Markdown vào thư mục `.md/extracts/audit_batch/`.

---

## Công cụ thực thi

Quy trình ghép ảnh và điều phối AI Vision được xử lý qua script:
```text
.agents/skills/ccba-ai-qc-integrated-audit/scripts/semantic_audit_engine.py
```
