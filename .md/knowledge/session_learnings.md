# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants (Compacted Working Memory)

> **Phạm vi áp dụng:** Hub (`ccba-agent-platform`) & Spokes (`ccba-legal-knowledge`, etc.)  
> **Tiêu chuẩn:** OKF v2.2, ADR 0016, 0021, 0030, 0031, 0033, 0035, 0037, 0046, 0051, 0053, 0056, 0057.  
> **Tra cứu Chi tiết Lịch sử & Bug Post-Mortems:** [session_learnings_history.md](archive/session_learnings_history.md) | Ngưỡng bộ nhớ: $\le 10\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc, Phân Tầng Kỹ Năng & Quản Trị Seams (Architecture & Governance)

- **RULE-1.1 [ADR 0057 — Khung 2 Giai Đoạn & Chỉ Số GPI]**:
  - *Cổng 0 (Determinism)*: Tác vụ thuần giải thuật/I/O $\rightarrow$ chuyển xuống Monorepo Package Deep Seams (`packages/*/src/`). Kỹ năng `SKILL.md` tuyệt đối không chứa code logic nghiệp vụ trần.
  - *Cổng 1 (Orchestration)*: Tác vụ đa luồng/StateGraph/HITL $\rightarrow$ chuyển lên Tier 3 Composite Orchestrator (short-circuit Cổng 1, không tính GPI).
  - *Công thức GPI*: $\mathbf{GPI} = (S \times 2.5) + (K \times 2.0) + (A \times 2.0) - (P \times 1.5)$. Nếu $\text{GPI} < 12.0 \rightarrow$ Tier 2A (`references/*.md`); Nếu $\text{GPI} \ge 12.0 \rightarrow$ Tier 2B (`.agents/skills/ccba-<name>/`). User Rituals (`disable-model-invocation: true`) bắt buộc $A = 1.0$.
- **RULE-1.2 [ADR 0053 — Single-Writer Protocol Cho Orchestrators]**:
  - Mọi quy trình điều phối đa tác tử (`ccba-teamwork`, swarms) bắt buộc tuân thủ Single-Writer: Lead Orchestrator là thực thể duy nhất ghi mã nguồn và logs. Subagents phân tán chỉ xuất Unified Diff / Structured Patch vào `.system_generated/scratch/`, nghiêm cấm sửa file trực tiếp.
- **RULE-1.3 [ADR 0035 — Deep Modules, Seams & Zero-Exemption AST]**:
  - Thin Seam: Module/package chỉ bộc lộ `__all__` hoặc `__init__.py`. Tuyệt đối không import private submodule `_*`.
  - Zero-Exemption: Gỡ bỏ toàn bộ bypass hardcoded theo tên file trong `check_dependency_contracts.py`. Tệp thử nghiệm lịch sử chuyển vào `archive/`.
- **RULE-1.4 [ADR 0033 & ADR 0056 — Spoke Directory Hygiene & Zombie Prevention]**:
  - Cấu trúc `.\.md\`: Gốc chỉ chứa cấu hình (`workspace_context.yaml`); dữ liệu nạp vào `.\.md\extracted_docs\`; tri thức vào `.\.md\knowledge\`; thử nghiệm vào `.\.md\archive\`.
  - Spoke Synchronizer (`coordinator.py`): Đổi tên workflows cũ thành `.md.bak` (nhãn `DEPRECATED_MIGRATED_TO_SKILL`), xóa thư mục cũ theo `SKILL_DEPRECATION_ALIASES`, không tự sinh thư mục `.agents/workflows/` rỗng.
- **RULE-1.5 [ADR 0037 & ADR 0051 — Two-Tier Traceability Matrix & Status Regex]**:
  - Tier 1: Platform Constitution (55 Hub ADRs). Tier 2: Spoke Domain Decisions (`docs/adr/`). Bảo toàn bảng tùy chỉnh qua thẻ `<!-- CUSTOM_SECTIONS_START -->` ... `<!-- CUSTOM_SECTIONS_END -->`.
  - Regex bắt trạng thái ADR phải bao quát tiền tố list marker `(?:\*|-)?\s*\*\*\s*Status:\s*\*\*`. Lọc bỏ file non-ADR (`notes.md`, `template.md`).
- **RULE-1.6 [ADR 0044 — Federated RAG & Dynamic Import]**:
  - Tier 0 import Tier 1 dùng `try: from ccba_legal.xxx import yyy; except ImportError: pass`. Cache BM25 Singleton cấp module; Cache Embedding `.npy` bắt buộc kiểm tra SHA-256 qua `.sha256` sidecar.
- **RULE-1.7 [ADR 0046 — Sanitized Fleet Telemetry Protocol]**:
  - Khi tổng hợp telemetry từ Spokes về Hub, tuyệt đối chỉ trích xuất dữ liệu đo lường phi định danh (`tokens`, `cost`, `tool_counts`, `status`). Cấm tuyệt đối thu thập prompt text, câu hỏi người dùng, hoặc dữ liệu khách hàng từ Spoke.

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Strict Testing)

- **RULE-2.1 [Strict Mypy Type-Safety — Chống Anti-Pattern AP9.1]**:
  - NGHIÊM CẤM dùng `[[tool.mypy.overrides]] ignore_errors = true` trong `pyproject.toml`. Ép kiểu tường minh cho binary I/O, fonts, dicts. Chỉ dùng `ignore_missing_imports = true` cho third-party thiếu stubs.
- **RULE-2.2 [Spoke CI Gates Verification Pipeline]**:
  - 5 Cổng Zero-Tolerance bắt buộc trước khi nghiệm thu: (1) `lint_visual_parity.py`, (2) `validate_legal_spoke.py`, (3) `test_converter_regression.py`, (4) `verify_all_docs_against_pdf.py` (SHA-256 Valid), (5) `verify_cross_links.py`.
- **RULE-2.3 [Fast Feedback Loops (< 2s) & Parity Contract Tests]**:
  - Unit tests nòng cốt phải đạt SLA $< 2\text{s}$ (`pytest -m fast`). `test_cli_doc_parity.py`: Khớp nối 100% giữa CLI và `SKILL.md`. `drift_auditor.py`: Miễn trừ `not filepath.startswith("scripts/tests/")` chống cảnh báo giả.
- **RULE-2.4 [Relative Link Resolution Depth]**:
  - Tệp trong `.agents/skills/<skill>/SKILL.md` trỏ về package monorepo dùng 3 cấp lùi: `../../../packages/<pkg>`.
  - Tệp trong `references/<ref>.md` trỏ về root monorepo dùng 4 cấp lùi: `../../../../`.
  - CẤM TUYỆT ĐỐI commit đường dẫn `file:///` hoặc URI `conversation://` vào kho Git.
- **RULE-2.5 [Windows Subprocess UTF-8 Encoding Standard]**:
  - Trên Windows, `subprocess.run(..., text=True)` mặc định mã hóa theo code page `cp1252`. BẮT BUỘC truyền `encoding="utf-8", errors="replace"` chống lỗi `UnicodeDecodeError` khi đọc stdout có tiếng Việt, emoji, hoặc SVG box-drawing.

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu Hiện Hành (Legal & Data Standards)

- **RULE-3.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - MỌI văn bản pháp luật viện dẫn (kể cả mock fixtures, demo slides) BẮT BUỘC ĐANG CÓ HIỆU LỰC (CURRENT / IN-FORCE).
  - VĂN BẢN HIỆN HÀNH: **Luật Xây dựng 2025** (Luật số `135/2025/QH15`), **Nghị định 217/2026/NĐ-CP** (Quản lý Hoạt động Xây dựng — thay thế NĐ 175/2024 & NĐ 15/2021), **Nghị định 207/2026/NĐ-CP** (Quản lý Chất lượng & Bảo trì — thay thế NĐ 06/2021).
  - TUYỆT ĐỐI CẤM dùng NĐ 175/2024, NĐ 15/2021, NĐ 06/2021 làm căn cứ pháp lý hiện tại.
- **RULE-3.2 [TVPL VIP 3-Tier Download Priority — ADR 0031]**:
  - Tier 1 (`part=-100`): VIP Digital Vector PDF (Mỏ neo Pháp lý Tối thượng).
  - Tier 2 (`part=-1&docx=1`): VIP OpenXML Word Document (Nguồn dữ liệu gốc vàng nạp `docx_converter.py`).
  - Tier 3 (`part=0`): Gazette Scan PDF (Dự phòng).
- **RULE-3.3 [Làm Sạch Bảng Biểu & Chú Thích Pháp Lý]**:
  - Footnote: Khử lặp số thứ tự: `re.sub(r"^[0-9]+[)\.]\s*", "", fn_clean).strip()`. Bảng Markdown nhận diện qua cặp dòng tiêu đề và phân cách `| :--- |`.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent (Workflows, Commands & Review)

- **RULE-4.1 [Entry Point Duy Nhất Khi Có Issue ID: `/ccba-new-feature`]**:
  - Khi đã xác định Issue ID, LUÔN đề xuất `/ccba-new-feature #<id>` làm hành động tiếp theo (bao trọn 8 bước Factory Model).
  - CẤM TUYỆT ĐỐI nhảy thẳng vào `/ccba-implement`, `/ccba-to-spec`, `/ccba-to-tickets`.
- **RULE-4.2 [Slash Command Parity & Active Commands SSOT]**:
  - BẮT BUỘC đối chiếu `catalog.yaml` trước khi đề xuất bất kỳ lệnh `/command`. Chỉ kỹ năng có `command: /...` mới được gắn tiền tố `/`.
  - Tài liệu tham chiếu trong `references/*.md` (Tier 2A) CẤM dùng tiền tố `/` (hướng dẫn người dùng gọi Master Skill kèm nạp reference).
- **RULE-4.3 [Tiêu Chí Hoàn Thành Đa Nhánh & DRY Reference]**:
  - Tiêu chí hoàn thành phải có nhánh kiểm chứng cho từng cờ (`--compare`, `--port`, `--improve`, `--copy-raw`).
  - Quy tắc kết hợp cờ chỉ tuyên bố 1 lần duy nhất tại mục `Kết hợp không hợp lệ` trong `MODES.md`.
- **RULE-4.4 [GitHub Copilot Multi-Tier Review Gating]**:
  - Quét `author.login` thay vì `user.login`. Bắt buộc kiểm tra `### 🟡 Changes recommended` và review `body` của Copilot kể cả khi trạng thái là `COMMENTED`. Cấm merge nếu chưa sửa hoặc giải trình.

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows, Chrome CDP & Tooling)

- **RULE-5.1 [Chromium VIP Session Engine & CDP Browser Target]**:
  - Profile độc lập: `~/.gemini/antigravity/chrome_vip` trên cổng `9222`. Lệnh `Browser.setDownloadBehavior` BẮT BUỘC gọi qua Browser Target WebSocket (`http://127.0.0.1:{port}/json/version`).
  - Toàn bộ DOM Selectors đăng nhập, xác nhận phiên TVPL kế thừa tập trung từ `TVPLSelectors` trong `selectors.py`.
- **RULE-5.2 [Windows Path Quotes & Hook Protection]**:
  - Khi Antigravity IDE trên Windows tự bọc đường dẫn `hooks.json` trong dấu ngoặc kép `"C:\..."`, vô hiệu hóa bằng `{}` và khóa thuộc tính `IsReadOnly = $true` trên PowerShell chống lỗi `Cannot find module`.
  - Thiết lập timeout $\ge 60\text{s}$ cho integration tests có scan metadata trên Windows.
- **RULE-5.3 [Query Sanitization & Turnstile Bypass]**:
  - Query TVPL có dấu `/`, `:`, `-` phải thay bằng dấu cách (`quote_plus`) chống lỗi IIS mã hóa `%2F`.
