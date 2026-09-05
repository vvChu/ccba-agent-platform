# 0056. Migration of Legacy Workflows to Modern Skills and Direct CCBA Namespace Standardization

* **Status:** Accepted
* **Date:** 2026-09-05
* **Deciders:** CCBA Platform Core Team
* **Consulted:** ADR 0021 (BIGBIM Retention), ADR 0040 (Skills Hierarchy), ADR 0047 (Catalog Manifest SSOT), ADR 0051 (Hub-Spoke Sync Hardening & Virtual Fallback)

---

## Context & Problem Statement

Hệ sinh thái AI Agent trên Google Antigravity đã chuyển dịch triệt để từ các tệp quy trình tĩnh (`.agents/workflows/*.md`) sang kiến trúc kỹ năng đóng gói động (**Dynamic Agent Skills** tại `.agents/skills/**/SKILL.md`). Kỹ năng hiện đại cung cấp khả năng gọi lệnh trực tiếp từ giao diện chat (`command: /{skill_name}`), nạp ngữ cảnh theo nhu cầu (Context Budget On-Demand), kèm theo tài nguyên bổ trợ (`resources/`) và mã thực thi cô lập (`scripts/`).

Trước khi thực hiện cải tiến này, nền tảng CCBA Agent Services Platform gặp phải các thách thức kiến trúc:
1. **Lưỡng hình Kiến trúc (Dual-Architecture Overhead):** Sự cùng tồn tại song song giữa 69 legacy workflows và 77 skills tạo ra chi phí bảo trì kép, làm phân mảnh `catalog.yaml` và gây nhầm lẫn trong điều phối đa tác tử.
2. **Thiếu Định Danh Doanh Nghiệp Thống Nhất:** Nhiều kỹ năng nội bộ mang tên chung chung (`wait-what`, `ask`, `copywriting`, `spoke-adopter`, `tvpl-vip-crawler`), không có tiền tố để phân biệt rõ ràng giữa kỹ năng độc quyền của tổ chức CCBA và các công cụ/skills tích hợp sẵn của IDE.
3. **Hiện tượng "Zombie Bloat" tại Spoke:** Khi Hub đổi tên hoặc nâng cấp kỹ năng, các trạm Spoke chạy `sync_spoke.py` vẫn giữ nguyên các thư mục kỹ năng cũ và tệp workflow cũ, dẫn tới tình trạng dư thừa tài nguyên và nguy cơ gọi nhầm phiên bản lỗi thời.

---

## Decision Outcome

Đội ngũ kiến trúc CCBA quyết định thực hiện cuộc chuyển đổi quy mô lớn, dứt khoát và an toàn:

### 1. Trực Tiếp Chuẩn Hóa Namespace `ccba-*`
- Đổi tên trực tiếp toàn bộ các kỹ năng nội bộ CCBA sang tiền tố `ccba-*` (ví dụ: `wait-what` $\rightarrow$ `ccba-wait-what`, `ask` $\rightarrow$ `ccba-ask`, `tvpl-vip-crawler` $\rightarrow$ `ccba-tvpl-vip-crawler`).
- **Bảo tồn ranh giới bất biến:**
  - Giữ nguyên 5 kỹ năng miền `bigbim-*` (`bigbim-classification`, `bigbim-governance`, `bigbim-rase`, `bigbim-risk`, `bigbim-vbpl-digest`) theo ADR 0021.
  - Giữ nguyên thư mục bootstrap gốc `.agents/skills/platform-loader/` để đảm bảo tương thích ngược tuyệt đối cho quy trình Spoke Discovery và các test fixtures.
- Nền tảng đạt tổng cộng **99 kỹ năng** (93 `ccba-*`, 5 `bigbim-*`, 1 `platform-loader`).

### 2. Chuyển Đổi 100% Legacy Workflows Sang Modern Skills
- Toàn bộ 22 workflows chưa có kỹ năng tương ứng đã được nâng cấp thành 22 kỹ năng `ccba-*` hoàn chỉnh (bao gồm 3 quy trình thẩm tra PCCC chuyên sâu).
- Toàn bộ 69 tệp workflow cũ trong `.agents/workflows/` được lưu trữ an toàn dưới dạng `*.md.bak`. Thư mục `.agents/workflows/` không còn bất kỳ active `.md` nào.

### 3. Cơ Chế Khử Zombie Bloat & Ánh Xạ Chuyển Hướng Tại Spoke
- Bổ sung bảng ánh xạ chuyển hướng `SKILL_DEPRECATION_ALIASES` (83 mục) trong `scripts/spoke/sync/coordinator.py`.
- Khi Spoke thực hiện đồng bộ:
  - Tự động xóa các thư mục kỹ năng cũ (un-prefixed) sau khi đã sao chép kỹ năng `ccba-*` mới.
  - Tự động phát hiện và đổi tên các workflow cũ tại Spoke thành `.md.bak` (gắn nhãn `DEPRECATED_MIGRATED_TO_SKILL`).

### 4. Hiện Đại Hóa Bộ Sinh Mã Kỹ Năng (Scaffolding Engine)
- Nâng cấp `scripts/scaffolding/skill_generator.py`:
  - `create_skill_from_script`: Tự động cưỡng chế tiền tố `ccba-` cho các kỹ năng mới sinh.
  - `write_skill_markdown`: Tự động tiêm các trường frontmatter chuẩn Antigravity (`user-invocable: true`, `command: /{skill_name}`, `triggers:`).
  - `sync_all_skills`: Bổ sung cơ chế bóc tách tiền tố (`name_no_prefix`) giúp liên kết thông minh giữa folder kỹ năng `ccba-<name>` và script nguồn `scripts/<name>.py`.

### 5. Tái Biên Dịch Single Source of Truth (SSOT) Catalog
- `catalog.yaml` được biên dịch lại toàn diện: Quản lý chính xác 99 skills, 0 active workflows.

---

## Consequences

### Positive
- **Hợp nhất Kiến trúc:** Loại bỏ hoàn toàn sự phân mảnh Workflow/Skill, đưa toàn bộ nền tảng về 1 chuẩn kỹ năng duy nhất của Google Antigravity.
- **Tường minh Nhận diện:** Người dùng và Agent dễ dàng nhận biết các kỹ năng thuộc hệ sinh thái CCBA qua tiền tố `ccba-*` và kích hoạt nhanh qua thanh slash command (`/ccba-*`).
- **Sạch Sẽ & An Toàn tại Spoke:** Cơ chế deprecation aliases loại bỏ triệt để zombie bloat và rủi ro nhầm lẫn phiên bản tại các trạm Spoke.
- **Hệ Thống Kiểm Thử 100% Xanh:** Toàn bộ 346 tests nền tảng, 660 tests packages, 99 skill validation gates, linter `ruff` và type checker `mypy` đều vượt qua kiểm định.

### Negative / Trade-offs
- Các dự án Spoke hiện hữu cần chạy `python scripts/sync_spoke.py --apply` để dọn dẹp các tệp cũ và nạp các kỹ năng mang namespace mới.
- Các tài liệu tham khảo nội bộ và hướng dẫn sử dụng cần thời gian chuyển đổi thói quen gõ lệnh slash command từ dạng cũ sang `/ccba-*`.
