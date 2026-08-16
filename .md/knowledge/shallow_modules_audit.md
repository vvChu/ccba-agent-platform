# 🔍 Báo Cáo Khảo Sát Kiến Trúc Mã Nguồn: Shallow Modules Audit & Deletion Test (Ticket 1)

> **Mã công việc**: Wayfinder Ticket 1 (`T1: [Research] Khảo sát Module Nông`)  
> **Phương pháp luận**: Triết lý Deep Modules & Grey Box Seams (John Ousterhout, Matt Pocock - *AI Hero*)  
> **Nguyên tắc rà soát**: Code-First Research & Double-Pass Adversarial Review  
> **Mục tiêu**: Xác định các module nông (shallow modules), file phân mảnh, rò rỉ chi tiết nội bộ, duplicate logic và áp dụng Phép thử xóa bỏ (Deletion Test) trên toàn bộ 8 packages tại `packages/` và thư mục `src/`.

---

## 1. Tổng Quan Hiện Trạng Toàn Bộ Codebase

| Thư mục / Package | Số file `.py` | Trạng thái Seam (`__init__.py`) | Đánh giá Kiến trúc |
| :--- | :---: | :---: | :--- |
| `src/ccba_agent_platform` | 1 | Rỗng (Placeholder hatchling) | ✅ Tối giản (Chỉ để thỏa mãn workspace root) |
| `packages/ccba-legal-intel` (`ccba_legal`) | **21** | ⚠️ Bị phân mảnh, thiếu 11 file trong seam | 🔴 **Rất nông & hỗn loạn** (Nhiều module rác/lạc domain) |
| `packages/ccba-ai` (`ccba_ai`) | **14** | ⚠️ Seam quá rộng (41 symbols), ôm đồm services | 🟡 **Ôm đồm đa nhiệm** (Trộn lẫn client, CLI hooks, SEO, Task) |
| `packages/ccba-harness` (`ccba_harness`) | **9** | 🟢 Tốt (Private prefix `_`), thiếu 1 seam | 🟢 **Gần hoàn hảo** (Chỉ cần bổ sung `EvalOrchestrator` vào seam) |
| `packages/ccba-maskara` (`ccba_maskara`) | **6** | 🟢 Tốt (Private prefix `_`), seam hơi rộng | 🟢 **Đạt chuẩn Deep Module** (Chỉ cần thu gọn constant public) |
| `packages/ccba-notebooklm` (`ccba_notebooklm`) | **8** | 🟢 Chuẩn mực 2-Tier Seam (`_` prefix 100%) | 🌟 **Module mẫu mực nhất repo (Role Model)** |
| `packages/ccba-ooxml` (`ccba_ooxml`) | **15** | ⚠️ Phân mảnh script rời rạc (`pack`, `unpack`, `validate`) | 🟡 **Bị xé nhỏ file tiện ích** + Trùng tên `TableReconstructor` |
| `packages/ccba-pdf-prep` (`ccba_pdf_prep`) | **9** | 🟢 Đã có Deep Seam `PDFProcessingPipeline` | 🟢 **Tốt**, tồn tại 1 zombie forwarding shim (`xlsx_recalc`) |
| `packages/mdconverter` (`mdconverter`) | **30** | ⚠️ CLI xé lẻ 9 file, core 16 file phẳng | 🟡 **Phân mảnh CLI và Core** |

---

## 2. Chi Tiết Khảo Sát Từng Package & Phép Thử Xóa Bỏ (Deletion Test)

---

### 🏛️ Package 1: `ccba-legal-intel` (`ccba_legal`) — *Điểm nóng cần tái cấu trúc nhất*

Hiện tại thư mục `src/ccba_legal/` có tới **21 file Python nằm phẳng (flat)** ở tầng root. `__init__.py` chỉ export một phần, 11 file còn lại bị bỏ lửng hoặc gọi chéo lộn xộn.

#### Danh sách các module nông và kết quả Deletion Test:

1. **`ccba_legal.adr` (`adr.py` - 105 dòng)**:
   - *Bản chất*: Bộ quét git diff sinh tài liệu Architecture Decision Record (ADR).
   - *Vấn đề*: Hoàn toàn lạc domain! Không liên quan gì đến Văn bản Pháp luật Việt Nam hay TVPL.
   - *Phép thử xóa bỏ (Deletion Test)*:
     - Codebase usage: **0 active callers** (Chỉ có duy nhất test `test_adr.py` tự import nó).
     - *Kết luận*: **XÓA hoặc DI CHUYỂN** sang `scripts/governance/` hoặc tooling của repo. Loại bỏ hoàn toàn khỏi `ccba-legal-intel`.

2. **`ccba_legal.alert_handler` (`alert_handler.py` - 79 dòng)**:
   - *Bản chất*: Gửi Webhook Telegram khi gặp CAPTCHA/hết hạn VIP.
   - *Vấn đề*: File nông 79 dòng, không được export trong `__init__.py`, chưa từng được tích hợp vào `crawler.py` hay `LegalIntelPipeline`.
   - *Phép thử xóa bỏ (Deletion Test)*:
     - Codebase usage: Chỉ có `test_telegram_alert.py` import.
     - *Kết luận*: Đóng gói làm private submodule `_alert_handler.py` và tích hợp sâu vào bên trong `crawler.py` (Crawler tự kích hoạt khi phát hiện chặn), không để trôi nổi ở root.

3. **`ccba_legal.hybrid_rag` (`hybrid_rag.py` - 73 dòng)**:
   - *Bản chất*: Thuật toán BM25/TF-IDF đồ chơi viết bằng Python thuần trên memory (73 dòng).
   - *Vấn đề*: Không được export ở `__init__.py`, không liên kết với hệ thống vector/RAG chính.
   - *Phép thử xóa bỏ (Deletion Test)*:
     - Codebase usage: Chỉ có `test_hybrid_rag_integration.py` import.
     - *Kết luận*: Xóa hoặc hợp nhất vào bộ indexer/searcher nội bộ `_search.py`.

4. **`ccba_legal.intake` (`intake.py` - 107 dòng) & `ccba_legal.conflict` (`conflict.py` - 124 dòng)**:
   - *Bản chất*: Trích xuất 5 trục dữ kiện và tính điểm rủi ro Lex Superior / Lex Specialis.
   - *Vấn đề*: Bị bóc tách thành 2 file nhỏ riêng rẽ, trong khi chỉ được sử dụng duy nhất bởi `LegalProcessor` trong `coordinator.py`.
   - *Phép thử xóa bỏ (Deletion Test)*:
     - Codebase usage: Bên ngoài không ai import trực tiếp ngoài `coordinator.py` và file test riêng.
     - *Kết luận*: Chuyển thành private submodules (`_intake.py`, `_conflict.py`) hoặc gộp vào `_advisory.py` giấu sau seam `LegalProcessor`.

5. **Bộ ba VBHN Delta Patching: `ast_parser.py` (213 dòng) + `patch_generator.py` (98 dòng) + `vbhn_merger.py` (95 dòng)**:
   - *Bản chất*: Toàn bộ pipeline bóc tách cây AST luật (`#D12-K2-Pa`), sinh patch JSON từ LLM, và merge thành file Markdown `VBHN_{slug}.md`.
   - *Vấn đề*: Tổng cộng 406 dòng nhưng bị xé thành 3 file nhỏ trôi nổi ở root của package mà không có seam đại diện tại `__init__.py`.
   - *Phép thử xóa bỏ (Deletion Test)*:
     - Codebase usage: 3 file này chỉ import lẫn nhau và phục vụ bài toán hợp nhất văn bản VBHN.
     - *Kết luận*: Gom thành 1 deep sub-package hoặc 1 deep module duy nhất: `ccba_legal._patching` hoặc `ccba_legal._ast` với một Seam cấp cao: `VBHNMerger` / `LegalASTPatcher`.

6. **Trùng lặp 3 lần Logic Regex Heading (`formatter.py` vs `packager.py` vs `ast_parser.py` vs `appendices.py`)**:
   - `appendices.py` định nghĩa `AppendixSplitter` và `roman_to_decimal`.
   - `formatter.py` định nghĩa `OKFStructureProcessor.split_concept_appendices` và viết lại hàm `roman_to_decimal` cục bộ.
   - `packager.py` (`generate_clauses_json`) tự viết lại regex bắt `Chương / Mục / Điều / Khoản / Điểm`.
   - `ast_parser.py` lại viết một bộ regex thứ 3 cho `Chương / Mục / Điều / Khoản / Điểm`.
   - *Kết luận*: Cần thống nhất 1 bộ parser AST duy nhất làm Single Source of Truth (SSOT).

---

### 🤖 Package 2: `ccba-ai` (`ccba_ai`) — *Ôm đồm đa nhiệm & Trùng lặp tính năng*

1. **`write_file` & `hooks/privacy_guard.py` (76 dòng)**:
   - *Vấn đề*: `ccba_ai/__init__.py` export trực tiếp hàm `write_file` (ghi file và kiểm tra leak API key qua regex). Đây là logic trùng lặp 100% với package chuyên biệt `ccba-maskara`!
   - *Phép thử xóa bỏ (Deletion Test)*:
     - `write_file` chỉ được gọi trong đúng `test_privacy_guard.py`.
     - *Kết luận*: Xóa hàm `write_file` và module `hooks/privacy_guard.py` trong `ccba-ai`, chuyển giao trách nhiệm hoàn toàn cho `ccba-maskara`.

2. **`legal_knowledge.py` (80 dòng)**:
   - *Vấn đề*: File này chứa comment rõ ràng: `# NOTE: zero active callers — retained for API stability only`.
   - *Phép thử xóa bỏ (Deletion Test)*:
     - Không có script hoặc service nào trong toàn bộ repo gọi `legal_knowledge`.
     - *Kết luận*: Đánh dấu deprecated và xóa bỏ an toàn.

3. **`services/` (`plan.py`, `seo.py`, `team.py`)**:
   - *Vấn đề*: `ccba-ai` là thư viện kết nối AI Gateway (Gateway Client SDK). Việc nhồi nhét logic quản lý task nhóm (`team.py`), cập nhật phase kế hoạch (`plan.py`), và chấm điểm SEO web (`seo.py`) vào SDK AI làm loãng ranh giới domain.
   - *Kết luận*: Nên tách các business services này ra đúng tầng application hoặc tooling.

4. **`mcp_server.py`**:
   - Chứa mã dynamic load không an toàn từ `Path.cwd() / "scripts" / "idop_scaffolder.py"`.

---

### 🛡️ Package 3: `ccba-harness` (`ccba_harness`) — *Thiếu Seam cho `EvalOrchestrator`*

- **Ưu điểm**: Là một trong những package có kiến trúc đóng gói tốt nhất repo (toàn bộ file nội bộ đều mang prefix `_`: `_engine.py`, `_guard.py`, `_file_monitor.py`, `_mutex.py`, `_process_monitor.py`, `_sql_monitor.py`, `_state.py`).
- **Lỗ hổng Seam**: Module `orchestrator.py` (`EvalOrchestrator`) được thêm vào nhưng quên chưa export trong `__init__.py` và `__all__`. Test file `test_orchestrator.py` phải import sâu qua `from ccba_harness.orchestrator import EvalOrchestrator`.
- **Hành động khắc phục**: Re-export `EvalOrchestrator` tại `ccba_harness.__init__.__all__` và đổi tên file thành `_orchestrator.py`.

---

### 🎭 Package 4: `ccba-maskara` (`ccba_maskara`) — *Thu gọn Seam Surface*

- **Ưu điểm**: Đã dùng private prefix `_locator.py`, `_redactor.py`, `_rules.py`, `_scanner.py`. Có Deep Seam rõ ràng `MaskaraScanner`.
- **Điểm cần tinh gọn**: `__all__` đang re-export tới 14 items, bộc lộ cả các hằng số nội bộ (`AGENT_SPECS`, `AGENT_ALIASES`, `SAFE_STRINGS`, `REGEX_PATTERNS`, `BACKUP_DIR`) và các helper nhỏ (`normalize_agent_name`, `get_default_roots`).
- **Hành động**: Giữ `MaskaraScanner` và 2 hàm tiện ích cấp cao (`detect_secrets_in_text`, `redact_secrets_in_text`), ẩn các hằng số cấu hình vào trong lớp Scanner.

---

### 📄 Package 5: `ccba-ooxml` (`ccba_ooxml`) — *Phân mảnh File Thao tác & Xung đột Định danh*

1. **Phân mảnh `pack.py` (140 dòng), `unpack.py` (54 dòng), `validate.py` (61 dòng), `workspace.py` (170 dòng)**:
   - `unpack.py` chỉ có 1 hàm 30 dòng kèm khối `if __name__ == '__main__':` làm CLI.
   - `validate.py` chỉ có 1 hàm CLI `main()` gọi sang `validation/validator.py`.
   - `workspace.py` (`OOXMLWorkspace`) lại wrap lại cả `unpack_document` và `pack_document`.
   - *Kết luận*: Gom các file phân mảnh này về làm private backend đằng sau Deep Seam `OOXMLWorkspace` và `OOXMLValidator`.
2. **Xung đột tên class (Name Collision) nghiêm trọng**:
   - `packages/ccba-ooxml/src/ccba_ooxml/tables.py` có class `TableReconstructor` (dùng python-docx bóc tách bảng XML).
   - `packages/mdconverter/src/mdconverter/core/table_reconstructor.py` cũng có class `TableReconstructor` (dùng pandoc convert docx sang gfm để trích xuất phụ lục).
   - Hai class trùng tên 100% nhưng nằm ở 2 package khác nhau và làm 2 nhiệm vụ hoàn toàn khác nhau $\rightarrow$ Gây hiểu nhầm nghiêm trọng cho AI Agent.

---

### 👁️ Package 6: `ccba-pdf-prep` (`ccba_pdf_prep`) — *Loại bỏ Zombie Shim*

- **Ưu điểm**: Đã thiết lập Deep Seam chuẩn mực `PDFProcessingPipeline` tại `__init__.__all__`.
- **Zombie Module**: `document_skills/xlsx_recalc.py` (37 dòng): Là một forwarding shim cũ chuyển hướng sang `ccba_ooxml.calc`.
- **Phép thử xóa bỏ (Deletion Test)**:
  - Chỉ có duy nhất 1 test `test_domain_purity_no_xlsx_recalc_export` kiểm tra xem nó có bị export ra ngoài hay không.
  - Runtime code không có bất kỳ file nào sử dụng.
  - *Kết luận*: Xóa bỏ `xlsx_recalc.py` để giữ sạch domain PDF Vision thuần khiết.

---

### 🔄 Package 7: `mdconverter` (`mdconverter`) — *Sprawl Subcommands & Loose Core Files*

1. **Phân mảnh CLI (`mdconverter/cli/`)**:
   - CLI bị xé nhỏ thành 9 file micro-commands (`analyze_cmd.py`, `clean_form_cmd.py`, `config_cmd.py`, `convert_cmd.py`, `helpers.py`, `lint_cmd.py`, `patch_links_cmd.py`, `process_table_cmd.py`, `validate_cmd.py`) cùng 1 thư mục rỗng `commands/`.
   - *Kết luận*: Gom nhóm các lệnh CLI theo cụm nghiệp vụ hoặc gom vào router tập trung, xóa thư mục rỗng `commands/`.
2. **16 file phẳng trong `mdconverter/core/`**:
   - Các module như `link_patcher.py` (80 dòng), `form_cleaner.py` (170 dòng), `watcher.py` (115 dòng) nằm rời rạc mà không được bọc vào Seam `ConversionPipeline` / `PostProcessor` ở package root.

---

## 3. Ma Trận Đánh Giá và Đề Xuất Xử Lý (Deletion / Consolidation Matrix)

| STT | Target File / Module | Vấn đề Kiến trúc | Đề xuất Xử lý | Rủi ro Breakage | Độ ưu tiên |
| :---: | :--- | :--- | :--- | :---: | :---: |
| 1 | `ccba_legal/adr.py` | Lạc domain (Git tooling trong legal) | **XÓA / DI CHUYỂN** sang `scripts/` | Rất thấp (0 callers) | P1 (Cao) |
| 2 | `ccba_legal/alert_handler.py` | Nông (79 dòng), chưa tích hợp | Gom thành `_alert_handler.py` trong crawler | Thấp (Sửa 1 test) | P2 (Vừa) |
| 3 | `ccba_legal/hybrid_rag.py` | Toy implementation (73 dòng) | Gom vào `_search.py` hoặc xóa | Rất thấp | P3 (Thấp) |
| 4 | `ccba_legal/{ast_parser, patch_generator, vbhn_merger}.py` | 3 file xé lẻ (406 dòng) | Gom thành `ccba_legal._patching` + Seam `LegalASTPatcher` | Thấp (Gom test) | P1 (Cao) |
| 5 | `ccba_legal/{intake, conflict}.py` | Nông, chỉ `LegalProcessor` dùng | Đổi thành private `_intake.py`, `_conflict.py` | Rất thấp | P2 (Vừa) |
| 6 | `ccba_ai/legal_knowledge.py` | Dead code (0 active callers) | **XÓA** an toàn | Không có | P1 (Cao) |
| 7 | `ccba_ai/hooks/privacy_guard.py` & `write_file` | Trùng lặp với `ccba-maskara` | **XÓA**, dùng `ccba_maskara` | Thấp (Sửa 1 test) | P2 (Vừa) |
| 8 | `ccba_harness/orchestrator.py` | Thiếu trong `__all__` của package | Export `EvalOrchestrator` tại `__init__`, đổi thành `_orchestrator.py` | Không có | P1 (Cao) |
| 9 | `ccba_pdf_prep/document_skills/xlsx_recalc.py` | Zombie forwarding shim (37 dòng) | **XÓA** an toàn | Không có | P1 (Cao) |
| 10 | `ccba_ooxml/{unpack, validate}.py` | File script nông | Gom vào `_unpack.py`, `_validate.py` đằng sau `OOXMLWorkspace` | Thấp | P2 (Vừa) |
| 11 | Trùng tên `TableReconstructor` (`ccba_ooxml` vs `mdconverter`) | Xung đột định danh class | Đổi tên trong `mdconverter` thành `AppendixTableExtractor` | Thấp | P2 (Vừa) |

---

## 4. Đề Xuất Kế Hoạch Cho Ticket 2 & Ticket 4

Khảo sát đã hoàn thành đầy đủ mục tiêu của **Ticket 1**. Dữ liệu đã sẵn sàng để chuyển sang **Ticket 2** (*Chuẩn hóa Seam & Public Exports cho Monorepo Packages*):

1. **Hình mẫu chuẩn mực cần nhân rộng**: Áp dụng cấu trúc 2 tầng (Tier 1 Transport / Tier 2 Orchestration) của `ccba-notebooklm` cho toàn bộ các packages còn lại (`ccba_legal`, `ccba_ai`, `ccba_ooxml`, `mdconverter`).
2. **Quy tắc Private Prefix**: Mọi file nằm trong `src/<package>/` bắt buộc phải có tiền tố `_` nếu là chi tiết thực thi nội bộ (trừ file `__init__.py` và `cli.py`).
3. **Seam Tập trung**: Bên ngoài chỉ được phép import từ package root (ví dụ: `from ccba_legal import LegalIntelPipeline, LegalProcessor`), cấm tuyệt đối việc import sâu vào `from ccba_legal.some_internal_file import ...`.
