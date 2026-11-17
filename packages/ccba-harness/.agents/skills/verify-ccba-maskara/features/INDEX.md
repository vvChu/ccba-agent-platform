# Feature Registry — `verify-ccba-maskara`

| ID | Tính Năng / Hợp Đồng Seam | Thành Phần Nguồn | Ca Kiểm Thử | Trạng Thái |
| :--- | :--- | :--- | :--- | :--- |
| `FEAT-MSK-001` | Public Deep Seams (`__all__`) & Danh Mục `REGEX_PATTERNS` | `ccba_maskara.__init__`, `_rules.py` | `test_feat_msk_001_public_seams_and_rules_catalog` | `stable` |
| `FEAT-MSK-002` | Chuẩn Hóa Agent & Từ Chối Agent Lạ (`bug_path_1`) | `ccba_maskara._locator` | `test_feat_msk_002_agent_locator_and_unknown_agent_error` | `stable` |
| `FEAT-MSK-003` | Bộ Lọc An Toàn (`SAFE_STRINGS`, `_KNOWN_TOKEN_METRICS`) & Guard Tệp Bỏ Qua (`bug_path_2`) | `ccba_maskara._scanner` | `test_feat_msk_003_safe_filters_and_file_skip_guards` | `stable` |
| `FEAT-MSK-004` | Thay Thế Byte An Toàn, Backup Registry & Lọc Span Trùng (`bug_path_3`) | `ccba_maskara._redactor` | `test_feat_msk_004_redaction_backup_and_overlap_guard` | `stable` |
| `FEAT-MSK-005` | Statechart Anti-Lie, `bug_path` Parity & Live Gateway Fail-Closed Replay (`bug_path_4`) | `ccba_maskara._scanner` / `verify_statechart_anti_lie` | `test_feat_msk_005_statechart_anti_lie_and_live_bug_paths` | `stable` |
| `FEAT-MSK-006` | Surface Diff Parity, LF SHA-256 Provenance Lock & 4-State Drift Classifier | `run_verify_maskara.py` | `test_feat_msk_006_surface_diff_provenance_and_drift_modes` | `stable` |
