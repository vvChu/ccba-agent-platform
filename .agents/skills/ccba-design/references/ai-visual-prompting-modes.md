# Ba Chế Độ Kiến Tạo Prompt Thị Giác AI & Cổng Thẩm Định Brief (Clean-Room Synthesis)

> **Tư thế Kiến trúc & Bản quyền:** Tài liệu tổng hợp nguyên bản (Clean-Room Engineering) dành riêng cho hệ sinh thái CCBA Agent Services Platform. Mọi tác vụ sinh mô tả thị giác, SVG hoặc kịch bản tạo ảnh bắt buộc định tuyến qua Seam `ccba_ai.routing.choose_model()` (`ModelArchetype`) trên AI Gateway nội bộ; nghiêm cấm nhúng cứng chuỗi định danh mô hình thô hoặc gọi công cụ bên ngoài không qua kiểm soát.

Tài liệu này quy định cổng khóa thông tin đầu vào trước khi sinh tài sản đồ họa và 3 phương thức cấu trúc câu lệnh thị giác (Visual Prompting Modes) phục vụ thiết kế cổng thông tin kỹ thuật, hồ sơ năng lực B2B, ấn phẩm BIM/xây dựng và truyền thông thương hiệu trong `/ccba-design`.

---

## 1. Cổng Khóa Brief Trước Khi Sinh Tài Sản (Pre-Generation Brief Gate)

Tuyệt đối không phát lệnh sinh hình ảnh hoặc dựng đồ họa từ một yêu cầu mơ hồ một dòng. Trước khi soạn cấu trúc prompt, Agent bắt buộc xác lập rõ **5 thông số nền tảng** (trích xuất từ `MASTER.md` / ngữ cảnh dự án hoặc hỏi ngắn gọn qua `ask_question` nếu chưa có):

1. **Chủ thể trọng tâm & Hành động (Focal Subject):** Đối tượng chính cần thể hiện là gì (công trình hạ tầng, sơ đồ mặt cắt kỹ thuật, chân dung vận hành, hay biểu tượng trừu tượng)?
2. **Tỷ lệ khung hình đích (Target Aspect Ratio):**
   - `1:1` — Ảnh vuông mạng xã hội, thẻ danh mục, biểu trưng cân đối.
   - `16:9` — Trang bìa thuyết trình, khung hero cổng thông tin web, hình thu nhỏ video.
   - `4:3` — Minh họa chèn trong báo cáo kỹ thuật, tài liệu hướng dẫn đọc sâu.
   - `9:16` — Khung dọc thiết bị di động, bảng thông tin đứng.
3. **Bảng màu & Hệ Token Thương Hiệu (Design-System Palette):** Ánh xạ trực tiếp mã màu chủ đạo, màu nhấn và độ tương phản nền sáng/tối từ bộ semantic tokens của dự án để hình ảnh ăn khớp hoàn toàn với giao diện bao quanh.
4. **Bề mặt xuất bản & Khoảng thở bố cục (Surface & Negative Space):** Xác định rõ vị trí đặt chữ đè lên ảnh (text overlay safe zone) để chừa mảng nền tĩnh tối thiểu `25–35%` diện tích không có chi tiết rối.
5. **Ranh giới loại trừ (Negative Constraints):** Liệt kê tường minh các yếu tố cấm xuất hiện (chữ vô nghĩa bị méo nét, hiệu ứng lóa sáng nhân tạo rẻ tiền, chi tiết kết cấu sai lệch vật lý xây dựng, biểu tượng nhạy cảm).

---

## 2. Ba Chế Độ Cấu Trúc Prompt Thị Giác (Three Visual Prompting Modes)

Tùy theo dữ liệu đầu vào của bài toán, lựa chọn một trong ba chế độ kiến tạo câu lệnh sau:

### Chế Độ 1 — Tra Cứu Nguyên Mẫu Ngành Nghề (Domain Archetype Lookup)
Áp dụng khi khởi tạo mới tài sản hình ảnh cho một lĩnh vực chuyên môn đã rõ tính chất (tư vấn xây dựng, khu công nghiệp FDI, kiểm định an toàn PCCC, quản trị dữ liệu số).
- **Cấu trúc lắp ghép 5 lớp:** `[Chủ thể & Bối cảnh ngành] + [Góc máy & Tiêu cự quang học] + [Chất liệu bề mặt & Ánh sáng] + [Bảng màu định hướng từ Design Tokens] + [Ràng buộc kỹ thuật & Tỷ lệ khung]`.
- **Nguyên tắc kiểm soát:** Luôn neo cụ thể tính chất vật liệu (bê tông trần, kính cường lực, thép kết cấu, giấy mỹ thuật mờ) và nguồn sáng tự nhiên có hướng thay vì dùng các tính từ ca ngợi sáo rỗng. Kết hợp tra cứu kho dữ liệu nội bộ `../scripts/ui/search.py`, `../scripts/logo/search.py` hoặc `../scripts/cip/search.py` để đồng bộ ngôn ngữ ngành.

### Chế Độ 2 — Tái Tổ Hợp Cấu Trúc Đa Tham Chiếu (Multi-Reference Structural Remix)
Áp dụng khi người dùng cung cấp từ hai hình ảnh hoặc mẫu giao diện tham khảo trở lên và muốn chắt lọc ưu điểm riêng của từng nguồn vào một thiết kế thống nhất.
- **Quy tắc phân vai tách bạch (Orthogonal Slot Assignment):** Mỗi tài liệu tham chiếu chỉ được gán quyền quyết định cho **duy nhất một chiều thuộc tính** để tránh xung đột hỗn độn:
  - *Tham chiếu A (Khung bố cục & Hình học):* Quy định tỷ lệ chia cột, đường dẫn mắt, vị trí điểm nhấn và tỷ lệ khoảng trắng.
  - *Tham chiếu B (Hệ sắc độ & Ánh sáng):* Quy định nhiệt độ màu, độ tương phản sáng tối và chất cảm bề mặt.
  - *Tham chiếu C (Mật độ chi tiết):* Quy định mức độ tối giản hoặc chi tiết kỹ thuật của đường nét.
- Trước khi xuất câu lệnh cuối, viết rõ bảng ánh xạ 3 dòng xác nhận thuộc tính nào lấy từ nguồn nào và thuộc tính nào của nguồn cũ bị loại bỏ hoàn toàn.

### Chế Độ 3 — Chuyển Giao Phong Cách Kỹ Thuật Có Kiểm Soát (Controlled Technical Style Transfer)
Áp dụng khi cần chuyển hóa cùng một nội dung nghiệp vụ sang các ngôn ngữ biểu đạt chuyên ngành phục vụ báo cáo, hội thảo kỹ thuật hoặc cổng thông tin điều hành:
- **Bản vẽ mặt cắt kiến trúc (Architectural Section Cut):** Đường nét kỹ thuật sắc gọn trên nền giấy sáng, mặt cắt trực giao làm nổi bật luồng di chuyển, hệ thống cơ điện MEP hoặc tuyến thoát nạn bằng một màu nhấn duy nhất.
- **Mô hình trục đo kỹ thuật số (Isometric BIM & Infrastructure View):** Góc chiếu đẳng cự `30°` sạch sẽ, phân lớp rõ các tầng dữ liệu (kết cấu, thiết bị, cảm biến), nền trung tính không nhiễu, phù hợp minh họa kiến trúc hệ thống và CDE.
- **Lưới mô-đun Bento điều hành (Modular Bento Grid):** Sắp xếp các khối thông tin tỷ lệ bất đối xứng cân bằng, bo góc đồng bộ với hệ thống component, ánh sáng phẳng dịu nhẹ.
- **Khắc nét tối giản biên tập (Minimalist Editorial Line Engraving):** Nét mảnh đơn sắc hoặc hai tông màu tương phản cao, phù hợp làm hình minh họa đầu chương cho tài liệu quy chuẩn, hồ sơ thầu và cẩm nang quản trị.

---

## 3. Quy Trình Kiểm Chứng Hậu Sinh & Dự Phòng An Toàn

1. **Định tuyến thực thi chuẩn nền tảng:** Với biểu tượng vector và sơ đồ cấu trúc, ưu tiên xuất mã XML/SVG sạch qua `../scripts/icon/generate.py` (sử dụng `ModelArchetype.REASONING`). Với các kịch bản kết xuất bitmap trong `../scripts/logo/generate.py` hoặc `../scripts/cip/generate.py`, tuân thủ cơ chế dừng báo lỗi minh bạch (Fail-Fast) của adapter nếu Seam sinh ảnh chuyên biệt chưa được bật trên môi trường hiện tại.
2. **Kiểm định chất lượng đầu ra:** Đối chiếu sản phẩm với 5 thông số tại Cổng khóa Brief — đảm bảo vùng đặt chữ đạt chuẩn tương phản WCAG 2.2 (`>= 4.5:1` kiểm tra bằng `../scripts/ui/search.py --contrast`), không vỡ bố cục ở các kích thước xuất bản mục tiêu và không sót chi tiết sai lệch ngữ cảnh chuyên môn.
