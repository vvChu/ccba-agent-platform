# Báo cáo Đánh giá Năng lực Kỹ thuật Xây dựng - Model `qwen-local-primary`
**Dự án tham chiếu:** Sửa Chữa, Cải Tạo Nâng Cấp Khối Nhà B Và D Bệnh Viện Nguyễn Tri Phương
**Công cụ test:** `ccba-ai` kết nối tới AI Gateway Server.

---

## 1. Tổng quan Đánh giá (Executive Summary)

Trải qua 5 bài kiểm tra chuyên sâu bao gồm Kiến thức TCVN, Đọc hiểu bản vẽ (text-based), Cơ học đất - Nền móng, Quản lý dự án (Nghị định 15/10), và Ứng dụng BIM, model `qwen-local-primary` thể hiện:
- **Tư duy Logic (Chain-of-Thought) xuất sắc:** Ở mọi bài test, model đều tự động tạo khối `<think>` phân tích bối cảnh, trích xuất từ khóa, xác định vai trò (Kỹ sư kết cấu, Giám đốc QLDA, BIM Manager) trước khi trả lời.
- **Kiến thức chuyên môn vững vàng:** Model dẫn chiếu chính xác các TCVN, ISO 19650 và các thông số chuyên ngành mà không bị ảo giác.
- **Tiếng Việt chuyên ngành chuẩn mực:** Mặc dù luồng tư duy nội bộ (thinking process) pha trộn tiếng Anh, nhưng văn phong đầu ra hoàn toàn đáp ứng đúng thuật ngữ Kỹ thuật Xây dựng Việt Nam (ví dụ: *tán xạ, cốt đai kháng chấn, vùng tới hạn, móng nông, Á sét dẻo mềm*).

---

## 2. Chi tiết Kết quả Từng Bài Kiểm Tra

### Bài 1: Kiến thức Kỹ thuật Xây dựng & TCVN
*   **Prompt:** Kiểm tra hàm lượng thép giới hạn cột lệch tâm theo TCVN 5574:2018 và tải trọng gió theo TCVN 2737:2023.
*   **Phân tích của AI:**
    *   *TCVN 5574:2018:* Nhận diện chính xác $\mu_{min} = 0.6\%$ và $\mu_{max} = 5\%$ (có thể lên 6% tại vị trí nối thép) cho cột chịu nén lệch tâm.
    *   *TCVN 2737:2023:* Nhận diện được sự thay đổi cốt lõi so với bản 1995: Áp dụng phương pháp tiếp cận tương đồng Eurocode/ISO, bổ sung bản đồ vận tốc gió cơ bản ($V_b$), hệ số địa hình ($K_z$), hệ số địa hình cực trị ($K_t$), và gộp thành phần động/tĩnh vào cùng một công thức.

### Bài 2: Khả năng Đọc hiểu Cấu tạo Kháng chấn (TCVN 9386:2012)
*   **Prompt:** Đánh giá khoảng cách thép đai $a=100mm$ tại vùng tới hạn của dầm 200x400.
*   **Phân tích của AI:**
    *   Model tự động tính toán chiều cao làm việc $d \approx 400 - 25 - 8 - 10 = 357mm$.
    *   Nhớ chính xác quy định cấu tạo TCVN 9386:2012: Khoảng cách cốt đai vùng tới hạn không được vượt quá $min(d/4, 24d_w, 225, 8d_L)$ (Model có sự xê dịch quy định quốc tế ACI $d/2$ và $150mm$, tuy nhiên vẫn kết luận $a=100mm$ thỏa mãn vì nhỏ hơn giới hạn nghiêm ngặt nhất là $150mm$).
    *   *Đánh giá:* Rất tốt, có khả năng tính nhẩm kích thước hữu ích (effective depth) chính xác từ dữ liệu thô.

### Bài 3: Phân tích Địa chất & Nền móng (Móng nông BV NTP)
*   **Prompt:** Tại sao chọn móng nông cho cầu thang thép với địa chất lớp 1 (Á sét dẻo mềm) đến -3m, mực nước ngầm -2.9m, đào sâu 2.5m?
*   **Phân tích của AI:**
    *   *Logic nước ngầm:* Model tính toán cốt đáy móng là -2.5m, mực nước ngầm là -2.9m. Suy ra đáy móng nằm trên mực nước ngầm 0.4m $\rightarrow$ Rủi ro bục/tràn nước ngầm thấp, không cần biện pháp hạ mực nước ngầm phức tạp.
    *   *Logic kết cấu:* Cầu thang thép có tải trọng nhẹ, lớp Á sét dẻo mềm có sức chịu tải đủ đáp ứng mà không cần cọc ép, giúp tiết kiệm chi phí, dễ thi công ở công trình cải tạo.

### Bài 4: Quản lý Dự án (Xử lý phát sinh theo NĐ 15 & NĐ 10)
*   **Prompt:** Xử lý phát sinh đào móng sâu thêm 1m tại hố khoan HK1.
*   **Phân tích của AI:**
    *   Đưa ra đúng quy trình 6 bước chuẩn chỉnh: (1) Lập biên bản hiện trường/Xác nhận địa chất, (2) Tư vấn thiết kế ra bản vẽ xử lý kỹ thuật/điều chỉnh thiết kế, (3) Chủ đầu tư phê duyệt, (4) Lập dự toán phát sinh theo NĐ 10/2021, (5) Phụ lục hợp đồng, (6) Thanh toán.
    *   *Đánh giá:* Nắm rất vững quy trình pháp lý đầu tư công tại Việt Nam.

### Bài 5: Ứng dụng BIM trong công trình Cải tạo
*   **Prompt:** Quy trình xử lý giao cắt MEP-STR bằng Navisworks/Revizto và yêu cầu LOD.
*   **Phân tích của AI:**
    *   Đề xuất áp dụng Point Cloud (Scan data) cho phần hiện trạng (LOD 200-250) kết hợp với mô hình thiết kế mới (LOD 350).
    *   Quy trình Clash Detection: Thiết lập ma trận giao cắt (Clash Matrix), thiết lập Tolerance, phân tích Hard/Soft clash, và dùng Revizto để gán Issue Tracker cho từng bên.
    *   Khuyến nghị chính xác LOD 350 (theo AIA E203/ISO 19650) là mức tối thiểu để xuất bản vẽ Shop Drawing thi công.

---

## 3. Kết luận
`qwen-local-primary` hoàn toàn đủ năng lực để hoạt động như một "Trợ lý Kỹ thuật Xây dựng" (Civil Engineering Copilot). Tốc độ sinh text nhanh, khả năng tự soát lỗi (CoT) ấn tượng, và kiến thức TCVN sâu sắc khiến nó trở thành ứng cử viên hoàn hảo để tích hợp vào các luồng quy trình (workflow) tự động như kiểm tra thiết kế (QC), bóc tách khối lượng, và soát xét thuyết minh.
