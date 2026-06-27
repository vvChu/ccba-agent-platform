---
phase: 2
title: "SEO Audit Tool CLI"
status: completed-progress
priority: P2
dependencies: [phase-01]
---

# Phase 2: SEO Audit Tool CLI

## Overview
Xây dựng công cụ phân tích kỹ thuật SEO tự động để đánh giá mức độ tuân thủ chuẩn SEO của các tệp HTML/Markdown trong dự án.

## Tasks
- [ ] Triển khai script `scripts/seo_audit.py` hỗ trợ nhận đường dẫn tệp tin qua tham số CLI.
- [ ] Cài đặt các bộ lọc phân tích cấu trúc tiêu đề (h1-h6), độ dài meta tags, sự hiện diện của image alt tags và các liên kết ngoài.
- [ ] Chạy thử nghiệm xuất báo cáo tuân thủ chuẩn SEO trên một tệp tài liệu mẫu.

## Success Criteria
- [ ] Công cụ xuất báo cáo SEO chi tiết với tỷ lệ đạt chuẩn (%) và danh sách các khuyến nghị cần tối ưu hóa.
