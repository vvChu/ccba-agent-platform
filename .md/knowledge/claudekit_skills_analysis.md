# Báo cáo Nghiên cứu & Phân tích: Đề xuất Port và Bản địa hóa các Kỹ năng từ ClaudeKit

Tài liệu này phân tích chi tiết năng lực của các kỹ năng từ ClaudeKit thượng nguồn (`claudekit-engineer`), đánh giá tính tương thích và đề xuất phương án port chọn lọc sang nền tảng **ccba-agent-platform**.

---

## 1. Nhóm Suy luận & Đóng gói Tri thức (Technical & Meta)

### Kỹ năng: `ck:sequential-thinking` (Suy nghĩ tuần tự)
*   **Cơ chế hoạt động:** Hướng dẫn Agent phân rã các bài toán phức tạp thành một chuỗi các bước suy nghĩ có đánh số (`Thought 1/N`). Nó cho phép Agent tự động điều chỉnh số lượng bước (mở rộng/co hẹp), sửa đổi nhận định cũ (`[REVISION]`), hoặc rẽ nhánh giả thuyết (`[BRANCH A]`/`[BRANCH B]`).
*   **Đánh giá độ phù hợp (Feasibility):** **Cực kỳ cao (95%)**.
*   **Giá trị nghiệp vụ:** Giúp Agent nâng cấp năng lực suy luận logic khi đối soát các hồ sơ thiết kế phức tạp đa bộ môn hoặc đối chiếu các điều khoản pháp lý xây dựng chéo nhau (tránh lỗi ảo giác - hallucination).
*   **Đề xuất Porting:** Port nguyên bản thành một Native Skill tại `.agents/skills/sequential-thinking/` mà không cần cài đặt dependencies phức tạp.

### Kỹ năng: `repomix` (Đóng gói Codebase)
*   **Cơ chế hoạt động:** Sử dụng thư viện Node.js `repomix` để gom toàn bộ mã nguồn hoặc tài liệu trong thư mục dự án thành một file văn bản duy nhất (.txt) đã được tối ưu hóa XML tags để nạp nhanh vào LLM context.
*   **Đánh giá độ phù hợp (Feasibility):** **Trung bình (70%)**.
*   **Giá trị nghiệp vụ:** Hỗ trợ RAG nhanh trên quy mô toàn bộ dự án, tuy nhiên CCBA đã có sẵn các parser PDF/Word chuyên dụng tốt hơn.
*   **Đề xuất Porting:** Giữ ở mức tham chiếu, chưa cần port chính thức lên Hub.

---

## 2. Nhóm Trực quan hóa & Sinh báo cáo (Design & UI)

### Kỹ năng: `canvas-design` & `artifacts-builder`
*   **Cơ chế hoạt động:** Hướng dẫn Agent tạo ra các tác phẩm trực quan hoặc giao diện web HTML/CSS/JS đẹp mắt (sử dụng Tailwind, React, shadcn/ui) để hiển thị thông tin.
*   **Đánh giá độ phù hợp (Feasibility):** **Cao (85%)**.
*   **Giá trị nghiệp vụ:** Hỗ trợ đắc lực cho Agent khi cần sinh các báo cáo QC chất lượng cao, biểu đồ va chạm trực quan (clash detection heatmaps) hoặc dashboard tiến độ.
*   **Đề xuất Porting:** Không port toàn bộ script phức tạp, chỉ kế thừa các triết lý thiết kế (design guidelines) và tích hợp các templates layout HTML/CSS chuyên nghiệp vào thư mục `resources/` của skill `ccba-ai-qc-reporter`.

---

## 3. Nhóm Xử lý tài liệu Nhị phân (Document Skills)

### Kỹ năng: `docx` & `xlsx` (Thao tác OOXML nâng cao)
*   **Cơ chế hoạt động:** Kế thừa bộ công cụ thao tác OOXML nâng cao của Anthropic. Thay vì dùng các thư viện Python cơ bản (như `python-docx` vốn dễ làm mất định dạng gốc), kỹ năng này unpack tệp zip Word/Excel thành các tệp XML gốc (`document.xml`, `comments.xml`), sử dụng script Python/JS để can thiệp trực tiếp vào XML (như chèn tracked changes, comments, giữ nguyên style phức tạp), sau đó đóng gói zip lại.
*   **Đánh giá độ phù hợp (Feasibility):** **Cực kỳ cao (90%)**.
*   **Giá trị nghiệp vụ:** Các dự án CCBA phải làm việc liên tục với biểu mẫu nghiệm thu, biên bản hoàn thành công trình và báo cáo định dạng Word/Excel của khách hàng. Việc chỉnh sửa file mà vẫn giữ nguyên font chữ, styles và comments gốc là yêu cầu bắt buộc.
*   **Đề xuất Porting:**
    1. Port bộ scripts unpack/pack (`unpack.py`, `pack.py`) sang `scripts/` của Hub.
    2. Port tài liệu hướng dẫn can thiệp OOXML XML (`ooxml.md` và `docx-js.md`) làm tài liệu tham chiếu tĩnh (Static References) đặt trong thư mục con `.agents/skills/completion-checklist/resources/` để Agent đọc khi cần biên soạn file docx.

---

## 🎯 Ma trận Tổng kết Khảo sát (Porting Decision Matrix)

| Tên Kỹ năng Upstream | Độ tương thích Stack | Giá trị nghiệp vụ CCBA | KISS Score | Quyết định cuối cùng |
| :--- | :--- | :--- | :--- | :--- |
| **`sequential-thinking`** | 100% (Pure Markdown) | Cực kỳ cao (Audit & Logic) | 5/5 | **PORT NGAY** (Dạng Native Skill) |
| **`docx` (OOXML toolkit)** | 90% (Python scripts) | Rất cao (Hồ sơ hoàn thành) | 4/5 | **PORT CHỌN LỌC** (Scripts + References) |
| **`canvas-design`** | 70% (Playwright/Node) | Trung bình (Báo cáo trực quan)| 3/5 | **KẾ THỪA TEMPLATES** |
| **`repomix`** | 50% (Node.js engine) | Thấp (Đã có RAG tốt hơn) | 2/5 | **TẠM HOÃN** |

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
