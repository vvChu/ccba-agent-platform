# Thiết Kế Thử Nghiệm Định Lượng A/B & Kiểm Chứng Thông Điệp (Clean-Room Synthesis)

> **Tư thế Kiến trúc & Bản quyền:** Tài liệu tổng hợp nguyên bản (Clean-Room Engineering) phục vụ quy trình kiểm chứng thông điệp cổng thông tin B2B, trang giới thiệu dịch vụ tư vấn kỹ thuật và luồng tiếp nhận yêu cầu khách hàng trong `/ccba-copywriting`.

Thay vì tranh luận cảm tính về câu chữ tiêu đề, bố cục biểu mẫu hay lời kêu gọi hành động (CTA), mọi thay đổi trên bề mặt chuyển đổi quan trọng cần được đóng khung thành một phép thử có giả thuyết định lượng rõ ràng, cỡ mẫu tính trước và rào chắn thống kê nghiêm ngặt.

---

## 1. Khung Giả Thuyết Định Lượng Năm Thành Tố (5-Part Quantitative Hypothesis)

Không khởi chạy bất kỳ thử nghiệm nào nếu chỉ dừng ở mức *"thử đổi màu nút hoặc rút gọn tiêu đề xem sao"*. Một giả thuyết đạt chuẩn bắt buộc nối liền mạch 5 thành tố:

1. **Bằng chứng quan sát hiện trạng (Observed Friction):** Dữ liệu định lượng hoặc nhật ký phiên thực tế chỉ ra điểm rơi (ví dụ: tỷ lệ rời trang tại bước điền biểu mẫu yêu cầu thẩm định thiết kế vượt ngưỡng `68%`).
2. **Thay đổi can thiệp cụ thể (Proposed Intervention):** Mô tả chính xác biến số duy nhất được điều chỉnh ở phiên bản thử nghiệm so với bản đối chứng (ví dụ: rút biểu mẫu từ 9 trường xuống 4 trường cốt lõi và bổ sung dòng cam kết bảo mật hồ sơ bản vẽ ngay dưới nút gửi).
3. **Phân khúc đối tượng áp dụng (Target Cohort):** Nhóm lưu lượng nào tham gia phép thử (khách truy cập mới trên máy tính bàn, kỹ sư truy cập từ tài liệu chuyên môn, hay toàn bộ lưu lượng trang dịch vụ).
4. **Biên độ dịch chuyển kỳ vọng (Expected Directional Lift):** Chỉ số chính dự kiến thay đổi theo chiều nào và mức chênh lệch tối thiểu có ý nghĩa kinh doanh là bao nhiêu.
5. **Cơ chế tâm lý hoặc vận hành giải thích (Underlying Mechanism):** Vì sao sự can thiệp này giải quyết được rào cản nhận thức của người đọc (giảm ma sát nhập liệu và xóa bỏ lo ngại lộ lọt thông tin dự án trước khi ký NDA).

---

## 2. Phân Loại Mô Hình Thử Nghiệm Theo Quy Mô Lưu Lượng

| Mô Hình Phép Thử | Cơ Chế Phân Phối | Điều Kiện Áp Dụng Phù Hợp | Cảnh Báo Giới Hạn |
| :--- | :--- | :--- | :--- |
| **A/B Tiêu chuẩn** | Chia đều lưu lượng giữa 1 bản gốc (Control) và 1 bản biến thể (Variant) | Khi muốn kiểm định dứt điểm tác động của **một giả thuyết thay đổi rõ rệt** trên lưu lượng vừa và nhỏ | Không gộp quá nhiều thay đổi rời rạc nếu sau đó cần biết chính xác yếu tố nào tạo ra khác biệt. |
| **A/B/n Đa phương án** | So sánh đồng thời bản gốc với 2–3 biến thể thông điệp khác góc tiếp cận | Khi chọn lựa giữa các khung lập luận thuyết phục khác hẳn nhau (xem `copy-formulas.md`) trên trang lưu lượng khá | Cỡ mẫu yêu cầu tăng theo số lượng nhánh và cần hiệu chỉnh ngưỡng sai số tích lũy khi so sánh nhiều cặp. |
| **Đa biến (MVT)** | Tổ hợp đồng thời nhiều thành phần giao diện (tiêu đề × minh họa × nút hành động) | Chỉ dành cho cổng thông tin có lưu lượng truy cập rất lớn muốn đo hiệu ứng tương tác chéo giữa các phần tử | Tuyệt đối không dùng MVT trên trang B2B ít lượt truy cập vì thời gian thu thập mẫu sẽ kéo dài vô tận. |
| **Tách luồng đường dẫn (Split URL)** | Điều hướng người xem sang hai kiến trúc trang hoàn toàn độc lập | Khi đối chiếu hai cấu trúc dẫn dắt khác nhau từ gốc (ví dụ: trang đọc chuyên sâu dài hạn đối đầu trang tóm lược đặt lịch trực tiếp) | Phải khóa thẻ canonical về bản gốc và chặn lập chỉ mục trùng lặp trên đường dẫn thử nghiệm tạm thời. |

---

## 3. Cỡ Mẫu, Lực Thống Kê & Chu Kỳ Kinh Doanh Trọn Vẹn

Trước khi bật phân luồng, bắt buộc chốt cứng bốn tham số thiết kế thống kê và ghi vào biên bản thử nghiệm:
- **Độ tin cậy mục tiêu (Confidence Level):** Mặc định thiết lập ở ngưỡng **`95%`** ($\alpha = 0.05$) để khống chế nguy cơ kết luận nhầm biến thể thắng cuộc do nhiễu ngẫu nhiên (dương tính giả).
- **Lực thống kê (Statistical Power):** Mặc định đạt tối thiểu **`80%`** ($1 - \beta = 0.80$) nhằm đảm bảo phép thử đủ độ nhạy phát hiện mức cải thiện thực sự khi nó tồn tại.
- **Ngưỡng chênh lệch tối thiểu cần phát hiện (MDE — Minimum Detectable Effect):** Xác định biên độ cải thiện tương đối nhỏ nhất đáng để triển khai (với cổng thông tin B2B lưu lượng vừa phải, ưu tiên thử nghiệm các thay đổi lớn có MDE kỳ vọng cao thay vì tinh chỉnh vi mô).
- **Chu kỳ tuần làm việc trọn vẹn (Full Business-Week Cycles):** Luôn duy trì phép thử tối thiểu **1 đến 2 chu kỳ nguyên tuần (7 hoặc 14 ngày trọn vẹn)** kể cả khi đủ cỡ mẫu sớm hơn, nhằm cân bằng sai khác hành vi giữa giờ hành chính đầu tuần của khối doanh nghiệp và thời điểm cuối tuần.

---

## 4. Hệ Thống Chỉ Số Ba Tầng (3-Tier Metric Hierarchy)

Mỗi thử nghiệm chỉ được chọn **duy nhất một chỉ số quyết định** để phân định thắng thua, đi kèm hai tầng chỉ số giám sát an toàn:

1. **Chỉ số chính (Primary Metric — Duy nhất 1):** Phản ánh trực tiếp hành động tạo giá trị thực chất (tỷ lệ gửi yêu cầu tư vấn hợp lệ, tỷ lệ tải bộ hồ sơ mẫu hoàn tất), không dùng chỉ số bề mặt dễ gây hiểu lầm như lượt nhấp chuột tò mò.
2. **Chỉ số bổ trợ (Secondary Metrics):** Giúp giải mã hành vi trung gian (độ sâu cuộn trang, thời gian đọc bảng thông số kỹ thuật, tỷ lệ chuyển bước giữa các phần biểu mẫu).
3. **Chỉ số rào chắn an toàn (Guardrail Metrics):** Các ngưỡng sức khỏe hệ thống không được phép suy thoái khi biến thể thắng cuộc — bao gồm tỷ lệ hồ sơ rác/sai đối tượng, tỷ lệ hủy yêu cầu sau tư vấn đầu tiên, độ trễ tải trang (Core Web Vitals) và tỷ lệ lỗi biểu mẫu.

---

## 5. Kỷ Luật Chống Nhìn Trộm Sớm & Chẩn Đoán Lệch Tỷ Lệ Mẫu (SRM)

- **Nghiêm cấm dừng sớm theo cảm tính (Anti-Peeking Discipline):** Việc kiểm tra bảng kết quả hằng ngày rồi tuyên bố thắng cuộc ngay khoảnh khắc chỉ số $p\text{-value}$ vừa chạm dưới `0.05` làm tỷ lệ kết luận giả tăng vọt. Chỉ đọc kết quả ra quyết định khi đã chạm đủ cỡ mẫu tính trước và hoàn tất trọn chu kỳ tuần làm việc (trừ khi sử dụng mô hình kiểm định tuần tự đã hiệu chỉnh biên dừng từ đầu).
- **Kiểm tra Lệch Tỷ Lệ Phân Phối Mẫu (SRM — Sample Ratio Mismatch):** Khi thiết kế chia lưu lượng `50% / 50%` nhưng số người dùng thực nhận lại lệch đáng kể (ví dụ `52.4% / 47.6%`, phép kiểm $\chi^2$ báo bất thường ở ngưỡng $p < 0.001$), chứng tỏ cơ chế phân luồng, bộ nhớ đệm CDN, điều hướng di động hoặc trình chặn kịch bản đã làm hỏng tính ngẫu nhiên. **Khi phát hiện SRM, bắt buộc hủy bỏ toàn bộ kết quả phép thử đó**, sửa lỗi kỹ thuật phân luồng rồi mới đo lại từ đầu.
- **Lưu trữ sổ cái học thuật:** Mọi phép thử (dù thắng, hòa hay thua) đều phải lưu lại giả thuyết gốc, ảnh chụp hai phiên bản, số liệu 3 tầng và bài học rút ra về tâm lý khách hàng để tái sử dụng cho các chiến dịch soạn thảo kế tiếp.
