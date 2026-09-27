# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants (Compacted Working Memory)

> **Phạm vi áp dụng:** Hub (`ccba-agent-platform`) & Spokes (`ccba-legal-knowledge`, etc.)
> **Tiêu chuẩn:** ADR 0030, 0031, 0035, 0041, 0057, 0058.
> **Lịch sử & Post-Mortems:** [session_learnings_history.md](archive/session_learnings_history.md) | Ngưỡng: $\le 10\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc, Phân Tầng Kỹ Năng & Quản Trị Seams (Architecture & Governance)

- **RULE-1.1 [ADR 0057 — Khung 2 Giai Đoạn & Chỉ Số GPI]**:
  - *Cổng 0 (Determinism)*: Thuần giải thuật/IO $\rightarrow$ Deep Seams (`packages/*/src/`). `SKILL.md` không code trần.
  - *Cổng 1 (Orchestration)*: Đa luồng/StateGraph/HITL $\rightarrow$ Tier 3 Composite Orchestrator (bỏ qua GPI).
  - *Chỉ số GPI*: $\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$. $< 12.0 \rightarrow$ Tier 2A; $\ge 12.0 \rightarrow$ Tier 2B. Rituals: $A = 1.0$.
- **RULE-1.2 [ADR 0053 — Single-Writer Protocol Cho Orchestrators]**:
  - Single-Writer: Lead Orchestrator duy nhất ghi mã/logs. Subagents chỉ xuất Structured Patch vào `.system_generated/scratch/`.
- **RULE-1.3 [ADR 0035 — Deep Modules, Seams & Zero-Exemption AST]**:
  - Thin Seam: Module chỉ bộc lộ `__all__` hoặc `__init__.py`. Cấm import private `_*`. Zero-Exemption: Gỡ bypass trong linter.
- *(RULE-1.4 [ADR 0033, ADR 0056], RULE-1.5 [ADR 0037, ADR 0051] tại Mục 23; RULE-1.9 tại Mục 24; RULE-1.6, 1.8 tại Mục 25 của archive/session_learnings_history.md)*
- **RULE-1.10 [Platform-Aware KISS & Anti-Phantom Deferral]**:
  - Tái sử dụng Package Seams / Master Skills có sẵn là KISS bậc 1; CẤM script chắp vá. Tra cứu Seam qua CLI (`compile_catalog.py --query <kw>`). CẤM hoãn kiến trúc chuẩn sang Phase 2.
- **RULE-1.11 [Static Seam Verification & AST Span Linter]**:
  - `validate_seam_exports()` kiểm tra Package Spoofing, Filesystem Existence, và Symbol Parity với `__all__`.
  - Trích xuất symbol luôn `.rstrip(".,;")`. Quét exemption comment import dùng dải `range(node.lineno - 1, getattr(node, "end_lineno", node.lineno))`.
- **RULE-1.12 [ADR 0060 — Team Whitelist & Federated Architecture]**:
  - *Team Whitelist*: BẮT BUỘC unignore `!.agents/teams/` trong `.gitignore` lưu trữ team specs.
  - *Federated Hubs Alignment*: 4 Hubs (`ccba-agent-platform`, `ccba-ai-gateway`, `ccba-legal-knowledge`, `ccba-bim-knowledge`) tự trị chia sẻ tri thức qua CLI/REST/gRPC.
- **RULE-1.13 [Parameter Externalization, AST Linter & Declarative Config]**:
  - *No Raw Models/IPs*: CẤM nhúng raw model (`gemini-*`, `gpt-*`) hoặc IP trong code/skills. Dùng `choose_model()` / `ModelArchetype` và biến môi trường (ngoại lệ: `# ccba:allow-raw-model`, `# ccba:allow-raw-ip`).
  - *AST Linter & Declarative Config*: `check_hardcoded_parameters.py` kiểm soát tĩnh. Trọng số và routing tách thành YAML/JSON theo nguyên tắc OCP.

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Strict Testing)

- **RULE-2.1 [Strict Mypy Type-Safety — Chống Anti-Pattern AP9.1]**:
  - CẤM `[[tool.mypy.overrides]] ignore_errors = true`. Ép kiểu tường minh binary I/O, dicts. Dùng `ignore_missing_imports = true` cho lib thiếu stubs.
- **RULE-2.3 [Fast Feedback Loops (< 2s) & Parity Contract Tests]**:
  - Unit tests nòng cốt đạt SLA $< 2\text{s}$ (`pytest -m fast`). `test_cli_doc_parity.py`: Khớp nối 100% giữa CLI và `SKILL.md`.
- **RULE-2.4 [Relative Link Resolution Depth]**:
  - Tệp `.agents/skills/<skill>/SKILL.md` trỏ về package monorepo dùng `../../../packages/<pkg>`. CẤM commit URI `file:///` hoặc `conversation://`.
- **RULE-2.5 [ADR 0058 — SSOT Archetype Routing, Disjoint Hierarchy & 100% Skill Coverage]**:
  - Ánh xạ kỹ năng sang đề thi (`eval_*.json`) BẮT BUỘC dùng `archetypes.py` làm SSOT (17 archetypes).
  - *Disjoint Hierarchy*: Archetype chuyên biệt (`platform_tooling`, `legal_tooling`, `visual_design`) đứng trước archetype khái quát (`orchestration`, `legal`, `visual`). 100% kỹ năng (74/74 skills) map chuẩn xác; cấm unmapped (`None`).
- *(RULE-2.8, 2.10, 2.11 tại Mục 24; RULE-2.12 tại Mục 25 của archive/session_learnings_history.md)*
- **RULE-2.9 [Test Fixture Isolation, Live Lock & Hub Decoupling]**:
  - *Env & Live Lock Isolation*: Test fixtures/runners (`conftest.py`) BẮT BUỘC xóa `CCBA_HUB_PATH`, `HUB_PATH` và mock triệt để lock vật lý (`is_kernel_runner_locked`, `check_daemon_lock`, `/tmp/*.lock` $\rightarrow$ `False`). CẤM rò rỉ biến môi trường hoặc đọc lock thật.
- **RULE-2.13 [Atomic Micro-PR Slicing & Single-Seam Locality]**:
  - *Micro-Task Slicing*: Phân rã task $\le 150-200$ LOC logic vào 1 Deep Seam duy nhất kèm test tự động; chia nhỏ task phức tạp thành micro-PRs giảm review fatigue và conflict.
- **RULE-2.14 [UTF-8 Offset Parity & Dynamic Mock Secrets]**:
  - *UTF-8 Offset Parity*: Chuỗi tiếng Việt/emoji byte length khác character offset. Cắt lát redaction string BẮT BUỘC dùng character index đảo ngược (`reversed(findings)`); byte redaction dùng `byte_start, byte_end`.
  - *Dynamic Mock Secrets*: Unit tests BẮT BUỘC tạo mock keys runtime (`f"sk-proj-{'a'*32}"`) chống CI diff scanner false-positive.
- **RULE-2.15 [Atomic Knowledge Cataloging, Hermetic Scripts & Ruff Guard]**:
  - *Atomic Knowledge Cataloging*: Mọi tệp `.md` mới trong `.md/knowledge/` BẮT BUỘC biên mục đồng thời vào `.md/knowledge/index.md` ngay tại commit tạo tệp, chống sập CI Orphan Notes.
  - *Hermetic Script Protocol*: Sửa mã nguồn/YAML đa dòng qua shell CẤM inline string có backticks; BẮT BUỘC dùng `cat << 'EOF' > /tmp/patch.py` (bọc nháy đơn) hoặc tool tệp chuyên dụng.
  - *Ruff B009 Attribute Guard*: Kiểm tra callable động BẮT BUỘC dùng `hasattr(obj, "method") and callable(obj.method)` thay vì `getattr(obj, "constant")`.

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu Hiện Hành (Legal & Data Standards)

- **RULE-3.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - Viện dẫn BẮT BUỘC CÒN HIỆU LỰC: **Luật Xây dựng 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP**, **NĐ 207/2026/NĐ-CP**, **NĐ 206/2026/NĐ-CP**. CẤM luật hết hiệu lực.
- **RULE-3.2 [TVPL VIP 3-Tier Download Priority — ADR 0031]**:
  - Tier 1 (`part=-100`): VIP Vector PDF. Tier 2 (`part=-1&docx=1`): VIP Word (`docx_converter`). Tier 3 (`part=0`): Scan PDF (Dự phòng).
- **RULE-3.4 [RAG Normative Spanning & ADR-0059 Test Isolation]**:
  - `clauses.json` span (`line_start`/`line_end`) bắt buộc bao trọn toàn văn quy phạm đa dòng; cấm span 1 dòng chỉ trỏ `<a>`.
  - Test suites bắt buộc dùng `tmp_path / "legal_registry.yaml"`, cấm ghi đè file gốc. CI Spoke hard-lock khi thiếu `clauses.json`.
- **RULE-3.5 [Documentation Link Scheme Portability Invariant]**:
  - `validate_docs.py` cấm URL tuyệt đối `file:///home/...` hoặc `file:///C:/...`. BẮT BUỘC dùng relative paths hoặc repo-relative links.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent (Workflows, Commands & Review)

- **RULE-4.1 [Entry Point Duy Nhất Khi Có Issue ID: `/ccba-new-feature`]**:
  - Có Issue ID: LUÔN đề xuất `/ccba-new-feature #<id>` (8 bước Factory Model). Cấm nhảy thẳng vào implement/spec/tickets.
- **RULE-4.2 [Slash Command Parity & Active Commands SSOT]**:
  - Đối chiếu `catalog.yaml` trước khi đề xuất `/command`. Chỉ kỹ năng có `command: /...` mới gắn tiền tố `/`. Tài liệu `references/*.md` (Tier 2A) cấm tiền tố `/`.
- **RULE-4.4 [GitHub Copilot Multi-Tier Review Gating]**:
  - Quét `author.login`. Bắt buộc kiểm tra `### 🟡 Changes recommended` và `body` Copilot kể cả khi COMMENTED. Cấm merge nếu chưa sửa/giải trình.
- **RULE-4.5 [Git Governance Pre-Push Lock & Architecture Drift Invariant]**:
  - Hub cấm push `main` qua hook `pre-push`; chỉ qua PR. Thêm/sửa tệp ngoài `tests/` bắt buộc cập nhật `arch_docs` (`README.md`, `PLATFORM.md`).
- **RULE-4.6 [PR Shift-Left CI & Zero-Red-Merge]**:
  - Chạm $\ge 2$ pkgs: BẮT BUỘC `verify-patch --preset ci`. CẤM `--admin`/`--auto`; 100% Green.
- *(RULE-4.7 tại Mục 25 của archive/session_learnings_history.md)*
- **RULE-4.8 [Automated Review Danger Triage, Two-way Door Gate & Maskara Diff Sanitizer]**:
  - *Danger Triage CI Gate*: Tệp cốt lõi (`AGENTS.md`, `.github/workflows/`, `scripts/`, `packages/`) $\rightarrow$ HARD gate; Pure Docs (`.md/**`, `README.md`, `WALKTHROUGH.md`) qua Defense-in-Depth $\rightarrow$ Two-way Door Fast-Path gán nhãn và Auto-Approve an toàn.
  - *Maskara Diff Gate*: `sanitize_review_diff.py --check` là Hard Blocker chặn merge PR rò rỉ secret. Deduplicate nhận xét báo cáo PR lũy kế (`per_page: 100`).
- **RULE-4.10 [Nightly Auto-Tune & TRIHT Release Gate (ADR-0045, ADR-0058)]**:
  - *Nightly Tuner*: PR `auto-tune/*` bắt buộc đối soát Evolution Matrix, kiểm tra Goodhart (cấm comment rác Ratchet, cấm nhồi từ khóa), 100% Skills Hygiene Pass.
  - *TRIHT Release*: Release PR qua 3 cổng buồng kín: Pre-Flight Cleanliness, Slow Hermetic Integration Tests, Post-Test Teardown trước khi Squash Merge.
- **RULE-4.11 [Concurrent Branch Alignment & Walkthrough PR Protocol]**:
  - *Remote Merge Realignment*: Khi nhánh PR nhận merge mới từ `main` trên GitHub, BẮT BUỘC kiểm tra commit local đã push, dùng `git reset --hard origin/<branch>` căn chỉnh working tree sạch sẽ; CẤM để unmerged files trước release.
  - *Walkthrough Dedicated PR*: Tuân thủ hook `pre-push` cấm push thẳng `main`, `walkthrough.md` BẮT BUỘC lưu trữ qua nhánh riêng `docs/walkthrough-pr-<id>` và Squash-Merge qua Fast-Path Review.

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows, Chrome CDP & Tooling)
*(Xem RULE-5.1-5.5 tại archive/session_learnings_history.md)*
