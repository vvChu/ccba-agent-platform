---
phase: 1
title: "Design CLI Integration"
status: completed
priority: P2
dependencies: []
---

# Phase 1: Design CLI Integration

## Overview
Thiết kế luồng tham số CLI và tích hợp Microsoft Power Platform CLI (PAC CLI) để đóng gói Power Automate Flow và Code Apps vào Solution zip.

## Tasks
- [x] Phân tích cú pháp của các lệnh `pac solution init` và `pac solution pack`.
- [x] Thiết kế tham số mới `--pack` và `--solution-name` trong `scripts/idop_scaffolder.py`.
- [x] Xác định cơ chế gọi PAC CLI an toàn qua `subprocess.run` kèm theo kiểm tra tính khả dụng của lệnh `pac` trong PATH.

## Success Criteria
- [x] Đặc tả thiết kế tham số và kiểm tra môi trường được phê duyệt.
