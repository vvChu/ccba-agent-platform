# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants (Compacted Working Memory)

> **Phạm vi:** Hub & Spokes | OKF v2.2, ADR 0016-0058 | [session_learnings_history.md](archive/session_learnings_history.md)

---

## Miền 1. 🏛️ Kiến Trúc & Phân Tầng Kỹ Năng (Architecture & Governance)

- **RULE-1.1 [ADR 0057 — Khung 2 Giai Đoạn & GPI]**: Cổng 0: Deep Seams (`packages/*/`). Cổng 1: Tier 3 Orchestrator. $\mathbf{GPI} = 2.5S + 2K + 2A - 1.5P$. $< 12.0 \rightarrow$ Tier 2A; $\ge 12.0 \rightarrow$ Tier 2B.
- **RULE-1.2 [ADR 0053 — Single-Writer Protocol]**: Đa tác tử: Duy nhất Lead ghi codebase/logs; subagents xuất PatchBlocks. Hợp nhất qua `execute_swarm_patches`.
- **RULE-1.3 [ADR 0035 — Deep Modules & Zero-Exemption AST]**: Thin Seam: Package chỉ bộc lộ `__all__`/`__init__.py`, cấm import `_*`. Gỡ bypass trong `check_dependency_contracts.py`.
- **RULE-1.4 [ADR 0033 & ADR 0056 — Directory Hygiene]**: `.\.md\`: Gốc chỉ chứa `workspace_context.yaml`, `extracted_docs/`, `knowledge/`, `archive/`.
- **RULE-1.5 [ADR 0037 & ADR 0051 — Traceability Matrix]**: Giữ qua `<!-- CUSTOM_SECTIONS_START -->`...`<!-- CUSTOM_SECTIONS_END -->`. Regex: `(?:\*|-)?\s*\*\*\s*Status:\s*\**`.
- **RULE-1.6 [ADR 0044 — Federated RAG & Dynamic Import]**: Dynamic import `ccba_legal`. Cache BM25 Singleton, `.npy` kèm `.sha256`.
- **RULE-1.7 [ADR 0046 — Fleet Telemetry]**: Trích xuất phi định danh (`tokens`, `cost`). Cấm log prompt/dữ liệu khách hàng.
- **RULE-1.8 [ADR 0058 — Discrete Diagnostic Commands]**: `SelfHealingEngine`: mảng lệnh độc lập (`["c1", "c2"]`), CẤM ghép `&&` (< 500ms).
- **RULE-1.9 [Corpus Discovery]**: Quét `project_root` qua `reg_parent/{, .md/}legal_docs`, `project_root/{, .md/}legal_docs`.
- **RULE-1.10 [ADR 0057 — Skill Promotion]**: Tier 2A $\rightarrow$ 2B: (1) Xóa triggers trùng; (2) Trỏ alias ngắn; (3) Tách Hub vs Spoke.
- **RULE-1.11 [Diagrams]**: Mermaid: Subgraph dùng `style <id>`, cấm `classDef`. Nhãn `["..."]`.
- **RULE-1.12 [Cognitive Skills Budget]**: Trần 10 skills/bundle (ADR-0040). Kỹ năng tư duy (`ccba-issue-tree`) gán `disable-model-invocation: true`.
- **RULE-1.13 [Default Branch Resolution]**: `ccba-create-pr` cấm hardcode `main`: Dò `git symbolic-ref --short refs/remotes/origin/HEAD` hoặc fallback `origin/main`.
- **RULE-1.14 [ADR 0050/0051 — Spoke Discovery]**: Spoke đọc `hub_path`, tra `spoke_registry_decrypted.yaml`. 3 tầng: T1 (CLI `get-clause`) $\rightarrow$ T2 (Registry) $\rightarrow$ T3 (SSOT `legal_registry.yaml`).

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Testing)

- **RULE-2.1 [Strict Mypy Type-Safety]**: CẤM `ignore_errors = true`. Ép kiểu binary I/O, dicts. Chỉ dùng `ignore_missing_imports = true` khi thiếu stubs.
- **RULE-2.2 [Spoke CI Gates]**: 5 Cổng CI: `lint_visual_parity`, `validate_legal_spoke`, `test_converter_regression`, `verify_all_docs_against_pdf` (SHA-256), `verify_cross_links`.
- **RULE-2.3 [Fast Loops (< 2s) & Parity Tests]**: Tests $< 2\text{s}$ (`pytest -m fast`). `test_cli_doc_parity.py`: Khớp 100% CLI và `SKILL.md`.
- **RULE-2.4 [Relative Link Resolution Depth]**: `SKILL.md` trỏ pkg 3 cấp `../../../packages/`; `references/` trỏ root 4 cấp. CẤM link `file:///`.
- **RULE-2.5 [Windows Subprocess UTF-8 Standard]**: `subprocess.run(..., text=True)` trên Windows: `encoding="utf-8", errors="replace"`.
- **RULE-2.7 [Safe-Remove & POSIX +x]**: `safe_remove`: Win junction (`0x400`) dùng `rmdir`, cấm đệ quy link. `_make_writable`: Giữ `+x` (`st_mode | S_IWUSR`), cấm mode tĩnh `0o600` trên POSIX dirs.
- **RULE-2.8 [Offline XML/OOXML Validation]**: `lxml`: Nhúng schema offline, XMLParser(no_network=True, resolve_entities=False).
- **RULE-2.9 [Flaky Test Root-Cause Transparency]**: Test retry PASS chưa sửa mã: CẤM coi là đã sửa xong. Phải tìm gốc rễ.
- **RULE-2.10 [Git Simplify Gate Bypass]**: `simplify_gate` chặn diff $> 400$ LOC, $> 8$ files. Commit thêm `# APPROVED: <lý_do>`.
- **RULE-2.11 [CI Mock & Drift Auditor]**: CI duy trì `CCBA_AI_MOCK: "1"`. `drift_auditor.py` loại trừ `not filepath.startswith("tests/") and "/tests/" not in filepath`.
- **RULE-2.12 [Deterministic Completion & Socket Safety]**: Hard Completion: CLI `sync` khi 0 bundle BẮT BUỘC exit 1. Maskara: chặn keys đầu `query_rag()`. Socket clamp `timeout <= 1.0s` trên Windows.
- **RULE-2.13 [Tuner Circuit Breaker & Compaction]**: `LLMTaskAdapter` default `CircuitBreaker()`. Caller ghi đè env budget. Prompt compaction (> 300 dòng) strip comments & bullets `- Cập nhật quy chuẩn...`.
- **RULE-2.14 [Gate 1b Ruff Check]**: BẮT BUỘC chạy `ruff check .` và `ruff format --check .` trước khi push (Gate 1b chặn trên 3.10/3.11/3.12).
- **RULE-2.15 [Architecture Drift Guard]**: Code mới trong `packages/*/` BẮT BUỘC cập nhật `README.md`/`PLATFORM.md` tránh CI `validate-docs` chặn (Exit 1).
- **RULE-2.16 [TRIHT Post-Gate Teardown]**: Cổng 0.3 chặn tệp tracked bị sửa ngoài cache (`.md/data/*.yaml`); BẮT BUỘC revert trước release.
- **RULE-2.17 [Word COM Single-Pass & Layout Guard]**: Điền `.doc`/`.docx` qua DOM Cell/Range; ép `AllowBreakAcrossPages = False` / `<w:cantSplit/>`; thu hồi `WINWORD.EXE` trong `finally`.

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu (Legal & Data Standards)

- **RULE-3.1 [Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**: VB viện dẫn BẮT BUỘC CURRENT: **Luật XD 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP** (thay NĐ 175/15), **NĐ 207/2026/NĐ-CP** (thay NĐ 06). CẤM VB hết hiệu lực.
- **RULE-3.2 [TVPL VIP 3-Tier Download — ADR 0031]**: Tier 1 (`part=-100`): VIP PDF. Tier 2 (`part=-1&docx=1`): VIP Word (`docx_converter.py`). Tier 3 (`part=0`): Gazette Scan PDF.
- **RULE-3.3 [Làm Sạch Bảng Biểu & Chú Thích]**: Footnote: `re.sub(r"^[0-9]+[)\.]\s*", "", fn_clean).strip()`. Bảng qua tiêu đề và `| :--- |`.
- **RULE-3.4 [ADR 0059 — Nguyên Văn 100% & Chống Bịa Đặt]**: CẤM bịa đặt VBPL. Thiếu tệp: dùng `TVPLCrawler` tải PDF/DOCX chính thức, đóng dấu SHA-256 (`pdf_sha256`), kiểm `validate_bundle_provenance()`.
- **RULE-3.5 [Deep Seam CLI Retrieval]**: Dùng `python -m ccba_legal get-clause --doc <id> --clause <id>` (< 500 tokens) thay vì `view_file` file MD thô (~60k tokens).

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent (Workflows & Review)

- **RULE-4.1 [Entry Point Duy Nhất: `/ccba-new-feature`]**: Có Issue ID, LUÔN gọi `/ccba-new-feature #<id>` (8 bước Factory Model). CẤM làm tắt.
- **RULE-4.2 [Slash Command Parity & SSOT]**: Tra `catalog.yaml` trước khi đề xuất `/command`. Chỉ kỹ năng có `command: /...` mới gắn `/`. `references/*.md` CẤM dùng `/`.
- **RULE-4.3 [Tiêu Chí Hoàn Thành Đa Nhánh]**: Tiêu chí hoàn thành phải kiểm chứng từng cờ (`--compare`, `--port`, `--improve`).
- **RULE-4.4 [Copilot Review Gating]**: Báo cáo nghiệm thu ghi `review_id`/`id` vào `.md/knowledge/reports/walkthrough.md`.
- **RULE-4.5 [AI Gateway Spark Auth]**: LiteLLM Spark: Bearer `${SPARK_API_KEY}` (qua env). Ưu tiên `gemini-3.7-flash` (< 1s), route `qwen-local-primary`.
- **RULE-4.6 [Tier 3 Orchestrator — ADR-0057/0058]**: SSOT tại `.agents/skills/ccba-platform/SKILL.md`, Single-Writer. Spoke sync gọi `ccba-harness verify-patch`.
- **RULE-4.7 [ArtifactMetadata Invariant]**: `ArtifactMetadata` CHỈ dùng cho brain (`<appDataDir>\brain\<id>/`). Bỏ qua khi ghi workspace.
- **RULE-4.8 [Zero-Polling Hard Invariant]**: CẤM polling loop `manage_task(status)`. Dừng tool để runtime tự đánh thức qua Reactive Wakeup.
- **RULE-4.9 [RSA-OAEP & Telemetry — ADR-0046]**: RSA-2048 OAEP plaintext $\le 190$ bytes. Tách metadata tĩnh khỏi telemetry (`.md/telemetry/spoke_heartbeats.yaml`).
- **RULE-4.10 [ADR-0045 Spoke Leakage Guard & Walkthrough]**: Gốc `.md/` CHỈ chứa `workspace_context.yaml`. Nghiệm thu tại `.md/knowledge/reports/walkthrough.md` (CẤM tại `.md/walkthrough.md`).
- **RULE-4.11 [Embedding & Reasoning Timeout Scaling]**: `embed()`: `extra_body={"drop_params": True}`. Reasoning: `max_tokens` $\ge 16,384$, auto-timeout `max(timeout, max_tokens/50.0)`.
- **RULE-4.12 [Referral Hooks & Concept Invariants]**: Tích hợp qua Referral Hooks tại rẽ nhánh. Dùng định danh khái niệm ("các Ghế CCBA", "ma trận RACI") chống drift.
- **RULE-4.13 [PR Body]**: `gh pr create`: Body qua env (`--body "$PR_BODY"`). CẤM escape `\n` trong quotes.
- **RULE-4.14 [Merge Danger]**: Phân loại: Door (`Two-way`/`One-way`), Blast Radius (`Localized`/`Package-wide`/`Monorepo-wide`/`Spoke-affecting`).
- **RULE-4.15 [Self-Healing PR CLI & Scoped Tuner]**: `gh pr create` fallback retry không nhãn khi lỗi. Tuner hỗ trợ `--skill <name>` chạy kiểm thử mẻ nhỏ.
- **RULE-4.16 [Admin Squash Merge Bypass]**: Base branch policy chặn merge: dùng `gh pr merge --squash --delete-branch --admin` khi 100% CI xanh & Copilot review sạch.

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows & Tooling)

- **RULE-5.1 [Chromium VIP Session & CDP Target]**: Profile `~/.gemini/antigravity/chrome_vip` cổng 9222. `Browser.setDownloadBehavior` qua WebSocket.
- **RULE-5.2 [Windows Path]**: Windows: IDE bọc `hooks.json` `"C:\..."` $\rightarrow$ vô hiệu `{}` và khóa `IsReadOnly = $true`.
- **RULE-5.3 [Query Sanitization & Turnstile Bypass]**: Query TVPL: thay `/`, `:`, `-` bằng space (`quote_plus`) chống lỗi IIS mã hóa `%2F`.
- **RULE-5.4 [Upstream Git Engine Windows Safety]**: Git Win: Mutex `.md/scratch/upstream_sync.lock`; chữa `index.lock`; dọn bằng `safe_remove` (RULE-2.7).
- **RULE-5.5 [Worktree Isolation & Git Safety]**: Worktree: `cd "$WORKTREE_DIR"` trước export `PYTHONPATH`. Dọn nhánh: check `diff_res.returncode == 0` trước khi đối soát.
