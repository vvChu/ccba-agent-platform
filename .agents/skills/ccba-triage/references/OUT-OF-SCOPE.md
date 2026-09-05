# Quản lý Cơ sở Tri thức Tính năng ngoài Phạm vi (.out-of-scope/)

Thư mục `.out-of-scope/` (hoặc thư mục tương đương cục bộ tại `.md/knowledge/out-of-scope/` khi chạy offline) lưu trữ hồ sơ của các yêu cầu tính năng đã bị từ chối chính thức (nhãn `wontfix`). **Lưu ý**: Đảm bảo tạo thư mục này nếu nó chưa tồn tại để quy trình có thể thực thi ngay lập tức.

## Cấu trúc thư mục (Directory Structure)

Mỗi file trong thư mục đại diện cho một **Khái niệm (Concept)** bị từ chối, không tạo file riêng cho từng issue lẻ:
```
.out-of-scope/
├── dark-mode.md
├── plugin-system.md
└── graphql-api.md
```

---

## Định dạng tài liệu chuẩn (File Format)

```markdown
# [Tên Khái niệm - Ví dụ: Giao diện tối]

Quyết định chính thức: Dự án này không hỗ trợ hiển thị giao diện tối (Dark Mode).

## Lý do từ chối (Why this is out of scope)

[Trình bày chi tiết lý do kỹ thuật hoặc định hướng phát triển của dự án. Không ghi các lý do tạm thời như "thiếu nhân lực", mà tập trung vào kiến trúc hệ thống và triết lý sản phẩm]

## Danh sách các yêu cầu cũ (Prior requests)

- #42 — "Thêm tùy chọn nền tối"
- #87 — "Hỗ trợ night theme cho accessibility"
```

---

## Luồng vận hành (Workflow)

1. **Khi đối soát đầu vào:**
   - Đọc qua toàn bộ các tệp tin trong `.out-of-scope/`. Đối chiếu sự cố/PR mới xem có trùng khớp khái niệm đã từ chối hay không.
   - Nếu phát hiện trùng khớp, báo cáo Maintainer kèm lý do lịch sử trước khi xử lý tiếp.

2. **Khi đóng ticket dạng wontfix:**
   - Nếu là yêu cầu nâng cấp (`enhancement`) bị từ chối: kiểm tra tệp khái niệm tương ứng trong `.out-of-scope/` đã tồn tại chưa.
   - Nếu đã có: bổ sung mã định danh của issue mới vào danh sách `Prior requests`.
   - Nếu chưa có: tạo mới tệp Markdown đặt tên theo dạng `kebab-case.md` mô tả rõ ràng lý do từ chối.
   - Không áp dụng cho sự cố lỗi (`bug`) hoặc các tính năng **đã được triển khai**.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
