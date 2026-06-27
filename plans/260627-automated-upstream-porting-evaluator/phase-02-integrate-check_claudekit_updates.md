---
phase: 2
title: "Integrate check_claudekit_updates"
status: completed-progress
priority: P2
dependencies: [phase-01]
---

# Phase 2: Integrate check_claudekit_updates

## Overview
Liên kết `scripts/check_claudekit_updates.py` với `assess_upstream_features.py` để tự động kích hoạt tiến trình đánh giá khi phát hiện upstream thay đổi.

## Tasks
- [ ] Cập nhật `scripts/check_claudekit_updates.py` để gọi tiến trình con (subprocess) của `assess_upstream_features.py` khi phát hiện commit mới.
- [ ] Truyền tham số commit SHA mới nhất cho script đánh giá.
- [ ] Chạy giả lập (mocking) tiến trình chạy ngầm để đảm bảo hoạt động bất đồng bộ diễn ra an toàn.

## Success Criteria
- [ ] Tiến trình checker tự động gọi bộ evaluator khi phát hiện thay đổi trên nhánh gốc.
