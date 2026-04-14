---
name: ccba-ai-qc-integrated-audit
description: Sử dụng AI Vision để đối soát đồng thời 4 bộ môn (Arch-KC-MEP-PCCC) qua hình ảnh Quad-View.
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
2. Skill này sẽ ghép chúng thành một ảnh collage **Quad-View**.
3. Gửi ảnh collage và prompt kỹ thuật đến AI Gateway (model `ocr-primary`).
4. Nhận kết quả rủi ro dưới dạng liệt kê hoặc JSON.

## Danh mục Script
- `scripts/audit_engine.py`: Logic ghép ảnh và điều phối AI Audit.
