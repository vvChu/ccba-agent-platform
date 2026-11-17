# Feature Registry — `verify-ccba-mdconverter`

| ID | Tính Năng / Hợp Đồng Seam | Thành Phần Nguồn | Ca Kiểm Thử | Trạng Thái |
| :--- | :--- | :--- | :--- | :--- |
| `FEAT-MDC-001` | PEP 562 Lazy Public Seams & Phân Cấp Lỗi `MDConvertError` | `mdconverter.__init__`, `core/exceptions.py` | `test_feat_mdc_001_lazy_seams_and_exception_hierarchy` | `stable` |
| `FEAT-MDC-002` | `ConverterRegistry` Priority Selection & `ValueError` Extension Lạ (`bug_path_2`) | `mdconverter.core.registry` | `test_feat_mdc_002_converter_registry_priority_and_unknown_extension` | `stable` |
| `FEAT-MDC-003` | `ConversionCache` Hit-Miss & Missing-File Stale-Index Replay (`bug_path_4`) | `mdconverter.core.cache` | `test_feat_mdc_003_conversion_cache_hit_miss_and_stale_index_replay` | `stable` |
| `FEAT-MDC-004` | `ConversionPipeline` Drawing `SKIPPED` Branch & `PostProcessor` Chain | `mdconverter.core.pipeline` | `test_feat_mdc_004_pipeline_skip_drawing_and_postprocessors` | `stable` |
| `FEAT-MDC-005` | Statechart Anti-Lie, `bug_path` Parity, Nested `RuntimeError` (`bug_path_1`) & Segmented `SUCCESS` With `[!ERROR]` (`bug_path_3`) | `mdconverter.core.pipeline` / `verify_statechart_anti_lie` | `test_feat_mdc_005_statechart_anti_lie_and_live_bug_paths` | `stable` |
| `FEAT-MDC-006` | Surface Diff Parity, LF SHA-256 Provenance Lock & 4-State Drift Classifier | `run_verify_mdconverter.py` | `test_feat_mdc_006_surface_diff_provenance_and_drift_modes` | `stable` |
