# Feature Registry — `verify-ccba-pdf-prep`

| ID | Tính Năng / Hợp Đồng Seam | Thành Phần Nguồn | Ca Kiểm Thử | Trạng Thái |
| :--- | :--- | :--- | :--- | :--- |
| `FEAT-PDF-001` | Public Deep Seams (`__all__`) & Kiểu DTOs (`PDFReport`, `Segment`, `PDFCategory`) | `ccba_pdf_prep.__init__`, `core.py` | `test_feat_pdf_001_public_seams_and_dtos` | `stable` |
| `FEAT-PDF-002` | Phân Nhóm Đoạn Trang (`get_segments`) & Luật `should_skip` (`DRAWING`) | `ccba_pdf_prep.core` | `test_feat_pdf_002_report_segments_and_skip_contract` | `stable` |
| `FEAT-PDF-003` | Khởi Tạo Pipeline & Lỗi Mất/Hỏng Tệp PDF (`bug_path_1`) | `ccba_pdf_prep.pipeline` | `test_feat_pdf_003_missing_pdf_and_analyzer_failure` | `stable` |
| `FEAT-PDF-004` | Chiến Lược Bản Vẽ: Tiling Lỗi (`bug_path_2`) & Suy Giảm Khung Tên/Composite (`bug_path_3`) | `ccba_pdf_prep.pipeline`, `vision.py`, `detector.py` | `test_feat_pdf_004_drawing_tiling_and_degraded_branches` | `stable` |
| `FEAT-PDF-005` | Statechart Anti-Lie, `bug_path` Parity & Live `UNKNOWN`/`TEXT_RICH` Replay (`bug_path_4`) | `ccba_pdf_prep.pipeline` / `verify_statechart_anti_lie` | `test_feat_pdf_005_statechart_anti_lie_and_live_bug_paths` | `stable` |
| `FEAT-PDF-006` | Surface Diff Parity, LF SHA-256 Provenance Lock & 4-State Drift Classifier | `run_verify_pdf_prep.py` | `test_feat_pdf_006_surface_diff_provenance_and_drift_modes` | `stable` |
