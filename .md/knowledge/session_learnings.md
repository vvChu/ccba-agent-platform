# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants (Compacted Working Memory)

> **Phạm vi:** Hub & Spokes | OKF v2.2, ADR 0016-0058
> **Tra cứu:** [session_learnings_history.md](archive/session_learnings_history.md) | Ngưỡng: $\le 10\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc & Phân Tầng Kỹ Năng (Architecture & Governance)

- **RULE-1.1 [ADR 0057 — Khung 2 Giai Đoạn & Chỉ Số GPI]**:
  - Cổng 0: Giải thuật/IO $\rightarrow$ Deep Seams (`packages/*/src/`). `SKILL.md` cấm code logic trần.
  - Cổng 1: Đa luồng/StateGraph/HITL $\rightarrow$ Tier 3 Composite Orchestrator (không tính GPI).
  - $\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$. $\text{GPI} < 12.0 \rightarrow$ Tier 2A (`references/`); $\ge 12.0 \rightarrow$ Tier 2B (`.agents/skills/ccba-<name>/`). Rituals (`disable-model-invocation: true`) ép $A = 1.0$.
- **RULE-1.2 [ADR 0053 — Single-Writer Protocol]**:
  - Đa tác tử (`ccba-teamwork`, swarms): Lead duy nhất ghi codebase/logs; subagents chỉ xuất PatchBlocks vào sandbox, cấm sửa trực tiếp. Hợp nhất qua `execute_swarm_patches`.
- **RULE-1.3 [ADR 0035 — Deep Modules, Seams & Zero-Exemption AST]**:
  - Thin Seam: Package chỉ bộc lộ `__all__`/`__init__.py`, cấm import private `_*`. Gỡ bypass hardcoded trong `check_dependency_contracts.py`. Test lịch sử vào `archive/`.
- **RULE-1.4 [ADR 0033 & ADR 0056 — Directory Hygiene]**:
  - `.\.md\`: Gốc chỉ chứa cấu hình (`workspace_context.yaml`); `extracted_docs/`; `knowledge/`; `archive/`.
  - Spoke Synchronizer (`coordinator.py`): Đổi workflows cũ thành `.md.bak` (`DEPRECATED_MIGRATED_TO_SKILL`), xóa thư mục theo `SKILL_DEPRECATION_ALIASES`.
- **RULE-1.5 [ADR 0037 & ADR 0051 — Traceability Matrix]**:
  - Tier 1: Hub Constitution (55 ADRs). Tier 2: Spoke Domain (`docs/adr/`). Giữ qua `<!-- CUSTOM_SECTIONS_START -->`...`<!-- CUSTOM_SECTIONS_END -->`.
  - Regex trạng thái ADR: `(?:\*|-)?\s*\*\*\s*Status:\s*\*\*`. Lọc bỏ file non-ADR (`notes.md`, `template.md`).
- **RULE-1.6 [ADR 0044 — Federated RAG & Dynamic Import]**:
  - Tier 0 import Tier 1: `try: from ccba_legal.xxx import yyy; except ImportError: pass`. Cache BM25 Singleton; Cache Embedding `.npy` đối chiếu sidecar `.sha256`.
- **RULE-1.7 [ADR 0046 — Sanitized Fleet Telemetry]**:
  - Telemetry Spoke $\rightarrow$ Hub: Chỉ trích xuất số liệu phi định danh (`tokens`, `cost`, `tool_counts`). Cấm thu thập prompt text/dữ liệu khách hàng.
- **RULE-1.8 [ADR 0058 — Discrete Diagnostic Commands]**:
  - `SelfHealingEngine` (`verify-patch --self-heal`): mảng lệnh độc lập (`["cmd1", "cmd2"]`), CẤM ghép chuỗi `&&` để regex chẩn đoán đúng và tự phục hồi (< 500ms).
- **RULE-1.9 [Multi-Tier Corpus Discovery & Layout Normalization]**:
  - Quét corpus từ registry trong `.md/data/`: suy luận `project_root` (3 cấp lùi) và quét 4 ứng viên: `reg_parent/{, .md/}legal_docs`, `project_root/{, .md/}legal_docs`.
- **RULE-1.10 [ADR 0057 — Standalone Skill Promotion Triad]**:
  - Thăng hạng Tier 2A $\rightarrow$ Tier 2B: (1) Xóa triggers trùng ở nguồn; (2) Sửa `SKILL_DEPRECATION_ALIASES` trong `coordinator.py` trỏ alias ngắn về skill mới; (3) Phân định ranh giới Hub $\rightarrow$ Spoke vs Upstream $\rightarrow$ Hub trong `SKILL.md` và `catalog.yaml`.

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Testing)

- **RULE-2.1 [Strict Mypy Type-Safety — Chống AP9.1]**:
  - CẤM `ignore_errors = true`. Ép kiểu tường minh cho binary I/O, fonts, dicts. Chỉ dùng `ignore_missing_imports = true` cho 3rd-party thiếu stubs.
- **RULE-2.2 [Spoke CI Gates Verification Pipeline]**:
  - 5 Cổng: (1) `lint_visual_parity.py`, (2) `validate_legal_spoke.py`, (3) `test_converter_regression.py`, (4) `verify_all_docs_against_pdf.py` (SHA-256), (5) `verify_cross_links.py`.
- **RULE-2.3 [Fast Feedback Loops (< 2s) & Parity Contract Tests]**:
  - Tests nòng cốt $< 2\text{s}$ (`pytest -m fast`). `test_cli_doc_parity.py`: Khớp 100% CLI và `SKILL.md`. `drift_auditor.py`: Miễn trừ `scripts/tests/` chống cảnh báo giả.
- **RULE-2.4 [Relative Link Resolution Depth]**:
  - `SKILL.md` trỏ package dùng 3 cấp `../../../packages/<pkg>`; `references/` trỏ root dùng 4 cấp `../../../../`. CẤM commit URI `file:///` hoặc `conversation://`.
- **RULE-2.5 [Windows Subprocess UTF-8 Encoding Standard]**:
  - `subprocess.run(..., text=True)` trên Windows mặc định `cp1252`. BẮT BUỘC `encoding="utf-8", errors="replace"` chống `UnicodeDecodeError`.
- **RULE-2.7 [Safe-Remove, Read-Only & Symlink Cleanup Invariant]**:
  - `safe_remove`: Windows symlink ném `NotADirectoryError` nếu dùng `rmtree()`. Kiểm tra `is_symlink() or is_file()`, gỡ read-only bằng `chmod(0o666)` rồi mới gọi `rmtree()`.
- **RULE-2.8 [Offline XML/XSD Validation & Schema Cache]**:
  - XML/OOXML (`lxml`): CẤM tải schema qua HTTP $\rightarrow$ nhúng offline, dùng `Resolver`. `XMLParser(no_network=True, resolve_entities=False)` chống XXE. Cache `XMLSchema` (`_COMPILED_SCHEMA_CACHE`).
- **RULE-2.9 [Flaky Test Root-Cause Transparency & No-False-Pass Lock]**:
  - Test FAIL rồi PASS khi retry chưa sửa mã: CẤM kết luận đã sửa xong. Bắt buộc tìm cội nguồn kỹ thuật và giải trình minh bạch trước release.
- **RULE-2.10 [Git Simplify Gate Bypass Protocol]**:
  - `simplify_gate` (`scripts/hooks/simplify.py`) chặn diff $> 400$ LOC, $> 8$ files khi gặp hard verbs (`deploy`, `ship`, `merge`...). Với commit tài sản lớn/sinh tự động (Web Portal, `docs/`), chèn `# APPROVED: <lý_do>` vào câu lệnh để kích hoạt `context.is_approved` vượt cổng an toàn.

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu (Legal & Data Standards)

- **RULE-3.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - MỌI văn bản viện dẫn BẮT BUỘC ĐANG CÓ HIỆU LỰC (CURRENT). Chặn đứng LLM Legacy Bias bằng pre-check trước khi xuất báo cáo.
  - VĂN BẢN HIỆN HÀNH: **Luật Xây dựng 2025** (`135/2025/QH15`), **Nghị định 217/2026/NĐ-CP** (thay NĐ 175/2024 & NĐ 15/2021), **Nghị định 207/2026/NĐ-CP** (thay NĐ 06/2021). CẤM dùng văn bản hết hiệu lực.
- **RULE-3.2 [TVPL VIP 3-Tier Download Priority — ADR 0031]**:
  - Tier 1 (`part=-100`): VIP Digital Vector PDF (Mỏ neo Pháp lý). Tier 2 (`part=-1&docx=1`): VIP OpenXML Word Document (cho `docx_converter.py`). Tier 3 (`part=0`): Gazette Scan PDF.
- **RULE-3.3 [Làm Sạch Bảng Biểu & Chú Thích Pháp Lý]**:
  - Footnote: Khử lặp số: `re.sub(r"^[0-9]+[)\.]\s*", "", fn_clean).strip()`. Bảng Markdown nhận diện qua tiêu đề và `| :--- |`.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent (Workflows & Review)

- **RULE-4.1 [Entry Point Duy Nhất Khi Có Issue ID: `/ccba-new-feature`]**:
  - Khi có Issue ID, LUÔN đề xuất `/ccba-new-feature #<id>` (8 bước Factory Model). CẤM nhảy thẳng implement.
- **RULE-4.2 [Slash Command Parity & Active Commands SSOT]**:
  - BẮT BUỘC đối chiếu `catalog.yaml` trước khi đề xuất `/command`. Chỉ kỹ năng có `command: /...` mới gắn tiền tố `/`. Tài liệu `references/*.md` CẤM dùng `/`.
- **RULE-4.3 [Tiêu Chí Hoàn Thành Đa Nhánh & DRY Reference]**:
  - Tiêu chí hoàn thành phải có nhánh kiểm chứng cho từng cờ (`--compare`, `--port`, `--improve`, `--copy-raw`).
- **RULE-4.4 [GitHub Copilot Review Gating & Walkthrough Mirroring]**:
  - Quét `author.login`. Bắt buộc xét `### 🟡 Changes recommended` và `body` Copilot dù `COMMENTED`. Cấm merge nếu chưa giải trình.
  - `audit_pr_comments.py`: Ghi `review_id` (`PRR_...`) và inline comment `id` vào `walkthrough.md` để vượt audit.
- **RULE-4.5 [AI Gateway Spark Auth & Fast-Inference Gating]**:
  - LiteLLM Spark (100.83.192.30:8090): Bearer `sk-spark-secure-key-2026`. Ưu tiên `gemini-3.7-flash` (< 1s), route `qwen-local-primary` sau GPU warmup.
- **RULE-4.6 [Tier 3 Orchestrator & Deterministic Verification Gating — ADR-0057 / ADR-0058]**:
  - Router/Orchestrator: SSOT tại `.agents/skills/ccba-platform/SKILL.md` (`tier: orchestrator`), tuân thủ Single-Writer Protocol.
  - Đồng bộ Spoke (`sync_spoke.py`): cờ `--verify` kích hoạt `ccba-harness verify-patch`, khóa cứng nếu lỗi.
- **RULE-4.7 [ArtifactMetadata Workspace Invariant]**:
  - `ArtifactMetadata` CHỈ dùng cho tệp trong brain (`<appDataDir>\brain\<id>/`). Bỏ qua khi ghi workspace chống schema rejection.
- **RULE-4.8 [Zero-Polling & Reactive Wakeup Hard Invariant]**:
  - CẤM TUYỆT ĐỐI polling loop `manage_task(status)` khi lệnh chạy nền. BẮT BUỘC dừng gọi tool để runtime tự đánh thức qua Reactive Wakeup hoặc làm việc song song. Ưu tiên scoped test (<10s).

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows & Tooling)

- **RULE-5.1 [Chromium VIP Session Engine & CDP Browser Target]**:
  - Chromium VIP: Profile `~/.gemini/antigravity/chrome_vip` cổng `9222`. `Browser.setDownloadBehavior` gọi qua WebSocket (`http://127.0.0.1:{port}/json/version`).
- **RULE-5.2 [Windows Path Quotes & Hook Protection]**:
  - Windows: IDE tự bọc `hooks.json` trong `"C:\..."` $\rightarrow$ vô hiệu bằng `{}` và khóa `IsReadOnly = $true` trên PowerShell. Timeout $\ge 60\text{s}$ cho tests.
- **RULE-5.3 [Query Sanitization & Turnstile Bypass]**:
  - Query TVPL có dấu `/`, `:`, `-` phải thay bằng dấu cách (`quote_plus`) chống lỗi IIS mã hóa `%2F`.
- **RULE-5.4 [Upstream Git Engine Windows Safety]**:
  - Git Windows (`upstream_evaluator.py`): (1) Mutex lock `.md/scratch/upstream_sync.lock`; (2) Tự chữa lành stale `index.lock`; (3) `safe_rmtree` dùng `os.chmod(p, stat.S_IWRITE)`; (4) Khử bẫy Zero-Scan: repo mới phải quét initial audit.
