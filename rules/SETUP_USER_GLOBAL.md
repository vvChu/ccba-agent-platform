# Hướng dẫn cập nhật User Global Rules

## Nội dung cần thêm vào user_global

Thêm section sau vào cuối `user_global` rules (Settings → Gemini → User Rules):

```
## 4. CCBA Agent Services Platform (Hub)
- **Hub Path**: `D:\GitHubProjects\ccba-agent-platform`
- **Rule**: Khi bắt đầu phiên làm việc ở BẤT KỲ workspace nào, Agent nên đọc Hub để nắm:
  1. Danh sách skills available: `Hub/.agent/skills/` (đọc SKILL.md frontmatter)
  2. CCBA rules: `Hub/rules/` (đọc khi tạo output mang danh CCBA)
  3. Knowledge base: `Hub/knowledge/session_learnings.md` (đọc patterns/anti-patterns)
- **Rule**: Khi project hiện tại có `.md/workspace_context.yaml`, đọc file này để lấy local overrides
- **Rule**: Output cuối cùng lưu về thư mục project, KHÔNG lưu rải rác ở Hub
- **Rule**: Temp/processing files lưu ở `Hub/.md/`
```

## Cách cập nhật

1. Mở Gemini Settings (VS Code: Ctrl+Shift+P → "Gemini: Open Settings")
2. Tìm mục "User Rules" hoặc "Custom Instructions"
3. Thêm nội dung trên vào cuối rules hiện có
4. Save

## Hiệu lực

Sau khi thêm, Agent sẽ tự động:
- Biết vị trí Hub khi làm việc ở bất kỳ workspace nào
- Load skills/rules/knowledge từ Hub khi cần
- Tuân thủ CCBA identity & quality standards
