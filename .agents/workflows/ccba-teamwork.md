---
name: ccba-teamwork
command: /ccba-teamwork
description: Khởi động quy trình điều phối đa tác nhân dài hạn (Teamwork Multi-Agent Framework) theo mô hình 3 vai trò, lập Team Sheet và điều phối các đợt thực thi song song.
disable-model-invocation: true
bundle: _core
triggers:
- teamwork
- ccba-teamwork
- điều phối nhóm
- multi-agent
- team sheet
---
# Workflow: Điều Phối Đa Tác Nhân Dài Hạn (/ccba-teamwork)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `ccba-teamwork` tại [SKILL.md](../skills/ccba-teamwork/SKILL.md) để bắt đầu:

1. **Giai đoạn 1 (Structured Interview):** Phỏng vấn xác định mục tiêu dự án, non-goals, phân rã seams và ánh xạ trách nhiệm giải trình (11 Ghế CCBA Charter 2026).
2. **Giai đoạn 2 (Team Sheet Generation):** Sinh tệp `.agents/teams/[project]_team_sheet.md` theo template chuẩn và thực hiện File-path Pre-Check.
3. **Giai đoạn 3 (Parallel Milestone Execution):** Dispatch Workers (read-only, max 3/batch, timeout 10 phút), tổng hợp kết quả scratch và ghi file chính thức.
4. **Giai đoạn 4 (Success Auditor Gate):** Kiểm định scoped test suite, quét Maskara, kiểm toán Post-Merge Diff Audit và biên dịch Catalog SSOT.
