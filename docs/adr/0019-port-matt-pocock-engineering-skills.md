# ADR 0019: Đồng bộ Quy trình Triển khai Kỹ nghệ từ Thượng nguồn & Dọn dẹp Thành phần Lỗi thời

* **Trạng thái:** Approved
* **Người đề xuất:** Antigravity AI Agent
* **Ngày quyết định:** 2026-07-13

---

## 1. Ngữ cảnh (Context)
CCBA Agent Platform sử dụng một quy trình kỹ nghệ để chuyển dịch từ ý tưởng thành mã nguồn chạy được. Trước đây, một số skill và workflow được tạo ra dưới dạng cục bộ/địa hóa (như `to-prd` cho việc viết PRD, `ccba-to-tickets` cho việc phân rã công việc, và alias `/ccba-to-issues`). 

Tuy nhiên, việc duy trì song song cả tên gọi cục bộ và cấu hình đăng ký khuyết trên đĩa của các skill chuẩn thượng nguồn (`to-spec`, `implement`) gây ra sự chồng chéo, phân mảnh tài liệu và khó khăn cho lập trình viên khi đồng bộ mã nguồn giữa Hub và Spoke. Để đồng bộ hóa và chuẩn hóa quy trình triển khai khớp với thượng nguồn `mattpocock-skills` mà vẫn bảo đảm các quy tắc quản trị thông tin của CCBA (như lưu trữ mọi tài liệu trong `.md/`), chúng tôi cần thực hiện một đợt tái cấu trúc và porting toàn diện.

## 2. Quyết định (Decisions)
Chúng tôi quyết định thực hiện các thay đổi kiến trúc và cấu trúc sau:

1.  **Loại bỏ các skill/workflow lỗi thời:**
    *   Xóa bỏ hoàn toàn skill `to-prd` và workflow `/ccba-to-prd`. Thống nhất sử dụng thuật ngữ `spec` và skill `to-spec` thay thế cho `prd`.
    *   Xóa bỏ workflow alias tương thích ngược `/ccba-to-issues.md`. Sử dụng duy nhất `/ccba-to-tickets` làm lệnh phân rã chính quy.
2.  **Đồng bộ & Thích ứng hóa các skill thượng nguồn:**
    *   **`to-spec`**: Port skill này từ thượng nguồn, nhưng thích ứng hóa đường dẫn lưu trữ offline về vùng cấu trúc ẩn `.md/knowledge/specs/spec-{slug}.md` để tuân thủ hiến pháp CCBA Rule 1.
    *   **`to-tickets`**: Đổi tên thư mục skill cục bộ từ `ccba-to-tickets` thành `to-tickets` để khớp tên gọi thượng nguồn, nhưng giữ nguyên nội dung thích ứng của CCBA (lưu local tickets tại `.md/knowledge/issues/` và tích hợp `/ccba-setup-skills`).
    *   **`implement`**: Port skill lập trình khép kín này từ thượng nguồn về [implement](../../.agents/skills/implement/) và khôi phục workflow `/ccba-implement` trên đĩa.
    *   **`setup-matt-pocock-skills` & `ask-matt`**: Port đầy đủ hai skill này về Hub để cung cấp cấu hình chuẩn cho các Spoke không sử dụng cấu trúc thư mục ẩn `.md/`.
3.  **Cập nhật Danh mục Central Hub:**
    *   Cập nhật `catalog.yaml` để liên kết chính xác các skill và workflow mới/được đổi tên, loại bỏ các đăng ký cũ.

## 3. Hệ quả (Consequences)
*   **Tích cực:** 
    *   Thống nhất được bộ thuật ngữ và quy trình (`spec` -> `tickets` -> `implement`) chuẩn thượng nguồn.
    *   Codebase của Central Hub được dọn dẹp sạch sẽ, không còn các tệp tin mồ côi hoặc alias dư thừa.
    *   Bảo đảm 100% tính tuân thủ quy tắc quản trị dữ liệu của CCBA (lưu trữ Specs/Tickets trong `.md/`).
*   **Tiêu cực:** Các nhà phát triển quen với lệnh cũ `/ccba-to-prd` và `/ccba-to-issues` sẽ cần chuyển sang dùng `/ccba-to-spec` và `/ccba-to-tickets`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
