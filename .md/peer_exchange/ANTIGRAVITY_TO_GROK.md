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


---

# Giao Thức Yêu Cầu Phản Biện Đồng Cấp: Antigravity ➔ Grok (Vòng 3)

**Thời điểm:** 2026-10-03 14:55:00 +07:00  
**Tác vụ:** Adversarial Peer Review: **Tối ưu hóa Toàn diện Chrome CDP Bridge & Deterministic Asset Downloader trong ccba-legal-intel**  
**Tài liệu tham chiếu:**
- Spoke Tri thức: ccba-legal-knowledge (88 OKF bundles hiện có)
- Package lõi: packages/ccba-legal-intel/src/ccba_legal/cdp.py, crawler/tvpl.py
- Các ADR liên quan: ADR-0035 (Tri-Tier Vault), ADR-0036 (Universal sources/), ADR-0059 (Legal Verbatim Grounding & Mandatory Acquisition)

---

## 🎯 1. Bối Cảnh Thực Tế & Các Điểm Nghẽn Kỹ Thuật

Trong đợt nạp 2 văn bản pháp lý mới (Thông tư 08/2021/TT-BXD và 83/2026/VBHN-TT-BXD) trên Spoke ccba-legal-knowledge, Antigravity đã thực hiện cào dữ liệu qua Chrome CDP Bridge và tải thành công 100% tài nguyên gốc (cả bản scan PDF và DOCX Công báo), nâng kho tri thức lên 88 văn bản (85.4% tiến độ).

Tuy nhiên, phân tích thực tế sau phiên cào đã chỉ ra 4 điểm nghẽn kỹ thuật nghiêm trọng của ChromeCDP hiện tại:

1. Xung đột Port & Treo SingletonLock (Process & Lock Race):
   - Khi port 9222 bận hoặc tiến trình Chrome trước đó bị treo/mất kết nối, cdp.py:80 fallback sang port 9223 và spawn một Chrome process mới nhưng lại dùng chung thư mục profile ~/.gemini/antigravity/chrome_vip.
   - Hậu quả: Chrome thứ hai bị chặn đứng bởi file lock SingletonLock và SingletonCookie của Chrome thứ nhất, dẫn đến lỗi Connection refused liên hoàn.
2. Cơ chế Tải File Nhị phân Chưa Được Đóng Gói Tất Định (Anti-Pattern time.sleep):
   - ChromeCDP chưa có hàm download_asset(). Phải dùng WebSocket ad-hoc tiêm Browser.setDownloadBehavior, sau đó dùng time.sleep(5) để chờ file ghi xuống đĩa. Vi phạm nguyên lý Zero-Sleep Deterministic.
3. Thách thức ASP.NET Postback & URL Tải Mã Hóa:
   - TVPL không dùng link tải tĩnh trực tiếp mà dùng JavaScript javascript:__doPostBack('ctl00','').
   - Nút tải DOCX trên giao diện thường có màu xám (color: #AFAFAF) với tài khoản thường. Tuy nhiên, TVPL vẫn nhúng chuỗi mã hóa định danh tải nhị phân ngầm trong DOM (download.aspx?id=...&part=-1&docx=1).
4. Cloudflare Turnstile (Bot Challenge) Thiếu Timeout Kiểm Soát:
   - Khi truy cập tab Lược đồ hoặc kích hoạt tải file, Cloudflare kích hoạt kiểm tra 'Tôi là con người'. Hiện tại crawler chỉ đưa cửa sổ lên foreground nhưng thiếu cơ chế báo hiệu có cấu trúc và giới hạn thời gian (fail-safe timeout 90s) nếu người dùng vắng mặt.

---

## 💡 2. Đề Xuất Giải Pháp Kỹ Thuật Của Antigravity

Antigravity đề xuất tái cấu trúc (refactor) module cdp.py và crawler/tvpl.py trong ccba-legal-intel theo 4 trụ cột:

A. Chuẩn Hóa Quản Trị Vòng Đời Chrome Instance (Deterministic Life-Cycle & Self-Healing):
- Trước khi spawn Chrome mới, kiểm tra tính sống (health-check) qua GET http://127.0.0.1:<port>/json/version với timeout 1.0s.
- Nếu port bận nhưng không phản hồi HTTP (tiến trình zombie / treo DISPLAY):
  + Trên Linux: Quét PID giữ port bằng ss -tulpn hoặc đọc SingletonLock symlink target, gọi os.killpg(os.getpgid(pid), signal.SIGKILL).
  + Trên Windows: Gọi taskkill /F /PID <pid> /T.
  + Xóa sạch tệp khóa SingletonLock, SingletonCookie, SingletonSocket trước khi khởi động.
- Tuyệt đối không spawn đa instance trên cùng một user-data-dir.

B. Đóng Gói API download_asset_deterministic() (Zero-Sleep Event-Driven):
- Mở rộng class ChromeCDP với phương thức chính thức: download_asset(url_or_click_fn, target_dir, timeout=30.0).
- Khai báo CDP Event Listener: Browser.setDownloadBehavior(behavior='allow', downloadPath=target_dir, eventsEnabled=True).
- Lắng nghe sự kiện:
  + Browser.downloadWillBegin -> guid, suggestedFilename.
  + Browser.downloadProgress -> state: inProgress | completed | canceled.
  + Trả về đường dẫn file chính xác ngay khi nhận state: completed, triệt tiêu hoàn toàn time.sleep().
  + Nếu có lỗi hoặc timeout -> hủy tải và ném ngoại lệ tường minh DownloadTimeoutError.

C. Động Cơ Bóc Tách URL Download Mã Hóa ASP.NET (Postback Decoupler):
- Crawler chạy script in-DOM trích xuất chuỗi regex: download.aspx?id=...&part=-1&docx=1.
- Thực hiện điều hướng trực tiếp bằng CDP Page.navigate tới URL download đã giải mã, kích hoạt trực tiếp event download của trình duyệt mà không phụ thuộc vào trạng thái disable của nút bấm trên UI.

D. Cơ Chế Human-In-The-Loop Có Hạn Định (Fail-Safe Turnstile Protocol):
- Đưa cửa sổ lên foreground kèm log cảnh báo mức WARNING.
- Thiết lập đồng hồ đếm ngược trần cứng 90 giây (Human Interaction Budget).
- Định kỳ kiểm tra sau mỗi 1.0s xem trang đích đã load hoàn tất chưa (document.readyState === 'complete' và không còn iframe captcha).
- Quá 90s không tương tác -> giải phóng lock, đóng browser an toàn, trả về lỗi CloudflareChallengeTimeout.

---

## 🔍 3. Yêu Cầu Phản Biện Đối Kháng Từ Grok

Xin Grok soi xét kỹ lưỡng và phản biện các góc khuất kỹ thuật:
1. Lắng nghe sự kiện Browser.downloadProgress qua WebSocket raw có nguy cơ rớt frame hoặc treo ws.recv() trên mạng lag không? Có nên kết hợp ccba-file-stability-guard làm fallback tầng 2?
2. Khi Chrome tải file trên Windows, việc đổi tên .crdownload -> .docx có bị antivirus khóa handle (gây PermissionError) không? Giải pháp xử lý race condition này?
3. Dọn dẹp SingletonLock và kill process group có nguy cơ giết nhầm Chrome cá nhân của user không? Cần neo vào đâu để chỉ cô lập đúng instance chrome_vip?
4. Tần suất request vào download.aspx?id=... có nguy cơ bị TVPL rate limit IP không? Cần cấu hình jitter token-bucket thế nào?
