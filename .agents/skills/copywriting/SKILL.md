---
name: copywriting
description: Kỹ năng tạo văn bản theo mẫu chuẩn đã thống nhất, kế thừa trực tiếp nguồn dữ liệu biểu mẫu (templates) được chuẩn hóa và sinh ra từ quy trình nghiên cứu tài liệu hiện trạng (/ccba-extract-style). Tích hợp các công thức viết thuyết phục (AIDA, PAS) để hoàn thiện nội dung.
argument-hint: "[loại-văn-bản-theo-mẫu] [ngữ-cảnh]"
license: MIT
metadata:
  author: claudekit
  version: "1.0.0"
---

# Kỹ năng Soạn thảo Văn bản theo Mẫu chuẩn (Copywriting from Standardized Templates)

Kỹ năng này chịu trách nhiệm **tạo văn bản mới (hồ sơ đề xuất thầu, quyết định, công văn, hợp đồng, tờ trình...) theo mẫu chuẩn đã thống nhất**. Nguồn dữ liệu biểu mẫu đầu vào của kỹ năng này bắt buộc phải kế thừa trực tiếp từ các tệp template do quy trình nghiên cứu tài liệu hiện trạng [/ccba-extract-style](../../workflows/ccba-extract-style.md) tạo ra và lưu trữ tại thư mục `templates/`.

## Khi nào sử dụng

- Tạo hồ sơ đề xuất thầu, hồ sơ năng lực mới từ các biểu mẫu thầu đã được chuẩn hóa.
- Soạn thảo quyết định hành chính, tờ trình, công văn, thông báo từ các biểu mẫu hành chính công sở đã thống nhất cấu trúc.
- Soạn thảo hợp đồng, biên bản thỏa thuận thương mại dựa trên các biểu mẫu hợp đồng tiêu chuẩn.
- Hoàn thiện nội dung thuyết phục cho các biểu mẫu trên bằng cách áp dụng các công thức viết (AIDA, PAS, BAB).

## Luồng dữ liệu (Data Flow) & Nguyên tắc Vận hành

```
   [Tài liệu hiện hữu]
          │
          ▼
┌───────────────────┐
│/ccba-extract-style│  (Nghiên cứu tài liệu thô & Tạo mẫu chuẩn)
└─────────┬─────────┘
          │
          ▼ (Lưu tệp mẫu chuẩn hóa)
┌───────────────────┐
│copywriting/      │  (Nạp template sạch & điền thông tin dự án mới)
│templates/         │
└─────────┬─────────┘
          │
          ▼ (Áp dụng công thức viết thuyết phục)
┌───────────────────┐
│/ccba-copywriting  │  (Tạo văn bản hoàn chỉnh)
└───────────────────┘
```

## Quy trình Sinh tài liệu của Agent

1. **Nạp biểu mẫu mẫu**:
   - Khi nhận yêu cầu soạn thảo từ người dùng, Agent **bắt buộc** phải đọc thư mục `templates/` để tìm tệp biểu mẫu tương ứng (ví dụ: `quyet_dinh_bo_nhiem_template.md` hoặc `de_xuat_thau_template.md`).
   - Tuyệt đối không tự suy đoán cấu trúc văn bản hoặc tự tạo khung biểu mẫu nếu chưa có tệp template tương ứng được sinh từ quy trình nghiên cứu `/ccba-extract-style`.
2. **Điền thông tin và Viết nội dung**:
   - Agent phân tích các placeholders dạng `{{placeholder}}` trong tệp template và thu thập thông tin dự án/hành chính mới để điền vào.
   - Áp dụng các công thức viết thuyết phục (xem tại `references/copy-formulas.md`) để làm giàu nội dung chi tiết cho các phần trong biểu mẫu, đảm bảo giữ nguyên cấu trúc chuẩn hóa.

## Các Công thức Viết Thuyết phục Hỗ trợ

Tài liệu chi tiết: `references/copy-formulas.md`

- **AIDA**: Attention (Thu hút) → Interest (Thích thú) → Desire (Khao khát) → Action (Hành động) (Phù hợp cho hồ sơ đề xuất, giới thiệu giải pháp).
- **PAS**: Problem (Vấn đề) → Agitate (Khơi sâu nỗi đau) → Solution (Giải pháp) (Phù hợp cho tờ trình giải quyết sự cố, đề xuất kỹ thuật).
- **BAB**: Before (Trước kia) → After (Sau này) → Bridge (Cầu nối) (Phù hợp cho các báo cáo đánh giá tác động, case study).

## Tiêu chuẩn Thực thi của Agent (Best Practices)

1. **Tuân thủ Tuyệt đối Biểu mẫu mẫu**: Không được thay đổi Quốc hiệu, tiêu ngữ, hoặc cấu trúc khung pháp lý/hành chính của biểu mẫu đã được thống nhất. Chỉ hoàn thiện nội dung bên trong các phần nội dung và placeholders.
2. **Kế thừa Văn phong đã Phân tích**: Sử dụng các đặc tả văn phong lưu tại `assets/writing-styles/` để viết nội dung điền vào biểu mẫu, đảm bảo tính đồng nhất về tông giọng của CCBA.
3. **Trình bày nhiều biến thể**: Đối với các phần nội dung thuyết phục, hãy cung cấp tối thiểu 2 phương án viết để người dùng lựa chọn trước khi xuất file.
