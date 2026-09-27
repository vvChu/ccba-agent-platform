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
  - Thin Seam: Module chỉ bộc lộ `__all__` hoặc `__init__.py`. Cấm import private submodule `_*`. Zero-Exemption: Gỡ bypass trong linter.
- *(RULE-1.4 [ADR 0033 & ADR 0056] và RULE-1.5 [ADR 0037 & ADR 0051] tại Mục 23; RULE-1.9 tại Mục 24 của archive/session_learnings_history.md)*
- **RULE-1.6 [ADR 0044 — Federated RAG & Dynamic Import]**:
  - Tier 0 import Tier 1: `try: from ccba_legal.xxx import yyy; except ImportError: pass`. Cache BM25 Singleton; Cache Embedding `.npy` kiểm tra SHA-256 sidecar.
- **RULE-1.8 [ADR 0044 & Issue #326 — Multi-Device Spoke & Invariant Merge]**:
  - *Universal Invariant Regex*: Regex multiline bảo tồn 100% điều khoản cục bộ khi sync.
  - *Cross-Drive Fallback*: Khi `relpath` lỗi `ValueError`, fallback `hub_path` về `None`, tránh gắn cứng ổ đĩa.
- **RULE-1.10 [Platform-Aware KISS & Anti-Phantom Deferral]**:
  - *Platform-Aware KISS*: Tái sử dụng Monorepo Package Seams / Master Skills có sẵn là KISS bậc 1. CẤM script chắp vá hay ad-hoc data silo.
  - *Pre-Flight Gate Receipt*: Bắt buộc tra cứu Seam qua CLI (`compile_catalog.py --query <keyword>`) trước khi đề xuất code mới.
  - *Anti-Phantom Deferral*: CẤM chia "Phase 1 chắp vá" rồi hoãn kiến trúc chuẩn sang "Phase 2" khi hạ tầng đã sẵn sàng.
- **RULE-1.11 [Static Seam Verification, Punctuation Immunity & AST Span Linter]**:
  - *Static Seam Verification*: `validate_seam_exports()` kiểm tra 3 rào chắn: Package Spoofing, Filesystem Existence, và Symbol Parity với `__all__`.
  - *Punctuation Immunity*: Trích xuất symbol từ markdown luôn dùng `s.strip().rstrip(".,;")` chống dấu chấm câu văn xuôi làm ô nhiễm symbol.
  - *AST Span Linter*: Quét exemption comment trên AST import BẮT BUỘC dùng dải `range(node.lineno - 1, getattr(node, "end_lineno", node.lineno))`.
- **RULE-1.12 [ADR 0060 — Team Whitelist & 4-Hubs Federated Architecture]**:
  - *Team Whitelist*: BẮT BUỘC unignore `!.agents/teams/` trong `.gitignore` để lưu trữ team specs.
  - *Federated Hubs Alignment*: 4 Hubs (`ccba-agent-platform`, `ccba-ai-gateway`, `ccba-legal-knowledge`, `ccba-bim-knowledge`) vận hành theo mô hình Federated Decentralized, chia sẻ hợp đồng tri thức và REST/gRPC/CLI, tự trị không tạo điểm nghẽn.
- **RULE-1.13 [Parameter Externalization, AST Linter & Declarative Config]**:
  - *No Raw Models/IPs*: CẤM nhúng raw model (`gemini-*`, `gpt-*`) hoặc IP trong code/skills. Dùng `choose_model()` / `ModelArchetype` và biến môi trường (ngoại lệ: `# ccba:allow-raw-model`, `# ccba:allow-raw-ip`).
  - *AST Linter & Declarative Config*: `check_hardcoded_parameters.py` kiểm soát tĩnh. Trọng số và routing tách thành YAML/JSON theo nguyên tắc OCP.

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Strict Testing)

- **RULE-2.1 [Strict Mypy Type-Safety — Chống Anti-Pattern AP9.1]**:
  - CẤM `[[tool.mypy.overrides]] ignore_errors = true`. Ép kiểu tường minh cho binary I/O, fonts, dicts. Chỉ dùng `ignore_missing_imports = true` cho third-party thiếu stubs.
- **RULE-2.3 [Fast Feedback Loops (< 2s) & Parity Contract Tests]**:
  - Unit tests nòng cốt đạt SLA $< 2\text{s}$ (`pytest -m fast`). `test_cli_doc_parity.py`: Khớp nối 100% giữa CLI và `SKILL.md`.
- **RULE-2.4 [Relative Link Resolution Depth]**:
  - Tệp `.agents/skills/<skill>/SKILL.md` trỏ về package monorepo dùng `../../../packages/<pkg>`. CẤM commit URI `file:///` hoặc `conversation://`.
- **RULE-2.5 [ADR 0058 — SSOT Archetype Routing, Disjoint Hierarchy & 100% Skill Coverage]**:
  - Ánh xạ kỹ năng sang đề thi (`eval_*.json`) BẮT BUỘC dùng `archetypes.py` làm SSOT (17 archetypes).
  - *Disjoint Hierarchy*: Archetype chuyên biệt (`platform_tooling`, `legal_tooling`, `visual_design`) đứng trước archetype khái quát (`orchestration`, `legal`, `visual`). 100% kỹ năng (74/74 skills) map chuẩn xác; cấm unmapped (`None`).
- *(RULE-2.8, RULE-2.10 và RULE-2.11 đã di dời vào archive/session_learnings_history.md Mục 24)*
- **RULE-2.9 [Test Fixture Isolation, Live Lock & Hub Decoupling]**:
  - *Env & Live Lock Isolation*: Test fixtures/runners (`conftest.py`) BẮT BUỘC xóa `CCBA_HUB_PATH`, `HUB_PATH` và mock triệt để lock vật lý hệ điều hành (`is_kernel_runner_locked`, `check_daemon_lock`, `/tmp/*.lock` $\rightarrow$ `False`). CẤM rò rỉ biến môi trường hoặc đọc lock thật, bảo đảm test 100% Green khi máy chủ chạy daemon nền.
- **RULE-2.12 [LiteLLM Budget Error Resilience & Vector Top-K]**:
  - *Budget Error Resilience*: Bắt lỗi LiteLLM kiểm tra đồng thời: `("budget" in err.lower() and "exceeded" in err.lower())`.
  - *Vector L2 Normalization*: Embeddings chuẩn hóa L2 trước khi cache; truy vấn dùng dot-product (`@`) và `np.argpartition` $O(n + k \log k)$ cho corpus lớn.
- **RULE-2.13 [Atomic Micro-PR Slicing & Single-Seam Locality]**:
  - *Atomic Micro-Task Slicing*: Phân rã task $\le 150-200$ LOC logic, neo vào 1 Deep Seam duy nhất, kèm lệnh kiểm thử tự động xác định. Cắt nhỏ task phức tạp thành chuỗi micro-PRs độc lập giảm thiểu review fatigue và rủi ro merge conflict.

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu Hiện Hành (Legal & Data Standards)

- **RULE-3.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - MỌI văn bản viện dẫn BẮT BUỘC ĐANG CÓ HIỆU LỰC: **Luật Xây dựng 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP**, **NĐ 207/2026/NĐ-CP**, **NĐ 206/2026/NĐ-CP**. CẤM văn bản hết hiệu lực.
- **RULE-3.2 [TVPL VIP 3-Tier Download Priority — ADR 0031]**:
  - Tier 1 (`part=-100`): VIP Vector PDF (Mỏ neo tối thượng). Tier 2 (`part=-1&docx=1`): VIP Word (Nguồn vàng cho `docx_converter`). Tier 3 (`part=0`): Scan PDF (Dự phòng).
- **RULE-3.4 [RAG Normative Spanning & ADR-0059 Test Isolation]**:
  - `clauses.json` span (`line_start`/`line_end`) bắt buộc bao trọn toàn văn quy phạm đa dòng; cấm span 1 dòng chỉ trỏ `<a>`.
  - Test suites bắt buộc dùng `tmp_path / "legal_registry.yaml"`, cấm ghi đè file gốc. CI Spoke hard-lock khi thiếu `clauses.json`.
- **RULE-3.5 [Documentation Link Scheme Portability Invariant]**:
  - `validate_docs.py` cấm URL tuyệt đối `file:///home/...` hoặc `file:///C:/...`. BẮT BUỘC dùng relative paths hoặc repo-relative links.

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
- **RULE-4.7 [POSIX Traversal ACLs vs SGID Group Inheritance]**:
  - Máy chủ Linux đa người dùng: Cấp traversal `g:ccba-devs:--x` trên thư mục cha và gán SGID (`chmod -R g+s`) cho các repos kế thừa nhóm sở hữu.
- **RULE-4.8 [Automated Review Danger Triage & Advisory Gating]**:
  - *Danger Triage CI Gate*: Phân loại PR: Tệp cốt lõi (`AGENTS.md`, `.github/workflows/`, `scripts/`, `packages/`) $\rightarrow$ HARD gate (chặn merge khi lỗi); Docs/satellite $\rightarrow$ ADVISORY gate (không chặn build). Deduplicate nhận xét tự động từ Bugbot/Copilot tránh spam PR.

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows, Chrome CDP & Tooling)
*(RULE-5.1-5.5 tại archive/session_learnings_history.md)*
