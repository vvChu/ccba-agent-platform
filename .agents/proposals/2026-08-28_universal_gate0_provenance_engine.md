---
proposal_id: "2026-08-28_universal_gate0_provenance_engine"
type: "tool"
name: "universal-gate0-provenance-engine"
status: "open"
priority: "Cao"
proposed_by_project: "ccba-legal-knowledge"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-08-28"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Pháp điển"
---

# Proposal: Universal Gate 0 Ingestion Provenance and DOCX vs PDF Gazette Cross-Verification Engine

## 1. Tóm Tắt & Bối Cảnh Thực Tế (Context & Pain Points)
Trong quá trình số hóa và nạp dữ liệu pháp lý (Ingestion Gate 0) trên quy mô lớn tại Spoke `ccba-legal-knowledge` (với hơn 31 văn bản Luật, Nghị định, Thông tư, QCVN, TCVN):
1. **Rủi ro sai lệch dữ liệu nguồn:** Tệp DOCX tải về từ Thư Viện Pháp Luật đôi khi có thể bị thiếu điều khoản, mất phụ lục hoặc lệch ký tự so với bản in Công báo chính thức (Official Gazette PDF).
2. **Thiếu module đối soát tập trung trên Hub:** Logic so khớp trước đây nằm rải rác dưới dạng script cục bộ của Spoke, không thể tái sử dụng cho các Spokes khác hoặc các pipeline Audit thiết kế.
3. **Hiện tượng False Positive với PDF scan:** Các file PDF Công báo dạng scan hình ảnh (không có text layer số) thường bị chấm điểm Text Parity 0%, dẫn tới báo lỗi giả trong CI.

---

## 2. Giải Pháp Triển Khai Trên Hub (Implementation Details)

Đã đóng gói Deep Seam [`ccba_legal.provenance`](file:///D:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel/src/ccba_legal/provenance.py) vào package `ccba-legal-intel`:
1. **Kiểm soát Cấu Trúc Đa Cấp (`check_structure_alignment`):** Tự động bóc tách và đối chiếu 100% số lượng Điều, Chương, Phụ lục giữa DOCX và PDF.
2. **Đo Lường Text Parity Thông Minh (`compute_text_parity`):** So khớp ngữ nghĩa và tần suất xuất hiện các đoạn văn bản; tự động nhận diện PDF scan ảnh (`is_scanned`) để tránh false positive.
3. **Giao Diện Public Tinh Gọn (`verify_docx_against_pdf`):** Cho phép gọi 1-command từ bất kỳ Spoke nào, trả về báo cáo cấu trúc JSON chi tiết.

---

## 3. Kiểm Thử & Nghiệm Thu (Verification & QA)
- **Unit Tests Hub:** Bổ sung [`tests/test_provenance.py`](file:///D:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel/tests/test_provenance.py) với 5/5 unit tests pass 100%.
- **Spoke Production Parity:** Đã nghiệm thu thành công trên toàn bộ 27 gói văn bản có tài sản kép tại `ccba-legal-knowledge` (`27/27 PASS 100%`).
- **Linter & Code Hygiene:** Đạt 100% `ruff check` và `check_spoke_leakage.py`.