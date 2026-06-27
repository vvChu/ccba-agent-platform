---
phase: 1
title: "Design CLI Integration"
status: pending
priority: P2
dependencies: []
---

# Phase 1: Design CLI Integration

## Overview
Thiết kế luồng tham số CLI và tích hợp Microsoft Power Platform CLI (PAC CLI) để đóng gói Power Automate Flow và Code Apps vào Solution zip.

## Tasks
- [ ] Phân tích cú pháp của các lệnh `pac solution init` và `pac solution pack`.
- [ ] Thiết kế tham số mới `--pack` và `--solution-name` trong `scripts/idop_scaffolder.py`.
- [ ] Xác định cơ chế gọi PAC CLI an toàn qua `subprocess.run` kèm theo kiểm tra tính khả dụng của lệnh `pac` trong PATH.

## Success Criteria
- [ ] Đặc tả thiết kế tham số và kiểm tra môi trường được phê duyệt.
