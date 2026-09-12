# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants (Compacted Working Memory)

> **Phạm vi áp dụng:** Hub (`ccba-agent-platform`) & Spokes (`ccba-legal-knowledge`, etc.) | OKF v2.2, ADR 0016-0058  
> **Tra cứu Chi tiết Lịch sử & Bug Post-Mortems:** [session_learnings_history.md](archive/session_learnings_history.md) | Ngưỡng bộ nhớ: $\le 10\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc, Phân Tầng Kỹ Năng & Quản Trị Seams (Architecture & Governance)

- **RULE-1.1 [ADR 0057 — Khung 2 Giai Đoạn & Chỉ Số GPI]**:
  - Cổng 0 (Determinism): Giải thuật/IO $\rightarrow$ Deep Seams (`packages/*/src/`). `SKILL.md` cấm code logic trần.
  - Cổng 1 (Orchestration): Đa luồng/StateGraph/HITL $\rightarrow$ Tier 3 Composite Orchestrator (không tính GPI).
  - $\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$. $\text{GPI} < 12.0 \rightarrow$ Tier 2A (`references/`); $\ge 12.0 \rightarrow$ Tier 2B (`.agents/skills/ccba-<name>/`). Rituals (`disable-model-invocation: true`) ép $A = 1.0$.
- **RULE-1.2 [ADR 0053 — Single-Writer Protocol Cho Orchestrators]**:
  - Đa tác tử (`ccba-teamwork`, swarms) bắt buộc Single-Writer: Lead duy nhất ghi codebase/logs; subagents chỉ xuất PatchBlocks vào sandbox. Hợp nhất qua `execute_swarm_patches`.
- **RULE-1.3 [ADR 0035 — Deep Modules, Seams & Zero-Exemption AST]**:
  - Thin Seam: Package chỉ bộc lộ `__all__`/`__init__.py`, cấm import private `_*`. Gỡ bypass hardcoded trong `check_dependency_contracts.py`. Tệp thử nghiệm vào `archive/`.
- **RULE-1.4 [ADR 0033 & ADR 0056 — Spoke Directory Hygiene & Zombie Prevention]**:
  - Cấu trúc `.\.md\`: Gốc chỉ chứa cấu hình (`workspace_context.yaml`); `extracted_docs/`; `knowledge/`; `archive/`.
  - Spoke Synchronizer (`coordinator.py`): Đổi workflows cũ thành `.md.bak` (`DEPRECATED_MIGRATED_TO_SKILL`), xóa thư mục theo `SKILL_DEPRECATION_ALIASES`.
- **RULE-1.5 [ADR 0037 & ADR 0051 — Two-Tier Traceability Matrix & Status Regex]**:
  - Tier 1: Hub Constitution (55 ADRs). Tier 2: Spoke Domain (`docs/adr/`). Giữ bảng qua `<!-- CUSTOM_SECTIONS_START -->`...`<!-- CUSTOM_SECTIONS_END -->`.
  - Regex trạng thái ADR: `(?:\*|-)?\s*\*\*\s*Status:\s*\*\*`. Lọc bỏ file non-ADR (`notes.md`, `template.md`).
- **RULE-1.6 [ADR 0044 — Federated RAG & Dynamic Import]**:
  - Tier 0 import Tier 1 dùng `try: from ccba_legal.xxx import yyy; except ImportError: pass`. Cache BM25 Singleton module; Cache Embedding `.npy` đối chiếu sidecar `.sha256`.
- **RULE-1.7 [ADR 0046 — Sanitized Fleet Telemetry Protocol]**:
  - Telemetry Spoke $\rightarrow$ Hub: Chỉ trích xuất số liệu phi định danh (`tokens`, `cost`, `tool_counts`, `status`). Cấm thu thập prompt text/dữ liệu khách hàng.
- **RULE-1.8 [ADR 0058 — Self-Healing Engine & Discrete Diagnostic Commands]**:
  - Lệnh nạp `SelfHealingEngine` (`verify-patch --self-heal`) BẮT BUỘC là mảng lệnh độc lập (`["cmd1", "cmd2"]`), CẤM ghép chuỗi `&&` để regex chẩn đoán đúng và tự phục hồi (< 500ms).
- **RULE-1.9 [Multi-Tier Corpus Discovery & Layout Normalization]**:
  - Quét corpus từ registry trong `.md/data/`: suy luận `project_root` (3 cấp lùi nếu ở `.md/data`) và quét 4 ứng viên: `reg_parent/{, .md/}legal_docs`, `project_root/{, .md/}legal_docs`.

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Strict Testing)

- **RULE-2.1 [Strict Mypy Type-Safety — Chống Anti-Pattern AP9.1]**:
  - CẤM `ignore_errors = true`. Ép kiểu tường minh cho binary I/O, fonts, dicts. Chỉ dùng `ignore_missing_imports = true` cho 3rd-party thiếu stubs.
- **RULE-2.2 [Spoke CI Gates Verification Pipeline]**:
  - 5 Cổng bắt buộc: (1) `lint_visual_parity.py`, (2) `validate_legal_spoke.py`, (3) `test_converter_regression.py`, (4) `verify_all_docs_against_pdf.py` (SHA-256), (5) `verify_cross_links.py`.
- **RULE-2.3 [Fast Feedback Loops (< 2s) & Parity Contract Tests]**:
  - Unit tests nòng cốt phải $< 2\text{s}$ (`pytest -m fast`). `test_cli_doc_parity.py`: Khớp 100% CLI và `SKILL.md`. `drift_auditor.py`: Miễn trừ `scripts/tests/` chống cảnh báo giả.
- **RULE-2.4 [Relative Link Resolution Depth]**:
  - `.agents/skills/<skill>/SKILL.md` trỏ package dùng 3 cấp lùi `../../../packages/<pkg>`; `references/` trỏ root dùng 4 cấp `../../../../`. CẤM commit URI `file:///` hoặc `conversation://`.
- **RULE-2.5 [Windows Subprocess UTF-8 Encoding Standard]**:
  - `subprocess.run(..., text=True)` trên Windows mặc định `cp1252`. BẮT BUỘC `encoding="utf-8", errors="replace"` chống `UnicodeDecodeError` khi đọc stdout tiếng Việt/box-drawing.
- **RULE-2.7 [Safe-Remove, Read-Only & Symlink Cleanup Invariant]**:
  - `safe_remove`: Trên Windows symlink ném `NotADirectoryError` nếu dùng `shutil.rmtree()`. Kiểm tra `is_symlink() or is_file()` trước, gỡ read-only bằng `chmod(0o666)`, rồi mới gọi `rmtree()`.
- **RULE-2.8 [Hardened Offline XML/XSD Validation & Schema Caching]**:
  - XML/OOXML (`lxml`): CẤM tải `schemaLocation` qua HTTP $\rightarrow$ nhúng schema offline và dùng `lxml.etree.Resolver`. `XMLParser(no_network=True, resolve_entities=False)` chống DTD/XXE leaks. Cache `XMLSchema` (`_COMPILED_SCHEMA_CACHE`) theo đường dẫn tránh nghẽn CPU.
- **RULE-2.9 [Flaky Test Root-Cause Transparency & No-False-Pass Lock]**:
  - Test FAIL rồi PASS khi retry chưa sửa mã: CẤM kết luận đã sửa xong. Bắt buộc tìm cội nguồn kỹ thuật và giải trình minh bạch trước release.

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu Hiện Hành (Legal & Data Standards)

- **RULE-3.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - MỌI văn bản pháp luật viện dẫn BẮT BUỘC ĐANG CÓ HIỆU LỰC (CURRENT). Chặn đứng LLM Legacy Bias bằng bộ lọc pre-check trước khi xuất báo cáo kỹ thuật.
  - VĂN BẢN HIỆN HÀNH: **Luật Xây dựng 2025** (`135/2025/QH15`), **Nghị định 217/2026/NĐ-CP** (thay NĐ 175/2024 & NĐ 15/2021), **Nghị định 207/2026/NĐ-CP** (thay NĐ 06/2021). CẤM dùng văn bản hết hiệu lực.
- **RULE-3.2 [TVPL VIP 3-Tier Download Priority — ADR 0031]**:
  - Tier 1 (`part=-100`): VIP Digital Vector PDF (Mỏ neo Pháp lý). Tier 2 (`part=-1&docx=1`): VIP OpenXML Word Document (cho `docx_converter.py`). Tier 3 (`part=0`): Gazette Scan PDF.
- **RULE-3.3 [Làm Sạch Bảng Biểu & Chú Thích Pháp Lý]**:
  - Footnote: Khử lặp số thứ tự: `re.sub(r"^[0-9]+[)\.]\s*", "", fn_clean).strip()`. Bảng Markdown nhận diện qua tiêu đề và phân cách `| :--- |`.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent (Workflows, Commands & Review)

- **RULE-4.1 [Entry Point Duy Nhất Khi Có Issue ID: `/ccba-new-feature`]**:
  - Khi có Issue ID, LUÔN đề xuất `/ccba-new-feature #<id>` làm bước tiếp theo (8 bước Factory Model). CẤM nhảy thẳng implement.
- **RULE-4.2 [Slash Command Parity & Active Commands SSOT]**:
  - BẮT BUỘC đối chiếu `catalog.yaml` trước khi đề xuất `/command`. Chỉ kỹ năng có `command: /...` mới gắn tiền tố `/`.
  - Tài liệu `references/*.md` (Tier 2A) CẤM dùng tiền tố `/` (gọi Master Skill kèm reference).
- **RULE-4.3 [Tiêu Chí Hoàn Thành Đa Nhánh & DRY Reference]**:
  - Tiêu chí hoàn thành phải có nhánh kiểm chứng cho từng cờ (`--compare`, `--port`, `--improve`, `--copy-raw`). Quy tắc kết hợp cờ chỉ tuyên bố tại `Kết hợp không hợp lệ` trong `MODES.md`.
- **RULE-4.4 [GitHub Copilot Multi-Tier Review Gating & Workspace Walkthrough Mirroring]**:
  - Quét `author.login` thay vì `user.login`. Bắt buộc kiểm tra `### 🟡 Changes recommended` và review `body` của Copilot kể cả khi là `COMMENTED`. Cấm merge nếu chưa sửa hoặc giải trình.
  - `audit_pr_comments.py` chỉ đọc `Path.cwd() / "walkthrough.md"` (HUB-ADR-0058): BẮT BUỘC ghi nhận `review_id` (`PRR_...`) và inline comment `id` trực tiếp vào `walkthrough.md` tại gốc repo để vượt qua chốt chặn audit.
- **RULE-4.5 [AI Gateway Spark Auth & Fast-Inference Gating]**:
  - LiteLLM Server Spark (100.83.192.30:8090): Header `Authorization: Bearer sk-spark-secure-key-2026`. Ưu tiên `gemini-3.7-flash` (< 1s), route `qwen-local-primary` sau GPU warmup.
- **RULE-4.6 [Tier 3 Orchestrator & Deterministic Verification Gating — ADR-0057 / ADR-0058]**:
  - Router/Orchestrator (`/ccba-platform`): bản ghi SSOT tại `.agents/skills/ccba-platform/SKILL.md` (`tier: orchestrator`, `bundle: _core`, `is-orchestrated: true`), tuân thủ Single-Writer Protocol.
  - Đồng bộ Spoke (`sync_spoke.py`): cờ `--verify` kích hoạt `ccba-harness verify-patch` sau ghi đĩa, khóa cứng nếu lỗi.
- **RULE-4.7 [ArtifactMetadata Workspace Invariant]**:
  - `ArtifactMetadata` CHỈ hợp lệ cho tệp artifact trong thư mục brain (`<appDataDir>\brain\<id>/`). Bỏ qua trường này khi ghi code/docs trong workspace chống schema rejection.

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows, Chrome CDP & Tooling)

- **RULE-5.1 [Chromium VIP Session Engine & CDP Browser Target]**:
  - Chromium VIP: Profile `~/.gemini/antigravity/chrome_vip` cổng `9222`. `Browser.setDownloadBehavior` gọi qua WebSocket (`http://127.0.0.1:{port}/json/version`). Selectors tập trung trong `selectors.py`.
- **RULE-5.2 [Windows Path Quotes & Hook Protection]**:
  - Windows: IDE tự bọc `hooks.json` trong `"C:\..."` $\rightarrow$ vô hiệu bằng `{}` và khóa `IsReadOnly = $true` trên PowerShell. Timeout $\ge 60\text{s}$ cho tests trên Windows.
- **RULE-5.3 [Query Sanitization & Turnstile Bypass]**:
  - Query TVPL có dấu `/`, `:`, `-` phải thay bằng dấu cách (`quote_plus`) chống lỗi IIS mã hóa `%2F`.
