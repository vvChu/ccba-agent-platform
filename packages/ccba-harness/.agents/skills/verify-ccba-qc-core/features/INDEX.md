# Feature Registry — `verify-ccba-qc-core`

| ID | Tính Năng / Hợp Đồng Seam | Thành Phần Nguồn | Ca Kiểm Thử | Trạng Thái |
| :--- | :--- | :--- | :--- | :--- |
| `FEAT-QCC-001` | PEP 562 `_LAZY_EXPORTS` (`14` symbols), `__all__` & `__dir__` Parity | `ccba_qc_core.__init__` | `test_feat_qcc_001_lazy_exports_and_dir_parity` | `stable` |
| `FEAT-QCC-002` | `PcccJurisdictionRouter` Dual-Pathway Routing (`C07` Escalation `bug_path_4`, `PC07`, `CQCMVXD`, & `PC13` Self-Appraisal `bug_path_3`) | `ccba_qc_core.jurisdiction` | `test_feat_qcc_002_pccc_jurisdiction_routing_and_escalation` | `stable` |
| `FEAT-QCC-003` | `DiscoveryEngine` (`SheetEntry`, `ProjectBackbone`, `find_index_pages` & Missing PDF `bug_path_1`) | `ccba_qc_core.discovery` | `test_feat_qcc_003_discovery_engine_and_missing_pdf_bug_path_1` | `stable` |
| `FEAT-QCC-004` | `QCBatchOrchestrator` (`find_page_in_dir`, `render_page`, `blank.png` Fallback `bug_path_2` & Missing Matrix Guard) | `ccba_qc_core.pipeline` | `test_feat_qcc_004_batch_orchestrator_blank_fallback_bug_path_2` | `stable` |
| `FEAT-QCC-005` | Statechart Anti-Lie, `bug_path` Parity & `ReporterEngine.synthesize` Markdown + JSON Export | `ccba_qc_core.reporter` / `verify_statechart_anti_lie` | `test_feat_qcc_005_statechart_anti_lie_and_reporter_synthesize` | `stable` |
| `FEAT-QCC-006` | Surface Diff Parity, LF SHA-256 Provenance Lock & 4-State Drift Classifier | `run_verify_qc_core.py` | `test_feat_qcc_006_surface_diff_provenance_and_drift_modes` | `stable` |
