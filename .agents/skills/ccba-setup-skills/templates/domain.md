# Tài liệu Miền Tri Thức (Domain Docs)

Cách các công cụ kỹ thuật tiêu thụ tài liệu nghiệp vụ/miền tri thức của dự án khi khảo sát codebase.

## Các tài liệu cần đọc trước khi khảo sát

- **`CONTEXT.md`** tại thư mục gốc dự án (hoặc tại `.md/knowledge/CONTEXT.md` nếu được di chuyển vào thư mục tri thức).
- **`CONTEXT-MAP.md`** tại thư mục gốc (hoặc tại `.md/knowledge/CONTEXT-MAP.md`) nếu dự án có nhiều miền tri thức con — file này sẽ chỉ đường dẫn cụ thể đến từng file `CONTEXT.md` của từng bộ môn/module. Đọc các file liên quan đến nghiệp vụ cần làm việc.
- **`docs/adr/`** — Đọc các tài liệu Quyết định Kiến trúc (ADRs) liên quan đến phần tính năng chuẩn bị code. Đối với monorepo/multi-context, kiểm tra thêm thư mục ADRs cục bộ của từng module con (ví dụ: `src/<context>/docs/adr/` hoặc `packages/<package>/docs/adr/`).

Nếu các tệp tin này không tồn tại, **tiến hành một cách âm thầm**. Không báo lỗi, không tự ý đề xuất tạo mới chúng trước khi bắt đầu. Kỹ năng `/ccba-grilling` hoặc `/ccba-codebase-design` sẽ kích hoạt việc tạo mới một cách lười biếng (lazy) khi các thuật ngữ hoặc quyết định kiến trúc thực sự được giải quyết.

## Bố cục file mẫu

Dự án Đơn miền tri thức (Single-context):
```
/
├── CONTEXT.md                    ← Định nghĩa thuật ngữ & nghiệp vụ chung
├── docs/
│   └── adr/                      ← Chứa các quyết định kiến trúc chuẩn
│       ├── 0001-setup-db.md
│       └── 0002-use-jwt.md
└── src/
```

Dự án Đa miền tri thức (Multi-context):
```
/
├── CONTEXT-MAP.md                ← Bản đồ định tuyến các miền tri thức
├── docs/
│   └── adr/                      ← Các quyết định kiến trúc toàn hệ thống
└── packages/ (hoặc src/)
    ├── ordering/
    │   ├── CONTEXT.md            ← Tri thức nghiệp vụ module Đặt hàng
    │   └── docs/adr/             ← Quyết định kiến trúc của module Đặt hàng
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

## Sử dụng đúng từ vựng trong Glossary

Khi xuất tài liệu, viết code, đặt tên biến, comment, đặt tên test case, hoặc viết Issue, bắt buộc phải dùng chính xác thuật ngữ đã được định nghĩa trong `CONTEXT.md`. Tuyệt đối không dùng các từ đồng nghĩa khác ngoài Glossary để tránh nhầm lẫn nghiệp vụ.

Nếu khái niệm bạn cần chưa có trong Glossary, đó là dấu hiệu: Hoặc bạn đang tự chế ra ngôn ngữ mà dự án không sử dụng, hoặc đang có lỗ hổng tri thức cần cập nhật (hãy ghi chú lại để chạy `/ccba-grilling`).

## Cảnh báo xung đột ADR

Nếu đề xuất kỹ thuật của bạn đi ngược lại với một quyết định kiến trúc đã thống nhất trong ADR, bạn phải nêu rõ cảnh báo trong báo cáo/kế hoạch:
> **⚠️ Xung đột với ADR-0007 (Mô hình Event-Sourced cho Đặt hàng)**: Đề xuất này sử dụng ghi đè trực tiếp trạng thái, cần mở lại thảo luận vì lý do...

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
