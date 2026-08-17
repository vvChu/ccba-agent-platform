# CCBA AutoResearch: Program Specification (program.md)

> Thí nghiệm tối ưu hóa tự động (Karpathy Git-Ratchet Auto-Tuner) cho Kỹ năng Phân loại Thông tin Mô hình BIM (bigbim-classification).

---

## 🎯 Mục tiêu Thí nghiệm (Experiment Goal)
- **Target File**: `.agents/skills/bigbim-classification/SKILL.md`
- **Target Score**: 95.0%
- **Max Iterations**: 10
- **Dataset File**: `.agents/skills/eval-gate/test_cases/eval_bigbim_classification.json`

---

## 🛡️ Ranh giới & Rào chắn (Guardrails)
- **Được phép sửa (Allowed Files)**: Chỉ sửa duy nhất nội dung phần body của `Target File`. Giữ nguyên 100% phần YAML Frontmatter.
- **Cấm sửa (Prohibited Files)**: `test_cases/`, `scorers.py`, `eval_runner.py`, `git_ratchet_tuner.py`.
- **Rào chắn Điểm Liệt (Hard Floor Invariant)**: Bắt buộc 0 Critical Failures (tuyệt đối không nhầm lẫn giữa các bảng phân loại Uniclass Pr / PM / En / Ss / EF, bảo toàn nguyên lý phân tầng ISO 12006-2:2015 và ISO 22274:2013).

---

## 🔄 Cơ chế Bánh cóc (Ratchet Invariants)
1. **KEEP (Commit)**: Khi `Score_mới > Score_cũ` và không có Điểm Liệt $\rightarrow$ AI tự động `git commit`.
2. **REVERT (Rollback)**: Khi `Score_mới <= Score_cũ` hoặc có lỗi $\rightarrow$ AI tự động `git checkout -- <file>`.
