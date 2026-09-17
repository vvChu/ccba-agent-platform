# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants (Compacted Working Memory)

> **Phạm vi:** Hub & Spokes | OKF v2.2, ADR 0016-0058
> **Tra cứu:** [session_learnings_history.md](archive/session_learnings_history.md) | Ngưỡng: $\le 10\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc & Phân Tầng Kỹ Năng (Architecture & Governance)

- **RULE-1.1 [ADR 0057 — Khung 2 Giai Đoạn & Chỉ Số GPI]**:
  - Cổng 0: Giải thuật/IO $\rightarrow$ Deep Seams (`packages/*/src/`). `SKILL.md` cấm code logic trần.
  - Cổng 1: Đa luồng/StateGraph/HITL $\rightarrow$ Tier 3 Composite Orchestrator (không tính GPI).
  - $\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$. $< 12.0 \rightarrow$ Tier 2A; $\ge 12.0 \rightarrow$ Tier 2B. Rituals ép $A = 1.0$.
- **RULE-1.2 [ADR 0053 — Single-Writer Protocol]**:
  - Đa tác tử: Lead duy nhất ghi codebase/logs; subagents chỉ xuất PatchBlocks vào sandbox. Hợp nhất qua `execute_swarm_patches`.
- **RULE-1.3 [ADR 0035 — Deep Modules, Seams & Zero-Exemption AST]**:
  - Thin Seam: Package chỉ bộc lộ `__all__`/`__init__.py`, cấm import `_*`. Gỡ bypass trong `check_dependency_contracts.py`. Test cũ vào `archive/`.
- **RULE-1.4 [ADR 0033 & ADR 0056 — Directory Hygiene]**:
  - `.\.md\`: Gốc chỉ chứa `workspace_context.yaml`; `extracted_docs/`; `knowledge/`; `archive/`.
- **RULE-1.5 [ADR 0037 & ADR 0051 — Traceability Matrix]**:
  - Giữ qua `<!-- CUSTOM_SECTIONS_START -->`...`<!-- CUSTOM_SECTIONS_END -->`. Regex status: `(?:\*|-)?\s*\*\*\s*Status:\s*\*\*`. Lọc bỏ non-ADR.
- **RULE-1.6 [ADR 0044 — Federated RAG & Dynamic Import]**:
  - Dynamic import: `try: from ccba_legal.xxx import yyy; except ImportError: pass`. Cache BM25 Singleton, `.npy` kèm `.sha256`.
- **RULE-1.7 [ADR 0046 — Sanitized Fleet Telemetry]**:
  - Chỉ trích xuất số liệu phi định danh (`tokens`, `cost`). Cấm log prompt/dữ liệu khách hàng.
- **RULE-1.8 [ADR 0058 — Discrete Diagnostic Commands]**:
  - `SelfHealingEngine`: mảng lệnh độc lập (`["c1", "c2"]`), CẤM ghép `&&` để tự phục hồi (< 500ms).
- **RULE-1.9 [Corpus Discovery]**:
  - Quét `project_root` qua `reg_parent/{, .md/}legal_docs`, `project_root/{, .md/}legal_docs`.
- **RULE-1.10 [ADR 0057 — Skill Promotion Triad]**:
  - Tier 2A $\rightarrow$ Tier 2B: (1) Xóa triggers trùng; (2) Trỏ alias ngắn; (3) Tách Hub vs Spoke.
- **RULE-1.11 [Diagramming Hygiene]**:
  - Mermaid: Subgraph dùng `style <id>`, cấm `classDef`. Nhãn `["..."]`, ngắt `<br/>`. D2/Kroki: SVG.
- **RULE-1.12 [Model-Invocation Budget & Cross-Cutting Cognitive Skills]**:
  - Trần 10 model-invoked skills/bundle (ADR-0040). Kỹ năng tư duy (`ccba-issue-tree`) gán `disable-model-invocation: true` để gọi qua `/command` hoặc referral mà không tốn system tokens.

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Testing)

- **RULE-2.1 [Strict Mypy Type-Safety — Chống AP9.1]**:
  - CẤM `ignore_errors = true`. Ép kiểu tường minh cho binary I/O, fonts, dicts. Chỉ dùng `ignore_missing_imports = true` khi thiếu stubs.
- **RULE-2.2 [Spoke CI Gates Verification Pipeline]**:
  - 5 Cổng: (1) `lint_visual_parity`, (2) `validate_legal_spoke`, (3) `test_converter_regression`, (4) `verify_all_docs_against_pdf` (SHA-256), (5) `verify_cross_links`.
- **RULE-2.3 [Fast Feedback Loops (< 2s) & Parity Contract Tests]**:
  - Tests $< 2\text{s}$ (`pytest -m fast`). `test_cli_doc_parity.py`: Khớp 100% CLI và `SKILL.md`.
- **RULE-2.4 [Relative Link Resolution Depth]**:
  - `SKILL.md` trỏ package 3 cấp `../../../packages/`; `references/` trỏ root 4 cấp. CẤM URI `file:///` hoặc `conversation://`.
- **RULE-2.5 [Windows Subprocess UTF-8 Encoding Standard]**:
  - `subprocess.run(..., text=True)` trên Windows: `encoding="utf-8", errors="replace"`.
- **RULE-2.7 [Safe-Remove & Read-Only Cleanup]**:
  - `safe_remove`: Check `is_symlink() or is_file()`, `chmod(0o666)` trước xóa; tránh `NotADirectoryError`.
- **RULE-2.8 [Offline XML/OOXML Validation]**:
  - `lxml`: Nhúng schema offline, dùng `XMLParser(no_network=True, resolve_entities=False)`.
- **RULE-2.9 [Flaky Test Root-Cause Transparency]**:
  - Test retry PASS chưa sửa mã: CẤM kết luận đã sửa xong. Phải tìm nguyên nhân gốc.
- **RULE-2.10 [Git Simplify Gate Bypass]**:
  - `simplify_gate` chặn diff $> 400$ LOC, $> 8$ files. Commit tự động thêm `# APPROVED: <lý_do>`.

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu (Legal & Data Standards)

- **RULE-3.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - MỌI văn bản viện dẫn BẮT BUỘC ĐANG CÓ HIỆU LỰC (CURRENT). Chặn đứng LLM Legacy Bias bằng pre-check.
  - VĂN BẢN HIỆN HÀNH: **Luật Xây dựng 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP** (thay NĐ 175 & NĐ 15), **NĐ 207/2026/NĐ-CP** (thay NĐ 06). CẤM dùng VB hết hiệu lực.
- **RULE-3.2 [TVPL VIP 3-Tier Download Priority — ADR 0031]**:
  - Tier 1 (`part=-100`): VIP Digital Vector PDF. Tier 2 (`part=-1&docx=1`): VIP OpenXML Word (`docx_converter.py`). Tier 3 (`part=0`): Gazette Scan PDF.
- **RULE-3.3 [Làm Sạch Bảng Biểu & Chú Thích Pháp Lý]**:
  - Footnote: `re.sub(r"^[0-9]+[)\.]\s*", "", fn_clean).strip()`. Bảng Markdown nhận diện qua tiêu đề và `| :--- |`.
- **RULE-3.4 [ADR 0059 — Cưỡng Chế Nguyên Văn & Chống Bịa Đặt Dữ Liệu Pháp Lý]**:
  - CẤM tự suy diễn/bịa đặt điều khoản VBPL trong code/fixtures. Trích dẫn nguyên văn 100%.
  - Mandatory Acquisition First: Thiếu tệp gốc dùng `TVPLCrawler` tải PDF/DOCX chính thức hoặc xin file gốc. Đóng dấu SHA-256 (`pdf_sha256`), kiểm định bằng `validate_bundle_provenance()`.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent (Workflows & Review)

- **RULE-4.1 [Entry Point Duy Nhất Khi Có Issue ID: `/ccba-new-feature`]**:
  - Khi có Issue ID, LUÔN đề xuất `/ccba-new-feature #<id>` (8 bước Factory Model). CẤM nhảy thẳng implement.
- **RULE-4.2 [Slash Command Parity & Active Commands SSOT]**:
  - Đối chiếu `catalog.yaml` trước khi đề xuất `/command`. Chỉ kỹ năng có `command: /...` mới gắn tiền tố `/`. Tài liệu `references/*.md` CẤM dùng `/`.
- **RULE-4.3 [Tiêu Chí Hoàn Thành Đa Nhánh & DRY Reference]**:
  - Tiêu chí hoàn thành phải có nhánh kiểm chứng cho từng cờ (`--compare`, `--port`, `--improve`, `--copy-raw`).
- **RULE-4.4 [GitHub Copilot Review Gating & Walkthrough Mirroring]**:
  - Quét `author.login`. Bắt buộc xét `### 🟡 Changes recommended` và `body` dù `COMMENTED`. Cấm merge nếu chưa giải trình. Ghi `review_id`/`id` vào `walkthrough.md` để vượt audit.
- **RULE-4.5 [AI Gateway Spark Auth & Fast-Inference Gating]**:
  - LiteLLM Spark: Bearer `sk-spark-secure-key-2026`. Ưu tiên `gemini-3.7-flash` (< 1s), route `qwen-local-primary` sau GPU warmup.
- **RULE-4.6 [Tier 3 Orchestrator & Deterministic Verification Gating — ADR-0057 / ADR-0058]**:
  - Router/Orchestrator: SSOT tại `.agents/skills/ccba-platform/SKILL.md` (`tier: orchestrator`), Single-Writer Protocol. Spoke sync (`sync_spoke.py --verify`) kích hoạt `ccba-harness verify-patch`.
- **RULE-4.7 [ArtifactMetadata Workspace Invariant]**:
  - `ArtifactMetadata` CHỈ dùng cho brain (`<appDataDir>\brain\<id>/`). Bỏ qua khi ghi workspace.
- **RULE-4.8 [Zero-Polling & Reactive Wakeup Hard Invariant]**:
  - CẤM polling loop `manage_task(status)`. Dừng tool để runtime tự đánh thức qua Reactive Wakeup.
- **RULE-4.9 [RSA-OAEP Length & Decoupled Telemetry Heartbeat — ADR-0046]**:
  - RSA-2048 OAEP giới hạn plaintext $\le 190$ bytes. Tách metadata tĩnh (`static_hash`) khỏi telemetry động (`.md/telemetry/spoke_heartbeats.yaml` gitignored).
- **RULE-4.10 [ADR-0045 Spoke Leakage Guard & Report Mirroring Location]**:
  - Gốc `.md/` CHỈ chứa `workspace_context.yaml`. Báo cáo nghiệm thu BẮT BUỘC đặt tại `.md/knowledge/reports/walkthrough.md` (CẤM lưu tại `.md/walkthrough.md`). `audit_pr_comments.py` tự động đối soát đường dẫn này.
- **RULE-4.11 [OpenAI SDK Embedding & Reasoning Timeout Scaling]**:
  - `embed()` Gemini: `extra_body={"drop_params": True}` chống HTTP 400. Model: `gemini-embedding-2` (3072 dims).
  - Reasoning: Sàn `max_tokens` $\ge 16,384$. Auto-Timeout: `max(timeout, max_tokens / 50.0)`. Thẻ `<think>` bóc tách vào `ChatResult.thinking`.
- **RULE-4.12 [Cross-Skill Referral Hooks & Concept-Level Invariants]**:
  - Khung tư duy tích hợp qua Referral Hooks tại điểm rẽ nhánh (bugs, qc, legal, grilling, spec). CẤM hardcode số lượng ("11 Ghế", "5 trạng thái") trong heading/text; dùng định danh khái niệm ("các Ghế CCBA", "ma trận RACI") chống drift review.

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows & Tooling)

- **RULE-5.1 [Chromium VIP Session Engine & CDP Browser Target]**:
  - Profile `~/.gemini/antigravity/chrome_vip` cổng 9222. `Browser.setDownloadBehavior` qua WebSocket.
- **RULE-5.2 [Windows Path Quotes & Hook Protection]**:
  - Windows: IDE bọc `hooks.json` trong `"C:\..."` $\rightarrow$ vô hiệu bằng `{}` và khóa `IsReadOnly = $true` trên PowerShell. Timeout $\ge 60\text{s}$.
- **RULE-5.3 [Query Sanitization & Turnstile Bypass]**:
  - Query TVPL có dấu `/`, `:`, `-` thay bằng dấu cách (`quote_plus`) chống lỗi IIS mã hóa `%2F`.
- **RULE-5.4 [Upstream Git Engine Windows Safety]**:
  - Git Windows: Mutex `.md/scratch/upstream_sync.lock`; chữa stale `index.lock`; `safe_rmtree` với `chmod(0o666)`; Khử Zero-Scan.
