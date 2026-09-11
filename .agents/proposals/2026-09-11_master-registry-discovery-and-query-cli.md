---
proposal_id: "2026-09-11_master-registry-discovery-and-query-cli"
type: "tool"
name: "master-registry-discovery-and-query-cli"
status: "merged"
priority: "Cao"
related_issue: "#258"
merged_pr: "#263"
merged_commit: "b4dd92a2"
merged_date: "2026-09-11"
proposed_by_project: "ccba-legal-knowledge"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-09-11"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Pháp điển"
---

# Đề Xuất Nâng Cấp Package `ccba-legal-intel`: Master Registry Discovery, Query CLI Subcommands & Chuẩn Hóa Đường Dẫn Spoke (Issue #258)

## 1. Tóm Tắt & Vấn Đề Thực Tế Cần Giải Quyết
Qua quá trình triển khai thực tế giữa Hub (`ccba-agent-platform`) và Spoke Tri thức Gốc (`ccba-legal-knowledge`) cùng các Spoke tiêu thụ (Thẩm tra, Thiết kế, Phần mềm), phát hiện các hạn chế nghiêm trọng sau:
1. **Lỗi định vị Registry khi cài đặt dạng Editable (`pip install -e`)**:
   - `resolve_project_root()` duyệt ngược từ `Path(__file__).resolve()`. Khi package cài đặt trong Spoke, `__file__` luôn trỏ về `packages/ccba-legal-intel` trong Hub và nạp `legal_registry.yaml` giả lập (chỉ có 7 văn bản mock) thay vì 42 văn bản quy chuẩn của kho tri thức Master.
2. **Thiếu công cụ tra cứu dòng lệnh (CLI Subcommands)**:
   - CLI `python -m ccba_legal` trước đây chỉ hỗ trợ ingestion/convert (`fetch`, `convert`, `consolidate`, `sync`, `lint`) mà thiếu hoàn toàn các lệnh tra cứu nhanh (`query`, `get-clause`, `get-table`).
3. **Bất nhất quy ước đường dẫn lưu trữ tri thức tại Spoke nghiệp vụ**:
   - `sync_spoke.py` sao chép vào `.\.md\legal_docs\`, trong khi `python -m ccba_legal sync` mặc định lưu vào `.\legal_docs\` (cấp 1), gây xung đột với ADR 0033 và ADR 0036.
4. **Thiếu Facade API thống nhất theo ADR 0026 / ADR 0035**:
   - Chưa có lớp `LegalKnowledgeEngine` đóng vai trò entrypoint thống nhất cho toàn bộ tác vụ tra cứu metadata, bóc tách điều khoản AST và truy xuất bảng số liệu 2D.

## 2. Giải Pháp Kỹ Thuật Đã Triển Khai
1. **Thuật toán Định vị Master Registry Đa Tầng (Multi-Tier Discovery - Read-Only)**:
   - Hàm `discover_master_registry_path()` ưu tiên:
     a) Tham số truyền trực tiếp `registry_path`.
     b) Biến môi trường `CCBA_LEGAL_REGISTRY_PATH` / `CCBA_LEGAL_KNOWLEDGE_PATH`.
     c) Cấu hình trong `.md/workspace_context.yaml`.
     d) Đọc Spoke Registry trên Hub (`.md/data/spoke_registry_decrypted.yaml` hoặc `spoke_registry.yaml`) tìm Spoke `archetype: "knowledge_corpus"` hoặc `ccba-legal-knowledge`.
     e) Danh sách đường dẫn ứng viên cục bộ (`~/GitHubProjects/ccba-legal-knowledge`, v.v.).
     f) Fallback an toàn về mock test registry để bảo vệ 100% các unit test nội bộ.
   - `LegalRegistryManager` giữ nguyên mặc định local để tránh nguy cơ Spoke ghi đè làm hỏng Master Registry SSOT.
2. **Lớp Facade `LegalKnowledgeEngine` (ADR 0035)**:
   - Tích hợp in-memory cache cho bundle, hàm bóc tách điều khoản chuẩn mực **Tier-Aware Semantic Slicing** (phân biệt cấp độ Điều vs Khoản, tránh dừng sớm ở tiểu mục con), và chuẩn hóa Alias Parser (`d1` -> `dieu-1`, `d15k2` -> `dieu-15-khoan-2`).
   - Hàm `csv_to_markdown` tự động căn chỉnh độ rộng cột và escape ký tự pipe `\|`.
   - Bảo vệ an ninh hai tầng (Two-Tier Containment) chống Path Traversal (CWE-22) kết hợp Regex Whitelist và `is_relative_to()`.
3. **Bổ sung 3 CLI Subcommands trong `ccba_legal.cli`**:
   - `python -m ccba_legal query "<keyword>"`: Tìm kiếm văn bản, hiển thị bảng console màu sắc với nhãn hiệu lực (CURRENT / SUPERSEDED) và văn bản thay thế.
   - `python -m ccba_legal get-clause --doc <slug> --clause <clause_id>`: Bóc tách nhanh toàn văn điều khoản.
   - `python -m ccba_legal get-table --doc <slug> --table <table_id> [--format csv|markdown]`: Trích xuất bảng số liệu 2D.
   - Cưỡng chế `sys.stdout.reconfigure(encoding="utf-8")` theo RULE-2.5 chống lỗi `cp1252` trên Windows terminal.
4. **Chuẩn Hóa Đường Dẫn Lưu Trữ Tri Thức Spoke**:
   - `pull_latest_okf_bundles` tự động phân loại: Spoke nghiệp vụ lưu vào `.\.md\legal_docs\` (ADR 0033); Master Spoke lưu tại `legal_docs/` (ADR 0036).

## 3. Các Tệp Tin Thay Đổi
- [NEW] `packages/ccba-legal-intel/src/ccba_legal/engine.py`: Lớp Facade `LegalKnowledgeEngine`, Tier-Aware Slicing, Two-tier CWE-22 protection, `canonicalize_clause_id`, `csv_to_markdown`.
- [MODIFY] `packages/ccba-legal-intel/src/ccba_legal/registry.py`: Hàm `discover_master_registry_path()`, ủy quyền `query()` sang engine mới.
- [MODIFY] `packages/ccba-legal-intel/src/ccba_legal/cli.py`: Cấu hình UTF-8, thêm 3 subcommands `query`, `get-clause`, `get-table`.
- [MODIFY] `packages/ccba-legal-intel/src/ccba_legal/sync/engine.py`: Chuẩn hóa default `.md/legal_docs`, mở rộng danh mục `04_appendices`.
- [MODIFY] `packages/ccba-legal-intel/src/ccba_legal/federated_rag.py`: Hỗ trợ đệ quy nạp toàn bộ 42 bundle trong các danh mục `01_vbpl`, `02_qcvn`, `03_tcvn`, `04_appendices`.
- [MODIFY] `packages/ccba-legal-intel/src/ccba_legal/__init__.py`: Export `LegalKnowledgeEngine` vào `__all__`.
- [MODIFY] `.agents/skills/ccba-legal-intel/SKILL.md`: Bổ sung hướng dẫn CLI mới và Facade API.
- [MODIFY] `packages/ccba-legal-intel/AGENTS.md`: Bổ sung `LegalKnowledgeEngine` vào danh mục Public Deep Seams.
- [MODIFY] `packages/ccba-legal-intel/tests/test_cli_doc_parity.py`: Mở rộng test contract parity với `SKILL.md`.
- [NEW] `packages/ccba-legal-intel/tests/test_legal_knowledge_engine.py`: 12 unit tests kiểm thử toàn diện `LegalKnowledgeEngine`.
- [NEW] `packages/ccba-legal-intel/tests/test_registry_discovery.py`: 7 unit tests kiểm thử các tầng ưu tiên discovery.
- [NEW] `.agents/proposals/2026-09-11_master-registry-discovery-and-query-cli.md`: Đề xuất Proposal chuẩn ADR 0045.

## 4. Kết Quả Kiểm Thử & Nghiệm Thu
- **Unit Tests**: 31/31 passed in 14.36s (`test_parser_registry.py`, `test_cli_doc_parity.py`, `test_legal_knowledge_engine.py`, `test_registry_discovery.py`, `test_sync_spoke.py`).
- **Linter**: `ruff check packages/ccba-legal-intel` đạt 100% clean.
- **Deterministic Hard Completion Lock (ADR-0058)**: `python -m ccba_harness verify-patch` đạt trạng thái `ALL PASSED` (2/2 passed, Exit Code 0).
- **Thực tế CLI**: Đã chạy thử nghiệm thành công `query`, `get-clause`, `get-table` trên PowerShell Windows không gặp lỗi encoding.
