# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants (Compacted Working Memory)

> **Phạm vi áp dụng:** Hub (`ccba-agent-platform`) & Spokes (`ccba-legal-knowledge`, etc.)
> **Tiêu chuẩn:** OKF v2.4, ADR 0030, 0031, 0035, 0041, 0044, 0051, 0057, 0058, 0059.
> **Lịch sử & Post-Mortems:** [session_learnings_history.md](archive/session_learnings_history.md) | Ngưỡng: $\le 10\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc, Phân Tầng Kỹ Năng & Quản Trị Seams (Architecture & Governance)

- **RULE-1.1 [ADR 0057 — Khung 2 Giai Đoạn & Chỉ Số GPI]**:
  - *Cổng 0 (Determinism)*: Tác vụ thuần giải thuật/IO $\rightarrow$ Package Deep Seams (`packages/*/src/`). `SKILL.md` không chứa code trần.
  - *Cổng 1 (Orchestration)*: Tác vụ đa luồng/StateGraph/HITL $\rightarrow$ Tier 3 Composite Orchestrator (short-circuit Cổng 1, không tính GPI).
  - *Chỉ số GPI*: $\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$. $\text{GPI} < 12.0 \rightarrow$ Tier 2A; $\ge 12.0 \rightarrow$ Tier 2B. User Rituals: $A = 1.0$.
- **RULE-1.2 [ADR 0053 — Single-Writer Protocol Cho Orchestrators]**:
  - Đa tác tử tuân thủ Single-Writer: Lead Orchestrator duy nhất ghi mã/logs. Subagents chỉ xuất Structured Patch vào `.system_generated/scratch/`.
- **RULE-1.3 [ADR 0035 — Deep Modules, Seams & Zero-Exemption AST]**:
  - Thin Seam: Module chỉ bộc lộ `__all__` hoặc `__init__.py`. Cấm import private submodule `_*`.
  - Zero-Exemption: Gỡ bỏ bypass hardcoded trong `check_dependency_contracts.py`. Tệp thử nghiệm chuyển vào `archive/`.
- **RULE-1.4 [ADR 0033 & ADR 0056 — Spoke Directory Hygiene & Zombie Prevention]**:
  - Cấu trúc `.\.md\`: Gốc chứa `workspace_context.yaml`; dữ liệu vào `extracted_docs/`; tri thức vào `knowledge/`; thử nghiệm vào `archive/`.
  - Spoke Synchronizer (`coordinator.py`): Đổi tên workflows cũ thành `.md.bak` (DEPRECATED_MIGRATED_TO_SKILL), xóa thư mục cũ theo aliases.
- **RULE-1.5 [ADR 0037 & ADR 0051 — Two-Tier Traceability Matrix & Status Regex]**:
  - Tier 1: Hub (53 ADRs). Tier 2: Spoke (`docs/adr/`). Bảo toàn bảng tùy chỉnh qua markers `CUSTOM_SECTIONS`.
  - Regex bắt trạng thái ADR: `(?:\*|-)?\s*\*\*\s*Status:\s*\*\*`. Lọc bỏ file non-ADR (`notes.md`, `template.md`).
- **RULE-1.6 [ADR 0044 — Federated RAG & Dynamic Import]**:
  - Tier 0 import Tier 1: `try: from ccba_legal.xxx import yyy; except ImportError: pass`. Cache BM25 Singleton module; Cache Embedding `.npy` kiểm tra SHA-256 sidecar.
- **RULE-1.7 [Clean Architecture — Phân Tách Hạ Tầng Kết Nối]**:
  - Tách hạ tầng xác thực thành `drive_client.py`, tránh inverted coupling giữa Pull và Push.
- **RULE-1.8 [ADR 0044 & Issue #326 — Multi-Device Spoke & Universal Invariant Merge]**:
  - *Universal Invariant Regex*: Dùng regex multiline bảo tồn 100% điều khoản cục bộ khi sync.
  - *Cross-Drive Fallback*: Khi `relpath` lỗi `ValueError`, fallback `hub_path` về `None`, tránh gắn cứng ổ đĩa vào context.
- **RULE-1.9 [2-Phase Planning Guardrail — The Factory Model]**:
  - Refactoring bộ trích xuất/chuyển đổi BẮT BUỘC phân lập 2 giai đoạn: Phase 1 (Pure Structural Refactoring — Zero-Regression 0.0%, 100% byte-for-byte identical, dual-dispatch) và Phase 2 (Feature/Schema Mutations). Cấm scope conflation.

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Strict Testing)

- **RULE-2.1 [Strict Mypy Type-Safety — Chống Anti-Pattern AP9.1]**:
  - CẤM `[[tool.mypy.overrides]] ignore_errors = true`. Ép kiểu tường minh cho binary I/O, fonts, dicts. Chỉ dùng `ignore_missing_imports = true` cho third-party thiếu stubs.
- **RULE-2.2 [Spoke CI Gates Verification Pipeline]**:
  - 5 Cổng Zero-Tolerance: lint_visual_parity, validate_legal_spoke, test_converter_regression, verify_all_docs_against_pdf, verify_cross_links.
- **RULE-2.3 [Fast Feedback Loops (< 2s) & Parity Contract Tests]**:
  - Unit tests nòng cốt đạt SLA $< 2\text{s}$ (`pytest -m fast`). `test_cli_doc_parity.py`: Khớp nối 100% giữa CLI và `SKILL.md`.
- **RULE-2.4 [Relative Link Resolution Depth]**:
  - Tệp `.agents/skills/<skill>/SKILL.md` trỏ về package monorepo dùng `../../../packages/<pkg>`. CẤM commit URI `file:///` hoặc `conversation://`.
- **RULE-2.5 [ADR 0058 — SSOT Archetype Routing & Disjoint Subdomains]**:
  - Ánh xạ kỹ năng sang đề thi (`eval_*.json`) BẮT BUỘC dùng `archetypes.py` làm SSOT. Từ khóa chuyên biệt (`grill`, `adr`, `risk`) tách thành subdomain độc lập chống va chạm regex.
- **RULE-2.6 [YouTube Ingestion & Livestream Garbage Guard]**:
  - Lọc bỏ `live_chat` và ngắt sớm nếu `is_live: True`. Regex guard chặn HTML rác trước Map-Reduce.
- **RULE-2.7 [Dry-Run Complete Isolation]**:
  - `--dry-run` BẮT BUỘC cô lập 100%: CẤM ghi báo cáo, CẤM alert Telegram, CẤM xóa stale briefs, CẤM copy tệp về repo gốc.
- **RULE-2.8 [Cross-Platform Sandbox Root Traversal Invariant]**:
  - CẤM giả định độ sâu cố định `parents[N]` khi tìm thư mục gốc. Trên Linux runner, `/tmp/dir/sub` có `parents[2]` trỏ về root `/` gây `PermissionError: [Errno 13]`. BẮT BUỘC duyệt ngược tìm `(p / ".md").is_dir()`, fallback local `.cache/`, và bọc `try...except (PermissionError, OSError)`.
- **RULE-2.9 [Test Fixture Isolation & Hub Discovery Decoupling]**:
  - Test fixtures và runners (`run_isolated_tests.py`, root `conftest.py`) BẮT BUỘC cô lập môi trường: xóa `CCBA_HUB_PATH` và `HUB_PATH`. CẤM rò rỉ biến môi trường máy trạm vào test subprocess.

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu Hiện Hành (Legal & Data Standards)

- **RULE-3.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - MỌI văn bản pháp luật viện dẫn BẮT BUỘC ĐANG CÓ HIỆU LỰC. VĂN BẢN HIỆN HÀNH: **Luật Xây dựng 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP** (thay NĐ 175 & 15), **NĐ 207/2026/NĐ-CP** (thay NĐ 06), **NĐ 206/2026/NĐ-CP** (thay NĐ 10). CẤM dùng văn bản hết hiệu lực.
- **RULE-3.2 [TVPL VIP 3-Tier Download Priority — ADR 0031]**:
  - Tier 1 (`part=-100`): VIP Vector PDF (Mỏ neo tối thượng). Tier 2 (`part=-1&docx=1`): VIP Word (Nguồn vàng cho `docx_converter`). Tier 3 (`part=0`): Scan PDF (Dự phòng).
- **RULE-3.3 [Làm Sạch Bảng Biểu, Footnotes & ADR 0044 Multi-Part Disambiguation]**:
  - Footnote: Khử lặp số `re.sub(r"^[0-9]+[)\.]\s*", "", fn_clean).strip()`; khử lặp chú thích ô gộp ngang OpenXML (`gridSpan`).
  - Subheader: Kiểm tra `not is_numeric` trước khi gộp dòng subheader tránh nuốt dữ liệu cột cùng giá trị.
  - Multi-Part: Quy chuẩn đa phần mang tiền tố `bang_pXX_YY.csv` và trường `part_id: "pXX"` trong `tables_catalog.json`.
- **RULE-3.4 [RAG Normative Spanning & ADR-0059 Test Isolation]**:
  - `clauses.json` span (`line_start`/`line_end`) bắt buộc bao trọn toàn văn quy phạm pháp luật đa dòng của điều khoản; cấm span 1 dòng chỉ trỏ thẻ `<a>`.
  - Test suites bắt buộc dùng `tmp_path / "legal_registry.yaml"`, cấm ghi đè vào `.md/data/legal_registry.yaml`. Gate 4 CI Spoke hard-lock khi thiếu `clauses.json`.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent (Workflows, Commands & Review)

- **RULE-4.1 [Entry Point Duy Nhất Khi Có Issue ID: `/ccba-new-feature`]**:
  - Có Issue ID: LUÔN đề xuất `/ccba-new-feature #<id>` (8 bước Factory Model). Cấm nhảy thẳng vào `/ccba-implement`, `/ccba-to-spec`, `/ccba-to-tickets`.
- **RULE-4.2 [Slash Command Parity & Active Commands SSOT]**:
  - Đối chiếu `catalog.yaml` trước khi đề xuất `/command`. Chỉ kỹ năng có `command: /...` mới gắn tiền tố `/`. Tài liệu `references/*.md` (Tier 2A) cấm tiền tố `/`.
- **RULE-4.3 [Tiêu Chí Hoàn Thành Đa Nhánh & DRY Reference]**:
  - Tiêu chí hoàn thành phải có nhánh kiểm chứng cho từng cờ (`--compare`, `--port`, `--improve`, `--copy-raw`). Quy tắc kết hợp cờ chỉ tuyên bố 1 lần tại `MODES.md`.
- **RULE-4.4 [GitHub Copilot Multi-Tier Review Gating]**:
  - Quét `author.login` thay vì `user.login`. Bắt buộc kiểm tra `### 🟡 Changes recommended` và review `body` của Copilot kể cả khi COMMENTED. Cấm merge nếu chưa sửa/giải trình.
- **RULE-4.5 [Git Governance Pre-Push Lock & Architecture Drift Invariant]**:
  - Repo Hub cấm push trực tiếp lên `refs/heads/main` qua hook `pre-push`; mọi thay đổi qua PR. Sửa file trong `packages/`, `scripts/`, `drift_auditor.py` bắt buộc cập nhật `arch_docs` (`README.md`, `PLATFORM.md`) cùng PR.
- **RULE-4.6 [PR Shift-Left CI & Zero-Red-Merge]**:
  - CI chạy `ruff check` và `ruff format --check` toàn monorepo. Chạm $\ge 2$ pkgs, BẮT BUỘC chạy `verify-patch --preset ci`. CẤM dùng `gh pr merge --admin` hoặc `--auto`; dùng Reactive Wakeup `gh pr checks --watch`, chờ Copilot review xong và đạt 100% Green trước khi merge.

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows, Chrome CDP & Tooling)

- **RULE-5.1 [Chromium VIP Session Engine & CDP Browser Target]**:
  - Profile `~/.gemini/antigravity/chrome_vip` cổng `9222`. `Browser.setDownloadBehavior` BẮT BUỘC qua Browser Target WebSocket (`/json/version`). Selectors kế thừa `TVPLSelectors`.
- **RULE-5.2 [Windows Path Quotes & Hook Protection]**:
  - Khi Antigravity IDE bọc ngoặc kép `"C:\..."` vào `hooks.json`, vô hiệu bằng `{}` và khóa `IsReadOnly = $true` trên PowerShell. Timeout $\ge 60\text{s}$ cho integration tests có scan metadata trên Windows.
- **RULE-5.3 [Query Sanitization & Turnstile Bypass]**:
  - Query TVPL có dấu `/`, `:`, `-` phải thay bằng dấu cách (`quote_plus`) chống lỗi IIS mã hóa `%2F`.
