---
request_id: 'req-20261004-issue457-plan'
verdict: 'APPROVE_WITH_CONDITIONS'
conditions:
  - id: 'C1'
    description: 'Bắt buộc chuẩn hóa URL theo chuẩn POSIX slash ("/") trên Windows, áp dụng timeout 5.0s và atomic write (ghi file tạm trước khi rename) để tránh hỏng cache khi đứt kết nối giữa chừng.'
    blocking: true
  - id: 'C2'
    description: 'Cấm tuyệt đối gọi GitHub REST API (/contents/) không xác thực để tránh cạn kiệt Rate Limit (60 req/h/IP). Toàn bộ luồng tải thư mục tables/ phải là manifest-driven (đọc danh sách từ metadata.yaml/registry) hoặc on-demand streaming qua GitHub Raw.'
    blocking: true
  - id: 'C3'
    description: 'Chuẩn hóa cấu trúc trả về Graceful Degradation: Bắt toàn bộ URLError/SocketTimeout/HTTPError, không quăng exception thô, trả về status="degraded_offline" kèm Actionable CLI Guidance chuẩn mực.'
    blocking: true
  - id: 'C4'
    description: 'Tuân thủ nghiêm ngặt ngân sách Micro-PR 1 (<= 150 LOC diff trong engine.py), bổ sung kiểm thử cô lập mock network 100% không phụ thuộc Internet trong test suite.'
    blocking: true
risk_score: 2
effort: 'S'
summary: 'Kế hoạch kiến trúc cho Issue #457 được phê duyệt với 4 điều kiện kỹ thuật bắt buộc nhằm bảo vệ tính tất định đa nền tảng, triệt tiêu bẫy Rate Limit và bảo đảm an toàn Micro-PR.'
---

# BÁO CÁO THẨM ĐỊNH ĐỐI KHÁNG & PHẢN BIỆN KỸ THUẬT (ADVERSARIAL REVIEW)
## ĐÁNH GIÁ KẾ HOẠCH TRIỂN KHAI ISSUE #457: REMOTE STREAMING SYNC & WHEEL PACKAGING

> **Người thẩm định**: Grok 4.7 xhigh (Adversarial Auditor & Gatekeeper)  
> **Gửi tới**: Antigravity (Lead Architect & Implementation Orchestrator)  
> **Dự án**: CCBA Agent Services Platform (`ccba-agent-platform`)  
> **Phạm vi**: Issue [#457](https://github.com/vvChu/ccba-agent-platform/issues/457) — Remote Streaming Sync & Automated CI Wheel Packaging  
> **Khung quy chuẩn**: ADR-0007, ADR-0026, ADR-0050, ADR-0058, ADR-0061, Guardrail 19  

---

### 1. Đánh Giá Cơ Chế Streaming / Tải Dữ Liệu: GitHub Raw vs GitHub API vs On-Demand & Vấn Đề Thư Mục Con `tables/`

#### 🔴 Phân tích rủi ro & Bẫy kiến trúc (Architectural Pitfalls):
1. **Bẫy Rate Limit của GitHub REST API (Phương án C - LOẠI BỎ)**:
   - Nếu gọi API `https://api.github.com/repos/vvChu/ccba-legal-knowledge/contents/...` khi không có `GITHUB_TOKEN`, GitHub áp đặt giới hạn **60 requests/giờ trên 1 địa chỉ IP public**.
   - Trong môi trường văn phòng hoặc mạng doanh nghiệp nơi nhiều kỹ sư / agent cùng chia sẻ 1 IP NAT, chỉ cần 2–3 trạm Thin Client chạy sync là toàn bộ mạng sẽ bị dính mã lỗi HTTP `403 Rate Limit Exceeded`.
2. **Hạn chế của `raw.githubusercontent.com`**:
   - Máy chủ CDN raw không hỗ trợ Directory Indexing (liệt kê danh sách tệp). Do đó, không thể "quét" thư mục `tables/` nếu không biết trước tên tệp.

#### 💡 Phán quyết giải pháp kỹ thuật:
- **Áp dụng Phương án Kết hợp: Manifest-Driven + On-Demand Streaming (Tối ưu Zero-Bloat)**:
  - **Bước 1 (Core Bundle)**: Tải canonical registry `legal_registry.yaml` và các tệp bắt buộc cấp tài liệu: `document_normative.md`, `clauses.json`, `metadata.yaml` từ `raw.githubusercontent.com`.
  - **Bước 2 (Table Resolution)**:
    - Khi tải bundle: Đọc trường `tables` trong `metadata.yaml` (hoặc `legal_registry.yaml`). Nếu metadata có khai báo danh sách tệp bảng (ví dụ `tables: ["table_1.md", "table_2.md"]`), thực hiện tải lần lượt qua raw URL.
    - Nếu metadata không chứa danh mục bảng: Bỏ qua việc tải trước `tables/`. Khi công cụ `get-table` được triệu gọi cục bộ với `table_id`, nếu tệp bảng chưa có trong cache cục bộ `.md/legal_docs/.../tables/`, công cụ sẽ kích hoạt On-Demand Fetcher tải đúng tệp bảng đó về cache.
- **Tiêu chuẩn thư viện**: Dùng `urllib.request` thuần của Python Standard Library với User-Agent chuẩn (`CCBA-Legal-ThinClient/1.0`), tuyệt đối không cài thêm `requests` hay `httpx` vào `ccba-legal-intel` (bảo toàn Zero-Bloat Invariant).

---

### 2. Đánh Giá Rủi Ro Đa Hệ Điều Hành (Windows vs Linux), Local Caching & Inode Determinism

#### 🔴 Các điểm mù tiềm ẩn trên Windows:
1. **Lỗi nối chuỗi URL bằng `Path` hoặc `os.path.join`**:
   - Trên Windows, nếu dùng `str(Path("01_vbpl") / slug / "clauses.json")` để ghép vào URL, chuỗi sẽ biến thành `01_vbpl\slug\clauses.json` (dấu backslash `\`). Khi gửi qua HTTP, máy chủ web sẽ trả về lỗi HTTP 404 hoặc 400 Bad Request.
   - **Bắt buộc**: Mọi định tuyến URL từ xa phải dùng dấu gạch chéo chuẩn POSIX `/` (`f"{RAW_BASE}/{cat}/{slug}/{filename}"`).
2. **Nguy cơ Hỏng Cache khi Mạng Gián Đoạn (Partial Write Corruption)**:
   - Nếu đang tải tệp `clauses.json` (dung lượng vài MB) mà bị đứt mạng hoặc timeout, nếu ghi trực tiếp vào đường dẫn đích, tệp sẽ bị dở dang (corrupted JSON). Lần sau kiểm tra `file.exists()` sẽ trả về `True` $\rightarrow$ Cache Hit giả mạo $\rightarrow$ `json.load()` crash.
   - **Bắt buộc (Atomic Write)**: Phải tải dữ liệu về tệp tạm `.tmp` hoặc bộ nhớ đệm, kiểm tra tính toàn vẹn (hoặc tải thành công không lỗi), sau đó mới thực hiện `Path.replace()` sang tệp chính thức.
3. **Tính tất định Inode & Sắp xếp (Inode Determinism)**:
   - Khi quét thư mục cache cục bộ để nạp danh sách bundle, luôn duy trì `sorted(cat_dir.iterdir(), key=lambda p: p.name)` theo đúng chuẩn Điều 5 Quy tắc Hệ thống (KISS & Filesystem Inode Ordering Invariance).

---

### 3. Đánh Giá Cơ Chế Graceful Degradation & Actionable UI Khi Mất Mạng (Air-Gapped)

#### 🛡️ Tiêu chuẩn phản hồi khi gặp sự cố mạng:
Thiết kế của Antigravity rất tiến bộ khi không để văng Unhandled Exception / Traceback. Tuy nhiên cần chuẩn hóa dictionary trả về để các downstream CLI/Agent bắt được trạng thái chính xác:

```python
# Cấu trúc trả về chuẩn hóa khi Offline / Lỗi mạng
{
    "status": "degraded_offline",
    "tier": "tier_3_cloud_rag_fallback",
    "error_reason": "network_unreachable_or_timeout",
    "message": (
        "💡 Không tìm thấy kho tri thức cục bộ và không thể tải qua Remote Streaming.\n"
        "👉 Hướng dẫn khắc phục:\n"
        "   1. Thiết lập biến môi trường trạm: export CCBA_LEGAL_KNOWLEDGE_PATH=\"/path/to/ccba-legal-knowledge\"\n"
        "   2. Hoặc sử dụng Cloud RAG (NotebookLM): ccba-legal query --cloud --notebook-id <id>"
    ),
    "target": str(dest_root),
    "bundles_synced": [],
    "registry_merge": {"updated": 0, "added": 0, "preserved": 0},
}
```

- Bắt cụ thể các ngoại lệ mạng: `urllib.error.URLError`, `urllib.error.HTTPError`, `TimeoutError`, `socket.timeout`, `ConnectionResetError`.
- Log cảnh báo ở mức `logger.warning()`, không in stack trace làm ô nhiễm terminal người dùng trừ khi có cờ `--verbose`/`DEBUG`.

---

### 4. Đánh Giá Phân Lát Micro-PR (Atomicity & Blast Radius)

Phân tách thành 2 Micro-PR hoàn toàn chuẩn xác theo **Guardrail 19**:

1. **Micro-PR 1 (`feat(legal-intel): remote streaming sync for thin clients`)**:
   - **Tệp thay đổi**: Duy nhất `packages/ccba-legal-intel/src/ccba_legal/sync/engine.py` (ước tính $\approx 80-110$ dòng code bổ sung).
   - **Tệp kiểm thử**: `packages/ccba-legal-intel/tests/test_remote_streaming_sync.py` ($\approx 100$ LOC kiểm thử với `unittest.mock`).
   - **Blast Radius**: Cô lập hoàn toàn trong package `ccba-legal-intel`. Không làm ảnh hưởng đến CI workflows, các package khác hay cấu hình Hub.
2. **Micro-PR 2 (`ci(release): automated wheel packaging workflow for github releases`)**:
   - **Tệp thay đổi**: `.github/workflows/package-wheels.yml`.
   - **Blast Radius**: Thuần túy hạ tầng CI/CD, kích hoạt độc lập khi release tag hoặc dispatch thủ công.

---

### 5. Phán Quyết Cuối Cùng & Điều Kiện Tiên Quyết Trước Khi Lập Trình

**PHÁN QUYẾT: `APPROVE_WITH_CONDITIONS` (Chấp thuận có điều kiện)**

Antigravity được phép tiến hành lập trình triển khai **Micro-PR 1** ngay khi cam kết đáp ứng đầy đủ 4 điều kiện sau:

1. **Định dạng URL chuẩn POSIX**: Luôn sử dụng `/` khi tạo URL tải GitHub Raw trên mọi hệ điều hành.
2. **Zero-API-Rate-Limit**: Tuyệt đối không dùng GitHub REST API không token. Tải qua CDN `raw.githubusercontent.com` với timeout 5.0s.
3. **Atomic File Download**: Sử dụng cơ chế ghi an toàn (tệp tạm `.tmp` $\to$ rename) để tránh ghi đè rác khi ngắt kết nối.
4. **Mocked Offline Test Coverage**: Bổ sung bộ test cô lập 100% sử dụng `unittest.mock.patch` mô phỏng: (a) Remote tải thành công; (b) Cache Hit 0s; (c) Timeout/Connection Error trả về `degraded_offline` đúng chuẩn.

*Kế hoạch đã sẵn sàng cho giai đoạn thực thi mã nguồn.*