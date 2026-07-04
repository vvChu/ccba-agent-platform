---
proposal_id: "2026-07-04_ccba-document-standardization"
type: "skill"
name: "ccba-document-standardization"
status: "open"
priority: "High"
proposed_by_project: "ccba-agent-platform"
proposed_date: "2026-07-04"
applies_to:
  - "Khối Admin"
  - "Marketing"
  - "Ban Kỹ thuật thiết kế"
---

# Đề xuất Tích hợp: Kỹ năng Trích xuất & Soạn thảo Văn bản theo Mẫu chuẩn CCBA

## 1. Mô tả
Đề xuất tích hợp bộ kỹ năng **`ccba-document-standardization`** lên Platform Hub dùng chung. Bộ kỹ năng này hỗ trợ tự động hóa hoàn toàn quy trình nghiên cứu tài liệu thô hiện trạng (quyết định, hợp đồng, báo cáo, tờ trình), tự động trích xuất đặc trưng văn phong thầu/hành chính, tự động làm sạch và dựng thành tệp biểu mẫu chuẩn hóa (Templates có chứa placeholders và metadata phân loại) để phục vụ cho việc sinh tài liệu mới chính quy.

## 2. Vấn đề giải quyết
- **Lãng phí thời gian hành chính**: Nhân sự Admin tốn nhiều thời gian định dạng và căn chỉnh các văn bản hành chính theo đúng thể thức pháp lý (Nghị định 30/2020/NĐ-CP).
- **Rủi ro rò rỉ dữ liệu mật (Data Leakage)**: Việc gửi trực tiếp tài liệu hiện trạng thô có chứa số CCCD, Email, SĐT, hoặc giá trị tài chính lên các Cloud AI công cộng vi phạm chính sách bảo mật thông tin doanh nghiệp.
- **Lỗi định dạng bảng biểu**: Các bảng biểu Markdown thường bị vỡ định dạng cột khi chèn dữ liệu thô nhiều mục thủ công.

## 3. Giải pháp & Kiến trúc Đề xuất
Giải pháp áp dụng mô hình phân tách vai trò khép kín **Producer-Consumer Design**:

### Kịch bản Nghiên cứu & Dựng mẫu (`extract-style`) - Producer:
- Người dùng đặt tệp/thư mục tài liệu hiện trạng vào `assets/writing-styles/`.
- Chạy script phân tích trích xuất tích hợp thư viện **`maskara-privacy`** tự động che giấu số điện thoại, email, số CCCD, giá trị tiền mặt trước khi gửi chuỗi văn bản lên AI.
- AI Gateway (LiteLLM/Spark) trả về phân tích văn phong và bản dựng template Markdown có placeholders (dạng `{{placeholder}}`).
- Tự động gán Frontmatter phân loại (`category`, `document_type`) và các row-looping markers (`<!-- ROW_START -->`/`<!-- ROW_END -->`) cho bảng biểu, lưu vào thư mục `templates/`.

### Kịch bản Soạn thảo theo mẫu (`copywriting`) - Consumer:
- Nạp template tương ứng từ `templates/` đã được chuẩn hóa.
- Yêu cầu người dùng điền thông tin dự án mới cho các placeholders.
- Áp dụng các công thức viết thuyết phục (PAS, AIDA, BAB) và tự động ép kiểu định dạng đặt tên văn bản đầu ra chuyên nghiệp theo đúng Hiến pháp CCBA (`CCBA_ADM_<LOẠI>_...`).

## 4. Danh sách các tệp đề xuất chuyển lên Hub
```text
.agents/skills/copywriting/
  ├── SKILL.md
  ├── references/
  │    ├── copy-formulas.md
  │    ├── cta-patterns.md
  │    ├── email-copy.md
  │    ├── headline-templates.md
  │    ├── landing-page-copy.md
  │    ├── power-words.md
  │    └── writing-styles.md
  ├── scripts/
  │    └── extract-writing-styles.py
  └── templates/
       └── copy-brief.md

.agents/workflows/
  ├── ccba-copywriting.md
  └── ccba-extract-style.md
```
Tri thức nền đi kèm: Báo cáo nghiên cứu quy định soạn thảo văn bản hành chính Việt Nam [CCBA_RD_VBPL_004_Rev00-ND_30_2020_CongTacVanThu.md](../../.md/knowledge/CCBA_RD_VBPL_004_Rev00-ND_30_2020_CongTacVanThu.md).
