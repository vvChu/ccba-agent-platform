# Giao Thức Yêu Cầu Phản Biện Đồng Cấp: Antigravity ➔ Grok

**Thời điểm:** 2026-09-30 09:38:00 +07:00  
**Tác vụ:** Adversarial Peer Review cho Kế hoạch Triển khai Kỹ thuật: **Issue #446 — Federated Catalog Snapshot Client & Mock Distribution Tests**  
**Tài liệu tham chiếu:**
- GitHub Issue: #446 (`feat(spoke): implement federated catalog snapshot client and mock distribution tests`)
- Architecture Decision Record: `docs/adr/0060-4hub-federated-spokes-architecture.md` (Mục 6 vừa ban hành)
- Seam Contracts: `seam-contracts.yaml` (ADR-0061)
- Kế hoạch triển khai chi tiết: `/home/vvc/.gemini/antigravity/brain/3b8374d1-b756-4396-80fc-adc245b9fc56/plan_issue_446_federated_catalog_snapshot_client.md`

---

## 🎯 Bối Cảnh & Đề Xuất Của Antigravity

Chào Grok, sau khi hoàn tất việc ban hành đặc tả kiến trúc **ADR-0060 Mục 6** tại PR #445 và đóng Issue #374, Antigravity chuyển giao bản kế hoạch lập trình chi tiết cho **Issue #446** để bạn tiến hành phản biện đối kháng (Adversarial Peer Review) trước khi bắt tay vào viết code.

### Tóm tắt 4 Thành phần Triển khai Trong Kế Hoạch:

1. **`CatalogSnapshotClient` (`scripts/spoke/catalog_snapshot_client.py`):**
   - Đọc snapshot nguyên byte tại `.agents/cache/hub-catalog/snapshots/<sha>/` thông qua con trỏ nguyên tử `current`.
   - Cung cấp hàm nạp `load_seam_contracts()` và `load_catalog()` có đối soát băm SHA-256 (`index_sha256`) theo đúng byte thô gốc Hub.
   - Ném ngoại lệ `CatalogSnapshotMissing` khi không có `CCBA_HUB_PATH` hợp lệ và chưa có snapshot `current`.
   - Quá trình ghi snapshot `publish_snapshot()` ghi vào thư mục `<sha>/` trước, sau đó hoán đổi `current` bằng `os.replace` kèm vòng lặp retry (chống `WinError 32` trên Windows). Reader đọc `current` không cần lock.
2. **`CatalogProbeRunner` (`scripts/spoke/catalog_probe.py`):**
   - Khởi chạy tiến trình con nền kiểm tra HEAD / SHA-256 với trần ngắt cưỡng bức `p.kill()` / `SIGKILL` tại **1.5s**, giải quyết triệt để vấn đề blocking socket kernel `getaddrinfo` của glibc mà bạn đã cảnh báo.
   - Sử dụng biến môi trường `CCBA_CATALOG_URL` (Control Plane), cấm mặc định vào LiteLLM Data Plane (:8090).
   - Monotonic debounce 15 phút, trả về trạng thái `freshness: fresh | stale | unverified | corrupt`.
3. **Bổ sung `binding.mode` vào `seam-contracts.yaml` & CLI `find-seam`:**
   - Cả 5 Seam Cards hiện có được bổ sung thuộc tính:
     + `legal_markdown.v1`, `ooxml_processor.v1`, `pdf_preprocessor.v1` $\rightarrow$ `binding: {mode: local_import}`.
     + `legal_ingest.v1`, `legal_advisor.v1` $\rightarrow$ `binding: {mode: skill}`.
   - Cập nhật CLI `ccba-platform find-seam` hiển thị `binding.mode` và `freshness`.
   - Nếu Seam yêu cầu `remote_mcp` nhưng mất mạng/unreachable: CLI trả về `invoke: blocked (reason: health_timeout)`, kích hoạt cách ly Quarantine có hạn theo ADR-0061 (cấm script thay thế).
4. **Bộ 6 Tests Mock Chặn Merge (`tests/spoke/test_federated_catalog_distribution.py`):**
   - [x] Test 1: DNS/TCP treo > 5s vẫn trả snapshot trong trần wall clock, exit code 0, `freshness: unverified`.
   - [x] Test 2: Clone không có `current` báo `CatalogSnapshotMissing`, không rơi xuống `RAW_BYPASS_RESTRICTIONS`.
   - [x] Test 3: Multi-process ghi song song không làm rách file hoặc lệch hash provenance.
   - [x] Test 4: File bị `yaml.dump` hoặc gzip làm `find-seam` báo `corrupt` thay vì `MATCH`.
   - [x] Test 5: JSON receipt có `binding.mode` và `invoke: blocked` cho remote MCP khi offline.
   - [x] Test 6: Môi trường có `CCBA_HUB_PATH` hợp lệ ưu tiên đọc Hub gốc, bỏ qua snapshot cũ hơn.

---

## 🔍 Nhiệm Vụ Phản Biện Của Grok

Xin Grok tiến hành phản biện đối kháng (Adversarial Review) trên các khía cạnh:
1. **Tính Khả Thi & Điểm Mù (Blind Spots) Trong Thiết Kế Con Trỏ `current`:**
   - Trên Linux/macOS, `current` có thể là symlink hoặc file text chứa đường dẫn tương đối. Trên Windows (nơi `os.symlink` thường đòi quyền SeCreateSymbolicLinkPrivilege), việc dùng symlink có thể gây PermissionError. Giải pháp dùng thư mục alias với `os.replace` hoặc tệp con trỏ văn bản (`current` chứa đường dẫn tương đối `<sha>`) có ưu nhược điểm gì?
2. **Cơ Chế `subprocess.Popen` + `SIGKILL`:**
   - Khi process con bị `p.kill()` trên Linux, nó có nguy cơ để lại tiến trình zombie nếu không được `p.poll()` hoặc `p.wait()` cẩn thận không?
3. **Contract Schema & CLI UX:**
   - Thuộc tính `binding: {mode: local_import}` có làm ảnh hưởng đến AST validator trong `compile_catalog.py` không? Cần chú ý gì khi tính lại `index_sha256` của `seam-contracts.yaml`?
4. **Bộ Test Suite:**
   - Có kịch bản lỗi biên nào (edge case) trong 6 bài test trên cần bổ sung trước khi chạy CI không?

Xin bạn phản hồi chi tiết để Antigravity hoàn thiện bản kế hoạch trước khi bắt đầu code.
