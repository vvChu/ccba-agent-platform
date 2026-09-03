---
id: 230
title: "feat(ccba-ooxml): deep seam presentation builder for automated slide deck generation"
state: "closed"
labels:
  - "enhancement"
  - "closed"
assignee: "Antigravity AI Agent"
created_at: "2026-09-02T06:27:43Z"
updated_at: "2026-09-03T02:10:30Z"
---

# 📖 Mô tả (Description)
### 1. Bối cảnh & Vấn đề (Context & Problem):
- Package `ccba-ooxml` hiện có các module rất hoàn thiện cho văn bản Word (`docx/change_engine.py`, `docx/comment_engine.py`), nhưng phần `pptx` mới chỉ dừng ở mức kiểm tra tính toàn vẹn XML (`validation/pptx.py`).
- Trong các luồng công việc đào tạo nội bộ (`/ccba-prepare-seminar`), báo cáo chủ đầu tư và thuyết minh thẩm tra kỹ thuật, Agent phải dừng lại ở định dạng Markdown/text thô do thiếu công cụ tự động hóa xuất bản sang slide PowerPoint (`.pptx`).

---

### 2. Đề xuất giải pháp (RFC Proposal):
Mở rộng `packages/ccba-ooxml` với các module chuyên sâu cho PowerPoint:
- **`ccba_ooxml.pptx.deck_builder`**: Engine phân tích AST từ Markdown sang các slide PowerPoint có cấu trúc.
- **`ccba_ooxml.pptx.templates`**: Bộ master layout chuẩn nhận diện thương hiệu CCBA (Slide tiêu đề, slide nội dung 2 cột, slide bảng số liệu, slide thẻ so sánh Callout).
- **Hỗ trợ định dạng phong phú**: Tự động chuyển bảng Markdown thành PowerPoint Native Tables và khối chú thích Callout.
- **CLI & Python API**: Hỗ trợ `python -m ccba_ooxml build-deck input.md --output seminar.pptx`.

---

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [x] Bổ sung module `ccba_ooxml.pptx.deck_builder` và `ccba_ooxml.pptx.templates`.
- [x] Tự động chuyển đổi file Markdown seminar / báo cáo thành tệp `.pptx` hoàn chỉnh với layout chuẩn CCBA.
- [x] Bộ test suite `test_deck_builder.py` đạt 100% độ phủ cho các layout phổ biến (Title, Split, Table, Cards).
- [x] Tích hợp liền mạch với skill `seminar-builder` và workflow `/ccba-prepare-seminar`.

---
*Được đề xuất tự động từ Spoke `ccba-legal-knowledge` qua workflow `/ccba-issue-to-hub`.*

---

# 💬 Thảo luận (Discussion Log)
> **@Antigravity AI Agent (Triage)** (2026-09-02T06:40:00Z):
> Đã hoàn tất quy trình sàng lọc và thẩm định kỹ thuật (Triage).
> Xác nhận nhu cầu mở rộng tính năng tạo PowerPoint Presentation (`.pptx`) từ Markdown cho `ccba-ooxml`, phục vụ trực tiếp `seminar-builder` và báo cáo kỹ thuật.
> Đã gán nhãn `enhancement` và chuyển trạng thái sang `ready-for-agent`. Đính kèm Agent Brief chi tiết bên dưới.

---

## Agent Brief

**Phân loại:** enhancement
**Tóm tắt yêu cầu:** Xây dựng Deep Seam Presentation Builder (`ccba_ooxml.pptx.deck_builder`) để tự động chuyển đổi Markdown thành file PowerPoint (`.pptx`) theo mẫu nhận diện thương hiệu CCBA.

### Hành vi hiện tại (Current behavior)
- `packages/ccba-ooxml` chỉ hỗ trợ chỉnh sửa docx nâng cao và validate cấu trúc pptx cơ bản.
- Chưa có module sinh slide thuyết trình tự động từ nội dung Markdown.

### Hành vi mong muốn (Desired behavior)
- `ccba_ooxml.pptx.deck_builder` phân tích cú pháp Markdown (headings, bullets, tables, callout blocks, slide dividers `---` hoặc `<!-- slide -->`) và dựng slide deck hoàn chỉnh.
- Master Layout chuẩn thương hiệu CCBA (Primary: Deep Navy `#003366`, Secondary: Amber Gold `#FFBF00`, Neutral: Pure White `#FFFFFF`).
- Hỗ trợ các dạng layout:
  - Title / Cover Slide
  - Single / Split Column (2-column layout)
  - Data Tables (Native PPTX Table)
  - Cards / Key Takeaways Callout Boxes
- Giao diện CLI `python -m ccba_ooxml build-deck <input_md> --output <output_pptx>`.

### Các Interface & Kiểu dữ liệu chính (Key interfaces)
- `packages/ccba-ooxml/src/ccba_ooxml/pptx/deck_builder.py`: `DeckBuilder`, `SlideSpec`
- `packages/ccba-ooxml/src/ccba_ooxml/pptx/templates.py`: `CCBAPresentationTheme`
- `packages/ccba-ooxml/src/ccba_ooxml/__init__.py`: Export `build_presentation_from_markdown`

### Tiêu chuẩn nghiệm thu (Acceptance criteria)
- [x] Chuyển đổi thành công Markdown có nhiều slide thành tệp `.pptx` mở được trên Microsoft PowerPoint / LibreOffice mà không có lỗi format.
- [x] Bảng và danh sách hiển thị cân đối, đúng typography và màu sắc thương hiệu.
- [x] CLI `build-deck` hoạt động ổn định.
- [x] Bộ test suite `test_deck_builder.py` pass 100%.

### Phạm vi loại trừ (Out of scope)
- Không can thiệp vào các logic Word docx hiện có trong `ccba-ooxml/docx`.

### Đề xuất chế độ thực thi (Recommended Execution Strategy)
- **Mức độ phức tạp**: Trung bình (trong phạm vi package `ccba-ooxml`)
- **Khuyến nghị thực thi**:
  - `[x]` 🟢 **Standard** (`/ccba-implement`): Triển khai tuần tự, scoped tests.
  - `[ ]` 🟣 **Deep Reasoning** (`/boost`): Điều tra chuyên sâu root-cause / phản biện đa vòng.
  - `[ ]` 🔵 **Multi-Agent Orchestration** (`/ccba-teamwork` hoặc `/teamwork-preview`): Phân rã Seams và chạy đa tác nhân song song.

---

> **@Antigravity AI Agent (Resolution)** (2026-09-03T02:10:30Z):
> Đã hoàn tất triển khai và nghiệm thu đầy đủ tính năng Deep Seam Presentation Builder cho `ccba-ooxml`:
> - Module `ccba_ooxml.pptx.deck_builder` và `ccba_ooxml.pptx.templates` (Swiss Minimalist + Storytelling With You archetypes).
> - Tích hợp CLI `python -m ccba_ooxml build-deck` và skill `seminar-builder`.
> - Hoàn thành 100% test coverage (28/28 tests), pass toàn bộ 6 cổng CI GitHub Actions.
> - Đã merge vào nhánh chính qua PR [#235](https://github.com/vvChu/ccba-agent-platform/pull/235). Trạng thái Issue: **CLOSED**.
