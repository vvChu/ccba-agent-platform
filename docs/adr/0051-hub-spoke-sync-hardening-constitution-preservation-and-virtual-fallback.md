# ADR 0051: Hub-Spoke Sync Hardening, Constitution Preservation & Virtual Hub Fallback

## 1. Trạng Thái (Status)
**ACCEPTED & ADOPTED** (2026-08-31)

## 2. Bối Cảnh (Context)
Trong quá trình vận hành thực tế tại Spoke (`vvc_working_space`) và tương tác đa bộ môn (Phần mềm, Tư vấn, Pháp lý), đã phát hiện 5 điểm nghẽn kỹ thuật:
1. **Lệch pha Workflow - Skill (Ghost Workflows)**: Thư mục `.agents/workflows/` và `.agents/skills/` bị lệch pha bundle (ví dụ: `ccba-legal-advisor.md` thuộc `_core` trong khi `legal-advisor` thuộc `_consulting`), dẫn tới Spoke loại hình `Phần mềm` chỉ tải `_core` và `_software` sẽ có file workflow nhưng thiếu file `SKILL.md` đích $\rightarrow$ gây lỗi Broken Link / 404.
2. **Ghi đè Hiến pháp `AGENTS.md` (Constitution Reset)**: Lệnh `sync_spoke.py` ghi đè toàn bộ `AGENTS.md` từ Hub template, xóa mất khối cấu hình `## Agent skills` (Issue Tracker, Triage Labels, Domain Docs, Custom Rules) của Spoke.
3. **Lỗi chữ ký hàm `sync_legal_assets`**: `scripts/spoke/sync/sdk_inspector.py` gọi hàm `sync_legal_assets` với tham số `target_spoke=...` gây lỗi `TypeError: unexpected keyword argument`.
4. **Thiếu hỗ trợ Đa Bundle trong YAML**: Chưa hỗ trợ trường `additional_bundles` trong `workspace_context.yaml` để Spoke kết hợp linh hoạt công cụ Phần mềm và Tư vấn/Pháp lý.
5. **Chưa có cơ chế Virtual Hub Fallback**: Khi Spoke chưa copy vật lý file skill về đĩa cục bộ (để tiết kiệm dung lượng), Agent thiếu quy chuẩn đọc trực tiếp qua `hub_path`.

## 3. Quyết Định Thiết Kế (Decisions)

### A. Đồng Bộ Đối Xứng 1:1 (Workflow-Skill Bundle Pairing)
- Mọi Workflow (`.agents/workflows/*.md`) bắt buộc phải khai báo trường `bundle:` trong YAML frontmatter khớp chính xác với `bundle:` của Skill liên kết (`.agents/skills/**/SKILL.md`).
- Trình biên dịch `compile_catalog.py` cưỡng chế kiểm tra tính nhất quán bundle giữa workflows và skills khi chạy `--check`.

### B. Hòa Trộn Hiến Pháp Bảo Toàn (Non-Destructive Section Merge)
- Khi cập nhật `AGENTS.md` trên Spoke, `SpokeCoordinator` thực hiện phân rã tài liệu theo cấp mục (`## Heading`):
  - Khối định nghĩa Layer 1 Constitution và Core Invariants được cập nhật theo bản mới nhất từ Hub.
  - Toàn bộ các section tùy biến riêng của Spoke (bao gồm `## Agent skills`, cấu hình Issue Tracker, Triage Labels, Custom Rules) được bảo lưu nguyên vẹn và hòa trộn ở phía dưới.

### C. Mở Rộng Parser Đa Bundle (`additional_bundles`)
- `SpokeCoordinator` hỗ trợ trích xuất trường `additional_bundles: list[str]` từ `workspace_context.yaml` (hỗ trợ cả cấp gốc và lồng trong `project:`).
- Các bundle bổ sung được tự động gộp vào `required_bundles` khi thực thi lệnh đồng bộ.

### D. Chuẩn Hóa Lời Gọi SDK & Chữ Ký Hàm
- Chuẩn hóa việc truyền `target_dir` và `project_root` trong `sdk_inspector.py` khi gọi `sync_legal_assets()` từ `ccba_legal.sync`.

### E. Quy Chuẩn Hóa Cơ Chế Virtual Hub Fallback
- Bổ sung điều khoản bất biến vào Layer 1 Constitution (`AGENTS.md`):
  > *"Virtual Hub Fallback: In Spoke mode, if a referenced skill is not physically present in `.\.agents\skills\`, the Agent MUST transparently read the skill definition directly from `[hub_path]\.agents\skills\<skill_name>\SKILL.md`."*
- Giúp Spoke duy trì trạng thái Zero-Bloat tối đa mà vẫn có khả năng vận hành đầy đủ 100% kỹ năng của toàn bộ nền tảng CCBA.

### F. Phân Giải Đường Dẫn Đa Hệ Điều Hành (Multi-OS Dynamic Hub Path Resolution)
- Hỗ trợ biến môi trường ưu tiên cao nhất `CCBA_HUB_PATH` trên toàn bộ các công cụ phát hiện và engine đồng bộ Spoke (`scripts/spoke/sync/discovery.py`).
- Mở rộng lược đồ `workspace_context.yaml` cho phép khai báo `hub_path` dưới dạng từ điển đa hệ điều hành:
  ```yaml
  hub_path:
    windows: "D:\\GitHubProjects\\ccba-agent-platform"
    linux: "/home/vvc/ccba/ccba-agent-platform"
  ```
- Trên các hệ thống Linux/WSL/POSIX, các hàm phân giải đường dẫn (`resolve_hub_path()`) tự động bỏ qua các chuỗi mang ký tự ổ đĩa Windows (`D:\...`) nếu không tồn tại trên đĩa, ngăn chặn lỗi `FileNotFoundError` và rò rỉ trạng thái máy cục bộ.

## 4. Hệ Quả (Consequences)
- **Bảo Vệ Toàn Vẹn Cấu Hình Spoke:** Cập nhật Hub không bao giờ làm mất cấu hình tracker, nhãn hoặc hướng dẫn riêng của Spoke.
- **Không Còn Ghost Workflows:** Loại bỏ triệt để các liên kết gãy giữa workflow và skill.
- **Linh Hoạt Đa Bundle:** Một Spoke Phần mềm có thể dễ dàng kích hoạt thêm bộ công cụ Tư vấn/Pháp lý chỉ bằng 1 dòng `additional_bundles: [_consulting]`.
- **Tức Thì 0ms:** Agent có thể tra cứu và thực thi mọi skill trên Hub qua Virtual Hub Fallback mà không cần tải hàng trăm MB về máy.
- **Liền Mạch Đa Nền Tảng (Cross-Platform Parity):** Agent vận hành trơn tru trên cả Linux, WSL, CI và Windows mà không cần sửa đổi thủ công cấu hình khi chuyển đổi máy trạm.
