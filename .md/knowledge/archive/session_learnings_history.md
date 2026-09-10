# 🧠 CCBA Platform Knowledge Base: Session Learnings & Architectural Invariants

> **Scope:** Hub (`ccba-agent-platform`) & Spokes (`ccba-legal-knowledge`, etc.)
> **Standard:** OKF v2.2, ADR 0016, ADR 0021, ADR 0031, ADR 0032.

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
  - **Giải pháp:** Kết nối tới LiteLLM Gateway trên Server Spark (`100.83.192.30:8090`) với header xác thực `Authorization: Bearer sk-spark-secure-key-2026`. Định tuyến linh hoạt: sử dụng `gemini-3.7-flash` làm mô hình phản hồi nhanh (< 1s cho các bước map-reduce trinh sát tài liệu) và dùng `qwen-local-primary` sau khi đã hoàn tất warmup GPU.





