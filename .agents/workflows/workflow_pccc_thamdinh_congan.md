---
name: workflow_pccc_thamdinh_congan
description: Quy trình Thẩm định thiết kế PCCC phần Hệ thống Cơ điện (MEP) nộp Cơ quan Công an (PC07)
applies_to:
  - "Quản lý chất lượng"
  - "Thẩm tra thiết kế"
  - "PCCC"
bundle: "_qc"
disable-model-invocation: true
---
# Quy trình Thẩm định thiết kế PCCC phần Hệ thống MEP (Cơ quan Công an)

Căn cứ theo điểm c khoản 1 Điều 17 Luật PCCC số 55/2024/QH15 và Nghị định số 105/2025/NĐ-CP, Cơ quan Công an (Cục/Phòng Cảnh sát PCCC - PC07) thực hiện thẩm định chuyên biệt đối với phần Hệ thống chủ động và Hệ thống điện PCCC.

## 1. Thẩm quyền và Nội dung thẩm định (Phần Cơ điện - Chủ động)

Nội dung do Cơ quan Công an thẩm định tập trung vào điểm e, g khoản 1 Điều 16 Luật 55/2024/QH15:
*   **[e] Hệ thống điện PCCC:** Hệ thống cáp cấp nguồn cho bơm chữa cháy, quạt hút khói/tăng áp, thang máy chữa cháy, chiếu sáng sự cố, tiếp địa.
*   **[g] Phương tiện & Hệ thống báo/chữa cháy:**
    *   Hệ thống báo cháy tự động (khói, nhiệt, chuông, còi, tủ trung tâm).
    *   Hệ thống chữa cháy (vách tường, Sprinkler tự động, màng ngăn Drencher, khí/bọt).
    *   Phương tiện chữa cháy xách tay (bình chữa cháy).

## 2. Danh mục Hồ sơ trình Thẩm định

Để nộp Cơ quan Công an thẩm định (Mẫu PC11 theo NĐ 105/2025), hồ sơ thiết kế MEP cần bao gồm:
1.  **Hệ thống Báo cháy:**
    *   Sơ đồ nguyên lý toàn hệ thống.
    *   Mặt bằng bố trí đầu báo, nút nhấn, còi đèn, dây cáp từng tầng.
    *   Chi tiết lắp đặt thiết bị.
2.  **Hệ thống Chữa cháy:**
    *   Sơ đồ không gian (Isometric) / Sơ đồ nguyên lý cấp nước chữa cháy.
    *   Mặt bằng bố trí đầu phun Sprinkler, họng nước vách tường, bình chữa cháy.
    *   Chi tiết trạm bơm chữa cháy (bố trí bơm, tủ điện, ống hút/đẩy, dung tích bể ngầm).
3.  **Hệ thống Điện PCCC:**
    *   Sơ đồ nguyên lý cấp nguồn riêng biệt cho tải PCCC.
    *   Chi tiết cáp chống cháy (FR), tuyến cáp đi an toàn.
4.  **Thuyết minh tính toán:**
    *   Thuyết minh tính toán thủy lực mạng lưới cấp nước PCCC.
    *   Tính toán dung lượng ắc quy dự phòng cho tủ trung tâm báo cháy.

## 3. Trình tự thực hiện (Dành cho Agent/Kỹ sư)

Sử dụng CCBA Agent Platform để audit lỗi thiết kế MEP trước khi nộp PC07:

1.  **Thu thập dữ liệu MEP:** Chuyển đổi Thuyết minh MEP PCCC và Bản vẽ MEP PCCC sang Markdown/Vector.
2.  **Kích hoạt AI Audit:** Gọi module Semantic Map-Reduce Audit cho:
    *   "Package 2: MEP Water vs Specs" (Đồng bộ số liệu bơm, bể nước).
    *   "Package 3: MEP Alarm vs Arch" (Đồng bộ vị trí báo cháy, vùng phủ, trần giả).
3.  **Kiểm soát rủi ro điển hình (Common Pitfalls):**
    *   Kiểm tra sự lệch pha giữa Thuyết minh (vd: tính toán 45m3) và Bản vẽ (vd: bể 54m3).
    *   Đảm bảo việc trích dẫn đúng quy chuẩn cấp điện (QCVN 12:2014/BXD).
4.  **Hoàn thiện:** Sửa lỗi thiết kế và in Hồ sơ xin Thẩm duyệt thiết kế PCCC nộp Cơ quan Công an.
