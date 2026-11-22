---
proposal_id: "2026-11-22_xu-ly-van-phong-xlsx-calc-standards"
type: "skill"
name: "xu-ly-van-phong-xlsx-calc-standards"
status: "open"
priority: "Cao"
related_issue: "#851"
proposed_by_project: "ccba-engineering-calc"
proposed_by_archetype: "project_delivery"
proposed_date: "2026-11-22"
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
---

# Proposal: Tier 2A Bilingual Engineering Calculation Sheet Standards for `ccba-xu-ly-van-phong`

## 1. Phân loại Theo ADR-0057 (`evaluate-gpi`) & ADR-0045
- Chạy `ccba-harness evaluate-gpi` xác nhận quy trình chuẩn hóa bảng tính kỹ thuật song ngữ đạt **`GPI = 9.50 < 12.0`** (`S=3.0, K=2.0, A=2.0, P=4.0` với Master Skill `ccba-xu-ly-van-phong`) $\rightarrow$ phân tầng đích là **Tier 2A (Progressive Reference & Canonical Template)** trực thuộc `ccba-xu-ly-van-phong`, không tạo Standalone Skill mới để tránh phình ngữ cảnh và trùng lặp trigger.
- Phần thực thi tất định (YAML IR $\rightarrow$ `.xlsx`/PDF) đã được tách về Tầng 1 (`ccba-ooxml`, PR #852) theo Cổng 0 `ADR-0057` & `ADR-0061`.

## 2. Nội dung Cập nhật Trên `ccba-xu-ly-van-phong`
1. Thêm cặp template + schema mẫu trung tính: `templates/xlsx-bang-tinh-ky-thuat-song-ngu.md` & `templates/calc_sheet_template_schema.yaml` (`CCBA-CALC-SAMPLE-01`, không chứa dữ liệu dự án cụ thể).
2. Bổ sung **Palette X4 — CCBA Brand Identity v3.4 & RULE-6.1** vào `standards/color/xlsx-palettes.md`.
3. Cập nhật `standards/structure/xlsx-structure.md` với quy chuẩn bố cục A4 Portrait 2 sheet và độ rộng cột `[6, 44, 21, 11, 9, 25]` / `[15, 36, 13, 52]`.
4. Cập nhật `resources/xlsx.md` với bảng ánh xạ Deep Seam `ccba-ooxml` (`TID251`) và 5 rào chắn thực chiến (YAML 1.1 `item_no:`, `fitToHeight=0` + manual `Break`, gộp khối `A:C`/`D:F`, `CellRichText` xếp dọc, đối soát pháp lý ADR-0059 & kiểm định ảnh PDF→PNG).
5. Cập nhật `SKILL.md` lên `v2.2.0`.
