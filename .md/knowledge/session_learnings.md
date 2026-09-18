# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants (Compacted Working Memory)

> **Phạm vi:** Hub & Spokes | OKF v2.2, ADR 0016-0058
> **Tra cứu:** [session_learnings_history.md](archive/session_learnings_history.md) | Ngưỡng: $\le 10\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc & Phân Tầng Kỹ Năng (Architecture & Governance)

- **RULE-1.1 [ADR 0057 — Khung 2 Giai Đoạn & Chỉ Số GPI]**:
  - Cổng 0: Deep Seams (`packages/*/`). `SKILL.md` cấm logic trần. Cổng 1: Tier 3 Composite Orchestrator.
  - $\mathbf{GPI} = 2.5S + 2K + 2A - 1.5P$. $< 12.0 \rightarrow$ Tier 2A; $\ge 12.0 \rightarrow$ Tier 2B. Rituals ép $A = 1.0$.
- **RULE-1.2 [ADR 0053 — Single-Writer Protocol]**: Đa tác tử: Lead duy nhất ghi codebase/logs; subagents chỉ xuất PatchBlocks. Hợp nhất qua `execute_swarm_patches`.
- **RULE-1.3 [ADR 0035 — Deep Modules, Seams & Zero-Exemption AST]**: Thin Seam: Package chỉ bộc lộ `__all__`/`__init__.py`, cấm import `_*`. Gỡ bypass trong `check_dependency_contracts.py`.
- **RULE-1.4 [ADR 0033 & ADR 0056 — Directory Hygiene]**: `.\.md\`: Gốc chỉ chứa `workspace_context.yaml`, `extracted_docs/`, `knowledge/`, `archive/`.
- **RULE-1.5 [ADR 0037 & ADR 0051 — Traceability Matrix]**: Giữ qua `<!-- CUSTOM_SECTIONS_START -->`...`<!-- CUSTOM_SECTIONS_END -->`. Regex status: `(?:\*|-)?\s*\*\*\s*Status:\s*\*\*`.
- **RULE-1.6 [ADR 0044 — Federated RAG & Dynamic Import]**: Dynamic import: `try: from ccba_legal.xxx import yyy; except ImportError: pass`. Cache BM25 Singleton, `.npy` kèm `.sha256`.
- **RULE-1.7 [ADR 0046 — Sanitized Fleet Telemetry]**: Chỉ trích xuất số liệu phi định danh (`tokens`, `cost`). Cấm log prompt/dữ liệu khách hàng.
- **RULE-1.8 [ADR 0058 — Discrete Diagnostic Commands]**: `SelfHealingEngine`: mảng lệnh độc lập (`["c1", "c2"]`), CẤM ghép `&&` (< 500ms).
- **RULE-1.9 [Corpus Discovery]**: Quét `project_root` qua `reg_parent/{, .md/}legal_docs`, `project_root/{, .md/}legal_docs`.
- **RULE-1.10 [ADR 0057 — Skill Promotion Triad]**: Tier 2A $\rightarrow$ Tier 2B: (1) Xóa triggers trùng; (2) Trỏ alias ngắn; (3) Tách Hub vs Spoke.
- **RULE-1.11 [Diagramming Hygiene]**: Mermaid: Subgraph dùng `style <id>`, cấm `classDef`. Nhãn `["..."]`, ngắt `<br/>`. D2/Kroki: SVG.
- **RULE-1.12 [Model-Invocation Budget & Cognitive Skills]**: Trần 10 model-invoked skills/bundle (ADR-0040). Kỹ năng tư duy (`ccba-issue-tree`) gán `disable-model-invocation: true` không tốn tokens.
- **RULE-1.13 [Cross-Platform Default Branch Resolution]**: `ccba-create-pr` cấm hardcode `main`. Dò qua `git symbolic-ref --short refs/remotes/origin/HEAD` hoặc fallback `origin/main`.
- **RULE-1.14 [ADR 0050 & ADR 0051 — Hub-Mediated Spoke Discovery & Virtual-First Retrieval]**:
  - Spoke chỉ cần `hub_path`. SDK tự tra `spoke_registry_decrypted.yaml` trên Hub định vị `ccba-legal-knowledge`.
  - Phân giải 3 tầng: T1 (CLI `get-clause`/`.\.md\legal_docs\`) $\rightarrow$ T2 (Master Registry) $\rightarrow$ T3 (SSOT `legal_registry.yaml`). Cấm copy cả kho luật về Spoke (tránh nghẽn OneDrive).

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Testing)

- **RULE-2.1 [Strict Mypy Type-Safety — Chống AP9.1]**: CẤM `ignore_errors = true`. Ép kiểu binary I/O, dicts. Chỉ dùng `ignore_missing_imports = true` khi thiếu stubs.
- **RULE-2.2 [Spoke CI Gates Verification Pipeline]**: 5 Cổng CI: `lint_visual_parity`, `validate_legal_spoke`, `test_converter_regression`, `verify_all_docs_against_pdf` (SHA-256), `verify_cross_links`.
- **RULE-2.3 [Fast Feedback Loops (< 2s) & Parity Contract Tests]**: Tests $< 2\text{s}$ (`pytest -m fast`). `test_cli_doc_parity.py`: Khớp 100% CLI và `SKILL.md`.
- **RULE-2.4 [Relative Link Resolution Depth]**: `SKILL.md` trỏ pkg 3 cấp `../../../packages/`; `references/` trỏ root 4 cấp. CẤM link `file:///` hay `conversation://`.
- **RULE-2.5 [Windows Subprocess UTF-8 Encoding Standard]**: `subprocess.run(..., text=True)` trên Windows: `encoding="utf-8", errors="replace"`.
- **RULE-2.7 [Safe-Remove & Read-Only Cleanup]**: `safe_remove`: Check `is_symlink() or is_file()`, `chmod(0o666)` trước xóa; tránh `NotADirectoryError`.
- **RULE-2.8 [Offline XML/OOXML Validation]**: `lxml`: Nhúng schema offline, XMLParser(no_network=True, resolve_entities=False).
- **RULE-2.9 [Flaky Test Root-Cause Transparency]**: Test retry PASS chưa sửa mã: CẤM coi là đã sửa xong. Phải tìm gốc rễ.
- **RULE-2.10 [Git Simplify Gate Bypass]**: `simplify_gate` chặn diff $> 400$ LOC, $> 8$ files. Commit thêm `# APPROVED: <lý_do>`.
- **RULE-2.11 [CI Mock Isolation & Drift Auditor Path Normalization]**: CI `.github/workflows/ci.yml` duy trì `CCBA_AI_MOCK: "1"`. `drift_auditor.py` loại trừ `not filepath.startswith("tests/") and "/tests/" not in filepath`.
- **RULE-2.12 [Deterministic Completion, Fail-Fast Security & Socket Safety]**:
  - ADR-0058 Hard Completion: CLI `sync` khi `len(bundles_synced) == 0` hoặc fallback cloud BẮT BUỘC exit 1.
  - Fail-Fast Maskara: Chặn API keys đầu `query_rag()`. Socket: `is_port_open` clamp `timeout <= 1.0s` an toàn Windows.

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu (Legal & Data Standards)

- **RULE-3.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - MỌI VB viện dẫn BẮT BUỘC ĐANG CÓ HIỆU LỰC (CURRENT). Chặn LLM Legacy Bias.
  - HIỆN HÀNH: **Luật Xây dựng 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP** (thay NĐ 175 & 15), **NĐ 207/2026/NĐ-CP** (thay NĐ 06). CẤM VB hết hiệu lực.
- **RULE-3.2 [TVPL VIP 3-Tier Download Priority — ADR 0031]**: Tier 1 (`part=-100`): VIP Vector PDF. Tier 2 (`part=-1&docx=1`): VIP Word (`docx_converter.py`). Tier 3 (`part=0`): Gazette Scan PDF.
- **RULE-3.3 [Làm Sạch Bảng Biểu & Chú Thích Pháp Lý]**: Footnote: `re.sub(r"^[0-9]+[)\.]\s*", "", fn_clean).strip()`. Bảng qua tiêu đề và `| :--- |`.
- **RULE-3.4 [ADR 0059 — Cưỡng Chế Nguyên Văn & Chống Bịa Đặt Dữ Liệu Pháp Lý]**:
  - CẤM tự suy diễn/bịa đặt VBPL; trích dẫn nguyên văn 100%.
  - Thiếu tệp gốc: dùng `TVPLCrawler` tải PDF/DOCX chính thức, đóng dấu SHA-256 (`pdf_sha256`), kiểm `validate_bundle_provenance()`.
- **RULE-3.5 [Deep Seam CLI Retrieval Over Raw File Ingestion]**: Agent gọi CLI `python -m ccba_legal get-clause --doc <id> --clause <id>` trích xuất AST (< 500 tokens) thay vì dùng `view_file` mở file MD thô (~60k tokens).

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent (Workflows & Review)

- **RULE-4.1 [Entry Point Duy Nhất Khi Có Issue ID: `/ccba-new-feature`]**: Có Issue ID, LUÔN gọi `/ccba-new-feature #<id>` (8 bước Factory Model). CẤM làm tắt.
- **RULE-4.2 [Slash Command Parity & Active Commands SSOT]**: Đối chiếu `catalog.yaml` trước khi đề xuất `/command`. Chỉ kỹ năng có `command: /...` mới gắn `/`. `references/*.md` CẤM dùng `/`.
- **RULE-4.3 [Tiêu Chí Hoàn Thành Đa Nhánh & DRY Reference]**: Tiêu chí hoàn thành phải kiểm chứng từng cờ (`--compare`, `--port`, `--improve`, `--copy-raw`).
- **RULE-4.4 [GitHub Copilot Review Gating & Walkthrough Mirroring]**: Báo cáo nghiệm thu ghi `review_id`/`id` vào `.md/knowledge/reports/walkthrough.md`.
- **RULE-4.5 [AI Gateway Spark Auth & Fast-Inference Gating]**: LiteLLM Spark: Bearer `sk-spark-secure-key-2026`. Ưu tiên `gemini-3.7-flash` (< 1s), route `qwen-local-primary`.
- **RULE-4.6 [Tier 3 Orchestrator & Deterministic Verification Gating — ADR-0057 / ADR-0058]**: SSOT tại `.agents/skills/ccba-platform/SKILL.md`, Single-Writer. Spoke sync kích hoạt `ccba-harness verify-patch`.
- **RULE-4.7 [ArtifactMetadata Workspace Invariant]**: `ArtifactMetadata` CHỈ dùng cho brain (`<appDataDir>\brain\<id>/`). Bỏ qua khi ghi workspace.
- **RULE-4.8 [Zero-Polling & Reactive Wakeup Hard Invariant]**: CẤM polling loop `manage_task(status)`. Dừng tool để runtime tự đánh thức qua Reactive Wakeup.
- **RULE-4.9 [RSA-OAEP Length & Decoupled Telemetry Heartbeat — ADR-0046]**: RSA-2048 OAEP plaintext $\le 190$ bytes. Tách metadata tĩnh (`static_hash`) khỏi telemetry (`.md/telemetry/spoke_heartbeats.yaml` gitignored).
- **RULE-4.10 [ADR-0045 Spoke Leakage Guard & Report Mirroring Location]**: Gốc `.md/` CHỈ chứa `workspace_context.yaml`. Báo cáo nghiệm thu BẮT BUỘC tại `.md/knowledge/reports/walkthrough.md` (CẤM tại `.md/walkthrough.md`).
- **RULE-4.11 [OpenAI SDK Embedding & Reasoning Timeout Scaling]**: `embed()`: `extra_body={"drop_params": True}` (`gemini-embedding-2`). Reasoning: sàn `max_tokens` $\ge 16,384$, auto-timeout `max(timeout, max_tokens/50.0)`.
- **RULE-4.12 [Cross-Skill Referral Hooks & Concept-Level Invariants]**: Tích hợp qua Referral Hooks tại rẽ nhánh. Dùng định danh khái niệm ("các Ghế CCBA", "ma trận RACI") chống drift.
- **RULE-4.13 [Cross-Shell PR Body Variable Formatting]**: `gh pr create`: Truyền nội dung qua biến môi trường (`--body "$PR_BODY"`). CẤM escape `\n` trần trong quotes hoặc PowerShell `` `n `` trong bash blocks.

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows & Tooling)

- **RULE-5.1 [Chromium VIP Session Engine & CDP Browser Target]**: Profile `~/.gemini/antigravity/chrome_vip` cổng 9222. `Browser.setDownloadBehavior` qua WebSocket.
- **RULE-5.2 [Windows Path Quotes & Hook Protection]**: Windows: IDE bọc `hooks.json` trong `"C:\..."` $\rightarrow$ vô hiệu bằng `{}` và khóa `IsReadOnly = $true` trên PowerShell. Timeout $\ge 60\text{s}$.
- **RULE-5.3 [Query Sanitization & Turnstile Bypass]**: Query TVPL: thay `/`, `:`, `-` bằng dấu cách (`quote_plus`) chống lỗi IIS mã hóa `%2F`.
- **RULE-5.4 [Upstream Git Engine Windows Safety]**: Git Windows: Mutex `.md/scratch/upstream_sync.lock`; chữa stale `index.lock`; `safe_rmtree` với `chmod(0o666)`.
