# Templates — Reusable document templates

Thư mục chứa templates chung cho nhiều projects (Word, Excel, Markdown).

## Quy tắc

- Skill-specific templates → lưu trong `.agent/skills/{skill}/templates/`
- Templates dùng chung nhiều skills → lưu ở đây
- Dùng placeholders `{{VARIABLE}}` cho nội dung động

## Phân biệt với Skill Templates

| | Templates/ (global) | Skill templates |
|---|---------------------|----------------|
| **Scope** | Dùng chung | Dùng trong 1 skill |
| **Ví dụ** | Mẫu công văn CCBA | Checklist hồ sơ hoàn thành |
