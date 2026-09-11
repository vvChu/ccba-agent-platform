---
name: ccba-seminar-builder
description: Chuẩn bị nội dung seminar/training nội bộ CCBA. Tạo recap, agenda, outline,
  và archive nội dung các buổi thảo luận.
applies_to:
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _consulting
tier: kernel
metadata:
  author: CCBA
  version: 1.1.0
user-invocable: true
command: /ccba-seminar-builder
gpi:
  s: 3.0
  k: 2.0
  a: 4.0
  p: 1.0
triggers:
- seminar
- đào tạo
- training
- recap
- agenda
- buổi thảo luận
- ccba-teach
- teach
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

### Bước 1: Tạo Agenda & Outline Seminar
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

### Bước 2: Xuất Bản Slide Thuyết Trình PowerPoint (.pptx) Tự Động
Từ bản thảo Outline/Agenda Markdown đã duyệt, tự động biên dịch sang tệp trình chiếu PowerPoint chuẩn nhận diện thương hiệu CCBA ver 3.4 kết hợp phong cách **Swiss Minimalist & Storytelling With You** (Cole Nussbaumer Knaflic) qua Deep Seam `ccba_ooxml.pptx`:

```bash
python -m ccba_ooxml build-deck path/to/outline.md --output path/to/seminar.pptx --aspect-ratio 16:9
```
Hoặc gọi trực tiếp trong Python:
```python
from ccba_ooxml import build_presentation_from_markdown

build_presentation_from_markdown("outline.md", "seminar.pptx")
```
- **Hỗ trợ đầy đủ các Archetypes Bố Cục Đỉnh Cao**:
  - **Cover Hero Slide**: Eyebrow Capsule `[TRUNG TÂM CCBA — VIỆN IBST]`, Tiêu đề Display 34pt, thanh 3 màu và Logo IBST BIM độ nét cao.
  - **The Big Idea (`::: big-idea`)**: Khẩu hiệu chiến lược kèm 3 thẻ cột trụ (Bối cảnh, Rủi ro, Hành động).
  - **Visual Agenda (`::: agenda active=N`)**: Lộ trình 4 chặng tự động highlight phần đang nói kèm badge Navy `ĐANG TRÌNH BÀY`.
  - **Horizontal Process Stepper (`::: steps`)**: Quy trình 4 bước ngang `01` $\rightarrow$ `02` $\rightarrow$ `03` $\rightarrow$ `04` trực quan.
  - **Split 60/40 Comparison (`::: split`)**: Cột trái bối cảnh cũ 38% (`#F8FAFC`) vs Cột phải CCBA WAY đột phá 58% (viền Cyan `#0093DD`).
  - **Swiss Clean Table + Hero KPI Cards**: 3 Thẻ số liệu lớn đặt trên bảng dữ liệu không viền dọc.
  - **Asymmetric Bento Grid (`> [!ARCH]`, `> [!STRUCT]`, `> [!MEP]`)**: Thẻ Hero 54% bên trái + 2 Thẻ phụ 43% xếp chồng bên phải.
  - **Field Evidence Quote (`::: quote`)**: Thẻ trích dẫn lời chứng thực thực tế từ Chủ đầu tư / Ban QLDA.

**Tiêu chí hoàn thành:** Slide PowerPoint (.pptx) được biên dịch thành công từ outline markdown.

### Bước 3: Tạo Monthly Recap
1. Hỏi user đường dẫn đến tài liệu các buổi seminar trong tháng.
2. Đọc các file seminar (PDF, PPTX).
3. Tổng hợp theo template `templates/monthly_recap.md` để ghi nhận các Key takeaways, Action items và các chủ đề cần follow-up.
4. **Tiêu chí hoàn thành:** Hoàn thiện bản tóm tắt tháng lưu trữ dạng Markdown tại thư mục quy định.

### Bước 4: Thông báo thay đổi lịch
1. Đọc template `templates/notification.md`.
2. Điền thông tin thay đổi (lịch cũ → mới, lý do).
3. **Tiêu chí hoàn thành:** Xuất thông báo dạng văn bản hành chính hoàn chỉnh để gửi qua Zalo/Email.

### Bước 5: Archive Seminar
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


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/interactive_teaching.md` | Mẫu hình giảng dạy tương tác trong các buổi seminar và đào tạo nội bộ |

