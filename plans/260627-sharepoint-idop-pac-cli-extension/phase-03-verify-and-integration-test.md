---
phase: 3
title: "Verify and Integration Test"
status: pending
priority: P2
dependencies: [phase-02]
---

# Phase 3: Verify and Integration Test

## Overview
Cập nhật kịch bản kiểm định E2E `verify_idop_setup.py` để tự động hóa việc xác minh sản phẩm đóng gói Solution zip.

## Tasks
- [ ] Cập nhật `verify_idop_setup.py` để gọi lệnh đóng gói của `idop_scaffolder.py`.
- [ ] Bổ sung kiểm tra sự tồn tại và tính hợp lệ của tệp tin Solution zip đầu ra.
- [ ] Chạy kiểm định toàn diện E2E và ghi nhận kết quả nghiệm thu.

## Success Criteria
- [ ] Kịch bản `verify_idop_setup.py` thực thi thành công 100% các bài test và trả về Exit Code 0.
