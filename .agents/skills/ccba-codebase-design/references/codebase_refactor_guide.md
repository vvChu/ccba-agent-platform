# ccba-improve-codebase-architecture — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Cẩm nang rà soát module sâu và tái cấu trúc kiến trúc mã nguồn
> **Mô tả gốc:** Quét codebase tìm kiếm cơ hội làm sâu module, xuất báo cáo trực quan dưới dạng HTML, và thực hiện grilling để chốt phương án cải tiến.

---

# Cải tiến Kiến trúc Mã nguồn (Improve Codebase Architecture)

Kỹ năng này giúp phát hiện các điểm nghẽn kiến trúc thực tế và đề xuất **Cơ hội làm sâu module (Deepening Opportunities)** — các hoạt động refactor giúp chuyển đổi các module nông (shallow modules) thành các module sâu (deep modules), đồng thời loại bỏ nợ kỹ thuật tồn dư (symbol collisions, import drift, legacy scripts). Mục tiêu tối thượng là tăng khả năng kiểm thử (testability) và tính dễ định hướng cho AI (AI-navigability).

Quy trình này được định hướng bởi domain model của dự án và xây dựng trên bộ từ vựng thiết kế phần mềm thống nhất:
- Sử dụng chính xác các thuật ngữ từ kỹ năng `/ccba-codebase-design` (**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**) và các nguyên lý đi kèm (phép thử xóa bỏ - deletion test, "interface là bề mặt kiểm thử", "một adapter = seam giả thuyết, hai adapter = seam thực tế"). Tuyệt đối không dùng lệch sang các từ "component", "service", "API" hoặc "boundary".
- Ngôn ngữ domain trong `CONTEXT.md` cung cấp tên gọi chuẩn cho các seam; các tài liệu ADR trong thư mục `.md/knowledge/` ghi nhận các quyết định kiến trúc đã chốt mà quy trình này không được tự ý lật lại.

---

## Quy trình Thực hiện (Process)

### Bước 1: Khám phá & Quét Thực Chiến (Explore & Ground-Truth Sweep)
- Đọc bảng thuật ngữ domain (`CONTEXT.md`) và bất kỳ tài liệu quyết định thiết kế (ADRs) liên quan đến phân vùng mã nguồn chuẩn bị tác động.
- Sử dụng subagent thuộc kiểu `Explore` để quét codebase một cách tự nhiên. Ghi chép lại các điểm gây cản trở lập trình thực tế (architectural friction):
  * **Xung đột Định danh Toàn Cục (Cross-Package Symbol Collision - P6.21):** Quét phát hiện các class/function/module có tên trùng lặp giữa các package khác nhau nhưng thực hiện nghiệp vụ khác nhau (như `TableReconstructor` vs `AppendixExtractor`).
  * **Xâm phạm Ranh giới Seam (Private Submodule Import Violation - P6.16, P6.17):** Nơi code bên ngoài package vượt qua `__init__.py` public interface để import trực tiếp vào file private `_internal.py` hoặc submodule lõi (`from ccba_pkg._core import ...`). *Lưu ý:* Absolute import hợp lệ bên trong cùng một package (`from pkg.core import X` trong `pkg/cli/cmd.py`) theo PEP 328 **không phải** là import drift.
  * **Script Dùng Một Lần Tồn Dư (Legacy One-off Scripts):** Các script di trú ticket cũ (`execute_ticket*.py`) nằm rải rác trong các thư mục vận hành thay vì được lưu trữ tại `.md/knowledge/archive/`.
  * **Module Nông Thực Sự (True Shallow Modules):** Nơi nào giao diện interface phức tạp gần bằng phần code triển khai bên trong?
  * **Logic Bị Phân Mảnh (Scattered Domain Logic):** Nơi nào muốn hiểu một khái niệm nghiệp vụ lại phải nhảy qua nhảy lại giữa quá nhiều module nhỏ?
  * **Thiếu Kiểm Thử / Khó Viết Unit Test:** Phân vùng nào đang thiếu kiểm thử hoặc cực kỳ khó viết unit test với giao diện hiện tại?
  * **Vi phạm Hợp Đồng Phụ Thuộc (Dependency Contract Violations - P6.16):** Nếu dự án có bộ quét AST hợp đồng (`check_dependency_contracts.py` hoặc `.importlinter`), chạy trước và ghi nhận kết quả. Các vi phạm `PrivateSubmoduleSeamViolation`, `FoundationLeafPurityViolation`, `LeafIndependenceViolation` là ứng viên friction sẵn có.
- Áp dụng **phép thử xóa bỏ (deletion test)** đối với các module nghi ngờ bị nông: Nếu xóa module đó đi thì độ phức tạp sẽ tập trung lại một chỗ hay chỉ bị dịch chuyển sang chỗ khác? Nếu câu trả lời là "tập trung lại một chỗ", đó chính là seam tốt cần làm sâu.
- **Tiêu chí hoàn thành:** Lập danh sách thô các vùng module bị nông, coupling cao hoặc chứa nợ kỹ thuật thực tế.

### Bước 2: Vòng Bắn Hạ & 5 Cổng Phản Biện Kèm Bằng Chứng (Adversarial Shoot-Down & 5 Evidence-Backed Gates)

*Quy tắc bất biến:* **Tuyệt đối không đưa các phỏng đoán hoặc heuristic chưa kiểm chứng vào Báo cáo HTML.** Trước khi chuyển sang bước dựng báo cáo, Agent **bắt buộc** phải thực thi vòng bắn hạ tích hợp sẵn 5 cổng phản biện đối với từng ứng viên thô. Mỗi cổng yêu cầu **bằng chứng thực địa (Hard Evidence)** — không chấp nhận dấu tích ✅ tự khai:

1. **Cổng 1: Phân biệt Glue Code vs Domain Logic (Rule P6.20):**
   * **Hành động bắt buộc:** Đọc trực tiếp từng dòng (`view_file`) của hàm/module định bóc tách. Đếm tỷ lệ dòng `subprocess/tempfile/argparse/print` so với dòng thuật toán nghiệp vụ.
   * **Dẫn chứng ghi vào báo cáo:** Tệp, phạm vi dòng, tỷ lệ phần trăm Glue vs Domain.
   * *Rào chắn:* Nếu $\ge 70\%$ là Glue Code $\rightarrow$ Giữ nguyên tại CLI script, không bọc thành Seam lõi. **Loại bỏ ứng viên.**

2. **Cổng 2: Đếm Số Caller & Xác Minh Implementation (Hard Caller Gate - Rule P6.5, P6.22):**
   * **Hành động bắt buộc:** Chạy `grep_search` đếm callers thực tế. Sau đó **mở mã nguồn** (`view_file`) của **từng caller** để xác minh caller đang *tự viết lại logic* hay *đã import từ Deep Seam SSOT*.
   * **Dẫn chứng ghi vào báo cáo:** Danh sách `file:line` của từng caller kèm đánh giá "tự triển khai" hoặc "import SSOT".
   * *Rào chắn:* Nếu caller đã import SSOT chuẩn $\rightarrow$ **Xác định là False Positive, loại bỏ 100%.** Nếu Caller $= 1$ (không phức tạp domain) $\rightarrow$ Xếp loại `Speculative / Low ROI`.

3. **Cổng 3: Kiểm chứng SDK & Dependency Signatures:**
   * **Hành động bắt buộc:** Các phương thức/class định tích hợp có signature khớp với mã nguồn thực tế không? `grep`/`view_file` mã nguồn package, không suy đoán.
   * **Dẫn chứng ghi vào báo cáo:** Signature thực tế trích xuất từ `packages/.../core.py`.

4. **Cổng 4: Bất Biến Định Danh Duy Nhất (Cross-Package Unique Naming - Rule P6.21):**
   * **Hành động bắt buộc:** `grep_search` xác nhận symbol name mới chưa từng tồn tại ở bất kỳ package nào khác.
   * **Dẫn chứng ghi vào báo cáo:** Kết quả `grep_search` (0 matches = đạt).

5. **Cổng 5: Bằng Chứng Cản Trở Đo Lường Được (Measurable Friction - Not Theoretical):**
   * **Hành động bắt buộc:**
     - Nếu liên quan hiệu năng: Chạy 1 lệnh benchmark (`time.perf_counter()` hoặc `Measure-Command`) để lấy số đo thực tế `[đo thực tế: X ms]`. Khi phát hiện điểm nghẽn duyệt file/I/O: luôn kiểm tra xem lệnh quét có đang duyệt vào các thư mục rác (`node_modules`, `.md`, `.git`, `.venv`) hay không trước khi kết luận thuật toán bị chậm.
     - Nếu liên quan lỗi runtime: Trích xuất traceback hoặc log crash cụ thể (ví dụ: `UnicodeEncodeError charmap CP1252`).
     - Nếu chỉ mang tính thẩm mỹ mà có rủi ro gãy vỡ $\rightarrow$ Ghi nhận ADR và Hoãn lại (Defer under KISS). **Loại bỏ ứng viên.**
   * **Dẫn chứng ghi vào báo cáo:** Số đo benchmark hoặc traceback lỗi cụ thể.

**Đào Thải & Ghi Nhận:**
- **Rào chắn cứng:** Số ứng viên đưa vào Báo cáo HTML **KHÔNG ĐƯỢC VƯỢT QUÁ 3**. Nếu sau Vòng Bắn Hạ vẫn còn >3 ứng viên đạt chuẩn, xếp hạng theo ROI (Callers $\times$ Measurable Friction) và loại bỏ các ứng viên xếp cuối cho đến khi $\le 3$.
- **Ghi nhận ứng viên bị loại (Eliminated Candidate Record — BẮT BUỘC):** Đối với **mỗi** ứng viên bị bắn hạ hoặc bị loại do vượt ngưỡng 3, Agent **bắt buộc** ghi lại một dòng ngắn gọn gồm: tên ứng viên, cổng nào bắn hạ (hoặc "ROI thấp hơn"), lý do 1 câu. Danh sách này được đính kèm vào phần cuối Báo cáo HTML (mục *"Ứng viên đã loại"*) để các đợt quét kiến trúc sau không lặp lại cùng đề xuất. Nếu lý do loại bỏ là một quyết định kiến trúc nền tảng quan trọng $\rightarrow$ Đề xuất ghi nhận thành ADR.

- **Tiêu chí hoàn thành:** Toàn bộ $\le 3$ ứng viên đưa vào HTML đều có bảng 5 Cổng đính kèm dẫn chứng `file:line` và số liệu đo thực tế. Phần **"Ứng viên đã loại"** trong HTML **không được để trống** — nếu không có ứng viên nào bị loại, ghi rõ "Không có ứng viên bị loại trong đợt quét này".

### Bước 3: Trình bày Báo cáo dưới dạng HTML (Present candidates as an HTML report)
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
  * **Giới hạn cứng:** Báo cáo chỉ hiển thị **tối đa 3 ứng viên** đã vượt qua Vòng Bắn Hạ (Bước 2). Vi phạm giới hạn này khiến báo cáo không đạt Tiêu chí hoàn thành.
  * Mỗi ứng viên cải tiến phải có hình ảnh so sánh **trước/sau (Before/After)** trực quan.
- Mỗi ứng viên đề xuất (card) phải hiển thị đủ:
  * **Files:** Các tệp tin/module liên quan kèm dòng code cụ thể.
  * **Problem:** Lý do kiến trúc hiện tại gây cản trở/friction đo lường được (kèm số đo benchmark thực tế).
  * **Solution:** Mô tả bằng văn xuôi giải pháp thay đổi (ưu tiên Re-export / KISS trước khi tạo Seam).
  * **Benefits:** Giải thích dưới góc độ tăng tính locality, leverage và cách cải thiện bộ test.
  * **Before / After diagram:** Sơ đồ side-by-side minh họa trực quan việc làm sâu module.
  * **Adversarial Gate Evidence:** Bảng dẫn chứng 5 Cổng phản biện (Callers count thực tế kèm `file:line`, SDK signature, Unique Naming, Real friction).
  * **Recommendation strength:** Đánh giá mức độ đề xuất chính xác theo 5 Cổng:
    - `Strong`: $\ge 2$ callers thực tế (đã xác minh implementation) + Domain Orchestration phức tạp + Bằng chứng đo lường cải thiện rõ rệt.
    - `Worth exploring`: Housekeeping/Cleanup (giải quyết symbol collisions, import drift, dọn dẹp scripts).
    - `Speculative`: 1 caller, hoặc Glue Code thuần túy (ADR + Defer under KISS).
- Kết thúc báo cáo bằng:
  * **Đề xuất hàng đầu (Top recommendation)** để chỉ rõ ứng viên nên xử lý đầu tiên kèm lý do.
  * **Danh sách ứng viên đã loại (Eliminated Candidates):** Bảng gồm tên ứng viên, cổng bắn hạ, lý do 1 câu. Đây là bộ nhớ cho các đợt quét tương lai.
- **Tiêu chí hoàn thành:** Báo cáo HTML được ghi thành công vào thư mục tạm `.md/scratch/`, mở được trên trình duyệt mặc định mà không gặp lỗi CLI, hiển thị đầy đủ các thẻ ứng viên, sơ đồ Before/After, và danh sách ứng viên bị loại.

### Bước 4: Vòng lặp Chất vấn (Grilling loop)
- Sau khi người dùng chọn một ứng viên cải tiến, kích hoạt kỹ năng `/ccba-grilling` để tiến hành phỏng vấn sâu với Kỹ sư về: các ràng buộc (constraints), dependency, cấu trúc của module được làm sâu, logic nằm sau seam, và các test case được bảo toàn.
- Cập nhật domain model và tài liệu tri thức song song:
  * Nếu đặt tên module làm sâu theo một khái niệm mới chưa có trong `CONTEXT.md` $\rightarrow$ Thêm thuật ngữ đó vào `CONTEXT.md`.
  * Nếu làm sắc nét thêm một thuật ngữ mập mờ $\rightarrow$ Cập nhật định nghĩa trực tiếp vào `CONTEXT.md`.
  * Nếu người dùng từ chối đề xuất vì một lý do kỹ thuật nền tảng quan trọng $\rightarrow$ Đề xuất ghi nhận thành tài liệu ADR trong thư mục `.md/knowledge/` để tránh các đợt quét sau đề xuất lại trùng lặp.
  * Nếu muốn so sánh các thiết kế interface khác nhau cho module sâu $\rightarrow$ Kích hoạt kỹ năng `/ccba-codebase-design` và chạy cơ chế parallel sub-agent (thiết kế hai phương án độc lập để đối chiếu).
  * **Đề xuất dựng mẫu thử nhanh (ADR 0010):** Sau khi thống nhất phương án triển khai, nếu việc refactor ảnh hưởng trực tiếp đến **Core Platform (Hub)** (ví dụ: sửa đổi core services, metadata registry, database schema chung), Agent bắt buộc phải đề xuất hoặc kích hoạt `/ccba-prototype` (nhánh Logic/UI) để dựng nhanh mô phỏng hoạt động trước khi code thật. Đối với các Spoke apps hoặc hàm nghiệp vụ độc lập, Agent đề xuất viết code trực tiếp và chạy suite kiểm thử để tối ưu thời gian.
- **Tiêu chí hoàn thành:** Phiên chất vấn grilling kết thúc, thống nhất được phương án triển khai cụ thể, và các tài liệu tri thức (`CONTEXT.md`, ADRs) được cập nhật đồng bộ.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
