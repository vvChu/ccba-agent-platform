# Thư viện Kỹ thuật Brainstorm

> Tài liệu tham chiếu cho workflow `/ccba-brainstorm`. Agent nạp file này khi cần gợi ý kỹ thuật phù hợp với chủ đề.

---

## Hướng dẫn chọn kỹ thuật

| Tình huống | Nhóm đề xuất |
|------------|-------------|
| Chủ đề mới, chưa có ý tưởng nào | Structured |
| Đã có ý tưởng ban đầu, cần mở rộng | Creative |
| Bí ý tưởng, cần phá vỡ lối mòn | Creative hoặc Provocative |
| Cần đào sâu 1 hướng cụ thể | Deep Exploration |
| Cần nhiều góc nhìn đa chiều | Collaborative |

---

## Nhóm 1: Structured Frameworks (Khuôn khổ có cấu trúc)

### SCAMPER
Áp dụng 7 phép biến đổi lên ý tưởng/sản phẩm hiện có: **S**ubstitute (Thay thế), **C**ombine (Kết hợp), **A**dapt (Thích ứng), **M**odify (Chỉnh sửa), **P**ut to other use (Dùng khác), **E**liminate (Loại bỏ), **R**everse (Đảo ngược). Phù hợp khi cải tiến sản phẩm/quy trình đã tồn tại.

### Six Thinking Hats (Sáu chiếc mũ tư duy)
Nhìn vấn đề từ 6 góc: Sự kiện (Trắng), Cảm xúc (Đỏ), Rủi ro (Đen), Lợi ích (Vàng), Sáng tạo (Xanh lá), Quy trình (Xanh dương). Mỗi "mũ" một vòng brainstorm riêng. Phù hợp khi nhóm có xu hướng tranh luận thay vì sáng tạo.

### Mind Mapping
Bắt đầu từ chủ đề trung tâm, phân nhánh tự do. Mỗi nhánh là một khía cạnh, mỗi lá là ý tưởng cụ thể. Phù hợp khi cần hệ thống hóa ý tưởng rời rạc.

---

## Nhóm 2: Creative Expansion (Mở rộng sáng tạo)

### Reversal (Đảo ngược)
Đặt câu hỏi ngược: "Làm sao để thất bại hoàn toàn?" hoặc "Điều gì sẽ khiến khách hàng ghét sản phẩm?" Sau đó đảo ngược các câu trả lời thành giải pháp. Phù hợp khi bị kẹt trong lối mòn tư duy.

### Analogical Thinking (Tư duy tương tự)
Mượn giải pháp từ ngành/lĩnh vực khác: "Ngành hàng không giải quyết vấn đề tương tự thế nào?" Phù hợp khi cần đột phá ngoài phạm vi chuyên môn.

### What-if (Giả định)
Đặt các giả định cực đoan: "Nếu ngân sách không giới hạn?", "Nếu chỉ có 1 ngày?", "Nếu khách hàng là trẻ em 10 tuổi?" Phù hợp khi cần phá vỡ ràng buộc tâm lý.

### Random Stimulus (Kích thích ngẫu nhiên)
Chọn một từ/hình ảnh ngẫu nhiên, tìm liên kết với chủ đề. Sự ngẫu nhiên buộc não bộ tạo kết nối mới. Phù hợp khi nhóm đã cạn ý tưởng.

---

## Nhóm 3: Deep Exploration (Khám phá sâu)

### 5 Whys (5 lần Tại sao)
Hỏi "Tại sao?" liên tiếp 5 lần để đào xuống gốc rễ vấn đề. Mỗi câu trả lời mở ra lớp nguyên nhân sâu hơn. Phù hợp khi cần hiểu rõ bản chất trước khi sinh ý tưởng.

### Question Storming (Bão câu hỏi)
Thay vì sinh ý tưởng, sinh **câu hỏi** về chủ đề. Mục tiêu: 15-20 câu hỏi trong 10 phút. Câu hỏi hay thường mở ra hướng giải quyết tốt hơn câu trả lời vội. Phù hợp khi chưa rõ vấn đề thực sự là gì.

### Assumption Mapping (Liệt kê giả định)
Liệt kê mọi giả định đang ngầm chấp nhận, sau đó thách thức từng cái: "Giả định này có đúng không? Nếu sai thì sao?" Phù hợp khi cần đánh giá lại nền tảng của dự án.

---

## Nhóm 4: Collaborative (Cộng tác đa vai)

### Role Playing (Nhập vai)
Mỗi persona (khách hàng, đối thủ, nhà đầu tư, skeptic) đóng góp ý tưởng từ góc nhìn riêng. Tích hợp với **Party Mode** của workflow. Phù hợp khi cần đa chiều hóa ý tưởng.

### Round Robin (Luân phiên)
Mỗi lượt chỉ 1 người (hoặc persona) nêu 1 ý tưởng, luân phiên liên tục. Tránh 1 giọng nói áp đảo. Phù hợp khi có nhiều persona trong Party Mode.

### Brainwriting
Viết ý tưởng ra giấy (hoặc text) thay vì nói. Sau mỗi vòng, trao đổi bản viết và xây dựng trên ý tưởng người khác. Phù hợp khi cần độ sâu hơn tốc độ.

---

## Cách sử dụng

Agent đọc file này khi cần gợi ý kỹ thuật cho phiên brainstorm. Chọn dựa trên:
1. Bảng "Hướng dẫn chọn kỹ thuật" ở trên
2. `suggested_techniques` trong `brainstorm_topics.yaml` (nếu có)
3. Tình trạng hiện tại của phiên (stuck → Creative, cần sâu → Deep, cần đa chiều → Collaborative)

Mỗi kỹ thuật chạy theo Hybrid Rhythm: Agent gợi ý technique → giải thích 1-2 câu → bắt đầu vòng đầu tiên.
