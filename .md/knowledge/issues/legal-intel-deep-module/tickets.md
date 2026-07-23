# Danh Sách Tickets: Refactor Seam Sâu LegalIntelPipeline

Tóm tắt: Phân rã công việc refactor gói dịch vụ `ccba-legal-intel` từ tài liệu đặc tả [spec-legal-intel-deep-module.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/specs/spec-legal-intel-deep-module.md).

👉 **Nguyên tắc:** Chỉ thực hiện các ticket nằm ở Biên giới (Frontier) - là những ticket không bị chặn hoặc tất cả blockers của nó đã ở trạng thái `[x]` hoàn thành.

---

## Ticket 1: [Pre-factoring] Build MockChromeCDP Adapter & Mock Fixtures for Offline Testing

**Bị chặn bởi:** Không có — có thể bắt đầu ngay.

**Giá trị bàn giao:** Cung cấp lớp giả lập `MockChromeCDP` và bộ dữ liệu mẫu (fixtures) giúp toàn bộ test suite và developer có thể chạy thử nghiệm quy trình cào VBPL offline hoàn toàn mà không cần bật trình duyệt Chrome thật hay có kết nối mạng.

**Tiêu chí nghiệm thu:**
- [ ] Lớp `MockChromeCDP` giả lập đầy đủ các phương thức kết nối WebSocket CDP và phản hồi dữ liệu HTML/Metadata giả định.
- [ ] Chạy Unit Test thử nghiệm `MockChromeCDP` độc lập thành công mà không phát sinh kết nối mạng thật.

---

## Ticket 2: [Core Seam] Implement LegalIntelPipeline Deep Class in ccba_legal.coordinator

**Bị chặn bởi:** Ticket 1 (`MockChromeCDP Adapter`)

**Giá trị bàn giao:** Bóc tách và đóng gói toàn bộ quy trình cào VBPL (tự động phát hiện/mở port Chrome 9222, quản lý khóa `TVPLSessionMutex`, cào dữ liệu 3 tầng, parse HTML và đóng gói OKF bundle) vào một class seam sâu duy nhất `LegalIntelPipeline` với phương thức chính `process_document(url_or_id)`.

**Tiêu chí nghiệm thu:**
- [ ] Class `LegalIntelPipeline` được định nghĩa trong `ccba_legal.coordinator` với phương thức `process_document(url_or_id, force_refresh=False) -> LegalProcessResult`.
- [ ] Tự động kích hoạt context manager `TVPLSessionMutex` để ngăn ngừa lỗi trùng lặp phiên đăng nhập VIP.
- [ ] Trả về đối tượng `LegalProcessResult` chứa đường dẫn bundle, doc_id và trạng thái xử lý.

---

## Ticket 3: [CLI Adapters] Refactor legal_intelligence.py & legal_sync.py into Thin Invocation Wrappers

**Bị chặn bởi:** Ticket 2 (`LegalIntelPipeline Deep Class`)

**Giá trị bàn giao:** Rút gọn các file script CLI (`scripts/legal_intelligence.py` và `scripts/legal_sync.py`) từ hơn 400 dòng code phức tạp xuống thành wrapper mỏng (5-10 dòng) chỉ làm nhiệm vụ parse tham số và gọi `LegalIntelPipeline().run_cli()`.

**Tiêu chí nghiệm thu:**
- [ ] `scripts/legal_intelligence.py` giữ nguyên 100% giao diện dòng lệnh (CLI options/flags) cũ.
- [ ] Mọi cuộc gọi CLI đều ủy quyền hoàn toàn cho `LegalIntelPipeline`.
- [ ] Không còn đoạn code tự quản lý port Chrome CDP hoặc format JSON thủ công rải rác ở tệp script.

---

## Ticket 4: [Verification] Add End-to-End Seam Test Suite & CI Gate Integration

**Bị chặn bởi:** Ticket 3 (`CLI Thin Adapters`)

**Giá trị bàn giao:** Xây dựng bộ test suite kiểm chứng toàn trình (end-to-end) qua seam `LegalIntelPipeline` và tích hợp vào công cụ CI Gate (`scripts/run_harness_evals.py`) để đảm bảo không xảy ra suy giảm chất lượng (regression).

**Tiêu chí nghiệm thu:**
- [ ] Thêm file test `packages/ccba-legal-intel/tests/test_legal_pipeline_seam.py`.
- [ ] Chạy thành công lệnh kiểm thử `.venv\Scripts\pytest -q packages/ccba-legal-intel/tests`.
- [ ] Chạy thành công `python scripts/run_harness_evals.py --quick` với 0 lỗi cảnh báo.
