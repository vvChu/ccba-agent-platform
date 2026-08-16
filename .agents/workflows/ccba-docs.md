---
description: Khởi động quy trình tự động cập nhật và kiểm định tài liệu kỹ thuật của dự án.
triggers: [/ccba-docs, cập nhật tài liệu, update docs]
applies_to:
  - "Phần mềm"
bundle: "_core"
disable-model-invocation: true
---
# Workflow: ccba-docs

Khi người dùng kích hoạt Slash Command này, Agent **bắt buộc** phải nạp và thực thi kỹ năng `docs_manager` tại [SKILL.md](../skills/docs_manager/SKILL.md) để bắt đầu quy trình quản lý tài liệu.
