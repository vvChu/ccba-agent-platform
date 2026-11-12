# Canonical Concept Note v8.3 — Cẩm Nang Quy Chuẩn Tri Thức Nguyên Tử

Tài liệu này định nghĩa cấu trúc chuẩn hóa cho mọi Concept Note được trích xuất từ sách trong hệ thống VvC Second Brain và CCBA Platform.

---

## 1. Cấu Trúc Bắt Buộc 6 Thành Phần (Canonical v8.3 Body Order)

Mỗi file concept note (`04 - Permanent/concepts/snake_case_concept_name.md`) bắt buộc tuân thủ thứ tự sau:

```markdown
---
title: "Tên khái niệm nguyên tử"
aliases:
  - "Tên gọi khác 1"
  - "Tên tiếng Anh (nếu có)"
tags:
  - knowledge
  - domain/<lĩnh_vực>
  - type/concept
type: concept
origin: book
date_created: YYYY-MM-DD
date_modified: YYYY-MM-DD
source: "YYYY-MM-DD_Book_Title_Author.md"
source_page: ""
source_chapter: "[[ten_chuong_tieng_viet]]"
ground_truth_page: ""
ground_truth_chapter: "[[ten_chuong_ban_goc_en]]"
source_type: epub | pdf | text
summary: "Tóm tắt insight cốt lõi 1-2 câu — KHÔNG lặp lại Evidence Hook."
people:
  - "Tên Tác Giả"
companies:
  - "Tổ Chức / NXB"
status: seed | growing | evergreen
related:
  - "[[snake_case_concept_1]]"
  - "[[snake_case_concept_2]]"
confidence: high
---

> "Trích dẫn nguyên văn bằng tiếng Việt (hoặc dịch sát nghĩa nếu nguồn là tiếng Anh) làm bằng chứng thực chứng cho khái niệm."
> — **Tên Tác Giả**, trích dẫn trong *Tên Sách*, [[source_note_slug|Tên Nguồn Ngắn]]

## Core Idea

[Phân tích chuyên sâu 1-3 đoạn văn bằng thuần tiếng Việt. Luận giải bản chất cơ chế, động lực vận hành và ý nghĩa ứng dụng thực tiễn. Tuyệt đối KHÔNG lồng quote thứ hai bên trong. Tuyệt đối KHÔNG lặp lại nội dung của Evidence Hook.]

## 📖 Bản gốc & Ngữ cảnh mở rộng (Ground Truth)

> "[Đoạn trích dẫn nguyên văn bằng TIẾNG ANH (hoặc ngôn ngữ gốc của nguồn thô) từ sách để phục vụ đối chiếu, kiểm chứng học thuật và khử ảo giác AI.]"
> — **Author Name**, *Original Book Title*, Chapter X: "Chapter Name"

---

## References

- [[YYYY-MM-DD_Book_Title_Author|Tên Sách (Source Note)]]
- [[chuong_sach_lien_quan|Chương Sách Liên Quan]]
- [[khai_niem_nen_tang|Khái Niệm Nền Tảng Khác]]
```

---

## 2. Bất Biến Vàng (Golden Invariants)

1. **Nguyên tử hóa (Atomic)**: Một khái niệm = Một tệp duy nhất. Không gộp nhiều ý tưởng khác biệt vào chung một ghi chú.
2. **Đối xứng Song Ngữ (Bilingual Ground Truth Grounding)**:
   - Hook đầu trang: BẮT BUỘC bằng **Tiếng Việt**.
   - Ground Truth phần dưới: BẮT BUỘC bằng **Tiếng Anh nguyên bản** từ tệp Markdown corpus thô.
3. **Clean Wikilinks (Cấm bọc backticks quanh wikilinks)**:
   - Cú pháp ví dụ bắt buộc phải đặt trong fenced code block (ngôn ngữ `text`):
   ```text
   [[concept_slug|Tên Hiển Thị]]
   ```
   - Tuyệt đối cấm bọc inline backticks quanh liên kết wikilinks vì sẽ biến liên kết thành code pill xám và làm gãy đồ thị Graph View trong Obsidian.
4. **Hai Chiều Đóng Kín (Bidirectional Linking)**:
   - Khi tạo concept note mới, phải tìm ít nhất 1-2 concept note cũ có liên quan mật thiết để cập nhật ngược liên kết `related` hoặc trích dẫn trong `## Core Idea`.
