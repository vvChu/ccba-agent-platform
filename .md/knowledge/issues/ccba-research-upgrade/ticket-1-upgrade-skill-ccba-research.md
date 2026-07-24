# Ticket 1: Upgrade Skill ccba-research (`ticket-1-upgrade-skill-ccba-research`)

> **Map:** [`[Bản đồ Wayfinder ccba-research-upgrade]`](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/ccba-research-upgrade/map.md)  
> **Loại Ticket:** Task [AFK]  
> **Trạng thái:** Đã đóng (Closed)  
> **Assignee:** Agent (Antigravity)  

---

## ❓ Câu hỏi / Tác vụ (Question / Task)

Cập nhật tệp [`d:\GitHubProjects\ccba-agent-platform\.agents\skills\ccba-research\SKILL.md`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-research/SKILL.md) với 4 cải tiến nâng cấp từ thượng nguồn `claudekit-engineer`:

1. **Search Budget Cap**: Giới hạn tối đa **5 lượt gọi tool tìm kiếm/tra cứu (max 5 tool calls)** trong prompt giao nhiệm vụ cho subagent `research`.
2. **Mẫu Báo cáo Kỹ thuật 5 phần**:
   - Section 1: Executive Summary (Tóm tắt thực thi)
   - Section 2: Key Findings (Phát hiện cốt lõi, Best practices, Common Pitfalls)
   - Section 3: Implementation Recommendations (Khuyến nghị triển khai)
   - Section 4: References & Citations (Tài liệu tham chiếu & Nguồn trích dẫn sơ cấp)
   - Section 5: Unresolved Questions (Các câu hỏi/điểm mù chưa làm rõ)
3. **Quy chuẩn Kiểm chứng Nguồn tin (Cross-Reference Validation)**: Yêu cầu đối chiếu chéo các nguồn tin độc lập và ưu tiên tài liệu trong 12 tháng gần nhất / VBPL hiện hành.
4. **Cơ chế Lưu trữ Linh hoạt (Dynamic Storage)**: Hỗ trợ lưu mặc định tại `.md/knowledge/research_and_studies/research-[slug].md` hoặc thư mục issue tương ứng.

---

## 📋 Kết quả Thực hiện (Resolution)

- Đã nâng cấp thành công tệp `SKILL.md` của `ccba-research` chứa đầy đủ 4 tính năng cải tiến.
- Kiểm định `python scripts/validate_skills.py` đạt 100% OK.

---

## 📋 Tiêu chí Hoàn thành (Completion Criteria)

- [x] Tệp `SKILL.md` của `ccba-research` được cập nhật đầy đủ 4 nội dung trên.
- [x] Chạy `python scripts/validate_skills.py` đạt kết quả 100% OK.
