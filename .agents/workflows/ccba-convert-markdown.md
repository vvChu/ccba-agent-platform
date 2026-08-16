---
description: Chuyển đổi tài liệu sang Markdown qua Deep Seam ConversionPipeline (tự động xử lý bảng biểu, biểu mẫu, liên kết)
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
disable-model-invocation: true
---
# Workflow: Convert to Markdown (/ccba-convert-markdown)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `markdown-document-processing` tại [SKILL.md](../skills/markdown-processing/SKILL.md) để chuyển đổi tài liệu Word/PDF sang Markdown thông qua Deep Seam `ConversionPipeline` (tự động phục hồi bảng vỡ, làm sạch biểu mẫu và chuẩn hóa liên kết phụ lục trong 1 bước).
