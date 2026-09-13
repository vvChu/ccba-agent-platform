# 🛡️ Walkthrough: Issue #268 — Harden Spoke Sync & Decouple Archetype from Registry Timestamp

## 1. Executive Summary

Issue #268 resolves 4 foundational architectural and ergonomic bottlenecks in the CCBA Hub-Spoke synchronization subsystem:
1. **SDK Inspector Domain Decoupling (ADR-0044 & ADR-0050)**: Prevents inappropriate package recommendations (`ccba-qc-core`, `ccba-ooxml`, `ccba-pdf-prep`) for `knowledge_corpus` spokes and categorizes recommendations by functional domain rather than a misleading generic label.
2. **Post-Sync Verification Seam (ADR-0058)**: Discovers test suites across candidate directories (`tests`, `scripts/tests`, `src/tests`, or `verification.test_path` in `workspace_context.yaml`) and executes tests within the Spoke's virtual environment (`.venv/Scripts/python.exe`) rather than the Hub's Python interpreter.
3. **Archetype Taxonomy Preservation (ADR-0041 §3)**: Stops collapsing `knowledge_corpus` spokes into `"Tác vụ Admin"`. Propagates `archetype` across `workspace_context.yaml`, `SpokeRegistrar`, `LegalKnowledgeSyncOrchestrator`, and `scripts/ccba_platform_cli.py`.
4. **Static Registry & Dynamic Heartbeat Decoupling (ADR-0046)**: Computes a `static_hash` of spoke metadata. If unchanged, skips RSA re-encryption on `--apply`, eliminating perpetual Git working-tree churn in `.md/data/spoke_registry.yaml`. Records `last_sync` timestamps to gitignored `.md/telemetry/spoke_heartbeats.yaml`.

---

## 2. Changes Made by Component

| Component / File | Changes & Rationale |
| :--- | :--- |
| [`scripts/spoke/sync/sdk_inspector.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/spoke/sync/sdk_inspector.py) | - Extracted `is_legal_related_spoke()` helper.<br/>- Implemented tiered resolution in `resolve_packages_to_check()` (Tier 0: `ccba-harness`, `ccba-ai`; Tier 1: archetype defaults; Tier 2: `hub_packages`).<br/>- Added `get_categorized_recommendations()` for domain grouping while keeping `get_recommendations()` for backward compatibility.<br/>- Updated `LegalKnowledgeSyncOrchestrator` to prioritize `archetype or project_type`.<br/>- Applied whitespace trimming on `hub_packages` entries. |
| [`scripts/spoke/sync/__init__.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/spoke/sync/__init__.py) | - Exported `is_legal_related_spoke`. |
| [`scripts/spoke/spoke_bootstrap.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/spoke/spoke_bootstrap.py) | - Updated `resolve_target_packages()` to only inject `ccba-legal-intel` for `knowledge_corpus` if `is_legal_related_spoke` is True. |
| [`scripts/spoke/sync/coordinator.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/spoke/sync/coordinator.py) | - Propagated `spoke_archetype` from `workspace_context.yaml` down to `_sync_full_bundle`, `SpokeRegistrar().register()`, and `LegalKnowledgeSyncOrchestrator`.<br/>- Displayed categorized recommendations with domain headers in terminal output.<br/>- Updated `verify_spoke` to discover Spoke venv Python (`SpokeBootstrapper`) and verify `pytest` execution.<br/>- Extended test discovery across candidate directories (`tests`, `scripts/tests`, `src/tests`) or custom `verification.test_path`.<br/>- Safe-checked `workspace_context.yaml` existence before calling `load_yaml`.<br/>- Decoupled `project_type` extraction from `archetype` fallback, using explicit `archetype_to_project_type` mapping only when `project_type` is omitted. |
| [`scripts/spoke/sync/registry.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/spoke/sync/registry.py) | - Updated `build_spoke_info()` and `register()` to accept `archetype: str = ""` and persist `"archetype"`.<br/>- Decoupled `last_sync` from static `spoke_info` to eliminate unnecessary re-encryption.<br/>- Implemented `static_hash` computation with SHA-256; skips RSA encryption if static hash is unchanged.<br/>- Recorded dynamic `last_sync` to `.md/telemetry/spoke_heartbeats.yaml`. |
| [`scripts/spoke/decrypt_spoke_registry.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/spoke/decrypt_spoke_registry.py) | - Added `load_spoke_heartbeats(hub_root)` helper.<br/>- Injected `last_sync` from heartbeats into decrypted spokes and preserved `archetype` with backward fallback.<br/>- Dynamically derived `spoke_id` from `path` when absent in decrypted cache for headless CI environments. |
| [`scripts/ccba_platform_cli.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/ccba_platform_cli.py) | - Updated Spoke Health Dashboard to prioritize `archetype` over generic `project_type`. |
| [`scripts/tests/test_spoke_sync_modules.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/tests/test_spoke_sync_modules.py) | - Added 5 comprehensive test cases covering tier resolution, categorized recommendations, multi-directory test discovery in venv, static hash registry decoupling, and dynamic telemetry heartbeats. |

---

## 3. Verification Results

### 3.1 Scoped Unit & Integration Tests
Ran `scripts/tests/test_spoke_sync_modules.py` and all related spoke suites:
- **`scripts/tests/test_spoke_sync_modules.py`**: **34/34 PASSED** (including `test_verify_spoke_multi_dir_and_venv` and `test_registry_static_hash_and_heartbeat_decoupling`).
- **Spoke Suite Total**: **100/100 PASSED** across:
  - `tests/test_spoke_sdk_detector.py`
  - `tests/test_sandbox_registry_ttl.py`
  - `tests/test_delivery_spoke_setup.py`
  - `tests/test_spoke_batch_sync.py`
  - `tests/test_archetype_lifecycle_matrix.py`
  - `tests/test_sandbox_auditor.py`
  - `tests/test_sandbox_promoter.py`
  - `tests/test_spoke_cli.py`

### 3.2 Ruff & Linting Parity
```powershell
python -m ruff check scripts/spoke/sync/ scripts/spoke/spoke_bootstrap.py scripts/spoke/decrypt_spoke_registry.py scripts/ccba_platform_cli.py scripts/tests/test_spoke_sync_modules.py
# Result: All checks passed!
```

### 3.3 ADR-0058 Hard Completion Lock
Executed via `ccba-harness verify-patch`:
```text
# 🛡️ Deterministic Patch Verification Report: ✅ ALL PASSED

- Overall Status: PASS
- Commands Executed: 2/2 passed
- Total Duration: 10850.0 ms

| Status | Exit Code | Duration | Command |
| :---: | :---: | :---: | :--- |
| PASS | 0 | 162.4ms | `python -m ruff check ...` |
| PASS | 0 | 10687.6ms | `python -m pytest scripts/tests/test_spoke_sync_modules.py ... -q` |
```

### 3.4 GitHub Actions Dual-Gate CI Status
- **Run ID**: `34727974436` (CI), `34727974441` (Documentation), `34727974440` (Security & Privacy)
- **Status**: 100% GREEN (Python 3.10, 3.11, 3.12, Markdown Lint, CodeQL, Skills & Catalog Gate all passed).

---

## 4. Copilot Review Auditing & Remediation (Dual-Gate CI Cổng 2)

### Review `PRR_kwDOQzfV088AAAABNUV-mQ`
- **Góp ý từ Copilot**: `sync_spoke_bundle()` still falls back to using `archetype` as `project_type`, which can re-couple bundle selection to archetype and contradicts the intended decoupling in this PR.
- **Xử lý & Khắc phục** (Commit `4fe6d3d0`):
  - Loại bỏ việc gán trực tiếp chuỗi `archetype` vào biến `project_type` trong `scripts/spoke/sync/coordinator.py`.
  - Thiết lập bảng ánh xạ rõ ràng `archetype_to_project_type` (`knowledge_corpus` -> `"Tác vụ Admin"`, `project_delivery` -> `"Thẩm tra thiết kế"`...), đảm bảo `project_type` luôn là loại hình hợp lệ trong `catalog.yaml` mà không làm nhập nhằng với taxonomy archetype.

### Inline Issue `3998103472`
- **Góp ý từ Copilot**: `hub_packages` values from `workspace_context.yaml` are appended without trimming whitespace. A value like `" ccba-ooxml "` will never match `hub_root / "packages" / pkg`.
- **Xử lý & Khắc phục** (Commit `4fe6d3d0`):
  - Áp dụng `.strip()` cho tất cả các phần tử trong `hub_packages` tại `scripts/spoke/sync/sdk_inspector.py` để loại bỏ khoảng trắng thừa, đảm bảo tính nhất quán với `SpokeBootstrapper`.
