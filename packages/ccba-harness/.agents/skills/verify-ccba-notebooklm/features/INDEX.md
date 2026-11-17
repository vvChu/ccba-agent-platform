# Feature Registry — `verify-ccba-notebooklm`

| ID | Tính Năng / Hợp Đồng Seam | Thành Phần Nguồn | Ca Kiểm Thử | Trạng Thái |
| :--- | :--- | :--- | :--- | :--- |
| `FEAT-NLM-001` | Public Deep Seams (`__all__` 15 symbols, 2-Tier Interface & Alias `NotebookLMClient`) | `ccba_notebooklm.__init__` | `test_feat_nlm_001_public_seams_and_tier_aliases` | `stable` |
| `FEAT-NLM-002` | Cổng `run_maskara_gate` (`bug_path_1` Block, Temp Redact, `bug_path_2` Bypass, `bug_path_3` Fail-Open) & `sanitize_prompt_for_query` Fail-Closed | `ccba_notebooklm._security` | `test_feat_nlm_002_maskara_gate_and_prompt_sanitization` | `stable` |
| `FEAT-NLM-003` | Chuẩn Hóa Path `normalize_to_relative`, SHA-256 Registry, `workspace_context.yaml` & Task State | `ccba_notebooklm._registry` | `test_feat_nlm_003_registry_context_routing_and_task_state` | `stable` |
| `FEAT-NLM-004` | Ngưỡng Quota $\ge 90\%$ (`check_quota_and_warn`) & Dọn Nguồn Mồ Côi (`run_garbage_collection`, `bug_path_4`) | `ccba_notebooklm._gc` | `test_feat_nlm_004_quota_guard_and_orphan_gc_bug_path_4` | `stable` |
| `FEAT-NLM-005` | Statechart Anti-Lie, `bug_path` Parity & Hậu Xử Lý `post_process_summary` Idempotent | `ccba_notebooklm._artifacts` / `verify_statechart_anti_lie` | `test_feat_nlm_005_statechart_anti_lie_and_summary_postprocess` | `stable` |
| `FEAT-NLM-006` | Surface Diff Parity, LF SHA-256 Provenance Lock & 4-State Drift Classifier | `run_verify_notebooklm.py` | `test_feat_nlm_006_surface_diff_provenance_and_drift_modes` | `stable` |
