# Feature Registry — `verify-ccba-diagram`

| ID | Tính Năng / Hợp Đồng Seam | Thành Phần Nguồn | Ca Kiểm Thử | Trạng Thái |
| :--- | :--- | :--- | :--- | :--- |
| `FEAT-DIA-001` | Public Deep Seams (`__all__` 16 symbols) & Ergonomics `DiagramTheme` | `ccba_diagram.__init__`, `theme.py` | `test_feat_dia_001_public_seams_and_theme_defaults` | `stable` |
| `FEAT-DIA-002` | Bộ Định Tuyến `apply_smart_layout`, Xóa Tag `#layout:`, Bảo Toàn Container (`bug_path_1`) & Fallback Lạ (`bug_path_2`) | `ccba_diagram.router` | `test_feat_dia_002_router_hints_topology_and_bug_paths` | `stable` |
| `FEAT-DIA-003` | Giao Điểm Biên Hình Học (`get_shape_boundary_point`) & Chống Đảo Mũi Tên (`compute_safe_arrow_endpoints`, `bug_path_3`) | `ccba_diagram.geometry` | `test_feat_dia_003_geometry_boundary_and_overlap_clamp` | `stable` |
| `FEAT-DIA-004` | Chuẩn Hóa Biên Dương Canvas (`normalize_canvas_bounding_box`) & Đồng Bộ Text (`sync_bound_text_translation`) | `ccba_diagram.geometry` | `test_feat_dia_004_canvas_normalization_and_bound_text_sync` | `stable` |
| `FEAT-DIA-005` | Statechart Anti-Lie, `bug_path` Parity & Bảng Đặc Tả `generate_markdown_spec_table` (`bug_path_4`) | `ccba_diagram.matrix_table` / `verify_statechart_anti_lie` | `test_feat_dia_005_statechart_anti_lie_and_matrix_table` | `stable` |
| `FEAT-DIA-006` | Surface Diff Parity, LF SHA-256 Provenance Lock & 4-State Drift Classifier | `run_verify_diagram.py` | `test_feat_dia_006_surface_diff_provenance_and_drift_modes` | `stable` |
