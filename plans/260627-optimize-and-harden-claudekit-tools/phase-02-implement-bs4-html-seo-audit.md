---
phase: 2
title: "Implement BS4 HTML SEO Audit"
status: completed-progress
priority: P2
dependencies: [phase-01]
---

# Phase 2: Implement BS4 HTML SEO Audit

## Overview
Nâng cấp công cụ `seo_audit.py` để hỗ trợ rà soát cấu trúc SEO của tệp HTML sử dụng thư viện `beautifulsoup4`.

## Tasks
- [ ] Cài đặt/Đảm bảo thư viện `beautifulsoup4` có sẵn trong môi trường phát triển.
- [ ] Cập nhật `scripts/seo_audit.py` để phát hiện phần mở rộng `.html`/`.htm` và thực hiện phân tích bằng BeautifulSoup.
- [ ] Kiểm tra phân cấp heading (`<h1>`-`<h6>`), các thẻ meta tiêu đề/mô tả, thẻ alt của ảnh `<img>` trong HTML.
- [ ] Chạy thử nghiệm SEO audit trên một tệp HTML thực tế.

## Success Criteria
- [ ] Xuất báo cáo SEO và tính điểm tương tự Markdown cho các tệp HTML.
