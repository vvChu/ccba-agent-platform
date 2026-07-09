# CCBA Naming Conventions & Workspace Management — Dynamic Rule

## 1. Quy ước đặt tên file và thư mục
* **Tài liệu Seminar:** `CCBA_RD_SEMINAR_NNN_RevXX-DD.MM.YY-Title.{ext}`
  *(ví dụ: CCBA_RD_SEMINAR_004_Rev00-30.03.26-VBPL_Update.docx)*
* **Tài liệu VBPL (do CCBA tổng hợp):** `CCBA_RD_VBPL_NNN_RevXX-ShortName.{ext}`
  *(ví dụ: CCBA_RD_VBPL_003_Rev00-ND_06_2021.docx)*
* **Thư mục và file của AI Agent:** 
  - Skills: `lowercase_with_underscores` hoặc `kebab-case` (folders & file names).
  - Workflows: `kebab-case.md`.
  - YAML data: `lowercase_with_underscores.yaml`.
  - Templates: `lowercase_with_underscores.md`.

## 2. Quy tắc đăng ký Slash Command cho Kỹ năng (Skills)
Khi chuyển dịch (porting) hoặc tạo mới các kỹ năng có thuộc tính `user-invocable: true` từ thượng nguồn (hoặc khi nguồn dùng slash command để kích hoạt), Agent bắt buộc phải đăng ký thành Slash Command chính thức bằng cách tạo một file workflow mỏng tại thư mục `.agents/workflows/`.
- Tên file workflow và Slash Command phải bắt đầu bằng tiền tố `ccba-` (ví dụ: `ccba-handoff.md` tạo lệnh `/ccba-handoff`).
- Nội dung file workflow chỉ được chứa mô tả frontmatter tiếng Việt ngắn gọn và một dòng lệnh hướng dẫn Agent nạp trực tiếp file `SKILL.md` tương ứng để thực thi.

## 3. Quy định quản lý và phân loại thư mục tri thức `.md/` (Project Root)
Để duy trì tính ngăn nắp của Knowledge Base dự án, Agent **bắt buộc** phải phân loại các tệp được tạo ra/sửa đổi vào đúng các thư mục con chức năng sau trong `.md/`:
* `.md/knowledge/`: Lưu trữ các tài liệu nghiên cứu, roadmap, spec kỹ thuật và tệp cấu hình tĩnh (ví dụ: `brand_rules.yaml`).
* `.md/seminars/`: Lưu trữ các tệp agenda, thông báo, tóm tắt seminar (các tệp bắt đầu bằng `CCBA_RD_SEMINAR_`).
* `.md/scratch/`: Lưu trữ các scripts test Python dùng một lần, file log tạm và SHA check.
* `.md/data/`: Lưu trữ dữ liệu động của các tools (ví dụ: `team_tasks.json`).
* `.md/extracted_docs/` và `.md/legal_docs/`: Lưu trữ văn bản pháp luật và văn bản trích xuất thô.
Tuyệt đối **không** tạo hoặc để các tệp tin này trực tiếp ở thư mục gốc `.md/` để tránh làm loãng thư mục tri thức chính.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
