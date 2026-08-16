---
name: workflow_pccc_cdt_tuthamdinh
description: Quy trình Hỗ trợ Chủ đầu tư Tự thẩm định toàn bộ thiết kế PCCC (theo Luật 55/2024 & NĐ 105/2025)
applies_to:
  - "Quản lý chất lượng"
  - "Thẩm tra thiết kế"
  - "PCCC"
bundle: "_qc"
disable-model-invocation: true
---
# Quy trình Tư vấn Hỗ trợ Chủ đầu tư Tự thẩm định toàn bộ thiết kế PCCC

Căn cứ điểm đ khoản 1 Điều 17 Luật PCCC số 55/2024/QH15 và khoản 1 Điều 8 Nghị định số 105/2025/NĐ-CP, đối với các công trình không thuộc thẩm quyền thẩm định của Cơ quan chuyên môn về xây dựng và Cơ quan Công an, **Chủ đầu tư / Chủ sở hữu công trình có trách nhiệm tự tổ chức thẩm định thiết kế về PCCC**.

Quy trình này hướng dẫn cách sử dụng CCBA AI Agent để hỗ trợ Chủ đầu tư thực hiện nhiệm vụ rà soát toàn diện và xuất Mẫu PC13 theo đúng quy định pháp luật.

## 1. Nội dung Tự thẩm định (Full Audit)

Chủ đầu tư phải tự chịu trách nhiệm trước pháp luật về việc thẩm định đầy đủ 07 nội dung (từ điểm a đến điểm g khoản 1 Điều 16 Luật 55/2024/QH15):
*   **Phần Kiến trúc & Thụ động:**
    *   [a] Khoảng cách phỏng cháy, chữa cháy.
    *   [b] Đường bộ, bãi đỗ xe, khoảng trống phục vụ PCCC.
    *   [c] Giải pháp thoát nạn.
    *   [d] Bậc chịu lửa, giải pháp ngăn cháy, chống cháy lan.
    *   [đ] Giải pháp chống khói.
*   **Phần Chủ động & Hệ thống điện:**
    *   [e] Hệ thống điện phục vụ phòng cháy và chữa cháy.
    *   [g] Phương tiện, hệ thống phòng cháy và chữa cháy.

## 2. Trình tự thực hiện bằng CCBA Semantic Audit Engine

Thay vì phải rà soát thủ công một lượng lớn bản vẽ Kiến trúc, Điện, Nước và Thuyết minh, Chủ đầu tư/Tư vấn QLDA áp dụng phương pháp Map-Reduce của CCBA:

**Bước 1: Chuẩn bị Hồ sơ (Data Ingestion)**
Tập hợp toàn bộ Thuyết minh tính toán, Bản vẽ Kiến trúc PCCC và Bản vẽ MEP PCCC vào một thư mục chung.

**Bước 2: Phân tách Gói Dữ Liệu (Map)**
*   Gói 1 (Legal & Specs): Thuyết minh tổng hợp + Quy chuẩn áp dụng.
*   Gói 2 (MEP Water): Mặt bằng bơm, bể nước, vách tường, Sprinkler + Thuyết minh.
*   Gói 3 (MEP Alarm vs Arch): Mặt bằng Kiến trúc + Báo cháy + Điện PCCC.

**Bước 3: Chạy Engine Đánh Giá (Reduce)**
*   Sử dụng Local LLM (qwen-local-primary) chạy tuần tự qua các Gói dữ liệu để so sánh chéo, phát hiện xung đột và lỗi sai thông số.
*   Cross-check tự động với cơ sở dữ liệu TCVN 3890:2023, TCVN 5738:2021, TCVN 7336:2021 và QCVN 06:2022/BXD.

**Bước 4: Trích xuất Báo cáo Thẩm định (PC13)**
*   Hệ thống tổng hợp các Findings (Lỗi) và xuất ra Báo cáo Đánh giá Chất lượng Hồ sơ.
*   Sử dụng kết quả này làm cơ sở để phát hành **Văn bản kết quả thẩm định thiết kế về phòng cháy, chữa cháy** (Mẫu số PC13 ban hành kèm theo Nghị định số 105/2025/NĐ-CP). Chủ đầu tư ký và lưu hồ sơ theo quy định.
