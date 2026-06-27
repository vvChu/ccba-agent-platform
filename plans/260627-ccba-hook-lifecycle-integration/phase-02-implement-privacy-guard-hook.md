---
phase: 2
title: "Implement Privacy Guard Hook"
status: pending
priority: P2
dependencies: [phase-01]
---

# Phase 2: Implement Privacy Guard Hook

## Overview
Hiện thực hóa lớp bảo mật chặn ghi đè API Keys (Gemini, OpenAI, LlamaCloud, Groq...) vào bất kỳ file mã nguồn `.py` hay `.md` nào.

## Tasks
- [ ] Khởi tạo module `ccba_ai/hooks/` và lớp `PrivacyGuardHook`.
- [ ] Hiện thực hóa hàm chặn Regex để quét nội dung file trước khi ghi đè trên ổ đĩa.
- [ ] Cho phép đọc tệp `hooks.yaml` để xác định cấu hình kích hoạt.
- [ ] Tích hợp `PrivacyGuardHook` vào hàm ghi file chính thức của AI Client trong `ccba-ai`.

## Success Criteria
- [ ] Lớp chặn chặn đứng được mã ghi đè chứa API keys mẫu và in thông báo lỗi rõ ràng.
