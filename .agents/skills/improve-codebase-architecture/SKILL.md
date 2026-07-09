---
name: improve-codebase-architecture
description: Quét codebase tìm kiếm cơ hội làm sâu module, xuất báo cáo trực quan dưới dạng HTML, và thực hiện grilling để chốt phương án cải tiến.
disable-model-invocation: true
category: engineering
keywords: [architecture, design, deep-module, refactor, visual-report, cải tiến kiến trúc, module sâu, báo cáo trực quan, refactor mã nguồn]
metadata:
  author: CCBA
  version: "1.1.0"
---

# Cải tiến Kiến trúc Mã nguồn (Improve Codebase Architecture)

Kỹ năng này giúp phát hiện các điểm nghẽn kiến trúc và đề xuất **Cơ hội làm sâu module (Deepening Opportunities)** — các hoạt động refactor giúp chuyển đổi các module nông (shallow modules) thành các module sâu (deep modules). Mục tiêu tối thượng là tăng khả năng kiểm thử (testability) và tính dễ định hướng cho AI (AI-navigability).

Quy trình này được định hướng bởi domain model của dự án và xây dựng trên bộ từ vựng thiết kế phần mềm thống nhất:
- Sử dụng chính xác các thuật ngữ từ kỹ năng `/codebase-design` (**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**) và các nguyên lý đi kèm (phép thử xóa bỏ - deletion test, "interface là bề mặt kiểm thử", "một adapter = seam giả thuyết, hai adapter = seam thực tế"). Tuyệt đối không dùng lệch sang các từ "component", "service", "API" hoặc "boundary".
- Ngôn ngữ domain trong `CONTEXT.md` cung cấp tên gọi chuẩn cho các seam; các tài liệu ADR trong thư mục `.md/knowledge/` ghi nhận các quyết định kiến trúc đã chốt mà quy trình này không được tự ý lật lại.

---

## Quy trình Thực hiện (Process)

### 1. Khám phá (Explore)
- Đọc bảng thuật ngữ domain (`CONTEXT.md`) và bất kỳ tài liệu quyết định thiết kế (ADRs) liên quan đến phân vùng mã nguồn chuẩn bị tác động.
- Sử dụng subagent thuộc kiểu `Explore` để quét codebase một cách tự nhiên. Ghi chép lại các điểm gây cản trở lập trình (architectural friction):
  * Nơi nào muốn hiểu một khái niệm nghiệp vụ lại phải nhảy qua nhảy lại giữa quá nhiều module nhỏ?
  * Nơi nào chứa các module **nông (shallow)** — giao diện interface phức tạp gần bằng phần code triển khai bên trong?
  * Nơi nào các hàm thuần túy (pure functions) bị bóc tách ra chỉ để phục vụ viết unit test, trong khi lỗi thực tế lại nằm ở cách gọi chúng (thiếu **locality**)?
  * Nơi nào các module có coupling chặt chẽ và bị rò rỉ logic qua các seam của chúng?
  * Phân vùng nào đang thiếu kiểm thử hoặc cực kỳ khó viết unit test với giao diện hiện tại?
- Áp dụng **phép thử xóa bỏ (deletion test)** đối với các module nghi ngờ bị nông: Nếu xóa module đó đi thì độ phức tạp sẽ tập trung lại một chỗ hay chỉ bị dịch chuyển sang chỗ khác? Nếu câu trả lời là "tập trung lại một chỗ", đó chính là seam tốt cần làm sâu.
- **Tiêu chí hoàn thành:** Lập danh sách ghi nhận được ít nhất 2 vùng module bị nông hoặc coupling cao, kèm kết quả phép thử xóa bỏ (deletion test) cho mỗi vùng.

### 2. Trình bày Báo cáo dưới dạng HTML (Present candidates as an HTML report)
- Viết một file HTML đơn lẻ (single-file) vào thư mục tạm của dự án: `.md/scratch/architecture-review/architecture-review-<timestamp>.html` (tự động tạo thư mục nếu chưa tồn tại).
- Kích hoạt mở tệp tin báo cáo bằng trình duyệt mặc định trên hệ thống Windows của kỹ sư thông qua lệnh:
  ```powershell
  Start-Process "<absolute-path-to-file>"
  ```
- Trình bày đường dẫn tuyệt đối của tệp tin vừa tạo cho người dùng trên chat.
- **Đặc trưng thiết kế báo cáo:**
  * Sử dụng **Tailwind CSS qua CDN** để dàn trang và **Mermaid JS qua CDN** để vẽ sơ đồ trực quan (quan hệ call graphs, dependencies, sequences).
  * *Lưu ý Offline:* Đính kèm một dòng thông báo nổi bật ở đầu trang: *"Báo cáo này yêu cầu kết nối Internet để tải các tài nguyên đồ họa trực tuyến (Mermaid & Tailwind CSS)"*.
  * Sử dụng kết hợp CSS/SVG tự chế cho các phần visual dạng editorial (biểu đồ khối lượng, mặt cắt cấu trúc, animation đóng/mở).
  * Mỗi ứng viên cải tiến phải có hình ảnh so sánh **trước/sau (Before/After)** trực quan.
- Mỗi ứng viên đề xuất (card) phải hiển thị đủ:
  * **Files:** Các tệp tin/module liên quan.
  * **Problem:** Lý do kiến trúc hiện tại gây cản trở/friction.
  * **Solution:** Mô tả bằng văn xuôi giải pháp thay đổi.
  * **Benefits:** Giải thích dưới góc độ tăng tính locality, leverage và cách cải thiện bộ test.
  * **Before / After diagram:** Sơ đồ side-by-side minh họa trực quan việc làm sâu module.
  * **Recommendation strength:** Đánh giá mức độ đề xuất (`Strong` | `Worth exploring` | `Speculative`) dưới dạng badge màu.
- Kết thúc báo cáo bằng phần **Đề xuất hàng đầu (Top recommendation)** để chỉ rõ ứng viên nên xử lý đầu tiên kèm lý do.
- **Tiêu chí hoàn thành:** Báo cáo HTML được ghi thành công vào thư mục tạm `.md/scratch/`, mở được trên trình duyệt mặc định mà không gặp lỗi CLI, hiển thị đầy đủ các thẻ ứng viên và sơ đồ Before/After.

### 3. Vòng lặp Chất vấn (Grilling loop)
- Sau khi người dùng chọn một ứng viên cải tiến, kích hoạt kỹ năng `/grilling` để tiến hành phỏng vấn sâu với Kỹ sư về: các ràng buộc (constraints), dependency, cấu trúc của module được làm sâu, logic nằm sau seam, và các test case được bảo toàn.
- Cập nhật domain model và tài liệu tri thức song song:
  * Nếu đặt tên module làm sâu theo một khái niệm mới chưa có trong `CONTEXT.md` $\rightarrow$ Thêm thuật ngữ đó vào `CONTEXT.md`.
  * Nếu làm sắc nét thêm một thuật ngữ mập mờ $\rightarrow$ Cập nhật định nghĩa trực tiếp vào `CONTEXT.md`.
  * Nếu người dùng từ chối đề xuất vì một lý do kỹ thuật nền tảng quan trọng $\rightarrow$ Đề xuất ghi nhận thành tài liệu ADR trong thư mục `.md/knowledge/` để tránh các đợt quét sau đề xuất lại trùng lặp.
  * Nếu muốn so sánh các thiết kế interface khác nhau cho module sâu $\rightarrow$ Kích hoạt kỹ năng `/codebase-design` và chạy cơ chế parallel sub-agent (thiết kế hai phương án độc lập để đối chiếu).
  * **Đề xuất dựng mẫu thử nhanh (ADR 0010):** Sau khi thống nhất phương án triển khai, nếu việc refactor ảnh hưởng trực tiếp đến **Core Platform (Hub)** (ví dụ: sửa đổi core services, metadata registry, database schema chung), Agent bắt buộc phải đề xuất hoặc kích hoạt `/ccba-prototype` (nhánh Logic/UI) để dựng nhanh mô phỏng hoạt động trước khi code thật. Đối với các Spoke apps hoặc hàm nghiệp vụ độc lập, Agent đề xuất viết code trực tiếp và chạy suite kiểm thử để tối ưu thời gian.
- **Tiêu chí hoàn thành:** Phiên chất vấn grilling kết thúc, thống nhất được phương án triển khai cụ thể, và các tài liệu tri thức (`CONTEXT.md`, ADRs) được cập nhật đồng bộ.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
