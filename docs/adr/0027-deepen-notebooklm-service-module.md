# ADR 0027: Deepen NotebookLMService Module & Separate Service Layer

- **Status:** Accepted
- **Date:** 2026-08-13
- **Context:** Package `ccba-notebooklm` có 3 hàm (`get_source_id_by_path`, `extract_and_summarize`, `query_rag`) tại `_artifacts.py` tự lặp lại ~120 dòng code xử lý SHA-256 hash, registry lookup, xóa nguồn cũ khi mismatch, quét Maskara security gate và upload nguồn mới. Ngoài ra tồn tại 2 bug ẩn: `extract_and_summarize` gọi Maskara Gate trước khi check cache registry (lãng phí I/O), còn `query_rag` bỏ sót SHA-256 mismatch detection (silently dùng lại source cũ khi file đổi).

## Decisions

1. **Dedicated Service Module (`_service.py`):**
   Tạo module `_service.py` độc lập chứa class `NotebookLMService`, bọc `CCBANotebookLMClient` qua composition. Giữ `_client.py` là lớp bọc RPC mỏng nhằm tránh lỗi vi phạm phân tầng (Layer Violation).

2. **Fix 2 Hidden Behavioral Bugs in `ensure_source()`:**
   Chuẩn hóa phương thức `NotebookLMService.ensure_source()` sử dụng **Lazy Maskara Gate** (chỉ quét khi thực sự cần upload) và **Luôn kiểm tra SHA-256 mismatch** (tự động xóa nguồn cũ và re-upload khi file local thay đổi).

3. **TDD Discipline & Characterization Tests:**
   Viết bộ unit test mới `tests/test_service.py` trước khi refactor `_artifacts.py` nhằm đảm bảo tính tương thích ngược 100% của các top-level facade functions.

## Consequences

- Triệt tiêu hoàn toàn code duplication giữa 3 workflow functions.
- Sửa dứt điểm 2 bug ẩn về hiệu năng I/O và tính chính xác của dữ liệu RAG.
- Giữ nguyên 100% API tương thích ngược tại `__init__.py`.
