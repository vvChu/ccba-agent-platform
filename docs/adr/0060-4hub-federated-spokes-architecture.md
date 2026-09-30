# 0060. 4-Hubs × Federated Spokes Architecture & Distributed Ecosystem Governance

* **Status:** Accepted
* **Date:** 2026-09-25
* **Deciders:** CCBA Platform Core Team, DGX Spark Systems Architect & Lead Engineer
* **Consulted:** ADR 0035 (Deep Modules), ADR 0043 (IDOP Resilience), ADR 0044 (Federated RAG), ADR 0053 (Teamwork Multi-Agent Framework), ADR 0057 (Two-Stage Governance), ADR 0058 (Deterministic Hard Completion Lock), ADR 0059 (Cryptographic Provenance)

---

## Context & Problem Statement

Hệ sinh thái CCBA vận hành trên máy chủ AI chuyên dụng NVIDIA DGX Spark (kiến trúc Blackwell GB10, 128GB LPDDR5X Unified Memory) cùng hệ thống đa kho mã nguồn phân tán. Khảo sát thực nghiệm diện rộng và nghiên cứu chuyên sâu đa tác tử (Teamwork Framework — ADR 0053 theo Issue #366) đã phát hiện 4 điểm nghẽn kiến trúc và nguy cơ an ninh cốt tử:

1. **Rò Rỉ Bộ Nhớ Prisma Query Engine (10.22 GB RAM) Trong AI Gateway:**
   - Tiến trình LiteLLM Proxy ghi nhận toàn bộ payload hội thoại dạng `jsonb` vào bảng `LiteLLM_SpendLogs` trong PostgreSQL (:15432), tích tụ suốt 6.5 tháng đạt 347,086 dòng (894 MB, TOAST chiếm 533 MB).
   - Tiến trình Rust Prisma Query Engine (`query-engine-linux-arm64`) ngốn **10.22 GB RAM vật lý** (đỉnh ảo 15.67 GB) do thiếu chính sách cắt tỉa tự động và bộ cấp phát `glibc malloc` trên ARM64 (20 core, 160 arenas) bị phân mảnh heap trầm trọng, đe dọa trực tiếp Unified Memory của vLLM và Milvus.
2. **Lỗ Hổng An Ninh Nghiêm Trọng Nếu Cấp `chmod o+x /home/vvc` Cho Multi-User:**
   - Để các kỹ sư khác (`tta`, `tat`, `mtt`) truy cập vào các workspace dự án bên dưới `/home/vvc`, một số đề xuất đưa ra phương án chạy `chmod o+x /home/vvc`.
   - Khảo sát thực tế phát hiện `~/.ssh/config` (mode 664), `~/.gemini/` (projects.json, google_accounts.json, và SQLite conversations.db chứa mã nguồn bí mật) đều mở quyền đọc cho other. Khi cấp bit `+x` cho `other` trên `/home/vvc`, bất kỳ user hay daemon unprivileged nào biết đường dẫn đều đọc trộm được toàn bộ secrets và chat logs!
3. **Nhu Cầu Đồng Bộ Dữ Liệu Doanh Nghiệp Với Microsoft 365 (IDOP-CCBA-WAY):**
   - Hệ sinh thái IDOP sở hữu 59 SharePoint Lists schema qua 6 miền nghiệp vụ (CDE ISO 19650, CRM Opportunities, Hợp đồng, Phân bổ doanh thu, OKRs, Quản trị).
   - Kiến trúc trước đây phụ thuộc vào script PowerShell/PnP trên Windows, không có cơ chế điều tiết lưu lượng phẳng (Token Bucket Rate Limiter) và hàng đợi Dead-Letter Queue (DLQ), dẫn đến nguy cơ bị Microsoft Graph API chặn lỗi HTTP 429 Throttling khi đồng bộ dữ liệu hàng loạt từ GPU Server.
4. **Điểm Nghẽn Độ Trễ RAG 25.4s Do Xung Đột VRAM & Cơ Chế Swap Bộ Nhớ:**
   - Profiling thực nghiệm phát hiện: Bước nhúng câu truy vấn bằng mô hình BGE-M3 trên GPU Blackwell thực tế **chỉ mất 0.283 giây (283ms)**.
   - Tuy nhiên, do container vLLM `qwen36b` chiếm cố định 70.5 GB VRAM (`gpu-memory-utilization 0.85`), PyTorch trong `rag-service` chỉ thấy 1.39 GB free VRAM, buộc hệ thống phải dùng cơ chế `model.to("cuda")` (6.75s) và `model.to("cpu")` + `empty_cache()` (14.92s) liên tục. Chu kỳ swap bộ nhớ này chiếm tới 21.67s (98.7% thời gian nhúng), làm tê liệt trải nghiệm tra cứu quy chuẩn pháp lý.
5. **Điểm Nghẽn Phân Phối Catalog & Seam Contracts Cho Spokes Độc Lập (Issue #374):**
   - Cơ chế dò tìm Hub hiện tại (`HubDiscoverer`) giả định Spoke luôn nằm trên cùng hệ thống tệp cục bộ với Hub (qua `CCBA_HUB_PATH` hoặc thư mục lân cận).
   - Khi triển khai Federated Spokes trên máy trạm cá nhân của kỹ sư (`tta`, `tat`, `mtt`), laptop công trường, hoặc container CI không clone toàn bộ repo Hub, Spoke không thể đọc trực tiếp filesystem của Hub, dẫn đến lỗi `HubNotFoundError`. Các công cụ tra cứu Seam (`find-seam`) và Linter (`check_dependency_contracts.py`) không thể đối soát hợp đồng Seam (ADR-0061).

---

## Decision Outcome

Đội ngũ kiến trúc CCBA quyết định ban hành **HUB-ADR-0060** chuẩn hóa mô hình phân tầng **4-Hubs × Federated Spokes** và các quy chuẩn quản trị hệ thống:

```
                             ┌─────────────────────────────────────────────────────────┐
                             │               MICROSOFT 365 ENTERPRISE                  │
                             │               (IDOP-CCBA-WAY Production)                │
                             │  - 59 SharePoint Lists (CDE, CRM, Cash, OKRs...)        │
                             │  - Entra ID App-Only (Sites.FullControl.All)            │
                             │  - SharePoint Online Portals (/sites/idop, /sites/iCDE) │
                             └───────────────────────────▲─────────────────────────────┘
                                                         │
                                    Outbound Bridge Sync │ (Python MSAL + HTTPX Token Bucket + DLQ)
                                                         │
┌────────────────────────────────────────────────────────▼─────────────────────────────────────────────────────────┐
│                                             NVIDIA DGX SPARK HUB                                                 │
│                                            (dgx-spark-toolkit)                                                   │
│                                                                                                                  │
│  ┌───────────────────────┐  ┌────────────────────────┐  ┌───────────────────────┐  ┌──────────────────────────┐  │
│  │   vLLM EngineCore     │  │   Speaches Whisper     │  │  Milvus Standalone    │  │       Neo4j Graph        │  │
│  │  - Qwen 36B (98k ctx) │  │  - Large-v3 (FP16)     │  │  - legal_docs_v11     │  │  - Regulatory Graph      │  │
│  │  - VRAM Util = 0.80   │  │  - 200 MB VRAM, 3.6 GB │  │  - 4,051 entities     │  │  - 19 nodes, 12 rels     │  │
│  │  - Port 8004          │  │  - Port 8008 (Blackwell)│ │  - Port 19530         │  │  - Port 7474 / 7687      │  │
│  └───────────▲───────────┘  └───────────▲────────────┘  └───────────▲───────────┘  └────────────▲─────────────┘  │
│              │                          │                           │                            │               │
│              └──────────────────────────┼───────────────────────────┴────────────────────────────┘               │
│                                         │                                                                        │
│                             ┌───────────┴────────────────────────────┐                                           │
│                             │     LiteLLM AI Gateway Proxy (:8090)   │                                           │
│                             │   - 22 Models, Virtual Key Quotas      │                                           │
│                             │   - SpendLogs Retention 30d (Batch SQL)│                                           │
│                             │   - Postgres (:15432) | Redis (:16379) │                                           │
│                             └───────────────────▲────────────────────┘                                           │
└─────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────┘
                                                  │
         ┌────────────────────────────────────────┼────────────────────────────────────────┐
         │                                        │                                        │
┌────────▼────────────────┐            ┌──────────▼──────────────┐             ┌───────────▼────────────┐
│      INTELLIGENCE       │            │       LEGAL DATA        │             │      SYNTHESIS         │
│   ccba-agent-platform   │            │  ccba-legal-knowledge   │             │       VvC_Notes        │
│                         │            │                         │             │                        │
│ - Layer 1 Constitution  │            │ - OKF v2.4 Knowledge    │             │ - VvC LLM OS (v5-v8)   │
│ - Skills Catalog        │            │ - SHA-256 Provenance    │             │ - Architecture Vault   │
│ - ccba_harness (Gate 0) │            │ - TVPL Crawler & Raw    │             │ - Strategic Playbooks  │
│ - Governance & CLI      │            │ - Bilateral Parity      │             │ - Cognitive Synthesis  │
└────────▲────────────────┘            └──────────▲──────────────┘             └───────────▲────────────┘
         │                                        │                                        │
         └────────────────────────────────────────┼────────────────────────────────────────┘
                                                  │ (Virtual Keys, POSIX ACLs, FastMCP RAG API)
                                 ┌────────────────┴────────────────┐
                                 │        FEDERATED SPOKES         │
                                 │  - bim-planner                  │
                                 │  - ibim_accounting              │
                                 │  - AC_IBSTBM2 / PP_IBSTBM       │
                                 │  - Multi-Developers (tta, tat..)│
                                 └─────────────────────────────────┘
```

### 1. Phân Định Ranh Giới 4-Hubs × Federated Spokes (Separation of Concerns)
- **Compute Hub (`dgx-spark-toolkit`)**: Quản trị hạ tầng máy chủ, Docker containers, vLLM, Speaches Whisper, LiteLLM Gateway, Milvus và Neo4j.
- **Governance & Intelligence Hub (`ccba-agent-platform`)**: Trung tâm ban hành Hiến pháp Layer 1, Skills Catalog SSOT, khung điều phối đa tác tử Teamwork (ADR 0053), harness kiểm định tự động (ADR 0058), và SDK `ccba-ai`.
- **Legal Data Hub (`ccba-legal-knowledge`)**: Kho dữ liệu chuẩn mực OKF v2.4, AST điều khoản `clauses.json`, văn bản gốc PDF/DOCX có chữ ký băm mật mã SHA-256 (ADR 0059), và TVPL VIP crawler (ADR 0031).
- **Synthesis Hub (`VvC_Notes`)**: Kho tri thức cá nhân, tổng kết phương pháp luận VvC LLM OS, các playbooks chiến lược và mô hình nhận thức.
- **Operations Hub (`IDOP-CCBA-WAY`)**: Nền tảng điều hành nghiệp vụ thực tế của Viện IBST và CCBA trên Microsoft 365 Enterprise.

### 2. Chuẩn Mực An Ninh OS Topology: POSIX ACLs Pin-Hole Traversal
- **Cấm Tuyệt Đối:** Sử dụng `chmod o+x /home/vvc`.
- **Nhóm Kỹ Sư Cộng Tác (`ccba-devs`):** Khởi tạo nhóm hệ thống `ccba-devs` bao gồm các kỹ sư được ủy quyền (`vvc`, `tta`, `tat`, `mtt`), loại trừ nghiêm ngặt tài khoản remote guest (`rdpuser`) và service daemons.
- **Traversal Pin-Hole:** Cấp quyền duyệt đường dẫn DUY NHẤT cho nhóm trên thư mục gốc:
  `setfacl -m g:ccba-devs:--x /home/vvc` trong khi bảo toàn tuyệt đối `other::---` (Mode 0750).
- **Default Inheritance:** Cấp quyền đọc/ghi/thực thi và kế thừa mặc định cho nhóm trên các Hub chia sẻ:
  `setfacl -R -m g:ccba-devs:rwX -d -m g:ccba-devs:rwX /home/vvc/Codebase /home/vvc/ccba /home/vvc/VvC_Notes`.
- **Defense-in-Depth:** Thắt chặt quyền Mode 0700 và xóa bỏ hoàn toàn ACLs kế thừa trên các thư mục cá nhân bí mật: `~/.ssh`, `~/.gemini`, `~/.config`, `~/.claude`.
- **Môi Trường Python Multi-User:** Tự động áp dụng `umask 0002` qua `/etc/profile.d/ccba-umask.sh` khi người dùng thuộc nhóm `ccba-devs`, kết hợp cờ SetGID `chmod -R g+s` trên thư mục `.venv`.

### 3. Quản Trị Dữ Liệu AI Gateway & Cấp Phát Khoá Ảo (Virtual Keys)
- **Chính Sách Cắt Tỉa Dữ Liệu Định Kỳ (Retention Policy):**
  - Cắt tỉa bảng `LiteLLM_SpendLogs` theo chu kỳ 30 ngày bằng script SQL chia lô (`BATCH_SIZE = 10000`, `pg_sleep(0.05)`).
  - Tuân thủ nghiêm ngặt **RULE-5.5** về chuẩn hóa múi giờ: Chuyển đổi mốc 00:00:00 ICT sang UTC trước khi quét chỉ mục `startTime`.
  - Thiết lập tham số `maximum_spend_logs_retention_period: 30d` trong cấu hình LiteLLM để kích hoạt tiến trình dọn dẹp ngầm tự động.
- **Cấp Phát Khoá Ảo Động (`POST /key/generate`):**
  - Quản trị hạn ngạch chi phí và tốc độ độc lập cho từng Spoke và kỹ sư:
    + `spoke-idop`: 120 RPM, \$50/30d, 8 parallel requests.
    + `spoke-bim-planner`: 60 RPM, \$30/30d, 4 parallel requests.
    + `spoke-legal`: 60 RPM, \$40/30d, 4 parallel requests.
    + `dev-tta` / `dev-tat`: 30 RPM, \$15/30d, 2 parallel requests.
  - Tích hợp cổng kiểm tra Idempotency Gate chống tạo trùng lặp token.

### 4. Thiết Kế Python Outbound Bridge Worker Cho Microsoft 365
- **Loại Bỏ Phụ Thuộc PowerShell:** Xây dựng module thuần Python `ccba_m365_bridge.py` dựa trên `msal` (App-Only ConfidentialClientApplication) và `httpx`.
- **Token Bucket Rate Limiting:** Duy trì tốc độ đẩy dữ liệu phẳng tối đa 5.0 requests/giây để không bao giờ chạm ngưỡng giới hạn của SharePoint Online.
- **Khả Năng Chịu Lỗi 429 & Throttling:** Tôn trọng tuyệt đối header `Retry-After` kèm jitter ngẫu nhiên để chống hiện tượng thundering herd.
- **Dead-Letter Queue (DLQ):** Toàn bộ các yêu cầu thất bại do mạng gián đoạn được lưu trữ dưới dạng JSON nguyên tử tại `.system_generated/dlq/` (`STAGED_LOCAL` theo ADR-0043), cho phép phát lại tự động (replay) khi kết nối phục hồi.

### 5. Tối Ưu Hóa Độ Trễ RAG (SLA < 1.5s) & Zero-Bloat Federated RAG
- **Persistent GPU Pool:** Điều chỉnh `--gpu-memory-utilization` của vLLM `qwen36b` từ `0.85` xuống `0.80`, giải phóng 6.0 GB VRAM trên chip Blackwell GB10.
- **Triệt Tiêu Swap VRAM:** Duy trì mô hình nhúng BGE-M3 (1.1 GB VRAM) và CrossEncoder Reranker (1.2 GB) thường trực 100% trên GPU, xóa bỏ hoàn toàn chu kỳ swap CPU $\leftrightarrow$ GPU 21.6s, đưa độ trễ nhúng từ **21.9s xuống < 50ms** và tổng độ trễ `/search` xuống **< 1.0s - 1.2s**.
- **Zero-Bloat Spokes:** Các Spoke không tải bản sao kho dữ liệu 700 MB, thay vào đó gọi FastMCP tool `query_legal_ground_truth` (ADR 0010 / ADR 0044) hoặc tải tệp chỉ mục nén `clauses_compact_index.json` (~8.5 MB).
- **Cache Bất Biến `.npy`:** Lưu ma trận nhúng vector đi kèm sidecar `embeddings.npy.sha256` đối soát với mã băm nội dung văn bản nguồn, bảo đảm truy xuất tức thì trong 2ms mà vẫn duy trì tính toàn vẹn pháp lý (ADR 0059).

### 6. Giao Thức Phân Phối Catalog Đa Tầng (Federated Spoke Catalog & Seam Distribution Protocol)
*(Bổ sung theo Amendment 2026-09-30 — Thẩm định đồng cấp bởi Grok 4.7 xhigh tại Issue #374)*

Nhằm giải quyết triệt để vấn đề phân phối tri thức quản trị và hợp đồng Seam (ADR-0061) cho các Federated Spokes không chia sẻ hệ thống tệp vật lý với Hub, nền tảng chuẩn hóa kiến trúc **Hybrid Multi-Tier Distribution**:

#### A. Phân Tầng Giao Thức (Tiered Architecture)
1. **Tier 1 (Zero-Latency Local Snapshot):**
   - Mọi Spoke lưu trữ bản snapshot nguyên byte (raw bytes) tại `.agents/cache/hub-catalog/snapshots/<sha>/` gồm:
     + `seam-contracts.yaml`: Bản sao đúng từng byte từ Hub root.
     + `catalog.yaml`: Bản sao đúng từng byte từ Hub `.agents/skills/platform-loader/catalog.yaml`.
     + `.catalog_provenance.json`: Tệp siêu dữ liệu chứng thực nguồn gốc.
   - Quá trình hoán đổi phiên bản sử dụng thao tác nguyên tử `os.replace` trên con trỏ văn bản/symlink `current` trỏ tới snapshot hợp lệ.
   - Mọi thao tác đọc (Reader) chỉ mở snapshot thông qua `current`, không sử dụng lock file để tránh xung đột luồng và nghẽn tiến trình.
   - **Cách ly Định Danh Oracle:** Tuyệt đối không lưu snapshot tại `.agents/catalog.yaml` để tránh làm sai lệch nhận diện `HubDiscoverer._is_valid_hub` (gây hiện tượng nhận diện nhầm Spoke thành Hub).
2. **Tier 2 (Non-blocking Subprocess Probe & Graceful Fallback):**
   - **Rào chắn chống treo Socket (DNS/Tailscale Hanging Defense):** Tiến trình Linter và CLI tra cứu tuyệt đối **không mở socket mạng trực tiếp** trong tiến trình chính (do hàm `getaddrinfo` của glibc chạy blocking dưới kernel và không thể ngắt bởi client-side HTTP timeout).
   - Mọi hoạt động kiểm tra cập nhật (probe) bắt buộc thực thi trong một tiến trình con nền (background subprocess), bị áp trần ngắt cưỡng bức bằng `SIGKILL` tại **1.5 giây**.
   - **Phân định Mặt phẳng (Plane Separation):** Endpoint cập nhật snapshot lấy từ biến môi trường `CCBA_CATALOG_URL` (Control Plane) hoặc GitHub Raw URL. Nghiêm cấm trỏ vào LiteLLM Gateway (:8090 — Data Plane suy luận gắn hạn mức token/RPM).
   - **Monotonic Debounce:** Giới hạn tần suất thăm dò tối thiểu 15 phút một lần trong cache máy cục bộ.
   - **Biên lai Kiểm toán Bắt buộc:** Biên lai `find-seam` bắt buộc chứa trường `freshness`:
     + `fresh`: Mã băm khớp với bản probe thành công gần nhất (< 15 phút).
     + `stale`: Mã băm lệch với remote nhưng chưa cập nhật snapshot.
     + `unverified`: Mất mạng hoặc timeout, sử dụng an toàn snapshot cục bộ.
     + `corrupt`: Mã băm nội dung thực tế không khớp với `.catalog_provenance.json` (thoát mã lỗi 1).
3. **Tier 3 (Phân Định Thực Thi Seam qua `binding.mode`):**
   - Hợp đồng Seam trong `seam-contracts.yaml` bắt buộc phân định cách gọi qua trường `binding.mode`:
     + `local_import`: Thực thi qua import module Python trong virtualenv của Spoke (yêu cầu cài đặt package qua pip/wheel).
     + `remote_mcp`: Ủy quyền thực thi qua MCP Tool trên DGX Spark (:8004/:8008). Khi mất mạng, trả về `invoke: blocked`, lý do `health_timeout`, kích hoạt cách ly Quarantine có thời hạn theo ADR-0061; cấm viết script thay thế ad-hoc.
     + `skill`: Kích hoạt qua slash-command sau khi đồng bộ skill.

#### B. Đặc Tả Siêu Dữ Liệu Chứng Thực (.catalog_provenance.json)
```json
{
  "schema": 1,
  "seam_contracts_sha256": "<raw_bytes_sha256_of_seam_contracts>",
  "catalog_sha256": "<raw_bytes_sha256_of_catalog>",
  "hub_commit": "<40_hex_git_commit_or_null>",
  "source_url": "<CCBA_CATALOG_URL_or_filesystem_path>",
  "fetched_at_utc": "<ISO_8601_UTC_timestamp>"
}
```

#### C. Quy Định Mã Lỗi & Phân Giải Hub
- **Thứ tự phân giải:**
  1. Nếu `CCBA_HUB_PATH` trỏ tới Hub hợp lệ có filesystem: Đọc trực tiếp từ file gốc Hub.
  2. Nếu không có Hub filesystem: Đọc snapshot từ con trỏ `current` trong cache Spoke.
  3. Nếu không tìm thấy cả Hub lẫn snapshot `current`: Ném mã lỗi `CatalogSnapshotMissing` (yêu cầu chạy `ccba-init-spoke` hoặc tải snapshot), tuyệt đối không ngụy trang thành `RAW_BYPASS_RESTRICTIONS`.

---

## Consequences

### Tích Cực (Positive)
- **Tối Ưu Hóa Tài Nguyên Đột Phá:** Thu hồi ~10 GB RAM vật lý từ Prisma Query Engine, giải phóng 800 MB đĩa WAL, và hạ độ trễ tra cứu pháp lý RAG từ 25.4s xuống dưới 1.2s (tăng tốc x20).
- **An Ninh Cấp Doanh Nghiệp (Multi-User Hardening):** Đóng kín hoàn toàn các lỗ hổng lộ lọt token và dữ liệu riêng tư trên thư mục home, cho phép đội ngũ kỹ sư (`tta`, `tat`, `mtt`) cùng lập trình chung mượt mà không xung đột quyền ghi.
- **Tự Động Hóa Vận Hành Doanh Nghiệp:** Cầu nối Python M365 Outbound Bridge cho phép đưa dữ liệu kiểm định BIM và tiến độ CDE từ DGX Spark lên trực tiếp 59 danh mục SharePoint mà không cần can thiệp thủ công.
- **Kiểm Soát Chi Phí Minh Bạch:** Quản trị hạn mức API từng Spoke qua Virtual Keys, ngăn ngừa rủi ro cạn kiệt ngân sách hoặc lỗi cascade failures.
- **Phân Phối Catalog Đa Tầng Không Xung Đột (ADR-0060 Mục 6):** Cho phép các Spoke hoạt động độc lập và ngoại tuyến 100% với độ trễ < 2ms, đồng thời phát hiện cập nhật tự động khi có mạng mà không bao giờ bị treo bởi blocking DNS/Tailscale.

### Tiêu Cực & Thách Thức (Trade-offs & Mitigations)
- **Yêu Cầu Quyền Quản Trị Hệ Thống Cho POSIX ACLs:** Script `setup_ccba_devs_acls.sh` yêu cầu quyền `sudo` để gán nhóm và quyền trên `/home/vvc`. *Biện pháp:* Đóng gói script độc lập có cơ chế kiểm tra an toàn và chạy thẩm định `bash -n` trước khi thực thi.
- **Giới Hạn Tốc Độ Microsoft Graph API:** Việc giới hạn 5 req/s có thể kéo dài thời gian đồng bộ ban đầu khi nạp hàng ngàn hồ sơ CDE. *Biện pháp:* Kết hợp cơ chế lọc Delta Query và chỉ đồng bộ các tệp có cập nhật mới.
- **Độ Phức Tạp Quản Lý Snapshot Cache Trên Spoke:** Cần cơ chế dọn dẹp các snapshot cũ hơn để không chiếm dụng dung lượng đĩa. *Biện pháp:* Giữ tối đa 2 snapshot gần nhất (bản `current` và bản trước đó) tại `.agents/cache/hub-catalog/snapshots/`.
