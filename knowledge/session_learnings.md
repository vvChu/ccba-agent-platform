# Session Learnings - Kiến thức tích lũy

> [!NOTE]
> File này được cập nhật tự động thông qua workflow `/session-retrospective`.
> Chứa các kiến thức có giá trị nhất được phát hiện qua các phiên làm việc.

## Cập nhật gần nhất: 2026-03-28 (Session abaca450)

---

## 📐 Patterns (Mẫu tốt)

### Skill-Driven Agent Architecture for Domain Knowledge

- **Ngữ cảnh**: Khi cần AI Agent hỗ trợ lặp lại các tác vụ chuyên ngành (VBPL, checklist, seminar)
- **Vấn đề giải quyết**: Mỗi phiên làm việc phải giải thích lại context, templates, quy trình
- **Giải pháp**:

  1. Tạo `.agent/skills/[tên-skill]/` với cấu trúc: SKILL.md + data/ + templates/

  2. SKILL.md chứa hướng dẫn cho Agent: When to Use, How to Use, Key Files

  3. Data files dùng YAML cho structured data (registry, checklist)

  4. Templates dùng Markdown với placeholders `{{VAR}}`

  5. Workflows (`.agent/workflows/`) orchestrate nhiều skills
- **Ví dụ**: 3 skills (legal-document-tracker, completion-checklist, seminar-builder) + 2 workflows
- **Files**:
  - `.agent/skills/legal-document-tracker/` (5 files)
  - `.agent/skills/completion-checklist/` (4 files)
  - `.agent/skills/seminar-builder/` (4 files)
  - `.agent/workflows/prepare-seminar.md`
  - `.agent/workflows/update-legal-registry.md`
- **Nguồn**: Session f21c8edb, 2026-03-28

---

### OneDrive Unicode Path Resolution Pattern

- **Ngữ cảnh**: Khi cần truy cập folders trên OneDrive có tên tiếng Việt (Unicode)
- **Vấn đề giải quyết**: `list_dir` tool fail do NFC/NFD encoding mismatch; `Get-ChildItem -Recurse` treo do cloud-only files-on-demand
- **Giải pháp**:

  1. Dùng `.NET API` thay vì PowerShell cmdlets:

     ```powershell
     [System.IO.Directory]::GetDirectories($path)
     ```

  2. Hoặc dùng `-Filter` thay vì `-Recurse` khi tìm folder cụ thể:

     ```powershell
     Get-ChildItem $root -Recurse -Filter "BIM_VBPL" -Directory
     ```

  3. Redirect output ra file nếu console truncate Unicode:

     ```powershell
     ... | Out-File "output.txt" -Encoding utf8
     ```
- **Nguồn**: Session f21c8edb, 2026-03-28

---

### VBPL Registry YAML Pattern

- **Ngữ cảnh**: Khi cần theo dõi nhiều VBPL với metadata phức tạp (trạng thái, thay thế, hiệu lực)
- **Vấn đề giải quyết**: VBPL thay đổi liên tục, cần single source of truth
- **Giải pháp**:

  1. YAML registry với các section: laws, decrees, standards, seminars, monitoring

  2. Mỗi entry có: id, title, status, effective_date, replaces/replaced_by, local_files

  3. Monitoring section theo dõi VBPL chưa ban hành (status: pending/watching/fulfilled)

  4. Validate bằng `yaml.safe_load()` sau mỗi cập nhật
- **File**: `.agent/skills/legal-document-tracker/registry/legal_registry.yaml`
- **Nguồn**: Session f21c8edb, 2026-03-28

---

### Multi-Skill Workflow Orchestration Pattern

- **Ngữ cảnh**: Khi một quy trình cần kết hợp nhiều skills khác nhau
- **Vấn đề giải quyết**: Skills hoạt động độc lập, cần kết nối thành flow hoàn chỉnh
- **Giải pháp**:

  1. Workflow file (`.agent/workflows/`) mô tả các bước tuần tự

  2. Mỗi bước reference đến skill cụ thể và template cần dùng

  3. Workflow có thể gọi workflow khác (VD: `/prepare-seminar` gọi `/update-legal-registry`)

  4. Output bước trước là input bước sau
- **Ví dụ**: `/prepare-seminar` → thu thập → recap (seminar-builder) → check VBPL (legal-tracker) → agenda → xuất file
- **Nguồn**: Session f21c8edb, 2026-03-28

---

### Self-Learning Feedback System for Document Conversion

- **Ngữ cảnh**: Khi cần hệ thống tự động phát hiện và sửa lỗi format trong markdown
- **Vấn đề giải quyết**: Lỗi conversion lặp lại, cần human review từng file
- **Giải pháp**:

  1. Tạo `feedback_rules.yaml` lưu trữ các rules học được

  2. Implement `FeedbackRulesEngine` để detect issues

  3. CLI commands: `list-rules`, `check`, `fix`, `add-rule`, `stats`

  4. Context-aware detection (nhận diện văn bản pháp lý)
- **Files**:
  - `scripts/feedback_rules.yaml` (8 rules)
  - `scripts/feedback_manager.py` (CLI + Engine)
  - `scripts/structural_validator.py` (Auto-fix)
- **Nguồn**: Session a7a841ef, 2026-01-04

---

### Vietnamese Legal Document Formatting Best Practice

- **Ngữ cảnh**: Format văn bản pháp lý VN trong Markdown
- **Vấn đề giải quyết**: Quá nhiều bullet/bold làm rối cấu trúc
- **Giải pháp - Nguyên tắc tối giản**:

  1. **Tiêu đề phụ** ("Đối với..."): Text thường + dấu `:`, KHÔNG bullet/bold

  2. **Điểm a, b, c, d**: Text thường, mỗi điểm một paragraph

  3. **Danh sách items**: Chỉ dùng bullet `-` cho items ngang cấp thực sự

  4. **Cấu trúc phân cấp**: Chương → Mục → Điều → Khoản (1,2,3) → Điểm (a,b,c)

  5. **Spacing Enforcement**: BẮT BUỘC có dòng trống trước các mục a, b, c (liệt kê) để tránh dính dòng.
- **Ánh xạ Markdown**:

  | Cấp pháp lý | Markdown |
  | ------------- | ---------- |
  | Chương | `## Chương I` |
  | Điều | `### Điều 8` |
  | Khoản | `#### 8.1` |
  | Điểm | `a. Nhiệm vụ...` |

- **Files**:
  - `brain/legal_format_guide.md` (Hướng dẫn chi tiết)
  - `scripts/apply_best_practices.py` (Batch apply)
- **Nguồn**: Session a7a841ef, 2026-01-04

---

### Context-Aware Legal Document Detection

- **Ngữ cảnh**: Tránh false positive khi check repeated_numbering trong văn bản pháp lý
- **Vấn đề giải quyết**: Văn bản pháp lý VN có cấu trúc mỗi Điều có danh sách số riêng (1,2,3 reset)
- **Giải pháp**:

  1. Detect markers: `Điều \d+`, `Chương [IVX]+`, `Khoản \d+`, `Quy chế`, `Nghị định`

  2. Nếu là legal doc → dùng `_check_true_repeated_numbering()` (chỉ flag 3+ consecutive "1." without 2+)

  3. Nếu không phải legal doc → dùng pattern matching chuẩn

- **Code**:

  ```python
  def _is_legal_document(self, content: str) -> bool:
      legal_markers = [r'Điều \d+\.', r'Chương [IVX]+\.', ...]
      return any(re.search(m, content) for m in legal_markers)
  ```

- **Nguồn**: Session a7a841ef, 2026-01-04

---

### LlamaParse for Scanned PDF Processing

- **Ngữ cảnh**: Khi cần xử lý PDF scan (không có text layer) trong RAG pipeline
- **Vấn đề giải quyết**: Gemini OCR tạo chunks kém chất lượng (18 chunks), không preserve structure
- **Giải pháp**:

  1. Sử dụng LlamaParse API làm primary parser

  2. LlamaParse preserve document structure (headers/tables)

  3. Kết quả: 678 chunks chất lượng cao vs 18 với Gemini OCR

- **Config**:

```python
## LlamaCloud API integration

LLAMAPARSE_API_KEY = "llx-..."
```text

- **Nguồn**: Session a50f3a98, 2025-11-21

---

### DeepSeek with Groq Fallback Pattern

- **Ngữ cảnh**: Khi sử dụng nhiều LLM providers cho generation
- **Vấn đề giải quyết**: API key insufficient balance hoặc rate limit
- **Giải pháp**:

  1. Implement primary generator (DeepSeek)

  2. Automatic fallback to secondary (Groq llama-3.3-70b-versatile)

  3. Log warning nhưng không fail transaction

- **Nguồn**: Session memorized, ongoing

---

### Markdown List Formatting Pattern

- **Ngữ cảnh**: Chuyển đổi legal documents (docx/pdf) sang markdown
- **Vấn đề giải quyết**: List items bị merge hoặc bullet format sai
- **Giải pháp**:

  1. Dùng regex rules trong self-learning system

  2. Detect merged items (a, b, c, d trên cùng dòng)

  3. Split và format lại với proper indentation

- **Nguồn**: Session a7a841ef, 2026-01-03

---

### Document Migration with Standardized Naming

- **Ngữ cảnh**: Khi cần hợp nhất tài liệu từ legacy folder sang cấu trúc mới
- **Vấn đề giải quyết**: Tên file tiếng Việt với ký tự đặc biệt, format không nhất quán
- **Giải pháp**:

  1. Giữ nguyên content tiếng Việt gốc

  2. Đổi tên file sang English với prefix phân loại (REG_, PROC_, DEC_, IDOP_)

  3. Thêm YAML Front Matter với metadata (title, source_file, date, status)

  4. Sử dụng underscore thay vì space

- **Ví dụ**:
  - `qđ486.2023_chức năng.md` → `DEC_486_Functions_and_Duties.md`
  - `idop v3.0 nền tảng.md` → `IDOP_Integrated_Platform_Spec.md`
- **Nguồn**: Session 878ac215, 2026-01-03

---

### Single Source of Truth Pattern

- **Ngữ cảnh**: Khi có nhiều version/summary của cùng một tài liệu
- **Vấn đề giải quyết**: Redundancy dẫn đến confusion, outdated info
- **Giải pháp**:

  1. Identify authoritative source (full legal text, detailed spec)

  2. Remove/archive abbreviated summaries

  3. Rename authoritative file với naming convention chuẩn

  4. Verify content completeness trước khi xóa redundant files

- **Áp dụng**:
  - `QD486_Full_Content.md` (summary) → Replaced by `DEC_486_Functions_and_Duties.md` (full)
  - `IDOP_Architecture.md` (high-level) → Replaced by `IDOP_Integrated_Platform_Spec.md` (detailed)
- **Nguồn**: Session 878ac215, 2026-01-03

---

### CCBA OPS 2025 Folder Structure Convention

- **Ngữ cảnh**: Thiết kế cấu trúc folder cho tài liệu quản trị doanh nghiệp
- **Vấn đề giải quyết**: Tài liệu phân tán, khó tìm kiếm
- **Giải pháp**: Cấu trúc 4 cấp theo chức năng:

  ```txt

  CCBA_OPS_2025/
  ├── 01_GOVERNANCE/       # Quy chế, cơ cấu, chiến lược
  │   ├── 1.1_Co_cau_To_chuc/
  │   └── 1.2_Chien_luoc_Phat_trien/
  ├── 02_REGULATIONS/      # Quy chế tài chính, KHCN, dự án
  │   ├── 2.1_Quy_che_Tai_chinh_2025/
  │   └── 2.3_Quy_che_Quan_ly_Du_an/
  ├── 03_PROCESS/          # Quy trình nghiệp vụ
  │   └── 3.1_Quy_trinh_Loi/
  └── 04_DIGITAL_PLATFORM/ # IDOP specs, appendices
      └── 4.1_He_thong_Kien_truc/

  ```

- **Nguồn**: Session 878ac215, 2026-01-03

---

## ⛔ Anti-patterns (Cách tránh)

### Avoid OneDrive Recursive Listing on Cloud-Only Folders

- **Vấn đề**: `Get-ChildItem -Recurse` trên OneDrive cloud-only folders sẽ trigger download từng file, có thể treo vô hạn (>2 phút không output)
- **Thay thế bằng**:
  - Dùng `-Filter` để tìm folder cụ thể: `Get-ChildItem $root -Recurse -Filter "FolderName" -Directory`
  - Hoặc dùng `-Depth 0` để chỉ list level hiện tại
  - Yêu cầu user "make available offline" trước khi truy cập
- **Nguồn**: Session f21c8edb, 2026-03-28

---

### Avoid list_dir Tool for Vietnamese Unicode Paths on OneDrive

- **Vấn đề**: `list_dir` tool không xử lý đúng Unicode NFC/NFD encoding cho tên folder tiếng Việt trên OneDrive (VD: `04_ĐÀO_TẠO_NỘI_BỘ` — parent list OK nhưng vào bên trong thì "directory does not exist")
- **Thay thế bằng**: PowerShell Get-ChildItem hoặc .NET `[System.IO.Directory]::GetDirectories()`
- **Nguồn**: Session f21c8edb, 2026-03-28

---

### Avoid Excessive Bullets in Legal Documents

- **Vấn đề**: Dùng bullet cho mọi thứ khiến văn bản pháp lý khó đọc, mất phân cấp
- **Thay thế bằng**:
  - Tiêu đề phụ: Text thường (không bullet)
  - Điểm a, b, c: Text thường (không bullet)
  - Chỉ dùng bullet cho danh sách items ngang cấp thực sự
- **Nguồn**: Session a7a841ef, 2026-01-04

---

### Avoid Bold for Introductory Phrases

- **Vấn đề**: Dùng `**Đối với...**` làm visual noise, không cần thiết
- **Thay thế bằng**: Text thường + dấu hai chấm: `Đối với các hợp đồng Viện ký:`
- **Nguồn**: Session a7a841ef, 2026-01-04

---

### Avoid Table-Broken Numbering

- **Vấn đề**: Khi chèn bảng vào giữa danh sách số, Markdown parser thường reset số về 1.
- **Giải pháp**: Kiểm tra kỹ đánh số sau bảng. Sử dụng hard-coded numbering (3., 4.) nếu cần.
- **Nguồn**: Session a7a841ef, 2026-01-04

---

### Avoid Merged Variable Definitions

- **Vấn đề**: Định nghĩa biến (VD: `TLCN: ...`) viết liền nhau bị merge.
- **Giải pháp**: Chuyển thành Bullet List (`- Key: Value`).
- **Nguồn**: Session a7a841ef, 2026-01-04

---

### Avoid Enable Reranker on CPU

- **Vấn đề**: Reranking rất chậm (~60s) trên CPU, blocking retrieval
- **Thay thế bằng**:
  - Set `ENABLE_RERANKER=False` cho CPU-only deployment
  - Retrieval time: ~800ms vs 80s
- **Nguồn**: User global memory, ongoing

---

### Avoid Large Context Window for RAG

- **Vấn đề**: Stuffing quá nhiều chunks vào context gây hallucination
- **Thay thế bằng**:
  - Balancing broad understanding với specialized expertise
  - Prioritize và organize information effectively
- **Nguồn**: Best practices research, 2026-01-04

---

### Avoid Soft Numbering in Complex Lists

- **Vấn đề**: Trong Markdown, nếu danh sách bị ngắt quãng bởi nội dung khác, số thứ tự sẽ reset về `1.`.
- **Giải pháp**: Hardcode số thứ tự (1., 2., 3...) cho danh sách phức tạp.
- **Nguồn**: Session a7a841ef (Section 14.3.4 Fix), 2026-01-04

---

---

## 🔧 Solutions (Giải pháp tham chiếu)

### Batch Apply Formatting Best Practices

- **Vấn đề**: Cần áp dụng format chuẩn cho nhiều files cùng lúc
- **Giải pháp**:

  1. Chạy dry-run để preview: `python apply_best_practices.py --dry-run`

  2. Apply changes: `python apply_best_practices.py`

  3. Script tự detect legal documents và apply rules

- **Kết quả mẫu**: 56 fixes across 7 files
- **Files liên quan**: `scripts/apply_best_practices.py`
- **Nguồn**: Session a7a841ef, 2026-01-04

---

### Fix Milvus max_length Exception

- **Vấn đề**: `MilvusException` khi field vượt quá `max_length` 500 chars
- **Giải pháp**:

  1. Xác định schema limits trong `src/vector_store/milvus.py`

  2. Implement truncation trong `src/ingestion/layout_chunker.py`

  3. Truncate metadata fields trước khi insert

- **Files liên quan**:
  - `src/vector_store/milvus.py`
  - `src/ingestion/layout_chunker.py`
- **Nguồn**: Session ba0f7366, 2025-11-30

---

### Format Bold Headers Pattern

- **Ngữ cảnh**: Các tiêu đề dạng `**1. Header**` trong văn bản Markdown.
- **Vấn đề**: Nếu không có dòng trống theo sau, tiêu đề bị gộp với đoạn văn bản kế tiếp.
- **Giải pháp**:
  - Detect bold headers (`**\d+...**`) ngay trước text.
  - Insert blank line (`\n\n`) vào giữa.
- **Nguồn**: Session a7a841ef (Rule 7), 2026-01-04

---

### Batch Convert Missing Files Solution

- **Vấn đề**: Folder chứa hỗn hợp file nguồn (.pdf) và file đã convert (.md), cần tìm file chưa convert.
- **Giải pháp**:

  1. Scan đệ quy folder tìm file source (.pdf, .doc, .docx).

  2. Check file .md tương ứng (cùng tên).

  3. Nếu thiếu -> Gọi `convert_documents.py`.
- **Script**: `scripts/batch_convert_missing.py`
- **Nguồn**: Session a7a841ef, 2026-01-04

---

### Systematic Numbering Validation Solution

- **Vấn đề**: Đảm bảo không còn file nào bị lỗi "Repeated 1." (Reset numbering).
- **Giải pháp**:

  1. Script `check_numbering_continuity.py`.

  2. Scan file md, đếm tỷ lệ "1." so với "2." trong từng mục.

  3. Flag warning nếu tỷ lệ lệch (nhiều "1." nhưng không có "2.").

- **Nguồn**: Session a7a841ef, 2026-01-04

---

### Smart Indexing for Scanned PDFs

- **Vấn đề**: OCR heavy usage triggers Gemini API rate limits
- **Giải pháp**:

  1. Sử dụng `run_smart_indexing.py` với LlamaParse integration

  2. Robust, resumable indexing

  3. Skip already-indexed files
- **Nguồn**: User global memory, ongoing

---

### IDOP Documentation Migration to CCBA_OPS_2025

- **Vấn đề**: Tài liệu IDOP v3.0 nằm rải rác trong legacy folder, các appendix không được migrate
- **Giải pháp**:

  1. Xác định danh sách files cần migrate (Platform Spec, DB Design, Appendices A-G)

  2. Đọc nội dung từng file, thêm YAML Front Matter

  3. Đổi tên theo naming convention (IDOP_Appendix_X_*.md)

  4. Ghi vào thư mục đích `04_DIGITAL_PLATFORM/4.1_He_thong_Kien_truc/`

  5. Xóa redundant files (IDOP_Architecture.md)

- **Files đã migrate**:
  - `IDOP_Integrated_Platform_Spec.md`
  - `IDOP_Database_Logical_Design.md`
  - `IDOP_Appendix_A_Compliance_Framework.md`
  - `IDOP_Appendix_B_Knowledge_Map.md`
  - `IDOP_Appendix_C_UI_Mockup.md`
  - `IDOP_Appendix_E_Access_Control.md`
  - `IDOP_Appendix_F_KPI_Data_Structure.md`
  - `IDOP_Appendix_G_Views_JSON_Templates.md`
  - `PROC_Hybrid_Workflow_Methodology.md` (→ 03_PROCESS)
- **Nguồn**: Session 878ac215, 2026-01-03

---

## ⚙️ Configurations (Cấu hình tối ưu)

| Setting | Value | Lý do | Áp dụng khi |
| --------- | ------- | ------- | ------------- |
| `ENABLE_RERANKER` | `False` | Retrieval ~800ms vs 80s | CPU-only deployment |
| `MILVUS_HNSW_EF_SEARCH` | `32` | Balance speed/accuracy | General use |
| `PDF_MAX_PAGES_SINGLE_PASS` | `20` | Ensure chunking triggers | PDF > 20 pages |
| Primary Parser | LlamaParse | 678 vs 18 chunks | Scanned PDFs |
| Primary Generator | Groq llama-3.3-70b | Fast, reliable fallback | DeepSeek unavailable |

---

## 🔗 Integrations (Tích hợp)

### RAG System Architecture

- **Primary Parser**: LlamaParse (scanned) → LayoutChunker (Markdown)
- **Vector Store**: Milvus với HNSW index
- **Generator**: DeepSeek → Groq (fallback)
- **Frontend**: Streamlit (app.py) + FastAPI (server.py)
- **Launch Script**: `start_app.bat` cho simultaneous launch

---

### Self-Learning Feedback System Architecture

- **Rules Storage**: `feedback_rules.yaml` (8 rules)
- **Detection Engine**: `FeedbackRulesEngine` in `feedback_manager.py`
- **CLI Interface**: `feedback_manager.py` (list-rules, check, fix, add-rule, stats)
- **Batch Analysis**: `batch_analyze.py`
- **Best Practice Apply**: `apply_best_practices.py`

---

## 📝 Session History

| Date | Session ID | Topic | Patterns Added |
| ---- | ---------- | ----- | -------------- |
| 2026-03-28 | 227a7981 | **Platform Finalization & Phase 2 Discovery** | 3 patterns, 2 anti-patterns, 1 solution |
| 2026-03-28 | f21c8edb | **VBPL Skills/Workflows & Seminar Preparation** | 4 patterns, 2 anti-patterns, 1 solution |
| 2026-01-04 | a7a841ef | **Markdownlint Compliance & Full System Consolidation** | 2 patterns, 1 config, 3 solutions |
| 2026-01-04 | a7a841ef | Self-Learning & Auto-Format Best Practices | 4 patterns, 2 anti-patterns, 2 solutions |
| 2026-01-04 | 878ac215 | CCBA Strategic Docs & IDOP Migration | 3 patterns, 1 solution |
| 2026-01-03 | a7a841ef | Fixing Legal Document Formatting | Markdown rules |
| 2025-11-30 | ba0f7366 | Fix Milvus Metadata | Truncation pattern |
| 2025-11-21 | a50f3a98 | Refine RAG Data Quality | LlamaParse pattern |

---

## Session 2026-01-04 (Markdownlint Compliance)

### Patterns Added

#### Markdownlint Config for Vietnamese Legal Docs
- **Ngữ cảnh**: Khi cần đảm bảo markdown compliance mà không phá vỡ format văn bản pháp lý VN
- **Vấn đề giải quyết**: Các rule strict (MD007, MD022, MD032) không phù hợp với convention VN
- **Giải pháp**: Disable các rules không phù hợp trong `.markdownlint.json`:
  - `MD003, MD005, MD007, MD009, MD013, MD022, MD023, MD024, MD025, MD026, MD029, MD030, MD032, MD033, MD034, MD035, MD036, MD041, MD046`
- **File**: `.markdownlint.json`

#### Unified CLI Pattern (main.py)
- **Ngữ cảnh**: Thay vì nhiều scripts riêng lẻ, dùng 1 entry point
- **Giải pháp**: `scripts/main.py` với subcommands: `convert`, `scan-missing`, `validate`, `fix`
- **File**: `scripts/main.py`

### Solutions Added

#### 14-Rule Auto-Fix System
- **Vấn đề**: Cần tự động fix nhiều loại lỗi format
- **Giải pháp**:
  - Rule 1-7: Legal doc formatting (bullets, bold, spacing)
  - Rule 8-9: Table spacing (MD060), Code block lang (MD040)
  - Rule 10: Header normalization (MD025)
  - Rule 11-14: Spacing, Style, Indent, Newline (MD022, MD032, MD004, MD007, MD047)
- **File**: `scripts/apply_best_practices.py`

#### Environment Variable Security
- **Vấn đề**: API keys hardcoded trong config.py
- **Giải pháp**:
  - Sử dụng `.env` file với `python-dotenv`
  - `config.py` tự động load `.env`
  - `.gitignore` đã có `.env`
- **Files**: `config.py`, `.env`, `.env.example`

### Anti-patterns Identified

#### Avoid Strict Markdown Lint Rules for Legal Docs
- **Vấn đề**: MD007 (indent 0), MD022 (blank around headers) phá vỡ cấu trúc VN
- **Thay thế**: Disable các rules không phù hợp, chỉ giữ MD040, MD060

---

## Cập nhật: 2026-01-04 (Session Retrospective - Phase 19-20)

### Patterns Added

#### Modern Python Project Setup Pattern
- **Ngữ cảnh**: Tạo Python CLI tool từ đầu với best practices 2025
- **Vấn đề giải quyết**: Cần setup chuẩn để publish PyPI, CI/CD
- **Giải pháp**:
  - **src/ layout**: `src/mdconverter/` (tránh import conflicts)
  - **pyproject.toml**: Build system với hatchling (thay setup.py)
  - **Pydantic Settings**: Config validation + .env loading
  - **Typer CLI**: Modern CLI với auto-completion (thay argparse)
  - **Ruff**: Fast linter (100x faster than Flake8)
  - **MyPy**: Strict type checking
  - **pytest + coverage**: Testing with reports
- **Files**: `pyproject.toml`, `src/mdconverter/`, `.pre-commit-config.yaml`

#### GitHub Workflow Pattern
- **Ngữ cảnh**: Setup repo mới trên GitHub với đầy đủ CI/CD
- **Giải pháp**:
  1. `git init && git add . && git commit -m "Initial commit"`
  2. Tạo repo GitHub qua browser (hoặc gh cli)
  3. `git remote add origin URL && git push -u origin main`
  4. Add topics: Settings → About → Add topics
  5. GitHub Actions tự động chạy trên push
- **Files**: `.github/workflows/ci.yml`

### Solutions Added

#### LlamaParse Integration
- **Vấn đề**: Scanned PDFs cần OCR + structure preservation
- **Giải pháp**:
  - LlamaParse API với async job processing
  - Upload → Poll status → Get markdown result
  - Fallback chain: LlamaParse → Gemini → Pandoc
- **File**: `src/mdconverter/core/llamaparse.py`

#### MkDocs Material Documentation
- **Vấn đề**: Cần documentation site chuyên nghiệp
- **Giải pháp**:
  - `mkdocs.yml` với Material theme + dark mode
  - mkdocstrings auto-generate API docs từ docstrings
  - 8 pages: index, install, quickstart, cli, config, vn-legal, api, contributing
- **Files**: `mkdocs.yml`, `docs/`

### Anti-patterns Identified

#### Avoid argparse for New CLI Projects
- **Vấn đề**: argparse verbose, không có auto-completion/rich output
- **Thay thế**: Typer (based on Click) với type hints, rich integration

#### Avoid Monolithic Scripts
- **Vấn đề**: 1 file lớn khó maintain và test
- **Thay thế**: Plugin architecture với core/ và plugins/ folders

---

## Cập nhật: 2026-03-28 (VBPL Skills/Workflows & Seminar Preparation)

### Patterns Added

#### Skill-Driven Agent Architecture
- **Ngữ cảnh**: Tổ chức AI Agent knowledge thành skills có cấu trúc
- **Giải pháp**: SKILL.md + data/ (YAML) + templates/ (Markdown) trong `.agent/skills/`
- **Files**: 3 skills × (~4 files/skill) + 2 workflows

#### OneDrive Unicode Path Resolution
- **Ngữ cảnh**: Truy cập folders OneDrive có tên tiếng Việt
- **Giải pháp**: Dùng .NET API hoặc PowerShell -Filter thay vì list_dir tool

#### VBPL Registry YAML
- **Ngữ cảnh**: Theo dõi nhiều VBPL với metadata phức tạp
- **Giải pháp**: YAML registry (laws/decrees/standards/monitoring sections)
- **File**: `.agent/skills/legal-document-tracker/registry/legal_registry.yaml`

#### Multi-Skill Workflow Orchestration
- **Ngữ cảnh**: Kết nối nhiều skills thành quy trình hoàn chỉnh
- **Giải pháp**: Workflow files mô tả bước tuần tự, mỗi bước reference skill + template

### Solutions Added

#### Download PDF từ Cổng TTĐT Chính phủ (gov.vn)
- **Vấn đề**: Cần tải văn bản chính thức từ moc.gov.vn
- **Giải pháp**:
  1. Browser subagent tìm trang `moc.gov.vn/vn/Pages/VanBan.aspx`
  2. Xác nhận URL PDF pattern: `moc.gov.vn/Images/FileVanBan/BXD_{SoHieu}_{NgayBanHanh}.pdf`
  3. Download bằng `Invoke-WebRequest -Uri $url -OutFile $path -UseBasicParsing`
- **Ví dụ**: `BXD_19-VBHN-BXD_25032026.pdf` (96 trang, 1.36 MB)
- **Lưu ý**: Trang chi tiết VB có thể bị lỗi 404, nhưng link PDF trực tiếp vẫn hoạt động

### Conventions Added

#### CCBA Seminar Naming Convention
- **Format**: `CCBA_RD_SEMINAR_NNN_RevXX-DD.MM.YY-Title`
  - `NNN`: Số thứ tự (001, 002, 003...)
  - `RevXX`: Revision (Rev00, Rev01...)
  - `DD.MM.YY`: Ngày seminar
  - `Title`: Tên chủ đề (kebab-case)
- **Lưu trữ**: `BIM_VBPL/YYYY/`

### Anti-patterns Identified

#### Avoid OneDrive Recursive Listing
- **Vấn đề**: `-Recurse` trên cloud-only folder trigger download, treo >2 phút
- **Thay thế**: `-Filter` + `-Directory` hoặc yêu cầu "make available offline"

#### Avoid list_dir for Vietnamese OneDrive Paths
- **Vấn đề**: NFC/NFD encoding mismatch → "directory does not exist"
- **Thay thế**: PowerShell Get-ChildItem hoặc .NET API

---

## Cập nhật: 2026-03-28 (Platform Finalization & Phase 2 Discovery)

### Patterns Added

#### Platform-Loader Active Discovery Pattern
- **Ngữ cảnh**: Khi Agent cần truy cập Hub skills/workflows từ bất kỳ workspace nào
- **Vấn đề giải quyết**: Agent chỉ scan `.agent/skills/` trong workspace active → không thấy Hub skills khi ở Spoke
- **Giải pháp**:
  1. Tạo `platform-loader` skill trong Hub — manifest chứa catalog tất cả services
  2. `catalog.yaml` liệt kê skills/workflows/rules kèm **trigger keywords**
  3. Agent đọc SKILL.md → match trigger keywords → route đến đúng skill
  4. Cross-workspace: dùng absolute Hub path để `view_file()` skill từ xa
  5. `GEMINI.md` (user_global) Section 4 bootstrap Agent biết Hub location
  6. `workspace_context.yaml` trong Spoke chứa `discovery.bootstrap_skill`
- **Điểm**: Importance 5, Reusability 5, Reliability 4 = **14/15**
- **Files**:
  - `.agent/skills/platform-loader/SKILL.md`
  - `.agent/skills/platform-loader/catalog.yaml`
  - `C:\Users\chuvu\.gemini\GEMINI.md` (Section 4)
- **Nguồn**: Session 227a7981, 2026-03-28

#### Spoke Workspace Cleanup Pattern
- **Ngữ cảnh**: Khi Spoke workspace chứa legacy code/dev artifacts sau khi migrate sang Hub
- **Vấn đề giải quyết**: Cluttered workspace với 168 files hỗn loạn, .venv sync qua OneDrive
- **Giải pháp**:
  1. Xóa dev artifacts: `.venv/`, `.env`, `.github/`, `.pre-commit-config.yaml`, linter configs
  2. Xóa migrated code: `scripts/`, `.agent/workflows/` (đã ở Hub)
  3. Tổ chức lại: `source-docs/` (PDF gốc) + `converted/` (markdown) + subfolders theo nhóm
  4. Giữ lại: `.md/workspace_context.yaml`, `.vscode/`, `README.md`
- **Kết quả**: 168 → 100 files, root items 40 → 8
- **Điểm**: Importance 4, Reusability 5, Reliability 4 = **13/15**
- **Nguồn**: Session 227a7981, 2026-03-28

#### GitHub Ruleset Toggle for Batch Operations
- **Ngữ cảnh**: Khi cần batch delete branches nhưng bị block bởi GitHub Rulesets
- **Vấn đề giải quyết**: `git push --delete` thất bại do "Automatic Review with Copilot" ruleset
- **Giải pháp**:
  1. Vào Settings → Rules → Rulesets
  2. Tạm set enforcement "Disabled"
  3. Thực hiện batch operations (delete branches qua browser UI)
  4. **BẮT BUỘC re-enable** ruleset sau khi xong
- **Điểm**: Importance 3, Reusability 4, Reliability 5 = **12/15**
- **Nguồn**: Session 227a7981, 2026-03-28

### Anti-patterns Identified

#### Avoid .venv in OneDrive-Synced Folders
- **Vấn đề**: `.venv/` chứa hàng nghìn files nhỏ (50-200 MB), OneDrive sync cực chậm và tốn bandwidth
- **Thay thế**:
  - Đặt `.venv` ngoài OneDrive folder
  - Hoặc thêm `.venv` vào OneDrive exclusion list
  - Hoặc dùng global `.gitignore`-style exclusion
- **Nguồn**: Session 227a7981, 2026-03-28

#### Avoid Keeping Dev Artifacts in Document Workspaces
- **Vấn đề**: Sau khi migrate code sang Hub, Spoke workspace vẫn giữ `.env`, `.github/`, `.pre-commit-config.yaml`, linter configs → clutter + security risk (API keys)
- **Thay thế**: Xóa toàn bộ dev artifacts khi workspace chuyển thành document-only Spoke
- **Nguồn**: Session 227a7981, 2026-03-28

### Solutions Added

#### Branch Deletion Blocked by GitHub Rulesets
- **Vấn đề**: `git push origin --delete <branch>` fail với `GH013: Repository rule violations`
- **Nguyên nhân**: GitHub Ruleset "Automatic Review with Copilot" áp dụng lên ALL branches, block cả delete operations
- **Giải pháp**:
  1. Dùng GitHub browser UI (Branches page) thay vì git CLI
  2. Nếu vẫn bị block → tạm disable ruleset → delete → re-enable
  3. `git remote prune origin` để cleanup local tracking refs
- **Nguồn**: Session 227a7981, 2026-03-28

---

## Session abaca450 — AI Gateway Integration & Platform Refactor (2026-03-28)

### Patterns Added

#### Modular Services Architecture in Python Monorepo

- **Ngữ cảnh**: Khi cần tổ chức nhiều internal tools/libraries trong 1 repo
- **Vấn đề giải quyết**: Code monolith với single pyproject.toml, khó maintain
- **Giải pháp**:
  1. Tạo `packages/` directory, mỗi service = 1 sub-package
  2. Mỗi package có riêng `pyproject.toml`, `src/`, `tests/`
  3. Root `pyproject.toml` chứa `[tool.uv.workspace]` config
  4. Shared tooling (ruff, mypy) vẫn ở root
  5. Install editable: `pip install -e packages/[name]`
- **Files**: `packages/ccba-ai/`, `packages/mdconverter/`
- **Nguồn**: Session abaca450, 2026-03-28

#### Unified AI Gateway via pip Package

- **Ngữ cảnh**: Khi có self-hosted LLM gateway và cần standardize access
- **Vấn đề giải quyết**: Mỗi project tự viết client code, hardcode URLs/keys
- **Giải pháp**:
  1. Tạo lightweight pip package (`ccba-ai`): `from ccba_ai import ai`
  2. Package dùng OpenAI SDK underneath, pointing to gateway
  3. Config via env vars (`AI_GATEWAY_URL`, `AI_GATEWAY_KEY`)
  4. Set env vars ở User level → mọi project tự nhận
  5. SKILL.md document cho AI Agent biết cách dùng
- **Nguồn**: Session abaca450, 2026-03-28

#### Identity-First Repo Management

- **Ngữ cảnh**: Khi repo evolve qua nhiều phase, identity bị lẫn lộn
- **Vấn đề giải quyết**: README nói "tool A", PLATFORM.md nói "platform B"
- **Giải pháp**:
  1. Periodic "identity audit": README, pyproject name, URLs phải nhất quán
  2. Khi chuyển đổi, update TOÀN BỘ identity cùng lúc (1 commit)
  3. Checklist: README, pyproject.toml, CI, .pre-commit, docs/
- **Nguồn**: Session abaca450, 2026-03-28

#### Lazy dotenv Loading Pattern

- **Ngữ cảnh**: Khi dùng `python-dotenv` trong packages
- **Vấn đề giải quyết**: `load_dotenv()` không tham số → search recursive → hang 30s+
- **Giải pháp**: Chỉ load khi `.env` exists tại CWD, truyền explicit path
- **Nguồn**: Session abaca450, 2026-03-28

### Anti-patterns Added

#### Hardcoded API Keys in Scripts

- **Vấn đề**: Scripts chứa keys dưới dạng fallback: `os.getenv("KEY", "AIzaSy...")` → keys vào Git history VĨNH VIỄN
- **Thay thế bằng**: Luôn dùng env vars hoặc pip package. KHÔNG BAO GIỜ có fallback value là real key
- **Nguồn**: Session abaca450, 2026-03-28

#### Multi-Provider Direct API Calls

- **Vấn đề**: Mỗi LLM provider có riêng provider class + API key → quản lý 5+ keys, 3+ URLs
- **Thay thế bằng**: Single AI Gateway (LiteLLM) → 1 URL, 1 key, gateway handles routing
- **Nguồn**: Session abaca450, 2026-03-28

### Solutions Added

#### Pydantic Settings extra="ignore" for Legacy Env Vars

- **Vấn đề**: Sau khi remove fields từ Settings class, old env vars gây `extra_forbidden` error
- **Giải pháp**: Thêm `extra="ignore"` vào `SettingsConfigDict`
- **Nguồn**: Session abaca450, 2026-03-28

#### System Environment Variables for Cross-Project Config

- **Vấn đề**: Mỗi project cần `.env` file riêng cho cùng 1 config (AI Gateway)
- **Giải pháp**: `[System.Environment]::SetEnvironmentVariable("KEY", "value", "User")` — set 1 lần, mọi process mới đều nhận
- **Nguồn**: Session abaca450, 2026-03-28


