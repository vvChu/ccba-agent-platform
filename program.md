# CCBA AutoResearch: Program Specification (program.md)

> Thí nghiệm tối ưu hóa tự động mở rộng toàn diện (Maximized Git-Ratchet Loop) cho kỹ năng Tra cứu & Pháp điển Pháp luật (ccba-legal-intel).

---

## 🎯 Mục tiêu Thí nghiệm (Experiment Goal)
- **Target File**: .agents/skills/ccba-legal-intel/SKILL.md
- **Target Score**: 100.0%
- **Max Iterations**: 10
- **Dataset File**: .agents/skills/eval-gate/test_cases/eval_legal_intel.json

---

## 🛡️ Ranh giới & Rào chắn (Guardrails)
- **Được phép sửa (Allowed Files)**: Chỉ sửa duy nhất nội dung phần body của `Target File`.
- **Cấm sửa (Prohibited Files)**: `test_cases/`, `scorers.py`, `eval_runner.py`, `git_ratchet_tuner.py`.
- **Rào chắn Điểm Liệt (Hard Floor Invariant)**: Bắt buộc 0 Critical Failures (tuyệt đối không trích dẫn nghị định/thông tư hết hiệu lực như NĐ 136/2020 hay QCVN 06:2020).

---

## 🔄 Cơ chế Bánh cóc (Ratchet Invariants)
1. **KEEP (Commit)**: Khi `Score_mới > Score_cũ` và không có Điểm Liệt $\rightarrow$ AI tự động `git commit`.
2. **REVERT (Rollback)**: Khi `Score_mới <= Score_cũ` hoặc có lỗi $\rightarrow$ AI tự động `git checkout -- <file>`.
