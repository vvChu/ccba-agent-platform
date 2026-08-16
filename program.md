# CCBA AutoResearch: Program Specification (program.md)

> Thí nghiệm Red-Teaming & Stress-Testing Bẫy Thiết Kế PCCC (Bậc chịu lửa, Khói, Thoát nạn) cho kỹ năng ccba-ai-qc-pccc-audit.

---

## 🎯 Mục tiêu Thí nghiệm (Experiment Goal)
- **Target File**: .agents/skills/ccba-ai-qc-pccc-audit/SKILL.md
- **Target Score**: 95.0%
- **Max Iterations**: 5
- **Dataset File**: .agents/skills/eval-gate/test_cases/eval_pccc_audit_redteam.json

---

## 🛡️ Ranh giới & Rào chắn (Guardrails)
- **Được phép sửa (Allowed Files)**: Chỉ sửa duy nhất nội dung phần body của `Target File`.
- **Cấm sửa (Prohibited Files)**: `test_cases/`, `scorers.py`, `eval_runner.py`, `git_ratchet_tuner.py`.
- **Rào chắn Điểm Liệt (Hard Floor Invariant)**: Bắt buộc 0 Critical Failures (tuyệt đối không chấp thuận vi phạm bậc chịu lửa, khoảng cách thoát nạn, hệ thống hút khói, kết cấu thép trần, buồng thang bộ hoặc thiếu van ngăn cháy).

---

## 🔄 Cơ chế Bánh cóc (Ratchet Invariants)
1. **KEEP (Commit)**: Khi `Score_mới > Score_cũ` và không có Điểm Liệt $\rightarrow$ AI tự động `git commit`.
2. **REVERT (Rollback)**: Khi `Score_mới <= Score_cũ` hoặc có lỗi $\rightarrow$ AI tự động `git checkout -- <file>`.
