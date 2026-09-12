---
name: ccba-docs-manager
description: Tác nhân Quản lý Tài liệu Kỹ thuật và API của CCBA Platform.
applies_to:
- Phần mềm
bundle: _software
tier: kernel
disable-model-invocation: true
user-invocable: true
command: /ccba-docs-manager
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
gpi:
  s: 3.0
  k: 3.0
  a: 1.0
  p: 1.0
triggers:
- ccba-docs-manager
- quản lý tài liệu
- document manager
- docs
- ccba-docs-validator
- docs-validator
---

# Kỹ năng: Quản lý Tài liệu Kỹ thuật (Docs Manager)

Kỹ năng này đóng vai trò là một **Technical Writer QA** chuyên biệt, chịu trách nhiệm duy trì tính nhất quán, bảo mật và chính xác của tài liệu kỹ thuật so với thực tế mã nguồn (codebase).

Agent **bắt buộc** phải thực thi theo đúng quy trình 5 pha sau đây:

---

## 🛠️ Quy trình thực thi 5 pha

### Pha 1: Đóng gói Codebase (Scouting & Pack)
1.  Đóng gói toàn bộ codebase hiện tại thành một tệp XML tạm thời:
    ```bash
    python scripts/security/repomix_pack.py --source . --output .md/scratch/repomix-output.xml
    ```
2.  Đọc cấu trúc và metadata từ tệp XML vừa tạo để hiểu cấu trúc codebase hiện tại.
- **Tiêu chí hoàn thành:** Codebase được đóng gói thành công thành tệp XML tạm thời phục vụ phân tích.

### Pha 2: Kiểm soát Bảo mật (Verify Secrets)
1.  Chạy công cụ bảo mật quét và che giấu (redact) secrets trực tiếp trên file XML đóng gói:
    ```bash
    python scripts/maskara.py redact
    ```
    *(Hệ thống đã được vá lỗi XML Bypass để đảm bảo quét sạch secrets trong tệp XML)*.
2.  Nếu phát hiện rò rỉ secrets nghiêm trọng (như mật khẩu Database dạng raw), **dừng ngay tiến trình** và báo cáo lỗi cho người dùng.
- **Tiêu chí hoàn thành:** Tệp XML đóng gói được quét sạch secrets, không có rò rỉ thông tin nhạy cảm.

### Pha 3: Sao lưu & Cập nhật Tài liệu (Backup & Update)
1.  **Sao lưu bảo vệ dữ liệu (Backup Gate)**: Trước khi cập nhật hoặc phân rã bất kỳ tệp tài liệu nào, **bắt buộc** phải sao lưu toàn bộ các tệp tài liệu kỹ thuật mục tiêu (bao gồm cả phân vùng `.md/knowledge/` và các tài liệu tri thức gốc `README.md`, `PLATFORM.md`, `CONTRIBUTING.md`, `SECURITY.md`) vào thư mục tạm `.md/scratch/backups/`.
2.  **Khởi tạo Baseline (Lần chạy đầu tiên)**:
    - Nếu dự án chưa có `.md/knowledge/codebase_summary.md`:
    - Chia nhỏ codebase thành các phân vùng module chính.
    - Gọi song song **tối đa 3-5 subagents** để nghiên cứu sâu và lập báo cáo tóm tắt cho từng module.
    - Hợp nhất các báo cáo này để xây dựng tài liệu baseline.
3.  **Cập nhật tài liệu kỹ thuật**:
    - Kế thừa các biểu mẫu chuẩn từ Hub tại `.agents/templates/` (ví dụ: `project_overview_pdr_template.md`).
    - Ghi nhận tài liệu kỹ thuật **tập trung vào phân vùng `.md/knowledge/`** để tuân thủ nguyên tắc ngăn nắp của Knowledge Base dự án.
    - **Đồng bộ tài liệu tri thức gốc**: Đối chiếu cấu trúc codebase thực tế (các packages và tệp tin) với sơ đồ thư mục và hướng dẫn trong `README.md`, `PLATFORM.md`, và `CONTRIBUTING.md`. Nếu phát hiện không đồng bộ (thêm/bớt package, đổi tên thư mục AI hoặc thay đổi Slash Commands), **bắt buộc** phải cập nhật lại sơ đồ và bảng hướng dẫn trong các tài liệu gốc này.
4.  **Quản lý kích thước (Size Limit 800 LOC)**:
    - Nếu tệp tài liệu nào vượt quá 800 dòng (LOC), chủ động phân rã nó thành tệp `index.md` dẫn hướng và các tệp con nằm trong thư mục con tương ứng (ví dụ: `.md/knowledge/system_architecture/`).
    - Gọi kỹ năng **`ccba-relative-link-patcher`** để tự động vá và chuẩn hóa các liên kết tương đối bị ảnh hưởng.
- **Tiêu chí hoàn thành:** Tài liệu kỹ thuật được sao lưu, cập nhật đầy đủ và đồng bộ với hiện trạng codebase mới nhất.

### Pha 4: Kiểm định Tài liệu chống Ảo ảnh (Validate)
1.  Chạy script kiểm định tài liệu chính thức cho cả các tệp tài liệu tri thức gốc và các tài liệu thay đổi:
    ```bash
    python scripts/validate_docs.py . --src src,packages,scripts --changed
    ```
2.  **Quy trình Rollback**: Nếu kiểm định phát hiện lỗi liên kết hỏng (`Exit 1`) và Agent không thể tự động sửa lỗi sau 3 lượt thử, Agent **bắt buộc** phải:
    - Khôi phục lại các tệp tài liệu gốc từ thư mục `.md/scratch/backups/`.
    - Xóa bỏ hoàn toàn các tệp tin modular con bị lỗi.
    - Thông báo lỗi chi tiết cho người dùng và dừng tiến trình.
- **Tiêu chí hoàn thành:** Lệnh `validate_docs.py` vượt qua với 0 lỗi broken links và 0 architecture drift.

### Pha 5: Dọn dẹp Tài nguyên Tạm thời (Cleanup)
1.  Xóa hoàn toàn tệp tin tạm `.md/scratch/repomix-output.xml`.
2.  Báo cáo danh sách các tài liệu đã được cập nhật thành công kèm theo kết quả kiểm định `validate_docs.py`.
- **Tiêu chí hoàn thành:** Xóa sạch tệp XML tạm và báo cáo tóm tắt danh sách tài liệu đã cập nhật.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/markdown_hallucination_check.md` | Quy trình kiểm tra tính xác thực của tài liệu Markdown, ngăn ngừa ảo ảnh thông tin |

