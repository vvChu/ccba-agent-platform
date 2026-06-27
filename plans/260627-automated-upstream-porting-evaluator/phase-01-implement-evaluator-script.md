---
phase: 1
title: "Implement Evaluator Script"
status: completed-progress
priority: P2
dependencies: []
---

# Phase 1: Implement Evaluator Script

## Overview
Hiện thực hóa mã nguồn của `scripts/assess_upstream_features.py` để phân tích và đánh giá tự động các kỹ năng mới sử dụng mô hình LLM từ `ccba-ai`.

## Tasks
- [ ] Khởi tạo tệp tin `scripts/assess_upstream_features.py` với cấu trúc nạp chéo git diff của cả 2 thư mục `claudekit-engineer` và `claudekit-marketing`.
- [ ] Tích hợp bộ gọi AI Gateway (`from ccba_ai import ai`) để gửi Prompt kiểm thử Double-Pass Adversarial Review.
- [ ] Tạo báo cáo tổng hợp kết quả định dạng Markdown tại `.md/port_recommendations.md`.
- [ ] Viết bộ test đơn giản giả lập một skill mới để kiểm tra tính đúng đắn của logic đánh giá.

## Success Criteria
- [ ] Sinh tệp tin `.md/port_recommendations.md` với đánh giá của AI chính xác sau khi chạy thử nghiệm.
