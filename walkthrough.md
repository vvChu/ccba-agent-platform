# Walkthrough: Tái Cấu Trúc AGENTS.md theo Mô hình Progressive Disclosure

Đã hoàn thành tái cấu trúc toàn diện hệ thống chỉ dẫn của CCBA Platform dựa trên các quyết định từ phiên `/ccba-grill-with-docs` và chuẩn mực từ bài viết *"A Complete Guide To AGENTS.md"* của Matt Pocock.

---

## 🎯 Các Hạng Mục Đã Thực Hiện

### 1. Root Configuration & Cross-Agent Parity Bridge
- **`AGENTS.md`**: Tinh gọn mỏ neo định vị Platform còn dưới 25 dòng (< 300 tokens), giữ các bất biến cốt lõi (Hub vs Spoke, Reuse-First Gate, Session Learnings, Automation Quality).
- **`CLAUDE.md`**: Cầu nối tương thích chuẩn mực cho Claude Code tại thư mục gốc repository.
- **`.agents/AGENTS.md`**: Đồng bộ cấu trúc tối giản với root `AGENTS.md`.

### 2. Phân rã Quy chuẩn Chuyên biệt (`docs/rules/`)
- **`docs/rules/execution_guardrails.md`**: 8 Execution Guardrails (Scoped Pytest, Anti-Polling, TDD Cap, Safe Process Termination, 2-Tier Test Speed).
- **`docs/rules/git_conventions.md`**: Quy chuẩn branch naming, commit types, và atomic logical units.
- **`docs/rules/code_quality.md`**: Automation-First quality gates, Deep Seams, KISS architecture.

### 3. Phân tầng Monorepo (`packages/*/AGENTS.md`)
Đã thiết lập 8 tệp `AGENTS.md` tinh gọn (3-6 dòng) xác định Public Deep Seams và scoped test commands:
- `packages/ccba-ai/AGENTS.md`
- `packages/ccba-harness/AGENTS.md`
- `packages/ccba-legal-intel/AGENTS.md`
- `packages/ccba-maskara/AGENTS.md`
- `packages/ccba-notebooklm/AGENTS.md`
- `packages/ccba-ooxml/AGENTS.md`
- `packages/ccba-pdf-prep/AGENTS.md`
- `packages/mdconverter/AGENTS.md`

### 4. Ghi nhận Hồ sơ Kiến trúc & Thuật ngữ Miền
- **5 ADRs mới**: ADR 0030, ADR 0031, ADR 0032, ADR 0033, ADR 0034 trong `docs/adr/`.
- **8 Thuật ngữ chuẩn hóa** được bổ sung vào `CONTEXT.md`.

---

## 🤖 Giải Trình & Đối Soát Nhận Xét Của Copilot (PR #193)

Tất cả 6 nhận xét của Copilot đã được tiếp thu, đối soát trực tiếp với `__init__.py` của các packages và sửa lỗi trong commit `348fc4b`:

- **Comment 3788190826** (`packages/ccba-harness/AGENTS.md`): Đã cập nhật import seams thành `HarnessEngine, HarnessGuard, FileMutexLock, HarnessLocal`.
- **Comment 3788190838** (`packages/ccba-legal-intel/AGENTS.md`): Đã cập nhật import seams thành `LegalIntelPipeline, LegalProcessor, LegalSyncEngine, LegalRegistryManager, LegalGroundingGate`.
- **Comment 3788190843** (`packages/ccba-notebooklm/AGENTS.md`): Đã cập nhật import seams thành `CCBANotebookLMClient, NotebookLMClient, get_client, query_rag, handle_artifact_flow, extract_and_summarize`.
- **Comment 3788190852** (`packages/mdconverter/AGENTS.md`): Đã cập nhật import seams thành `ConversionPipeline, ConverterRegistry, BaseConverter, ConversionResult, get_settings`.
- **Comment 3788190859** (`packages/ccba-maskara/AGENTS.md`): Đã cập nhật import seams thành `MaskaraScanner, detect_secrets_in_text, redact_secrets_in_text`.
- **Comment 3788190865** (`packages/ccba-ooxml/AGENTS.md`): Đã cập nhật import seams thành `pack_document, unpack_document, validate_document, OOXMLWorkspace, recalc_xlsx, DocxDocument`.

---

## 🧪 Kết quả Kiểm chứng (Validation)

1. **Linter Static Verification**:
   - `ruff check packages/` $\rightarrow$ **All checks passed!**
2. **Comprehensive Test Suite**:
   - `python scripts/eval/run_isolated_tests.py --all --stress` $\rightarrow$ **10/10 Targets Passed (100% Pass)**.
