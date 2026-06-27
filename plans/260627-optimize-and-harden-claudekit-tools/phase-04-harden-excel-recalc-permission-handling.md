---
phase: 4
title: "Harden Excel Recalc Permission Handling"
status: completed-progress
priority: P2
dependencies: [phase-03]
---

# Phase 4: Harden Excel Recalc Permission Handling

## Overview
Gia cố xử lý lỗi ghi tệp tin Macro LibreOffice ở thư mục AppData/UserHome của hệ điều hành, đảm bảo hệ thống tự động fallback sang `openpyxl` nếu thiếu quyền ghi.

## Tasks
- [ ] Rà soát hàm `setup_libreoffice_macro` trong `packages/ccba-pdf-prep/src/ccba_pdf_prep/document_skills/xlsx_recalc.py`.
- [ ] Bao bọc việc tạo thư mục và ghi tệp tin Macro bằng khối `try-except Exception` toàn diện.
- [ ] Trả về cảnh báo và kích hoạt chế độ fallback sang `openpyxl` thay vì để hệ thống crash.
- [ ] Chạy unit test để đảm bảo không xảy ra biệt lệ chết (fatal exception) khi mất quyền ghi.

## Success Criteria
- [ ] Module hoạt động bền bỉ, không crash chương trình ngay cả khi không có quyền ghi thư mục AppData.
