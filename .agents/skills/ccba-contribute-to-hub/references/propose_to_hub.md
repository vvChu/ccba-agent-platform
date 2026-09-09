# ccba-propose-to-hub — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Quy trình đề xuất kỹ năng/tính năng mới từ Spoke lên Hub trung tâm
> **Mô tả gốc:** [Alias tương thích ngược của /ccba-contribute-to-hub] Đóng gói mã nguồn, tests, proposal từ Spoke và mở PR lên Hub

---

# Workflow: Propose to Hub (Alias -> /ccba-contribute-to-hub)

> [!NOTE]
> **Định tuyến chuẩn hóa:** Kỹ năng này là Alias tương thích ngược (Backward Compatibility) của [`/ccba-contribute-to-hub`](../ccba-contribute-to-hub/SKILL.md).
> - Để đề xuất **Ý tưởng / RFC / Báo lỗi**, sử dụng: [`/ccba-issue-to-hub`](../ccba-issue-to-hub/SKILL.md).
> - Để đóng gói **Mã nguồn / Tests / Mở PR**, sử dụng: [`/ccba-contribute-to-hub`](../ccba-contribute-to-hub/SKILL.md).

---

## Quy Trình Thực Thi:
Vui lòng tham khảo chi tiết toàn bộ các bước tại [`ccba-contribute-to-hub`](../ccba-contribute-to-hub/SKILL.md):
1. **Bước 1:** Thu thập thông tin & Mã nguồn đóng gói.
   - **Tiêu chí hoàn thành:** Thu thập đầy đủ thông tin và mã nguồn cần đóng gói theo hướng dẫn của ccba-contribute-to-hub.
2. **Bước 2:** Kiểm tra trùng lặp trên Hub (`catalog.yaml`, `packages/`).
   - **Tiêu chí hoàn thành:** Xác nhận không trùng lặp công cụ hiện có trên Hub catalog.
3. **Bước 3:** Đóng gói mã nguồn & Tạo file proposal chuẩn ADR-0045 trên branch mới.
   - **Tiêu chí hoàn thành:** Tệp proposal được tạo trên nhánh mới tuân thủ đúng ADR 0045.
4. **Bước 4:** Mở GitHub Pull Request (`gh pr create`).
   - **Tiêu chí hoàn thành:** PR được mở thành công trên repository Hub.
5. **Bước 5:** Vòng lặp dừng chờ bất đồng bộ & Tự làm xanh CI (Self-Healing Loop).
   - **Tiêu chí hoàn thành:** Toàn bộ checks CI vượt qua thành công mà không có lỗi.
6. **Bước 6:** Báo cáo hoàn tất & Sẵn sàng cho Maintainer thẩm định (`/ccba-review-proposal`).
   - **Tiêu chí hoàn thành:** Báo cáo hoàn tất quy trình đóng góp và sẵn sàng bàn giao thẩm định.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
