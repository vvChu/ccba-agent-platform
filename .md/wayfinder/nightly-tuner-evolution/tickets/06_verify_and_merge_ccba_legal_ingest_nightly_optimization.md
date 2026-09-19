# Ticket 06: Nghiệm Thu & Chốt Kết Quả Auto-Tune Đêm 19/09 Cho Kỹ Năng `ccba-legal-ingest`

- **Type:** Task (AFK / Review & PR)
- **Status:** open
- **Assignee:** Antigravity AI Agent
- **Target Branch:** `auto-tune/nightly-20260919_000014`
- **Target Seam:** `.agents/skills/ccba-legal-ingest/SKILL.md`
- **Reference:** Commit `ac1d445658cc0cf9be5f11cc9cf115eb39b043be`

---

## 🎯 Mục Tiêu
Nghiệm thu kết quả tối ưu hóa tự động của Nightly Tuner trên nhánh `auto-tune/nightly-20260919_000014`.
Kỹ năng `ccba-legal-ingest` đã được cải thiện từ **86.7% lên 100.0% (+13.3%)** bằng cách bổ sung mục:
`## 5. Rào Chắn Điểm Liệt & Cập Nhật Hiệu Lực Văn Bản (Hard Floor Invariant)` với các quy chuẩn cập nhật bắt buộc:
- Nghị định 136/2020/NĐ-CP $\rightarrow$ **Nghị định 105/2025/NĐ-CP**.
- QCVN 06:2020/BXD $\rightarrow$ **QCVN 06:2022/BXD & Sửa đổi 1:2023**.
- Thông tư 149/2020/TT-BCA $\rightarrow$ Văn bản cập nhật mới nhất.

---

## 📋 Nhiệm Vụ Thực Hiện
1. Kiểm tra tính toàn vẹn của diff trên nhánh `auto-tune/nightly-20260919_000014`.
2. Chạy kiểm định 15 cổng CI gate qua `python scripts/validate_skills.py --file .agents/skills/ccba-legal-ingest/SKILL.md --enforce-gpi`.
3. Kiểm tra `python -m ccba_harness verify-patch --preset skill --target .agents/skills/ccba-legal-ingest/SKILL.md`.
4. Mở Pull Request lên GitHub với tiêu đề:
   `auto-tune: optimize ccba-legal-ingest skill 86.7% -> 100.0% (+13.3%) [nightly-20260919_000014]`
   kèm nhãn `needs-triage`.

---

## ✅ Tiêu Chí Nghiệm Thu (Acceptance Criteria)
- [ ] 1. Toàn bộ kiểm định kỹ năng `validate_skills.py` và `verify-patch --preset skill` đạt 100% PASS.
- [ ] 2. PR được tạo thành công trên GitHub bằng `gh pr create`.
