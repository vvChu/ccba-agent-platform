---
proposal_id: "2026-11-23_harden-docx-post-edit-and-spoke-retrospective-cli"
type: "skill"
name: "harden-docx-post-edit-and-spoke-retrospective-cli"
status: "merged"
merged_pr: "#876"
merged_commit: "843032de"
merged_date: "2026-11-23"
priority: "Trung bình"
related_issue: "#874"
proposed_by_project: "consulting_spoke"
proposed_by_archetype: "project_delivery"
proposed_date: "2026-11-23"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
---

# Proposal: Bổ Sung Rào Chắn Hậu Chỉnh Tay Word (`ccba-xu-ly-van-phong`) & Sửa Đường Dẫn Guardrails Spoke (`ccba-session-retrospective`)

## 1. Bối cảnh & Kiểm toán Nền tảng (ADR-0057 / ADR-0061)
- Phần nền tảng cho Báo cáo Đánh giá Kỹ thuật DOCX (`TechnicalReportBuilder`, `docx-ccba-brand.md`, `docx-ky-thuat-bao-cao-danh-gia.md`, `tech_report_template_schema.yaml` và 4 rào chắn biên tập) đã được hợp nhất vào Hub qua PR `#863` / Issue `#856`.
- Trong vận hành thực tế tại Spoke tư vấn `project_delivery` (thư mục dự án non-git trên OneDrive) và quá trình rà soát tệp `.docx` sau khi người dùng chỉnh tay trực tiếp trên Microsoft Word, phát sinh thêm **2 điểm thiếu hụt** ở Tier 2A trên `origin/main`:
  1. **`ccba-xu-ly-van-phong/resources/docx.md`:** Chưa có rào chắn kiểm định hậu chỉnh tay Microsoft Word. Khi mở và lưu tay `.docx` bằng Word cho các phiên bản sau (`Rev. N`), Word thường gỡ bỏ `<w:tblLayout w:val="fixed"/>`, để lệch mã phiên bản ở `word/header*.xml` so với Trang bìa, làm mất màu zebra ở dòng thêm mới, và giữ nguyên `<dc:creator>python-docx</dc:creator>` trong `docProps/core.xml`.
  2. **`ccba-session-retrospective/SKILL.md`:** Bước 4 mục 3 vẫn chỉ dẫn lệnh `python scripts/_guardrails/check_spoke_cleanliness.py && python scripts/_guardrails/check_hub_import_depth.py` vốn không tồn tại trên các Spoke thông thường (trên Hub 2 script này nằm ở `scripts/spoke/`), và Bước 5 chưa có hướng dẫn cho Spoke tư vấn non-git. (Issue `#874` đang mở cho `ccba-maskara`, `ccba-release-feature` và `sync_adr_matrix.py`; đề xuất này bổ sung sạch cho Bước 4/Bước 5 mà không xung đột.)

## 2. Thay đổi Đề xuất (Tier 2A — `SKILL.md` & `resources/docx.md`)
1. **`ccba-xu-ly-van-phong` (`2.3.0 -> 2.3.1`):**
   - Cập nhật `resources/docx.md` bổ sung **Rào chắn 5: Kiểm định hậu chỉnh tay Microsoft Word (`Post-Manual-Word-Edit Hygiene`)** kèm tiêu chí hoàn thành đo được (`word/header*.xml` khớp `Rev.`, 100% bảng giữ `<w:tblLayout w:val="fixed"/>` tổng `9071 DXA` + `<w:cantSplit/>`, `docProps/core.xml` sạch) và ghi chú tính tùy chọn của dòng tiêu đề khối ký trong Rào chắn 2.
2. **`ccba-session-retrospective` (`1.7.2 -> 1.7.3`):**
   - Cập nhật Bước 4 mục 3 dùng `${CCBA_HUB_PATH:-../ccba-agent-platform}/scripts/spoke/check_spoke_cleanliness.py --path .` và `check_hub_import_depth.py --path .`.
   - Bổ sung hướng dẫn xử lý cho Spoke **non-git** tại Bước 5.
