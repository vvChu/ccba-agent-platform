# BÁO CÁO ĐÁNH GIÁ CHẤT LƯỢNG TOÀN DIỆN: SLASH COMMAND `/ccba-docs` & DOCS MANAGER AGENT

## 1. Giới thiệu
Báo cáo thực hiện đánh giá toàn diện về chất lượng cấu trúc, bảo mật và độ ổn định của Slash Command `/ccba-docs` và Docs Manager Agent vừa tích hợp trong CCBA Agent Services Platform. Đánh giá kết hợp rà soát tĩnh (Static Review) đối chiếu với Hiến pháp Layer 1 (`AGENTS.md`) và chạy thử nghiệm stress-test trên codebase giả lập biệt lập.

## 2. Kết quả Rà soát Tĩnh cấu trúc Workflow (M1)
Qua phân tích tệp cấu trúc `.agents/workflows/ccba-docs.md`, chúng tôi ghi nhận các điểm vi phạm Hiến pháp Layer 1 (Constitution) của Platform:
*   **Vi phạm cấu trúc đăng ký Slash Command (Nghiêm trọng)**: Hiến pháp quy định các file workflow đăng ký slash command phải là tệp mỏng (chỉ chứa frontmatter và một chỉ thị nạp `SKILL.md`). Tệp `ccba-docs.md` hiện tại chứa toàn bộ logic 5 pha chi tiết và chạy bash trực tiếp, vi phạm nghiêm trọng quy tắc đóng gói nghiệp vụ của Agent.
*   **Vi phạm quy ước đặt tên (Trung bình)**: Tệp workflow tham chiếu tới các kỹ năng ở dạng kebab-case (`maskara-privacy`, `relative-link-patcher`), vi phạm quy tắc bắt buộc của Skills phải đặt tên ở dạng snake_case (`lowercase_with_underscores`). Thư mục thực tế của `relative-link-patcher` trên đĩa cũng đang vi phạm quy tắc này.
*   **Vi phạm nguyên tắc lưu trữ tập trung (Trung bình)**: Chỉ định lưu tài liệu kỹ thuật do AI sinh ra ngoài phân vùng `.md/` (ghi vào `docs/` thay vì `.md/knowledge/`), vi phạm nguyên tắc giữ gìn ngăn nắp của Knowledge Base dự án.
*   **Hạn chế của Linter tĩnh**: Công cụ `validate_docs.py` báo thành công do regex lọc liên kết và biểu tượng `CODE_REF_RE` bị bỏ sót các ký hiệu nằm trong backtick có chứa ký tự `-`, `.`, `/`, dẫn đến lọt lướt các tham chiếu ảo ảnh.

## 3. Kết quả Stress-Test thực nghiệm (M2 & M3)
Quá trình chạy stress-test tự động trên codebase giả lập con tại `.md/scratch/teamwork_test/` đã xác định 4 lỗi vận hành và bảo mật nghiêm trọng:
1.  **Lọt bảo mật do bỏ qua XML (Security Leak - Rất nghiêm trọng)**:
    *   Hành vi: Quét secrets bằng Maskara trên file XML đóng gói của Repomix (`repomix-output.xml`) trả về không phát hiện lỗi (Exit 0) dù chứa API keys thô. Tuy nhiên, quét trực tiếp file `.env` thì phát hiện chính xác (Exit 1).
    *   Nguyên nhân: Hàm `looks_like_session_text()` trong `maskara.py` chỉ quét các đuôi tệp văn bản/cấu hình cố định và bỏ qua `.xml` một cách lặng lẽ. Do đó, toàn bộ secrets bị đóng gói vào XML sẽ không bao giờ được phát hiện hay che giấu.
2.  **Nguy cơ rò rỉ secrets khi tiến trình bị ngắt (Leak Window - Nghiêm trọng)**:
    *   Hành vi: Đóng gói codebase thô (Pha 1) được thực hiện trước khi quét bảo mật (Pha 2).
    *   Rủi ro: File XML chứa secrets thô được ghi xuống đĩa. Nếu tiến trình bị crash hoặc ngắt trước Pha 5 dọn dẹp, secrets thô sẽ nằm lại trên đĩa cứng vô thời hạn, có nguy cơ bị cloud sync tự động hoặc đẩy lên Git.
3.  **Lỗi logic Rollback gây mất dữ liệu gốc vĩnh viễn (Data Loss - Rất nghiêm trọng)**:
    *   Hành vi: Sau khi rollback, file gốc `docs/big_document.md` bị mất hoàn toàn 805 dòng dữ liệu gốc ban đầu và bị ghi đè bởi phiên bản đã chia nhỏ (93 dòng).
    *   Nguyên nhân: Cấu trúc workflow thực hiện backup ở đầu Pha 4, trong khi Pha 3 đã thực hiện phân tách và ghi đè trực tiếp lên tệp gốc. Điều này làm cho bản backup thực chất là bản lỗi/bản đã sửa đổi, khiến tính năng rollback vô tác dụng và làm mất sạch dữ liệu gốc của dự án.
4.  **Hỏng liên kết tương đối do phân rã tệp (Broken Links - Trung bình)**:
    *   Hành vi: Khi tệp lớn bị chia nhỏ vào thư mục con (ví dụ `docs/big-document/sub_part.md`), các liên kết ảnh tương đối `./assets/` và liên kết chéo khác bị hỏng hoàn toàn do không được cập nhật thêm tiền tố `../`.
    *   Nguyên nhân: Kỹ năng `relative-link-patcher` chỉ được lập trình để vá các liên kết phụ lục bắt đầu bằng `./appendices/`. Nó không có khả năng cập nhật lại chiều sâu cho các liên kết tài nguyên thông thường khác.
5.  **Lỗi CLI của relative-link-patcher (Thấp)**:
    *   Lệnh CLI `python -m mdconverter.cli` bị crash do package thiếu file khởi chạy entrypoint `__main__.py`.

## 4. Đề xuất Kiến nghị khắc phục & Tối ưu hóa
Kính đề nghị Ban Điều hành Dự án phê duyệt các phương án tái cấu trúc và sửa đổi kỹ thuật sau:
1.  **Tái cấu trúc file Workflow**: Chuyển đổi tệp `.agents/workflows/ccba-docs.md` thành một tệp mỏng chỉ thực hiện trigger. Di chuyển toàn bộ logic 5 pha sang kỹ năng mới `.agents/skills/docs_manager/SKILL.md` (định dạng snake_case chuẩn).
2.  **Cập nhật quy hoạch lưu trữ tài liệu**: Cấu hình tệp `docs_manager/SKILL.md` ghi nhận tài liệu kỹ thuật vào `.md/knowledge/` thay vì `docs/` để tuân thủ hiến pháp dự án tri thức.
3.  **Vá lỗi Maskara XML Bypass**: Cập nhật `maskara.py` to bổ sung định dạng `.xml` vào danh sách quét hoặc bổ sung tùy chọn bắt buộc quét nếu tệp đích được chỉ định cụ thể.
4.  **Đảo ngược thứ tự quét Secrets**: Thực hiện quét secrets bằng Maskara trực tiếp trên các thư mục gốc codebase (`src/`, `packages/`, `.env`) **trước** khi chạy Repomix đóng gói codebase. Đồng thời cấu hình loại trừ (`default_excludes`) của Repomix để chủ động bỏ qua tệp nhạy cảm.
5.  **Điều chỉnh thời điểm Backup**: Di chuyển bước sao lưu toàn bộ các tệp docs mục tiêu lên đầu Pha 3 (trước khi thực hiện bất kỳ thay đổi nào) để đảm bảo rollback khôi phục đúng trạng thái nguyên bản.
6.  **Nâng cấp relative-link-patcher**: Thêm tệp `__main__.py` để sửa lỗi CLI. Nâng cấp bộ patcher để tự động tính toán lại chiều sâu thư mục tương đối cho tất cả liên kết tài nguyên khi di chuyển file.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
