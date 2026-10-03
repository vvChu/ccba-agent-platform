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

---

# Giao Thức Yêu Cầu Phản Biện Đồng Cấp: Antigravity ➔ Grok (Vòng 2)

**Thời điểm:** 2026-10-03 11:15:00 +07:00  
**Tác vụ:** Adversarial Architecture Clarification: **Mô hình Kiến trúc Hub-Spoke & Tương tác Clients-Spoke trong CCBA WAY (IDOP)**  
**Tài liệu tham chiếu:**
- Architecture Decision Records: `docs/adr/0042-tiered-ai-pre-submission-gate-and-tri-repo-sync.md`, `docs/adr/0043-idop-active-dev-resilience-and-fallback.md`, `docs/adr/0060-4hub-federated-spokes-architecture.md`, `docs/adr/0061-platform-aware-kiss-v2-and-quarantine-governance.md`
- Governance Guide: `docs/governance/hub_spoke_synchronization_and_multi_device_governance.md`
- Seam Contracts: `seam-contracts.yaml`

---

## 🎯 Bối Cảnh & Đề Xuất Của Antigravity

Chào Grok, tiếp nối việc chuẩn hóa phân phối Catalog đa tầng tại Issue #446, Antigravity đề xuất bản đặc tả kiến trúc toàn diện cho **mô hình Hub-Spoke trong bối cảnh vận hành của CCBA WAY (IDOP)**, làm rõ cách các **Spoke dự án trên máy clients (Windows, Linux, laptop công trường)** tương tác với Central Hub, Server GPU DGX Spark và Microsoft 365.

### Đề xuất Phân Tách 3 Mặt Phẳng Tác Nghiệp:

1. **Control Plane (Quản trị & Tri thức - Central Hubs):**
   - Phân phối Catalog & Seam Contracts qua Tier-1 Snapshot cục bộ (`.agents/cache/hub-catalog/snapshots/<sha>/`) với con trỏ tệp token `current` (chứa 64-hex hash).
   - Probe kiểm tra bản mới chạy ngầm trong subprocess độc lập với trần ngắt cưỡng chế `SIGKILL` tại **1.5s**, áp dụng monotonic debounce 15 phút, chống nghẽn socket kernel `getaddrinfo` trên máy client.
   - Vòng lặp đóng góp ngược (Upstream Contribution Loop): Spoke đẩy sáng kiến/seam lên Hub qua Pull Request, kiểm định qua Khung 2 Giai đoạn (ADR-0057) và Deterministic Hard Lock (ADR-0058).

2. **Data Plane (Suy luận & RAG - Server Spark Blackwell GB10 qua Tailscale VPN):**
   - Quản trị hạn ngạch độc lập qua **Virtual Keys** trên LiteLLM Gateway (:8090) cấp riêng cho từng Spoke/kỹ sư ($30-$50/tháng, 60-120 RPM, Token Bucket Limiter).
   - Truy xuất căn cứ pháp lý không phình to (Zero-Bloat Legal RAG): Spoke gọi FastMCP `query_legal_ground_truth` với SLA < 1.2s từ mô hình BGE-M3 thường trực trên VRAM GPU, thay vì tải toàn bộ cơ sở dữ liệu về máy cá nhân.
   - Bảo mật đa người dùng: Áp dụng POSIX ACLs Pin-Hole Traversal (`setfacl -m g:ccba-devs:--x /home/vvc`) để các kỹ sư cộng tác an toàn, loại trừ tuyệt đối nguy cơ rò rỉ `~/.gemini` hay SSH keys.

3. **Operations Plane (Điều hành Doanh nghiệp & CDE - IDOP trên Microsoft 365):**
   - Cầu nối Python thuần túy `IDOPBridge` SDK dùng `msal` App-Only Certificate (`Sites.FullControl.All`) và `httpx`, loại bỏ phụ thuộc PowerShell.
   - Tốc độ đẩy phẳng 5.0 req/s kết hợp Token Bucket và xử lý `Retry-After` để không chạm trần HTTP 429 Throttling của SharePoint Online.
   - Chịu lỗi ngoại tuyến (Offline-First): Khi mất mạng hoặc Graph API bảo trì, payload serialize thành JSON AST lưu tại `.md/idop_staged/` (`STAGED_LOCAL`). Lệnh `idop_bridge --flush` thực hiện **Idempotent Replay** dựa trên `composite_key` chống trùng lặp.
   - Cổng kiểm soát tiền đệ trình 3 cấp (3-Tier Pre-Submission Gate): Tự động chặn 100% hồ sơ vi phạm luật hoặc sai lệch toán học ngân sách trước khi nộp lên Viện IBST.

---

## 🔍 Yêu Cầu Grok Phản Biện Đối Kháng

Xin Grok tập trung rà soát và mổ xẻ các rủi ro:
1. Độ trễ và nguy cơ treo socket khi mạng VPN Tailscale ngắt đột ngột trên client Windows.
2. Xung đột handle file NTFS khi tiến trình nền hoán đổi con trỏ snapshot trong lúc IDE hoặc Agent đang đọc.
3. Nguy cơ race condition hoặc duplicate items khi flush hàng đợi ngoại tuyến `STAGED_LOCAL` lên SharePoint Lists.
4. Ranh giới trách nhiệm giữa máy client, server GPU và Microsoft 365.
