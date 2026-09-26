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
- **RULE-1.5 [ADR 0037 & ADR 0051 — Two-Tier Traceability Matrix & Status Regex]**:
  - Tier 1: Hub (53 ADRs). Tier 2: Spoke (`docs/adr/`). Bảo toàn bảng tùy chỉnh qua markers `CUSTOM_SECTIONS`.
  - Regex bắt trạng thái ADR: `(?:\*|-)?\s*\*\*\s*Status:\s*\*\*`. Lọc bỏ file non-ADR (`notes.md`, `template.md`).
- **RULE-1.6 [ADR 0044 — Federated RAG & Dynamic Import]**:
  - Tier 0 import Tier 1: `try: from ccba_legal.xxx import yyy; except ImportError: pass`. Cache BM25 Singleton module; Cache Embedding `.npy` kiểm tra SHA-256 sidecar.
- **RULE-1.8 [ADR 0044 & Issue #326 — Multi-Device Spoke & Universal Invariant Merge]**:
  - *Universal Invariant Regex*: Regex multiline bảo tồn 100% điều khoản cục bộ khi sync.
  - *Cross-Drive Fallback*: Khi `relpath` lỗi `ValueError`, fallback `hub_path` về `None`, tránh gắn cứng ổ đĩa.
- **RULE-1.9 [2-Phase Planning Guardrail — The Factory Model]**:
  - Refactoring bộ trích xuất/chuyển đổi BẮT BUỘC phân lập 2 giai đoạn: Phase 1 (Pure Structural — Zero-Regression 0.0%, dual-dispatch) và Phase 2 (Feature/Schema Mutations). Cấm scope conflation.
- **RULE-1.10 [Platform-Aware KISS & Anti-Phantom Deferral]**:
  - *Platform-Aware KISS (Entropy Tối Thiểu)*: Tái sử dụng Monorepo Package Seams / Master Skills có sẵn là giải pháp KISS bậc 1. CẤM tạo script chắp vá hoặc ad-hoc data silo cục bộ rồi ngụy biện là KISS.
  - *Pre-Flight Gate Receipt*: Bắt buộc tra cứu Seam qua CLI (`compile_catalog.py --query <keyword>`) trước khi đề xuất code mới; dán kết quả tra cứu vào `implementation_plan.md`.
  - *Anti-Phantom Deferral*: CẤM chia "Phase 1 chắp vá tạm bợ" rồi hoãn kiến trúc chuẩn sang "Phase 2" khi hạ tầng nền tảng đã sẵn sàng.
- **RULE-1.11 [Static Seam Verification, Punctuation Immunity & AST Span Linter]**:
  - *Static Seam Verification*: `validate_seam_exports()` kiểm tra 3 rào chắn: Package Spoofing Guard, Filesystem Existence, và Symbol Parity với `__all__` (hỗ trợ `ast.AugAssign` `__all__ += [...]`).
  - *Punctuation Immunity*: Trích xuất symbol từ markdown luôn dùng `s.strip().rstrip(".,;")` chống dấu chấm câu văn xuôi làm ô nhiễm symbol.
  - *AST Span Linter*: Quét exemption comment trên AST import BẮT BUỘC dùng dải `range(node.lineno - 1, getattr(node, "end_lineno", node.lineno))` bao trọn dòng đóng ngoặc của multiline imports.



---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Strict Testing)

- **RULE-2.1 [Strict Mypy Type-Safety — Chống Anti-Pattern AP9.1]**:
  - CẤM `[[tool.mypy.overrides]] ignore_errors = true`. Ép kiểu tường minh cho binary I/O, fonts, dicts. Chỉ dùng `ignore_missing_imports = true` cho third-party thiếu stubs.
- **RULE-2.3 [Fast Feedback Loops (< 2s) & Parity Contract Tests]**:
  - Unit tests nòng cốt đạt SLA $< 2\text{s}$ (`pytest -m fast`). `test_cli_doc_parity.py`: Khớp nối 100% giữa CLI và `SKILL.md`.
- **RULE-2.4 [Relative Link Resolution Depth]**:
  - Tệp `.agents/skills/<skill>/SKILL.md` trỏ về package monorepo dùng `../../../packages/<pkg>`. CẤM commit URI `file:///` hoặc `conversation://`.
- **RULE-2.5 [ADR 0058 — SSOT Archetype Routing & Disjoint Subdomains]**:
  - Ánh xạ kỹ năng sang đề thi (`eval_*.json`) BẮT BUỘC dùng `archetypes.py` làm SSOT. Từ khóa chuyên biệt (`grill`, `adr`, `risk`) tách thành subdomain độc lập chống va chạm regex.
- **RULE-2.8 [Cross-Platform Sandbox Root Traversal Invariant]**:
  - CẤM độ sâu cố định `parents[N]` (tránh `PermissionError` trên Linux `/tmp`). BẮT BUỘC duyệt ngược tìm `(p / ".md").is_dir()`, fallback local `.cache/`, bọc `try...except (PermissionError, OSError)`.
- **RULE-2.9 [Test Fixture Isolation, Live Lock & Hub Decoupling]**:
  - *Env & Live Lock Isolation*: Test fixtures/runners (`conftest.py`) BẮT BUỘC xóa `CCBA_HUB_PATH`, `HUB_PATH` và mock triệt để lock vật lý hệ điều hành (`is_kernel_runner_locked`, `check_daemon_lock`, `/tmp/*.lock` $\rightarrow$ `False`). CẤM rò rỉ biến môi trường hoặc đọc lock thật, bảo đảm test 100% Green khi máy chủ chạy daemon nền.
- **RULE-2.10 [Temporal Invariance & Collinear Multi-Key Sort Guard]**:
  - *Temporal Invariance*: Test TTL/window CẤM ngày tĩnh; BẮT BUỘC ngày tương đối (`today - timedelta(...)`).
  - *Collinear Sort*: Test sắp xếp đa khóa BẮT BUỘC fixture nghịch chiều (`os.utime`), chống bẫy pass do cùng chiều.

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu Hiện Hành (Legal & Data Standards)

- **RULE-3.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - MỌI văn bản viện dẫn BẮT BUỘC ĐANG CÓ HIỆU LỰC: **Luật Xây dựng 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP** (thay NĐ 175 & 15), **NĐ 207/2026/NĐ-CP** (thay NĐ 06), **NĐ 206/2026/NĐ-CP** (thay NĐ 10). CẤM văn bản hết hiệu lực.
- **RULE-3.2 [TVPL VIP 3-Tier Download Priority — ADR 0031]**:
  - Tier 1 (`part=-100`): VIP Vector PDF (Mỏ neo tối thượng). Tier 2 (`part=-1&docx=1`): VIP Word (Nguồn vàng cho `docx_converter`). Tier 3 (`part=0`): Scan PDF (Dự phòng).
- **RULE-3.3 [Làm Sạch Bảng Biểu, Footnotes & ADR 0044 Multi-Part Disambiguation]**:
  - Footnote: Khử lặp số `re.sub(r"^[0-9]+[)\.]\s*", "", fn_clean).strip()`; khử lặp ô gộp OpenXML (`gridSpan`).
  - Subheader: `not is_numeric` trước khi gộp subheader tránh nuốt dữ liệu cùng giá trị.
  - Multi-Part: Đa phần mang tiền tố `bang_pXX_YY.csv` và `part_id: "pXX"` trong `tables_catalog.json`.
- **RULE-3.4 [RAG Normative Spanning & ADR-0059 Test Isolation]**:
  - `clauses.json` span (`line_start`/`line_end`) bắt buộc bao trọn toàn văn quy phạm đa dòng; cấm span 1 dòng chỉ trỏ `<a>`.
  - Test suites bắt buộc dùng `tmp_path / "legal_registry.yaml"`, cấm ghi đè file gốc. CI Spoke hard-lock khi thiếu `clauses.json`.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent (Workflows, Commands & Review)

- **RULE-4.1 [Entry Point Duy Nhất Khi Có Issue ID: `/ccba-new-feature`]**:
  - Có Issue ID: LUÔN đề xuất `/ccba-new-feature #<id>` (8 bước Factory Model). Cấm nhảy thẳng vào `/ccba-implement`, `/ccba-to-spec`, `/ccba-to-tickets`.
- **RULE-4.2 [Slash Command Parity & Active Commands SSOT]**:
  - Đối chiếu `catalog.yaml` trước khi đề xuất `/command`. Chỉ kỹ năng có `command: /...` mới gắn tiền tố `/`. Tài liệu `references/*.md` (Tier 2A) cấm tiền tố `/`.
- **RULE-4.4 [GitHub Copilot Multi-Tier Review Gating]**:
  - Quét `author.login`. Bắt buộc kiểm tra `### 🟡 Changes recommended` và `body` Copilot kể cả khi COMMENTED. Cấm merge nếu chưa sửa/giải trình.
- **RULE-4.5 [Git Governance Pre-Push Lock & Architecture Drift Invariant]**:
  - Hub cấm push `main` qua hook `pre-push`; chỉ qua PR. Thêm/sửa tệp ngoài `tests/` bắt buộc cập nhật `arch_docs` (`README.md`, `PLATFORM.md`).
- **RULE-4.6 [PR Shift-Left CI & Zero-Red-Merge]**:
  - Chạm $\ge 2$ pkgs: BẮT BUỘC `verify-patch --preset ci`. CẤM `--admin`/`--auto`; 100% Green trước khi merge.

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows, Chrome CDP & Tooling)
*(RULE-5.1 đến 5.3 đã di dời vào archive/session_learnings_history.md Mục 21; chi tiết 5.4-5.5 tại Mục 22)*

- **RULE-5.4 [Telegram ChatOps: Markdown v1, Subprocess Reaping & Cross-Repo Path]**:
  - *Markdown v1 & Subprocess*: Biến có `_` bọc backtick; Timeout/Cancel bắt buộc `proc.kill()` + `proc.wait()`; shell trap cleanup dùng `os.killpg`. Service systemd gọi chéo repo dùng `cwd` phân giải qua `CCBA_HUB_PATH`.
- **RULE-5.5 [Timezone-Normalized Observability cho Database Gateway UTC]**:
  - Truy vấn spend UTC gateway (LiteLLM) CẤM `CURRENT_DATE`. Bắt buộc lọc theo 00:00:00 ICT chuyển sang UTC: `WHERE "startTime" >= ((CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Ho_Chi_Minh')::date::timestamp AT TIME ZONE 'Asia/Ho_Chi_Minh' AT TIME ZONE 'UTC')`.

