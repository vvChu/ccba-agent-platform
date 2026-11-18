# 🎫 WF-03: Làm sâu Seam Phân giải Workspace & Hub Root (resolve_workspace_and_hub_roots) cho ccba_legal, ccba_harness và scripts/spoke

> **Thuộc bản đồ:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../map.md)  
> **Loại ticket:** `Task [AFK]`  
> **Trạng thái:** `CLOSED` *(Hoàn tất `2026-11-18` — PR `#804` (`PR-1a`) + PR `#805` (`PR-1b`), `import ccba_harness` `6.10 ms` `[đo thực tế]`)*  
> **Assignee:** `AI Platform Architect`  
> **Phụ thuộc:** Mở khóa [WF-04: Làm sâu Seam Che giấu Secret & PII Việt Nam (ccba_maskara) và Hợp nhất 3 Bộ Quét Phân kỳ](wf_04_unify_maskara_secret_and_pii_seam.md) và tham gia mở khóa [WF-06: Kiểm định Liên thông 4 Cổng ADR-0058, Đồng bộ Catalog/Docs SSOT & Đóng Bản đồ Wayfinder](wf_06_ci_verification_and_wayfinder_rollup.md)

---

## 1. Phạm vi Kỹ thuật (Ứng viên #1)

Triển khai theo đúng phương án đã khóa tại [WF-01: Phản biện & Chốt Thiết kế Chi tiết cho 3 Ứng viên Kiến trúc (Workspace/Hub Root Seam, Maskara Redaction Seam, OOXMLValidator Seam)](wf_01_grilling_architecture_design_lock.md) và đã duyệt tại [WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)](wf_02_peer_plan_audit_gate.md):

1. **Dựng Deep Seam thuần stdlib tại `ccba_harness`:**
   - Thêm module chứa `WorkspaceHubContext` và `resolve_workspace_and_hub_roots(start_dir: Path | None = None, ...) -> WorkspaceHubContext` (thuần stdlib, nạp `yaml` tùy chọn theo quyết định `Q2` của `WF-01`).
   - Đăng ký public symbol vào `_LAZY_EXPORTS` (`ast.Assign`, không type annotation) và `__all__` tại [ccba_harness/__init__.py](../../../../packages/ccba-harness/src/ccba_harness/__init__.py) đúng hợp đồng PEP 562 (`check_init_lazy_exports_parity`).
   - Triển khai module thuần stdlib `_workspace_roots.py` (`<= 250 LOC`, optional `yaml` + fallback parser), đồng bộ sang `scripts/_guardrails/_workspace_roots.py` cho tầng Spoke Tier-0; mở rộng `_LAZY_EXPORTS` (`ast.Assign`) cho `WorkspaceHubContext` và `resolve_workspace_and_hub_roots`.
   - Cấu hình `include_agents_md=False` ở shared walker (không dừng ở `AGENTS.md`), bỏ qua `packages/<pkg>/pyproject.toml` nội bộ khi ancestor có `seam-contracts.yaml`, bỏ fallback `parents[5]`, đọc `os.environ` động (không cache lúc import), và chỉ gọi `wslpath` khi binary tồn tại + có ổ đĩa Windows.
   - Giữ chi phí `import ccba_harness` &lt; `15 ms` (`8.22 ms` nền tảng `[đo thực tế]`) và tuân thủ `RULE-2.9` (`is_ephemeral_spoke_path` / `is_protected_hub_root`).
2. **Chuyển `10` điểm phân giải phân kỳ trực tiếp thành Thin Adapters tương thích ngược `100%` (tường minh `start_dir`):**
   - `ccba_legal`: [registry.py](../../../../packages/ccba-legal-intel/src/ccba_legal/registry.py#L27-L145) (`resolve_project_root` dùng `start_dir=Path(__file__).resolve()`; `discover_master_registry_path` kiểm tra `Path.cwd()` trước `L85` `resolve_project_root()`), [engine.py](../../../../packages/ccba-legal-intel/src/ccba_legal/sync/engine.py#L188-L285) (`start_dir=Path(cwd)`). Giữ **byte-y nguyên** `_discover_currency_card_path()` tại [currency_resolver.py](../../../../packages/ccba-legal-intel/src/ccba_legal/currency_resolver.py#L251-L277) để không chạm `covered_paths` của `verify-ccba-legal-intel`.
   - `ccba_harness` (import trực tiếp `ccba_harness._workspace_roots`): [peer.py](../../../../packages/ccba-harness/src/ccba_harness/cli/commands/peer.py#L17-L29) (`Path.cwd()`), [_daemon_reporting.py](../../../../packages/ccba-harness/src/ccba_harness/evals/_daemon_reporting.py#L57-L67) (`cwd`), [daemon.py](../../../../packages/ccba-harness/src/ccba_harness/evals/daemon.py#L88-L121) (`cwd`), [_miner_catalog.py](../../../../packages/ccba-harness/src/ccba_harness/evals/_miner_catalog.py#L359-L379) (`cwd`), [runner.py](../../../../packages/ccba-harness/src/ccba_harness/evals/runner.py#L360-L368) (`cwd`), [tuner.py](../../../../packages/ccba-harness/src/ccba_harness/evals/tuner.py#L129-L139) (`cwd`).
   - `scripts/spoke`: [spoke_bootstrap.py](../../../../scripts/spoke/spoke_bootstrap.py#L354-L404) (`start_dir=target_dir`) và [check_hub_import_depth.py](../../../../scripts/spoke/check_hub_import_depth.py#L45-L105) (`start_dir=root`) dùng chung `scripts/_guardrails/_workspace_roots.py` làm fallback Tier-0 khi Spoke chưa cài `ccba_harness`.
3. **Kiểm thử & Không rò rỉ phạm vi SHA-256 (`COND-SHA-SCOPE`):**
   - Viết unit tests cho kịch bản Delivery Spoke chỉ có `.md/workspace_context.yaml` (không có `.git`), `CCBA_HUB_PATH` đa thiết bị, đường dẫn Windows qua `wslpath`, và kiểm tra parity giữa `_workspace_roots.py` trong `ccba_harness` với `scripts/_guardrails/_workspace_roots.py`.
   - Vì `_discover_currency_card_path()` giữ nguyên (`verify-ccba-legal-intel` không bị chạm) và `PR-1a`/`PR-1b` không sửa tệp trong `covered_paths` của `verify-ccba-harness`, không thực hiện cập nhật `covered_sha256` ở `PR-1a`/`PR-1b` (chỉ chạy pytest + `verify-patch --preset code`).

## 2. Tiêu chí Hoàn thành (Completion Criteria)

- [x] Tự gán `Assignee` trên ticket trước khi thực thi.
- [x] `ccba_legal.registry.resolve_project_root()` và `find_project_root()` trên môi trường Delivery Spoke giả lập (chỉ có `.md/workspace_context.yaml`, không có `.git`) trả về đúng root của Spoke thay vì `packages/ccba-legal-intel` hoặc Hub root `[đo thực tế]`.
- [x] Mọi hàm <= `50 LOC`, mọi module chạm vào <= `800 LOC` (ngoại trừ phần còn lại của `registry.py` ghi nhận sang `[FOG-003]`, thu gọn `1260 -> 1242 LOC`).
- [x] `check_dependency_contracts.py` đạt `0` vi phạm (`519` files scanned, bao gồm `check_init_lazy_exports_parity`).
- [x] `python -m ccba_harness verify-patch --preset code --target packages/ccba-harness` và `--target packages/ccba-legal-intel` cùng `pytest` trên `scripts/tests/` đạt exit `0`.
- [x] Cập nhật kết quả vào [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../map.md), đóng ticket `WF-03` (`CLOSED`) và mở khóa [WF-04: Làm sâu Seam Che giấu Secret & PII Việt Nam (ccba_maskara) và Hợp nhất 3 Bộ Quét Phân kỳ](wf_04_unify_maskara_secret_and_pii_seam.md).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
