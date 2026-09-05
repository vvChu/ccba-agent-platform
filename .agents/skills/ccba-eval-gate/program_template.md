# CCBA AutoResearch: Program Specification Template (program.md)

> Lấy cảm hứng từ `karpathy/autoresearch`. File này là hợp đồng tối giản giữa Kỹ sư và AI Agent để điều phối vòng lặp tối ưu hóa tự động (Git-Ratchet Loop).

---

## 🎯 Mục tiêu Thí nghiệm (Experiment Goal)
- **Target File**: `.agents/skills/ccba-legal-intel/SKILL.md`
- **Target Score**: 95.0%
- **Max Iterations**: 10
- **Dataset File**: `.agents/skills/ccba-eval-gate/test_cases/eval_legal_intel.json`

---

## 🛡️ Ranh giới & Rào chắn (Guardrails)
- **Được phép sửa (Allowed Files)**: Chỉ sửa duy nhất nội dung phần body của `Target File`.
- **Cấm sửa (Prohibited Files)**: `test_cases/`, `scorers.py`, `eval_runner.py`, `git_ratchet_tuner.py`.
- **Rào chắn Điểm Liệt (Hard Floor Invariant)**: Bắt buộc 0 Critical Failures (không trích dẫn nghị định hết hiệu lực).

---

## 🔄 Cơ chế Bánh cóc (Ratchet Invariants)
1. **KEEP (Commit)**: Khi `Score_mới > Score_cũ` và không có Điểm Liệt $\rightarrow$ AI tự động `git commit`.
2. **REVERT (Rollback)**: Khi `Score_mới <= Score_cũ` hoặc có lỗi $\rightarrow$ AI tự động `git checkout -- <file>`.
