---
phase: 1
title: "Brand Enforcement Hook"
status: completed-progress
priority: P2
dependencies: []
---

# Phase 1: Brand Enforcement Hook

## Overview
Tích hợp hook kiểm tra và cảnh báo việc tuân thủ các quy tắc thương hiệu và từ ngữ cốt lõi đối với các nội dung văn bản do LLM tạo ra.

## Tasks
- [ ] Triển khai script hook `scripts/hooks/brand_enforcement.py` với cấu trúc từ khóa cần kiểm tra (ví dụ: `ccba-agent-platform`, `LiteLLM`, `Antigravity`).
- [ ] Tích hợp kiểm tra vào `scripts/hook_runner.py` ở giai đoạn `post-tool` để quét các tệp tin mới tạo.
- [ ] Chạy thử nghiệm phát hiện từ cấm hoặc sai chính tả thương hiệu.

## Success Criteria
- [ ] Cảnh báo thành công khi phát hiện viết sai chính tả các từ khóa thương hiệu chính hoặc sử dụng từ cấm trong tệp tin đầu ra.
