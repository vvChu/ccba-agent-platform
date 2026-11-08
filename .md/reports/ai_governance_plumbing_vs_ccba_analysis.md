# Báo Cáo Đối Chiếu Kiến Trúc: "AI Governance is Plumbing" (`@thmslj`, Varick Agents 2026) Với Mô Hình 4-Hubs × Federated Spokes Của CCBA

> **Nguồn đối chiếu:** Bài viết *"AI Governance is plumbing"* của Thomas LJ (`@thmslj`, Head of Engineering tại Varick Agents, cựu lãnh đạo kỹ thuật tại Dropbox), xuất bản ngày 06/11/2026. Bản lưu nguyên văn tại [`.md/extracted_docs/internet/ai_governance_is_plumbing/document.md`](../extracted_docs/internet/ai_governance_is_plumbing/document.md).

---

## 1. Biên Lai Kiểm Toán Hợp Đồng Seam (`ADR-0061` Audit Receipt)

```json
{
  "status": "MATCH",
  "index_sha256": "fe4c3c11ca879eba54a8790ade072dbd98022f26bb1393585dee90149dddacfc",
  "seam_ids": [
    "maskara_scanner.v1 (ccba_maskara:MaskaraScanner)",
    "harness_eval.v1 (ccba_harness:EvalRunner)"
  ]
}
```

---

## 2. Vòng 1 (Code-First Research): Bảng Đối Chiếu 5 Chốt Chặn Kỹ Thuật & Shadow Mode

| Chốt chặn trong bài viết | Phân loại trạng thái | Hiện trạng trong Codebase (`file:line`) | Khoảng trống thực tế (Gap) |
| :--- | :--- | :--- | :--- |
| **⑴ Provisioned Accounts & Revocable Scope** | **`[Đã tồn tại]`** *(tầng LLM)*<br>**`[Cần thay đổi code hiện có]`** *(tầng M365 IDOP)* | • **Tầng LLM:** Virtual Keys theo Spoke/Role trên LiteLLM `:8090` (`spoke-idop`: 120 RPM/\$50, `dev-tta`: 30 RPM/\$15 — `docs/adr/0060-4hub-federated-spokes-architecture.md:113-120`), kết hợp `scripts/hooks/privacy.py:33-111` chặn raw secrets.<br>• **Tầng IDOP:** `BridgeConfig` (`scripts/spoke/ccba_m365_bridge.py:56-109`) mặc định `dry_run = True`, `target_env = "DEV"`. | Khi chạy `PROD` (`dry_run=False`), `M365AuthManager` (`scripts/spoke/ccba_m365_bridge.py:181-245`) dùng chung 1 App-Only Service Principal (`Sites.FullControl.All`). Hàm `IDOPBridge.flush()` (`scripts/spoke/idop_bridge.py:284-292`) đang **hardcode `"Originator": "CCBA"`** và bỏ rơi `author_email`, `seat_role`, `receipt_id` khi tạo item trên SharePoint `CDEDocuments` (`scripts/spoke/ccba_m365_bridge.py:611-622`), làm mất dấu vết định danh người/agent thực thi trên System of Record. |
| **⑵ Point-of-Action Read / Propose / Update Gate** | **`[Cần thay đổi code hiện có]`** | • Đã tách bước **Propose** (`IDOPBridge.stage()` tại `scripts/spoke/idop_bridge.py:124-195` lưu `STAGED_LOCAL` tại `.md/idop_staged/PGV-*.json`) và **Update** (`IDOPBridge.flush()` tại `scripts/spoke/idop_bridge.py:218-338`). | Dù `docs/adr/0046-personal-sandbox-lifecycle-and-charter-2026-alignment.md:27` quy định *"Direct publishing to official SharePoint CdeDocuments is strictly blocked by IDOPBridge when sandbox_mode: true"*, trong code `scripts/spoke/idop_bridge.py:218-295` **chưa có dòng lệnh nào đọc `workspace_context.yaml` để chặn `flush(dry_run=False)` khi Spoke là `personal_sandbox`**. |
| **⑶ Named Owners cho từng Action Type (Quy tắc 90/10)** | **`[Đã tồn tại]`** *(tầng Git/PR)*<br>**`[Cần thay đổi code hiện có]`** *(tầng IDOP)* | • **Tầng Git/PR:** `packages/ccba-harness/src/ccba_harness/door_policy.py:24-87` (`ADR-0067`) đã phân tách `PAVED_ROAD` (90% tự động + 10% SHA-256 sample audit tại `is_sampled_for_audit`) và `ONE_WAY_DOOR` (7 nhóm bắt buộc Taste-Holder duyệt).<br>• **Tầng IDOP:** Đã định nghĩa 11 `seat_role` và 5 cấp QC trong `ADR-0046`. | `StagedSubmittal` (`scripts/spoke/idop_bridge.py:76-104`) chưa có trường `approved_by_email` (Named Approver) và `flush()` chưa kiểm tra điều kiện phê duyệt bắt buộc khi nâng trạng thái hồ sơ lên `S2`/`S3`/`A1` (`scripts/spoke/ccba_m365_bridge.py:553`). |
| **⑷ Central Registry & Chống Agent Sprawl** | **`[Đã tồn tại — Hoàn chỉnh]`** | • `FleetTelemetryReport.get_top_spoke_innovations()` (`packages/ccba-harness/src/ccba_harness/fleet.py:114-177`) tự động phát hiện tool/skill có $\ge 5$ lượt gọi hoặc xuất hiện tại $\ge 2$ Spokes `[đo thực tế — codebase]` để đề xuất gom về Hub (`ADR-0045`).<br>• `spoke_registry.yaml` đã có `owner_email` và **60-Day TTL Sweep** đánh dấu `INACTIVE_SANDBOX` (`ADR-0046`). | **Không có khoảng trống.** Hệ thống hiện tại đã giải quyết trọn vẹn bài toán Sprawl; không cần tạo thêm registry mới. |
| **⑸ Append-Only Log (Kể cả `DENIED`) & "No log, no action"** | **`[Cần thay đổi code hiện có]`** | • Đã có pattern `append_only_logger.py` và `packages/ccba-harness/src/ccba_harness/telemetry.py:1-180`.<br>• `HookCoordinator` (`scripts/hooks/coordinator.py:42-76`) điều phối 7 lifecycle hooks trả về `exit_code` `0`/`1`/`2`. | Khi `PrivacyHook` (`scripts/hooks/privacy.py:77-82`) hoặc `ScoutBlockHook` (`scripts/hooks/scout.py:140-145`) chặn một lệnh (`exit_code == 2` / `decision == "deny"`), kết quả chỉ in ra `stderr` rồi biến mất — **không được lưu vào tệp Append-Only Audit Log** để hậu kiểm những gì Agent đã cố thực hiện nhưng bị từ chối. |
| **⑹ Shadow Mode & Decision Diff** | **`[Cần triển khai mới]`** *(nhỏ gọn trên Seam sẵn có)* | • `IDOPBridge.flush(dry_run=True)` (`scripts/spoke/idop_bridge.py:229-298`) hiện chỉ gán `status = "SYNCED_MOCK_SANDBOX"` với `DRYRUN-<uuid>` (`scripts/spoke/ccba_m365_bridge.py:638`). | Thiếu bước đối chiếu (**Shadow Diff**) giữa bản ghi `STAGED_LOCAL` do Agent đề xuất và quyết định thực tế của Chủ trì/PM trên cùng `composite_key` để chứng minh độ chính xác trước khi cấp quyền `dry_run=False`. |

---

## 3. Vòng 2 (Self-Adversarial Review): Ba Giả Định Đã Kiểm Chứng & Phản Biện

1. **Giả định 1 (Bác bỏ):** *"Cần xây dựng một Central Agent Registry mới và daemon thu hồi Spoke không hoạt động theo bài viết của Varick."*
   - **Lý do bác bỏ:** Đã có `catalog.yaml`, `seam-contracts.yaml` (`ADR-0061`), `spoke_registry.yaml` (TTL 60 ngày theo `ADR-0046`), và `get_top_spoke_innovations()` trong `packages/ccba-harness/src/ccba_harness/fleet.py:114-177`. Xây thêm Registry mới sẽ vi phạm KISS và tạo mảnh vỡ SSOT.
2. **Giả định 2 (Hiệu chỉnh theo `ADR-0054`):** *"Áp dụng 'No log, no action' (Fail-Closed) cho mọi sự kiện trong `antigravity_hook_bridge.py`."*
   - **Lý do hiệu chỉnh:** `scripts/hooks/antigravity_hook_bridge.py:174-186` tuân thủ `ADR-0054` (Fail-Open `{"decision": "allow"}` khi có lỗi bất ngờ để không làm treo IDE của kỹ sư). Do đó, chỉ áp dụng **Fail-Closed ("No log, no write")** tại điểm thực thi ghi lên hệ thống ngoài (`IDOPBridge.flush(dry_run=False)`), còn tại `HookCoordinator` thì ghi append-only các sự kiện `exit_code in (1, 2)` ở chế độ non-blocking.
3. **Giả định 3 (Kiểm chứng KISS):** *"Kiểm tra Point-of-Action Allowlist, Sandbox Cap (`ADR-0046`) và Named Approver trên `IDOPBridge` chỉ cần ~30 dòng code tại `idop_bridge.py`."*
   - **Kết quả kiểm chứng:** `scripts/spoke/idop_bridge.py` hiện có `338 LOC` `[đo thực tế — codebase]`, dưới rất xa trần `800 LOC` của `RULE-2.20`. Việc kiểm tra `workspace_context.yaml` (`sub_type == "personal_sandbox"`), kiểm tra `approved_by_email` cho `approval_status in ("S2", "S3", "A1")`, và truyền provenance metadata vào `doc_payload` hoàn toàn gói gọn trong 1 Micro-PR $\le 200$ LOC (`ADR-0067`).

---

## 4. Ba Đề Xuất Kiến Trúc Cần Thảo Luận Cùng Peer Architect (Grok)

- **Đề xuất P1 (Ưu tiên #1 — `scripts/spoke/idop_bridge.py` & `scripts/spoke/ccba_m365_bridge.py`):**
  1. Thực thi chốt chặn `ADR-0046` ngay tại runtime của `IDOPBridge.flush()`: Nếu `dry_run=False` nhưng `.md/workspace_context.yaml` của Spoke có `sub_type: "personal_sandbox"` (hoặc `is_sandbox: true`), lập tức từ chối đẩy lên SharePoint (`status = "DENIED_SANDBOX_CAP"`) và ghi vào audit log.
  2. Bổ sung trường `approved_by_email: str | None = None` vào `StagedSubmittal`; khi `approval_status in ("S2", "S3", "A1")` và `dry_run=False`, bắt buộc `approved_by_email` phải khác rỗng (Named Individual theo chốt chặn ⑶).
  3. Truyền định danh provenance (`AuthorEmail`, `SeatRole`, `ReceiptId`) vào payload của `sync_cde_document()` thay vì chỉ gán tĩnh `"Originator": "CCBA"`.
- **Đề xuất P2 (Ưu tiên #2 — `scripts/hooks/coordinator.py` & `packages/ccba-harness/src/ccba_harness/fleet.py`):**
  1. Trong `HookCoordinator.run_event()`, khi `max_code in (1, 2)` (Warning hoặc Blocked/Denied), tự động append 1 dòng JSONL vào `.system_generated/logs/governance_audit.jsonl` (đã mask qua `redact_secrets_in_text` của `ccba-maskara` để không bao giờ ghi lộ secret bị `PrivacyHook` chặn vào file log!).
  2. Trong `IDOPBridge.flush(dry_run=False)`, áp dụng nguyên tắc **"No log, no write"**: ghi bản ghi kiểm toán vào `.md/idop_staged/audit_log.jsonl` trước khi gọi HTTP `POST` lên SharePoint; nếu ghi log thất bại (ví dụ `OSError`), hủy lệnh đẩy SharePoint.
- **Đề xuất P3 (Ưu tiên #3 — Shadow Diff trong `scripts/spoke/idop_bridge.py`):**
  - Thêm hàm nhẹ `compare_shadow_decisions()` đọc các biên lai `SYNCED_MOCK_SANDBOX` trong `.md/idop_staged/` và đối chiếu với danh sách quyết định thực tế của PM/Chủ trì trên cùng `composite_key` để tính tỷ lệ lệch hành vi trước khi nâng Spoke từ Shadow Mode lên Production.


---

## 5. Phán Quyết Cuối Cùng Sau Phiên Phản Biện `/ccba-teamwork` (Cổng `RULE-4.18` & Thực Thi Micro-Patch)

Sau khi triệu tập hội đồng 3 Read-Team Subagents (`IDOP Operational Reality Auditor`, `Hooks & Telemetry Red-Team Auditor`, `Scale & Architecture Fit Auditor`) theo cổng `RULE-4.18` (*Problem-Validity, Scale & Seam-Parity Gate*), hội đồng thống nhất kết luận:

1. **Bác bỏ 85% đề xuất ăn theo bài báo Varick (`not_planned` — Chống Cargo-Culting):**
   - **Khác biệt mô hình vận hành:** Bài báo của Varick giải quyết bài toán **Unattended 24/7 ERP Background Agents** chạy lúc 2 giờ sáng tại các tập đoàn `>$1B` (`1,000–100,000` nhân viên), trong khi CCBA vận hành mô hình **Human-in-the-Loop Copilot** cho 4–15 kỹ sư tư vấn với quy trình duyệt 5 cấp QC trên SharePoint (`ADR-0060`) và cổng `ONE_WAY_DOOR` / `PAVED_ROAD` 90/10 (`ADR-0067`).
   - **Loại bỏ P3 (`compare_shadow_decisions`)**: 100% Dead Code (`0 callers`), vì `StagedSubmittal` không lưu phán quyết AI và không có pipeline kéo quyết định thật của PM về để so sánh.
   - **Loại bỏ P2.1 (`governance_audit.jsonl` trong `HookCoordinator`)**: *Category Error* (đánh đồng IDE linter như `ScoutBlockHook` / `NamingHook` với cổng chặn ERP) và tạo *Write-Only Dead Log* trùng lặp với `transcript.jsonl` (`telemetry.py`).
   - **Loại bỏ P1.3 / P2.2 (`idop_audit.jsonl`)**: Trùng lặp I/O hoàn toàn với biên nhận `.md/idop_staged/PGV-*.json` và `DeadLetterQueueManager` (`.system_generated/dlq/`).
   - **Loại bỏ P1.2 (`approved_by_email` ở JSON local)**: *Security Theater* và mâu thuẫn với kiến trúc duyệt thật trên SharePoint (`Submissions` & `ApprovalNodes` trong `test_idop_schema_compatibility.py`).

2. **Chỉ thực thi Micro-Patch vệ sinh kỹ thuật nội tại (Phương Án 2 — Đã hoàn tất & Pass `verify-patch --preset code`):**
   - **`scripts/spoke/idop_bridge.py`**:
     + Bổ sung `IDOPBridge._is_sandbox_workspace()` chặn `flush(dry_run=False)` bằng `PermissionError` khi Spoke bật `sandbox_mode: true` hoặc `sub_type: personal_sandbox` (khớp cam kết `ADR-0046:27`).
     + Truyền `item.author_email` sẵn có vào trường `Originator` (fallback về `"CCBA"`).
     + Tách nhỏ các hàm `stage()` và `flush()` để mọi hàm trong file đạt $\le 50$ LOC (`RULE-2.20`).
   - **`scripts/spoke/spoke_cli.py`**:
     + Sửa `SpokeCLI.flush(dry_run: bool | None = None)` và `--dry-run` (`default=None`) để tôn trọng mặc định `BridgeConfig.dry_run = True`, tránh gán nhầm trạng thái `SYNCED_SHAREPOINT` khi chạy dry-run.
     + Tách nhỏ các hàm `status()`, `stage()`, `_build_arg_parser()` để mọi hàm đạt $\le 50$ LOC (`RULE-2.20`).
   - **`tests/spoke/test_idop_bridge.py`**:
     + Bổ sung `test_idop_bridge_sandbox_mode_guard_blocks_live_flush` và kiểm chứng `Originator` + `SYNCED_MOCK_SANDBOX` trong `test_spoke_cli_stage_and_flush`.
