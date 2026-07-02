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

## Vai trò
Skill này thực hiện "siêu năng lực" then chốt của IDOP: Kiểm tra xung đột đa bộ môn (Multi-disciplinary Clash Check) trong một lần quét duy nhất. Nó kết nối các bản vẽ khác nhau (Kiến trúc, Kết cấu, MEP, PCCC) và nhờ AI chỉ ra các điểm mâu thuẫn kỹ thuật.

## Cách sử dụng

### Các Trigger
- "Audit xung đột"
- "Integrated QC"
- "Đối soát 4 chiều"
- "N-Way Clash Check"

## Quy trình
1. Agent sử dụng tọa độ từ `ccba-ai-qc-discovery` để lấy 4 bản vẽ tương ứng.
   **Tiêu chí hoàn thành:** Đã định vị và tải thành công 4 file ảnh bản vẽ tương ứng từ thư mục dự án.
2. Skill này sẽ ghép chúng thành một ảnh collage **Quad-View**.
   **Tiêu chí hoàn thành:** Ảnh ghép `quad_view.png` được tạo thành công với bố cục 2x2 rõ nét.
3. Gửi ảnh collage và prompt kỹ thuật đến AI Gateway (model `ocr-primary`).
   **Tiêu chí hoàn thành:** Nhận được phản hồi HTTP 200 từ AI Gateway với phân tích visual.
4. Nhận kết quả rủi ro dưới dạng liệt kê hoặc JSON.
   **Tiêu chí hoàn thành:** Kết quả audit được lưu lại thành file `.json` hoặc in ra log kỹ thuật đầy đủ.

## Danh mục Script
- `scripts/audit_engine.py`: Logic ghép ảnh và điều phối AI Audit.
