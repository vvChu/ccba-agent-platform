# Feature Registry — `verify-ccba-legal-intel`

| ID | Tính Năng / Hợp Đồng Seam | Thành Phần Nguồn | Ca Kiểm Thử | Trạng Thái |
| :--- | :--- | :--- | :--- | :--- |
| `FEAT-LEG-001` | PEP 562 `_LAZY_EXPORTS` (`148` symbols), `__all__` & `__dir__` Parity | `ccba_legal.__init__` | `test_feat_leg_001_lazy_exports_and_dir_parity` | `stable` |
| `FEAT-LEG-002` | `DynamicStatutoryResolver` / `resolve_statutory_doc` 3-Tier, Tiền Nhiệm Lịch Sử (`bug_path_2`) & Date Guard (`bug_path_1`) | `ccba_legal.currency_resolver` | `test_feat_leg_002_dynamic_statutory_resolver_and_temporal_invariance` | `stable` |
| `FEAT-LEG-003` | `LegalGroundingGate`, `verify_legal_grounding` (`[text](url)` Exclusion) & `format_grounded_response` (`bug_path_3`) | `ccba_legal.grounding` | `test_feat_leg_003_grounding_gate_citations_and_national_fallback` | `stable` |
| `FEAT-LEG-004` | `ASTParser` (`parse_markdown`, `flatten_ast`, `find_node`) & `DeltaPatch` / `DeltaPatchItem` Serialization | `ccba_legal.ast_parser` | `test_feat_leg_004_ast_parser_hierarchy_and_delta_patch_roundtrip` | `stable` |
| `FEAT-LEG-005` | Statechart Anti-Lie, `bug_path` Parity & `VBHNEngine.merge_documents` (`REPLACE`/`ABROGATE`/`SUSPEND`/`INSERT` & Skip `bug_path_4`) | `ccba_legal.vbhn_engine` / `verify_statechart_anti_lie` | `test_feat_leg_005_statechart_anti_lie_and_vbhn_merge_bug_path_4` | `stable` |
| `FEAT-LEG-006` | Surface Diff Parity, LF SHA-256 Provenance Lock & 4-State Drift Classifier | `run_verify_legal_intel.py` | `test_feat_leg_006_surface_diff_provenance_and_drift_modes` | `stable` |
