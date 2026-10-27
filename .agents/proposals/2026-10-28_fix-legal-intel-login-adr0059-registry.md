---
proposal_id: "2026-10-28_fix-legal-intel-login-adr0059-registry"
name: "fix-legal-intel-login-adr0059-registry"
title: "Fix TVPL multi-session login visibility, enforce ADR-0059 fail-fast in ingest-legal, and strip transient sandbox keys"
date: "2026-10-28"
author: "Antigravity Agent"
source_project: "ccba-legal-knowledge"
type: "fix"
target_skill: "ccba-legal-intel"
related_issue: "#572"
status: "proposed"
---

## Bối cảnh (Context)
Khi thực thi `/ccba-legal-ingest` tại Spoke `ccba-legal-knowledge` để nạp **Quyết định số 1812/QĐ-BXD ngày 21/10/2026** trên Linux, 3 lỗi kỹ thuật đã phát sinh trong luồng `TVPLCrawler` và `ccba_platform_cli.py ingest-legal`:
1. **Multi-Session Dialog Visibility**: Hộp thoại cảnh báo đăng nhập đa phiên của TVPL hiển thị `.ui-dialog` chứa nút `"Đồng ý"`, nhưng DOM trang TVPL có sẵn các hộp thoại `.ui-dialog` ẩn (`display: none`) nằm trước chứa nút `"Tiếp tục"`. Bộ chọn JS trong `ChromeCDP.handle_login()` và `TVPLVIPDocProvider._ensure_logged_in()` click nhầm nút ẩn khiến phiên VIP không được kích hoạt.
2. **Vi phạm ADR-0059 (Synthetic Fallback)**: Khi `mock=False` mà crawler không tải được file `.docx` thật, `ccba_platform_cli.py` tự động gọi `_generate_authoritative_fallback()` tạo văn bản giả lập đưa vào Spoke, vi phạm trực tiếp bất biến **ADR-0059 (Legal Verbatim Grounding & Mandatory Acquisition Invariant)**.
3. **Rò rỉ đường dẫn tạm `/tmp/` và link rác**: `metadata_handoff.json` truyền nguyên các trường tạm thời (`docx_path`, `attachments`, `links` chứa link mạng xã hội/hướng dẫn) vào `legal_registry.yaml`.

## Thay đổi chi tiết (Changes)
- `packages/ccba-legal-intel/src/ccba_legal/crawler/selectors.py`, `cdp.py`, `providers.py`: Thêm `TVPLSelectors.get_multi_session_confirm_js()` kiểm tra `window.getComputedStyle(cur).display !== 'none'` trên toàn bộ chuỗi tổ tiên DOM và ưu tiên `.ui-dialog` đang hiển thị.
- `scripts/ccba_platform_cli.py`: Loại bỏ nhánh gọi `_generate_authoritative_fallback` khi `mock=False` (trả về `False` ngay lập tức kèm thông báo `ADR-0059 Acquisition Barrier`) và lọc bỏ các khóa tạm thời (`docx_path`, `pdf_path`, `attachments`, `links`, `content`) khỏi `metadata_handoff.json`.
- `packages/ccba-legal-intel/src/ccba_legal/tvpl_parser.py`: Lọc bỏ các link chia sẻ mạng xã hội (`facebook.com`, `dmca.com`) và link hướng dẫn (`tvpl-hdsd-`) trong `get_crawled_doc_data()`.

## Cách test (Verification)
```bash
pytest packages/ccba-legal-intel/tests/test_crawler_seam.py scripts/tests/test_ccba_platform_cli.py -q
python -m ccba_harness verify-patch
```
