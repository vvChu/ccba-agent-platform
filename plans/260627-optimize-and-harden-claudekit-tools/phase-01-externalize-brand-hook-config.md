---
phase: 1
title: "Externalize Brand Hook Config"
status: completed-progress
priority: P2
dependencies: []
---

# Phase 1: Externalize Brand Hook Config

## Overview
Di chuyển các từ khóa thương hiệu và từ cấm hardcode trong `brand_enforcement.py` vào tệp tin cấu hình chuyên dụng `.md/brand_rules.yaml`.

## Tasks
- [ ] Khởi tạo tệp tin cấu hình `.md/brand_rules.yaml` chứa cấu trúc cấu hình `brand_enforcement` (gồm danh sách regex và từ cấm).
- [ ] Cập nhật `scripts/hooks/brand_enforcement.py` để nạp cấu hình động từ `.md/brand_rules.yaml` (sử dụng thư viện `PyYAML`).
- [ ] Chạy thử nghiệm rà soát để đảm bảo hook hoạt động chính xác sau khi nạp động.

## Success Criteria
- [ ] Rà soát hoạt động đúng và cảnh báo chính xác dựa trên cấu hình được khai báo tại `.md/brand_rules.yaml`.
