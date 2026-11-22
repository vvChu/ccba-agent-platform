# Feature Registry — `verify-ccba-ooxml`

| ID | Tính Năng / Hợp Đồng Seam | Thành Phần Nguồn | Ca Kiểm Thử | Trạng Thái |
| :--- | :--- | :--- | :--- | :--- |
| `FEAT-OOX-001` | PEP 562 `_LAZY_EXPORTS` (`81` symbols), `__all__` & `__dir__` Parity | `ccba_ooxml.__init__` | `test_feat_oox_001_lazy_exports_and_dir_parity` | `stable` |
| `FEAT-OOX-002` | `unpack_document` Pretty-Printing, `pack_document` & `condense_xml` Comment/Whitespace Strip | `ccba_ooxml.unpack`, `pack.py` | `test_feat_oox_002_unpack_condense_and_pack_guards` | `stable` |
| `FEAT-OOX-003` | `OOXMLWorkspace` Lifecycle, Inactive `RuntimeError` (`bug_path_1`), Non-`.xlsx` Dict (`bug_path_2`) & Safe Rollback (`bug_path_3`) | `ccba_ooxml.workspace` | `test_feat_oox_003_workspace_lifecycle_and_bug_paths_1_2_3` | `stable` |
| `FEAT-OOX-004` | `TableReconstructor` (`extract_docx_tables`, Footnote, `replace_markdown_tables`, Exports) & `StructuredTable` | `ccba_ooxml.tables` | `test_feat_oox_004_table_reconstructor_slugs_and_exports` | `stable` |
| `FEAT-OOX-005` | Statechart Anti-Lie, `bug_path` Parity & Cảnh Báo / Bảo Toàn XML Hỏng Đối Xứng (`bug_path_4`) | `ccba_ooxml.unpack`, `pack.py` / `verify_statechart_anti_lie` | `test_feat_oox_005_statechart_anti_lie_and_malformed_xml_bug_path_4` | `stable` |
| `FEAT-OOX-006` | Surface Diff Parity, LF SHA-256 Provenance Lock & 4-State Drift Classifier | `run_verify_ooxml.py` | `test_feat_oox_006_surface_diff_provenance_and_drift_modes` | `stable` |
