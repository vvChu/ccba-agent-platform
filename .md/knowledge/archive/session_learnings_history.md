# 🧠 CCBA Platform Knowledge Base: Session Learnings & Architectural Invariants

> **Scope:** Hub (`ccba-agent-platform`) & Spokes (`ccba-legal-knowledge`, etc.)
> **Standard:** OKF v2.2, ADR 0016, ADR 0021, ADR 0031, ADR 0032.
> ⚠️ **Lưu ý:** Các mã băm commit SHA trước ngày 04/10/2026 trong tài liệu này có thể đã bị thay đổi do đợt tẩy rửa an toàn thông tin lịch sử (Security History Rewriting).

---

## 1. TVPL VIP 3-Tier Download Priority & Parameter Discovery (ADR 0031)

- **Tier 1 — VIP Digital Vector Searchable PDF (`part=-100` / `#ctl00_Content_ThongTinVB_filePDFHyperLink`):**
  - **Mỏ neo Pháp lý Tối thượng Cấp 1 (Primary Anchor of Trust)**: Bản PDF số hóa toàn văn (ví dụ QCVN 02 619 trang, QCVN 06 182 trang, TT 38 1,893 trang). Chứa trọn vẹn 100% thân văn bản, toàn bộ phụ lục, bảng biểu và đồ thị.
- **Tier 2 — VIP OpenXML Word Document (`part=-1&docx=1` / `#ctl00_Content_ThongTinVB_vietnameseHyperLink_Docx`):**
  - **Nguồn Dữ Liệu Gốc Vàng (Gold Source Input)**: Nạp trực tiếp vào `docx_converter.py` để sinh ra OKF v2.2 Markdown Bundle (phân rã biểu mẫu `templates/` và bảng tra cứu `tables/`).
- **Tier 3 — Gazette Scan PDF (`part=0` / `#ctl00_Content_ThongTinVB_pdfHyperLink`):**
  - Dự phòng khi TVPL chưa xuất bản bản PDF số hóa riêng.

---

## 2. Persistent Chromium VIP Session Engine & CLI (`python -m ccba_legal login`)

- **Profile Độc Lập:** Sử dụng `~/.gemini/antigravity/chrome_vip` để lưu Cookie phiên VIP Pro lâu dài.
- **Khởi chạy 1-Click:** Lệnh `python -m ccba_legal login` tự động mở Chrome/Edge trên cổng `9222`, cho phép đăng nhập 1 lần duy nhất, tránh bị Windows DPAPI chặn khi copy file cookie.
- **WebSocket Timeout Guard:** Bổ sung `timeout=8.0s` và bắt lỗi `(WebSocketTimeoutException, WebSocketConnectionClosedException)` trong `evaluate_js` và `navigate`, chống đơ luồng khi form ASP.NET PostBack/Reload.

---

## 3. Automated Contract Tests: CLI & Documentation Parity

- **`test_cli_doc_parity.py`:** Kiểm tra tự động tính khớp nối $100\%$ giữa các lệnh trong `cli.py` (`login`, `fetch`, `batch-fetch`, `convert`, `consolidate`, `process`) và hướng dẫn trong `SKILL.md`. Ngăn ngừa triệt để lỗi lệch pha tài liệu (Documentation Drift).

---

## 4. Spoke CI Gates Verification Pipeline

Mọi văn bản trước khi nghiệm thu vào kho tri thức bắt buộc phải vượt qua tuần tự 5 cổng kiểm định không dung thứ (Zero-Tolerance):
1. `python scripts/lint_visual_parity.py` (0 lỗi layout/thoát ký tự `\- ` và `&nbsp;&nbsp;\+ `)
2. `python scripts/validate_legal_spoke.py` (0 lỗi schema, AST, bảng biểu)
3. `python scripts/test_converter_regression.py` (100% gói vượt qua kiểm thử hồi quy)
4. `python scripts/verify_all_docs_against_pdf.py` (100% PDF Verified & SHA-256 Valid)
5. `python scripts/verify_cross_links.py` (100% liên kết điều khoản và phụ lục hợp lệ)

---

## 5. Spoke `.md` Directory Hygiene & Archiving Structure (ADR 0033)

- **Cấp gốc `.\.md\`**: Chỉ chứa các file cấu hình và mỏ neo tri thức tối thượng (`workspace_context.yaml`, `codebase_architecture_analysis.md`).
- **Thư mục con chuyên biệt**:
  - `.\.md\extracted_docs\`: Lưu trữ toàn bộ file Word (`.docx`) và PDF Công báo gốc đã nạp.
  - `.\.md\knowledge\`: Lưu trữ tri thức cốt lõi (`session_learnings.md`, architectural patterns).
  - `.\.md\archive\`: Nơi lưu trữ tất cả các script thử nghiệm, kiểm toán lịch sử và khảo sát (`audits/`, `inspections/`, `legacy_harvesters/`).
  - `.\.md\backups\`: Lưu trữ các bản sao lưu config (`.bak_*`).
  - `.\.md\data\`: Lưu trữ session locks, caches và audit logs.

---

## 6. Workflow Routing: `/ccba-new-feature` là Entry Point Duy Nhất Khi Có Issue ID

- **Quy tắc:** Khi đã xác định được Issue ID cần triển khai (ví dụ từ `/ccba-ask`, `/ccba-triage`, hoặc backlog review), **luôn đề xuất** `/ccba-new-feature #<id>` làm hành động tiếp theo.
- **KHÔNG BAO GIỜ** đề xuất `/ccba-implement`, `/ccba-to-spec`, hay `/ccba-to-tickets` làm entry point — đây là các bước con bên trong luồng `/ccba-new-feature`.
- **Lý do:** `/ccba-new-feature` bao trọn 8 bước lifecycle chuẩn (Factory Model):
  1. Pre-flight check & `git pull`
  2. Dọn branch cũ đã merge
  3. Bóc tách Issue (GitHub CLI hoặc Offline Fallback)
  4. Tạo branch chuẩn `feat/issue-<id>-*`
  5. Planning Mode (Triage Fast-Path + Reuse Assessment)
  6. Factory Model hand-off (route sang `/ccba-implement`, `/boost`, hoặc `/ccba-teamwork`)
  7. Coding & Verification (Quality Gates)
  8. Walkthrough & PR

  Nhảy thẳng vào `/ccba-implement` = bỏ qua 7 bước chuẩn bị.

---

## 7. Strict Legal Currency & Real-Time Validity Guardrail (Bảo Đảm Tính Hiện Hành Tuyệt Đối)

- **Nguyên tắc cốt lõi:** Mọi thông tin trao đổi, viện dẫn văn bản quy phạm pháp luật (VBPL), số hiệu luật, nghị định, thông tư và kịch bản thuyết trình (kể cả tệp dữ liệu mẫu, mock fixtures, demo slides) **BẮT BUỘC PHẢI LÀ VĂN BẢN ĐANG CÓ HIỆU LỰC (CURRENT / IN-FORCE)**.
- **Không dung thứ dữ liệu lỗi thời:** Tuyệt đối không sử dụng văn bản đã hết hiệu lực (như NĐ 175/2024, NĐ 15/2021, NĐ 06/2021) làm căn cứ quy chuẩn áp dụng hiện tại, trừ trường hợp so sánh đối chiếu lịch sử văn bản.
- **Nguồn đối chiếu:** Luôn tra cứu và đồng bộ với Registry Pháp lý CCBA (`legal_registry.yaml`) — Cụ thể từ 01/07/2026:
  - **Luật Xây dựng 2025** (Luật số `135/2025/QH15`).
  - **Nghị định 217/2026/NĐ-CP** (Quản lý Hoạt động Xây dựng — Thay thế NĐ 175/2024 và NĐ 15/2021).
  - **Nghị định 207/2026/NĐ-CP** (Quản lý Chất lượng & Bảo trì — Thay thế NĐ 06/2021).

---

## 39. Browser Target WebSocket CDP, Centralized TVPL DOM Selectors & Ingest Slug Standardization

- **Vấn đề Phát Hiện:**
  1. **Chromium Scope Bug khi Cấu Hình Tải File (`Browser.setDownloadBehavior`):** Lệnh `Browser.setDownloadBehavior` bị gọi trên Page Target WebSocket (`ws://127.0.0.1:9222/devtools/page/...`) thay vì Browser Target WebSocket (`/json/version`). Các phiên bản Chromium mới từ chối lệnh này ở cấp Tab khiến việc tải tệp tự động về thư mục Bundle bị vô hiệu hóa.
  2. **Trùng Lặp DOM Selectors & Lệch Pha Đăng Nhập TVPL:** TVPL cập nhật form đăng nhập sang `#usernameTextBox`, `#passwordTextBox`, `#loginButton`. Selector cũ hardcoded rải rác ở `cdp.py`, `providers.py`, `tier_downloader.py` dẫn đến rớt phiên VIP về Guest và tải nhầm link tiện ích (`/bieumau`) thành tệp rác `.dat`.
  3. **Thiếu Tùy Chọn Định Danh Slug Bundle (`--slug`) Trên CLI `ingest`:** Lệnh `ingest` tự động lấy số hiệu thông tư (ví dụ `15_2017_tt_bxd`) làm tên thư mục, trong khi đối với Quy chuẩn kỹ thuật quốc gia (`02_qcvn`) định danh chuẩn mực phải là `qcvn_09_2017_bxd`.
  4. **ASP.NET Query Filtering đối với Ký tự `/`:** Query tìm kiếm có chứa `/` (`15/2017/TT-BXD`) bị IIS chặn mã hóa `%2F`, khiến kết quả trả về rỗng và fallback fuzzy-redirect sang sai văn bản (`Nghị quyết 15/2017/NQ-HĐND`).

- **Giải Pháp Khái Quát Hóa Toàn Hệ Thống (System-Wide Generalization):**
  1. **Browser Target WebSocket CDP Client (`cdp.py`):**
     - Kết nối trực tiếp đến `http://127.0.0.1:{port}/json/version` lấy `webSocketDebuggerUrl` để gửi `Browser.setDownloadBehavior` cấp Browser, đảm bảo 100% tệp nhị phân tải về đúng thư mục chỉ định.
  2. **Centralized DOM Selectors Single Source of Truth (`selectors.py`):**
     - Đóng gói toàn bộ selectors đăng nhập, popup xác nhận đa phiên, nhãn VIP, và mẫu link tiện ích loại trừ vào `TVPLSelectors`.
     - Đồng bộ hóa toàn bộ các module `cdp.py`, `providers.py`, `session.py`, `tier_downloader.py` kế thừa từ `TVPLSelectors`.
  3. **Universal `--slug` CLI Flag & Asset Normalization (`cli.py`):**
     - Bổ sung `-s / --slug` vào `ingest_parser`. Khi có cờ `--slug`, CLI tự động đồng bộ tên thư mục bundle, tên file DOCX và PDF nguồn sang `<slug>.docx` và `<slug>.pdf`.
  4. **Query Sanitization & Turnstile Bypass (`providers.py`):**
     - Chuẩn hóa query thay thế `/`, `:`, `-` bằng dấu cách (`quote_plus`), tự động gọi `cdp.handle_cloudflare()` chờ và giải phóng Turnstile challenge.

---

## 8. Swiss Minimalist & Storytelling Presentation Builder (`ccba-ooxml.pptx`)

- **Core Pattern P8.1 — Hai Giai Đoạn Phân Tách (Markdown AST $\rightarrow$ SlideSpec $\rightarrow$ PPTX Render):**
  - **Pha 1 (`MarkdownDeckParser`):** Phân tích AST từ Markdown tiêu chuẩn (Frontmatter, badging `[TAG]`, split columns `::: split`, native pipe tables, callout cards `> [!NOTE]`, Cole Knaflic archetypes `::: big-idea`, `::: agenda`, `::: steps`, `::: quote`) thành cấu trúc trung gian trừu tượng `SlideSpec`.
  - **Pha 2 (`DeckBuilder`):** Ánh xạ `SlideSpec` sang các shape và textbox của `python-pptx` với hệ lưới 12 cột (12-column grid system), tự động căn chỉnh khoảng trắng (Negative Space / Breathing Room) và phân cấp Typography cực hạn (Display Title 36-40pt Bold, KPI Hero Number 48-60pt Bold, Body Text 14-16pt Regular).
- **Core Pattern P8.2 — Design Tokens & High-Contrast Swiss Color Palette:**
  - Chuẩn hóa toàn bộ màu sắc, kích thước và phông chữ qua dataclass `CCBAPresentationTheme` (Primary Navy `#363883`, Accent Red `#DA251C`, Cyan `#0093DD`, Surface `#F4F6F9`, Text `#1A202C`).
  - **Rào chắn WCAG 2.1 AA:** Tuyệt đối không phủ màu nền tối toàn slide gây chói/mờ trên máy chiếu công trường. Sử dụng màu nhận diện CCBA như **Surgical Accent Colors** (chấm tag 6px, thanh bar mảnh 2px, số KPI nổi bật).
- **Core Pattern P8.3 — Safe Dynamic JavaScript DOM Selectors:**
  - Luôn sử dụng `json.dumps(selector)` khi nhúng selector vào template JavaScript sinh động (`document.querySelector(${json.dumps(s)})`), chống hoàn toàn lỗi cú pháp vỡ chuỗi khi selector chứa dấu nháy đơn (`input[placeholder*='Tên đăng nhập']`).
- **Core Pattern P8.4 — Strict Markdown Table Delimiter Detection:**
  - Nhận diện bảng Markdown thông qua cặp dòng tiêu đề + dòng phân cách cú pháp (`| :--- |`), ngăn ngừa ngộ nhận các dòng văn xuôi có ký tự `|` thành bảng dữ liệu.

---

## 9. Two-Tier Traceability Matrix, Status Regex & Type-Safety Hardening (ADR 0037, ADR 0051)

- **Core Pattern P9.1 — Hai Tầng Phân Tách Ma Trận Truy Vết Kiến Trúc (Two-Tier Traceability Matrix):**
  - **Vấn đề giải quyết:** Khi Hub chạy công cụ biên dịch `sync_hub_adr_matrix.py` qua Spoke, việc ghi đè bảng ma trận đơn nguyên (monolithic table) dẫn đến mất mát các ADR nghiệp vụ nội bộ tại Spoke hoặc gây xung đột số hiệu (ID Collision) khi cả Hub và Spoke cùng dùng dải số `0001+` (ví dụ Hub có ADR 0001 về Skill Steps, còn Spoke `ccba-legal-knowledge` có ADR 0001 về VBHN Dual-Track Provenance).
  - **Kiến trúc Hai Tầng (Two-Tier Model):**
    - **Tier 1 — Platform Constitution (Hub ADRs):** Danh mục 55 ADRs của nền tảng, gắn liên kết chuẩn mực trỏ tới Hub repository trên GitHub kèm Living Skill Radar quét tự động cross-references (`SKILL.md`, `AGENTS.md`, `workflows/`, `CONTEXT.md`).
    - **Tier 2 — Domain-Specific Architecture Decisions (Spoke ADRs):** Quét cục bộ thư mục `docs/adr/` của Spoke, hiển thị dưới dạng bảng riêng biệt với liên kết tương đối nội bộ Spoke (`0001-*.md`).
  - **Bảo Toàn Bất Biến (Non-Destructive Section Preservation):** Tự động nhận diện thẻ `<!-- CUSTOM_SECTIONS_START -->` ... `<!-- CUSTOM_SECTIONS_END -->` hoặc các đề mục `## ` tùy chỉnh ngoài danh mục auto-generated để bảo toàn 100% các bảng đối soát và ghi chú miền nghiệp vụ riêng của Spoke.
  - **Cổng Kiểm Định CI Parity (`--check`):** Hỗ trợ chế độ dry-run và check mode trả về mã thoát `0/1` kèm unified diff để tích hợp vào CI/CD chống Documentation Drift.

- **Core Pattern P9.2 — Comprehensive ADR Status Regex & Non-ADR File Exclusion:**
  - **Status Regex Parity:** ADR markdown thực tế có thể sử dụng nhiều biến thể trạng thái khác nhau: frontmatter YAML (`status: accepted`), đề mục H2 (`## 1. Trạng Thái (Status)\n**ACCEPTED**`), hoặc danh sách gạch đầu dòng (`* **Status:** Accepted`, `- **Status:** Accepted`). Regex bắt trạng thái phải bao quát tiền tố list marker `(?:\*|-)?\s*\*\*\s*Status:\s*\*\*` thay vì chỉ tìm `\*\*Status:\*`.
  - **Non-ADR File Filter:** Trong thư mục `docs/adr/`, các tệp markdown phụ trợ (như `notes.md`, `guidelines.md`, `template.md`) phải được lọc bỏ qua điều kiện `[a for a in adr_list if a["num"] > 0]`, ngăn ngừa ngộ nhận thành ADR và sinh ra dải số hiệu `0000` giả mạo.

- **Core Pattern P9.3 — Strict Mypy Overrides: Narrowing over Blanket Suppression (Anti-Pattern AP9.1):**
  - **Anti-Pattern AP9.1 (Blanket Ignore Errors Suppression):** Dùng `[[tool.mypy.overrides]] module = ["package.*"] ignore_errors = true` trong `pyproject.toml` để vượt qua CI tạm thời là một anti-pattern nguy hiểm làm suy yếu hệ thống type-safety của toàn bộ monorepo.
  - **Chuẩn Hóa Type Annotations Tận Gốc:** Thay vì vô hiệu hóa kiểm tra kiểu, lập trình viên bắt buộc phải:
    1. Ép kiểu tường minh cho các hàm nhị phân và I/O (ví dụ `int(val)` từ `struct.unpack`, `Document(str(path))` từ docx).
    2. Định kiểu tường minh cho biến font (`font_bold: Any`) và dictionary cấu trúc (`fig_entry: dict[str, Any]`).
    3. Thay thế lambdas không định kiểu bằng named helper functions có type hints.
    4. Chỉ cấu hình `ignore_missing_imports = true` cho các thư viện bên ngoài chưa có type stubs (`docx.*`, `PIL.*`).

- **Core Pattern P9.4 — Deduplicated Numeric Normalization in Legal Table Footnotes:**
  - Khi chuẩn hóa chú thích bảng từ Word DOCX, nếu văn bản gốc vừa có `has_explicit_numbered` (nhận diện tiền tố số như `1) ` hoặc `1. `) vừa được gán lại nhãn chuẩn `**CHÚ THÍCH 1:**`, việc không bóc tách tiền tố số cũ sẽ gây lặp số thứ tự: `**CHÚ THÍCH 1:** 1) Nội dung`. Bắt buộc phải áp dụng bước làm sạch `re.sub(r"^[0-9]+[)\.]\s*", "", fn_clean).strip()` sau khi làm sạch từ khóa `CHÚ THÍCH`.

---

## 10. Federated RAG & ADR-Compliant Dynamic Import (Issue #232)

- **Core Pattern P10.1 — Tier 0 ← Tier 1 Dynamic Import via try/except ImportError:**
  - Khi package Tier 0 (`ccba-ai`) cần dùng chức năng từ Tier 1 (`ccba-legal-intel`), sử dụng `try: from ccba_legal.xxx import yyy; except ImportError: pass` tại module level. Tool MCP chỉ đăng ký khi dependency thực sự có mặt. Áp dụng trong `mcp_server.py` để đăng ký `query_legal_ground_truth` mà không tạo hard dependency (ADR 0044).

- **Core Pattern P10.2 — CI Docs Validator: Portable Links & Orphan Knowledge Gate:**
  - **Anti-Pattern AP10.1 (Non-portable `file:///` absolute links):** Tất cả links trong `.md/knowledge/` phải dùng repo-relative path (`../../../docs/adr/xxx.md`) thay vì `file:///d:/GitHubProjects/...`. CI `validate_docs.py` chặn hard error trên Linux runner.
  - **Anti-Pattern AP10.2 (Orphan Knowledge Notes):** File mới trong `.md/knowledge/` mà chưa đăng ký trong `index.md` sẽ fail `test_wiki_health_linter_real_workspace`. Luôn thêm entry vào `index.md` khi tạo knowledge file.
  - **Anti-Pattern AP10.3 (conversation:// links in committed docs):** URI scheme `conversation://` là local-only cho Antigravity IDE. Không bao giờ commit vào repo — thay bằng plain text.

- **Core Pattern P10.3 — Module-Level Singleton Cache cho MCP Latency:**
  - Hàm convenience `query_ground_truth()` ban đầu tạo `FederatedLegalEngine()` mới mỗi lần gọi — mỗi lần rebuild BM25 index. Copilot Review phát hiện → chuyển sang `_cached_engine` singleton tại module level. Pattern: `global _cached_engine; if _cached_engine is None: _cached_engine = Engine(...)`.

- **Core Pattern P10.4 — Embedding Cache Freshness via SHA-256 Sidecar:**
  - Cache `embeddings.npy` chỉ kiểm tra `len(matrix) == len(chunks)` dẫn đến stale cache khi corpus thay đổi mà giữ nguyên số chunk. Fix: lưu `.sha256` sidecar file cùng thư mục, validate hash trước khi load cache.

---

## 11. Workflows-to-Skills Migration, Namespace Standardization & Spoke Hygiene (ADR 0056)

- **Core Pattern P11.1 — False-Positive OKF Discrimination in Document & Link Linters:**
  - **Vấn đề:** Các linter markdown (`link_auditor.py`) khi kiểm tra schema OKF có thể bị false-positive nếu chỉ dựa vào sự xuất hiện của các trường frontmatter phổ biến như `status:` hoặc `timestamp:`, dẫn đến việc các tài liệu kỹ thuật, bảng hỏi discovery hay ADRs bị ép vào bộ quy tắc kiểm tra văn bản pháp quy (bắt buộc `type: Law/Decree/Circular...`).
  - **Giải pháp:** Siết chặt điều kiện nhận diện OKF: Chỉ kích hoạt kiểm tra OKF khi tệp nằm trong thư mục `legal_docs` hoặc chứa các trường định danh pháp quy đặc thù (`document_number`, `parent_document`, hoặc `type` thuộc danh sách loại hình VBPL).

- **Core Pattern P11.2 — Windows Packaging Distribution Metadata Scan Timeout:**
  - **Vấn đề:** Khi `googleapiclient` hoặc `google.api_core` được nạp lần đầu trong tiến trình Python trên Windows, cơ chế `check_python_version()` gọi `importlib.metadata.packages_distributions()`. Hàm này duyệt đệ quy qua toàn bộ cây thư mục `AppData\Roaming\Python\...` để kiểm tra `os.stat()`, có thể mất từ 15-30 giây và kích hoạt `pytest-timeout` nếu timeout mặc định được cấu hình là 30s.
  - **Giải pháp:** Đối với các integration tests có liên quan đến cloud SDKs hoặc Spoke init bundle, cần thiết lập timeout chuyên biệt (`-o timeout=60` hoặc `@pytest.mark.timeout(60)`) để tránh ngắt luồng giả mạo trong môi trường máy phát triển Windows.

- **Core Pattern P11.3 — Prefix-Stripping Mapping in Scaffolding & Synchronizer:**
  - **Vấn đề:** Khi thư mục kỹ năng mang tiền tố tổ chức `ccba-<name>` (ví dụ `ccba-maskara`), các mã nguồn hỗ trợ tại `scripts/` hoặc thư viện vẫn giữ nguyên tên gốc (`scripts/maskara.py`). Nếu scaffolder chỉ tìm kiếm theo tên kỹ năng đầy đủ sẽ gây lỗi gãy liên kết (Broken Script Reference).
  - **Giải pháp:** `skill_generator.py` và `coordinator.py` bắt buộc phải triển khai cơ chế bóc tách tiền tố (`name_no_prefix = name.removeprefix('ccba-').removeprefix('bigbim-')`) để tìm kiếm song song cả tên có tiền tố và không có tiền tố trong danh sách ứng viên (candidate scripts).

- **Core Pattern P11.4 — Two-Way Forwarding Aliases & Automated Legacy Archival:**
  - **Vấn đề:** Khi đổi tên kỹ năng trên Hub, các trạm Spoke nếu chỉ sao chép thư mục mới sẽ bị hiện tượng Zombie Bloat (tồn tại song song cả thư mục cũ và mới, cùng các tệp `.agents/workflows/*.md` lỗi thời).
  - **Giải pháp:** Triển khai bảng `SKILL_DEPRECATION_ALIASES` 2 chiều trong synchronizer (`coordinator.py`). Trong quá trình đồng bộ, Hub chủ động quét và xóa thư mục cũ tại Spoke, đồng thời đổi tên các file `.md` trong `.agents/workflows/` thành `.md.bak` (gắn nhãn `DEPRECATED_MIGRATED_TO_SKILL`), đảm bảo Spoke luôn sạch sẽ và chỉ sử dụng kỹ năng chuẩn.

---

## 12. GitHub Copilot Review Schema, Multi-Tier Release Gate Audit & Namespace Invariants

- **Core Pattern P12.1 — Copilot Review Schema & State Gating Anti-Pattern:**
  - **Vấn đề:** Trong GitHub CLI (`gh pr view --json reviews`), đối tượng reviewer sử dụng khóa `.author.login` thay vì `.user.login` (vốn là khóa của GitHub REST API). Ngoài ra, bot GitHub Copilot khi đưa ra các khuyến nghị sửa đổi quan trọng thường nộp bài với trạng thái `state: "COMMENTED"` và nhúng tiêu đề `### 🟡 Changes recommended` cùng các suppressed comments vào phần `body`, thay vì gán trạng thái chính thức *"CHANGES_REQUESTED"*. Nếu script release gate hoặc CI chỉ kiểm tra `state == "CHANGES_REQUESTED"` hoặc chỉ đọc inline diff comments (`pulls/{number}/comments`), toàn bộ các khuyến nghị của Copilot sẽ bị lọt lưới và PR bị merge sớm.
  - **Giải pháp:** Xây dựng quy trình audit đa tầng (Multi-tier Audit) trong `scripts/validation/audit_pr_comments.py`:
    1. Kiểm tra `reviewRequests` để phát hiện Copilot đang trong quá trình phân tích (trả về exit code 2, bắt buộc chờ).
    2. Đọc chính xác `author.login` và quét `### 🟡 Changes recommended` / *"CHANGES_REQUESTED"* trong review `body` (trả về exit code 1 nếu chưa xử lý).
    3. Quét toàn bộ inline comments thông qua endpoint `repos/:owner/:repo/pulls/{pr_number}/comments` có cờ `--paginate` để tránh sót trang.
    4. Quét các bình luận hội thoại chung trên PR (`comments`).
    5. Chỉ cho phép merge khi tất cả các điểm hợp lý đã được sửa đổi và kiểm thử, hoặc có giải trình chính thức trong `walkthrough.md`.

- **Core Pattern P12.2 — Strict Whitelist vs Prefix Matching in Governance Linting:**
  - **Vấn đề:** Khi định nghĩa các kỹ năng ngoại lệ (như `platform-loader`) bên cạnh các tiền tố chuẩn (`ccba-`, `bigbim-`), việc sử dụng chung hàm `name.startswith(("ccba-", "bigbim-", "platform-loader"))` khiến bất kỳ kỹ năng rác nào có tiền tố `platform-loader-*` (ví dụ `platform-loader-fake`) đều lọt qua CI Gate Namespace Purity.
  - **Giải pháp:** Tách biệt rõ ràng giữa tiền tố và phần tử ngoại lệ đơn lẻ: `name.startswith(("ccba-", "bigbim-")) or name == "platform-loader"`. Bổ sung unit tests chặn triệt để các biến thể tiền tố ngoại lệ giả mạo.

- **Core Pattern P12.3 — Test File Exemption from Structural Architecture Drift:**
  - **Vấn đề:** Bộ kiểm tra độ trôi dạt kiến trúc (`drift_auditor.py`) theo dõi các thư mục cốt lõi (`packages/`, `scripts/`, `skills/`). Khi một nhà phát triển thêm mới hoặc xóa bỏ một bài unit test độc lập trong `scripts/tests/`, linter kích hoạt lỗi `Structural drift detected` và yêu cầu cập nhật các tài liệu kiến trúc cấp cao (`README.md`, `PLATFORM.md`), gây ra cảnh báo giả (false-positive).
  - **Giải pháp:** Thêm điều kiện miễn trừ `not filepath.startswith("scripts/tests/")` trong logic phát hiện thay đổi cấu trúc của `drift_auditor.py`, phân định ranh giới rõ ràng giữa thay đổi kiến trúc hệ thống và bổ sung ca kiểm thử phần mềm.

---

## 13. Hub-Spoke Command & Argument Parity Invariant

- **Core Pattern P13.1 — Unified CLI & Multi-Engine Argument Alignment:**
  - **Vấn đề:** Khi hệ thống cung cấp nhiều cách thức kích hoạt cùng một tác vụ (ví dụ: `scripts/ccba_platform_cli.py sync-spoke` vs `scripts/sync_spoke.py` vs slash commands `/ccba-update-spoke`), nếu các cờ tham số (`--apply`, `--force`, `--bootstrap`, `--include-sandboxes`, `--archetype`) không được truyền đồng nhất ở cả parser và delegate layers, người dùng hoặc Agent sẽ gặp lỗi không đồng bộ hành vi giữa các entrypoints.
  - **Giải pháp:** Thiết lập sự đồng nhất 100% giữa CLI parser của Spoke Sync engine (`scripts/spoke/sync/cli.py`), Unified Platform CLI (`scripts/ccba_platform_cli.py`) và các file hướng dẫn kỹ năng (`SKILL.md`). Bổ sung ca kiểm thử tham số CLI tự động (`test_ccba_platform_cli_arguments`, `test_run_spoke_sync_cli_with_bootstrap`) trong CI để ngăn chặn regression.

- **Core Pattern P13.2 — Phantom Directory Prevention in Zero-Workflow Era:**
  - **Vấn đề:** Sau khi di dời toàn bộ workflows sang kỹ năng (`workflows: 0`), logic đồng bộ cũ trong `coordinator.py` vẫn gọi `spoke_workflows_dir.mkdir(parents=True, exist_ok=True)` vô điều kiện, làm tự sinh thư mục rỗng `.agents/workflows/` tại các Spoke mới.
  - **Giải pháp:** Chỉ tạo thư mục workflows khi `wfs_to_sync` có tệp cần đồng bộ (`if not dry_run and wfs_to_sync:`). Nếu Spoke đã có sẵn thư mục này từ trước, hệ thống quét và chuyển đổi sang `.md.bak` với nhãn `DEPRECATED_MIGRATED_TO_SKILL`. Nếu Spoke mới tinh, hoàn toàn không tạo thư mục thừa.

---

## 14. Architecture Seam Hardening, Relative Link Resolution & Zero-Exemption AST Governance

- **Core Pattern P14.1 — Relative Link Resolution Depth in Triple-Nested Skills:**
  - **Vấn đề:** Khi một tài liệu kỹ năng nằm sâu 3 cấp thư mục (`.agents/skills/<skill-name>/SKILL.md`), nếu liên kết tương đối trỏ tới gói Monorepo chỉ sử dụng 2 cấp (`../../packages/<pkg>`), đường dẫn sẽ bị phân giải sai thành `.agents/packages/<pkg>` (không tồn tại), dẫn đến lỗi vỡ liên kết trong bài kiểm thử quản trị `tests/governance/test_workflow_script_parity.py` (`test_workflow_and_skill_relative_links_resolve`).
  - **Giải pháp:** Bắt buộc sử dụng đúng 3 cấp lùi thư mục `../../../packages/<pkg>` khi tham chiếu từ các tệp `SKILL.md` hoặc tài liệu nằm trong thư mục con của `.agents/skills/`.

- **Core Pattern P14.2 — Non-Breaking Facade Seam Hardening (Wrappers over Public Instances):**
  - **Vấn đề:** Khi tái cấu trúc các tệp facade tại `scripts/` (ví dụ: `scripts/maskara.py`) để tuân thủ ranh giới gói và loại bỏ việc import vào các submodule private (`_locator`, `_redactor`), nếu lập trình viên xóa bỏ các hàm tiện ích (`normalize_agent_name`, `get_default_roots`, `resolve_targets`) khỏi `__all__`, điều này sẽ gây phá vỡ tương thích ngược (breaking change) cho các caller bên ngoài.
  - **Giải pháp:** Không xóa hàm tiện ích và không import private module; thay vào đó, re-export chúng dưới dạng các thin wrappers gọi trực tiếp các phương thức public instance trên lớp dịch vụ chính (`MaskaraScanner().normalize_agent_name(...)`). Mô hình này vừa đảm bảo tương thích ngược 100% cho mọi caller cũ, vừa tuân thủ triệt để ranh giới Seam trong kiểm tra AST.

- **Core Pattern P14.3 — Zero-Exemption AST Governance & Archive Directory Exclusion:**
  - **Vấn đề:** Việc duy trì các ngoại lệ hardcoded dạng `if py_file.name == 'maskara.py': continue` trong bộ kiểm tra hợp đồng phụ thuộc (`check_dependency_contracts.py`) làm suy yếu tính nghiêm ngặt của CI và tạo tiền lệ xấu. Đồng thời, sự tồn tại của các script demo một lần trong thư mục hoạt động `scripts/` làm phân tán không gian tìm kiếm của AI Agent.
  - **Giải pháp:** Di chuyển toàn bộ các script thử nghiệm lịch sử vào thư mục `archive/` (bảo toàn 100% lịch sử Git), đồng thời đưa `archive` vào whitelist loại trừ của AST linter. Gỡ bỏ hoàn toàn mọi bypass hardcoded theo tên file để đạt chuẩn Zero-Exemption trên toàn bộ 328+ tệp mã nguồn của monorepo.

---

## 15. Two-Stage Granularity Decision Framework, Fleet-Wide GPI Metric & Multi-Tier Skills Architecture (ADR 0057)

- **Core Pattern P15.1 — Two-Stage Granularity Decision Framework & Mathematical GPI Index ($S, K, A, P$):**
  - **Vấn đề:** Khi mở rộng kho kỹ năng (fleet of 100 skills), hệ thống đối mặt với tình thế lưỡng nan về độ mịn (Granularity Dilemma): nếu tạo quá nhiều micro-skills sẽ gây phân mảnh và tràn ngân sách token (Prompt Bloat / Lost-in-the-middle); ngược lại nếu gộp quá nhiều logic vào một skill sẽ biến thành "quả cầu bùn nhận thức" (Ball of Mud).
  - **Giải pháp:** Thiết lập Khung Quyết Định Hai Giai Đoạn và chuẩn hóa chỉ số Granularity & Placement Index (GPI) trong `packages/ccba-harness` (ADR 0057):
    + *Giai đoạn 1 (Structural Invariant Gates):* Cổng 0 (Determinism Gate) chặn đứng tác vụ thuần giải thuật (đưa xuống Tier 1 Package Function / Deep Seams); Cổng 1 (Orchestration Gate) chặn tác vụ đa luồng/StateGraph/HITL (đưa lên Tier 3 Composite Orchestrator).
    + *Giai đoạn 2 (GPI Formula):* $\mathbf{GPI} = (S \times 2.5) + (K \times 2.0) + (A \times 2.0) - (P \times 1.5)$. Nếu $\text{GPI} < 12.0 \rightarrow$ Tier 2A (Progressive Reference trong `references/*.md`); Nếu $\text{GPI} \ge 12.0 \rightarrow$ Tier 2B (Standalone Kernel Skill trong `.agents/skills/ccba-<name>/`).

- **Core Pattern P15.2 — Quản Trị Vùng Mù Scripts (Blind Spot Governance) qua Deep Seams:**
  - **Vấn đề:** Quá trình audit hạm đội phát hiện 14 skills chứa tới 105 scripts phụ trợ với 35.680 LOC. Các scripts này nằm ngoài phạm vi kiểm định chất lượng monorepo nếu chỉ quét `packages/`, dẫn tới nguy cơ nợ kỹ thuật tiềm ẩn, trùng lặp mã nguồn và trôi dạt hợp đồng phụ thuộc.
  - **Giải pháp:** Quy hoạch di dời các scripts phức tạp xuống packages tương ứng (`packages/ccba-legal-intel`, `packages/ccba-pdf-prep`, `packages/ccba-ai`...) thông qua giao diện hàm rõ ràng (Deep Seams). Mã nguồn trong `scripts/` của skill chỉ đóng vai trò thin adapter (10–30 LOC) gọi vào các Deep Seams này, bảo đảm 100% logic xác định đều được bảo vệ bởi unit test và linting tự động.

- **Core Pattern P15.3 — Khắc Phục Lỗi Lồng Đường Dẫn Windows Node.js trong Plugin PreToolUse Hooks:**
  - **Vấn đề:** Khi Antigravity IDE chạy trên Windows, cơ chế plugin telemetry hook tự động tạo cấu hình trong `hooks.json` với đường dẫn file bị bao bọc trong dấu ngoặc kép dạng `"C:\Users\...\bundle.js"`. Khi Node.js thực thi `path.isAbsolute(hookPath)`, ký tự ngoặc kép ở đầu khiến hàm trả về `false`, làm Node.js tự động ghép `pluginDir` vào phía trước thành `C:\...\plugins\<plugin>\"C:\...\bundle.js"`, gây lỗi `Cannot find module` và làm tê liệt toàn bộ tool calls trong môi trường agent.
  - **Giải pháp:** Vô hiệu hóa file cấu hình `hooks.json` bằng nội dung rỗng `{}` và thiết lập thuộc tính bảo vệ tệp `IsReadOnly = $true` trên PowerShell. Biện pháp này ngăn chặn vĩnh viễn tiến trình nền của IDE tự ý ghi đè đường dẫn lỗi, phục hồi hoàn toàn khả năng gọi tool của Agent mà không ảnh hưởng tới luồng công việc.

---

## 16. Fleet-Wide 3-Tier Skills Migration, Reference Harmonization & Single-Writer Orchestrators (BLUEPRINT-2026-SKILLS-001)

- **Core Pattern P16.1 — Relative Link Depth Harmonization in Progressive References (4-Level Traversal):**
  - **Vấn đề:** Khi một micro-skill được hợp nhất thành Progressive Reference trong thư mục `references/` của Master Skill (`.agents/skills/<master>/references/<ref>.md`), độ sâu đường dẫn tăng từ 3 lên 4 cấp so với repo root. Nếu giữ nguyên các liên kết tương đối cũ (`../../../docs/...`), validator sẽ báo lỗi Broken Link Error và chặn CI build trên GitHub Actions.
  - **Giải pháp:** Khi tái định tuyến tài liệu sang `references/`, chuẩn hóa đường dẫn tương đối: các tài liệu trỏ ra ngoài repo root phải sử dụng 4 cấp lùi `../../../../`; các tài liệu bổ trợ đi kèm cùng được di dời sang `references/` phải chuyển sang liên kết đồng cấp `./<sibling>.md`. Tránh dùng markdown link trỏ tới các file artifact chỉ sinh ra khi chạy runtime (dùng cú pháp inline code thay thế).

- **Core Pattern P16.2 — Short-Circuit Gate 1 for Composite Orchestrators & Single-Writer Protocol Enforcement:**
  - **Vấn đề:** Các quy trình điều phối cấp cao (Tầng 3) vi phạm Cổng 1 (Orchestration Gate) do tính chất điều phối đa tác tử, chuyển trạng thái phức tạp hoặc cần con người duyệt (HITL). Nếu bộ kiểm định `SkillValidator` bắt buộc phải có khối `gpi: {s, k, a, p}`, điều này gây mâu thuẫn kiến trúc vì công thức GPI chỉ áp dụng để phân định giữa Tier 2A và Tier 2B.
  - **Giải pháp:** Cập nhật `SkillValidator` nhận diện `tier: orchestrator` và short-circuit hợp lệ tại Cổng 1 mà không yêu cầu khối `gpi:`. Đồng thời, bổ sung cơ chế kiểm toán tự động cưỡng chế Single-Writer Protocol (ADR-0053): bất kỳ Orchestrator nào có dấu hiệu điều phối subagents (`dispatch worker`, `spawn subagent`, `team_sheet`) bắt buộc phải cam kết quy tắc Orchestrator là thực thể duy nhất ghi codebase/logs, các workers phân rã chỉ đọc trong sandbox độc lập.

---

## 17. Slash Command Parity & Active Commands Verification Guardrail

- **Core Pattern P17.1 — Phân định Tuyệt đối giữa Registered Slash Commands và Prompt-Driven / Reference Skills:**
  - **Vấn đề:** Sau các đợt refactor hợp nhất kỹ năng (ADR-0057), một số micro-skills cũ (như `improve-codebase-architecture`) được chuyển thành tài liệu tham chiếu (`references/codebase_refactor_guide.md`) nằm trong Reference Skill `ccba-codebase-design`. Nếu Agent tiếp tục dùng cú pháp Slash Command (`/ccba-improve-codebase-architecture`) khi hướng dẫn người dùng, người dùng gõ `/` trong IDE sẽ không tìm thấy lệnh, gây đứt gãy trải nghiệm và mất niềm tin.
  - **Giải pháp & Rào chắn Bất biến:**
    1. **Kiểm tra SSOT trước khi đề xuất:** Trước khi giới thiệu bất kỳ lệnh nào dưới dạng `/ten-lenh`, Agent BẮT BUỘC đối chiếu với trường `command:` trong `catalog.yaml`.
    2. **Quy ước hiển thị:**
       - Đối với tính năng có `command: /...`: Được phép dùng cú pháp `/ten-lenh` (ví dụ: `/ccba-grilling`, `/ccba-implement`, `/ccba-new-feature`, `/ccba-codebase-design`).
       - Đối với các tài liệu hướng dẫn nằm trong `references/*.md` (Tier 2A): Tuyệt đối KHÔNG gắn tiền tố `/`. Thay vào đó, hướng dẫn người dùng gọi Master Skill kết hợp nạp tài liệu tham chiếu tương ứng (ví dụ: *"Chạy `/ccba-codebase-design` và yêu cầu nạp cẩm nang `references/codebase_refactor_guide.md`"*).

- **Core Pattern P17.2 — Hoàn Thiện Tiêu Chí Hoàn Thành Đa Nhánh (Multi-Mode Completion) & Khử Trùng Lặp Tham Chiếu:**
  - **Vấn đề:** Khi một Skill có nhiều chế độ hoạt động (như `--compare`, `--port`, `--improve`, `--copy-raw`), tiêu chí hoàn thành trong `SKILL.md` thường chỉ được viết cứng cho luồng mặc định (`--port`), dẫn đến: (1) Lỗi Hoàn thành non (Agent không kiểm chứng việc phân tích sâu theo mode), (2) Khuyến nghị bước tiếp theo bị sai lệch (chế độ `--compare` chỉ cần so sánh kiến trúc nhưng lại ép chạy `/ccba-implement`). Đồng thời, các quy tắc kết hợp cờ dễ bị lặp lại nhiều nơi trong tài liệu tham chiếu (`MODES.md`).
  - **Giải pháp & Rào chắn Bất biến:**
    1. **Tiêu chí hoàn thành đa nhánh:** Mọi tiêu chí hoàn thành ở các pha phân tích và bàn giao phải có nhánh rẽ kiểm chứng tương ứng với cờ được gọi (dynamic next-step guidance).
    2. **Single Source of Truth trong tài liệu tham chiếu:** Các quy tắc kết hợp (như cấm kết hợp cờ) chỉ được tuyên bố một lần duy nhất tại phần `Kết hợp không hợp lệ`, không rải rác lặp lại trong mô tả từng cờ riêng lẻ.
    3. **Chuẩn hóa GPI cho User Rituals:** Các kỹ năng có `disable-model-invocation: true` phải khai báo đúng $A = 1.0$ theo barem định lượng chuẩn.
    4. **Khóa hợp đồng bằng Unit Test:** Cài đặt các kiểm thử đặc thù trong `tests/governance/` để bảo đảm các rào chắn này không bị thoái hóa trong tương lai.

---

## 18. Release v2.0-beyond-horizon, Fleet-Wide Spoke Synchronization & Swarm Map-Reduce Dogfooding

- **Core Pattern P18.1 — Self-Healing Engine (ADR-0058) & Discrete Diagnostic Commands:**
  - **Vấn đề:** Khi tích hợp `SelfHealingEngine` (`ccba_harness.self_heal`) vào quy trình tự động sửa lỗi qua `verify-patch --self-heal`, nếu danh sách lệnh kiểm thử được ghép thành một chuỗi duy nhất bằng toán tử shell `&&` (ví dụ `python -m ruff check ... && python -m ruff format --check ...`), engine chỉ bóc tách được chẩn đoán của lệnh đầu tiên trong chuỗi, khiến các lỗi format hoặc linter tiếp theo không được regex parser nhận diện và vá tự động.
  - **Giải pháp:** Cung cấp mảng các lệnh kiểm thử độc lập (ví dụ `["python -m ruff check --fix <target>", "python -m ruff format <target>"]`). Engine sẽ thực thi tuần tự, trích xuất mã lỗi cụ thể (ví dụ F541 f-string without placeholders, I001 import order) và thực thi vòng lặp vá lỗi tự trị (đạt Exit code 0 trong 414.4ms ở ngay vòng 1).

- **Core Pattern P18.2 — Single-Writer Protocol (ADR-0053) & Search-Replace PatchBlocks Atomic Merge:**
  - **Vấn đề:** Khi nhiều subagents/workers chạy song song cùng phát hiện các lỗi thẩm tra PCCC/Kiến trúc và cố gắng ghi trực tiếp vào một tệp kết quả tập trung (`FINDINGS_REGISTRY.md`), xung đột race condition, đè dữ liệu hoặc hỏng định dạng là điều tất yếu.
  - **Giải pháp:** Áp dụng triệt để Single-Writer Protocol: các workers trinh sát hoàn toàn độc lập trong chế độ Read-Only và chỉ xuất ra cấu trúc Search-Replace PatchBlocks có đính kèm SHA-256 hash và ngữ cảnh dòng code. Lead Orchestrator sử dụng `execute_swarm_patches` để thực hiện hợp nhất nguyên tử (atomic merge) vào tệp trung tâm (đạt 3.6ms latency với 0 collision và 0 rollback).

- **Core Pattern P18.3 — Pre-Execution Legal Guardrail Chống Legacy Invariant Bias (RULE-3.1):**
  - **Vấn đề:** Các mô hình ngôn ngữ lớn (LLMs) có xu hướng bị ảnh hưởng bởi tập dữ liệu đào tạo trước 2026, dễ tự động sinh ra các căn cứ pháp lý cũ đã hết hiệu lực tại Việt Nam (như NĐ 06/2021, NĐ 15/2021, NĐ 35/2023, NĐ 175/2024).
  - **Giải pháp:** Thiết lập bộ lọc tiền xử lý (pre-execution filter) và chốt chặn xác thực bắt buộc trước khi xuất báo cáo thẩm tra kỹ thuật (ví dụ Mẫu PC13). Toàn bộ pipeline bắt buộc kiểm tra danh mục văn bản hiện hành (Luật Xây dựng 2025 số 135/2025/QH15, NĐ 207/2026/NĐ-CP, NĐ 217/2026/NĐ-CP, NĐ 105/2025/NĐ-CP). Bất kỳ trích dẫn nào nhắc đến NĐ 06/2021 hay NĐ 175/2024 đều bị từ chối và cảnh báo vi phạm RULE-3.1 ngay lập tức.

- **Core Pattern P18.4 — AI Gateway Spark Server Auth & Fast-Inference Model Gating:**
  - **Vấn đề:** Khi chạy Swarm Map-Reduce với nhiều workers song song, việc gọi trực tiếp các mô hình cục bộ nặng có thể dẫn đến thời gian chờ warmup lâu (60-120s), gây nghẽn hàng đợi kiểm định.
  - **Giải pháp:** Kết nối tới LiteLLM Gateway trên Server Spark (`<TAILSCALE_GATEWAY_IP>:8090`) với header xác thực `Authorization: Bearer <YOUR_AI_GATEWAY_KEY>`. Định tuyến linh hoạt: sử dụng `gemini-3.7-flash` làm mô hình phản hồi nhanh (< 1s cho các bước map-reduce trinh sát tài liệu) và dùng `qwen-local-primary` sau khi đã hoàn tất warmup GPU.
---

## 19. Spoke Synchronization Hardening, Decoupled Telemetry Heartbeat & Spoke Leakage Guard (Issue #268, PR #269)

- **Core Pattern P19.1 — RSA-OAEP Plaintext Bound & Decoupled Telemetry Heartbeat (ADR-0046):**
  - **Vấn đề:** Trong `registry.py` và `spoke_bootstrap.py`, việc mã hóa khóa công khai RSA-2048 với padding OAEP (SHA-256) có giới hạn toán học chặt chẽ $256 - 2 \times 32 - 2 = 190$ bytes. Khi nối chuỗi metadata chứa đường dẫn thư mục dài kèm trường `last_sync` biến động theo từng giây, payload vượt quá 190 bytes dẫn đến ngoại lệ nghiêm trọng `ValueError: Plaintext is too long`. Đồng thời, việc cập nhật `last_sync` liên tục vào registry gây nhiễu git working tree tại Hub sau mỗi lần đồng bộ.
  - **Giải pháp:** Tách bạch hoàn toàn dữ liệu tĩnh và động:
    1. Chỉ mã hóa chuỗi đại diện định danh tĩnh tính bằng SHA-256 hash (`static_hash = sha256(path + archetype)[:16]`), luôn có kích thước cố định $< 100$ bytes, tuyệt đối an toàn dưới trần 190 bytes.
    2. Tuyến telemetry biến động (`last_sync`, trạng thái phiên) được định tuyến lưu vào tệp `.md/telemetry/spoke_heartbeats.yaml` (được đưa vào `.gitignore`), bảo vệ Git tree của Hub sạch sẽ.

- **Core Pattern P19.2 — ADR-0045 Spoke Leakage Guard & Report Mirroring Location:**
  - **Vấn đề:** Quy tắc cấu trúc thư mục kiến trúc quy định thư mục gốc `.md/` chỉ được phép chứa tệp `workspace_context.yaml`. Nếu Agent tạo báo cáo nghiệm thu tại `.md/walkthrough.md`, script kiểm định rò rỉ `scripts/governance/check_spoke_leakage.py` sẽ báo lỗi và chặn quy trình kiểm chuẩn.
  - **Giải pháp:** Chuẩn hóa vị trí báo cáo nghiệm thu và walkthrough tại `.md/knowledge/reports/walkthrough.md`. Nâng cấp bộ công cụ `scripts/validation/audit_pr_comments.py` để hỗ trợ tự động tìm kiếm và đối soát theo thứ tự ưu tiên: `walkthrough.md` $\rightarrow$ `.md/knowledge/reports/walkthrough.md`.

- **Core Pattern P19.3 — Archetype vs Project Type Decoupling & Test Verification Seam Hardening:**
  - **Vấn đề:** Cơ chế ánh xạ archetype cũ trong `sdk_inspector.py` tự động ghi đè hoặc phụ thuộc vào timestamp của registry, dẫn đến cảnh báo khuyến nghị SDK package sai lệch (thiếu nhận diện packages đã cài trong môi trường ảo qua `importlib.metadata`). Ngoài ra, lệnh `sync_spoke.py` thiếu tham số `--dry-run` an toàn cho các tác vụ kiểm thử tự động.
  - **Giải pháp:** Bổ sung hàm `archetype_to_project_type()` độc lập, tra cứu metadata packages hệ thống linh hoạt, trang bị cờ `--dry-run` cho `coordinator.py` và bổ sung 34/34 bài unit test hồi quy toàn diện trong `scripts/tests/test_spoke_sync_modules.py`.

---

## 20. AI Client Hardening: Embedding HTTP 400 Drop Params, Reasoning Streaming Tokens & Auto-Timeout Scaling (Issue #280, PR #281)

- **Core Pattern P20.1 — OpenAI SDK Embedding Compatibility & Gateway Drop Params Invariant:**
  - **Vấn đề:** Khi gọi `ai.embed()` với model Gemini (`gemini-embedding-2`) thông qua LiteLLM proxy, OpenAI Python SDK tự động chèn các tham số mặc định (như `encoding_format: "base64"`). Google Gemini API từ chối các tham số này và trả về lỗi HTTP 400 `UnsupportedParamsError`.
  - **Giải pháp:**
    1. Tại client SDK (`packages/ccba-ai/src/ccba_ai/client.py`), truyền `extra_body={"drop_params": True}` khi gọi `embeddings.create()`.
    2. Đổi default embedding model sang `gemini-embedding-2` (vector 3072 chiều).
    3. Tại tầng AI Gateway (RFC Issue #51 trên `dgx-spark-toolkit`), cấu hình `drop_params: true` toàn cục trên proxy để tự động gọt bỏ tham số không tương thích cho toàn bộ downstream clients.

- **Core Pattern P20.2 — Reasoning Model Streaming Token Floor & Auto-Timeout Scaling:**
  - **Vấn đề:** Với các reasoning models (`gemini-3.7-flash-high`, `-thinking`), giai đoạn suy luận tư duy ngốn nhiều token trước khi bắt đầu sinh câu trả lời. Nếu caller sử dụng mức trần mặc định thấp (ví dụ `max_tokens=1024`), luồng streaming bị cắt cụt giữa chừng ngay khi vừa xong phần thinking hoặc chưa kịp xuất nội dung. Đồng thời, các tác vụ sinh nội dung lớn (> 16,384 tokens) thường mất từ 60s đến 300s, khiến client timeout mặc định (30s) làm rớt kết nối.
  - **Giải pháp:**
    1. Trong `stream()` và `async stream()`, áp dụng `resolve_max_tokens(target_model, max_tokens, baseline_default=1024, reasoning_allocation=16384)` để tự động cấp sàn 16,384 tokens cho reasoning models.
    2. Bổ sung tham số `timeout: float | None` per-request và cơ chế Auto-Timeout Scaling cho `chat()`, `chat_with_metadata()` và `chat_multi()`: `effective_timeout = max(self.timeout, effective_max_tokens / 50.0)`.

- **Core Pattern P20.3 — Depth-Aware Thinking Tag Separation & Reasoning Content Audit:**
  - **Vấn đề:** Thẻ tư duy `<think>...</think>` có thể xuất hiện nhiều lần, lồng nhau, hoặc không có thẻ đóng (unclosed) do streaming bị ngắt. Regex đơn giản `r"<think>(.*?)</think>"` dễ bị nuốt mất nội dung hoặc văng lỗi.
  - **Giải pháp:** Xây dựng parser dò độ sâu ký tự (depth-tracking character scanner) trong `LLMOutputParser.extract_thinking_and_content()`. Bóc tách sạch sẽ trường `ChatResult.thinking` độc lập với `ChatResult.content`, ưu tiên nhận `reasoning_content` trực tiếp từ OpenAI/LiteLLM API nếu có.

- **Core Pattern P20.4 — Async Generator Pytest Mocking Invariant:**
  - **Vấn đề:** Trong `AsyncOpenAI`, `chat.completions.create(stream=True)` là một coroutine bất đồng bộ (`async def`) trả về một async generator. Việc mock bằng `return_value=async_gen()` sẽ gây lỗi `TypeError: object async_generator can't be used in 'await' expression`.
  - **Giải pháp:** Bắt buộc mock bằng `side_effect=mock_async_func` trong đó `mock_async_func` là một `async def` trả về `async_gen`.

---

## 21. Governed Issue Tree Methodology, Cross-Skill Referrals & Copilot Review Invariants (Issue #276, PR #282)

- **Core Pattern P21.1 — Standalone Kernel Skill & Model-Invocation Budgeting (ADR-0040, ADR-0057):**
  - **Vấn đề:** Khi bổ sung kỹ năng tư duy đa ngành `ccba-issue-tree` (McKinsey MECE Issue Tree & Governed Lifecycle), việc gán vào `bundle: _core` có nguy cơ phá vỡ giới hạn trần cứng 10 model-invoked skills (`MAX_MODEL_INVOKED_PER_BUNDLE = 10` tại `skill_validator.py:87`), gây lỗi `CONTEXT_BUDGET_CEILING_EXCEEDED`. Mặt khác, nếu ép kỹ năng này vào `bundle: _software` thì sẽ làm méo mó bản chất đa miền của một phương pháp luận giải quyết vấn đề (vốn dùng cho cả pháp lý, thẩm tra QC, BIM, và tranh chấp hợp đồng).
  - **Giải pháp:** Thiết lập `disable-model-invocation: true` trong frontmatter của `.agents/skills/ccba-issue-tree/SKILL.md`. Điều này cho phép kỹ năng nằm trọn vẹn trong `bundle: _core` (Tier 2B Standalone Kernel Skill, GPI = 14.50), kích hoạt trực tiếp qua lệnh `/ccba-issue-tree` hoặc qua phân phối của Orchestrator mà không tiêu tốn ngân sách system prompt tokens của các tác tử.

- **Core Pattern P21.2 — Progressive Cross-Skill Referral Hooks vs Knowledge Bloat:**
  - **Vấn đề:** Thay vì sao chép các chỉ dẫn phân tích cây vấn đề vào hàng chục kỹ năng hiện hữu (gây phình to kích thước file và trùng lặp logic), làm thế nào để các kỹ năng chuyên biệt tự động tận dụng được sức mạnh phân rã MECE khi gặp bài toán phức tạp?
  - **Giải pháp:** Thiết lập mạng lưới 7 điểm điều hướng (Cross-Skill Referral Hooks) có chọn lọc (Tier 1 High-Impact) tại đúng các nút rẽ nhánh quyết định:
    1. `ccba-diagnosing-bugs`: Pha 3 (Hypothesise cho lỗi đa dịch vụ phi tất định $\rightarrow$ Diagnostic Why-Tree).
    2. `ccba-ai-qc`: Pha 3 (Xung đột kỹ thuật đa bộ môn/PCCC $\rightarrow$ Why-Tree + How-Tree).
    3. `ccba-legal-advisor`: Bước 1/2 (Tranh chấp hợp đồng Cấp độ 3 $\rightarrow$ Why-Tree chuỗi trách nhiệm + How-Tree hòa giải/VIAC).
    4. `ccba-ask`: Bước 1 (Tiếp nhận bài toán mở đa chiều $\rightarrow$ Issue Tree).
    5. `ccba-grilling`: Nhánh A & Phòng thủ (Xung đột kiến trúc $\ge 2$ phương án $\rightarrow$ How-Tree).
    6. `bigbim-risk`: Bước 4 (Xung đột thông tin V2 & drift Unique ID $\rightarrow$ Why-Tree + How-Tree).
    7. `ccba-to-spec`: Bước 3 (Bóc tách Epic lớn $\rightarrow$ What-Tree 4 nhãn MECE: ANALYSIS, DECISION, COMMITMENT, SYNTHESIS).

- **Core Pattern P21.3 — Concept-Level Invariants vs Brittle Numeric Assertions:**
  - **Vấn đề:** Trong quá trình review PR #282, Copilot liên tục phát hiện và chặn merge (Changes recommended) do các số cứng bị lệch pha giữa các tệp: ví dụ câu chữ ghi "11 Ghế CCBA Charter" nhưng bảng RACI liệt kê 12 vai trò; hoặc ghi "máy trạng thái 5 bước" nhưng sơ đồ mô tả 6 trạng thái.
  - **Giải pháp:** Loại bỏ toàn bộ các số lượng đếm cơ học trong đề mục và lời văn mô tả. Quy chuẩn sang các định danh khái niệm bền vững: "các Ghế trách nhiệm Hiến chương CCBA", "ma trận RACI Hiến chương CCBA", và "ma trận vòng đời nhánh".

- **Core Pattern P21.4 — Test Isolation Side-Effect Cleanup Before Release:**
  - **Vấn đề:** Lệnh kiểm thử tiền phát hành `run_isolated_tests.py --all --stress` có thể sinh ra các side-effects trong working tree (ví dụ như tạo embedding cache files hoặc cập nhật metadata). Nếu không dọn sạch trước khi gọi `gh pr merge`, git checkout/merge sẽ bị xung đột hoặc thất bại.
  - **Giải pháp:** Luôn kiểm tra `git status --porcelain`, thực hiện `git restore` và `git clean -fd` đối với các artifacts sinh ra trong quá trình test trước khi thực hiện các thao tác chuyển nhánh hoặc merge.

---

## 22. Dynamic Default Branch Detection, CI Mock Isolation & Cross-Shell PR Body Standards (PR #283)

- **Core Pattern P22.1 — Cross-Platform Remote Default Branch Discovery (ADR-0045, ADR-0056):**
  - **Vấn đề:** Kỹ năng `ccba-create-pr` (v1.1.0) giả định ngầm toàn bộ repository đều sử dụng nhánh chính là `main`. Khi các dự án Spoke (như `dgx-spark-toolkit`) sử dụng nhánh `master` hoặc branch chính tùy biến, các lệnh Main Branch Guard (`git log origin/main..main`, `git reset --hard origin/main`) và lệnh tạo PR (`gh pr create --base main`) đều thất bại, gây đứt gãy quy trình đóng góp ngược lên Hub.
  - **Giải pháp:** Sử dụng lệnh Git chuẩn tắc, tất định và phi phụ thuộc tool ngoài:
    ```bash
    git symbolic-ref --short refs/remotes/origin/HEAD
    ```
    Trích xuất ra dạng `origin/main` hoặc `origin/master`, từ đó suy ra `<default_branch>`. Cung cấp cơ chế fallback native `git rev-parse --verify origin/main` / `origin/master`. Dùng placeholder `<default_branch>` xuyên suốt toàn bộ vòng đời tạo PR.

- **Core Pattern P22.2 — CI Mock Isolation Invariant vs GitHub Runner Communication Loss:**
  - **Vấn đề:** Trong quá trình sửa lỗi test trên branch PR, commit `863187d1` đã vô tình gỡ bỏ `CCBA_AI_MOCK: "1"` khỏi `.github/workflows/ci.yml`. Khi không có cờ mock, `python scripts/eval/run_harness_evals.py --all` cố gắng gửi HTTP request ra các endpoint LLM bên ngoài trong môi trường runner cô lập không có kết nối internet/VPN, dẫn đến treo vô hạn suốt 45 phút cho đến khi runner tự ngắt kết nối (`The hosted runner lost communication with the server`).
  - **Giải pháp:** Ràng buộc bất biến: Runner CI của GitHub Actions BẮT BUỘC duy trì `CCBA_AI_MOCK: "1"` cho mọi bước kiểm định harness và test. Tuyệt đối không tắt mock ở cấp độ workflow. Mọi unit test cần kiểm tra hành vi không mock phải chỉ định `mock_mode=False` hoặc override mock provider ở cấp độ test fixture cục bộ.

- **Core Pattern P22.3 — Cross-Shell PR Body Variable Formatting vs Literal Escape Sequences:**
  - **Vấn đề:** Lệnh `gh pr create --body "<Body>\n\nCloses #<id>"` truyền literal ký tự `\n` trong POSIX bash (do không expand escapes), khiến phần mô tả PR trên GitHub bị in ra chữ `\n\n` trần. Ngược lại, nếu dùng cú pháp PowerShell `` `n `` trong bash blocks sẽ gây lỗi cú pháp.
  - **Giải pháp:** Chuẩn hóa việc truyền nội dung qua biến môi trường hoặc pre-formatted string:
    ```bash
    gh pr create --title "<Title>" --body "$PR_BODY" --base <default_branch> --head <current_branch>
    ```

- **Core Pattern P22.4 — Drift Auditor Test-Path Normalization:**
  - **Vấn đề:** Trong `scripts/governance/drift_auditor.py`, bộ lọc loại trừ thay đổi cấu trúc (`structural_change`) chỉ kiểm tra `"/tests/" not in filepath`. Các tệp kiểm thử ở repo root (như `tests/test_spoke_batch_sync.py`) không chứa dấu gạch chéo đầu, do đó vẫn bị tính là structural change và kích hoạt cảnh báo Architectural Drift sai lệch.
  - **Giải pháp:** Chuẩn hóa bộ lọc bao quát cả root-level tests:
    ```python
    and not filepath.startswith("tests/")
    and "/tests/" not in filepath
    ```

---

## 18. Hub-Mediated Discovery, Fail-Fast Security & Deterministic Completion Gating (2026-09-17)

- **Core Pattern P23.1 — Hub-Mediated Spoke Discovery (Zero Extra Config):**
  - **Vấn đề:** Đề xuất ban đầu định thêm trường `legal_knowledge_path` vào `.md/workspace_context.yaml` tại Spoke và hardcode các đường dẫn ổ đĩa `C:`/`D:`. Điều này vừa gây gãy tính di động khi chạy trên Linux/CI/macOS, vừa tạo thêm gánh nặng cấu hình thủ công.
  - **Giải pháp:** Tận dụng con trỏ `hub_path` có sẵn trong `workspace_context.yaml`. SDK `ccba_legal` tự động đọc `hub_path` để tra cứu `spoke_registry_decrypted.yaml` (hoặc `spoke_registry.yaml`) trên Hub nhằm định vị Spoke pháp điển (`ccba-legal-knowledge`) trên máy trạm mà không cần thêm trường mới.

- **Core Pattern P23.2 — Dual-Personality Conflict & Virtual-First Knowledge Retrieval:**
  - **Vấn đề:** Xung đột giữa mô hình Zero-Copy (ADR-0051) và Full-Copy (ADR-0050). Việc tự động copy toàn bộ kho dữ liệu pháp lý (hàng trăm MB, hàng ngàn tệp PDF/CSV/JSON) về Spoke dự án trên OneDrive/SharePoint gây nghẽn mạng đồng bộ (sync churn), khóa file và tràn giới hạn đường dẫn Windows (`MAX_PATH > 260`). Ngoài ra, copy vật lý mà không có cache invalidation sẽ khiến Spoke đọc dữ liệu luật cũ khi Spoke gốc cập nhật.
  - **Giải pháp:** Thiết lập thứ tự phân giải 3 tầng ưu tiên Virtual-First:
    1. Tầng 1 (Virtual / Local): Trích xuất qua CLI Deep Seam hoặc quét `.md/legal_docs/`. Chỉ kéo chọn lọc qua `python -m ccba_legal sync --pull-latest --doc <id>` khi cần offline.
    2. Tầng 2 (Master Registry): Khám phá tự động qua Hub.
    3. Tầng 3 (SSOT): Đối soát `legal_registry.yaml` để loại trừ văn bản hết hiệu lực.

- **Core Pattern P23.3 — False-Positive Completion Gating vs ADR-0058 Hard Completion Lock:**
  - **Vấn đề:** Trong `ccba_legal/cli.py`, khi không tìm thấy kho tri thức cục bộ, lệnh `sync` rơi vào `fallback_cloud_vault` với `bundles_synced: []` (0 tệp), nhưng CLI vẫn in thông báo thành công màu xanh và trả về `Exit Code 0`. Điều này vi phạm nghiêm trọng ADR-0058 vì Agent tưởng việc đồng bộ đã xong trong khi thư mục trống trơn.
  - **Giải pháp:** Sửa điều kiện: nếu `status == "fallback_cloud_vault"` hoặc `len(bundles_synced) == 0`, lệnh `sync` BẮT BUỘC trả về `Exit Code 1` kèm thông báo lỗi rõ ràng.

- **Core Pattern P23.4 — Fail-Fast Maskara Security Gate for RAG Queries:**
  - **Vấn đề:** Gửi prompt RAG chứa API keys hoặc thông tin nhạy cảm lên Cloud (Google NotebookLM) trước khi kiểm tra bảo mật gây rò rỉ credential và lãng phí quota API.
  - **Giải pháp:** Đưa hàm `sanitize_prompt_for_query()` lên ngay dòng đầu tiên của `query_rag()`. Phát hiện critical keys (Google, OpenAI, Anthropic, GitHub) sẽ lập tức chặn đứng (ném `ValueError`, exit code 3) trước khi khởi tạo client hay kết nối mạng.

- **Core Pattern P23.5 — Deep Seam CLI Over Raw File Ingestion (Context Bloat Anti-Pattern):**
  - **Vấn đề:** Hướng dẫn Agent dùng `view_file` mở file Markdown thô của một bộ luật (như Luật Xây dựng 2025 nặng 194 KB ~ 60.000 tokens) gây cháy toàn bộ context window của Agent, dẫn đến mất tập trung và hallucination.
  - **Giải pháp:** Cưỡng chế Agent ưu tiên gọi CLI Deep Seam `python -m ccba_legal get-clause --doc <id> --clause <id>` trích xuất AST nguyên tử với chi phí < 500 tokens (tiết kiệm 95% token).

- **Core Pattern P23.6 — Windows Socket Connect Timeout Invariant:**
  - **Vấn đề:** Hàm kiểm tra cổng `is_port_open(port)` sử dụng socket stream mặc định không timeout, khiến trên Windows nếu cổng bị drop hoặc chặn bởi firewall thì lệnh kiểm tra Chrome CDP bị treo vô hạn.
  - **Giải pháp:** Luôn gán `s.settimeout(1.0)` trong mọi hàm socket probing.

---

## 19. Nightly Tuner Evolution, Worktree Isolation & Merge Danger Governance (2026-09-18)

- **Core Pattern P24.1 — Tuner Circuit Breaker & Real LLM Fast-Fail Invariant:**
  - **Vấn đề:** `LLMTaskAdapter` chuyển `circuit_breaker` sang `AIClient` nhưng không tự khởi tạo nếu caller không truyền vào, khiến cơ chế Fast-Fail `CircuitBreakerOpenError` khi gặp chuỗi lỗi 429/503 liên tiếp không được kích hoạt trong thực tế.
  - **Giải pháp:** `LLMTaskAdapter.__init__` tự động gán `self.circuit_breaker = circuit_breaker or (CircuitBreaker() if CircuitBreaker is not None else None)`, bảo đảm Fast-Fail luôn thường trực.

- **Core Pattern P24.2 — Caller-Specified Budget Ceiling Preservation:**
  - **Vấn đề:** Biến môi trường `CCBA_TUNER_TOKEN_BUDGET` ghi đè vô điều kiện `RatchetConfig.token_budget` ngay cả khi daemon đã truyền `remaining_budget` tường minh, phá vỡ hạch toán ngân sách tổng phiên.
  - **Giải pháp:** Đặt default `token_budget: int | None = None` và chỉ nạp từ biến môi trường khi `self.token_budget is None`.

- **Core Pattern P24.3 — Prompt Compaction Double-Strip (Comment & Auto-Generated Bullets):**
  - **Vấn đề:** Rào chắn phình to prompt (> 300 dòng) chỉ xóa dòng comment HTML `<!-- Ratchet Optimization Refinement ... -->` mà bỏ quên dòng bullet `- Cập nhật quy chuẩn rà soát vòng...`, khiến prompt tiếp tục tích lũy dòng rác qua các vòng lặp ratchet.
  - **Giải pháp:** Bộ lọc splitlines xóa song hành cả dòng comment và dòng bullet bắt đầu bằng `- Cập nhật quy chuẩn rà soát vòng`.

- **Core Pattern P24.4 — Worktree Subprocess Isolation & Localized PYTHONPATH:**
  - **Vấn đề:** Trong runner `run_nightly_tuner.sh`, `PYTHONPATH` được gán trỏ về `$PROJECT_ROOT` trước khi `cd "$WORKTREE_DIR"`. Các tiến trình con (`python3 -m ccba_harness ...`) trong worktree cô lập vẫn import module từ cây làm việc chính (có thể bị bẩn hoặc lệch pha).
  - **Giải pháp:** Chuyển vào `$WORKTREE_DIR` trước, sau đó gán `export PYTHONPATH="$WORKTREE_DIR/packages/...:$WORKTREE_DIR"`.

- **Core Pattern P24.5 — Subprocess Error Verification on Git Branch Cleanup:**
  - **Vấn đề:** `_cleanup_old_empty_branches` kiểm tra nhánh rỗng bằng `git cherry base_ref b`. Nếu lệnh thất bại (thiếu base_ref, detached HEAD, tên nhánh lỗi), `diff_res.stdout` trả về rỗng và hàm xóa nhầm nhánh.
  - **Giải pháp:** Kiểm tra nghiêm ngặt `diff_res.returncode == 0 and not diff_res.stdout.strip()` kèm `encoding="utf-8", errors="replace"`.

- **Core Pattern P24.6 — Merge Danger Assessment (Two-Way vs One-Way Door):**
  - **Quy chuẩn:** Phân loại rủi ro cho mọi PR và Implementation Plan:
    * **Door:** `Two-way` (dễ đảo ngược, thay đổi cô lập nội bộ) vs `One-way` (khó đảo ngược, breaking change, thay đổi schema/contract hoặc migration).
    * **Blast Radius:** `Localized` (cục bộ 1 hàm/file) vs `Package-wide` vs `Monorepo-wide` vs `Spoke-affecting` (ảnh hưởng Spoke downstream).

---

## 20. Word COM In-Place Form Filler, Hermetic Release Cleanliness & Architecture Drift Gate (2026-09-19)

- **Core Pattern P25.1 — Word COM In-Place Single-Pass & Process Lifecycle Teardown:**
  - **Vấn đề:** Điền dữ liệu vào biểu mẫu hành chính, hồ sơ thị thực (Visa Australia, vvC_Test) và hợp đồng định dạng `.doc` (Word 97-2003 nhị phân) không thể thực hiện bằng `python-docx` (chỉ hỗ trợ `.docx` XML). Các script cũ chuyển đổi sang `.docx` rồi convert ngược lại thường làm vỡ bảng biểu, mất tab stops, và rò rỉ tiến trình `WINWORD.EXE` chạy ngầm khi exception xảy ra.
  - **Giải pháp:** Xây dựng `WordFormFiller` trong `packages/ccba-ooxml/src/ccba_ooxml/form_filler/` với kiến trúc Dual-Engine: `WinwordEngine` thao tác in-place trực tiếp trên Word DOM Range và Table Cell (Windows COM native), đóng tài liệu và tắt application trong khối `finally` context manager; `SofficeFallbackEngine` chạy headless LibreOffice kết hợp `python-docx` trên Linux/Docker.

- **Core Pattern P25.2 — Anti-Row Split & Form Layout Guard:**
  - **Vấn đề:** Khi dữ liệu điền vào bảng dài hoặc nhiều dòng, Word tự động ngắt hàng bảng giữa 2 trang in khiến dòng chữ bị xé đôi; các dòng mẫu trống thừa trong biểu mẫu động không được cắt tỉa gây tràn trang in.
  - **Giải pháp:** `FormLayoutGuard` tự động cưỡng chế `Row.AllowBreakAcrossPages = False` (trên Word COM) hoặc inject `<w:cantSplit/>` vào cấu trúc XML OpenXML (`w:trPr`), tự động cắt tỉa hàng trống thừa (empty row pruning) và ép ngắt trang trước phần chữ ký/kết luận (`PageBreakBefore`).

- **Core Pattern P25.3 — Monorepo Architecture Drift Enforcement:**
  - **Vấn đề:** Khi bổ sung một module/sub-package mới vào `packages/ccba-ooxml/src/ccba_ooxml/form_filler/`, CI job `validate` chạy `validate_docs.py --changed` chặn đứng và trả về Exit Code 1 do quy tắc Architecture Drift: mọi thay đổi cấu trúc mã nguồn trong `packages/` bắt buộc phải được phản ánh tại ít nhất một tài liệu kiến trúc cấp cao (`README.md` hoặc `PLATFORM.md`).
  - **Giải pháp:** Cập nhật bảng tính năng và sơ đồ kiến trúc tại `README.md` song song với việc viết code tính năng, loại bỏ hoàn toàn Architecture Drift trước khi mở PR.

- **Core Pattern P25.4 — TRIHT Cleanliness Gate & Mock Registry Isolation:**
  - **Vấn đề:** Khi chạy bộ kiểm thử toàn diện `run_isolated_tests.py --all --stress`, các test suite của crawler (như `ccba-legal-intel`) ghi thêm bản ghi mock vào `.md/data/legal_registry.yaml` và `.md/data/sources_registry.yaml`. Nếu không kiểm soát, các thay đổi test này sẽ lọt vào commit trên `main` hoặc gây ô nhiễm working tree.
  - **Giải pháp:** Cổng 0.3 của Giao thức TRIHT (`check_release_cleanliness.py --phase post`) đối soát trạng thái working tree sau kiểm thử, phát hiện ngay các tệp dữ liệu bị sửa đổi ngoài danh mục cache tạm và chặn quy trình release (Exit Code 1), buộc Agent phải hoàn tác an toàn (`git checkout -- .md/data/*.yaml`) trước khi tiếp tục merge.

- **Core Pattern P25.5 — Admin Bypass for Branch Protection in Automated Release:**
  - **Vấn đề:** Khi repository có kích hoạt ruleset / branch protection policy trên nhánh `main` (yêu cầu approval review hoặc chặn direct merge), lệnh `gh pr merge --squash --delete-branch` thất bại với thông báo `base branch policy prohibits the merge`.
  - **Giải pháp:** Trong quy trình release tự động của maintainer (`/ccba-release-feature`), sau khi 100% checks của CI đã xanh và Copilot review đã được đối soát sạch sẽ qua `audit_pr_comments.py`, bổ sung cờ `--admin` (`gh pr merge <num> --squash --delete-branch --admin`) để hợp nhất an toàn.

---

## 21. Archived Historical Invariants (Di dời từ Active Working Memory theo Đề xuất Học tập v2)

Các quy tắc kiến trúc và vận hành dưới đây đã ổn định trong nền tảng và được di dời từ bộ nhớ làm việc `session_learnings.md` sang lưu trữ lịch sử theo Đề xuất Học tập v2:

- **RULE-1.4 [bullet 2 — Spoke Workflow Migration & Phantom Directory Prevention]:**
  - Spoke Synchronizer (`coordinator.py`): Đổi tên workflows cũ thành `.md.bak` (`DEPRECATED_MIGRATED_TO_SKILL`), xóa thư mục cũ theo aliases. (Chi tiết đối chiếu: Mục 11.4 và Mục 13.2).
- **RULE-1.7 [Clean Architecture — Phân Tách Hạ Tầng Kết Nối]:**
  - Tách hạ tầng xác thực thành `drive_client.py`, tránh inverted coupling giữa Pull và Push.
- **RULE-2.2 [Spoke CI Gates Verification Pipeline]:**
  - 5 Cổng Zero-Tolerance: `lint_visual_parity`, `validate_legal_spoke`, `test_converter_regression`, `verify_all_docs_against_pdf`, `verify_cross_links`. (Chi tiết đối chiếu: Mục 4).
- **RULE-2.6 [YouTube Ingestion & Livestream Garbage Guard]:**
  - Lọc bỏ `live_chat`, ngắt sớm nếu `is_live: True`. Chặn HTML rác trước Map-Reduce.
- **RULE-2.7 [Dry-Run Complete Isolation]:**
  - `--dry-run` BẮT BUỘC cô lập 100%: CẤM ghi báo cáo, CẤM alert Telegram, CẤM xóa stale briefs, CẤM copy tệp về repo gốc. (Chi tiết đối chiếu: Mục 19.3).
- **RULE-4.3 [Tiêu Chí Hoàn Thành Đa Nhánh & DRY Reference]:**
  - Tiêu chí hoàn thành có nhánh kiểm chứng từng cờ (`--compare`, `--port`, `--improve`, `--copy-raw`). Khai báo cờ DRY tại `MODES.md`. (Chi tiết đối chiếu: Mục 17.2).
- **RULE-4.7 [Spoke CLI Signature & Verbatim Verification Parity]:**
  - `sync_spoke.py`: cần `--apply` để ghi; `adopt_spoke.py`: dùng `--spoke` (cấm `--apply`, `--spoke-path`); CLI hợp nhất: dùng positional `[spoke_path]` (cấm `--spoke`).
  - `validate_docs.py`: chỉ nhận 1 thư mục. CẤM dùng `...` trong `--target` kiểm định (gây `Artifact not found`). (Chi tiết đối chiếu: Mục 13.1).
- **RULE-5.1 [Chromium VIP Session Engine & CDP Browser Target]:**
  - Profile `~/.gemini/antigravity/chrome_vip` cổng `9222`. `Browser.setDownloadBehavior` BẮT BUỘC qua Browser Target WebSocket (`/json/version`). Selectors kế thừa `TVPLSelectors`. (Chi tiết đối chiếu: Mục 2 và Mục 39).
- **RULE-5.2 [Windows Path Quotes & Hook Protection]:**
  - Khi IDE bọc ngoặc kép `"C:\..."` vào `hooks.json`, vô hiệu bằng `{}` và khóa `IsReadOnly = $true`. Timeout $\ge 60\text{s}$ cho tests scan metadata Windows. (Chi tiết đối chiếu: Mục 11.2).
- **RULE-5.3 [Query Sanitization & Turnstile Bypass]:**
  - Query TVPL có dấu `/`, `:`, `-` phải thay bằng dấu cách (`quote_plus`) chống lỗi IIS mã hóa `%2F`. (Chi tiết đối chiếu: Mục 39).

---

## 22. Archived Operational Invariants (Di dời từ Active Working Memory theo Chuẩn hóa Platform-Aware KISS)

- **RULE-5.4 [Telegram ChatOps: Markdown v1, Subprocess Reaping & Cross-Repo Path]:**
  - *Markdown v1 Escaping*: Trong Telegram Markdown v1, dấu `_` là cú pháp italic. MỌI biến chuỗi động chứa `_` (file, branch, model, skill) BẮT BUỘC bọc trong inline code backtick (`` `...` ``) kèm `_clean_md` thay ` ` ` thành `'`, chống lỗi `can't parse entities` gây rớt fallback plain text.
  - *Subprocess Reaping*: Khi dùng `asyncio.wait_for(proc.communicate(), timeout=...)`, trong `TimeoutError` và `CancelledError` BẮT BUỘC: tiến trình đơn gọi `proc.kill()` + `await proc.wait()`; shell runner có trap cleanup worktree BẮT BUỘC dùng `os.killpg` gửi `SIGTERM` $\rightarrow$ chờ 5s $\rightarrow$ `SIGKILL` triệt tiêu zombie và dọn dẹp worktree.
  - *Cross-Repo Service*: Service systemd gọi chéo repo BẮT BUỘC dùng tham số `cwd=` tường minh trỏ về gốc repo đích (phân giải qua `CCBA_HUB_PATH`), cấm gắn cứng đường dẫn máy trạm `/home/vvc/...` (vi phạm Machine-State Decoupling) hoặc dùng đường dẫn tương đối.
- **RULE-5.5 [Timezone-Normalized Observability cho Database Gateway UTC]:**
  - Khi truy vấn sản lượng token/spend trong ngày từ gateway lưu UTC (LiteLLM `LiteLLM_SpendLogs`), CẤM dùng `CURRENT_DATE` trong `WHERE` (mất trắng 00:00-07:00 ICT). BẮT BUỘC lọc theo mốc 00:00:00 ICT chuẩn hóa sang UTC bảo đảm Index Scan:
    `WHERE "startTime" >= ((CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Ho_Chi_Minh')::date::timestamp AT TIME ZONE 'Asia/Ho_Chi_Minh' AT TIME ZONE 'UTC')`.

---

---

## 24. Archived Operational & Testing Invariants (Di dời từ Active Working Memory sau PR #402 / Issue #366)

- **RULE-1.9 [2-Phase Planning Guardrail — The Factory Model]:**
  - Refactoring bộ trích xuất/chuyển đổi BẮT BUỘC phân lập 2 giai đoạn: Phase 1 (Pure Structural — Zero-Regression 0.0%, dual-dispatch) và Phase 2 (Feature/Schema Mutations). Cấm scope conflation.
- **RULE-2.8 [Cross-Platform Sandbox Root Traversal Invariant]:**
  - CẤM dùng độ sâu cố định `parents[N]` khi tìm gốc workspace (tránh `PermissionError` trên Linux sandbox hoặc `/tmp`). BẮT BUỘC duyệt ngược tìm `(p / ".md").is_dir()`, fallback local `.cache/`, bọc trong `try...except (PermissionError, OSError)`.
- **RULE-2.10 [Temporal Invariance & Collinear Multi-Key Sort Guard]:**
  - *Temporal Invariance*: Test TTL/window CẤM ngày tĩnh; BẮT BUỘC dùng ngày tương đối (`today - timedelta(...)`).
  - *Collinear Sort*: Test sắp xếp đa khóa BẮT BUỘC dùng fixture nghịch chiều (`os.utime`), chống bẫy test pass giả do thứ tự ngẫu nhiên cùng chiều.
- **RULE-2.11 [ADR 0058 — Multi-Archetype Simulation Immunity & Two-Tier Scorer Architecture]:**
  - *Simulation Anti-Hijacking*: Trong `simulation.py`, keyword nhận diện BẮT BUỘC gắn Positive Domain Anchors; CẤM keyword mạng generic (`rate limit`, `exponential backoff`) đứng độc lập. Phải có explicit exclusion guards giữa các sub-domains có nguy cơ chồng lấn.
  - *Two-Tier Scorer Architecture*: Đánh giá kỹ năng hệ thống/tooling BẮT BUỘC phân lập: Tier 1 (Tooling Integrity) kiểm tra Git CLI/sync/connectors; Tier 2 (Existential Guardrail Floor) kiểm tra an toàn (`--force-with-lease`, remote state idempotency, `CCBA_HUB_PATH`, verify-patch exit code 0). Thiếu toàn bộ $\rightarrow$ `is_critical_fail=True` buộc REVERT trong Auto-Tuner.

---

## 25. Archived Operational Invariants & Evals Engine Post-Mortem (Di dời từ Active Working Memory sau PR #401 & PR #413)

- **RULE-1.6 [ADR 0044 — Federated RAG & Dynamic Import]:**
  - Tier 0 import Tier 1: `try: from ccba_legal.xxx import yyy; except ImportError: pass`. Cache BM25; Embedding `.npy` kiểm tra SHA-256.
- **RULE-1.8 [ADR 0044 & Issue #326 — Multi-Device Spoke & Invariant Merge]:**
  - *Universal Invariant Regex*: Regex multiline bảo tồn 100% điều khoản cục bộ khi sync.
  - *Cross-Drive Fallback*: Khi `relpath` lỗi `ValueError`, fallback `hub_path` về `None`, tránh gắn cứng ổ đĩa.
- **RULE-2.12 [LiteLLM Budget Error Resilience & Vector Top-K]:**
  - *Budget Error Resilience*: Bắt lỗi LiteLLM kiểm tra đồng thời: `("budget" in err.lower() and "exceeded" in err.lower())`.
  - *Vector L2 Normalization*: Embeddings chuẩn hóa L2 trước khi cache; truy vấn dùng dot-product (`@`) và `np.argpartition` $O(n + k \log k)$ cho corpus lớn.
- **RULE-4.7 [POSIX Traversal ACLs vs SGID Group Inheritance]:**
  - Máy chủ Linux đa người dùng: Cấp traversal `g:ccba-devs:--x` trên thư mục cha và gán SGID (`chmod -R g+s`) cho các repos kế thừa nhóm sở hữu.
- **POST-MORTEM [Evals Engine Refactor & Dual-Dispatch Simulation Architecture (PR #401)]**:
  - *Monolithic Drift Root Cause*: Hàm `simulation.py` đơn khối ban đầu phát triển từ một vài mock đơn giản lên đến 1.426 dòng trong một hàm lồng nhau duy nhất `mock_agent_task()`. Sự phình to này dẫn tới (1) Trôi dạt kiến trúc khỏi `archetypes.py` (chỉ có một số ít domains được mock cẩn thận, còn lại rơi vào fallback); (2) Lỗi Prompt Hijacking khi câu lệnh kiểm thử chứa các từ khóa mạng chung chung (`rate limit`, `backoff`) khiến bộ mô phỏng trả về mock sai miền; (3) Auto-Tuner bị nghẽn do thiếu mutators cho 9/17 archetypes.
  - *Dual-Dispatch Solution*: Tách thành package `ccba_harness.evals.simulators/` gồm 17 domain simulators độc lập, protocol `BaseDomainSimulator`, và bộ điều phối 4 tầng (`dispatcher.py`). Ưu tiên hàng đầu (Tier 1) là phân giải Archetype từ `skill_name` qua `resolve_domain_archetype()`, giúp triệt tiêu hoàn toàn nguy cơ Prompt Hijacking trong khi vẫn hỗ trợ Tier 2-3 cho metadata và legacy callers. Bổ sung đầy đủ 17/17 mutators trong `tuner.py`, giải phóng toàn bộ năng lực tiến hóa của Auto-Tuner.






---

## 26. Sprint 1 Evals Engine Refactor & Release Post-Mortems (PR #419, PR #420)

### 1. Atomic Knowledge Cataloging & CI Orphan Note Prevention
- **Root Cause:** Khi tạo kế hoạch Sprint 1 (`.md/knowledge/plans/evals_sprint1_refactor_plan.md`), tệp markdown được commit vào feature branch nhưng chưa được khai báo vào mục lục trung tâm `.md/knowledge/index.md`. Linter `wiki_health_linter.py` trên CI GitHub Actions phát hiện Orphan Knowledge Note và đánh sập toàn bộ matrix kiểm thử trên Python 3.10, 3.11 và 3.12.
- **Invariant (RULE-2.15):** Mọi tệp tri thức `.md` sinh ra trong `.md/knowledge/` bắt buộc phải được biên mục đồng thời vào `.md/knowledge/index.md` ngay tại commit tạo tệp, không được để commit sau mới vá.

### 2. Hermetic Script Injection Protocol (Bash Subshell Escaping)
- **Root Cause:** Khi thực thi các lệnh sửa đổi file nhanh qua bash bằng `python -c "..."` có chứa nội dung Markdown/YAML mang ký hiệu backtick (```), bash cố gắng thực thi các đoạn text bên trong backtick như các lệnh subshell (`agent_name`, `send_message`, `verdict`), dẫn đến lỗi `command not found` và làm trôi lệnh cập nhật tệp.
- **Invariant (RULE-2.15):** Nghiêm cấm dùng inline string có backticks trong double quotes trên bash. Bắt buộc dùng `cat << 'EOF' > /tmp/patch.py` (nháy đơn quanh EOF) hoặc sử dụng file manipulation tools chuyên dụng.

### 3. Concurrent Remote Merge Realignment & Safe Reset Protocol
- **Root Cause:** Trong quá trình agent chỉnh sửa bản vá phản biện cục bộ, người dùng hoặc remote đã thực hiện merge nhánh `main` vào nhánh PR (`387adca2`). Khi pull nhánh, git phát sinh trạng thái unmerged paths do xung đột với stash cũ và working tree lệch pha.
- **Invariant (RULE-4.11):** Khi nhánh PR nhận commit merge mới từ `main` trên GitHub, sau khi kiểm tra commit cục bộ đã push an toàn, dùng `git reset --hard origin/<branch>` để căn chỉnh working tree về trạng thái sạch sẽ tuyệt đối của remote, triệt tiêu hoàn toàn unmerged conflict.

### 4. Walkthrough Dedicated PR Workflow
- **Invariant (RULE-4.11):** Do hook `pre-push` cấm tuyệt đối push trực tiếp vào `main`, tài liệu nghiệm thu `walkthrough.md` sau khi hoàn tất release feature bắt buộc phải được lưu trữ qua nhánh riêng `docs/walkthrough-pr-<id>` và mở PR riêng để CI tự động kiểm định và squash-merge theo Fast-Path Review.

---

## 27. Sprint 4 Evals Daemon, Reasoning Token Defense & CI Drift Post-Mortems (PR #434, Issue #433)

### Archived Invariants (Di dời từ Active Working Memory)
- **RULE-1.2 [ADR 0053 — Single-Writer Protocol Cho Orchestrators]**:
  - Single-Writer: Lead Orchestrator duy nhất ghi mã/logs. Subagents chỉ xuất Structured Patch vào `.system_generated/scratch/`.
- **RULE-1.3 [ADR 0035 — Deep Modules, Seams & Zero-Exemption AST]**:
  - Thin Seam: Module chỉ bộc lộ `__all__` hoặc `__init__.py`. Cấm import private `_*`. Zero-Exemption: Gỡ bypass trong linter.
- **RULE-1.11 [Static Seam Verification & AST Span Linter]**:
  - `validate_seam_exports()` kiểm tra Package Spoofing, Filesystem Existence, và Symbol Parity với `__all__`.
  - Trích xuất symbol luôn `.rstrip(".,;")`. Quét exemption comment import dùng dải `range(node.lineno - 1, getattr(node, "end_lineno", node.lineno))`.
- **RULE-2.1 [Strict Mypy Type-Safety — Chống Anti-Pattern AP9.1]**:
  - CẤM `[[tool.mypy.overrides]] ignore_errors = true`. Ép kiểu tường minh binary I/O, dicts. Dùng `ignore_missing_imports = true` cho lib thiếu stubs.
- **RULE-2.3 [Fast Feedback Loops (< 2s) & Parity Contract Tests]**:
  - Unit tests nòng cốt đạt SLA $< 2\text{s}$ (`pytest -m fast`). `test_cli_doc_parity.py`: Khớp nối 100% giữa CLI và `SKILL.md`.
- **RULE-2.4 [Relative Link Resolution Depth]**:
  - Tệp `.agents/skills/<skill>/SKILL.md` trỏ về package monorepo dùng `../../../packages/<pkg>`. CẤM commit URI `file:///` hoặc `conversation://`.
- **RULE-3.2 [TVPL VIP 3-Tier Download Priority — ADR 0031]**:
  - Tier 1 (`part=-100`): VIP Vector PDF. Tier 2 (`part=-1&docx=1`): VIP Word (`docx_converter`). Tier 3 (`part=0`): Scan PDF.

### Post-Mortems & Operational Invariants
#### 1. Invariant Marker Architecture Drift Prevention
- **Root Cause:** Khi tạo mới một kỹ năng (như `ccba-vllm-manager`), số lượng kỹ năng tăng từ 74 lên 75. Theo RULE-4.5, các marker `<!-- STATS:SKILL_COUNT -->` trong `README.md` và `PLATFORM.md` bị lệch, khiến linter `DocumentAuditor.audit_architecture_drift()` trên CI chặn đứng toàn bộ ma trận kiểm thử ở cả 4 jobs.
- **Invariant (RULE-4.12):** Mọi commit thêm/sửa/xóa Level-1 structural files (skills, packages, scripts) BẮT BUỘC phải chạy `python scripts/update_arch_stats.py` và commit đồng thời với tệp mới trước khi mở Pull Request.

#### 2. Thinking Token Starvation Defense in Structured Pipelines
- **Root Cause:** Các mô hình reasoning tiên tiến (DeepSeek-R1, Qwen-2.5-Coder-Thinking, v.v.) có xu hướng tiêu tốn hàng nghìn tokens trong thẻ suy nghĩ nội tâm (`<think>...</think>`). Nếu pipeline chỉ cấp `max_tokens=500` cho các tác vụ deterministic JSON extraction, HyDE queries, hoặc intent tagging, mô hình sẽ cạn kiệt token ngân sách trước khi kịp sinh ra kết quả hữu ích, gây sập parse JSON hoặc kết quả rỗng.
- **Invariant (RULE-5.8):** Đối với các tác vụ deterministic/structured output (JSON extraction, HyDE generation, tagging), BẮT BUỘC cấu hình `chat_template_kwargs: {"enable_thinking": False}` hoặc cấp dự phòng `max_tokens` vượt ngưỡng suy nghĩ tối thiểu. Phân tầng định tuyến tách biệt rõ `local-instruct` (không thinking cho structured tasks) và `local-coder`/`rag-core` (bật thinking cho phân tích mã nguồn và tổng hợp pháp lý).

#### 3. vLLM Container Production Mounting & Dual Parser Separation
- **Root Cause:** Khi triển khai vLLM trên container DGX Spark Blackwell qua Docker, mỗi lần restart container, cache biên dịch kernel AOT của PyTorch TorchInductor bị xóa sạch nếu không được mount ra ổ đĩa host, dẫn tới độ trễ khởi động lần đầu (TTFT) kéo dài hàng phút. Đồng thời, việc trộn lẫn parser suy nghĩ và parser gọi công cụ gây lỗi nhận diện sai tool calls.
- **Invariant (RULE-5.9):** Khi chạy container vLLM, BẮT BUỘC mount thư mục host `~/.cache/vllm` vào `/root/.cache/vllm`. Cấu hình cờ phân tách rõ ràng `--reasoning-parser` (ví dụ `qwen3`) và `--tool-call-parser` (ví dụ `qwen3_coder`).

#### 4. Evals Daemon Priority Ratchet & Cooldown Bypass
- **Root Cause:** Trong nightly evals daemon, cơ chế cooldown 3 ngày mặc định chặn các kỹ năng đang trong chu kỳ lặp nếu chỉ dựa trên mốc thời gian chạy gần nhất. Tuy nhiên, các kỹ năng mới chưa có bản ghi ledger cơ sở (`needs_ledger_seed`) hoặc các kỹ năng đang có thẻ lỗi phát hiện bởi Failure Mutator chưa được áp dụng (`has_unapplied_signals`) cần được kiểm thử và tiến hóa ngay lập tức. Nếu bị cooldown chặn, vòng phản hồi tự tối ưu sẽ bị đình trệ. Ngoài ra, việc ghi nhận `SKIPPED_COOLDOWN` vào log lịch sử vô tình kéo dài cửa sổ cooldown vô tận.
- **Invariant (RULE-2.16):** Trong `WeightedPriorityQueue`, các kỹ năng có `needs_ledger_seed=True` hoặc `has_unapplied_signals=True` BẮT BUỘC bypass cooldown (`in_cooldown = 0`). Hàm đọc metrics lịch sử `_load_historical_metrics()` BẮT BUỘC bỏ qua các bản ghi `SKIPPED_COOLDOWN` để không reset hoặc kéo dài cửa sổ cooldown của kỹ năng.

---

## 28. Ephemeral Worktree Lock Invariants, Subprocess Failure Transparency & Suspicious Success Post-Mortems (PR #436, PR #437, PR #85)

### Archived Invariants (Di dời từ Active Working Memory)
- **RULE-2.14 [UTF-8 Offset Parity & Dynamic Mock Secrets]**:
  - *UTF-8 Offset Parity*: Chuỗi tiếng Việt/emoji byte length khác character offset. Cắt lát redaction string BẮT BUỘC dùng character index đảo ngược (`reversed(findings)`); byte redaction dùng `byte_start, byte_end`.
  - *Dynamic Mock Secrets*: Unit tests BẮT BUỘC tạo mock keys runtime (`f"sk-proj-{'a'*32}"`) chống CI diff scanner false-positive.
- **RULE-4.10 [Nightly Auto-Tune & TRIHT Release Gate (ADR-0045, ADR-0058)]**:
  - *Nightly Tuner*: PR `auto-tune/*` bắt buộc đối soát Evolution Matrix, kiểm tra Goodhart, 100% Skills Hygiene Pass.
  - *TRIHT Release*: Release PR qua 3 cổng: Pre-Flight Cleanliness, Slow Hermetic Integration Tests, Post-Test Teardown.
- **RULE-4.11 [Concurrent Branch Alignment & Walkthrough PR Protocol]**:
  - *Remote Merge Realignment*: Khi nhánh PR nhận merge mới từ `main` trên GitHub, BẮT BUỘC kiểm tra commit local đã push, dùng `git reset --hard origin/<branch>` căn chỉnh working tree sạch sẽ; CẤM để unmerged files trước release.
  - *Walkthrough Dedicated PR*: Tuân thủ hook `pre-push` cấm push thẳng `main`, `walkthrough.md` BẮT BUỘC lưu trữ qua nhánh riêng `docs/walkthrough-pr-<id>` và Squash-Merge qua Fast-Path Review.

### Post-Mortems & Operational Invariants
#### 1. Ephemeral Worktree Pointer vs Directory & Mutex Lock Invariant
- **Root Cause:** Trong môi trường Git Worktrees (`git worktree add`), tệp `.git` tại thư mục gốc của worktree là một regular text file chứa chuỗi `gitdir: <path>`, không phải một thư mục. Khi `GitMutexLock` khởi tạo với đường dẫn mặc định `project_root / ".git" / "evals_tuner.lock"` và gọi `self.lock_path.parent.mkdir(parents=True, exist_ok=True)`, Python phát hiện `parent` là một tệp đã tồn tại và ném ngoại lệ nghiêm trọng `FileExistsError: [Errno 17] File exists`.
- **Invariant (RULE-2.17):** Cơ chế khóa `GitMutexLock` BẮT BUỘC phân giải nội dung tệp `.git` khi nó là regular file để lấy đường dẫn `gitdir` thực tế (hỗ trợ cả đường dẫn tuyệt đối lẫn tương đối từ worktree root), và đặt lock bên trong `worktree_gitdir / "evals_tuner.lock"`. Nếu `lock_path.parent` vẫn là một tệp thường sau khi khởi tạo, `acquire()` BẮT BUỘC ném `NotADirectoryError` tường minh thay vì âm thầm dịch chuyển đường dẫn khóa.

#### 2. Multi-Tier Subprocess Failure Transparency & Zero-Regression Report Fidelity
- **Root Cause:** `daemon.py` bắt ngoại lệ cho từng kỹ năng và ghi log nhưng không truyền lỗi ra CLI caller `nightly_tuner_daemon.py`, khiến tiến trình kết thúc với mã thoát `0`. Đồng thời, do `halt_reason` không được thiết lập thành `"ERROR"`, hàm dựng báo cáo Markdown `generate_evolution_report_markdown()` mặc định gán huy hiệu `⚪ UNCHANGED` và tick `✅ Zero-Regression`, tạo ra cảm giác sai lầm rằng hệ thống vẫn an toàn. Hơn nữa, `_finalize_disk_state()` nuốt ngoại lệ rollback khiến worktree bị dirty mà không báo động.
- **Invariant (RULE-2.17):** CLI facades BẮT BUỘC quét `report.results` và `sys.exit(1)` nếu bất kỳ kỹ năng nào dính trạng thái `ERROR: ...`. Quá trình hoàn tác đĩa `_finalize_disk_state()` khi gặp lỗi BẮT BUỘC lưu lại `finalize_error` và ném `RuntimeError` trong `run()` và `run_async()`. Báo cáo tiến hóa khi có lỗi ngoại lệ BẮT BUỘC gán `halt_reason="ERROR"`, huy hiệu `❌ ERROR: <status>`, và thay thế hoàn toàn checkmark Zero-Regression/Hard Floor bằng cảnh báo `⚠️ Lưu ý Thất bại`.

#### 3. Suspicious Success Defense-in-Depth in ChatOps Gateway
- **Root Cause:** ChatOps Gateway (`scripts/chatops_daemon.py`) khi thực thi lệnh shell `execute_shell_job()` trước đây tin tưởng tuyệt đối vào điều kiện `exit_code == 0` để thông báo `[THÀNH CÔNG]`. Khi một tiến trình con nuốt lỗi hoặc vô tình thoát mã 0 trong khi log ngập tràn lỗi ngoại lệ chết người, người quản trị qua Telegram nhận thông báo thành công giả tạo và không nhận ra sự cố.
- **Invariant (RULE-2.17):** ChatOps Gateway BẮT BUỘC bổ sung chốt chặn phòng vệ đa tầng `is_suspicious_success`: Ngay cả khi `exit_code == 0`, nếu ngõ ra tiến trình chứa các dấu hiệu lỗi nghiêm trọng (`[ERROR] ccba.eval`, `❌ Lỗi trong quá trình`, `Traceback (most recent call last):`), trạng thái thực thi BẮT BUỘC chuyển thành `⚠️ [CẢNH BÁO (CÓ LỖI XUẤT HIỆN TRONG LOG)]`, tự động hủy chế độ tin nhắn rút gọn để đính kèm tệp `.log` đầy đủ lên Telegram, và ghi nhật ký audit trail là `WARNING`.

---

## 29. Bugbot Rules, Read-Only Advisory AI Review & Danger Triage (PR #448 / PR #449)

- **RULE-4.8 [Review Danger Triage, Read-Only Advisory Guardrail & 10 Bugbot Invariants]:**
  - *Read-Only Advisory Guardrail*: Các công cụ tự động hóa kiểm duyệt (Cursor Bugbot, GitHub Copilot Reviewer) vận hành theo cơ chế Chỉ Đọc & Tư Vấn (Read-Only Advisory). AI Reviewers TUYỆT ĐỐI KHÔNG CÓ QUYỀN GỬI TRẠNG THÁI "APPROVE" và CẤM tự động merge mã nguồn logic nghiệp vụ.
  - *Danger Triage Matrix*: Tách biệt rõ giữa Deterministic Status Checks (Hard Floor - bắt buộc pass 100%) và Advisory AI Review (Soft Guidance - hỗ trợ con người). PR thay đổi tệp kiến trúc cốt lõi (`AGENTS.md`, `.github/workflows/`, `scripts/`, `packages/`) bắt buộc human review; PR chỉ sửa tài liệu (`.md/`, docstrings) được phép Auto-Approve an toàn sau khi vượt qua verifier.
  - *10 Bugbot Invariants SSOT*: Đối soát diff tự động theo 10 quy tắc bất biến tại `.github/bugbot-rules.md` (SEAM_REUSE, DECOUPLED_CONNECTION, AST_SPAN_INSPECTION, MULTI_KEY_SORT, INODE_INVARIANCE, POSIX_PERMISSIONS, MACHINE_STATE_DECOUPLING, SECRETS_MASKARA, VERIFIER_TEST_PARITY, ATOMIC_MICRO_PR).
  - *Opt-in Trigger Guardrail*: AI Review không tự động kích hoạt trên mọi commit; chỉ chạy khi có nhãn `ai-review-requested` hoặc lệnh `/ccba-ai-review`, loại trừ bot PRs, và diff bắt buộc phải đi qua cổng làm sạch bảo mật `ccba_maskara.redact_secrets_in_text()` để tránh rò rỉ secret và bão quota Gateway Spark.

---

## 30. Peer Telemetry & Model Provenance, Zero-Hang Process Lifecycle & Copilot Subprocess Invariants (PR #478 / ADR-0064)

### Background & Context
Trong các phiên tương tác đồng đẳng giữa Antigravity và Grok CLI trên Monorepo Hub, phát sinh 2 vấn đề lớn:
1. **Interactive TUI Hang**: Grok CLI khi nhận câu hỏi dạng chuỗi vị trí (`grok [OPTIONS] "prompt"`) khởi động vòng lặp TUI tương tác và không tự động thoát (`exit 0`). Khi đó, Antigravity rơi vào trạng thái ngủ hướng sự kiện (event-driven idle) bị đóng băng liên tục cho đến khi con người can thiệp.
2. **Blind Model & Cost Provenance (Nguy cơ lỗi 402)**: Hệ thống định tuyến đa tầng (`grok-4.7` trên xAI Cloud $\rightarrow$ `gemini-3.8-flash` qua Gateway) nhưng `PeerVerdictBlock` không ghi nhận model thực tế đã xử lý phán quyết. Đồng thời không đo đếm token dẫn đến nguy cơ chạm trần quota API.

### Phản biện Copilot Code Review & Subprocess Hardening Invariants
1. **Pipe Buffer Deadlock Prevention (Comment 4184089485)**:
   - *Vấn đề*: Khi chạy `subprocess.Popen` với `stdout=subprocess.PIPE` và `stderr=subprocess.PIPE` mà không drain đồng thời (chỉ gọi `communicate()` sau khi tiến trình đã kết thúc), nếu tiến trình con xuất dữ liệu vượt quá dung lượng OS pipe buffer (~64 KB trên Linux — rất phổ biến với `xhigh` deep reasoning), tiến trình con sẽ bị block ở lệnh ghi `write()`, `poll()` không bao giờ trả về, và watchdog spin cho đến khi timeout giết chết tiến trình hợp lệ.
   - *Invariant*: Tuyệt đối cấm dùng bare `subprocess.PIPE` cho các tiến trình chạy nền có output lớn mà không có reader thread. Bắt buộc chuyển hướng `stdout` và `stderr` sang tệp tạm độc lập `tempfile.TemporaryFile()` để có dung lượng đệm không giới hạn của hệ thống tệp.
2. **Stale Verdict File Reuse Guard (Comment 4184089581)**:
   - *Vấn đề*: Watchdog polling kiểm tra sự tồn tại của tệp `output_file` trên đĩa. Do các tệp verdict của peer exchange được lưu lại trên đĩa (ví dụ `grok_review_*.md`), nếu không kiểm tra thời gian tạo file, watchdog sẽ nhận nhầm tệp phán quyết cũ của phiên trước ngay ở vòng lặp đầu tiên và kết thúc sớm tiến trình với phán quyết lỗi thời.
   - *Invariant*: Watchdog BẮT BUỘC kiểm tra `os.path.getmtime(output_file) >= start_time` trước khi đọc phán quyết.
3. **Subprocess Text Encoding on Windows (Comment 4184011501)**:
   - *Vấn đề*: `subprocess.run(..., text=True)` nếu không chỉ định `encoding` sẽ dùng locale mặc định của hệ thống. Trên Windows (cp1252), khi output chứa ký tự Unicode/tiếng Việt sẽ ném ngoại lệ `UnicodeDecodeError` làm sập luồng đo lường telemetry.
   - *Invariant*: Mọi lệnh text-mode subprocess BẮT BUỘC truyền `encoding="utf-8", errors="replace"`.
4. **Maskara Secret Linter False-Positive Guard**:
   - *Vấn đề*: Rule `env-secret` trong Maskara quét các phép gán biến chứa chuỗi con `tokens` và gán giá trị không ngoặc kép có độ dài $\ge 8$ ký tự. Các biến telemetry Python gán cho kwarg như `reasoning_tokens=rsn`, `output_tokens=est_out` nếu đặt tên biến dài $\ge 8$ ký tự (`reasoning`, `est_output`) sẽ bị nhận nhầm là secret token.
   - *Invariant*: Đặt tên các biến telemetry truyền vào hàm ngắn gọn $< 8$ ký tự (`rsn`, `est_out`, `in_tok`).

---

## 31. Level-2 Peer Agent Delegation Protocol Dogfooding, Tool Sandboxing, Resilient Parsing & Transactional Rollback (PR #481, #482, #483, #484)

### Context & Implementation Summary
Phiên làm việc triển khai và dogfooding thực tế hệ sinh thái Level-2 Peer Agent Delegation Protocol (ADR-0063 / ADR-0064) qua 4 Pull Requests liên hoàn:
- **PR #481**: Gia cố rào chắn headless `qwen-local` (0 USD) với cờ `--deny "*"` và bóc tách tự động `extract_anchor_payload`.
- **PR #482**: Tích hợp CLI `ccba-harness apply-anchor-patch` với Two-Phase Commit, transactional rollback (`written_backups`), chuẩn hóa CRLF/LF, và mở rộng profiles `code_review`, `arch_audit`.
- **PR #483**: Triển khai 3 điều kiện thẩm định từ Grok Review (`COND-01` báo cáo rollback errors, `COND-02` `is_file()` guard, `COND-03` bảo tồn POSIX `st_mode`), cùng Pydantic condition coercion và session fallback.
- **PR #484**: Dogfooding thực tế profile `arch_audit` (Grok-4.7 xhigh, 19.3k reasoning tokens, 740k total tokens, $0.2545) thẩm định chuỗi 5 ADR (ADR-0060 $\to$ ADR-0064).

### Key Architectural Invariants & Learned Patterns
1. **Tool-Enabled Review Turn Budgeting & Tool Sandboxing**:
   - *Grok 1.0.46 Turn 0 Off-by-one*: Khi chạy headless 1-turn (`patch_fast`), không thể dựa vào `--max-turns 1` do Grok đếm prompt ban đầu là lượt 0 và ngắt sớm. Khóa triệt để quyền chạy lệnh terminal và tools bằng `--deny "*"` là giải pháp tối ưu.
   - *Multi-turn Turn Budget*: Profile có công cụ tra cứu (`code_review`, `arch_audit`) BẮT BUỘC thiết lập tối thiểu 10–14 turns. Thiết lập trần hẹp $\le 8$ turns khiến mô hình cạn lượt khi đang tra cứu `grep`/`read_file` trước khi kịp tổng hợp phán quyết cuối cùng.
2. **Resilient Pydantic Output Parsing & Session History Fallback**:
   - *Pydantic Coercion*: LLM thường xuyên xuất `conditions` dưới dạng danh sách chuỗi (`list[str]`) thay vì danh sách dicts, hoặc thêm các trường telemetry phụ. Thiết lập `extra="ignore"` và `@field_validator("conditions", mode="before")` tự động chuẩn hóa chuỗi thành `PeerCondition(id="COND-xx", description=...)` là điều kiện tiên quyết cho production zero-touch.
   - *Session History Fallback*: Khi các lệnh gọi tool của Grok CLI làm phân mảnh ngõ ra stdout, harness tự động đọc tin nhắn assistant cuối cùng trong `~/.grok/sessions/**/{session_id}/chat_history.jsonl` có giới hạn trần kích thước.
3. **ACID Two-Phase Commit with POSIX Mode Preservation & Error Reporting**:
---

## 32. Upstream Pstack Disciplines: AST Comment Sanitation, Dual-Mode Verification Harness & False-Positive Decoupling (PR #486)

### Context & Implementation Summary
Phiên làm việc tiếp thu và nội địa hóa toàn diện các chuẩn mực kỹ thuật từ Cursor `pstack` vào nền tảng CCBA Agent Services Platform sau khi hoàn thành phản biện đối kháng cùng Grok CLI (Verdict: `REVISE & PROCEED` với 5 điểm tinh chỉnh giải thuật):
- **Component 1 (Deep Seam `peer_gate.py`)**: Xây dựng `check_redundant_comments()` tích hợp vào 7-Stage Implementation Gate (`run_full_gate` / `run_implementation_gate`), tự động phát hiện mã chết bị comment out và comment lặp lại tên định danh $\le 5$ từ đứng trước hàm/lớp.
- **Component 2 (Quy chuẩn Nền tảng `docs/rules/code_quality.md`)**: Ban hành Mục 16 "Anti-Slop & Zero-Noise Code Discipline" (5 nguyên tắc cốt lõi).
- **Component 3 (Checklist Rà soát `ccba-code-review`)**: Thiết lập `references/unslop_checklist.md`, bump `ccba-code-review` lên v1.5.0.
- **Component 4 (Standalone Kernel Skill `ccba-create-verification-skill`)**: Tạo kỹ năng Tier 2B (GPI: 22.75) sinh bộ harness kiểm định `verify-<app>` và cẩm nang `features/INDEX.md`.
- **Bản vá CI (Commit `7e543378`)**: Sửa lỗi drift đếm skill `update_arch_stats.py` và khử false positive `[env-secret]` của Maskara. Đạt 100% (8/8 checks) CI passed và squash-merge vào `main` (`ab88e013`).

### Key Architectural Invariants & Learned Patterns
1. **AST Tokenized Comment Sanitation with Block Header Wrapping**:
   - `ast.parse()` tự động lược bỏ comments; do đó BẮT BUỘC dùng `tokenize.generate_tokens()` để định vị các token `tokenize.COMMENT`.
   - Đối với mã chết độc lập (def, class, import, return): Thử nghiệm `ast.parse()` trực tiếp sẽ ném `SyntaxError: unexpected EOF` với các block header (`def foo():`, `class Bar:`) hoặc `SyntaxError: return outside function`.
   - *Quy chuẩn bọc mã*: Nếu comment kết thúc bằng `:`, append thêm `\n    pass`; nếu bắt đầu bằng `return `, bọc trong `def _dummy():\n    {code}`. Chỉ khi AST module sinh ra node hợp lệ mới xác nhận là dead code. Mọi câu văn xuôi chứa từ khóa (như `# return early if cache hit`) sẽ gây `SyntaxError` khi parse và được giữ lại nguyên vẹn.
2. **Lexical Analysis Naming & Maskara False-Positive Decoupling**:
   - Bộ quét bí mật `ccba-maskara` có quy tắc `env-secret` nhận diện chuỗi regex `(?i)\b[A-Za-z0-9_]*TOKEN[A-Za-z0-9_]*\s*[:=]`.
   - Trong mã nguồn phân tích từ vựng (AST / Tokenizer), nếu đặt tên biến là `tokens = ...`, `name_tokens = ...`, Maskara sẽ ném vi phạm bảo mật giả `[SECURITY VIOLATION] [env-secret]` do chứa cụm từ `TOKEN` đi kèm phép gán biểu thức $\ge 8$ ký tự.
   - *Invariant*: Tuyệt đối không dùng danh từ chứa chuỗi con `token` cho các biến nhận kết quả gán trong code tokenizer. BẮT BUỘC dùng các định danh trung tính: `lex_items`, `lexemes`, `name_parts`, `name_vocab`.
3. **Embedded Verification Harness Directory Pattern (ADR-0044 Guardrail)**:
   - Khi tự động sinh kỹ năng kiểm định `verify-<app>` cho các Spoke repositories, toàn bộ mã kiểm thử và kịch bản thực thi BẮT BUỘC nằm gọn trong `.agents/skills/verify-<app>/harness/`.
   - Tuyệt đối không rải các kịch bản kiểm thử ra thư mục `scripts/` của Spoke, bảo vệ nghiêm ngặt ngân sách tối đa 15 scripts theo Hiến pháp Spoke Cleanliness (ADR-0044).
4. **Architecture Stats Synchronization Before Documentation Validation Gate**:
   - Khi tạo mới Standalone Kernel Skill (tăng tổng số kỹ năng từ 75 lên 76), các thẻ neo `<!-- SKILL_COUNT_START -->` trong `README.md` và `PLATFORM.md` BẮT BUỘC phải được cập nhật qua `python scripts/update_arch_stats.py` trước khi chạy `validate_docs.py` và tạo commit, ngăn chặn triệt để lỗi chặn cứng CI `Invariant marker drift`.

---

## 33. Multi-Agent Consensus Lattice, Watcher Isolation & Pstack Phase 2 Forensics (PR #487, PR #489 & Phase 2)

### Context & Implementation Summary
Chuỗi phiên làm việc hoàn thiện tầng Level-2.5 Multi-Agent Peer Co-Review và hấp thụ toàn diện 2 năng lực cuối cùng từ Cursor `pstack` (v0.15.0+):
- **PR #487 (HUB-ADR 0065)**: Cương xương hồ sơ tác nhân (`patch_fast`, `agentic_code`, `arch_audit`), thu hẹp phạm vi `_SYNC_MUTEX`, tiêu diệt triệt để nhóm tiến trình con qua POSIX `setsid` / Windows Process Group, và áp dụng cơ chế Fail-Closed cho thuật toán Topo Kahn.
- **PR #489 (Level-2.5 Multi-Agent Co-Review Orchestrator)**: Tiếp thu trọn vẹn 6 điều kiện đối kháng `COND-01` $\to$ `COND-06` từ Grok-4.7, xây dựng bảng xếp hạng Bậc ưu tiên toàn phần 11 token (`VERDICT_LATTICE_RANK`), quản trị Quorum Fail-Closed với `HANDOFF`, gộp conditions bằng phép OR cờ `blocking`, cô lập tiến trình trong `TemporaryDirectory(mode=0700)` ngoài cây `.md/peer_exchange`, và cung cấp CLI `ccba-harness peer-co-review`.
- **Pstack Phase 2 (Drift Maintenance & Figure-It-Out Forensics)**: Nâng cấp `ccba-create-verification-skill` thành Dual-Mode (`scaffold` + `maintain`) kèm cẩm nang `maintain_drift_guide.md` (COND-01 Pre-Remediation Provenance Check); ban hành Mục 17 `docs/rules/code_quality.md` với mô hình phân tách 4 vùng mù, ngắt mạch $\le 3$ lần thử-sai (COND-02), ứng xử headless least-privilege (COND-03), và bắt buộc khắc sâu Minimal Reproducer thành bài test thường trực (COND-04).

### Key Architectural Invariants & Learned Patterns
1. **Total Precedence Lattice & Synthetic Verdict Elimination**:
   - Khi hợp nhất nhiều phán quyết từ các tác nhân ngang hàng độc lập, thứ hạng ưu tiên phải được định nghĩa toàn phần trên 100% token của `VerdictType`.
   - Tuyệt đối cấm nhánh `else: consensus_verdict = "APPROVE"`. Mọi token lớp Chặn (`REJECT`, `REJECT_PLAN`, `GATE_FAIL`) luôn có độ ưu tiên cao nhất, tiếp theo là `REVISE_PLAN`, rồi đến `HANDOFF` khi thiếu quorum, kế tiếp là các phán quyết có điều kiện, và cuối cùng mới là lớp PASS.
2. **Ephemeral Run Directory & Background Watcher Isolation**:
   - Các kịch bản chạy đa tác nhân sinh ra nhiều file trung gian (prompt bản sao, verdict từng profile) tuyệt đối không được ghi tại `.md/peer_exchange/` với định dạng `*.tmp.md` hay `prompt_*.md`.
   - Do background watcher quét mọi file `.md` và coi `prompt_*` là yêu cầu mới, việc ghi file tạm cạnh prompt gốc sẽ kích hoạt watcher đệ quy vô tận.
   - *Quy chuẩn*: Bắt buộc tạo `tempfile.TemporaryDirectory(mode=0700)` nằm ngoài cây repository; chỉ publish duy nhất 1 file kết quả chính thức vào `.md/peer_exchange/` qua `atomic_write_text`.
3. **Telemetry Token Naming & Dict Unpacking for Maskara Compliance (RULE-1.16)**:
   - Các biến tính tổng telemetry không được đặt tên dạng `total_tokens = ...` hay `total_tokens += ...`. Phép gán này khớp với regex `(?i)\b[A-Za-z0-9_]*TOKEN[A-Za-z0-9_]*\s*[:=]` của Maskara và bị chặn tại cổng PR Danger Triage.
   - Bắt buộc dùng biến đệm trung tính (`agg_total`, `agg_input`, `agg_output`) và khởi tạo Pydantic model qua dict unpacking `CombinedTelemetry.model_validate({"total_tokens": agg_total})`.
4. **Verification Drift Provenance & Test Tampering Prevention**:
   - Khi bộ harness `verify-<app>` báo lỗi, cấm sửa bài test để cố tình làm xanh kết quả.
   - Bắt buộc đối chiếu lịch sử commit: nếu app đổi interface theo chủ đích $\to$ sửa `harness/`; nếu do lỗi hồi quy $\to$ giữ nguyên test và sửa mã nguồn ứng dụng.
5. **Hypothesis-Driven 4-Part Uncertainty Partitioning**:
   - Phân tách bài toán mơ hồ thành 4 nhóm: Factual questions (tự giải quyết bằng công cụ khảo sát codebase), Empirical forks (thử nghiệm tối đa 3 lần), Product preferences (ứng xử bảo thủ least-privilege khi chạy headless), Irreversible decisions (bắt buộc lập ADR).
   - Minimal Reproducer sau khi sửa lỗi thành công bắt buộc phải được chuyển thành test case chính thức trong `tests/` hoặc `harness/` để bảo vệ chống tái phát lỗi.







---

## 34. Skills Taxonomy, Scope Declaration & Multi-Environment Distribution Matrix (HUB-ADR 0066)

### Context & Implementation Summary
Phiên thảo luận kiến trúc và tiếp thu phản biện đối kháng từ Grok-4.7 (`APPROVE_PLAN`, risk_score 1/5) nhằm giải quyết dứt điểm khoảng trống kiến trúc phân phối lệnh Slash Command giữa Hub và Spoke:
- **HUB-ADR 0066**: Chuẩn hóa ma trận phân nhóm kỹ năng, kế thừa ADR-0057 (Two-Stage Decision & GPI).
- **Platform Operations Invariant**: Phân định rạch ròi giữa `bundle: _core` (vận hành vòng lặp SDLC của Agent ở mọi Spoke, tự động sync 100%) và `bundle: _software` (nghiệp vụ kỹ thuật phần mềm chuyên sâu, chỉ sync theo `project_type: software`).
- **Metadata Scope Declaration**: Thêm trường `scope: hub | spoke | universal` vào frontmatter `SKILL.md`.
- **Slash Command Distribution Guardrail**: Cập nhật `SkillValidator` và `validate_skills.py` chặn đứng các kỹ năng có `command: /...` thuộc `bundle: _governance` nhưng thiếu `scope: hub`, bảo đảm lập trình viên tại Spoke luôn nhận được gợi ý Slash Command trên IDE autocomplete popup.
- **Deterministic GPI Formula Check (COND-01)**: Tự động đối soát điểm GPI toán học $\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$.

### Archived Invariants (Di dời từ Active Working Memory)
- **RULE-1.15 [ADR 0057 — Upstream Retro Diagnostics & Deterministic Checks Invariant]**:
  - *Retro Diagnostics & Level 3 Index*: Khi có ma sát công cụ / lặp lỗi, đọc `references/agent_environment_diagnostics.md`. Kỹ năng có `references/` BẮT BUỘC khai báo Level 3 Reference Index trong `SKILL.md`.
  - *Deterministic Checks over Rules*: Lỗi cơ học BẮT BUỘC tạo automated linter/CI check (`verify-patch`, pre-commit); CẤM thêm prompt rules vào `AGENTS.md` gây Attention Dilution (ADR-0030).

---

## 35. CLI God Module Modularization, Static Module Budget Enforcement & Template Sanitizer Precision (PR #494)

### Context & Implementation Summary
Phiên làm việc refactor và giải phóng "God Module" `cli.py` (từ 1,514 dòng monofile xuống mỏng < 40 dòng thin dispatch shell), thiết lập dynamic command registry và cơ chế static module budget ratchet:
- **PR #494**: Xóa sổ monofile `cli.py`, tách nhỏ thành `ccba_harness.cli` (`main.py`, `registry.py`, `commands/evals.py`, `commands/peer.py`, `commands/telemetry.py`, `commands/verifier.py`, `commands/architecture.py`, `commands/skills.py`).
- **Static Module Size Budget Ratchet**: Thiết lập `check_ast_module_length` (giới hạn cứng $\le 500$ LOC cho tệp Python monorepo) và `check_ast_function_length` (post-parse body $\le 40$ LOC cho CLI command handlers), hỗ trợ `# ccba:quarantine` có kỳ hạn và issue URL.
- **Fail-Closed Dynamic Package Topology**: Bổ sung rào chắn an toàn khi `dep_graph` rỗng trong `spoke_bootstrap.py` $\to$ hoàn nguyên về `DEFAULT_PACKAGE_TOPOLOGY_ORDER` bảo toàn bất biến vị trí của `ccba-harness` và `ccba-ai`.
- **Security Scanner Template Sanitizer Precision**: Siết chặt kiểm tra cú pháp f-string template interpolation trong `ccba-maskara` để phân biệt chính xác biến nội suy Python có format specifier (`{var.total_tokens:,}`) với JSON strings chứa secret thật (`{"token": "..."}`).

### Key Architectural Invariants & Learned Patterns
1. **Explicit Registry & Thin Shell Pattern (KISS & High Locality)**:
   - Command dispatch shell (`main.py`) chỉ chứa logic phân giải đối số ban đầu và ủy quyền thực thi; cấm nhồi nhét xử lý nghiệp vụ hay định nghĩa hàng chục subparser trong cùng một monofile.
   - Các subcommand handlers độc lập được đặt trong `commands/` với interface thống nhất `register_subparser(subparsers)` và `run_cli(args)`.
2. **Post-Parse Function Length Gate & Legacy Quarantine**:
   - CLI command handlers thường có phần khai báo `argparse` dài nhưng phần logic sau khi `parse_args` phải được giữ mỏng ($\le 40$ LOC).
   - Các hàm thừa hưởng từ monofile cũ chưa kịp phân rã nhỏ phải được đánh dấu cách ly có kỳ hạn `# ccba:quarantine` kèm URL issue, cấm bỏ qua lén lút không có thời hạn.
3. **Empty Graph Fail-Closed in Dependency Topological Sort**:
   - Khi cây thư mục package không có `pyproject.toml` hoặc đồ thị phụ thuộc rỗng, thuật toán Kahn tuyệt đối không được trả về danh sách rỗng để tránh kích hoạt fallback sắp xếp theo từ điển alphabet (làm đảo lộn trật tự Tier-0 Anchor `ccba-harness` và `ccba-ai`). Bắt buộc trả về trật tự tĩnh mặc định `DEFAULT_PACKAGE_TOPOLOGY_ORDER`.
4. **Template Sanitizer Precision over Broad Wildcards**:
   - Rào chắn quét bí mật không được nới lỏng allowlist bằng `startswith("{")` đơn thuần (nguy cơ bỏ sót chuỗi JSON nhạy cảm).
   - Bắt buộc thẩm định cấu trúc: nếu bắt đầu bằng `{"` hoặc `{'` $\to$ coi là JSON/dict literal (không suppress); nếu bắt đầu bằng `{` theo sau là identifier hợp lệ và format specifier (`^\{[A-Za-z_][A-Za-z0-9_.]*[:,\s]`) hoặc kết thúc bằng `}` $\to$ an toàn; các biến token metrics phải nằm trong tập định danh đo lường tường minh (`known_token_metrics`).

---

## 36. Toàn Diện 76 Skills Chuẩn Hóa Platform-Aware Architecture Posture (ADR-0061, ADR-0057, ADR-0058)

### Context & Implementation Summary
Chiến dịch chuẩn hóa toàn bộ 76 skills của CCBA Agent Platform qua 11 đợt phối hợp thẩm định song phương với Grok 4.7 (Lead Reviewer) và Gemini Antigravity (Executor), đạt 100% phán quyết `APPROVE` (`conditions: []`, `risk_score: 1`):
- **Phân loại Seam chính xác**: Rạch ròi 16 Public Deep Seams (package-bound) và 60 skills dạng quy trình thao tác chuẩn (seam-exempt). Giữ nguyên 16 card trong `seam-contracts.yaml`, cấm lạm phát seam contract.
- **Tiêu đề Posture Thống Nhất**: Bắt buộc dùng đúng `## 🏛️ Platform-Aware Architecture Posture` (0 số ADR trong header). Cấm token ADR trong mục posture của các skill không tạo ADR mới để bảo vệ radar ma trận parity `sync_hub_adr_matrix.py`.
- **Two-Pass Peer Review Protocol**: Khóa trước kế hoạch (Pass 1 - `APPROVE_PLAN`) rồi mới triển khai mã nguồn và đối soát reflog nghiệm thu (Pass 2 - `APPROVE`). Thiết lập timeout `peer_dispatch` $\ge 900$s cho mô hình reasoning `xhigh`.
- **Atomic Micro-PR Slicing**: Phân rã mỗi đợt 7-8 skills thành 4 micro-PRs (1A-1D), khóa cục bộ bằng bộ 3 lệnh (< 1s) trước khi merge.
- **Deterministic Hard Completion Lock (ADR-0058)**: Cưỡng chế 6/6 cổng CI tự động toàn sàn (`python -m ccba_harness verify-patch --preset ci`) với Exit Code 0.

### Key Architectural Invariants & Learned Patterns
1. **Contract Inflation Prevention**: Kỹ năng SOP, pattern library, caller CLI không sở hữu package Python độc lập bắt buộc nhận `seam-exempt` kèm giải trình rõ ràng; không mở card Seam tùy tiện.
2. **Header Invariant & Parity Radar Isolation**: Regex quét ADR trong CI rất nhạy cảm với tiêu đề; việc cách ly hoàn toàn token ADR khỏi mục posture đảm bảo tính tất định 100% khi chạy `--check`.
3. **Reasoning Turn & Timeout Budgeting**: Khi peer agent sử dụng xhigh reasoning để đọc sâu hàng chục tệp trên đĩa, ngân sách thời gian phải $\ge 900$s và max turns $\ge 30-40$.
4. **Local Sub-Second Verification**: Sử dụng `--preset skill --target <path>` kiểm tra nhanh giúp phát hiện sai lệch cú pháp ngay lập tức trước khi chạy toàn sàn CI.

---

## 37. Closed-Loop Graduation Supersession, Spoke Markdown Link Sanitizer & Empirical Peer Claim Verification (PR #521, PR #527, PR #528)

### Context & Implementation Summary
Phiên phát triển và hoàn thiện cơ chế đồng bộ Spoke khép kín cùng cải tạo ngân sách AST ($\le 50$ LOC) cho phân hệ `scripts/spoke/sync/`:
- **PR #521 (`25f15eda`, Issue #520)**: Xây dựng module `scripts/spoke/sync/graduation.py` (`supersede_graduated_spoke_docs`, `audit_spoke_markdown_links`) và nâng cấp `sync_layer2_rules` để tự động thu hồi các bản nháp tri thức tại Spoke đã được chuẩn hóa thành Hub ADR (thay bằng stub định hướng `GRADUATED_STUB_MARKER`), bảo tồn lịch sử ghi chú cục bộ bằng nhánh SHA-8 (`COND-02`), đồng bộ tài liệu tham chiếu liên kết tầng 2 và tự động khử liên kết `file://` không khả chuyển hoặc tiền tố dư thừa `.md/` trong `.md/INDEX.md`.
- **PR #527 (`652eb997`)**: Phân rã 6 hàm/phương thức vượt trần 50 dòng trong `scripts/spoke/sync/coordinator.py` (`assess_catalog_freshness`: $85 \to 29$, `_sync_single_item`: $117 \to 38$, `_sync_full_bundle`: $435 \to 48$, `sync_spoke_bundle`: $234 \to 41$, `verify_spoke`: $111 \to 37$, `sync_all_spokes`: $93 \to 43$ LOC) sau 2 vòng thảo luận đối kháng với Grok (`req-discuss-refactor-coordinator-001` & `002`).
- **PR #528 (`6f198176`)**: Phân rã toàn bộ 4 phương thức vượt trần 50 dòng trong `scripts/spoke/sync/sdk_inspector.py` (`copy_if_needed`: $150 \to 46$, `_ensure_git_hook_activated`: $98 \to 14$, `resolve_packages_to_check`: $94 \to 27$, `sync_or_advise`: $79 \to 28$ LOC) và khử trùng lặp `is_legal_related_spoke`, đồng thời khóa cứng ratchet test `test_coordinator_ast_function_length_compliance` cho cả 3 module (`coordinator.py`, `graduation.py`, `sdk_inspector.py`).

### Key Architectural Invariants & Learned Patterns
1. **Branched SHA-8 Archive Preservation on Divergent Spoke Drafts (`graduation.py`, COND-02)**:
   - Khi thu hồi bản nháp tri thức tại `.md/knowledge/<name>.md` đã được chuẩn hóa thành Hub ADR, nếu tệp lưu trữ `.md/knowledge/archive/<name>.md` đã tồn tại nhưng bản nháp hiện hành lại có phát sinh ghi chú mới từ kỹ sư Spoke (khác nội dung sau khi chuẩn hóa CRLF/LF), hệ thống bắt buộc giữ nguyên bản lưu trữ gốc VÀ ghi thêm bản nhánh `<stem>.local-<sha8>.md` trước khi ghi đè stub `GRADUATED_STUB_MARKER`.
2. **Spoke Markdown Link Portability & Redundant Prefix Sanitization (`audit_spoke_markdown_links`)**:
   - Các tệp chỉ mục `.md/INDEX.md` tại Spoke thường bị nhiễm liên kết tuyệt đối `file:///...` hoặc tiền tố lặp `.md/knowledge/...` (dẫn tới đường dẫn ảo `.md/.md/knowledge/...`). Bộ kiểm toán `audit_spoke_markdown_links(spoke_root, apply_fixes=True)` tự động chuẩn hóa về đường dẫn tương đối khả chuyển trong pha `--sync-spoke` và kiểm tra nghiêm ngặt trong pha `--verify`.
3. **Empirical Rebuttal of Un-Grounded Peer Reviewer Claims (`audit_direct` vs Verbatim Code)**:
   - Khi sử dụng profile `audit_direct` (`max_turns=1`, không bật công cụ đọc đĩa), Peer Reviewer (Grok) có thể suy diễn sai các thuộc tính không tồn tại trong mã nguồn thực tế (ví dụ: giả định `SpokeSynchronizer` có `self.stats` và `self.logger`, đề xuất tạo dataclass `_BundleSyncState`, hoặc giả định `GateCheck` có thuộc tính `.findings` thay vì `.stdout_tail`).
   - Agent bắt buộc thực hiện Kiểm toán Phản biện (Bước 1 `/ccba-session-retrospective` & Rule #8): đối chiếu từng điều kiện `COND-xx` với AST thực tế, gửi vòng phản biện thứ 2 (`rebuttal`) kèm trích xuất nguyên văn mã nguồn để xác lập đồng thuận thực chứng, tuyệt đối không mù quáng thực thi các yêu cầu làm vỡ `capsys` hoặc monkeypatch seams.
4. **Module-Level Monkeypatch Seam & AST Function Length Ratchet (`coordinator.py`, `sdk_inspector.py`)**:
   - Khi phân rã các hàm điều phối lớn để thỏa mãn trần KISS ($\le 50$ LOC), các điểm neo cấp module đang được test suite monkeypatch (`coordinator.assess_catalog_freshness`, `_get_synchronizer_cls()`) phải được giữ nguyên ở cấp module và được gọi trực tiếp từ helper method, kết hợp khóa cứng bằng ratchet test `check_ast_function_length(targets, max_lines=50)`.

---

## 38. Quản Trị Phân Tầng Năng Lực AI Gateway (Reasoning Tiering Parity) & Định Vị Tầng Hệ Thống (Layer Anchoring)

### Context & Incident Root Cause (Sự cố ngày 2026-10-07)
Trong phiên rà soát và thẩm định kỹ năng, Grok CLI gọi `claude-sonnet-4-6` qua LiteLLM Gateway (`:8090`). Proxy thượng nguồn (`antigravity-tools` :8045) trả về lỗi HTTP 503 / 429 trên các model Claude.
LiteLLM tự động kích hoạt chuỗi fallback:
$$\text{claude-sonnet-4-6} \longrightarrow \text{claude-sonnet-4-5} \longrightarrow \text{claude-haiku-4} \longrightarrow \mathbf{ocr\text{-}tier4\ (gemini\text{-}2.5\text{-}flash)}$$
Model `gemini-2.5-flash` nhận request và trả về 200 OK. Do LiteLLM fallback trong suốt (*transparent fallback*), client Grok ghi nhận token tiêu thụ dưới tên `claude-sonnet-4-6`.
Hệ quả: Bài toán thẩm định kiến trúc/code review bị âm thầm hạ cấp (*silent degradation*) xuống một model cấp thấp chuyên dụng cho OCR tài liệu (non-thinking), tạo ra **ảo giác an toàn (False Sense of Security)** cực kỳ nguy hiểm.

### Key Architectural Invariants & Learned Rules
1. **Reasoning-Class Parity & Anti-Silent-Degradation (RULE-1.22)**:
   - Các tác vụ suy luận (Frontier Reasoning / Architecture Review / Code Audit) BẮT BUỘC duy trì tính đồng đẳng phân tầng (Class A).
   - CẤM các model Class A fallback về Class C (`ocr-tier4`, `ocr-fallback`).
   - Khi toàn bộ model suy luận cạn kiệt quota, Gateway BẮT BUỘC áp dụng chính sách **Fail-Fast** (trả về lỗi HTTP 503) thay vì âm thầm trả về kết quả hời hợt từ model OCR.
2. **Layer Anchoring Invariant (vLLM Backend vs Gateway Routing) (RULE-5.10)**:
   - *Tầng 1 (vLLM Engine / Hardware)*: Quản lý mô hình vật lý trên GPU GB10 (`--served-model-name qwen-local-primary`).
   - *Tầng 2 (LiteLLM Gateway / Routing)*: Quản lý bảng định tuyến, fallback và các Virtual Deployments (`local-coder` bật thinking vs `rag-core` tắt thinking).
   - Cú pháp mảng fallback tĩnh của LiteLLM `fallbacks: [{"model_a": ["model_b"]}]` chỉ chấp nhận chuỗi định danh `model_name`, CẤM đưa tham số động dạng `qwen-local-primary (enable_thinking=true)` vào cấu hình tĩnh.
   - Khi cấu hình fallback cho task suy luận trên DGX Spark, BẮT BUỘC dùng virtual deployment **`local-coder`** (đã đóng gói sẵn `chat_template_kwargs: {enable_thinking: true}`, `max_tokens: 16384`) thay vì `rag-core` hay tên engine vật lý.
3. **Traceability Action**:
   - Đã tạo RFC Issue [#95 trên vvChu/dgx-spark-toolkit](https://github.com/vvChu/dgx-spark-toolkit/issues/95) để tái cấu trúc toàn diện chuỗi fallback của `services/ai-gateway/litellm_config.yaml`.

---

## 40. One-Way Door 3-Tier Manifest, Backpressure Circuit-Breaker & Tool-Starvation Calibration in Plan Audits (Issue #519 / HUB-ADR 0067)

### Context & Implementation Summary
Phiên triển khai đặc tả Danh mục Cửa Một Chiều (One-Way Door Manifest) và Cơ chế Áp lực ngược (Backpressure Circuit-Breaker) cho Agent Harness theo Issue #519 và chuẩn hóa thành **HUB-ADR 0067**:
- **Slice 1 (`02221540` — `door_policy.py`)**: Thiết lập 7 danh mục Cửa Một Chiều trong `ONE_WAY_DOOR_MANIFEST` (`SCHEMA_MIGRATION`, `AUTHZ_SECURITY`, `CROSS_SPOKE_CONTRACT`, `PUBLIC_API_SEAM`, `PII_FINANCE_QUOTA`, `DEPENDENCY_LICENSE`, `HUB_CONSTITUTION`) phân tầng 3 mức (`TWO_WAY_DOOR`, `PAVED_ROAD`, `ONE_WAY_DOOR`) qua `classify_pr_door()`. Tích hợp bộ đếm tích lũy `compute_cumulative_streak()` tự động nâng cấp lên `ONE_WAY_DOOR` khi chạm chuỗi $K \ge 3$ PRs `PAVED_ROAD` liên tiếp trên cùng canonical module (`packages/<pkg_name>`) trong 72h hoặc vượt ngân sách $> 200$ logic LOC, kèm `is_sampled_for_audit()` lấy mẫu 10% SHA-256 tất định.
- **Slice 2 (`e7abffbf` — `backpressure.py`)**: Triển khai `evaluate_backpressure_queue()` và `validate_tradeoff_card()`:
  1. `evaluate_backpressure_queue`: Kích hoạt ngắt mạch hàng đợi khi số PR `ONE_WAY_DOOR` đang chờ $> 5$ hoặc tuổi PR lâu nhất $> 24.0\text{h}$, kèm cơ chế chống deadlock (`bypass_active=True` cho `is_existing_pr_update` và `is_hotfix`).
  2. `validate_tradeoff_card`: Cưỡng chế 3 trường bắt buộc trong `TradeoffCard` (`Core Invariant`, `Invalidation Condition`, `Git Hunk Reference` có neo dòng `#L<a>-L<b>` hoặc diff block $\le 30$ dòng, sau khi lọc HTML comments và placeholders) cho mọi PR thuộc `ONE_WAY_DOOR`.
- **Slice 3 (`55c8754e` — CLI, CI & HUB-ADR 0067)**: Đăng ký subcommand `ccba-harness door-triage` (`run_door_triage_cli` với `--logic-loc`, `--pr-number`, `--repo`, `--pr-body-file`, `--enforce-tradeoff-card`, `--json`) vào `cli/commands/architecture.py` và `.github/workflows/pr-verifier.yml`; cập nhật `.github/pull_request_template.md` và ban hành `docs/adr/0067-one-way-door-manifest-and-backpressure-circuit-breaker.md`.

### Key Architectural Invariants & Learned Patterns
1. **Package-Level Canonical Module Normalization against Salami Slicing (`COND-519-03` Calibration)**:
   - Nếu chuẩn hóa module ở cấp tệp lẻ hoặc `<submodule>`, tác nhân AI có thể chia nhỏ 1 đợt refactor lớn thành nhiều PR sửa các file khác nhau trong cùng một package để né ngưỡng `streak_threshold = 3`.
   - Bắt buộc gom nhóm ở cấp độ `packages/<pkg_name>` (hoặc `scripts/<subdir>`, `.agents/skills/<skill_name>`) trong `extract_canonical_module()` để khóa chặt hành vi Salami Slicing.
2. **Zero-Network Local Git Log over Redundant GitHub API Calls (`COND-519-01` KISS Calibration)**:
   - Khi GitHub Actions workflow (`pr-verifier.yml`) đã checkout với `fetch-depth: 0`, việc xây dựng thêm HTTP client gọi GitHub REST/GraphQL API để lấy lịch sử merge 72h là vi phạm KISS và tạo điểm lỗi mạng/rate-limit không cần thiết.
   - Sử dụng `git log --since=... --name-only` trong `load_recent_merges_from_git()` đảm bảo tính tất định 100% ở cả môi trường CI lẫn chạy offline cục bộ.
3. **Plan Audit Tool-Starvation Defense (`audit_plan` vs `audit_direct --no-tools`)**:
   - Profile `audit_plan` trong `peer.py` bật công cụ đọc đĩa (`read_file`, `list_dir`) nhưng không có `system_prompt` giới hạn số bước khảo sát, khiến Grok CLI dễ rơi vào vòng lặp đọc 30–40 tệp liên tiếp đến khi cạn kiệt `max_turns=12` mà chưa kịp sinh khối YAML `PeerVerdictBlock`.
   - Khi thẩm định `implementation_plan.md` đã đính kèm đầy đủ ngữ cảnh và chữ ký hàm, ưu tiên sử dụng `--profile audit_direct --no-tools` để nhận phán quyết tất định trong 1 turn ($\sim 35\text{s}$).
4. **CLI Subcommand Registration Parity Contract (`test_cli_contract_parity.py`)**:
   - Mọi subcommand mới đăng ký vào `ccba-harness` (như `door-triage`) bắt buộc phải được khai báo đồng bộ vào `ALL_SUBCOMMAND_INVOCATIONS` và `expected_symbols` trong `packages/ccba-harness/tests/test_cli_contract_parity.py` để vượt qua cổng kiểm tra tính tương đương hợp đồng CLI.

---

## 41. Thượng Nguồn Hóa Kiểm Tra AST Raw Model & IP Leakage Vào `check_spoke_cleanliness.py` (Issue #530 / PR #534)

### Context & Implementation Summary
Phiên xử lý Issue #530 (PR #534 — `c9313552`) tích hợp bộ kiểm tra chuỗi model thô và địa chỉ IPv4 cố định vào kịch bản vệ sinh trung tâm `scripts/spoke/check_spoke_cleanliness.py`:
- **Active Guardrail Wiring over Dead Helpers (Phương án A2)**: Tại Spoke `dgx-spark-toolkit`, hai hàm `check_raw_model_leakage` và `check_raw_ip_leakage` trước đó chỉ được định nghĩa độc lập để phục vụ unit test mà chưa được nối vào `scan_spoke_cleanliness()`, đồng thời có nguy cơ bị ghi đè mỗi khi chạy `sync_spoke.py --apply` (do `TestGuardrailCopier` trong `sdk_inspector.py` chép đè từ `scripts/spoke/check_spoke_cleanliness.py`). PR #534 tích hợp cả hai hàm vào Hub SSOT và nối trực tiếp vào `scan_spoke_cleanliness()` (`_append_code_violations`, `_append_machine_and_ip_violations`), cưỡng chế `Parameter Externalization & Dynamic Scale Invariant` (Layer 1 Constitution) trên toàn bộ Spokes.
- **Single-Line Docstring State Preservation (`COND-02`)**: Trong `check_raw_ip_leakage`, trạng thái `was_in_docstring = in_docstring` được ghi nhận trước khi đảo cờ `"""` / `'''` kết hợp kiểm tra `triple_q in stripped`, đảm bảo các docstring 1 dòng (`"""Example IP: <TAILSCALE_GATEWAY_IP>"""`) được bỏ qua chính xác thay vì chỉ bỏ qua docstring nhiều dòng.
- **AST Function Length Decomposition ($\le 50$ LOC)**: Tách `_hub_catalog_from_workspace_ctx`, `_append_code_violations`, và `_append_machine_and_ip_violations` để toàn bộ hàm trong `check_spoke_cleanliness.py` đạt $\le 50$ LOC (`peer-gate` 8/8 PASS).

### Key Architectural Invariants & Learned Patterns
1. **Guardrail SSOT & Active Pipeline Wiring Invariant (`RULE-1.13`)**:
   - Mọi hàm kiểm tra vệ sinh trong `scripts/spoke/check_spoke_cleanliness.py` (`check_raw_model_leakage`, `check_raw_ip_leakage`) bắt buộc phải được gọi trực tiếp trong `scan_spoke_cleanliness()`, cấm để ở trạng thái helper mồ côi chỉ gọi từ unit test (*Dead Guardrail Helper Anti-Pattern*).
   - `check_raw_ip_leakage` bắt buộc bảo toàn trạng thái `was_in_docstring` cho docstring 1 dòng (`"""..."""`), loại trừ loopback, `0.0.0.0`, multicast, broadcast, `STANDARD_PUBLIC_DNS` (`8.8.8.8`, `8.8.4.4`, `1.1.1.1`, `1.0.0.1`) và dòng có `# ccba:allow-raw-ip`.
2. **Secondary Worktree Release Cleanup (`--detach origin/main`)**:
   - Khi nhánh `main` đang được checkout tại worktree chính (`/home/vvc/ccba/ccba-agent-platform`), lệnh `gh pr merge --delete-branch` hoặc `git checkout main` tại worktree phụ sẽ báo lỗi `fatal: 'main' is already used by worktree`. Quy trình dọn dẹp chuẩn tại worktree phụ là `git fetch --prune origin && git checkout --detach origin/main && git branch -D <branch>` kết hợp `git -C <primary_worktree> pull origin main`.

---

## 42. Phản Biện Toàn Diện Backlog Đa Repo (`#511`, `#512`, `#514`, `#522`, `#523` & `IDOP-CCBA-WAY` `#10`–`#12`): Chống Thiên Lệch Tuân Thủ (`RULE-1.24`, `RULE-4.18`, `RULE-5.11`)

### Context & Incident Root Cause (Sự cố ngày 2026-10-17)
Trong phiên tổng rà soát backlog trên `vvChu/ccba-agent-platform` (12 issues: `#507`–`#514`, `#519`, `#522`, `#523`, `#530`) và `vvChu/idop-ccba-way` (3 issues: `#10`, `#11`, `#12`), các yêu cầu từ Hermes Agent / Wayfinder cũ chứa nhiều đề xuất lý thuyết sinh tự động từ tài liệu thiết kế tổng quát.
Ở vòng viết `Agent Brief` hàng loạt ban đầu, Agent đã rơi vào bẫy **Compliant Execution Bias** (cố gắng thu hẹp phạm vi để tạo ra một đặc tả kỹ thuật thực thi được cho mọi issue thay vì bác bỏ các đề xuất sai kiến trúc ngay từ đầu). Khi thực hiện kiểm toán phản biện 2 vòng (Double-Pass Adversarial Review — Rule 5 KISS & Rule 8) trên mã nguồn thực tế, chỉ có **3/12 issues** trên Hub (`#513` PR `#533`, `#530` PR `#534`, `#519` PR `#535`/`#536`) mang lại giá trị thực chất; **5 issues** (`#511`, `#512`, `#514`, `#522`, `#523`) bị đóng `not_planned`, **4 issues** (`#507`–`#510`) bị đóng `duplicate`, và **3 issues** trên `idop-ccba-way` (`#10`, `#11`, `#12`) được đóng `completed` do đã hoàn thành qua lộ trình `P3.0` $\to$ `P5.4` (PR `#28` $\to$ `#41`).

### Key Architectural Invariants & Learned Rules
1. **Federated Role & ERP Lifecycle Boundary Guard (`RULE-1.24`, ADR-0046, ADR-0060)**:
   - Bảng 15 `ROLE_ID` (`ROLE_DIRECTOR` $\to$ `ROLE_EXTERNAL_CLIENT` trong `06_ccba_org_role_matrix.md`) và chu trình nghiệp vụ 5 pha (`OPPORTUNITY (CRM)` $\to$ `CONTRACT (HĐKT)` $\to$ `WORK_ORDER (PGV)` $\to$ `EXECUTION` $\to$ `SETTLEMENT (Quyết toán P&L 3 tầng)`) thuộc độc quyền domain SharePoint ERP của Operations Hub **`IDOP-CCBA-WAY`** (`#522`, `#523`).
   - Tại **`ccba-agent-platform`**, SSOT định danh là **ADR-0046** (`seat_role` + 5 cấp `qc_governance`, bảo toàn vai trò kỹ thuật `CHU_TRI_BO_MON`), cầu nối bàn giao CDE là `scripts/spoke/idop_bridge.py` (`StagedSubmittal`), và kiểm soát hạn ngạch chi phí là **LiteLLM Virtual Keys** (`ADR-0060`) + `telemetry.py` / `fleet.py` (model local GPU `$0.00`). CẤM dựng Dual-SSOT hoặc chặn cứng tác tử R&D/Sandbox khi không có `pgv_code == APPROVED`.
2. **Pre-Brief / Pre-Plan Problem-Validity, Scale & Seam-Parity Gate (`RULE-4.18`)**:
   - Trước khi viết `Agent Brief` (`/ccba-contribute-to-hub`, `/ccba-issue-to-hub`) hoặc lập `implementation_plan.md` (`/ccba-new-feature`), Agent BẮT BUỘC thẩm định 4 chiều chống *Compliant Execution Bias*:
     1. *Scale Reality*: CẤM áp hạ tầng tìm kiếm phức tạp (Vector 40% + BM25 30% + Graph 30% RRF `#511`) lên tập dữ liệu tĩnh quy mô nhỏ (`catalog.yaml` $N=76$ skills, đọc `2ms` theo `ADR-0047`, đã có `find_seams` theo hợp đồng kiểu `in/out` `ADR-0061` và `score_skill_match` trong `_miner_catalog.py`).
     2. *ADR Invariant Parity*: CẤM đề xuất Push-Injection / `dynamic truncation` (`#512`) làm vỡ kiến trúc Pull-based Progressive Disclosure (`ADR-0040`) và cắt mất phần Guardrails ở cuối `SKILL.md`; CẤM trộn lẫn Runtime Telemetry vào chỉ số tĩnh Design-Time GPI (`#514`) làm gãy cổng CI tất định `validate_skills.py --enforce-gpi` (`ADR-0057`, `ADR-0058`).
     3. *Seam & Federated Boundary*: CẤM dịch cơ học khái niệm quản trị nhân sự (EOS GWC `#523`) hoặc quy trình kế toán ERP (`#522`) thành module trùng lặp với Seams sẵn có (`SandboxPromoter`, `MaskaraScanner`, `choose_model`, `evals/daemon.py`, `SKILL_DEPRECATION_ALIASES`).
     4. *Overcome-by-Events (OBE) Cross-Check*: Đối chiếu lịch sử commit/PR thực tế (`P3.0` $\to$ `P5.4` trên `IDOP-CCBA-WAY` `#10`–`#12`) để đóng `completed` các ticket đã được giải quyết ở các lát cắt kiến trúc sau.
3. **GitHub Classic Projects GraphQL Deprecation & Project V2 Field Discovery (`RULE-5.11`)**:
   - Lệnh `gh issue view <id>` (không truyền `--json`) thất bại với exit code 1 (`GraphQL: Projects (classic) is being deprecated`) do `gh` CLI mặc định truy vấn trường `projectCards` cũ. BẮT BUỘC luôn truyền `--json number,title,state,body,labels,comments` hoặc gọi `gh api repos/<owner>/<repo>/issues/<id>`.
   - Khi đồng bộ trạng thái trên GitHub Project V2 (`gh project item-edit`), luôn truy vấn `gh project field-list <num> --owner <owner> --format json` để lấy chính xác `PVTSSF_...` Field ID hiện hành và kiểm tra `--limit 100` trên `gh project item-list`.

---

## 43. Liveness-Aware Grok Watchdog, Multi-Turn Resume Telemetry & Degraded-Reasoning Gate (`RULE-4.19`, HUB-ADR 0063, HUB-ADR 0064)

### Context & Historical Forensics (Phân tích 602/603 phiên `~/.grok/sessions/` & 123 tệp `.md/peer_exchange/`)
Qua phân tích thực chứng trên **602/603 sessions** trong `~/.grok/sessions/` (`453.12M` tổng tokens, `6,510` model calls, `93` phiên bị hủy giữa chừng) và **123 tệp** trong `.md/peer_exchange/`, phát hiện 5 điểm nghẽn vận hành cốt lõi:
1. **Rò rỉ `.bridge_cache.json` & Lệch Schema [`status.json`](../../.md/peer_exchange/status.json)**: Mâu thuẫn kiểu giữa `CombinedTelemetry` và `PeerVerdictTelemetry` trong `PeerVerdictBlock`, tệp `.gate.md` bị phân loại nhầm thành `GROK_RESPONSE`, và 3 tệp lịch sử có `risk_score > 5` (`6, 18, 28`) khiến `pending_grok` bị kẹt ảo `9` yêu cầu.
2. **Độ trễ MCP Web-Search & Rò rỉ 15 Built-in Tools**: Grok CLI nạp `claude-api-web-search-mcp` (`275ms–490ms`) và tự động bật 15 built-in tools (tên tool ghi tệp thực tế là `write` thay vì `write_file`).
3. **Lệch Telemetry khi Resume đa lượt (`--resume` & `--fork-session`)**: Khi dùng `--resume`, `grok usage <session_id>` trả về `data["session"]` của Lượt 1 thay vì số liệu lượt hiện tại trong `data["turns"][-1]`.
4. **Hủy nhầm phiên đang Streaming hoặc Mất dữ liệu `temp_out` khi treo sau `turn_ended:*`**: `93/602` phiên bị hủy giữa chừng do chạm `deadline` cứng khi đang `streaming_text` hoặc treo sau `turn_ended:*`.
5. **Silent Reasoning Degradation (`reasoning_tokens == 0`)**: Phiên yêu cầu `high`/`xhigh` nhưng trả về `0` reasoning tokens mà không có cảnh báo chặn ở bước tổng hợp đồng thuận.

### Key Architectural Invariants & Learned Rules (`RULE-4.19`)
1. **Liveness-Aware Subprocess Watchdog (`_peer_watchdog.py` — `inspect_session_liveness`)**:
   - Đọc sự kiện cuối trong `~/.grok/sessions/**/<session_id>/events.jsonl` (`f"{etype}:{detail}"` và `age_seconds`):
     - **Fail-Fast An Toàn (`90s` chỉ cho `mcp_init_completed:`)**: Ngắt tiến trình ngay khi `last_state in ("turn_ended:error", "turn_ended:cancelled")` hoặc kẹt tại `mcp_init_completed:` quá `90.0s`. Tuyệt đối **không** ngắt sớm ở `phase_changed:waiting_for_model` (bảo vệ các phiên suy luận sâu hợp lệ kéo dài `90s–1,213s`).
     - **Turn-Ended Drain (`5s`) & Bảo toàn `temp_out`**: Khi tiến trình treo sau `turn_ended:*` (`age_s > 5.0s`), bắt buộc gọi `temp_out.seek(0); stdout_text = temp_out.read()` trước khi `_terminate_proc_tree(proc)`.
     - **Streaming Grace Window (`+45s`, tối đa 1 lần)**: Khi chạm `deadline` nhưng `last_state in ("phase_changed:streaming_text", "phase_changed:streaming_reasoning")` với `age_s < 5.0s`, cấp thêm `+45.0s` để hoàn tất xuất văn bản.
     - **Cứu hộ `chat_history.jsonl`**: Khi `_unwrap_grok_json_stdout` ghi nhận `stopReason != "end_turn"` hoặc thiếu frontmatter, gọi `_recover_verdict_from_chat_history()` để cứu hộ `PeerVerdictBlock` hợp lệ đã sinh ra trước khi chạm `max_turns`.
2. **Headless Tool Lockdown (`NO_TOOLS_DISALLOW_LIST` & `READ_ONLY_DISALLOW_LIST`)**:
   - Bật `disable_web_search: True` và `verbatim: True` cho toàn bộ 8 profiles trong `PROFILE_SPECS`; khóa đầy đủ 15 built-in tools của Grok CLI (bao gồm `"write"`, `"todo_write"`, `"monitor"`, `"search_tool"`, `"use_tool"`, `"workflow"`, `"enter_plan_mode"`, `"exit_plan_mode"`, `"ask_user_question"`, `"send_feedback"`, `"web_fetch"`).
3. **Multi-Turn Resume Telemetry & Degraded-Reasoning Gate (`_peer_telemetry.py` & `peer.py`)**:
   - Trong `_build_telemetry_from_usage_json()`, ưu tiên hợp nhất `turns[-1]` khi `len(turns) > 1` để lấy đúng token/cost của lượt `--resume`.
   - Khi `expected_reasoning_effort in ("high", "xhigh")` nhưng `reasoning_tokens <= 0`, bật `degraded_reasoning = True` trên `PeerVerdictTelemetry` và tự động chèn `PeerCondition(id="COND-DEGRADED-REASONING", blocking=True)` trong `_consolidate_peer_conditions()` / `synthesize_verdicts()` để hạ cấp `APPROVE` $\to$ `APPROVE_WITH_CONDITIONS`.

---

## 44. Xóa Sạch 100% `# ccba:quarantine` Toàn Monorepo, Phân Rã `peer.py` & Chống Ghi Đè Cấu Hình `pytest` Cục Bộ (PR `#540`–`#546`, `RULE-2.9`, `RULE-2.20`)

### Context & Refactoring Scope (Chuỗi PR `#540`, `#541`, `#542`, `#543`, `#545`, `#546` ngày 2026-10-18)
Sau khi hoàn tất PR `#539`, rà soát toàn diện kiến trúc `ccba-harness`, `ccba-legal-intel` và tài liệu quy tắc vận hành phát hiện:
1. [`docs/rules/execution_guardrails.md`](../../../docs/rules/execution_guardrails.md) dài `442` dòng (vượt ngân sách `< 250` dòng của Layer-2 rule docs và còn tham chiếu `ADR 0044` cũ thay vì `ADR-0061`).
2. [`packages/ccba-harness/src/ccba_harness/peer.py`](../../../packages/ccba-harness/src/ccba_harness/peer.py) dài `1,879` dòng (vượt ngân sách `800` LOC của `module_size_budget`), và chính [`peer_gate.py`](../../../packages/ccba-harness/src/ccba_harness/peer_gate.py) có 5 hàm vượt quá giới hạn `50` dòng của cổng `check_ast_function_length` do chính nó thực thi.
3. Toàn monorepo tồn tại **12 thẻ `# ccba:quarantine`** (`10` trong `ccba-harness` và `2` trong `ccba-legal-intel/src/ccba_legal/sync/engine.py`) cùng 2 module sát ngưỡng 800 dòng trong `ccba-legal-intel` (`engine.py` `821` LOC và `table_handler.py` `801` LOC).
4. Khi chạy lệnh Scoped Tests theo tài liệu `packages/*/AGENTS.md`, `pytest packages/ccba-legal-intel/tests` bị lỗi `ModuleNotFoundError: No module named 'ccba_pdf_prep'` kèm 47 cảnh báo `PytestUnknownMarkWarning`, và `pytest packages/mdconverter/tests` thất bại với `exit code 4 (unrecognized arguments: --cov=...)` do `[tool.pytest.ini_options]` trong `pyproject.toml` của package con ghi đè `pyproject.toml` gốc.

### Key Architectural Invariants & Learned Rules (`RULE-2.9`, `RULE-2.20`)
1. **Zero-Quarantine Monorepo & Modular Facade Decomposition (`RULE-2.20`)**:
   - **PR `#540` (`1ba5ea8b`)**: Tinh gọn `docs/rules/execution_guardrails.md` từ `442` xuống `243` dòng (`< 250` dòng), đồng bộ tham chiếu `ADR-0061` và danh mục 15 built-in tools của Grok CLI.
   - **PR `#541` (`b3430468`)**: Phân rã `peer.py` (`1,879 -> 775` LOC) thành 4 module có ranh giới trách nhiệm rõ ràng (`_peer_models.py` `384` LOC, `_peer_anchor.py` `290` LOC, `_peer_co_review.py` `468` LOC, và facade `peer.py` `775` LOC bảo toàn 100% `__all__` backward-compatibility), xóa `peer.py` khỏi `module_budget_baseline.json` và gỡ 5 thẻ `# ccba:quarantine` trong `cli/commands/peer.py` & `_peer_auto_apply.py`.
   - **PR `#542` (`e914a9e2`)**: Gỡ tiếp 5 thẻ `# ccba:quarantine` còn lại trong `ccba-harness` (`evals.py`, `telemetry.py`, `verifier.py`), phân rã 5 hàm vượt ngưỡng trong `peer_gate.py` ($\le 50$ LOC/hàm), và bổ sung `E203` vào `--extend-ignore=E501,E203` của `flake8` để tương thích với khoảng trắng trong slice (`line[idx : idx + N]`) của `ruff format`.
   - **PR `#543` (`e0073100`) & PR `#545` (`a93a57e7`)**: Gỡ 2 thẻ `# ccba:quarantine` cuối cùng tại `ccba_legal/sync/engine.py` (đưa tổng số `# ccba:quarantine` toàn monorepo về **0**), đồng thời phân rã `ccba_legal/engine.py` (`821 -> 686` LOC) và `table_handler.py` (`801 -> 692` LOC) đạt 100% `check_ast_function_length` ($\le 50$ LOC/hàm) và xóa cả 2 file khỏi `module_budget_baseline.json`.
   - **PR `#546` (`6d6970ac`)**: Bắt ngoại lệ `ValueError` thân thiện trong `run_verify_patch_cli` (`cli/commands/verifier.py`) khi gọi `--preset doc` / `--preset skill` thiếu `--target <file>`, trả về exit code `1` kèm thông báo `ERROR:` trên `stderr`.
2. **Subpackage `[tool.pytest.ini_options]` Shadowing & Hermetic Legal Sync Env (`RULE-2.9`)**:
   - Khi một package con (`ccba-legal-intel`, `mdconverter`, `ccba-ai`) định nghĩa `[tool.pytest.ini_options]` trong `packages/<pkg>/pyproject.toml`, `pytest` sẽ chọn file cấu hình cục bộ đó làm `inifile` và bỏ qua `pyproject.toml` gốc. Do đó, mọi `[tool.pytest.ini_options]` cấp package bắt buộc phải đồng bộ đầy đủ `pythonpath` sang các sibling packages phụ thuộc (`../ccba-pdf-prep/src`, `../ccba-ai/src`, `../ccba-harness/src`), danh sách `markers` chuẩn (`fast`, `unit`, `integration`, `slow`, `stress`, `adversarial`, `asyncio`), và cấm gắn cứng `--cov` trong `addopts`.
   - Các bài kiểm thử đồng bộ pháp lý (`test_hub_mediated_sync.py`, `test_remote_streaming_sync.py`) bắt buộc xóa cả `CCBA_LEGAL_KNOWLEDGE_PATH`, `CCBA_LEGAL_CORPUS_PATH`, `CCBA_HUB_PATH`, `HUB_PATH` qua `monkeypatch.delenv(..., raising=False)` để cô lập hoàn toàn khỏi biến môi trường máy trạm.

---

## 45. Điều Phối Đa Chế Độ Cho Kỹ Năng Hợp Nhất (`3-Mode Intent Dispatch`) & Chuẩn Hóa Tham Chiếu Kỹ Năng Trong `resources/*.yaml` (PR `#544`, `RULE-1.18`, `RULE-4.2`)

### Context & Incident Root Cause (Sự cố ngày 2026-10-18 trên `/ccba-ask`)
Khi người dùng gọi `/ccba-ask` để hỏi về kỹ năng thực hiện Brainstorming, rà soát 2 vòng (Double-Pass Adversarial Review — Rule 5 KISS & Rule 8) trên `.agents/skills/ccba-ask/` phát hiện 2 điểm đứt gãy hậu hợp nhất kỹ năng (Skill Consolidation):
1. **Đứt gãy định tuyến nội bộ trong `SKILL.md` (Missing Multi-Mode Dispatch Table)**: Trong đợt hợp nhất trần 76 skills (`ADR-0057`), `/ccba-ask` đã hấp thụ 2 kỹ năng `/ccba-brainstorm` (`references/brainstorm_templates.md`, `references/brainstorm_techniques.md`) và `/ccba-wait-what` (`references/clarification_patterns.md`), đồng thời bổ sung `brainstorm` và `wait-what` vào `triggers`. Tuy nhiên, phần thân `SKILL.md` chỉ mô tả duy nhất chế độ Tư vấn chọn Slash Command và không nhắc tới Brainstorming ở Bước 1 của luồng `Idea -> Ship`, khiến Agent chỉ trả lời lý thuyết nếu không chủ động mở Level 3 references.
2. **Tham chiếu kỹ năng lỗi thời (`Dangling Skill References`) trong `resources/brainstorm_topics.yaml`**: Đối chiếu thực nghiệm với 76 skills trong `.agents/skills/` phát hiện **11/20** mục trong `required_skills` của 4 chủ đề (`legal`, `pccc_mep`, `bim_arch`, `software`) vẫn trỏ tới tên cũ trước khi hợp nhất/đổi tên (`docx`, `pdf`, `legal-document-tracker`, `excalidraw-diagram`, `ccba-prototype`, `code-review`, `web-testing`, `api-circuit-breaker`, `append-only-logger`), do cổng `audit_workspace_gates()` trong `skill_validator.py` chỉ quét frontmatter của `SKILL.md` mà chưa quét khóa `required_skills` trong `resources/*.yaml`.

### Key Architectural Invariants & Learned Rules (`RULE-1.18`, `RULE-4.2`)
1. **Multi-Mode Intent Dispatch Table cho Consolidated Skills (`RULE-4.2`)**:
   - Mọi kỹ năng hợp nhất đa chức năng (như `/ccba-ask` tích hợp Router + Brainstorm Coach + Wait-What, `/ccba-contribute-to-hub` tích hợp Contribute + Review Proposal, `/ccba-issue-to-hub` tích hợp RFC Issue + Triage) **BẮT BUỘC** có bảng **Phân Tuyến Chế Độ Hoạt Động (Mode Dispatch Table)** ngay ở phần thân `SKILL.md` để chỉ rõ tín hiệu kích hoạt và tệp tham chiếu Level 3 cần nạp ngay lập tức (`references/brainstorm_templates.md`, `references/proposal_review_sop.md`, `references/issue_triage_flow.md`).
2. **Canonical Skill-Reference Parity trong `resources/*.yaml` (`RULE-1.18`)**:
   - Mọi danh sách kỹ năng trong tệp cấu hình tài nguyên của skill (`required_skills` trong `.agents/skills/*/resources/*.yaml`) bắt buộc phải khớp 100% với tên thư mục canonical trong `.agents/skills/` (có đầy đủ tiền tố namespace `ccba-` / `bigbim-` và không chứa tên skill đã bị gộp như `ccba-prototype`, `docx`, `pdf`).

---

## 46. Hậu Kiểm Đơn Luồng Grok Peer Exchange, Tái Kết Xuất YAML Frontmatter Bất Biến (`COND-RE-RENDER-ON-MUTATION`) & Sắp Xếp Đa Khóa Tất Định (`RULE-4.19`)

### Context & Incident Root Cause (Kiểm toán dữ liệu thực nghiệm 127 tệp `.md/peer_exchange/` & Thảo luận Peer `req-20261018-discuss-peer-coordination-refinements-001`)
Qua phân tích thực nghiệm toàn bộ `127` tệp trong `.md/peer_exchange/` (`58` prompts, `61` responses, `28.86M` tokens, `\$8.43` USD) và đối thoại phản biện trực tiếp với Grok CLI (`grok_discuss_peer_coordination_refinements.md`), phát hiện 5 lỗ hổng kỹ thuật trong luồng đơn (`peer-dispatch` không bật `--co-review`):
1. **Rò rỉ `APPROVE` khi suy luận suy giảm hoặc có điều kiện chặn ở luồng đơn (`Single-Verdict Guardrail Gap`)**: Logic chèn `COND-DEGRADED-REASONING` (`reasoning_tokens == 0` trên `high`/`xhigh`) và hạ cấp `APPROVE` $\to$ `APPROVE_WITH_CONDITIONS` khi có `blocking=True` hoặc `risk_score >= 4` trước đây chỉ nằm trong `synthesize_verdicts()` của `_peer_co_review.py` (chế độ 2-seat). Ở chế độ 1-seat mặc định (`59/61` lượt chạy thực tế), `_finalize_grok_verdict_and_telemetry()` chỉ gán `verdict.telemetry = telemetry` mà không hậu kiểm `verdict.verdict` hay `verdict.conditions`.
2. **Đứt gãy đồng bộ trên đĩa nếu không tái kết xuất YAML frontmatter (`COND-RE-RENDER-ON-MUTATION`)**: Do `grok usage` chỉ được gọi trong `_finalize_grok_verdict_and_telemetry()` *sau khi* Grok CLI thoát, mọi thay đổi trên `verdict` (`telemetry`, `conditions`, hoặc hạ cấp `verdict`) bắt buộc phải được kết xuất lại vô điều kiện qua `render_verdict_header(verdict) + "\n" + body.lstrip()` trước khi `atomic_write_text()`.
3. **Thứ tự thời gian `latest_verdict` và `update_live_summary` bị trôi theo bảng chữ cái**: `_build_latest_verdict()` lấy `responses[-1]` từ danh sách sắp xếp theo tên file (`sorted(p.iterdir(), key=lambda x: x.name)`), khiến phán quyết mới nhất theo thời gian thực (`mtime`) bị che khuất bởi tệp có tên đứng cuối bảng chữ cái (`prompt_grok_triage_all_open_issues_pr_plan.md`).
4. **Hồ sơ dự phòng `DEFAULT_GROK_SPEC` thiếu khóa công cụ ghi (`Write-Tool Exposure`)**: Khác với `PROFILE_SPECS["default"]` đã khóa `READ_ONLY_DISALLOW_LIST`, hằng số fallback `DEFAULT_GROK_SPEC` có `tools: None` và `disallowed_tools: []`.

### Key Architectural Invariants & Learned Rules (`RULE-4.19`, Global Rule #5)
1. **Single-Verdict Post-Validation & Unconditional Re-Render (`RULE-4.19` / `COND-RE-RENDER-ON-MUTATION`)**:
   - Hàm `_enforce_single_verdict_guardrails(verdict)` trong `_peer_telemetry.py` bắt buộc thực thi ở cuối `_finalize_grok_verdict_and_telemetry()`: tự động bơm `COND-DEGRADED-REASONING` (`blocking=True`) khi `telemetry.degraded_reasoning` bật, và hạ cấp `APPROVE`/`APPROVE_PLAN` xuống `APPROVE_WITH_CONDITIONS` nếu tồn tại điều kiện `blocking=True` hoặc `risk_score >= 4`.
   - Ngay sau hậu kiểm, `_finalize_grok_verdict_and_telemetry()` bắt buộc gọi `render_verdict_header(verdict)` vô điều kiện để đồng bộ YAML frontmatter xuống đĩa (`output_path`), đồng thời chỉ đọc `prompt_path` tối đa 1 lần trong bộ nhớ.
   - Khi `grok usage` thất bại và rơi về nhánh ước lượng văn bản `_build_fallback_telemetry()`, bắt buộc đặt `degraded_reasoning=False` để tránh dương tính giả (vì `TokenEstimator` không quan sát được `reasoningTokens`).
2. **Multi-Key Deterministic Chronological Sorting (`COND-CHRONOLOGICAL-TIE-BREAKER` / Global Rule #5)**:
   - Khi sắp xếp các tệp phán quyết trong `_build_latest_verdict()` và `update_live_summary()`, bắt buộc dùng khóa đa tiêu chí `key=lambda x: (-round(float(x.get("mtime", 0.0)), 4), x["path"].name)` (không dùng `reverse=True` bao trùm): ưu tiên `mtime` mới nhất giảm dần, và khi `mtime` trùng nhau trong cửa sổ `100us` (như sau `git checkout`/`clone`) thì phân xử tất định từ A $\to$ Z theo tên file.

---

## 47. Pstack Phase 3 (`Zero Skill Bloat`), Cổng Vệ Sinh Kỹ Năng Tiền Đánh Giá (`Pre-Eval Skill Hygiene Delta Guard`) & Bảo Toàn Ngân Sách Token Ban Đêm (`PR #550`, `PR #551`)

### Context & Incident Root Cause (Khảo sát `pstack v0.15.27/28` & Kiểm toán vận hành Nightly Auto-Tuner ngày 2026-10-19)
1. **Tiếp thu `pstack v0.15.20 -> v0.15.28` không làm phình số lượng kỹ năng (`PR #550` — `cd103c2e`)**:
   - Khảo sát 32 commits của `cursor/plugins/pstack` phát hiện 4 quy tắc thực chiến giá trị cao (`verify/maintain` với `sync_commit` + Semantic Mutation Proof, `unslop` Two-Edit Behavioral Test Litmus, `grill-me` Pre-Grill Sharpening, `catchup` Decision-Decidable Handoff). Thay vì tạo thêm skill mới vi phạm trần `ADR-0057`, cả 4 năng lực được tích hợp trực tiếp vào các Kernel Skills hiện hữu (`ccba-create-verification-skill` v1.2.0, `ccba-grilling` v1.1.0, `ccba-handoff` v2.1.0, `ccba-code-review/references/unslop_checklist.md`) và `docs/rules/code_quality.md` (Mục 10.4 & 17.5).
   - Trong quá trình chạy cổng kiểm định cho `PR #550`, phát hiện 2 bẫy kiểm định thực tế: (a) chạy `validate_skills.py --file <path>` đơn lẻ bỏ qua kiểm tra chéo cấp workspace (`UNREGISTERED_SLASH_COMMAND` trong `test_skill_taxonomy_and_gates.py` chặn việc nhắc tới tên lệnh `/ccba-verify` không đăng ký trong `catalog.yaml`); (b) cú pháp `$(git rev-parse --short HEAD)` trong khối `bash` chung bị `audit_skills_hygiene.py` chặn là Windows Bashism (`RE_BASHISMS`).
2. **Bão hòa chiến lược đột biến trên Nightly Auto-Tuner & Lỗ hổng Pre-Eval Hygiene (`PR #551` — `3ae61cca`)**:
   - Phân tích log `.md/logs/nightly_cron.log` và 5 PR tự động gần nhất (`#505`, `#515`, `#517`, `#538`, `#549`) cho thấy Pha `[3/3]` (`nightly_tuner_daemon.py`) tiêu tốn `1.93M – 6.78M tokens/đêm` (~1.5h–4.5h GPU) nhưng 74/75 skills rơi vào trạng thái bão hòa (`0.0% delta`), dẫn tới **5/5 PR đều bị đóng bỏ (`CLOSED`, `0 merged`)** và gây xung đột với nhánh `main`.
   - Ngoài ra, `_run_pre_eval_guards()` trong `_tuner_mutator.py` trước đây chỉ kiểm tra thẻ `ADR-XXXX` và `LinkAuditor`, chưa kiểm tra `audit_skill()` của `audit_skills_hygiene.py` trước khi gọi LLM chấm điểm. Bản thân `scripts/governance/audit_skills_hygiene.py` (`913 LOC`) cũng có 5/9 hàm vượt trần `50 LOC` (hàm `audit_skill` dài `239 LOC`) và hardcode ngày báo cáo `2026-09-12`.

### Key Architectural Invariants & Learned Rules (`RULE-2.5`, `RULE-2.20`, `RULE-4.1`, `RULE-4.16`)
1. **Semantic Mutation Proof 3-Step Rollback & Two-Edit Behavioral Test Litmus (`PR #550`)**:
   - Mọi bước kiểm chứng đột biến ngữ nghĩa (`Semantic Mutation Proof`) trong `ccba-create-verification-skill` bắt buộc tuân thủ hoàn nguyên 3 bước tất định: (1) xác nhận `git diff --quiet` sạch trước khi tiêm lỗi; (2) tiêm 1 đột biến ngữ nghĩa tối thiểu làm gãy bất biến cốt lõi và ghi nhận *counterexample failure log* (exit code $\ne 0$); (3) hoàn nguyên ngay lập tức qua `git checkout -- <mutated_files>` và xác minh lại `git diff --quiet` + pass suite.
   - Mọi unit/integration test mới phải vượt qua **Two-Edit Behavioral Test Litmus** (`docs/rules/code_quality.md` Mục 10.4): *Break the behavior* (làm sai lệch bất biến Mục 12) $\to$ test bắt buộc `FAIL`; *Change the internals* (đổi tên biến/hàm con nội bộ giữ nguyên hợp đồng I/O) $\to$ test bắt buộc `PASS`.
2. **Pre-Eval Skill Hygiene Delta Guard & Opt-In Nightly LLM Tuner (`PR #551`)**:
   - Trong `_RunAndGitMutatorMixin._run_pre_eval_guards()` (`_tuner_mutator.py`), hàm `_find_hygiene_audit_issues(baseline_content, mutated_content)` đối chiếu tập vi phạm `(category, detail)` của `audit_skill()` giữa bản đột biến và bản gốc (`mutated_issues - baseline_issues`). Cách đối chiếu chênh lệch (delta) này vừa chặn tức thì mọi lỗi vệ sinh mới (Windows bashisms `$(...)`, Dead Wood, lỗi frontmatter) trong `~2ms` trước khi tốn token LLM, vừa tương thích ngược 100% với các test fixtures tối giản không có frontmatter đầy đủ.
   - Trong `scripts/cron/run_nightly_tuner.sh`, Pha `[3/3]` mặc định thực thi cổng kiểm định tĩnh 76 skills (`python3 -m ccba_harness verify-patch --preset skill`, `0 tokens`, `~1.5s`). Chu trình đột biến LLM (`nightly_tuner_daemon.py`) được khóa sau cờ tường minh `--enable-tuner`, `--skill <name>`, hoặc biến môi trường `CCBA_ENABLE_NIGHTLY_TUNER=1`.

---

## 48. Phân Rã Layer 2 Rules Dưới Trần Antigravity 24KB, Tự Động Dọn Dẹp Zombie Rules & Di Trú Liên Kết Spoke (`PR #553` — `3f7db2d3`)

### Context & Incident Root Cause (Khảo sát Issue #552 ngày 2026-10-21)
1. **Giới hạn cứng 24KB của Google Antigravity Language Server (`rules.go:544`)**:
   - Runtime inspection phát hiện Antigravity tự động cắt cụt các tệp rule vượt quá 24,000 bytes khi nạp vào context window: `code_quality.md` (30,768 bytes, vượt 6.7KB, ~22% bị mất) và `execution_guardrails.md` (24,787 bytes, vượt 787 bytes).
   - Cơ chế `sync_layer2_rules` sao chép trực tiếp các tệp này xuống `.agents/rules/` của toàn bộ các Spoke (`IDOP-CCBA-WAY`, v.v.), khiến toàn bộ các AI Agent tại Spoke bị mất các quy tắc then chốt ở cuối file (như *Anti-Slop*, *Hypothesis-Driven Forensic*, *Atomic Micro-PR*, *Peer Delegation Protocol*).
2. **Nguy cơ Zombie Rules tại Spoke & Gãy Liên Kết Tham Chiếu**:
   - Nếu chỉ tạo tệp mới mà không dọn dẹp tệp cũ ở Spoke, cả tệp monolithic cũ và tệp phân rã mới sẽ cùng tồn tại song song, làm nhân đôi context injection.
   - Đồng thời, các liên kết trong `AGENTS.md` (kèm các anchor như `#19-atomic...`) cần được di trú tự động để tránh gãy liên kết khi các Spoke chạy lệnh đồng bộ.

### Key Architectural Invariants & Learned Rules (`RULE-1.25`, `RULE-5.12`)
1. **Antigravity 24KB Rule Hard Cap, Decomposition & Fleet Zombie Cleanup Invariant (`RULE-1.25`)**:
   - Mọi tệp quy tắc trong `docs/rules/` và `.agents/rules/` bắt buộc $\le 24,000$ bytes (mục tiêu $11–18$ KB) để triệt tiêu hoàn toàn lỗi silent truncation.
   - Khi phân rã tệp quy chuẩn tại Hub:
     - `docs/rules/code_quality.md` $\to$ `code_quality_standards.md` (16.3 KB) & `code_quality_verification.md` (18.2 KB).
     - `docs/rules/execution_guardrails.md` $\to$ `execution_runtime_guardrails.md` (11.2 KB) & `execution_coordination_guardrails.md` (14.8 KB).
   - `scripts/spoke/sync/graduation.py`: Bổ sung `LEGACY_MONOLITHIC_RULES` và cơ chế `_cleanup_legacy_monolithic_rules` tự động xóa tệp monolithic cũ khi sync xuống Spoke; `normalize_spoke_agents_links` tích hợp bảng `_migrate_legacy_rule_links` tự động viết lại đường dẫn cũ và anchor sang tệp phân rã mới.
2. **Venv Tooling Execution Parity & Non-Test Module Verify-Patch Pattern (`RULE-5.12`)**:
   - Trên môi trường Linux/POSIX, các công cụ linter (`ruff`, `mypy`) được cài đặt trong virtual environment `.venv/bin/python`, không nằm trong system python `/usr/bin/python3`. Lệnh kiểm định tự động bắt buộc phân giải qua `.venv/bin/python`.
   - Đối với các module không chứa test case (như `scripts/spoke/sync/graduation.py`), lệnh `verify-patch --preset code` sẽ thoát với exit code 5 (do pytest không thu thập được test nào). Quy chuẩn bắt buộc: sử dụng `verify-patch -c` chỉ định rõ linter + test suite mục tiêu thay cho preset code trần.
   - Kỷ luật AST Function Length $\le 50$ LOC: Mọi hàm bổ sung trong bộ đồng bộ hóa Spoke bắt buộc phải phân tách thành các hàm con đơn nhiệm, bảo đảm 100% tuân thủ bài test `test_coordinator_ast_function_length_compliance`.

---

## 49. Pstack Phase 4 (`v0.15.28`–`v0.15.36`), Kiểm Định Hạ Tầng `IDOP-CCBA-WAY` Hai Tầng (`Cycle-Safe BFS`), Đồng Bộ 3 Bề Mặt Thuật Ngữ `1812/QĐ-BXD` & Khắc Phục Điểm Mù `ImmutableSpanMasker.unmask` (`PR #581`–`#585`)

### Context & Incident Root Cause (Phiên ngày 2026-11-01 — PR `#581`, `#582`, `#583`, `#584`, `#585`)
1. **Tiếp thu `pstack` Phase 4 (`PR #581` `a1b60e8d`, `PR #582` `32527174`) & Kiểm định Hạ tầng Spoke `IDOP-CCBA-WAY` (`PR #583` `89553227`)**:
   - Qua thẩm định phản biện Grok (`Pass 1 Session: fdea9318-4eff-49c2-bc3f-614935fecc76`, `Pass 2 Session: 1a0cae16-2a73-497c-90b7-8f4f1677182f`), phát hiện 2 điểm mù trong kiểm định đồ thị trạng thái (`stateDiagram-v2`): (a) khối mã ví dụ thiếu từ khóa định danh đầu dòng (`stateDiagram-v2`) khiến trình kết xuất thất bại; (b) máy trạng thái phê duyệt thực tế của `IDOP-CCBA-WAY` (`CCBA_TrangThaiPheDuyet`: `Nhap -> DeTrinh -> YeuCauBoSung -> DeTrinh`) chứa chu trình lặp hợp lệ (`retry cycle`). Nếu dùng thuật toán tìm đường đệ quy ngây thơ không có tập `visited` sẽ rơi vào đệ quy vô tận (`RecursionError`), hoặc nếu cấm chu trình cứng nhắc sẽ bác bỏ nhầm quy trình nghiệp vụ thực tế.
   - Ngoài ra, CI của Hub trên GitHub Actions không có thư mục `/home/vvc/ccba/IDOP-CCBA-WAY`, nên bài kiểm thử hợp đồng hạ tầng phải tách thành 2 tầng (Tier 1 Golden Snapshot trong repo Hub + Tier 2 Live Spoke Parity tự động skip khi chạy trên CI runner).
2. **Đồng bộ 3 Bề Mặt Ngôn Ngữ Chung (`PR #584` `3af0ba55`) & Điểm Mù `doc_auto_evolution_engine.py`**:
   - Khi cập nhật `CONTEXT.md` để đóng các điều kiện `COND-S1..S3` từ Grok (`Session: cc36a0a9-759f-472d-90d5-5e8f6239f970`), việc ghi tên lớp tổng quát `` `SemanticDisambiguationMasker` `` trong `CONTEXT.md` làm gãy cổng CI `test_doc_auto_evolution_engine_dry_run` vì `doc_auto_evolution_engine.py` đối chiếu tĩnh mọi ký hiệu Python đặt trong dấu backtick của `CONTEXT.md` với cây AST thực tế (`ImmutableSpanMasker` trong `masker.py` và `FacetedDisambiguationEngine` trong `disambiguation.py`).
3. **Hai Điểm Mù Công Cụ Trong `ImmutableSpanMasker.unmask` & `conftest.py` Trên `pytest 8.x` (`PR #585` `9761e62b`)**:
   - Trong `packages/ccba-legal-intel/src/ccba_legal/lexicon/masker.py`, hàm `unmask()` dùng regex `r"(\d+)__\n*"` ăn tham lam toàn bộ ký tự xuống dòng `\n` ngay sau placeholder. Với các trích dẫn một dòng (`orig.count("\n") == 0`) ở cuối dòng YAML frontmatter (như `proposal_id: "..."\n`), `unmask()` nuốt mất ký tự `\n` của dòng YAML, làm dính liền toàn bộ YAML frontmatter của `.agents/proposals/*.md` khi chạy `lint_construction_terminology.py --fix` và bị `check_spoke_leakage.py` chặn với lỗi `PROPOSAL_PARSE_ERROR`.
   - Trên `pytest 8.3.5`, hook `pytest_cmdline_main` trong `conftest.py` chạy trước khi cờ `--version` được xử lý. Vì lệnh `[spoke_python, "-m", "pytest", "--version"]` không truyền đối số vị trí (`positional_args` rỗng), `conftest.py` chặn lệnh với `exit code 1`, khiến `SpokeSynchronizer._resolve_spoke_test_command` tưởng nhầm `.venv` của Spoke chưa cài `pytest` và fallback về `.venv` của Hub.

### Key Architectural Invariants & Learned Rules (`RULE-2.20`, `RULE-3.4`, `RULE-5.12`)
1. **Statechart Anti-Lie Pure-Python Verifier, Cycle-Safe BFS Liveness & 2-Tier Cross-Repo Contract (`PR #582`, `PR #583`)**:
   - Hàm `verify_statechart_anti_lie` (`scripts/governance/mermaid_syntax_linter.py`) cưỡng chế 4 bất biến Anti-Lie ($\le 20$ cạnh chuyển tiếp, hợp lệ cú pháp `stateDiagram-v2`, tính liên thông từng bước của `bug_path`, và đối chiếu các nút `class` với trạng thái lá).
   - Mọi thuật toán kiểm tra tính sống (`liveness`/`reachability`) trên máy trạng thái nghiệp vụ có vòng lặp bổ sung hồ sơ (`DeTrinh <-> YeuCauBoSung`) bắt buộc dùng **Cycle-Safe BFS (`visited: set[str]`)** (`find_reachable_states`, `has_path_bfs` trong `test_idop_schema_compatibility.py`) để bảo đảm mọi trạng thái trung gian đều có đường đi tới trạng thái kết thúc (`PheDuyet`, `TuChoi`) mà không bị treo vòng lặp.
   - Kiểm thử hợp đồng liên repo (Hub $\leftrightarrow$ Spoke) áp dụng mô hình **2-Tier Hybrid**: Tier 1 kiểm tra tĩnh trên Golden Snapshot (`tests/fixtures/idop_contract/core_lists_snapshot.json`, luôn chạy trên CI) kết hợp Tier 2 kiểm tra trực tiếp cây thư mục Spoke cục bộ (tự động `pytest.skip` khi vắng mặt trên CI).
2. **3-Surface Ubiquitous Language Sync, `CONTEXT.md` AST Grounding & Lossless `ImmutableSpanMasker.unmask` (`PR #584`, `PR #585`)**:
   - Chuẩn hóa thuật ngữ ngành xây dựng tuân thủ chuỗi ưu tiên 7 bậc (`Luật XD 2025 -> Nghị định -> QCVN -> TCVN -> 1812/QĐ-BXD -> Quy chế CCBA -> Hồ sơ Dự án`), đồng bộ trên cả 3 bề mặt (`CONTEXT.md`, `canonical_construction_taxonomy.yaml`, và `SKILL.md`).
   - Mọi định danh lớp/hàm Python viết trong backtick tại `CONTEXT.md` bắt buộc khớp 100% với tên định danh thực trong codebase (`ImmutableSpanMasker`, `FacetedDisambiguationEngine`) để vượt qua `test_doc_auto_evolution_engine_dry_run`.
   - `ImmutableSpanMasker.unmask()` chỉ được cắt đúng số lượng ký tự `\n` đệm (`padding_len = original.count("\n")`, trả về `original + match.group(2)[padding_len:]`), bảo toàn tuyệt đối các ký tự xuống dòng thuộc văn bản bao quanh và YAML frontmatter.
3. **Pytest 8.x `pytest_cmdline_main` Info-Flag Exemption & Direct Import Probe (`PR #585`)**:
   - Hook `pytest_cmdline_main` trong `conftest.py` bắt buộc miễn trừ tập cờ thông tin `{"--version", "-V", "--help", "-h", "--fixtures", "--markers"}` trước khi kiểm tra `positional_args`; đồng thời `SpokeSynchronizer._resolve_spoke_test_command` dùng `[spoke_python, "-c", "import pytest"]` để nhận diện chính xác `.venv` của Spoke khi chạy `sync_spoke.py --verify`.


---

## 50. Chuyển Dịch `mattpocock/skills` `v1.3.2` (`Zero Skill Bloat`), Mở Rộng `__path__` Cho Isolated Script Tests & Kiến Trúc Single-Source 5-Block Verification Harnesses (`PR #587`–`#590`)

### Context & Incident Root Cause (Phiên ngày 2026-11-01 đến 2026-11-03 — PR `#587` `fb84a076`, `#588` `0575c8a1`, `#589` `cd09c566`, `#590` `ae5c1b28`)
1. **Tiếp thu `mattpocock/skills` `v1.3.2` (`4ae2317`) không vượt trần 76 Hub Skills (`PR #587`)**:
   - Qua thẩm định phản biện 2 vòng với Grok (`Pass 1 Session: 6acfc77b-69f8-446a-8f2d-59b5e40ff5a3`, `Stage 3 Session: c8938996-3ee7-4309-9c61-25902f319059`, `risk_score: 1/10`), thay vì tạo thêm standalone skills làm vỡ trần `len(active_skill_names) == 76` của `test_skills_docs_integrity.py`, 3 kỹ năng mới có `GPI < 12.0` được chuyển dịch thành **Tier 2A Progressive References** (`ccba-implement/references/implement-spec.md`, `ccba-knowledge-loop/references/llm-wiki.md`, `ccba-grilling/references/to-questionnaire.md`) và 10 tệp kỹ năng/tham chiếu hiện hữu được nâng cấp tại chỗ (`COND-01` First-Unit Canary & Orchestrator Single-Writer, `COND-02` cô lập không gian tên `.md/knowledge/wiki/index.md`, `COND-03` token `<REDACTED>`, `COND-04` đăng ký chỉ mục Level 3).
2. **Hiện tượng Shadowing Không Gian Tên `tests.governance` Khi Chạy `run_isolated_tests.py --all --stress` (`PR #587`)**:
   - Khi chạy Cổng 0.2 TRIHT (`python scripts/eval/run_isolated_tests.py --all --stress`), mục tiêu `scripts` thực thi `pytest scripts/tests`. Vì `scripts/tests/__init__.py` tồn tại làm một regular package tên `tests`, trong khi thư mục gốc `./tests/` là một implicit namespace package (không có `./tests/__init__.py`), Python ưu tiên gắn tên module `tests` vào `scripts/tests` và che khuất hoàn toàn `./tests/governance/`, gây lỗi `ModuleNotFoundError: No module named 'tests.governance'` tại `scripts/tests/test_idop_schema_compatibility.py`.
3. **Nguy cơ Phình To Tệp Nhân Đôi (Dual-Tree Mirror Hazard) Trên Các Bộ Kiểm Định 5 Khối (`PR #589` & Thảo luận Chiến lược Grok `Session: 0a350328-e4e3-4a69-8da7-5ac5ea5dfdeb`)**:
   - Trong `PR #589`, việc đặt các kỹ năng `verify-ccba-*` (`scope: spoke`) tại `packages/ccba-harness/.agents/skills/verify-ccba-*/` giúp bảo toàn trần `76/76` Hub skills tại `.agents/skills/`, nhưng việc giữ bản sao kép của `harness/*.py` tại cả `packages/ccba-harness/.agents/skills/verify-ccba-*/harness/` lẫn `.agents/skills/ccba-*/harness/` làm tăng gấp đôi số lượng tệp Python cần bảo trì (`COND-02`).

### Key Architectural Invariants & Learned Rules (`RULE-2.21`)
1. **Cross-Directory Package `__path__` Extension in `scripts/tests/__init__.py` (`PR #587`)**:
   - Khi một thư mục kiểm thử con (`scripts/tests/__init__.py`) trùng tên định danh cấp cao (`tests`) với thư mục kiểm thử gốc (`./tests/`), bắt buộc mở rộng `__path__` ngay trong `scripts/tests/__init__.py` (`_ROOT_TESTS_DIR = str(Path(__file__).resolve().parents[2] / "tests"); if _ROOT_TESTS_DIR not in __path__: __path__.append(_ROOT_TESTS_DIR)`) để mọi câu lệnh `from tests.governance...` phân giải nhất quán cả khi chạy `pytest` toàn cục lẫn khi chạy cô lập `pytest scripts/tests`.
2. **Canonical Single-Source 5-Block Verification Skills (`COND-02`)**:
   - Toàn bộ các kỹ năng kiểm định 5 khối (`verify-ccba-harness`, `verify-ccba-xia`, `verify-ccba-wayfinder`, `verify-ccba-grilling`, `verify-ccba-implement`, `verify-ccba-knowledge-loop`, `verify-ccba-diagnosing-bugs`, `verify-ccba-tdd`, `verify-ccba-code-review`, `verify-ccba-create-pr`) đặt nguồn chuẩn duy nhất (Single Source of Truth) tại `packages/ccba-harness/.agents/skills/verify-ccba-<slug>/` (`SKILL.md`, `features/INDEX.md`, `harness/run_verify_<mod>.py`, `harness/test_<mod>_suite.py`), sử dụng `find_repo_root()` duyệt ngược `current.parents` tới `pyproject.toml`, tuyệt đối không nhân đôi tệp sang `.agents/skills/ccba-<slug>/harness/`.
3. **Historical LLM Wiki Namespace Isolation & Zero-Orphan Registration (`COND-03`)**:
   - Không gian tên Wiki lịch sử (`ccba-knowledge-loop/references/llm-wiki.md`) đặt tại `.md/knowledge/wiki/index.md` và `.md/knowledge/wiki/<topic-slug>.md`, tuân thủ nguyên tắc *"Write History, Not the Present"* (neo ngày `YYYY-MM-DD` và `ccba-agent-platform@<commit_sha>`), đồng thời bắt buộc đăng ký liên kết vào `.md/knowledge/index.md` và `.md/knowledge/log.md` để vượt qua `WikiHealthLinter.check_orphan_knowledge_files()`.

---

## 51. Tinh Khiết Luồng `stdio` MCP (`PYMUPDF_MESSAGE=fd:2`), Sandbox Giải Nén Archive / Bản Vẽ CAD (`.dwg`/`.dxf`) / Ảnh Nhúng `.xlsx` & Rút Gọn PDF Vector Bảo Toàn Byte-Stable (`RULE-5.13`)

### Context & Incident Root Cause (Phiên ngày 2026-11-04 đến 2026-11-05 trên Spoke `dgx-spark-toolkit` — `PR #160`, `PR #162`, `PR #163`, `PR #164`)
1. **Ô nhiễm luồng `sys.stdout` của `PyMuPDF` (`fitz`) trên MCP `stdio` và `--archive-worker` (`PR #164` — `1c2cf8f`)**:
   - Khi `hermes-gateway.service` khởi chạy `scripts/hermes_executive_mcp.py` bằng `.venv` của Hub (`<hub_path>/.venv/bin/python`), lệnh `from ccba_pdf_prep import ...` nạp `import fitz` (`PyMuPDF`), làm `fitz/__init__.py` gọi `message_warning(...)` và mặc định in dòng `warning: The 'fitz' API is deprecated and will be removed in future. Use 'import pymupdf' instead.` thẳng ra **`sys.stdout`**.
   - Dòng cảnh báo này vừa làm `mcp.client.stdio` báo lỗi `Failed to parse JSONRPC message from server` lúc khởi động, vừa chèn vào dòng đầu `stdout` của tiến trình con `--archive-worker` (trong `_extract_archive_cached`), khiến `json.loads` văng `JSONDecodeError` và báo `extractor_failed` trên môi trường production (dù chạy `pytest` trên `.venv` của Spoke vẫn pass vì `.venv` Spoke không cài `ccba_pdf_prep`).
2. **Rủi ro vượt trần bộ nhớ từ `openpyxl.load_workbook` và tọa độ neo `AnchorMarker` không trần trên tệp `.xlsx` (`PR #163` — `b13fae4`, Grok Sessions `a30ac4f5`, `996bdda8`, `58b8b160`)**:
   - Trong `openpyxl/reader/drawings.py:56`, hàm `load_workbook` gọi `Image(BytesIO(archive.read(dep.target)))` nạp toàn bộ các mục `xl/media/*` vào RAM ngay khi mở workbook, trước khi mã người dùng đọc `img.ref.read(MAX_DWG_PREVIEW_BYTES + 1)`.
   - Ngoài ra, `AnchorMarker.row` và `.col` trong `openpyxl` là số nguyên `0-based` không giới hạn đọc trực tiếp từ XML; nếu không kẹp trần chỉ số dòng/cột và chỉ duyệt các dòng hoạt động (`active_rows`), một tệp `.xlsx` có neo ở dòng/cột hàng triệu sẽ ép tiến trình cấp phát danh sách ô khổng lồ.
3. **Nhiễu ký tự SHX rời rạc trên PDF xuất từ bản vẽ CAD và Giải nén Archive / Đọc `.dwg` (`PR #162` — `b785268`, Grok Session `8dfa52d5`)**:
   - Các tệp PDF xuất từ AutoCAD (`AR.01.MB.TKO.pdf`) chứa hàng trăm dòng chỉ gồm 1–2 ký tự nét vẽ SHX (`"1"`, `"l"`, `"A"`), làm trôi ngữ cảnh trang đầu tiên; ngược lại, nếu áp bộ lọc khử trùng lặp lên PDF hành chính/pháp lý thông thường sẽ làm sai lệch bố cục văn bản gốc.

### Key Architectural Invariants & Learned Rules (`RULE-5.13`)
1. **MCP `stdio` & Worker Subprocess `stdout` Purity (`PYMUPDF_MESSAGE=fd:2`)**:
   - Mọi MCP Server giao tiếp qua `stdio` hoặc gọi tiến trình con trả kết quả JSON qua `stdout` bắt buộc đặt `os.environ.setdefault("PYMUPDF_MESSAGE", "fd:2")` ngay đầu module trước khi nạp `ccba_pdf_prep` / `fitz`, ép toàn bộ thông báo của `PyMuPDF` đi sang `stderr` (`fd:2`).
2. **Untrusted Archive, CAD (`.dwg`/`.dxf`) & `.xlsx` Media Defense-in-Depth (`COND-FFI`, `COND-XLSX-MEDIA-2MIB`, `COND-XLSX-ANCHOR-CLAMP`)**:
   - Giải nén `.rar`/`.zip`/`.7z` thực thi trong tiến trình con cô lập qua `ctypes` `libarchive.so.13` (khai báo đầy đủ `argtypes`/`restype` 64-bit `c_void_p`, `c_int64`, `c_ssize_t`), đọc `stdout` qua `select.select` + `os.read` có trần cứng và ngắt cả process group (`os.killpg`) ngay khi vượt ngưỡng; tính tổng dung lượng thư mục cache đệ quy (`os.walk(..., followlinks=False)` bao gồm `rendered_pages/`).
   - Trước khi gọi `openpyxl.load_workbook(path, data_only=True)`, hàm `_preflight_xlsx_zip` kiểm tra `zipfile.ZipFile.infolist()`: từ chối ngay nếu tổng số mục `> 400`, mục đơn lẻ `> 50 MiB`, tổng dung lượng `> 150 MiB`, hoặc bất kỳ mục `xl/media/*` nào có `file_size > 2 MiB`. Khi gắn ảnh PNG (khớp đủ 8 byte `SHARED_MAGIC_MAP[".png"]`), quy đổi tọa độ `0-based` sang `1-based` (`anc.row + 1`, `anc.col + 1`), kẹp trần `max(len(raw_rows), 10000)` × `max(actual_cols, 64)` (tính vào `skipped_total` nếu vượt trần), và chỉ duyệt tập dòng thực sự có dữ liệu hoặc neo hợp lệ (`active_rows`).
   - Với `.dwg`/`.dxf`: chỉ định tuyến `.dwg` qua `dwgread -v0 -O JSON` (`LibreDWG`), tuyệt đối không truy cập đường dẫn `[XREF]` trên host (`XREF Canary Isolation`), ép tổng chuỗi JSON đầu ra $\le 12,000$ ký tự, và chỉ chuyển mã `TCVN3 -> Unicode` (`_decode_tcvn3_if_needed`) khi chuỗi chưa chứa ký tự tiếng Việt Unicode dựng sẵn và có $\ge 2$ ký tự đặc trưng TCVN3.
3. **CAD-Exported Vector PDF Compaction & Zero-Auth Google Drive Folder Dispatch (`COND-PDF-IDENTITY`, `COND-FOLDER-DISPATCH`)**:
   - Hàm `_compact_pdf_page_if_cad(raw_page)` trả nguyên vẹn `(raw_page, False)` (100% byte-stable) cho mọi trang PDF có `< 40` dòng khác rỗng hoặc `< 50%` dòng 1–2 ký tự; chỉ các trang đạt ngưỡng CAD mới khử trùng lặp dòng $\ge 3$ ký tự theo thứ tự xuất hiện đầu tiên và gom tối đa 15 nhãn ngắn vào `[Nhãn ngắn/Trục]: ...`.
   - Trong `read_gdrive_file`, nhận diện link thư mục `/folders/<id>` trước `_extract_gdrive_file_id` và tải `embeddedfolderview` qua fetcher riêng (`follow_redirects=False`, kiểm tra chặt host `https://drive.google.com` mỗi hop, trần `512 KiB`, phân tích `flip-entry` bằng stdlib `HTMLParser` trong RAM, không ghi vào `gdrive_index.json`).


---

## 52. Thẩm Định Sức Khỏe Thượng Nguồn Mã Nguồn Mở (`OSS Vitality & Preflight Health Posture`), Chống Điểm Mù Nhánh `up-to-date` & Nhiễu Slash-Command Trên Đường Dẫn REST (`RULE-2.21`, `RULE-4.18`)

### Context & Incident Root Cause (Phiên ngày 2026-11-06 — Thẩm định `ccba-xia` v2.2.0 & `upstream_evaluator.py`, Grok Sessions `78d815b2` & `d9b05344`)
1. **Điểm mù nhánh `local_sha == remote_sha` đối với kho mã nguồn thượng nguồn bị bỏ rơi (`COND-01`, `COND-02`, `COND-05`)**:
   - Trong `scripts/spoke/upstream_evaluator.py`, một kho mã nguồn thượng nguồn bị ngừng bảo trì (ví dụ `claudekit-engineer`: `2,451` commits, commit cuối `2026-06-18`, tức `141` ngày không cập nhật tính tới `2026-11-06`) sẽ không phát sinh commit mới trên remote. Do đó, sau lần đồng bộ đầu tiên, `local_sha == remote_sha` luôn đúng và luồng thực thi luôn rẽ vào nhánh `else: ... is up-to-date`, không bao giờ gọi `evaluate_repo_diff()` hay `append_recommendation()`. Nếu đặt hàm đo sinh lực (`get_repo_vitality_metrics`) bên trong nhánh có diff, cảnh báo `STALE_UPSTREAM` trở thành mã chết đối với chính các repo đã ngừng hoạt động.
   - Đồng thời, với ngưỡng `180` ngày sẽ bỏ lọt `claudekit-engineer` (`141` ngày); ngược lại, nếu dùng ngưỡng số lượng commits cứng (`1,700–2,500` commits) làm cổng chặn sẽ loại nhầm các kho kỹ năng khai báo tinh gọn (`mattpocock-skills` chỉ có `553` commits nhưng vừa cập nhật `5` ngày trước) hoặc các repo dùng chiến lược `Squash and Merge` (`ccba-agent-platform` có `1,229` commits).
2. **Nhiễu nhánh phụ từ `pushed_at` của GitHub REST API và bẫy `git rev-list --count HEAD == 1` trên Shallow Clone (`COND-03`)**:
   - Trường `pushed_at` trả về từ `GET /repos/{owner}/{repo}` bị cập nhật mỗi khi có push vào bất kỳ nhánh phụ hoặc PR tự động nào (như Dependabot), không phản ánh nhịp độ phát triển trên nhánh mặc định (`default_branch`), và object repository cũng không chứa tổng số commits.
   - Khi chạy hạ cấp ngoại tuyến sau `git clone --depth 1`, lệnh `git rev-list --count HEAD` luôn trả về `1` bất kể lịch sử thực tế của dự án.
3. **Bẫy quét Slash Command (`UNREGISTERED_SLASH_COMMAND`) đối với đường dẫn REST API trong `SKILL.md` và `references/*.md`**:
   - Bộ kiểm định `validate_skills.py` (`test_zero_unregistered_slash_commands_in_skills_and_readme`) quét các chuỗi bắt đầu bằng dấu `/` (như `GET /repos/{owner}/{repo}` hoặc ``(`/commits`)``) trong thân `SKILL.md` và `references/*.md` và báo lỗi `UNREGISTERED_SLASH_COMMAND` vì `/repos` và `/commits` không phải lệnh slash đã đăng ký trong `catalog.yaml`.

### Key Architectural Invariants & Learned Rules (`RULE-2.21`, `RULE-4.18`)
1. **Unconditional Local Vitality Badge & Configurable `stale_upstream_days` (`scripts/spoke/upstream_evaluator.py`, `.md/knowledge/upstream_sources.yaml`)**:
   - Cấu hình `stale_upstream_days: 120` tại gốc `.md/knowledge/upstream_sources.yaml` (nạp qua `load_upstream_sources()` với fallback `DEFAULT_STALE_UPSTREAM_DAYS = 120`).
   - Hàm `get_repo_vitality_metrics(local_path, stale_days)` thực thi 3 lệnh `git` cục bộ (`git rev-parse --is-shallow-repository`, `git rev-list --count HEAD` khi `is_shallow=False`, và `git log -1 --format=%ct` kẹp `max(0, ...)` chống lệch đồng hồ tương lai), tính toán ngay đầu `check_and_evaluate_single()` và hiển thị huy hiệu `format_vitality_badge()` trên cả nhánh `up-to-date` (`local_sha == remote_sha`), chế độ `--fast` (`local_only=True`), nhánh hạ cấp mất mạng và trong mục đề xuất của `port_recommendations.md`.
2. **Two-Object GitHub API Preflight Health Check & Abandonware Challenge (`ccba-xia` v2.2.0)**:
   - Tại Bước 1 Pha 1 (Recon) của `ccba-xia/SKILL.md`, sử dụng 2 lệnh đơn đối tượng (`gh api repos/{owner}/{repo}` lấy `archived`, `default_branch`, `stargazers_count`, `pushed_at` và `gh api repos/{owner}/{repo}/commits/{default_branch}` lấy `commit.committer.date` làm `tip_commit_date`) để phân loại `health_posture` $\in$ `{FRESH, STALE, ARCHIVED, UNKNOWN}` (ưu tiên `ARCHIVED` cao nhất; khi ngoại tuyến trên bản clone `--depth 1`, chỉ dùng `git log -1 --format=%ct/%cI` và ghi `commit_count: "unknown (shallow clone)"`).
   - Khi `health_posture` là `STALE` hoặc `ARCHIVED`, Pha 4 (Challenge) bắt buộc kích hoạt câu hỏi phản biện *Abandonware / Maintenance Ownership* ở cả chế độ đầy đủ và chế độ `--fast` (`COND-R2`), bên cạnh 2 câu hỏi bất biến ADR-0057.
3. **Slash-Token Avoidance for REST Endpoints in Skill Markdown (`RULE-2.21`)**:
   - Trong mọi tệp `.agents/skills/*/SKILL.md` và `references/*.md`, tuyệt đối không viết đường dẫn REST API bắt đầu bằng dấu gạch chéo độc lập sau khoảng trắng hoặc dấu ngoặc (như `GET /repos/...` hay ``(`/commits`)``); bắt buộc viết theo cú pháp CLI không có `/` đầu (`gh api repos/{owner}/{repo}`) để không kích hoạt dương tính giả `UNREGISTERED_SLASH_COMMAND` trên `validate_skills.py`.

---

## 53. Làm Sâu Module Điều Phối QC (`QCAuditPipeline` Hybrid Variant 1+3), Rào Chắn Toàn Vẹn `__all__` Toàn Monorepo & Phân Rã AST $\le 50$ LOC (`RULE-1.10`, `RULE-2.20`)

### Context & Incident Root Cause (Phiên ngày 2026-11-06 — `/ccba-codebase-design`, Grok Sessions `f581b631` & `13eac630`)
1. **Nhân đôi điều phối Shallow Wrapper giữa `ccba-ai` và `ccba-qc-core` (`COND-DISCOVER-POLICY`, `COND-FAULT-POLICY`, `COND-LAZY-CTOR`)**:
   - `packages/ccba-ai/src/ccba_ai/pipeline.py` và `packages/ccba-qc-core/src/ccba_qc_core/pipeline.py` cùng định nghĩa lớp `QCAuditPipeline` với 112 dòng `run_audit` / `run_audit_sync` gần như giống hệt nhau, chỉ khác ở 3 chi tiết tinh tế: (a) `ccba_qc_core` truyền `extract_titleblocks=False, run_ai=False` vào `discover()` để tránh đốt tiền gọi Vision LLM 2 lần; (b) `ccba_qc_core` bắt `try/except Exception` kèm `logger.warning` trên từng stage (fault-tolerant batch); và (c) `ccba_qc_core` khởi tạo lười (lazy-init) `DiscoveryEngine`, `QuadViewAuditEngine`, `ReporterEngine` bên trong `run_audit`.
2. **Định danh treo (`Unbound`) và Trùng tên lớp trong `__all__` giữa các Package (`COND-SEAM-PRUNE`, `COND-HARNESS-EXPORT`)**:
   - `packages/ccba-harness/src/ccba_harness/__init__.py` khai báo `"load_eval_dataset"` trong `__all__` nhưng quên import từ `.evals`.
   - `packages/ccba-legal-intel/src/ccba_legal/__init__.py` khai báo `"format_all_qcvn_md_tables"` (thực tế nằm ở `mdconverter.tables`) và lặp 2 lần `"download_three_tier"`.
   - Cả `ccba_ai` và `mdconverter` đều xuất `"AuditFinding"` trong `__all__` với lược đồ Pydantic hoàn toàn khác nhau.
3. **Nợ kỹ thuật hàm $> 50$ LOC tại `mdconverter` và `check_dependency_contracts.py` (`RULE-2.20`)**:
   - Khi chạm vào `packages/mdconverter/src/mdconverter/academic.py`, `tables.py` và `scripts/governance/check_dependency_contracts.py`, cổng `peer-gate` (`check_ast_function_length`) chặn các hàm legacy vượt trần 50 dòng (`_check_module_import` 264 LOC, `audit_microstructure` 129 LOC, `export_paper_to_docx` 112 LOC, `extract_docx_tables` 109 LOC).

### Key Architectural Invariants & Learned Rules (`RULE-1.10`, `RULE-2.20`)
1. **Deep Seam Subclassing via 1-Line Hook Overrides over Intermediate ABCs (`Hybrid Variant 1+3`)**:
   - Thay vì tạo thêm lớp cơ sở trừu tượng trung gian (`BaseQCAuditPipeline`) làm phình bề mặt API, giữ `ccba_ai.pipeline.QCAuditPipeline` làm Deep Seam gốc (`_fault_tolerant: bool = False`, tách các stage helpers `_resolve_*_engine`, `_invoke_discovery`, `_run_discovery_stage`, `_run_audit_stage`, `_write_report` $\le 35$ LOC/hàm) và cho `ccba_qc_core.pipeline.QCAuditPipeline` kế thừa trực tiếp với `_fault_tolerant = True` + 4 hooks 1 dòng (`_invoke_discovery` khóa cứng `extract_titleblocks=False, run_ai=False`).
2. **Runtime `__all__` Binding & Cross-Package Symbol Disambiguation (`check_package_all_exports`)**:
   - Tích hợp `check_package_all_exports(packages_dir)` trực tiếp vào `scripts/governance/check_dependency_contracts.py` và `test_monorepo_package_all_exports_contract` (`packages/ccba-ai/tests/test_qc_pipeline.py`) để kiểm tra tự động cả 10 packages trong monorepo: đảm bảo `0` định danh treo (`hasattr(mod, sym)`) và `0` định danh trùng lặp trong `__all__`.
   - Đổi tên xuất khẩu trong `mdconverter.__all__` thành `"AcademicAuditFinding"` (giữ alias `AuditFinding = AcademicAuditFinding` ở cấp module để tương thích ngược).
3. **Filesystem Stem Sorting & AST $\le 50$ LOC Enforcement (`COND-SORT-PIN`, `RULE-2.20`)**:
   - Mọi truy vấn `rglob("*.pdf")` nạp bảng ánh xạ bản vẽ (`QCBatchOrchestrator.find_page_in_dir`) bắt buộc sắp xếp tất định `sorted(directory.rglob("*.pdf"), key=lambda p: (p.stem, str(p)))`.
   - Phân rã toàn bộ hàm vượt trần 50 LOC trong `academic.py`, `tables.py`, và `check_dependency_contracts.py` xuống $\le 45$ LOC/hàm.

---

## 54. Chuẩn Hóa Danh Xưng Pháp Nhân Theo `RULE-6.1`, Mẫu Thiết Kế `LEGACY_NATURAL_KEY_ALIASES` Fail-Closed Rebind, Kiến Trúc 4-Slice CCBA Unified Context Graph (`C-DRIFT-CONTRACT` v1.1) & Tiến Hóa `ccba-session-retrospective` v1.6.2 (`RULE-6.1`, `RULE-6.2`)

### Context & Incident Root Cause (Phiên ngày 2026-11-08 — Hub `PR #665`, `PR #671`; Legal `PR #50`–`#53`; Spark `PR #177`–`#182`; IDOP `PR #112`–`#113`, `#117`, `#120`; VvC_Notes `PR #105`–`#107`)
1. **Lỗi Lặp Từ Loại Danh Xưng Pháp Nhân & Nguy Cơ Đè Khóa Tự Nhiên SharePoint List (`RULE-6.1` — Hub `PR #671`, Legal `PR #52`–`#53`, Spark `PR #182`, IDOP `PR #117` & `#120`, VvC_Notes `PR #107`)**:
   - Chữ `I` trong `IBST` (`Institute`) đã mang nghĩa `"Viện"` và chữ `C` đầu trong `CCBA` (`Center`) đã mang nghĩa `"Trung tâm"`; việc ghép `"Viện IBST"`, `"Viện (IBST)"`, `"Viện trưởng IBST"`, `"Trung tâm CCBA"`, `"Viện/IBST"`, `"CCBA/TT BIM"` gây dư thừa ngữ nghĩa trên 5 repositories.
   - Trên SharePoint List (`IDOP-CCBA-WAY`), theo biên bản thẩm định đối kháng của Grok 4.7 (`req-20261107-plan-ibst-nomenclature-rule61-001`, 7 điều kiện `COND-ALIAS-EXACT`, `COND-FK-LOOKUP`, `COND-LIST-AND-PAYLOAD`, `COND-RULE4-CONTRACT`, `COND-SCOPE-LIVE-PATCH`, `COND-HISTORY`, `COND-VERIFY`), khi chuỗi hiển thị bị đổi theo `RULE-6.1` đồng thời là trường khóa tự nhiên (`key_field`) trên 6 danh sách (`Submissions`, `ApprovalNodes`, `ProjectMembers`, `EmployeeHistory`, `ApprovalDelegations`, `ApprovalWorkflows`), nếu dùng khớp tiền tố trần (`"[Gate 1]"`) để cập nhật sẽ có nguy cơ `PATCH` đè vào hồ sơ đấu thầu đang sống (`[Gate 1] Đăng ký đầu mối & Tham gia đấu thầu - {bidding_code}` do `bidding_package_creator.py` tạo), hoặc làm đứt gãy tra cứu khóa ngoại liên hoàn giữa Bước 5 $\to$ Bước 6 $\to$ Bước 7.
2. **Đứt Gãy Truy Vết Giữa Đồ Thị Pháp Lý 5-Ring, Quy Chế Nội Bộ Và Vận Hành EOS L10 (`RULE-6.2` — Hub `PR #665`, Legal `PR #50`–`#51`, Spark `PR #177`–`#181`, IDOP `PR #112`–`#113`, VvC_Notes `PR #105`–`#106`)**:
   - Các điều khoản trong `QCTK 2815` và `QCCTNB 3209` viện dẫn thông tư cũ (`11/2021/TT-BXD`, `13/2021/TT-BXD`, `09/2025/TT-BXD`) đã bị thay thế từ `01/07/2026` bởi `NĐ 206/2026/NĐ-CP` và `TT 36, 37/2026/TT-BXD`, đòi hỏi hợp đồng giao tiếp `C-DRIFT-CONTRACT` v1.1 để cảnh báo tự động mà không tự ý sửa ngầm văn bản nội bộ.
   - Trên dữ liệu vận hành thực tế (`etl_staging.db` & `m365_bridge.db`), phép nối `1:N` giữa hợp đồng và đơn vị phối hợp nếu không nhân trọng số `allocation_share` sẽ gây nhân bản fan-out `331,71 tỷ VNĐ` trên tổng `495.127.049.993 VNĐ`; các hóa đơn DLQ mơ hồ (`AMBIGUOUS` hoặc `confidence < 0.95`) nếu khấu trừ nhầm vào `Ghost WIP` sẽ làm lệch xếp hạng Pareto L10; và `SearchPipeline` nếu không cô lập khóa Redis semantic cache theo `ctx.corpus` hoặc chỉ kiểm tra `max(mtimes)` đơn lẻ sẽ làm rò rỉ kết quả chéo corpus và mù thay đổi khi hot-reload nhiều file cache JSON/NPZ.
3. **Điểm Mù Tham Số `--profile` Trong Bước 4 Của `ccba-session-retrospective/SKILL.md`**:
   - Bước 4 của `.agents/skills/ccba-session-retrospective/SKILL.md` (`v1.6.0`/`v1.6.1`) chỉ hướng dẫn `python scripts/governance/compact_session_learnings.py --check` mà không phân nhánh `--profile hub` vs `--profile spoke`, khiến khi chạy tại Spoke mà không truyền `--profile spoke` sẽ kiểm tra nhầm `HUB_REQUIRED_INVARIANTS` thay vì `SPOKE_REQUIRED_INVARIANTS`.

### Key Architectural Invariants & Learned Rules (`RULE-6.1`, `RULE-6.2`)
1. **Chuẩn Hóa Danh Xưng Pháp Nhân Theo `RULE-6.1` & Mẫu Thiết Kế `LEGACY_NATURAL_KEY_ALIASES` Fail-Closed Rebind (`RULE-6.1`)**:
   - Loại bỏ triệt để lỗi lặp từ ngữ nghĩa (`"Viện IBST"`, `"Viện (IBST)"`, `"Viện trưởng IBST"`, `"Trung tâm CCBA"`, `"Viện/IBST"`, `"CCBA/TT BIM"`), chuẩn hóa thành `"Viện"`, `"IBST"`, `"Viện KHCN Xây dựng (IBST)"`, `"đơn vị thành viên thuộc IBST"` (Quy tắc 4), `"14 Viện/Trung tâm chuyên ngành thuộc IBST"`, `"CCBA"`, `"Trung tâm"`, hoặc `"IBST - CCBA"`.
   - Khi đổi chuỗi hiển thị đồng thời là trường khóa tự nhiên (`key_field`) trên SharePoint List (`Submissions`, `ApprovalNodes`, `ProjectMembers`, `EmployeeHistory`, `ApprovalDelegations`, `ApprovalWorkflows`), tuyệt đối không dùng khớp tiền tố trần (`"[Gate 1]"`), mà dùng bảng ánh xạ nguyên văn `(list_name, key_field, legacy_exact_string)`, kiểm tra fail-closed khi cả khóa cũ và khóa mới cùng tồn tại, và gọi `existing_map.pop(legacy_key, None)` kèm rebind `existing_map[new_key] = item_id` ở mọi bước tra cứu khóa ngoại liên hoàn (Bước 5 $\to$ Bước 6 $\to$ Bước 7).
2. **Kiến Trúc 4-Slice CCBA Unified Context Graph, `C-DRIFT-CONTRACT` v1.1, 3 Rào Chắn Dữ Liệu Đối Kháng & Semantic Cache Isolation (`RULE-6.2`)**:
   - **Interface Contract 1 v1.1 (`C-DRIFT-CONTRACT`)**: Producer (`index_idop_kb.py`) xuất đầy đủ `contract_version: "1.1"`, `clause_id`, `drift_status`, `superseded_statutes[]`, `replacement_statutes[]` (tách riêng khỏi `guided_by[]`), `impacted_metrics[]`, `authority_signoff_role`, `source_path`, `content_hash` trên đủ 4 văn bản `.md/governance_constitution/` mà không tự sửa ngầm quy chế nội bộ. Consumer (`load_governance_drift_report_items`) kiểm tra `is_contract_valid` và từ chối phát hành thẻ `PROPOSE_GOVERNANCE_AMENDMENT` khi thiếu `impacted_metrics` hoặc `authority_signoff_role`.
   - **3 Rào chắn Dữ liệu Đối kháng**: (1) Áp trọng số `allocation_share` + guard `OVER_ALLOCATED_SHARE` bảo toàn chính xác `495.127.049.993 VNĐ` chống nhân bản fan-out `331,71 tỷ VNĐ`; (2) Tách bạch `Ghost WIP` (chỉ khấu trừ khi `confidence >= 0.95` và không chứa `AMBIGUOUS`) khỏi `Real WIP` theo Gate, xếp hạng Pareto L10 theo `real_wip_vnd` trên toàn bộ `ContractScope` (`#S1..#Sn`); (3) Tính `Metric #7` theo cửa sổ tuần ISO `iso_week_bounds_ict(period_key)` và khóa phân công Chủ trì khi có bất kỳ chứng chỉ hành nghề `EXPIRED` hoặc lỗi ngày hiệu lực.
   - **Semantic Cache Isolation & Multi-Asset Hot-Reload**: Cô lập khóa Redis semantic cache theo `ctx.corpus` trong `SearchPipeline`, bảo toàn các trường đồ thị 1-hop (`hop`, `graph_neighbors`, `via_source`, `edge_type`, `tags`), và theo dõi vector trạng thái `tuple[(path, mtime), ...]` thay cho `max(mtimes)` đơn lẻ.
3. **Phân Nhánh Tường Minh `--profile hub` vs `--profile spoke` Trong `ccba-session-retrospective` v1.6.2**:
   - Nâng cấp `.agents/skills/ccba-session-retrospective/SKILL.md` (`v1.6.2`) tại Bước 4 để chỉ định rõ `--profile hub --file .md/knowledge/session_learnings.md --check` trên Hub và `--profile spoke --file .md/knowledge/session_learnings.md --check` trên Spoke, đồng bộ đồng nhất trên toàn bộ 5 repositories.

---

## 55. Nâng Cấp Cơ Chế Phối Hợp Antigravity ↔ Grok: Khôi Phục Phiên 3 Tầng (`Dual-Clock delta_sec`), Chống Phình Payload Lượt Tiếp Nối, Khử Trùng Lặp Telemetry & Ép Kiểu Dung Sai Frontmatter Lịch Sử (`RULE-4.19`, `PR #682`, `PR #684`)

### Context & Incident Root Cause (Phiên ngày 2026-11-08 — Khảo sát Conversation `a46ad8bf` & Benchmark Lịch Sử, Grok Sessions `4a15bc86` & `f2818874`)
1. **Đứt Gãy Phiên Đa Lượt (`Stateless Multi-Turn Amnesia`) & San Phẳng `st_mtime` Khi `git checkout`**:
   - Trên Spoke `VvC_Notes` (Conversation `a46ad8bf`, `14c43933`, `caebea97`), chỉ `4/17` prompts truyền tường minh `resume_session_id`; các lượt vòng 2 (`_v2`, `_round2`, `_reverify`, `_signoff`) quên truyền `resume_session_id` dẫn tới tạo phiên mới và bơm lại toàn bộ thân tài liệu (`468–577` dòng), làm tốn gấp đôi token.
   - Đồng thời, mọi `PROFILE_SPECS` đều mặc định `fork_session: True`, khiến ngay cả khi truyền `resume_session_id` thì Grok vẫn phân nhánh sang `session_id` mới qua mỗi lượt.
   - Trên kho Git của Hub (`.md/peer_exchange/`), `git checkout` gán cùng một `st_mtime` cho hàng trăm tệp lịch sử; nếu bộ tự động dò tìm phiên (`_auto_discover_resume_session_id`) chỉ sắp xếp theo `st_mtime` thì thứ tự thời gian bị suy biến thành thứ tự bảng chữ cái và rò rỉ cả các verdict tương lai (độ chính xác Top-1 ban đầu chỉ đạt `28.6%` = `6/21`), hoặc nếu trộn lẫn `p_iso` (ISO timestamp trong frontmatter) với `mt` (`st_mtime` trên đĩa khi verdict thiếu timestamp) sẽ gây lệch hàng giờ đồng hồ thực trong unit tests.
2. **Nhân Đôi Chi Phí Telemetry Khi Chạy Lại Lượt Phản Biện & Rơi Rớt Prompt Sai Lệch Lược Đồ Frontmatter**:
   - Trong `status.json` của `VvC_Notes`, việc ghi nhiều tệp verdict cùng tham chiếu một snapshot `(session_id, turn_count, total_tokens, cost_usd)` khiến `gemini-3.8-flash-high` bị cộng đúp (`16 calls / $0.6687` thay vì `15 calls / $0.6237`).
   - Trên `153` mẫu prompt lịch sử trong `transcript_full.jsonl` và `17` mẫu tại `VvC_Notes`, các biến thể viết tay như `request_type: "architecture_review"` / `"verification"`, `from`/`to` hoặc `sender`/`recipient`, `source_documents: [{"path": "...", "role": "..."}]`, `profile: "code_audit"` / `"discuss"`, hoặc thiếu `output_path` khiến `parse_envelope_from_md()` trả về `None` âm thầm (`5/17` mẫu Spoke bị `peer-watch` bỏ sót).
3. **Bẫy Shell Redirect `> grok_*.md` Nuốt Mặt Nạ Lỗi & Nhân Đôi Bản Sao Giữa Brain Artifact Và `.md/peer_exchange/`**:
   - Agent gọi `grok -p ... > grok_review_*.md` trực tiếp qua bash khiến khi CLI thất bại sớm, tệp đích vẫn được tạo rỗng và che giấu mã lỗi thật; hoặc viết song song 2 bản `implementation_plan.md` ở cả `<appDataDir>/brain/<id>/` và `.md/peer_exchange/`.

### Key Architectural Invariants & Learned Rules (`RULE-4.19`)
1. **3-Tier Auto-Resume Session Discovery Với Đồng Hồ Kép (`Dual-Clock delta_sec`) & Gọt Tiền Tố Giai Đoạn (`_STAGE_PREFIX_RE`)**:
   - Khi `resume_session_id` không truyền tường minh (trừ khi opt-out bằng `"new"` / `"none"` / `"false"`), `_auto_discover_resume_session_id()` trong `packages/ccba-harness/src/ccba_harness/_peer_telemetry.py` tự động dò tìm `session_id` gần nhất trong cùng thư mục theo 3 tầng:
     * **Tier 1 (Normalized Thread Stem Match)**: Khớp gốc `request_id` hoặc tên tệp sau khi gọt tiền tố vai trò (`_PREFIX_ROLE_RE`), ngày `^\d{8}[-_]+`, tiền tố giai đoạn (`_STAGE_PREFIX_RE`: `discuss_`, `review_plan_`, `signoff_`, `final_signoff_`, `final_acceptance_`) và hậu tố vòng (`_ROUND_SUFFIX_RE`: `-v2`, `-r2`, `-round2`, `-pass2`, `-reverify`, `-signoff`, `-fix`).
     * **Tier 2 (Target/Source Document Overlap)**: Khớp tập tài liệu đích (`_extract_clean_doc_set` loại bỏ `.md/peer_exchange/*`, độ trùng lặp Jaccard $\ge 0.5$).
     * **Tier 3 (Continuous Discussion Thread)**: Khớp phiên thảo luận `request_type in ("discuss", "architecture")` trong cửa sổ `14,400s` (`4h`).
   - **Đồng hồ kép (`Dual-Clock delta_sec`)**: Tính `delta_sec = (p_iso - v_iso)` khi cả prompt hiện tại và verdict ứng viên (hoặc prompt gốc của nó) đều có ISO-8601 timestamp hợp lệ (`_parse_iso_ts`), và tự động chuyển sang `delta_sec = (p_mtime - mt)` khi một trong hai thiếu ISO timestamp; lọc `delta_sec >= -60.0` và sắp xếp theo `(round(delta_sec, 4), -round(mt, 4), v_name)` — đạt **`100.0%` (`21/21` trên Hub, `4/4` trên Spoke)** độ chính xác Top-1 Session Match.
   - Khi có `resume_session_id` (tường minh hoặc tự động khám phá) và người dùng không truyền `--fork-session`, tự động đặt `fork_session = False` để giữ liên tục 1 `session_id` xuyên suốt các vòng.
2. **Cảnh Báo Phình Payload Lượt Tiếp Nối (`_check_resumed_payload_bloat`) & Khử Trùng Lặp Snapshot Telemetry**:
   - Nếu lượt chạy có `resume_session_id` nhưng tệp prompt vẫn vượt `400` dòng hoặc `20,480` bytes (`20 KB`), phát cảnh báo `[WARN-RESUMED-PAYLOAD-BLOAT]` ra `stderr` nhắc chỉ gửi bảng đối chiếu điều kiện + git diff.
   - Trong `_accumulate_verdict_telemetry()` (`update_status_json`), khử trùng lặp theo khóa快照 `(session_id, turn_count, total_tokens, round(cost_usd, 4))` trong `seen_snapshots`, ngăn chặn cộng đúp chi phí khi ghi đè/tái xuất tệp verdict cùng lượt.
3. **Ép Kiểu Dung Sai Frontmatter Lịch Sử (`_normalize_envelope_frontmatter`), Cờ CLI `-o`/`--output-file` & Quy Tắc Cross-Surface SSoT**:
   - Chuẩn hóa dung sai trong `_peer_models.py`: ánh xạ `from`/`sender` $\to$ `from_agent`, `to`/`recipient` $\to$ `to_agent`, `context_files` $\to$ `source_documents`, `output_file` $\to$ `output_path`; ép kiểu danh sách dict `[{"path": "..."}]` qua `_coerce_doc_list()`; ánh xạ `_REQUEST_TYPE_ALIASES` (`architecture_review` $\to$ `review`, `verification` $\to$ `verify`, `consultation` $\to$ `consult`, `signoff` $\to$ `review`) và `_PROFILE_ALIASES` (`code_audit` $\to$ `code_review`, `discuss` $\to$ `audit_plan`); tự động suy diễn `output_path` từ tên tệp `prompt_<stem>.md` $\to$ `grok_<stem>.md` — nâng tỷ lệ nhận diện frontmatter lịch sử lên **`100.0%` (`153/153`)** và bổ sung `diagnose_envelope_parse_error()` báo lỗi dòng/trường cụ thể.
   - Bổ sung cờ `-o` / `--output-file` cho `ccba-harness peer-dispatch` và ghi nhận vào `docs/rules/execution_coordination_guardrails.md` (Mục `19.7` & `19.8`): cấm dùng shell redirect `> grok_*.md`, bắt buộc mọi prompt $> 60$ dòng hoặc đa lượt đi qua `peer-dispatch`, và giữ 1 bản SSoT duy nhất giữa `<appDataDir>/brain/<id>/` và `.md/peer_exchange/`.

---

## 56. Chuẩn Hóa Cổng Thông Tin 3 Tầng ("Tối Giản & Hé Lộ Dần" — `ccba-design` v2.5.0, `ccba-sharepoint-iac` v1.2.0, `UX-18..23`, `STK-07..08`, `SLOP-06..09`), Khử Quy Mô Tĩnh Theo `Dynamic Scale Invariant` & Tách Đường Dẫn Brain Mirror (`PR #677`–`#681`, `#683`, `#685`, `#687`–`#689`, `#693`, `#694`, IDOP `PR #121`, `#124`)

### Context & Incident Root Cause (Phiên ngày 2026-11-08 & 2026-11-09 — Hub `PR #677`–`#681`, `#683`, `#685`, `#687`–`#689`, `#693`, `#694`; Spoke `IDOP-CCBA-WAY` `PR #121`, `#124`; Grok Session `847cafd8`)
1. **Ma Sát Thị Giác, Điểm Mù Kiểm Toán Tĩnh & Ánh Xạ M365 Bản Địa Trên Cổng Thông Tin Kỹ Thuật (`skills_portal.html`, `IDOP-Cockpit.html`, `list-formatting/*.json`)**:
   - Trên `#map` của CCBA Skills Portal, khối `.jump-grid` và `.inline-advisor-banner` bị bó hẹp ở `760px` trong khi các `.goal-section` bên dưới rộng `1120px`/`1440px`, để trống một ô 50% ở hàng cuối khi có 5 thẻ lẻ; tỷ lệ cột `.spine-row` quá hẹp làm chật thẻ kỹ năng bên phải; và quy tắc `overflow-wrap: anywhere` áp tràn lan lên `.btn` khiến nút ngắn `📋 Copy` bị gãy làm 2 dòng.
   - Thanh Sidebar trái (`.app-sidebar`) xếp các liên kết tài liệu tĩnh ít dùng (`Guides`) lên trên nhóm `Topics` dùng hàng ngày, thiếu huy hiệu đếm `.sidebar-count-pill`, hiển thị tràn 8+ tài liệu phụ không thu gọn, và hàm `jumpToTopic()` luôn ép người dùng thoát khỏi chế độ `#skills` quay về `#map`.
   - Trình đọc Markdown trong `#skillModal` (`renderSafeMarkdown()`) chưa dựng được bảng pipe GFM (`.md-table`), gộp các dòng `>` liên tiếp kèm nhãn cảnh báo GitHub (`[!NOTE]`, `[!IMPORTANT]`...), hoặc gắn neo `id="md-anchor-<slug>"` cho tiêu đề `# / ## / ###` và định tuyến sâu `#doc/<path>` có kiểm tra whitelist.
   - Quy tắc quét tĩnh `SLOP-06` cũ chỉ kiểm tra chuỗi `"tabular-nums"` xuất hiện 1 lần trên toàn tệp, dẫn tới bỏ sót các bảng `<table class="ids-table">` thiếu `tabular-nums` khi trong tệp có huy hiệu khác mang class `.tabular-nums`;同时 Hub chưa có ánh xạ 3 tầng bản địa cho hệ sinh thái Microsoft 365 (`pnp/List-Formatting`, `AdaptiveCards`, Power Apps `.pa.yaml` & Code Apps, Power Automate `OpenApiConnection`).
2. **Vi Phạm `Dynamic Scale Invariant` & `Machine-State Decoupling` (`ADR-0061`) Giữa Hub Và Spoke**:
   - Tài liệu kỹ năng và SOP/Governance trên Hub gắn cứng các con số quy mô tại một thời điểm (`"58 SharePoint Lists"` ở `project_delivery_spoke_setup.md` / `ADR-0042` vs `"59 SharePoint Lists"` ở `stacks.csv` / `ADR-0060`, trong khi thực tế Spoke `IDOP-CCBA-WAY` ở `Slice P7.15` đã tiến hóa lên `62` Lists; cùng các số tĩnh `"15 ROLE_IDs"`, `"16 Entra ID Groups"`, `"2B/5B/10B"`, `"2026-W43"`, `"2TB/5TB"`). Ngoài ra, phép quét `grep` phân biệt hoa-thường bỏ sót các vị trí viết thường `lists` (`58/59 SharePoint lists`).
   - Tại Spoke `IDOP-CCBA-WAY`, `tools/build_prototype_html.py` và `tests/test_sharepoint_html_cockpit_prototype.py` gắn cứng đường dẫn máy cá nhân và UUID phiên chat `/home/vvc/.gemini/antigravity/brain/b598fb7e-4602-41e1-bb99-7b1b27070066/IDOP-Cockpit-Prototype.html`, đồng thời có nguy cơ xung đột cây thư mục làm việc (`Working Tree / Merge Race`) nếu chỉnh sửa trực tiếp khi phiên `b598fb7e` đang giữ khóa thực thi `Slice P7.15b`.

### Key Architectural Invariants & Learned Rules (`RULE-1.13`, `RULE-2.20`, `RULE-4.18`)
1. **Kiến Trúc Cổng Thông Tin 3 Tầng, Ánh Xạ Bản Địa M365/PowerPlatform & Bộ Quét Anti-Slop (`ccba-design` `v2.5.0` & `ccba-sharepoint-iac` `v1.2.0` — `STK-07..08`, `UX-18..23`, `SLOP-06..09`)**:
   - **3-Tier Progression of Attention ("Tối giản & Hé lộ dần" — `UX-18`, `UX-19`, `STK-07`)**:
     * **Tier 1 (`< 650px` Fold Budget)**: Tối đa 3 Zero-Noise Action Pills + Role-Adaptive Lenses + Slide-over Proximity Drawer; đồng bộ `100%` chiều rộng `--ccba-content-max` (`1440px`) và trải dài thẻ lẻ cuối hàng (`.jump-card:last-child:nth-child(odd) { grid-column: 1 / -1; }`).
     * **Tier 2 (Asymmetric Workflow Spine & Button Wrapping)**: Tỷ lệ cột bất đối xứng `minmax(260px, 0.55fr) minmax(0, 1.45fr)` (`gap: 2rem`), đánh số tuần tự `STEP 01..0N`, 1-Click Mode Toggle (Daily vs. L10 90-Minute Mode); phân biệt nút ngắn inline (`white-space: nowrap`) với nút lệnh/đường dẫn dài (`white-space: normal; overflow-wrap: anywhere`).
     * **Tier 3 (Lifecycle Stepper & Progressive Drawers)**: Thanh Project Lifecycle Stepper Bar, biểu đồ Mermaid/Babylon.js lazy-rendered, và ngăn kéo `<details>` thu gọn danh sách phụ `>4` mục (`.sidebar-guides-more`, `.goal-guides-drawer`).
   - **280px App Shell Sidebar & Context-Aware Routing (`UX-20`)**: Sắp xếp nhóm theo tần suất vận hành (`Explore -> Topics -> What's New -> Guides`), huy hiệu `.sidebar-count-pill` (`tabular-nums`), và định tuyến `jumpToTopic()` theo ngữ cảnh (cuộn tới `#goal-<id>` trên `#map` hoặc lọc chip tại chỗ trên `#skills` kèm đồng bộ `syncSidebarTopicsActive()`).
   - **5-Section Detail Modal, Safe Markdown Reader & `SLOP-06`/`SLOP-08` (`UX-21`, `UX-22`)**: Cấu trúc Modal 5 phần; khử XSS qua `escapeHtml(rawStr)` + `resolveAndSanitizeHref(rawHref, basePath)` + `slugifyMdHeading(rawHeading)` (`id="md-anchor-<slug>"`) + `scrollToMdAnchor(anchorId)` + whitelist `#skill/<slug>` & `#doc/<path>` (`findKnownDocGuide`); `SLOP-06` kiểm tra từng thẻ mở `<table\b[^>]*>` (trừ khi có CSS toàn cục `table { font-variant-numeric: tabular-nums; }`); `SLOP-08` bắt mọi `href` / JSX / `setAttribute` / `.href =` chứa `javascript:` / `data:` / `vbscript:` hoặc `.innerHTML = marked(...)`.
   - **Ánh Xạ 3 Tầng Bản Địa M365, Power Apps & Power Automate (`UX-23`, `STK-08`, `SLOP-09`, `ccba-sharepoint-iac` `v1.2.0`)**:
     * **SharePoint List/View/Form JSON (`pnp/List-Formatting`)**: Dùng `commandBarProps` ẩn nút hệ thống gây nhiễu ở Tier 1, `customCardProps` (`openOnEvent: hover`) làm Proximity Hover Card ở Tier 3, `customRowAction: executeFlow` kích hoạt Power Automate, và viền ngữ nghĩa `1px` thay vì `border-left: 5px`.
     * **Power Apps (`.pa.yaml` & Code Apps) & Power Automate**: Tách bố cục 3 tầng (`conHeaderBar` $\to$ `galMainQueue` + `conInspectorSpine` $\to$ `conDrawerOverlay`), tuân thủ **SharePoint Delegation Guardrail** (cấm `Search()`, `Lower()`, `In` trong `Filter()`), phân vai workload bảo vệ hạn ngạch 40,000 PPR/24h (nhường ETL/kiểm toán hàng loạt cho Python App-Only Graph API), và chặn liên kết chia sẻ tạm thời (`/:f:/g/`, `/:b:/g/`) cùng `ApiConnection`/`Invoker` cũ qua `SLOP-09`.
     * **Upstream Radar Routing (`ADR-0057`)**: Đăng ký `impeccable`, `web-quality-skills` ($\to$ `ccba-design`) và `power-platform-skills`, `pnp-list-formatting` ($\to$ `ccba-sharepoint-iac`) trong `upstream_sources.yaml` + `UPSTREAM_ALIAS_MAP`, bảo toàn trần 76 Active Skills.
2. **Cưỡng Chế `Dynamic Scale Invariant` Qua Quét Không Phân Biệt Hoa-Thường (`grep -rni`) & Cô Lập `CCBA_BRAIN_MIRROR_DIR` (`ADR-0061`)**:
   - Cấm gắn cứng con số quy mô tại một thời điểm (`58/59 SharePoint Lists`, `15 ROLE_IDs`, `16 Entra ID Groups`, `2B/5B/10B`, `2026-W43`, `2TB/5TB`) trong kỹ năng Hub (`stacks.csv`, `ux-guidelines.csv`, `SKILL.md`) và tài liệu vận hành (`SOP`, `Governance`, `Team Sheets`); luôn dùng công thức động (`all provisioned SharePoint Lists`, `federated ROLE_IDs`, `Master OneDrive Storage`) và kiểm tra bằng `grep -rni` để bắt cả biến thể viết thường (`lists` vs `Lists`).
   - Cấm hardcode đường dẫn `/home/vvc/.gemini/antigravity/brain/<uuid>/...` trong script/test của Spoke; tách qua biến môi trường tùy chọn `os.environ.get("CCBA_BRAIN_MIRROR_DIR")`. Khi phát hiện một phiên đồng đẳng đang giữ khóa thực thi trên Spoke (qua `transcript.jsonl` / `implementation_plan.md`), dừng mọi thao tác ghi/checkout trên Spoke đó và xuất **Handoff Prompt** để gộp thay đổi an toàn vào nhánh hiện hành của phiên kia.



---

## 57. Nâng Cấp Cặp Kỹ Năng `/ccba-build-skill` (`v1.1.1`) & `/ccba-skill-repair` (`v1.1.0`), Rào Chắn Chống Ghi Đè Mất `RULE` Trong `compact_session_learnings.py` & Cô Lập Worktree Khi Phát Hành Song Song (`PR #702`, `#703`)

### Context & Incident Root Cause (Phiên ngày 2026-11-11 — Hub `PR #702`, `PR #703`; Grok Session `19e6f8a3`)
1. **Rò Rỉ Hợp Đồng GPI JSON, Điểm Mù Quét Văn Xuôi & Lệch Nguồn Thật Hub/Spoke Giữa Cặp Kỹ Năng Tác Tạo – Bảo Trì**:
   - Tài liệu hướng dẫn cũ giả định CLI `evaluate-gpi --json` xuất chuỗi rút gọn `"tier-2b"` hoặc `"PASS_STANDALONE"`, trong khi mã nguồn thực tế (`packages/ccba-harness/src/ccba_harness/gpi.py`) xuất chuỗi đầy đủ `ArchitectureTier.value` (`"Tier 1: Package Function / Deep Seam"`, `"Tier 2A: Reference Doc inside Existing Skill"`, `"Tier 2B: Standalone Kernel Skill"`, `"Tier 3: Autonomous Workflow Skill"`), cờ boolean `allow_standalone_skill`, và trường lồng `breakdown.preserved_by_hysteresis`; đồng thời `evaluate_skill_file()` âm thầm bỏ qua các cờ `--s/--k/--a/--p` nếu frontmatter đã có sẵn đủ 4 khóa `gpi_*`.
   - Bộ kiểm định `audit_skills_hygiene.py` (`RE_DEAD_WOOD`, `RE_BASHISMS`, `RE_START_PROCESS`) quét toàn bộ nội dung `SKILL.md` kể cả văn xuôi cảnh báo (không chỉ code block), khiến việc trích dẫn nguyên văn cụm từ cấm trong quy tắc dễ tự gây lỗi `FAIL`.
2. **Ghi Đè Mất Bất Biến Hoạt Động Khi Chạy `compact_session_learnings.py --compact` & Đứt Liên Kết Tương Đối Trong Bản Sao Lưu**:
   - Khi gọi `compact_session_learnings.py --compact` để nén `session_learnings.md` xuống dưới trần `10.0 KB`, hàm `run_compact()` ghi đè thẳng hằng số tĩnh `COMPACTED_WORKING_MEMORY_TEMPLATE` (được viết từ thời điểm `ADR-0057`) lên tệp đích sau khi sao lưu, làm mất các mục `RULE-1.10..1.26`, `RULE-2.5..2.21`, `RULE-3.4..3.5`, `RULE-4.8..4.19`, `RULE-5.8..5.13` và toàn bộ `Miền 6` (`RULE-6.1..6.2`).
   - Đồng thời, `backup_to_archive()` chép nguyên văn liên kết tương đối `(archive/session_learnings_history.md)` và `(wiki/index.md)` từ `.md/knowledge/` sang `.md/knowledge/archive/`, làm CI `Documentation Check` (`validate_docs.py --changed`) báo lỗi `Broken Link Error`; còn 2 biên bản Grilling mới trong `.md/knowledge/decisions/` chứa lược đồ `file:///` và chưa đăng ký vào `.md/knowledge/index.md`, làm gãy `test_wiki_health_linter.py`.
3. **Xung Đột Phiên Đồng Đẳng Trên Nhánh `main` Cục Bộ & Hành Vi `--delete-branch` Ở Trạng Thái `--detach`**:
   - Khi một phiên đồng đẳng đang giữ các commit chưa đẩy trên nhánh `main` cục bộ (`ahead > 0`), việc chạy `git checkout` hoặc `session_cleanup.py --execute` trực tiếp trên thư mục gốc sẽ phá hỏng cây làm việc của phiên kia; ngoài ra, lệnh `gh pr merge <PR> --squash --delete-branch` sau khi gộp PR thành công sẽ trả mã thoát `1` nếu worktree hiện tại đang ở trạng thái detached HEAD mà chưa gỡ worktree hoặc xóa nhánh từ xa tường minh.

### Key Architectural Invariants & Learned Rules (`RULE-1.7`, `RULE-2.22`, `RULE-4.21`)
1. **Hợp Đồng GPI JSON, Dải Trễ Hysteresis, Bất Biến Văn Xuôi Sạch & 3 Trình Biên Dịch Trên Hub (`RULE-1.7`)**:
   - Khóa hợp đồng `ccba-harness evaluate-gpi --json` theo đúng `ArchitectureTier.value`, `allow_standalone_skill` và `breakdown.preserved_by_hysteresis`; chỉ truyền `--existing-tier tier-2b` khi frontmatter vốn đã khai báo `tier: kernel` trước khi sửa (cấm bơm cho bản nháp mới hoặc `tier: workflow`), và sửa trực tiếp 4 khóa `gpi_*` trong frontmatter thay vì truyền `--s/--k/--a/--p` lên tệp đã có đủ khóa.
   - Tách bạch kiểm định thành viên Hub SSOT qua sự hiện diện vật lý tại `<hub_path>/.agents/skills/<skill-dir>/SKILL.md` hoặc `catalog.yaml` (dừng ngay trên Spoke nếu `CCBA_HUB_PATH` không phân giải được); giữ văn xuôi `SKILL.md` sạch trước `RE_DEAD_WOOD`, `RE_BASHISMS`, `RE_START_PROCESS`; và trên Hub bắt buộc chạy đủ 3 writer (`compile_catalog.py`, `compile_skills_docs.py --write`, `sync_hub_adr_matrix.py`) kèm `verify-patch --preset skill`.
2. **Rào Chắn `find_dropped_rules`, Tái Định Tuyến Liên Kết Lưu Trữ `_rebase_archive_links` & Đăng Ký `index.md` Tức Thì (`RULE-2.22`)**:
   - Trong `scripts/governance/compact_session_learnings.py`, `run_compact()` gọi `find_dropped_rules(current_content, template)` để từ chối ghi đè (mã thoát `1`) nếu khuôn mẫu tĩnh làm rơi bất kỳ định danh `RULE-\d+\.\d+` nào đang có mặt (trừ khi truyền cờ tường minh `--allow-rule-drop`); ưu tiên nén câu chữ tại chỗ trong `session_learnings.md` và đẩy diễn giải đầy đủ sang `session_learnings_history.md`.
   - Hàm `backup_to_archive()` tự động gọi `_rebase_archive_links()` chuyển `(archive/<file>)` $\to$ `(<file>)` và `(wiki/<file>)` $\to$ `(../wiki/<file>)` cho bản chụp lưu trong `.md/knowledge/archive/`. Mọi tệp Markdown mới tạo dưới `.md/knowledge/` (ngoài `exclude_dirs`) bắt buộc dùng liên kết tương đối chuẩn repo (cấm `file:///`, khớp đúng tên tệp `docs/adr/NNNN-*.md`) và đăng ký ngay vào `.md/knowledge/index.md` + `log.md`.
3. **Cô Lập `git worktree` Khi `main` Có Phiên Song Song & Cổng Đầu Vào Tệp `-F` (`RULE-4.21`)**:
   - Khi nhánh `main` cục bộ chứa commit chưa đẩy của phiên đồng đẳng, toàn bộ quy trình TRIHT, gộp PR, lưu trữ `docs/walkthrough-pr-*` và nhánh `fix/session-retrospective-*` bắt buộc thực thi trên `git worktree` cô lập tách trực tiếp từ `origin/main`; gỡ bỏ worktree tạm trước khi chạy `gh pr merge --squash --delete-branch` (hoặc chạy bù `git push origin --delete <branch>`), và luôn truyền nội dung PR/comment qua `-F <body_file>` theo Bất biến §12.1.

---

## 58. Nâng Cấp Giao Thức Đồng Đẳng `v2.3` (`PeerPromptEnvelope` Lineage, Smart-Sync Scaffold & Spoke `.gitignore` Hygiene — `PR #704`)

### Context & Implementation Summary (Phiên ngày 2026-11-11 — Hub `PR #704`; Grok Sessions `aff784b5` & `ecba5b1f`)
- **Đối soát thực nghiệm toàn kho**: Quét `420` tệp `.md/peer_exchange/` trên `6` repo, `94` khối `PeerVerdictTelemetry`, và `1,037` phiên `~/.grok/sessions/`, đạt `FINAL_ACCEPT` ở vòng `signoff_diff` (`ecba5b1f-a1ac-4d4b-aead-bfc1c4492d6c`, `0` điều kiện chặn).
- **Truyền Lineage End-to-End & Bảo Toàn KV-Cache (`RULE-4.20`, `COND-09`, `COND-12`)**: Giữ `ConfigDict(extra="forbid")` trên `PeerPromptEnvelope` và truyền đủ 4 trường truy vết (`conversation_id`, `task_id`, `spoke_name`, `tags`) xuống `PeerVerdictBlock` trong `_attach_verdict_lineage()`, kèm cơ chế tự nạp `ANTIGRAVITY_CONVERSATION_ID` từ môi trường và suy luận `spoke_name` không cần ghi đè tệp prompt gốc.
- **Ép Kiểu Điều Kiện Đa Khóa & Định Tuyến Hậu Tố Prompt (`COND-13`, `COND-15`)**: Mở rộng `_coerce_condition_strings` nhận diện `title`/`summary`/`issue`/`rationale`/`detail`/`action`; ưu tiên bắt `*prompt*.md` trước `grok_signoff_*`/`grok_review_*` trong `_infer_stage_from_filename`; đồng bộ bảng `PROFILE_SPECS` (7 profile) trong `PEER_HANDSHAKE.md` và `README.md`.
- **Smart-Sync `.md/peer_exchange/`, Kiểm Tra Sức Khỏe Venv & Chuẩn Hóa `.gitignore` (`COND-01..11`, `COND-14`, `COND-16`)**: Bổ sung `ensure_peer_exchange_scaffold()` (chuẩn hóa `CRLF -> LF`, trả về schema 4 trường `{type, name, status, path}`, sao lưu bằng dấu thời gian không chứa `:` vào `.md/backups/peer_exchange/`, bảo toàn toàn bộ `grok_*`/`prompt_*`), `check_spoke_runtime_health()` warn-only exit `0`, và thống nhất `.gitignore` Hub/Spoke chỉ theo dõi `PEER_HANDSHAKE.md`, `README.md`, `.gitkeep`.
