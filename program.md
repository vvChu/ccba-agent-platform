# CCBA AutoResearch: Program Specification (program.md)

> Thí nghiệm tối ưu hóa tự động (Karpathy Git-Ratchet Auto-Tuner) cho Kỹ năng Biên soạn Học thuật (academic_writing).

---

## 🎯 Mục tiêu Thí nghiệm (Experiment Goal)
- **Target File**: .agents/skills/academic_writing/SKILL.md
- **Target Score**: 95.0%
- **Max Iterations**: 5
- **Dataset File**: .agents/skills/eval-gate/test_cases/eval_academic_writing.json

---

## 🛡️ Ranh giới & Rào chắn (Guardrails)
- **Được phép sửa (Allowed Files)**: Chỉ sửa duy nhất nội dung phần body của `Target File`.
- **Cấm sửa (Prohibited Files)**: `test_cases/`, `scorers.py`, `eval_runner.py`, `git_ratchet_tuner.py`.
- **Rào chắn Điểm Liệt (Hard Floor Invariant)**: Bắt buộc 0 Critical Failures (tuyệt đối không vi phạm văn phong cảm tính, bắt buộc trích dẫn chuẩn APA/BibTeX và cấu trúc CARS 3-Move).

---

## 🔄 Cơ chế Bánh cóc (Ratchet Invariants)
1. **KEEP (Commit)**: Khi `Score_mới > Score_cũ` và không có Điểm Liệt $\rightarrow$ AI tự động `git commit`.
2. **REVERT (Rollback)**: Khi `Score_mới <= Score_cũ` hoặc có lỗi $\rightarrow$ AI tự động `git checkout -- <file>`.
