# 🎫 Danh Sách Tickets: Refactor Seam Sâu LegalIntelPipeline

Tóm tắt: Phân rã công việc refactor gói dịch vụ `ccba-legal-intel` từ tài liệu đặc tả [spec-legal-intel-deep-module.md](../../specs/spec-legal-intel-deep-module.md) và kết quả Brainstorming [brainstorm_session_legal_intel_eval.md](file:///C:/Users/chuvu/.gemini/antigravity/brain/0c0a9304-cfbb-4fa3-9c81-3e11441ace97/brainstorm_session_legal_intel_eval.md).

👉 **Nguyên tắc:** Chỉ thực hiện các ticket nằm ở Biên giới (Frontier) - là những ticket không bị chặn hoặc tất cả blockers của nó đã ở trạng thái `[x]` hoàn thành.

---

## Ticket 1: [Pre-factoring] Build MockChromeCDP Adapter & Mock Fixtures for Offline Testing

**Bị chặn bởi:** Không có — có thể bắt đầu ngay `[UNBLOCKED]` `[AFK]`.

**Giá trị bàn giao:** Cung cấp lớp giả lập `MockChromeCDP` và bộ dữ liệu mẫu (fixtures) giúp toàn bộ test suite và developer có thể chạy thử nghiệm quy trình cào VBPL offline hoàn toàn mà không cần bật trình duyệt Chrome thật hay có kết nối mạng.

**Tiêu chí nghiệm thu:**
- [ ] Lớp `MockChromeCDP` giả lập đầy đủ các phương thức kết nối WebSocket CDP và phản hồi dữ liệu HTML/Metadata giả định.
- [ ] Chạy Unit Test thử nghiệm `MockChromeCDP` độc lập thành công mà không phát sinh kết nối mạng thật.

---

## Ticket 2: [Core Seam] Implement LegalIntelPipeline Deep Class in ccba_legal.coordinator

**Bị chặn bởi:** Ticket 1 (`MockChromeCDP Adapter`) `[DONE]`

**Giá trị bàn giao:** Bóc tách và đóng gói toàn bộ quy trình cào VBPL (tự động phát hiện/mở port Chrome 9222, lắng nghe DOM/Network ready thay cho hardcoded sleep, quản lý khóa `TVPLSessionMutex`, cào dữ liệu 3 tầng, parse HTML và đóng gói OKF bundle) vào một class seam sâu duy nhất `LegalIntelPipeline` với phương thức chính `process_document(url_or_id)`.

**Tiêu chí nghiệm thu:**
- [x] Class `LegalIntelPipeline` được định nghĩa trong `ccba_legal.coordinator` với phương thức `process_document(url_or_id, force_refresh=False) -> LegalProcessResult`.
- [x] Tự động phát hiện & auto-launch Chrome CDP port 9222 qua `ensure_chrome_cdp_port()` nếu chưa chạy.
- [x] Tự động kích hoạt context manager `TVPLSessionMutex` để ngăn ngừa lỗi trùng lặp phiên đăng nhập VIP.
- [x] Trả về đối tượng `LegalProcessResult` chứa đường dẫn bundle, doc_id và trạng thái xử lý.

---

## Ticket 3: [Performance] Integrate Subagent ccba-research Offloading & SHA-256 Delta Caching

**Bị chặn bởi:** Ticket 2 (`LegalIntelPipeline Deep Class`) `[DONE]`

**Giá trị bàn giao:** Tích hợp cơ chế tự động phân rã nhiệm vụ cào VBPL dung lượng lớn (> 100 trang) cho Subagent `ccba-research` chạy ngầm, áp dụng SHA-256 doc caching và cào Delta chênh lệch dựa trên đồ thị Lược đồ TVPL.

**Tiêu chí nghiệm thu:**
- [x] Tự động phát hiện URL/Văn bản kích thước lớn và đề xuất delegate sang `ccba-research`.
- [x] So sánh SHA-256 tệp trước khi tải lại, bỏ qua các văn bản trùng lặp đã tồn tại trong local registry (`status="cached"`).

---

## Ticket 4: [CLI Adapters] Refactor legal_intelligence.py & legal_sync.py into Thin Invocation Wrappers

**Bị chặn bởi:** Ticket 3 (`Async Offloading & Delta Caching`) `[DONE]`

**Giá trị bàn giao:** Rút gọn các file script CLI (`scripts/legal_intelligence.py` và `scripts/legal_sync.py`) từ hơn 400 dòng code phức tạp xuống thành wrapper mỏng (5-10 dòng) chỉ làm nhiệm vụ parse tham số và gọi `LegalIntelPipeline().run_cli()`.

**Tiêu chí nghiệm thu:**
- [x] `scripts/legal_intelligence.py` giữ nguyên 100% giao diện dòng lệnh (CLI options/flags) cũ.
- [x] Mọi cuộc gọi CLI đều ủy quyền hoàn toàn cho `LegalIntelPipeline`.
- [x] Support positional target URLs, `--async`, `--json`, `--download-source`, `--extract-related`.

---

## Ticket 5: [Verification] Add End-to-End Seam Test Suite & CI Gate Integration

**Bị chặn bởi:** Ticket 4 (`CLI Thin Adapters`) `[DONE]`

**Giá trị bàn giao:** Xây dựng bộ test suite kiểm chứng toàn trình (end-to-end) qua seam `LegalIntelPipeline` và xác nhận 100% test cases pass để đảm bảo không xảy ra suy giảm chất lượng (regression).

**Tiêu chí nghiệm thu:**
- [x] Chạy thành công toàn bộ test suite seam `test_legal_pipeline_seam.py` và `test_mock_cdp.py` (13/13 passed).
- [x] Đã chạy `python scripts/update_arch_stats.py` để đồng bộ số liệu kiến trúc.
- [x] Xác nhận 0 lỗi lặp lại.

---
*Tạo bởi CCBA Ticket Manager*
