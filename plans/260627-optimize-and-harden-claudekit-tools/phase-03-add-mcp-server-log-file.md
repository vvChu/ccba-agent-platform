---
phase: 3
title: "Add MCP Server Log File"
status: completed-progress
priority: P2
dependencies: [phase-02]
---

# Phase 3: Add MCP Server Log File

## Overview
Cấu hình ghi log gỡ lỗi của custom MCP Server ra tệp tin chuyên dụng `.md/mcp_server.log` thay vì luồng stderr.

## Tasks
- [ ] Cập nhật `packages/ccba-ai/src/ccba_ai/mcp_server.py` để mở và ghi thông tin log (kết nối, yêu cầu gọi tool, lỗi) vào tệp tin `.md/mcp_server.log`.
- [ ] Đảm bảo thư mục `.md` được tạo tự động nếu chưa có trước khi ghi log.
- [ ] Chạy thử nghiệm kết nối MCP để đảm bảo tệp log được sinh ra và ghi đúng định dạng.

## Success Criteria
- [ ] Tệp tin `.md/mcp_server.log` chứa nhật ký hoạt động đầy đủ của máy chủ MCP mà không gây nhiễu luồng stderr.
