---
proposal_id: "2026-07-02_skills-validator"
type: "skill"
name: "skills-validator"
status: "open"
priority: "Cao"
proposed_by_project: "ccba-agent-platform"
proposed_date: "2026-07-02"
applies_to:
  - "Tất cả"
---

## Mô tả
Kỹ năng kiểm định chất lượng tệp `SKILL.md` của các Kỹ năng (Skills) trên Platform. Giúp bảo đảm chất lượng tài liệu kỹ năng khi phân phối cho AI Agent.

## Vấn đề giải quyết
- Context Bloat: Tránh các mô hình AI tải ngữ cảnh bị quá tải (bloated) do phần mô tả kỹ năng (`description`) quá dài (giới hạn tối đa 180 ký tự cho Model-Invoked Skills).
- Lỗi logic hành động của Agent: Đảm bảo các bước hành động tuần tự trong kỹ năng luôn đi kèm tiêu chí hoàn thành rõ ràng (`**Completion Criterion:**` hoặc `**Tiêu chí hoàn thành:**`) để AI Agent có thể đối chiếu và tự kiểm tra chất lượng kết quả đầu ra.

## Giải pháp / Cấu trúc đề xuất
- Đóng gói kịch bản kiểm định [validate_skills.py](file:///d:/GitHubProjects/ccba-agent-platform/scripts/validate_skills.py) làm công cụ quét tĩnh.
- Cấu hình tích hợp Git pre-commit hook trong `.pre-commit-config.yaml` để tự động kiểm định cục bộ trước khi cho phép commit.

## Nội dung mẫu / Code mẫu
Xem mã nguồn chi tiết tại [validate_skills.py](file:///d:/GitHubProjects/ccba-agent-platform/scripts/validate_skills.py).

Cấu hình hook pre-commit mẫu:
```yaml
  - repo: local
    hooks:
      - id: validate-skills
        name: validate-skills
        entry: python scripts/validate_skills.py
        language: python
        types: [markdown]
        files: \.agents/skills/.*SKILL\.md$
        pass_filenames: true
```
