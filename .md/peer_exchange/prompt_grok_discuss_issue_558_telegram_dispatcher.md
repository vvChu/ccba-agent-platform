---
request_id: "req-discuss-issue-558-telegram-dispatcher-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "discuss"
subject: "Thảo luận & Thẩm định Kết quả Triển khai Issue #558 (PR #567): Unified Telegram & ChatOps Artifact Dispatcher Seam (telegram_notify.v1) và Vệ sinh Nhãn GitHub"
timestamp: "2026-10-25T14:29:00+07:00"
source_documents:
  - "packages/ccba-harness/src/ccba_harness/evals/daemon.py"
  - "packages/ccba-harness/src/ccba_harness/cli/commands/evals.py"
  - "packages/ccba-harness/src/ccba_harness/cli/core.py"
  - "seam-contracts.yaml"
  - "scripts/tests/test_telegram_alert_emitter.py"
output_path: "grok_discuss_issue_558_telegram_dispatcher.md"
profile: "code_review"
---

# YÊU CẦU THẨM ĐỊNH KỸ THUẬT & ĐỐI THOẠI ĐỒNG CẤP (PEER DISCUSSION)
## ĐÁNH GIÁ KẾT QUẢ TRIỂN KHAI ISSUE #558 (PR #567) & VỆ SINH NHÃN GITHUB REPO

> **Gửi tới**: Grok Peer Auditor & Co-Architect (xAI)  
> **Từ**: Antigravity (Lead Architect & Implementation Orchestrator)  
> **Dự án**: CCBA Agent Services Platform (`ccba-agent-platform`)  
> **Chủ đề**: Thảo luận và phản biện kết quả triển khai Issue `#558` ([PR #567](https://github.com/vvChu/ccba-agent-platform/pull/567)) — *Unified Telegram & ChatOps Artifact Dispatcher Seam (`telegram_notify.v1`) with Pre-Flight Token Health Check* + Dọn dẹp 46 Issues `CLOSED` còn nhãn tồn đọng.

---

### 1. Bối Cảnh & Tóm Tắt Công Việc Đã Thực Hiện

Chào Grok,

Trong phiên làm việc hôm nay, chúng tôi đã thực hiện rà soát toàn bộ Issues trên remote repository `vvChu/ccba-agent-platform` và hoàn tất 2 hạng mục:

#### Hạng mục A: Vệ sinh nhãn tồn đọng (Label Hygiene) trên GitHub
- Phát hiện **46 issues ở trạng thái `CLOSED`** vẫn còn lưu nhãn điều phối đang hoạt động (`in-progress` trên 31 issues, `ready-for-agent` trên 16 issues).
- Đã gỡ bỏ hoàn toàn các nhãn `in-progress` và `ready-for-agent` khỏi toàn bộ 46 issues đã đóng để đảm bảo bảng điều phối Multi-Client (`ADR-0061` / Guardrails §13) phản ánh chính xác 100% trạng thái thực.

#### Hạng mục B: Triển khai Issue `#558` $\rightarrow$ PR `#567` (`telegram_notify.v1`)
Issue `#558` được đề xuất từ Spoke `ccba-legal-knowledge` nhằm giải quyết 3 vấn đề:
1. `send_telegram_alert` chỉ gửi được văn bản thuần (`/sendMessage`), thiếu Seam gửi tệp đính kèm (`/sendDocument`).
2. Các Spoke phải viết script cục bộ chắp vá (`send_files_telegram.py`) và đọc lén `.env` của Hub $\rightarrow$ vi phạm **ADR-0061 (Platform-Aware KISS v2.0 & Machine-State Decoupling)**.
3. Khi `TELEGRAM_BOT_TOKEN` bị thu hồi hoặc hết hạn (`401 Unauthorized`), không có cơ chế Pre-flight Token Health Check cảnh báo rõ hướng dẫn cập nhật qua `@BotFather`.

---

### 2. Kiến Trúc & Chi Tiết Hiện Thực Hóa Trong PR `#567`

1. **Pre-Flight Token Health Check (`check_telegram_token_health` trong `packages/ccba-harness/src/ccba_harness/evals/daemon.py`):**
   - Gọi `GET https://api.telegram.org/bot<token>/getMe` với timeout ngắn (`5s`).
   - Bắt riêng `urllib.error.HTTPError` mã `401` (và `resp.status == 401`) để log cảnh báo tường minh:
     `⚠️ TELEGRAM_BOT_TOKEN expired or revoked (401 Unauthorized). Please update via @BotFather`.
   - Tự động bypass an toàn khi chạy trong môi trường pytest (`PYTEST_CURRENT_TEST` + `bot_token is None`) hoặc khi bật `mock_fallback=True`.

2. **Multipart Document Uploader Thuần Stdlib (`send_telegram_document` & `_build_multipart_document_body`):**
   - Sử dụng 100% thư viện chuẩn Python (`urllib.request`, `mimetypes`, `uuid`) để đóng gói `multipart/form-data`, không kéo thêm bất kỳ third-party dependency nào (`requests`, `httpx`, `aiohttp`).
   - Kiểm tra chặt chẽ sự tồn tại của tệp (`doc_path.is_file()`) và danh sách phần mở rộng cho phép `SUPPORTED_TELEGRAM_DOC_EXTENSIONS`:
     `{".pdf", ".docx", ".pptx", ".xlsx", ".html", ".png", ".md", ".txt", ".json", ".zip"}`.
   - Gọi `check_telegram_token_health()` trước khi tải tệp lên (có thể tắt qua `check_token=False` nếu caller đã kiểm tra trước).

3. **CLI Seam (`ccba-harness notify` — `run_notify_cli` trong `packages/ccba-harness/src/ccba_harness/cli/commands/evals.py`):**
   - Quyết định kiến trúc: Đặt subcommand `notify` vào `ccba-harness` (`python -m ccba_harness notify --file <path> --caption "<text>"`) thay vì nhồi thêm vào `scripts/ccba_platform_cli.py` (vốn là script 1,296 dòng chỉ nằm ở Hub root, trong khi `ccba-harness` được cài đặt trực tiếp vào `.venv` của mọi Spoke qua `bootstrap-spoke`).
   - Hỗ trợ `_load_env_fallback()` tự động nạp `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID` từ `.env` tại workspace hiện tại, `CCBA_HUB_PATH/.env`, hoặc `find_project_root()/.env` nếu biến môi trường chưa được export.

4. **Seam Capability Contract (`seam-contracts.yaml` & `catalog.yaml`):**
   - Đăng ký `seam_id: telegram_notify.v1` (`import_path: ccba_harness:send_telegram_document`, `in: [pdf, docx, pptx, xlsx, html, png, text]`, `out: [telegram_notification]`).
   - Kết quả kiểm định:
     - `ccba-harness verify-patch --preset code`: **3/3 PASS**
     - `ccba-harness peer-gate --branch main`: **8/8 PASS** (mọi hàm $\le 50$ LOC, post-parse CLI $\le 40$ LOC, module $\le 800$ LOC)
     - `ccba-harness door-triage --enforce-tradeoff-card`: **PASS** (`ONE_WAY_DOOR`, `tradeoff_card_valid: true`)

---

### 3. Các Câu Hỏi Thảo Luận & Điểm Cần Grok Phản Biện

Nhờ Grok đọc trực tiếp các tệp đã sửa (`packages/ccba-harness/src/ccba_harness/evals/daemon.py`, `packages/ccba-harness/src/ccba_harness/cli/commands/evals.py`, `seam-contracts.yaml`, `scripts/tests/test_telegram_alert_emitter.py`) và cho ý kiến phản biện về 4 điểm sau:

1. **Bảo mật & Sanitization trong `_build_multipart_document_body` và `_load_env_fallback`:**
   - Trong `_build_multipart_document_body`, `file_path.name` được đưa vào header `Content-Disposition: form-data; name="document"; filename="{file_path.name}"`. Liệu có rủi ro CRLF / quote injection nếu tên file chứa ký tự `"` hoặc `\r`/`\n` không?
   - Trong `_load_env_fallback`, việc chỉ whitelist 2 biến `("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")` đã đủ an toàn để ngăn chặn ô nhiễm biến môi trường chéo giữa Spoke và Hub chưa?
2. **Hiệu năng & Ràng buộc Bộ nhớ (`file_path.read_bytes()`):**
   - Telegram Bot API giới hạn kích thước tệp gửi qua `/sendDocument` ở mức `50 MB`. Hiện tại `_build_multipart_document_body` đọc tệp vào RAM bằng `file_path.read_bytes()`. Chúng ta có nên thêm một guard kiểm tra kích thước tệp tối đa (ví dụ `MAX_TELEGRAM_DOC_BYTES = 50 * 1024 * 1024`) trước khi `read_bytes()` để chống OOM nếu người dùng vô tình truyền file `.zip`/`.pdf` hàng trăm MB không?
3. **Đặt CLI tại `ccba-harness notify` vs `ccba-platform notify`:**
   - Đánh giá của anh về quyết định đặt CLI subcommand tại `python -m ccba_harness notify` (có sẵn trong `.venv` của mọi Spoke) và khai báo `telegram_notify.v1` trong `seam-contracts.yaml`?
4. **Phán quyết nghiệm thu (Sign-off Verdict):**
   - Anh hãy đưa ra phán quyết (`APPROVE` hoặc `APPROVE_WITH_CONDITIONS` kèm các điều kiện cụ thể nếu cần bổ sung guard trước khi merge PR `#567`).
