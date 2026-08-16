---
name: improve-codebase-architecture
description: Quét codebase tìm kiếm cơ hội làm sâu module, xuất báo cáo trực quan dưới dạng HTML, và thực hiện grilling để chốt phương án cải tiến.
disable-model-invocation: true
category: engineering
keywords: [architecture, design, deep-module, refactor, visual-report, cải tiến kiến trúc, module sâu, báo cáo trực quan, refactor mã nguồn]
metadata:
  author: CCBA
  version: "1.3.0"
---

# Cải tiến Kiến trúc Mã nguồn (Improve Codebase Architecture)

Kỹ năng này giúp phát hiện các điểm nghẽn kiến trúc thực tế và đề xuất **Cơ hội làm sâu module (Deepening Opportunities)** — các hoạt động refactor giúp chuyển đổi các module nông (shallow modules) thành các module sâu (deep modules), đồng thời loại bỏ nợ kỹ thuật tồn dư (symbol collisions, import drift, legacy scripts). Mục tiêu tối thượng là tăng khả năng kiểm thử (testability) và tính dễ định hướng cho AI (AI-navigability).

Quy trình này được định hướng bởi domain model của dự án và xây dựng trên bộ từ vựng thiết kế phần mềm thống nhất:
- Sử dụng chính xác các thuật ngữ từ kỹ năng `/codebase-design` (**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**) và các nguyên lý đi kèm (phép thử xóa bỏ - deletion test, "interface là bề mặt kiểm thử", "một adapter = seam giả thuyết, hai adapter = seam thực tế"). Tuyệt đối không dùng lệch sang các từ "component", "service", "API" hoặc "boundary".
- Ngôn ngữ domain trong `CONTEXT.md` cung cấp tên gọi chuẩn cho các seam; các tài liệu ADR trong thư mục `.md/knowledge/` ghi nhận các quyết định kiến trúc đã chốt mà quy trình này không được tự ý lật lại.

---

## Quy trình Thực hiện (Process)

### 1. Khám phá & Quét Thực Chiến (Explore & Ground-Truth Sweep)
- Đọc bảng thuật ngữ domain (`CONTEXT.md`) và bất kỳ tài liệu quyết định thiết kế (ADRs) liên quan đến phân vùng mã nguồn chuẩn bị tác động.
- Sử dụng subagent thuộc kiểu `Explore` để quét codebase một cách tự nhiên. Ghi chép lại các điểm gây cản trở lập trình thực tế (architectural friction):
  * **Xung đột Định danh Toàn Cục (Cross-Package Symbol Collision - P6.22):** Quét phát hiện các class/function/module có tên trùng lặp giữa các package khác nhau nhưng thực hiện nghiệp vụ khác nhau (như `TableReconstructor` vs `AppendixExtractor`).
  * **Trôi dạt Import Cục bộ (Internal Import Drift):** Nơi các file CLI hoặc submodule con trong một package lại import từ package-root (`from pkg import ...`) thay vì dùng relative import (`from .core import ...`).
  * **Script Dùng Một Lần Tồn Dư (Legacy One-off Scripts):** Các script di trú ticket cũ (`execute_ticket*.py`) nằm rải rác trong các thư mục vận hành thay vì được lưu trữ tại `.md/knowledge/archive/`.
  * **Module Nông Thực Sự (True Shallow Modules):** Nơi nào giao diện interface phức tạp gần bằng phần code triển khai bên trong?
  * **Logic Bị Phân Mảnh (Scattered Domain Logic):** Nơi nào muốn hiểu một khái niệm nghiệp vụ lại phải nhảy qua nhảy lại giữa quá nhiều module nhỏ?
  * **Thiếu Kiểm Thử / Khó Viết Unit Test:** Phân vùng nào đang thiếu kiểm thử hoặc cực kỳ khó viết unit test với giao diện hiện tại?
- Áp dụng **phép thử xóa bỏ (deletion test)** đối với các module nghi ngờ bị nông: Nếu xóa module đó đi thì độ phức tạp sẽ tập trung lại một chỗ hay chỉ bị dịch chuyển sang chỗ khác? Nếu câu trả lời là "tập trung lại một chỗ", đó chính là seam tốt cần làm sâu.
- **Tiêu chí hoàn thành:** Lập danh sách ghi nhận được ít nhất 2 vùng module bị nông, coupling cao hoặc chứa nợ kỹ thuật thực tế, kèm kết quả phép thử xóa bỏ (deletion test) cho mỗi vùng.

### 1.5. Tự Phản Biện Trước Đề Xuất (5 Mandatory Adversarial Gates)
Trước khi tổng hợp các ứng viên vào Báo cáo HTML hoặc Implementation Plan, Agent **bắt buộc** phải tự chạy rà soát 5 cổng phản biện (theo Rule #8 và Session Learnings):

1. **Cổng 1: Phân biệt Glue Code vs Domain Logic (Rule P6.21):**
   * Đọc trực tiếp từng dòng của hàm/module định bóc tách: Nếu $\ge 70\%$ nội dung là `subprocess.run()`, `tempfile.TemporaryDirectory()`, `argparse/typer` logic, hoặc in banner console (`print`), đó là **Infrastructure Glue Code**.
   * *Rào chắn:* Nghiêm cấm bọc Glue Code thành Class/Seam mới trong core packages khi không có nghiệp vụ tính toán nội tại. Glue Code thuộc về tầng script/CLI.
2. **Cổng 2: Đếm Số Caller Thực Tế (Hard Caller Count Gate - Rule P6.5 & P6.23):**
   * Chạy lệnh `grep_search` đếm số lượng callers thực tế đang tồn tại trong codebase hiện hành.
   * *Rào chắn:* Nếu số **Caller $= 1$** (chỉ có chính CLI/script gọi nó), đề xuất bóc tách tạo Seam mới **bắt buộc phải bị xếp loại `Speculative / Low ROI`**, tuyệt đối không được gắn nhãn `Strong Recommendation`. Chỉ đề xuất Seam mới khi có **$\ge 2$ callers độc lập**.
3. **Cổng 3: Kiểm chứng SDK & Dependency Signatures:**
   * Các phương thức/class định tích hợp (ví dụ: `ccba_ai`, `httpx`) có thực sự hỗ trợ kiểu dữ liệu cần thiết và có signature khớp với mã nguồn thực tế không? (Bắt buộc `grep`/`view_file` mã nguồn package, không suy đoán).
4. **Cổng 4: Bất Biến Định Danh Duy Nhất (Cross-Package Unique Naming - Rule P6.22):**
   * Các tên class/module mới định đặt có bị trùng lặp với bất kỳ symbol nào khác trong Monorepo không? Nếu có, phải đổi tên phản ánh chính xác 100% trách nhiệm (ví dụ `AppendixExtractor` thay vì `TableReconstructor`).
5. **Cổng 5: Bằng Chứng Cản Trở Đo Lường Được (Measurable Friction over Theoretical Purity):**
   * Đề xuất refactor có giải quyết một điểm đau đo lường được (giảm thời gian test, sửa lỗi flaky test, triệt tiêu symbol collision, sửa import drift) hay chỉ là "tái cấu trúc thẩm mỹ cho đẹp mắt"? Nếu chỉ mang tính thẩm mỹ mà có rủi ro gãy vỡ $\rightarrow$ Ghi nhận ADR và Hoãn lại (Defer under KISS).

- **Tiêu chí hoàn thành:** Mỗi ứng viên đề xuất phải có bảng đánh giá 5 Cổng trên. Ứng viên vi phạm Cổng 1 hoặc Cổng 2 phải bị hạ cấp xuống `Speculative` hoặc loại bỏ trước khi xuất bản báo cáo.

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
  * **Problem:** Lý do kiến trúc hiện tại gây cản trở/friction đo lường được.
  * **Solution:** Mô tả bằng văn xuôi giải pháp thay đổi.
  * **Benefits:** Giải thích dưới góc độ tăng tính locality, leverage và cách cải thiện bộ test.
  * **Before / After diagram:** Sơ đồ side-by-side minh họa trực quan việc làm sâu module.
  * **Adversarial Gate Score:** Kết quả kiểm chứng 5 Cổng phản biện (Callers count, Glue vs Domain, Unique Naming).
  * **Recommendation strength:** Đánh giá mức độ đề xuất chính xác theo 5 Cổng:
    - `Strong`: $\ge 2$ callers thực tế + Domain Orchestration phức tạp + Giảm thời gian test rõ rệt.
    - `Worth exploring`: Housekeeping/Cleanup (giải quyết symbol collisions, import drift, dọn dẹp scripts).
    - `Speculative`: 1 caller, hoặc Glue Code thuần túy, hoặc rủi ro phá vỡ hợp đồng downstream (ADR + Defer).
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
