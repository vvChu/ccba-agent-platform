---
id: 223
title: "feat(spoke-sync): harden hub-spoke synchronization, constitution preservation & virtual hub fallback"
state: "ready-for-agent"
labels:
  - "enhancement"
  - "ready-for-agent"
assignee: "none"
created_at: "2026-08-31T14:37:57Z"
updated_at: "2026-08-31T14:46:39Z"
---

# 📖 Mô tả (Description)
### 1. Bối cảnh & Vấn đề (Context & Problem):
Trong quá trình vận hành thực tế tại Spoke (`vvc_working_space`), đã phát hiện 5 điểm nghẽn kỹ thuật trong cơ chế đồng bộ Hub-Spoke:
1. **Lệch pha Workflow - Skill (Ghost Workflows)**: Thư mục `.agents/workflows/` được copy toàn bộ nhưng `.agents/skills/` bị lọc theo `project.type` (ví dụ: `Phần mềm` chỉ lấy `_core` và `_software`), dẫn đến tình trạng có file workflow (ví dụ `/ccba-legal-advisor`) nhưng thiếu file `SKILL.md` đích (gây lỗi Broken Link / 404).
2. **Ghi đè Hiến pháp `AGENTS.md` (Constitution Reset)**: Lệnh `sync_spoke.py` ghi đè toàn bộ `AGENTS.md` từ Hub template, xóa mất khối cấu hình `## Agent skills` (Issue Tracker, Triage Labels, Domain Docs) của Spoke.
3. **Lỗi chữ ký hàm `sync_legal_assets`**: `scripts/spoke/sync/coordinator.py` gọi hàm `sync_legal_assets` với tham số `target_spoke` gây lỗi `unexpected keyword argument 'target_spoke'`.
4. **Thiếu hỗ trợ Đa Bundle trong YAML**: Chưa hỗ trợ trường `additional_bundles` trong `workspace_context.yaml` để Spoke kết hợp linh hoạt công cụ Phần mềm và Tư vấn/Pháp lý.
5. **Chưa có cơ chế Virtual Hub Fallback**: Khi thiếu 1 skill, Agent phải copy vật lý file về đĩa thay vì đọc trực tiếp qua `hub_path`.

### 2. Đề xuất giải pháp (RFC Proposal):
- **Đồng bộ đối xứng 1:1 (Co-located Pairing)**: Cập nhật `coordinator.py` chỉ đồng bộ workflow nếu skill tương ứng thuộc Bundle được chọn (hoặc mở rộng cơ chế On-demand auto-fetch).
- **Bảo toàn khối `AGENTS.md` (Non-Destructive Section Merge)**: Tự động tách và bảo lưu khối `## Agent skills` của Spoke khi cập nhật `AGENTS.md`.
- **Sửa lỗi `sync_legal_assets()`**: Chuẩn hóa chữ ký hàm và tham số gọi module sync.
- **Hỗ trợ `additional_bundles` trong `workspace_context.yaml`**: Cập nhật parser để đọc mảng bundle bổ sung từ config Spoke.
- **Cơ chế Virtual Hub Fallback**: Quy chuẩn hóa việc Agent đọc trực tiếp từ `[hub_path]/.agents/skills/<skill>/SKILL.md` khi local chưa có file (tiết kiệm ổ cứng, tức thì 0ms).

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [ ] `sync_spoke.py` đồng bộ đối xứng Workflow và Skill theo bundle; không còn broken link.
- [ ] `sync_spoke.py` bảo toàn nguyên vẹn khối `## Agent skills` trong `AGENTS.md`.
- [ ] Khắc phục cảnh báo ngoại lệ trong `sync_legal_assets()`.
- [ ] Bổ sung unit tests cho parser `additional_bundles` và section-preserving merge.
- [ ] Cập nhật tài liệu ADR / Hiến pháp hướng dẫn Virtual Hub Fallback.

---
*Được đề xuất tự động từ Spoke `vvc_working_space` qua workflow `/ccba-issue-to-hub`.*


---

# 💬 Thảo luận (Discussion Log)
> **@Antigravity AI Agent (Triage)** (2026-08-31T21:47:00Z):
> Đã hoàn tất quy trình sàng lọc và thẩm định kỹ thuật (Triage). 
> Xác nhận 5 điểm nghẽn kỹ thuật nêu trong Issue #223 hoàn toàn có cơ sở trong mã nguồn Hub hiện tại (`coordinator.py`, `sdk_inspector.py`, `catalog.yaml`). 
> Đã gán nhãn `enhancement` và chuyển trạng thái sang `ready-for-agent`. Đính kèm Agent Brief hoàn chỉnh bên dưới.

---

## Agent Brief

**Phân loại:** enhancement
**Tóm tắt yêu cầu:** Gia cố cơ chế đồng bộ Hub-Spoke, bảo toàn hiến pháp `AGENTS.md`, xử lý ghost workflows, sửa chữ ký `sync_legal_assets`, hỗ trợ `additional_bundles` và hoàn thiện Virtual Hub Fallback.

### Hành vi hiện tại (Current behavior)
1. **Lệch pha Workflow - Skill (Ghost Workflows)**: `catalog.yaml` định nghĩa `ccba-legal-advisor.md` thuộc `bundle: _core` trong khi skill `legal-advisor` thuộc `bundle: _consulting`. Khi Spoke `Phần mềm` đồng bộ, workflow được copy nhưng skill không được copy, tạo liên kết hỏng (`../skills/legal-advisor/SKILL.md` không tồn tại).
2. **Ghi đè Hiến pháp `AGENTS.md`**: `coordinator.py:257` và `coordinator.py:504` dùng `shutil.copy2` ghi đè toàn bộ `AGENTS.md`, làm mất khối cấu hình `## Agent skills` tùy biến của Spoke.
3. **Lỗi chữ ký hàm `sync_legal_assets`**: `sdk_inspector.py:261` gọi `sync_legal_assets(target_spoke=self.spoke_root, pull_latest=True)` gây `TypeError: unexpected keyword argument 'target_spoke'` (do hàm trong `ccba_legal.sync.engine` nhận `target_dir`, `doc_ids`, `source_corpus_dir`, `update_registry`, `project_root`).
4. **Thiếu parser `additional_bundles`**: `coordinator.py:620-628` chỉ trích xuất `project_type` mà bỏ qua trường `additional_bundles` trong `workspace_context.yaml`.
5. **Cơ chế Virtual Hub Fallback**: Chưa có văn bản quy chuẩn hóa việc Agent đọc trực tiếp từ `[hub_path]/.agents/skills/<skill>/SKILL.md` khi Spoke chưa copy skill về đĩa.

### Hành vi mong muốn (Desired behavior)
1. **Đồng bộ đối xứng & chuẩn hóa bundle**: Chuẩn hóa bundle của `ccba-legal-advisor.md` về `_consulting` (hoặc đảm bảo workflow chỉ sync khi skill tương ứng được phép sync), ngăn ngừa broken link.
2. **Bảo toàn khối `AGENTS.md` (Non-Destructive Section Merge)**: Tách và bảo lưu các section tùy biến của Spoke (đặc biệt là khối `## Agent skills` gồm Issue Tracker, Triage Labels, Domain Docs) khi cập nhật `AGENTS.md`.
3. **Sửa chữ ký gọi `sync_legal_assets`**: Cập nhật `sdk_inspector.py` truyền đúng các tham số `target_dir=self.spoke_root / ".md" / "legal_docs"`, `project_root=self.spoke_root`.
4. **Hỗ trợ `additional_bundles` trong YAML**: Cập nhật parser trong `coordinator.py` đọc mảng `additional_bundles` từ `workspace_context.yaml` và gộp vào `required_bundles`.
5. **Virtual Hub Fallback SOP**: Ghi nhận hướng dẫn cơ chế Virtual Hub Fallback vào quy tắc/hiến pháp để Agent đọc trực tiếp từ Hub khi file skill chưa có ở Spoke.

### Các Interface & Kiểu dữ liệu chính (Key interfaces)
- `scripts/spoke/sync/coordinator.py`:
  - `SpokeCoordinator._sync_full_bundle(...)`
  - Hàm merge section `AGENTS.md` không phá hủy
  - Trích xuất `additional_bundles: list[str]` từ `workspace_context.yaml`
- `scripts/spoke/sync/sdk_inspector.py`:
  - `SpokeInspector._sync_legal_components(...)` gọi đúng `sync_legal_assets(...)`

### Tiêu chuẩn nghiệm thu (Acceptance criteria)
- [ ] `sync_spoke.py` bảo toàn nguyên vẹn khối `## Agent skills` và các section tùy biến trong `AGENTS.md` của Spoke.
- [ ] `sdk_inspector.py` gọi `sync_legal_assets()` thành công, không gặp lỗi `TypeError`.
- [ ] Trường `additional_bundles` trong `workspace_context.yaml` được parser nạp vào danh sách bundles cần đồng bộ.
- [ ] Loại bỏ tình trạng Ghost Workflows / Broken links giữa workflow và skill.
- [ ] Bổ sung/cập nhật unit tests cho merge `AGENTS.md`, parse `additional_bundles` và đồng bộ legal assets; toàn bộ test suite pass 100%.

### Phạm vi loại trừ (Out of scope)
- Không can thiệp vào cơ chế bảo mật khóa ký số của Spoke Registry (đã hoàn thiện ở ADR 0048).
- Không tự ý commit hay push trực tiếp vào branch `main` của Hub ngoài quy trình Pull Request.
