# Visual & Diagramming Rules — Quy Chuẩn Trực Quan Hóa Tri Thức

Tài liệu này tổng hợp các quy chuẩn công thái học thị giác (Document Ergonomics) bắt buộc áp dụng khi biên dịch sách thành sơ đồ và bảng biểu.

---

## 1. Ngưỡng Vàng Lai (Hybrid Golden Threshold)

- **Khi nào dùng Mermaid inline?**:
  - Luồng tuyến tính một chiều ($\le 8$ nodes).
  - Tương tác song phương (sequence $\le 6$ bước).
  - Sơ đồ phân nhánh đơn giản.
- **Khi nào BẮT BUỘC vẽ Excalidraw 16:9?**:
  - Sơ đồ kiến trúc tổng thể $\ge 3$ layers.
  - Số lượng node $\ge 9$ nodes.
  - Kết nối chéo phức tạp $\ge 3$ subgraphs.
  - Vị trí lưu tệp: BẮT BUỘC lưu tại `03 - Resources/attachments/<ten_so_do>.excalidraw.md`.

---

## 2. Quy Chuẩn Sơ Đồ Excalidraw 16:9 (Executive Typography)

1. **Khung Canvas 16:9**:
   - Chiều rộng hộp bao ngang (Horizontal Bounding Box, tính cả tọa độ điểm mũi tên 2D `el.x + pt[0]`): Khóa cứng $1.000\text{px} \le W \le 1.150\text{px}$ (khuyến nghị chuẩn $1.080\text{px}$; cổng C4 `verify_excalidraw_map.py` kiểm định cứng trên cả JSON thô và `compressed-json`).
   - Chiều cao canvas mục tiêu: Khuyến nghị tỷ lệ $600\text{px} \le H \le 720\text{px}$ (mở rộng tự động theo số tầng để không tràn chữ).
2. **Cỡ chữ gốc (Raw `fontSize` Floor)**:
   - Tiêu đề chính (Title): $24\text{px} - 28\text{px}$, Bold.
   - Nhãn phân hệ (Section Header): $16\text{px} - 20\text{px}$, Bold.
   - Nội dung node (Node Text): Khóa cứng sàn `fontSize ≥ 13px` (khuyến nghị $13\text{px} - 15\text{px}$, đồng bộ 100% với `excalidraw_worker.py` và cổng C4 Pha 6 để đảm bảo sàn hiển thị $\ge 8.5\text{px}$ sau khi nhúng thu phóng trong note).
3. **Auto-Expand Container**:
   - Chiều cao khung chứa phải lớn hơn chiều cao văn bản ít nhất $30\text{px}$ ($H \ge H_{text} + 30\text{px}$) để chống tràn text.
4. **Màu sắc Grayscale Học thuật**:
   - Sử dụng bảng màu Grayscale (nền xám nhạt `#f4f4f5` / `#e4e4e7`, viền `#27272a` hoặc `#52525b`, chữ `#18181b`). Tránh màu vàng chói hoặc phối màu sặc sỡ.
5. **Bảng Đặc Tả Ma Trận Kiến Trúc Markdown**:
   - BẮT BUỘC tạo Bảng Đặc Tả ngay dưới thẻ nhúng `![[...excalidraw.md|100%]]` trong Topic Note để phục vụ tra cứu văn bản và nạp ngữ cảnh cho LLM (được cổng C4 kiểm tra tự động khi Topic Note nhúng `.excalidraw`).

---

## 3. Quy Chuẩn Bảng Markdown Bản Địa (Zero-ASCII Box Art)

- **CẤM TUYỆT ĐỐI**: Dùng khối mã nguồn văn bản với các ký tự ASCII hộp phân cách để vẽ bảng hoặc sơ đồ.
- **BẮT BUỘC**: Dùng thẻ Bảng Markdown chuẩn (`| Cột 1 | Cột 2 |`) với các quy tắc:
  - Căn lề rõ ràng: `| :--- | :--- | :---: | :--- |`
  - Thoát ký tự pipe khi nhúng wikilink trong bảng:
    ```text
    [[slug|Tên hiển thị]]  -->  [[slug\|Tên hiển thị]]
    ```
  - Xuống dòng nội bộ ô bảng bằng thẻ HTML `<br/>`.
  - Không để rò rỉ các thực thể HTML parser (`#40;`, `#41;`) ra ngoài bảng Markdown; dùng dấu ngoặc đơn thông thường `()`.
