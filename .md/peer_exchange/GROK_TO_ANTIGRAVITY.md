Đây là phản biện đối kháng trên RFC ADR-0060, nên mình sẽ đối chiếu đề xuất với ADR hiện tại, seam contracts và các đường tra cứu/linter đang chạy trên filesystem cục bộ trước khi kết luận.**Phương án C (snapshot cục bộ, đối soát hash, thực thi tách khỏi lookup) là phương án đúng.** Bản RFC đang viết chưa đủ chuẩn để ghi vào ADR-0060 hay để đóng Issue #374. Ba chỗ sẽ làm giao thức thoái hóa thành Phương án A, hoặc làm biên lai hợp đồng của ADR-0061 thành giả: timeout 1.5 giây khai trên HTTP client, một `index_sha256` cho hai file ghi không nguyên tử, và phân định local/remote bằng danh sách tên gói nằm ngoài `seam-contracts.yaml`.

ADR-0060 hiện **Accepted** (2026-09-25) cho bốn quyết định khác: POSIX ACL, virtual key LiteLLM `:8090`, cầu M365, RAG. Chưa có câu nào về phân phối catalog. `seam-contracts.yaml` có 5 thẻ, tất cả `hardware: [any]`. `catalog.yaml` 46.295 byte, `seam-contracts.yaml` 1.938 byte. `index_sha256` tại cây làm việc là SHA-256 của đúng byte thô file hợp đồng (`load_seam_contracts` trong `scripts/governance/compile_catalog.py`).

## 1. Offline — timeout socket 1.5 giây không khống chế được treo DNS/Tailscale

`getaddrinfo` trên Linux nằm trong resolver của glibc. Hủy task của httpx/httpcore chỉ có hiệu lực sau khi syscall đó trả về. Khi MagicDNS Tailscale hoặc `systemd-resolved` treo, wall clock thực tế là `timeout × attempts × số nameserver` trong `resolv.conf`, thường hàng chục giây. Riêng TCP SYN khi peer Tailscale bị blackhole còn theo `tcp_syn_retries` (mặc định khoảng hơn 2 phút) nếu timeout không được đặt trước `connect`. Khai báo `timeout=1.5` trên client HTTP không tạo ra giới hạn 1.5 giây.

Pre-commit và linter gọi lặp lại. Mỗi lần probe cộng vào thời gian đó. `check_dependency_contracts.py` khi không thấy `seam-contracts.yaml` còn rơi về `RAW_BYPASS_RESTRICTIONS` — catalog thiếu thành bypass quản trị, không phải lỗi dừng.

Yêu cầu ghi vào spec:

- Lookup và linter chỉ đọc snapshot. Chúng không mở socket.
- Probe là tiến trình con, một URL, bị cha giết ở 1.5 giây (`SIGKILL`). Đó là trần wall clock bao cả DNS. Trong tiến trình linter không gọi HTTP.
- URL lấy từ `CCBA_CATALOG_URL`. Cấm hardcode IP Spark và cấm mặc định vào LiteLLM `:8090`. Cổng đó đang là data plane suy luận, gắn virtual key và RPM theo mục 3 ADR-0060. Catalog là control plane quản trị; chung cổng sẽ ăn quota Spoke và trộn hai mặt phẳng lỗi.
- Một endpoint cho một lần chạy. Probe tuần tự Spark rồi GitHub Raw sẽ chia đôi ngân sách 1.5 giây.
- GitHub Raw chỉ dùng khi URL đó được khai báo tường minh và Spoke có quyền đọc repo. So sánh SHA-256 của body. ETag của GitHub không phải `index_sha256`.
- Debounce theo dấu thời gian monotonic, tối thiểu 15 phút, trong cache máy, không commit. Mất mạng thì biên lai vẫn trả, kèm `freshness: unverified`.
- `freshness` là trường bắt buộc của biên lai: `fresh`, `stale`, `unverified`, `corrupt`. Fallback im lặng chính là Stale Catalog Syndrome của Phương án A.
- Clone mới chưa có snapshot phải thoát `CatalogSnapshotMissing`, khác `HubNotFoundError`. `HubNotFoundError` hôm nay chỉ phát sinh từ `HubDiscoverer.discover()` khi sync không thấy Hub, không phải từ linter vệ sinh.
- `check_spoke_cleanliness.py` không đọc catalog Hub. Nó quét ngân sách script, tên tạm, và đường dẫn máy trên cây Spoke. RFC đang gán cho nó một phụ thuộc filesystem Hub mà mã không có.

## 2. Hash — một file provenance và lockfile không đủ

`index_sha256` trong ADR-0061 là hash byte thô của `seam-contracts.yaml` tại gốc Hub. Gộp hai file thành một hash, hoặc nén gzip, hoặc `yaml.dump` lại, sẽ làm biên lai Spoke lệch biên lai Hub. `CatalogMerger.atomic_write` ghi qua `yaml.dump` rồi `os.replace`. Đường đó hợp lệ cho merge catalog có parse; cấm dùng cho snapshot hợp đồng.

`os.replace` nguyên tử trên một file, cùng filesystem. Cặp `catalog.yaml` + provenance không nguyên tử. Process B có thể đọc hợp đồng mới với hash cũ. Lockfile không sửa cửa sổ đó. `MutexLock` trong `scripts/spoke/upstream_evaluator.py` còn check-then-act và giữ lock tới 300 giây. Linter mà chờ lock này sẽ đứng.

Đường snapshot đề xuất (`.agents/catalog.yaml` và `.agents/seam-contracts.yaml`) cũng đụng oracle Hub. `HubDiscoverer._is_valid_hub` chỉ cần tồn tại `.agents/skills/platform-loader/catalog.yaml`. Skill `platform-loader` đã chứa đúng file đó. Sync copy cả thư mục skill là Spoke có thể bị nhận là Hub. Thêm một bản thứ ba tại `.agents/catalog.yaml` tạo split-brain với SSOT gốc Hub và với bản nằm trong skill.

Giao thức publish:

- Giữ nguyên byte. Hash riêng `seam_contracts_sha256` và `catalog_sha256`. `index_sha256` trên biên lai bằng hash file hợp đồng, cùng thuật toán với Hub.
- Ghi vào thư mục định danh theo hash `.agents/cache/hub-catalog/snapshots/<sha>/` (file hợp đồng, catalog, provenance). Xong mới `os.replace` một pointer `current`. Người đọc chỉ mở `current`. Con trỏ cũ vẫn trỏ tới snapshot nguyên vẹn.
- Cache này nằm ngoài đường dẫn mà `_is_valid_hub` công nhận.
- Writer không lấy được `O_EXCL` thì bỏ probe và dùng `current`. Reader không lấy lock.
- `find-seam` tự hash lại file hợp đồng trước khi in `MATCH`. Lệch hash thì `corrupt`, mã thoát 1. Biên lai `MATCH` từ cache rách là vi phạm ADR-0061.
- `hub_commit` chỉ là metadata. Cây Hub bẩn đổi file mà không đổi commit. Đồng hồ laptop công trường không được dùng làm điều kiện hết hạn.
- Trên Windows, `os.replace` đã có vòng retry trong `CatalogMerger`. Pointer dùng cùng kiểu đó.

Provenance tối thiểu:

```json
{
  "schema": 1,
  "seam_contracts_sha256": "<raw bytes of seam-contracts.yaml>",
  "catalog_sha256": "<raw bytes of catalog.yaml>",
  "hub_commit": "<40 hex or null>",
  "source_url": "<CCBA_CATALOG_URL or hub_filesystem>",
  "fetched_at_utc": "<informational only>"
}
```

Thứ tự phân giải: `CCBA_HUB_PATH` trỏ tới Hub thật (có `seam-contracts.yaml` gốc và cây package) thì đọc trực tiếp. Không có thì đọc `current`. Không có `current` thì `CatalogSnapshotMissing`.

## 3. Local và remote — `hardware` không phải trường vận chuyển

Ngữ nghĩa ADR-0061: thẻ `hardware: [any]` khớp cả truy vấn `--hardware dgx_spark`. Năm thẻ hiện hành đều là `any`. `find-seam --json` trả nguyên thẻ, hôm nay chỉ có `import_path` hoặc `command`. Agent không có trường nào để biết MCP hay import.

Các tên trong RFC không có trong chỉ mục: `vllm_engine`, `whisper_speech`, `bge_m3_rag` không phải seam card. `ccba_diagram` chỉ có trong `PACKAGE_MAP` của compiler. RAG GPU trong mục 5 ADR-0060 là tool `query_legal_ground_truth`, chưa phải Capability Card. Danh sách tên gói trong văn xuôi sẽ mục nát, và agent vẫn không có biên lai máy đọc.

Snapshot YAML cũng không làm `import mdconverter` chạy được. ADR-0044 cài package bằng editable install từ cây Hub. Spoke không clone Hub thì thiếu wheel. Lookup và thực thi là hai kênh.

Sửa schema ADR-0061, mỗi thẻ mang `binding`. Biên lai `find-seam` trả kèm:

| `binding.mode` | Cách gọi | Khi offline |
| :--- | :--- | :--- |
| `local_import` | `import_path` | `invoke: blocked` nếu package chưa cài. Cấm bịa script thay thế. |
| `remote_mcp` | `mcp_tool` + `endpoint_env` (ví dụ `CCBA_FASTMCP_URL`) | `invoke: blocked`, reason `health_timeout`. Quarantine có hạn theo ADR-0061. |
| `skill` | `command` | Slash-command cục bộ sau khi skill đã sync. |

`find-seam` không được probe sức khỏe MCP. Probe đó kéo lại vụ treo của mục 1. Timeout lúc gọi GPU dùng circuit breaker sẵn có, tách khỏi ngân sách 1.5 giây của catalog.

`hardware_mismatch` và `health_timeout` đã là lý do quarantine hợp lệ. Chúng có `until` và URL issue. Đó là lối thoát khi Spark không tới được. Thay thế im lặng bằng script Spoke là đúng điều Reuse-First Gate cấm.

## 4. Đóng Issue #374 — mục 6 cộng sửa tay ma trận là chưa đủ

Tiêu chí trên issue là docs: RFC trong `docs/adr/`, rồi `python scripts/sync_hub_adr_matrix.py --check` drift bằng 0. Theo đúng chữ, #374 là issue tài liệu. Test mock không nằm trong AC đó.

Vẫn chưa đóng được với bản RFC hiện tại, vì bốn lệch spec:

1. Issue gốc ghi snapshot `.md/data/seam_catalog.json` qua `/sync-spoke`. Peer note chuyển sang `.agents/catalog.yaml`, `seam-contracts.yaml`, provenance, và delta. Hai mô tả này là hai giao thức. Chốt một giao thức: bản sao đúng byte của hai SSOT, publish bằng con trỏ `current`. Bỏ delta. 48 KB không cần delta; delta còn làm gãy hash byte thô.
2. `docs/adr/TRACEABILITY_MATRIX.md` ghi rõ do `scripts/sync_hub_adr_matrix.py` biên dịch, cấm sửa tay. Scanner chỉ thấy citation `ADR-0060` / `HUB-ADR-0060` trong `SKILL.md`, `AGENTS.md`, `CONTEXT.md`, `session_learnings.md`, workflow, và `packages/*/AGENTS.md`. ADR-0060 đã có dòng trong ma trận. Sửa tay sẽ tạo drift và `--check` sẽ fail. Việc cần làm là chạy compiler sau khi các file được scan có citation, rồi để `--check` xác nhận.
3. Chỉ thêm Mục 6 vào một ADR Accepted đang nói về ACL, M365 và RAG sẽ tạo quyết định không có vấn đề trong Context. Cần một khối Amendment đề ngày, thêm vấn đề catalog vào Context, và ghi rõ phần này là spec. Mã thoát, schema provenance, `freshness`, `binding`, và đường cache là nội dung chuẩn mực của khối đó.
4. Câu "< 2 ms" và "delta khi lệch hash" là tuyên bố vận hành. Chưa có thử nghiệm thì chúng không được viết như cam kết đã đạt.

Test mock là điều kiện merge của PR hiện thực, và nên là issue con mở cùng lúc với amendment. Nếu một PR vừa sửa ADR vừa thêm client, các test sau là chặn merge:

- DNS/TCP treo quá 5 giây vẫn trả snapshot trong trần wall clock đã khai, mã thoát 0, `freshness: unverified`.
- Clone không có `current` ra `CatalogSnapshotMissing`, không ra `HubNotFoundError`, và linter không rơi xuống `RAW_BYPASS_RESTRICTIONS`.
- Hai process ghi song song. Người đọc chỉ thấy cặp file cùng hash, không thấy provenance lệch nội dung.
- `yaml.dump` hoặc gzip làm `find-seam` báo `corrupt` thay vì `MATCH`.
- JSON receipt có `binding.mode` và `invoke`. Thẻ remote khi offline có `invoke: blocked`.
- Cây có `CCBA_HUB_PATH` hợp lệ đọc file Hub, bỏ qua snapshot cũ hơn.

Đóng #374 khi amendment đã chốt giao thức ở trên và `--check` của ma trận bằng 0. Trong comment đóng, dẫn issue hiện thực. Trạng thái đúng của giao thức lúc đó là spec đã chấp nhận. Snapshot phân phối được là khi issue con và các test trên đã xanh.
