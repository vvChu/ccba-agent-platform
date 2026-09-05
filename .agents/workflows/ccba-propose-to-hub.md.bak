---
name: propose-to-hub
description: '[Alias tương thích ngược của /ccba-contribute-to-hub] Đóng gói mã nguồn, tests, proposal từ Spoke và mở PR lên Hub'
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
disable-model-invocation: true
command: /ccba-propose-to-hub
triggers:
- đề xuất
- tích hợp Hub
- contribution
- propose
- skill mới
---
# Workflow: Propose to Hub (Alias -> /ccba-contribute-to-hub)

> [!NOTE]
> **Định tuyến chuẩn hóa:** Workflow này là Alias tương thích ngược (Backward Compatibility) của [`/ccba-contribute-to-hub`](ccba-contribute-to-hub.md).
> - Để đề xuất **Ý tưởng / RFC / Báo lỗi**, sử dụng: [`/ccba-issue-to-hub`](ccba-issue-to-hub.md).
> - Để đóng gói **Mã nguồn / Tests / Mở PR**, sử dụng: [`/ccba-contribute-to-hub`](ccba-contribute-to-hub.md).

---

## Quy Trình Thực Thi:
Vui lòng tham khảo chi tiết toàn bộ các bước tại [`.agents/workflows/ccba-contribute-to-hub.md`](ccba-contribute-to-hub.md):
1. **Bước 1:** Thu thập thông tin & Mã nguồn đóng gói.
2. **Bước 2:** Kiểm tra trùng lặp trên Hub (`catalog.yaml`, `packages/`).
3. **Bước 3:** Đóng gói mã nguồn & Tạo file proposal chuẩn ADR-0045 trên branch mới.
4. **Bước 4:** Mở GitHub Pull Request (`gh pr create`).
5. **Bước 5:** Vòng lặp dừng chờ bất đồng bộ & Tự làm xanh CI (Self-Healing Loop).
6. **Bước 6:** Báo cáo hoàn tất & Sẵn sàng cho Maintainer thẩm định (`/ccba-review-proposal`).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
