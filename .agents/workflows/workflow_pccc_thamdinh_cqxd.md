---
name: workflow_pccc_thamdinh_cqxd
description: Quy trình Thẩm định/Thẩm tra PCCC phần Kiến trúc & Kiểm soát khói nộp Cơ quan chuyên môn về xây dựng (theo Luật 55/2024 & NĐ 105/2025)
applies_to:
  - "Quản lý chất lượng"
  - "Thẩm tra thiết kế"
  - "PCCC"
bundle: "_qc"
disable-model-invocation: true
---
# Quy trình Thẩm định/Thẩm tra PCCC phần Kiến trúc & Kiểm soát khói (CQCMVXD)

Quy trình này áp dụng cơ chế lồng ghép thẩm định thiết kế xây dựng và thẩm định thiết kế PCCC theo quy định tại Điều 16, Điều 17 Luật PCCC số 55/2024/QH15 và Nghị định số 105/2025/NĐ-CP. Việc thẩm định do Cơ quan chuyên môn về xây dựng (CQCMVXD) chủ trì, có thể có sự tham gia của Tổ chức Tư vấn Thẩm tra độc lập (như CCBA).

## 1. Thẩm quyền và Nội dung thẩm định (Phần Kiến trúc - Thụ động)

Căn cứ vào điểm a, b, c, d, đ khoản 1 Điều 16 Luật 55/2024/QH15, nội dung thẩm định bao gồm:
*   **[a] Khoảng cách an toàn PCCC:** Khoảng cách giữa các công trình, hạng mục công trình, đường ranh giới khu đất.
*   **[b] Giao thông & Bãi đỗ xe:** Đường bộ, bãi đỗ xe cứu hỏa, vị trí và lối tiếp cận phục vụ chữa cháy.
*   **[c] Lối thoát nạn:** Hành lang, đường thoát nạn, thang bộ, thang máy chữa cháy, lối ra khẩn cấp, gian lánh nạn.
*   **[d] Bậc chịu lửa & Ngăn cháy lan:** Giới hạn chịu lửa cấu kiện, giải pháp phân chia khoang cháy, bố trí mặt bằng công năng, chèn bịt chống cháy (Firestopping).
*   **[đ] Kiểm soát khói:** Phương án thoát khói (tự nhiên/cơ học), cấp khí bảo vệ (tăng áp) buồng thang bộ, giếng thang máy.

## 2. Danh mục Hồ sơ trình Thẩm định

Để đáp ứng quy định kiểm tra, Hồ sơ Thiết kế cần chuẩn bị:
1.  **Tổng mặt bằng công trình:** Thể hiện rõ khoảng cách, đường giao thông, bãi đỗ xe PCCC.
2.  **Mặt bằng Kiến trúc PCCC các tầng:** Thể hiện lối thoát nạn, phân chia khoang cháy, cửa chống cháy.
3.  **Chi tiết cấu tạo:** Thang thoát nạn, thang máy PCCC, vách/trần chịu lửa, chèn bịt kỹ thuật.
4.  **Bản vẽ Hệ thống thông gió:** Mặt bằng/sơ đồ nguyên lý tăng áp buồng thang, hút khói hành lang/tầng hầm.
5.  **Thuyết minh tính toán:**
    *   Bảng thống kê giới hạn chịu lửa cấu kiện (REI/EI).
    *   Bảng tính toán thoát nạn (chiều rộng cửa, chiều dài quãng đường).
    *   Thuyết minh tính toán hệ thống kiểm soát khói.

## 3. Trình tự thực hiện (Dành cho Agent/Kỹ sư)

Sử dụng CCBA Agent Platform để chạy kiểm tra (Audit) trước khi nộp hồ sơ:

1.  **Thu thập dữ liệu:** Trích xuất toàn bộ Thuyết minh PCCC và Bản vẽ Kiến trúc/Thông gió HVAC sang định dạng Markdown.
2.  **Kích hoạt AI Audit:** Gọi lệnh chạy module Semantic Map-Reduce Audit cho "Package 1: Legal & Architecture".
3.  **Cross-check Pháp lý:**
    *   Đối chiếu số liệu với QCVN 06:2022/BXD.
    *   Kiểm tra tính nhất quán giữa Bản vẽ mặt bằng và Thuyết minh.
4.  **Xuất báo cáo:** Chuyển kết quả Audit thành Phụ lục Báo cáo Thẩm tra Thiết kế, đóng dấu tư vấn và đệ trình lên Cơ quan chuyên môn về xây dựng cùng hồ sơ TKXD triển khai sau TKCS.
