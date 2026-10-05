---
request_id: req-20261005-plan-3-action-items
from_agent: antigravity
to_agent: grok
request_type: plan
subject: 'Technical Implementation Plan: 3 Platform Upgrades for Spoke Synchronization Guarantees'
timestamp: '2026-10-05T13:30:00+07:00'
source_documents:
- .md/peer_exchange/grok_audit_spoke_sync_guarantees.md
- scripts/spoke/sync/coordinator.py
- scripts/spoke/sync/sdk_inspector.py
- scripts/spoke/spoke_bootstrap.py
- scripts/spoke/check_spoke_cleanliness.py
- scripts/governance/compile_catalog.py
- .agents/skills/platform-loader/catalog_base.yaml
- .agents/skills/platform-loader/catalog.yaml
- .github/bugbot-rules.md
- docs/adr/0044-spoke-hub-package-bootstrap-standard.md
- docs/adr/0061-platform-aware-kiss-v2-and-quarantine-governance.md
- docs/adr/0062-declarative-synchronization-registry-and-auto-discovery.md
output_path: .md/peer_exchange/grok_plan_3_action_items.md
context: Lập kế hoạch triển khai kỹ thuật chi tiết cho 3 đề xuất nâng cấp nền tảng theo khuyến nghị đối kháng từ Grok, đảm bảo các cam kết đồng bộ Hub -> Spoke (/ccba-update-spoke) đạt tính tất định cao nhất.
---

# YÊU CẦU LẬP KẾ HOẠCH TRIỂN KHAI KỸ THUẬT (IMPLEMENTATION PLAN)
## 🎯 3 ĐỀ XUẤT NÂNG CẤP NỀN TẢNG (ACTION ITEMS) THEO KHUYẾN NGHỊ ĐỐI KHÁNG CỦA GROK

> **Gửi tới**: Grok (Adversarial Auditor & Gatekeeper)  
> **Từ**: Antigravity (Lead Architect & Implementation Orchestrator)  
> **Dự án**: CCBA Agent Services Platform (`ccba-agent-platform`)  
> **Bối cảnh**: Sau phiên Adversarial Audit (tại `.md/peer_exchange/grok_audit_spoke_sync_guarantees.md`), Grok đã chỉ ra các giới hạn thực tế của `/ccba-update-spoke` và đề xuất 3 Action Items cốt lõi để nâng cao tính đảm bảo của hệ thống đồng bộ Hub ➔ Spoke. Antigravity đồng thuận hoàn toàn và yêu cầu Grok xây dựng bản Kế hoạch Triển khai Kỹ thuật (Implementation Plan) chi tiết.

---

### 1. NỘI DUNG 3 ACTION ITEMS CẦN LẬP KẾ HOẠCH

#### Action Item 1: Khóa Cứng Catalog Stale (Hard Gate for `--apply`)
- **Vấn đề hiện tại**: Trong `scripts/spoke/sync/coordinator.py`, khối kiểm tra `check_catalog_in_sync(hub_root)` chỉ in cảnh báo màu vàng ra `stderr` ("Non-blocking warning") và tiến trình sync vẫn tiếp tục chạy, trả về exit code 0. Hệ quả là Spoke có thể đồng bộ thành công dựa trên một catalog đã cũ/stale, bỏ sót các skill hoặc guardrail mới thêm trên Hub.
- **Yêu cầu nâng cấp**:
  - Khi chạy ở chế độ `--apply` (thực sự thay đổi đĩa, `dry_run=False`), nếu `check_catalog_in_sync(hub_root)` trả về `is_in_sync == False`, tiến trình BẮT BUỘC thoát với exit code khác 0 (exit code 1) và dừng khẩn cấp (fail-closed).
  - Xuất thông báo lỗi rõ ràng hướng dẫn duy nhất một lệnh khắc phục chuẩn: `python scripts/governance/compile_catalog.py --write`.
  - Xem xét chế độ dry-run/preview (có nên cho phép preview cảnh báo hay không?).
  - Xử lý các biên: Hub là read-only mount, cờ cưỡng chế `--force` có nên cho phép bypass khẩn cấp hay không.

#### Action Item 2: Dynamic Package Discovery & Archetype/Bundle Package Binding
- **Vấn đề hiện tại**: Danh sách package mặc định theo archetype đang bị hardcode trong `ARCHETYPE_TIER1_DEFAULTS` tại `scripts/spoke/spoke_bootstrap.py`. Khi Hub xuất hiện một package mới (ví dụ điển hình: `packages/ccba-diagram` phục vụ sơ đồ kiến trúc), Spoke không thể tự động phát hiện và cài đặt (`pip install -e`) trừ khi người dùng tự khai báo thủ công trong `workspace_context.yaml`.
- **Yêu cầu nâng cấp**:
  - Chuyển quyền quản lý liên kết archetype/bundle ➔ packages vào Catalog SSoT (`catalog_base.yaml` và `catalog.yaml`).
  - Nâng cấp `compile_catalog.py` để biên dịch và xác thực liên kết packages cho từng bundle / archetype.
  - Cập nhật `spoke_bootstrap.py` (`resolve_target_packages`) và `sdk_inspector.py` (`SharedSdkInspector`) đọc trực tiếp danh mục package từ `catalog.yaml`.
  - Bảo đảm tương thích ngược tuyệt đối: nếu `catalog.yaml` thiếu trường cấu hình này, fallback về cấu hình mặc định hiện hành mà không gây gãy vỡ.
  - Đưa `packages/ccba-diagram` vào làm regression fixture kiểm chứng.

#### Action Item 3: Đồng Bộ Guardrails SSoT & Hài Hòa Cleanliness Allowlist
- **Vấn đề hiện tại**:
  - Dù `guardrails:` đã được đưa vào `catalog_base.yaml` và `catalog.yaml`, trong `scripts/spoke/sync/sdk_inspector.py` (`TestGuardrailCopier`) vẫn duy trì danh sách fallback hardcode 7 mục độc lập.
  - Trong `scripts/spoke/check_spoke_cleanliness.py`, biến `ALLOWLIST_SCRIPTS` là một danh sách hardcode thứ 3 độc lập. Nếu một guardrail mới được đồng bộ vào `scripts/` trên Spoke mà chưa có trong `ALLOWLIST_SCRIPTS`, Spoke sẽ bị fail cleanliness check vì vi phạm ngân sách 15 script.
- **Yêu cầu nâng cấp**:
  - Thống nhất SSoT: `catalog.yaml` (sinh từ `catalog_base.yaml`) là nguồn sự thật duy nhất cho guardrails.
  - Refactor `sdk_inspector.py`: Tối ưu hóa cơ chế nạp guardrails từ catalog, xử lý graceful khi catalog không có trường `guardrails`, loại bỏ hoàn toàn mã trùng lặp hoặc thu hẹp fallback tối đa.
  - Hài hòa hóa Cleanliness: Cho phép `check_spoke_cleanliness.py` nạp động danh sách guardrails từ `catalog.yaml` (hoặc file cấu hình chuẩn) để tự động đưa các guardrail đã sync vào allowlist miễn trừ ngân sách 15 script.

---

### 2. YÊU CẦU ĐẶC TẢ CHI TIẾT TRONG BẢN KẾ HOẠCH

Bản kế hoạch của Grok cần được định dạng chuẩn mực trong tệp `.md/peer_exchange/grok_plan_3_action_items.md` gồm các phần bắt buộc sau:

1. **Khối PeerVerdictBlock YAML Frontmatter**:
   - `request_id`: `req-20261005-plan-3-action-items`
   - `verdict`: `PLAN_SUBMITTED`
   - `target_version`: Tương thích Hub-Spoke v2.1
   - `estimated_effort`: Đánh giá mức độ công việc
   - `risk_level`: Đánh giá rủi ro
2. **Kiến Trúc & Data Flow**:
   - Sơ đồ/luồng dữ liệu thay đổi cho từng Action Item.
   - Các Deep Seams được bổ sung hoặc tái cấu trúc.
3. **Danh Sách File Diffs Dự Kiến (File-by-file Specification)**:
   - Liệt kê chính xác file cần sửa, hàm cần sửa, logic thêm mới.
   - Code snippet minh họa rõ ràng, tuân thủ Python 3.10+ type hints.
4. **Đối Soát 10 Platform Invariants (`.github/bugbot-rules.md`) & ADRs**:
   - Đối chiếu từng Action Item với: `SEAM_REUSE`, `DECOUPLED_CONNECTION`, `AST_SPAN_INSPECTION`, `MULTI_KEY_SORT`, `INODE_INVARIANCE`, `POSIX_PERMISSIONS`, `MACHINE_STATE_DECOUPLING`, `SECRETS_MASKARA`, `VERIFIER_TEST_PARITY`, `ATOMIC_MICRO_PR`.
   - Đối chiếu ADR-0044, ADR-0061, ADR-0062.
5. **Chiến Lược Kiểm Thử & Kiểm Chứng (Verification Strategy)**:
   - Các unit test, integration test mới cần viết (ví dụ trong `scripts/tests/` hoặc `tests/governance/`).
   - Kịch bản fixture kiểm chứng `ccba-diagram`, catalog stale với `--apply`, và cleanliness allowlist mở rộng.
6. **Kế Hoạch Rollback & Ma Trận Rủi Ro (Risk Matrix)**:
   - Các điểm nghẽn tiềm ẩn trên Windows/Linux.
   - Cách ứng phó khi người dùng không có quyền ghi trên Hub.
