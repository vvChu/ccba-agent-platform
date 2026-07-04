---
name: seminar-builder
description: Chuẩn bị nội dung seminar/training nội bộ CCBA. Tạo recap, agenda, outline, và archive nội dung các buổi thảo luận.
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_consulting"
---

# Seminar Content Builder

Skill hỗ trợ chuẩn bị nội dung cho các buổi Seminar/Thảo luận/Training nội bộ của CCBA.

## When to Use

- Cần **chuẩn bị nội dung** cho buổi seminar sắp tới
- Cần **tổng hợp recap** các buổi thảo luận trong tháng
- Cần **tạo agenda** cho buổi seminar
- Cần **thông báo thay đổi lịch** seminar
- Cần **archive** nội dung seminar đã diễn ra
- User nói: "chuẩn bị seminar", "tổng hợp tháng", "agenda seminar", "recap"

## Key Files

| File | Mô tả |
|------|--------|
| `templates/monthly_recap.md` | Template tổng hợp nội dung các buổi trong tháng |
| `templates/agenda.md` | Template chương trình/agenda seminar |
| `templates/notification.md` | Template thông báo lịch/thay đổi lịch |

## How to Use

### 1. Tạo Agenda Seminar

1. Hỏi user:
   - Ngày, giờ tổ chức
   - Chủ đề chính (1-3 topics)
   - Thời lượng dự kiến
   - Người trình bày (nếu có)
2. Đọc template `templates/agenda.md`
3. Tạo agenda với timeline cụ thể
4. Xuất Markdown + Word

### 2. Tạo Monthly Recap

1. Hỏi user đường dẫn đến tài liệu các buổi seminar trong tháng
2. Đọc các file seminar (PDF, PPTX → extract text nếu cần)
3. Tổng hợp theo template `templates/monthly_recap.md`:
   - Key takeaways từng buổi
   - Action items còn pending
   - Chủ đề cần follow-up
4. Xuất Markdown + Word

### 3. Thông báo thay đổi lịch

1. Đọc template `templates/notification.md`
2. Điền thông tin thay đổi (lịch cũ → mới, lý do)
3. Xuất format phù hợp để gửi qua Zalo/Email

### 4. Archive Seminar

Sau mỗi buổi seminar, lưu trữ tài liệu vào thư mục theo cấu trúc:
```
BIM_VBPL/
  YYYY/
    CCBA_RD_SEMINAR_NNN_RevXX-DD.MM.YY-Title.pdf
    CCBA_RD_SEMINAR_NNN_RevXX-DD.MM.YY-Title.pptx
```

Naming convention:
- `CCBA_RD_SEMINAR_` — prefix cố định
- `NNN` — số thứ tự (001, 002, 003...)
- `RevXX` — revision (Rev00, Rev01...)
- `DD.MM.YY` — ngày seminar
- `Title` — tên chủ đề (kebab-case)

## Source Documents

Tài liệu seminar lưu tại:
```
D:\OneDrive - IBST BIM\00 CCBA\03 PMO Documents\
  06 BIM RD and International Coo\
    04_ĐÀO_TẠO_NỘI_BỘ\04_Cập_nhật_kiến_thức\BIM_VBPL\
```

## Dependencies

- `python-docx` (cho xuất Word)
- Skill `legal-document-tracker` (cho nội dung VBPL liên quan)
- Skill `completion-checklist` (cho nội dung hồ sơ hoàn thành)
