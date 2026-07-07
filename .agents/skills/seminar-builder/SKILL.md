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

## Quy trình Thực hiện (Process)

### 1. Tạo Agenda & Outline Seminar
1. Hỏi user các thông tin cơ bản: Ngày giờ tổ chức, chủ đề chính, thời lượng dự kiến, người trình bày.
2. Đọc tệp template `templates/agenda.md` để đảm bảo áp dụng đúng khung cấu trúc chuẩn của CCBA.
3. Thiết lập cấu trúc tri thức theo nguyên tắc **Neo giữ Khái niệm (Concept Grounding)**:
   - Xác định rõ phần **Khái niệm tiền đề (Prerequisites)**: Kiến thức/tiêu chuẩn người nghe cần biết trước.
   - Sắp xếp Outline chương trình sao cho các **Khái niệm giới thiệu mới (Introduced Concepts)** được trình bày tuần tự từ cơ bản đến nâng cao. Chủ đề nâng cao chỉ được thảo luận sau khi các chủ đề nền móng đã được neo giữ.
4. Áp dụng **Lựa chọn Định dạng (Format Selection)** để thiết lập cấu trúc Agenda:
   - Dựng bảng biểu (Table) cho timeline thời gian cụ thể của buổi Seminar.
   - Sử dụng văn xuôi lập luận (Prose) cho phần tóm tắt lý do lựa chọn chủ đề.
   - Sử dụng các callouts (`> [!IMPORTANT]`) cho các lưu ý đặc thù về công tác chuẩn bị.
5. **Tiêu chí hoàn thành:** Bản thảo Agenda hiển thị rõ ràng phần Prerequisites, Introduced Concepts và bảng timeline chi tiết trình người dùng duyệt trước khi xuất bản file chính thức.

### 2. Tạo Monthly Recap
1. Hỏi user đường dẫn đến tài liệu các buổi seminar trong tháng.
2. Đọc các file seminar (PDF, PPTX).
3. Tổng hợp theo template `templates/monthly_recap.md` để ghi nhận các Key takeaways, Action items và các chủ đề cần follow-up.
4. **Tiêu chí hoàn thành:** Hoàn thiện bản tóm tắt tháng lưu trữ dạng Markdown tại thư mục quy định.

### 3. Thông báo thay đổi lịch
1. Đọc template `templates/notification.md`.
2. Điền thông tin thay đổi (lịch cũ → mới, lý do).
3. **Tiêu chí hoàn thành:** Xuất thông báo dạng văn bản hành chính hoàn chỉnh để gửi qua Zalo/Email.

### 4. Archive Seminar
1. Sau mỗi buổi seminar, lưu trữ tài liệu vào thư mục theo cấu trúc:
   ```
   .md/seminars/
     YYYY/
       CCBA_RD_SEMINAR_NNN_RevXX-DD.MM.YY-Title.pdf
       CCBA_RD_SEMINAR_NNN_RevXX-DD.MM.YY-Title.pptx
   ```
2. Đảm bảo naming convention: `CCBA_RD_SEMINAR_NNN_RevXX-DD.MM.YY-Title.ext`.
3. **Tiêu chí hoàn thành:** Tệp tài liệu được lưu trữ chính xác vào đúng thư mục phân loại và được cập nhật/đăng ký vào danh mục các buổi thảo luận (trường `seminars:`) tại tệp tin registry [.md/data/legal_registry.yaml](../../../.md/data/legal_registry.yaml).

## Source Documents

Tài liệu seminar lưu tại: `.md/seminars/` (tuyệt đối không lưu rải rác ngoài Project Root).
