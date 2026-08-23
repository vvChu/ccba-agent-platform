# 🎫 Ticket 04: Đóng Gói Bài Học Kinh Nghiệm Vào session_learnings.md

## 🎯 Mục Tiêu (Goal)
Ghi nhận 2 quy tắc thiết kế cốt lõi (Design Patterns) vào `.md/knowledge/session_learnings.md`:
1. **Pattern P7.20 (Hub-Spoke Taxonomy & Bundle Integrity Guard):**
   - Nguyên tắc: Mọi thay đổi về Archetype / Bundle / Spoke Type phải được cập nhật đồng bộ qua 4 điểm chạm: `catalog.yaml` -> CLI Help/Choices -> Workflow `applies_to` -> Bootstrap Python detector.
   - Được bảo vệ bởi CI Gate tự động `test_taxonomy_integrity.py`.
2. **Pattern P7.21 (Sandbox Identification Invariant):**
   - Nguyên tắc: Không bao giờ đánh đồng Archetype cấp cao (`specialized_extension`) với cờ trạng thái tạm thời (`is_sandbox`). Phải kiểm tra đúng `sub_type == 'personal_sandbox'` hoặc `guardrails.sandbox_mode == True`.

## 🛠️ Yêu Cầu Kỹ Thuật
- Định dạng Markdown chuẩn Knowledge Base, liên kết tới ADR 0041, ADR 0044, ADR 0046.
