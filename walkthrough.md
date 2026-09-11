# Walkthrough: Release PR #263 (Issue #258 — Master Registry Discovery, Query CLI Commands & Unify Spoke Knowledge Path)

## 1. Tổng Quan Release
- **PR Number:** [#263](https://github.com/vvChu/ccba-agent-platform/pull/263)
- **Branch:** `proposal/issue-258-master-registry-discovery-and-query-cli` $\rightarrow$ `main`
- **Tiêu đề:** `feat(legal-intel): enhance master registry discovery, add query CLI commands and unify spoke knowledge path (#258)`
- **Issue liên quan:** [Issue #258](https://github.com/vvChu/ccba-agent-platform/issues/258)
- **Thể chế & Kiến trúc:** ADR 0026, ADR 0033, ADR 0035, ADR 0036, ADR 0045, ADR 0058
- **Mục tiêu hoàn thành:**
  1. **Master Registry Discovery Tự Động (Read-Only)**: Spoke cài đặt qua `pip install -e` tự động định vị Master Registry 42 văn bản tại `ccba-legal-knowledge` qua thuật toán discovery đa tầng. `LegalRegistryManager` giữ nguyên mặc định local, bảo vệ tuyệt đối unit test cô lập.
  2. **Bộ 3 CLI Subcommands Tra Cứu**: Bổ sung `query`, `get-clause`, `get-table` hỗ trợ đầu ra màu sắc, JSON, Markdown và căn chỉnh cột bảng 2D.
  3. **Chuẩn Hóa Đường Dẫn Tri Thức Spoke (ADR 0033 & ADR 0036)**: `ccba_legal sync` tự động phân loại: Spoke tiêu thụ lưu tại `.\.md\legal_docs\`; riêng Master Spoke `ccba-legal-knowledge` lưu tại `legal_docs/`.
  4. **Facade Class `LegalKnowledgeEngine`**: Entrypoint thống nhất cho tìm kiếm, bóc tách AST điều khoản (Tier-Aware Semantic Slicing), alias parsing (`d1` $\rightarrow$ `dieu-1`), và bảo mật hai tầng chống CWE-22 (Two-Tier Containment).

---

## 2. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot (PR #263)

- **Review ID:** `PRR_kwDOQzfV088AAAABNLg5Dg`

| ID / Review | Tệp Tin | Vấn Đề Copilot Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| `3989832503` | `packages/ccba-legal-intel/src/ccba_legal/federated_rag.py` | `_resolve_corpus_paths()` derives `candidate_corpus` as `master_reg.parent / "legal_docs"`. When the discovered registry is the common `.md/data/legal_registry.yaml` layout, this points to `.md/data/legal_docs` (non-existent), so master discovery will never return bundles and will fall back to scanning upward from the installed package path (which won’t find the spoke corpus in editable installs). Derive the corpus root from the project root when the registry is inside `.md/data`, and check both `legal_docs/` and `.md/legal_docs/`. | **ĐÃ KHẮC PHỤC TRIỆT ĐỂ** (trong commit `7fe530a0`): Cập nhật hàm `FederatedLegalEngine._resolve_corpus_paths()` để nạp danh sách ứng viên đa tầng (`candidates`): (1) `reg_parent / "legal_docs"`, (2) `reg_parent / ".md" / "legal_docs"`. Đặc biệt, kiểm tra nếu `reg_parent.name == "data"` và `reg_parent.parent.name == ".md"`, tự động suy luận `project_root = reg_parent.parent.parent` và bổ sung thêm `project_root / "legal_docs"` cùng `project_root / ".md" / "legal_docs"`. Thuật toán duyệt qua từng ứng viên và nạp toàn bộ bundle hợp lệ. Đã xác nhận hoạt động chuẩn xác và reply trên PR. |

---

## 3. Chi Tiết Các Hạng Mục Kỹ Thuật Đã Hoàn Thành

1. **Facade Engine & Security (`packages/ccba-legal-intel/src/ccba_legal/engine.py`)**:
   - `LegalKnowledgeEngine`: Quản lý in-memory cache, tìm kiếm keyword/status, bóc tách điều khoản theo thuật toán Tier-Aware Semantic Slicing.
   - `canonicalize_clause_id`: Phân giải alias thông minh (`d1` $\rightarrow$ `dieu-1`, `d15k2` $\rightarrow$ `dieu-15-khoan-2`).
   - `csv_to_markdown`: Căn chỉnh cột Markdown tự động và escape ký tự pipe `\|`.
   - **Bảo mật CWE-22 (Two-Tier Containment)**: Kết hợp Regex Whitelist `^[a-zA-Z0-9_\-]+$` và `path.resolve().is_relative_to()`.

2. **Registry & Discovery (`packages/ccba-legal-intel/src/ccba_legal/registry.py`)**:
   - Hàm `discover_master_registry_path()` ưu tiên 6 tầng (registry_path $\rightarrow$ env vars $\rightarrow$ workspace_context.yaml $\rightarrow$ spoke registry $\rightarrow$ local candidates $\rightarrow$ fallback).
   - Giữ nguyên mặc định local của `LegalRegistryManager`.
   - Hàm `query()` ủy quyền sang `LegalKnowledgeEngine.search()`.

3. **CLI Subcommands (`packages/ccba-legal-intel/src/ccba_legal/cli.py`)**:
   - Cấu hình `sys.stdout.reconfigure(encoding="utf-8")` theo RULE-2.5 chống lỗi `cp1252` trên Windows PowerShell.
   - Bổ sung 3 subcommands: `query`, `get-clause`, `get-table` (hỗ trợ cờ `--json`, `--format`, `--corpus`).

4. **Đồng Bộ & Federated RAG (`sync/engine.py`, `federated_rag.py`)**:
   - `pull_latest_okf_bundles`: Phân loại đích lưu trữ theo loại Spoke. Mở rộng quét `04_appendices`.
   - `FederatedLegalEngine`: Nạp toàn diện 42 bundles thuộc `01_vbpl`, `02_qcvn`, `03_tcvn`, `04_appendices` qua Master Discovery đa tầng.

5. **Bộ Kiểm Thử Toàn Diện & Documentation Parity**:
   - `test_legal_knowledge_engine.py`: 12 tests kiểm thử toàn diện slicing, alias, CSV/Markdown formatting, và traversal protection.
   - `test_registry_discovery.py`: 7 tests kiểm thử các tầng ưu tiên discovery.
   - `test_cli_doc_parity.py`: Mở rộng kiểm tra parity 3 lệnh CLI mới với `.agents/skills/ccba-legal-intel/SKILL.md`.

---

## 4. Kết Quả Kiểm Thử Toàn Diện (Pre-release Gate)

- **Unit Tests Scoped**: 31/31 passed in 14.36s (Exit code 0).
- **Linter & Code Format (Ruff)**: 100% clean, all checks passed.
- **Isolated Tests Stress Suite (`run_isolated_tests.py -p ccba-legal-intel --stress`)**: 261/261 passed (Exit code 0).
- **Deterministic Hard Completion Lock (ADR-0058)**: `python -m ccba_harness verify-patch` ALL PASSED (2/2 commands executed, duration: 20.1s).
- **GitHub Actions CI (PR #263)**: 6/6 jobs PASS 100%:
  - `Lint Markdown`: Pass
  - `Test - Python 3.10`: Pass
  - `Test - Python 3.11`: Pass
  - `Test - Python 3.12`: Pass
  - `scan`: Pass
  - `validate`: Pass
- **Copilot PR Review Audit (`audit_pr_comments.py`)**: Đã giải trình và nghiệm thu toàn bộ Copilot Review `PRR_kwDOQzfV088AAAABNLg5Dg` và Comment `3989832503`.

---

## 5. Báo Cáo An Ninh Bảo Mật (Security Verification Report)

1. **CWE-22 (Path Traversal)**:
   - Hai tầng bảo vệ độc lập: Regex Whitelist loại bỏ toàn bộ chuỗi nguy hiểm (`..`, `/`, `\`); giải quyết đường dẫn tuyệt đối với `is_relative_to(corpus_dir)`.
2. **CWE-78 (OS Command Injection)**:
   - Toàn bộ subcommands CLI thực thi trong không gian bộ nhớ tiến trình Python, không dùng `subprocess` hay shell commands ngoài luồng.
3. **CWE-20 (Improper Input Validation)**:
   - Chuẩn hóa đầu vào người dùng, alias mapping và document slug an toàn.
4. **RULE-2.5 (Windows Encoding Standard)**:
   - Đảm bảo tương thích hoàn toàn UTF-8 trên Windows PowerShell.
