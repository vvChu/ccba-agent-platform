# Chế Độ C: Giải Thích, Làm Rõ & Tóm Lược (`Clarify & Explain`)

> **Tài liệu tham chiếu Chế độ C của `/ccba-ask`.** Nạp tệp này khi người dùng gõ `wait-what`, yêu cầu giải thích một kỹ năng/công cụ, hoặc muốn tóm lược ý nghĩa của phiên làm việc / đợt nâng cấp gần đây. Toàn bộ Chế độ C tuân thủ tuyệt đối nguyên tắc **Chỉ đọc (`Read-Only`)**.

---

## Mẫu 1: Wait-What — Giải Thích Lại Bằng Ngôn Ngữ Đời Thường

> *Thích ứng từ `wait-what` (Matt Pocock, MIT License).*

Kích hoạt khi người dùng gõ `wait-what`, *"khoan đã, chưa hiểu"*, hoặc chỉ trích dẫn một cụm từ khó hiểu ở tin nhắn trước:
1. **Dừng thực thi ngay lập tức:** Không tiếp tục lập trình, không sửa tệp, không chạy bước kế tiếp.
2. **Diễn đạt lại trực diện:**
   - Dùng tiếng Việt ngắn gọn, rõ ràng như người trao đổi trực tiếp với người; lược bỏ biệt ngữ, mã băm (hash), đường dẫn dài hoặc chỉ số kỹ thuật không cần thiết để hiểu ý.
   - Bổ sung bối cảnh nền bị thiếu và đối chiếu đúng thuật ngữ chuẩn hóa trong `CONTEXT.md`.
   - Nếu có thuật ngữ kỹ thuật bắt buộc giữ, giải thích nghĩa thực tế trong đúng 1 mệnh đề.
3. **Xác nhận hiểu:** Kết thúc bằng 1 câu hỏi ngắn kiểm tra người dùng đã nắm rõ ý chưa trước khi làm bước tiếp theo.

---

## Mẫu 2: Explain Skill — Giải Thích Kỹ Năng Hoặc Công Cụ

Kích hoạt khi người dùng hỏi *"giải thích skill X"*, *"skill X dùng trong codebase này thế nào?"*, hoặc *"có nên dùng công cụ X?"*:
1. **Quy chuẩn bắt buộc của CCBA (Đọc tệp đích trước khi kết luận):** Tuyệt đối không suy đoán chức năng từ tên gọi hay bản tóm tắt trong bảng định tuyến. Phải đọc trực tiếp tệp `SKILL.md` (hoặc tài liệu định nghĩa công cụ) của mục tiêu trước khi giải thích hoặc khuyên bỏ qua bước nào.
2. **Cấu trúc giải thích gọn (4 phần):**
   - **Bản chất (1–2 câu):** Kỹ năng đó giải quyết bài toán cụ thể gì và tạo ra đầu ra gì.
   - **Áp dụng cho repo hiện tại:** Nêu rõ điểm khớp thực tế với `workspace_context.yaml` / kiến trúc codebase đang mở.
   - **Khi nào nên dùng vs không nên dùng:** Chỉ rõ cặp kỹ năng thay thế nếu bối cảnh không phù hợp (tham khảo [`builtin_vs_ccba.md`](builtin_vs_ccba.md)).
   - **Ví dụ 1-click (tối đa 1 khối):** 1 câu lệnh mẫu sẵn dùng nếu người dùng muốn thử ngay (nhưng **không tự chạy**).

---

## Mẫu 3: Catch-Up Phiên / PR — Tóm Lược Ý Nghĩa & Quyết Định Đang Chờ

Kích hoạt khi người dùng hỏi *"đợt nâng cấp vừa xử lý có ý nghĩa gì?"*, *"bình luận kết quả phiên trước"*, hoặc quay lại sau một chuỗi tác vụ nền dài:
1. **Mở đầu bằng `Waiting Calls` (1–2 câu):** Nêu ngay việc nào đang chờ người dùng quyết định (merge, duyệt thiết kế, chọn phương án), hoặc xác nhận *"Hiện không có mục nào chờ bạn duyệt."*
2. **Tóm lược giá trị thực (ngắn gọn, hướng tác động):**
   - Nhấn mạnh **điều gì thay đổi cho hệ thống / người dùng** (bài toán nào đã khóa, lỗi nào đã chặn, đòn bẩy gì tăng lên), không liệt kê máy móc từng commit hay log chạy test.
   - Chỉ giữ lại con số thật đã kiểm chứng từ nguồn (git log, transcript, báo cáo) và ghi rõ phạm vi còn bỏ ngỏ (nếu có).
3. **Danh sách quyết định cần chốt (nếu có):** Với mỗi mục chờ người dùng, nêu gọn trong 1 gạch đầu dòng: **Quyết định cần chốt** + **Khuyến nghị mặc định (`Your Pick`)** + **Rủi ro chính**. Nếu cần vẽ sơ đồ minh họa mối liên hệ, giữ **tối đa 6 nút, $\le 8$ từ/nút** và tuyệt đối không vẽ danh sách trạng thái thành sơ đồ.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
