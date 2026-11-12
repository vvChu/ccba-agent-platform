---
name: ccba-book-compiler
description: "Tự động hóa chuyển hóa sách/ebook (EPUB/PDF) thành tri thức Zettelkasten Canonical v8.3 kèm nén WebP in-memory, đối soát BGE-M3 và Excalidraw 16:9."
role: kernel_skill
bundle: _core
tier: kernel
disable-model-invocation: true
user-invocable: true
command: /ccba-book-compiler
gpi:
  s: 4.0
  k: 4.5
  a: 1.0
  p: 1.0
triggers:
  - ccba-book-compiler
  - ccba-book-compile
  - book-compile
  - ebook-compile
  - nap-sach
  - chuyen-hoa-sach
  - zettelkasten-compiler
  - book-ingest
metadata:
  version: "1.5.0"
  author: "CCBA & VvC Second Brain"
---

# Master Skill: Deep Ebook Compilation Engine (/ccba-book-compiler)

Kỹ năng này chuẩn hóa và tự động hóa 100% quy trình chuyển hóa một cuốn sách/ebook thô (`.epub` hoặc `.pdf`) thành mạng lưới tri thức sống động, kiểm chứng được bằng Ground Truth và áp dụng thực chiến ngay trong doanh nghiệp theo triết lý **LLM Compiler Pattern** và **Hiến pháp VvC Second Brain (v8.16.0)**.

---

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `package-bound` kết hợp Orchestrator hạt nhân cấp cao. Kỹ năng liên kết trực tiếp với Public Deep Seam **`diagram_layout.v1`** (`ccba_diagram:apply_smart_layout`, `generate_markdown_spec_table`, CLI `ccba-diagram`) cho bố cục sơ đồ 16:9, đồng thời điều phối các seams nền tảng xác định của Spoke (`scripts/pipeline/book_staging.py`, `scripts/epub_convert.py`, `scripts/pdf_convert.py`, `scripts/pipeline/ground_truth.py`, `scripts/pipeline/book_assets.py`, `scripts/pipeline/self_correct.py`, `scripts/pipeline/post_process.py`, `scripts/pipeline/semantic_merger.py`, `scripts/core/vector_store.py`, `scripts/services/excalidraw_worker.py`, `scripts/wiki_maintain.py`).
  - Tra cứu hợp đồng năng lực trước khi sinh sơ đồ (dùng biến môi trường `CCBA_HUB_PATH`):
    ```bash
    python "${CCBA_HUB_PATH}/scripts/ccba_platform_cli.py" find-seam --in diagram --out layout --json
    ```
- **Governance Compliance**: Đạt chuẩn Governance ADR-0057 Tier 2B Standalone Kernel Skill (`disable-model-invocation: true` theo ADR-0040) với điểm $\mathbf{GPI} = (4.0 \times 2.5) + (4.5 \times 2.0) + (1.0 \times 2.0) - (1.0 \times 1.5) = \mathbf{19.5} \ge 12.0$.
- **Bất biến Bắt buộc (Mandatory Invariants)**:
  1. *Race-Free Staging & Dual-Path Contract*: Mọi sách mới hoặc sách ngoại lai BẮT BUỘC đi qua `pipeline.book_staging.stage_book_for_compilation()` theo đúng thứ tự: kiểm tra `check_cross_machine_lease()` $\rightarrow$ tạo workspace `05 - Fleeting/<Book_Stem>/` $\rightarrow$ đồng bộ khóa mức cuốn sách `.book_stage_<Book_Stem>.lock` (tách rời khóa sống còn `.book_ingest.lock` của daemon 24/7) để trích xuất hoặc phục hồi corpus Markdown & ảnh `.webp` (`quality=80, max_dim=1200`, nén trong RAM, scratch trên `state_dir` cục bộ) tại `03 - Resources/books/<Book_Stem>_MD/` với chốt lũy đẳng `_toc_original.json` + đủ chương $\rightarrow$ khởi tạo `Source Note` qua `safe_write_text()` + `update_source_cache()` $\rightarrow$ sinh `_toc.json` & `<BOOK_CONTEXT>` $\rightarrow$ chép sách ngoại lai vào `03 - Resources/books/` cuối cùng.
  2. *Metadata SSoT Gate*: Quét 5 tệp `.md` mở đầu trong `03 - Resources/books/<Book_Stem>_MD/` (`Title`, `Copyright`, `ISBN`, `Edition`, `Author`) để khóa chuẩn Full Title, Subtitle, Edition và Full Authors trước khi biên soạn.
  3. *Write-Through Concept Pipeline & Batched Vector Flush*: Mọi Concept Note BẮT BUỘC chạy qua Stage 4 `verify_and_correct()` (`scripts/pipeline/self_correct.py`) và lưu qua `save_concept(..., book_name=book_name)` (`scripts/pipeline/post_process.py`) bên trong ngữ cảnh `with VectorStore.get_instance().batch():` (`scripts/core/vector_store.py`) để kích hoạt 5 cổng chất lượng, `arbitrate_and_merge()`, gắn sơ đồ NXB (`align_book_diagrams()`), cập nhật `_vault_concepts_cache.json` v4 và chỉ ghi đĩa `.npz` đúng 1 lần.
  4. *MOC Lifecycle Discipline*: CẤM tạo tay `MOC_*.md` hoặc sửa tay `00 - Maps of Content/index.md` ở Pha 2 (vì `_cleanup_stale_mocs` sẽ xóa MOC khi `0` concepts). Chỉ chạy `scripts/wiki_maintain.py` ở cuối Pha 5 sau khi toàn bộ concepts đã lưu; tên MOC chuẩn do hệ thống sinh là `MOC_<normalize_moc_name(aliases[0])>.md` (`--check-only` dùng để kiểm tra không ghi đĩa).
  5. *Zero-ASCII Art & Clean Wikilinks (v8.15.11)*: Cấm tuyệt đối vẽ sơ đồ ASCII/Unicode box art và cấm bọc backticks quanh wikilinks/embeds trên mọi bề mặt Markdown. Mọi tệp Topic/Source viết ra đĩa phải đi qua `clean_wikilink_quotes()` + `safe_write_text()`.
  6. *Excalidraw 16:9 Seam Delegation*: Ủy quyền bố cục cho `ccba_diagram` + `clean_and_repair_excalidraw_json()`, khóa chặt hộp bao ngang `1.000px ≤ W ≤ 1.150px` (tính cả tọa độ điểm mũi tên 2D `el.x + pt[0]`) và cỡ chữ gốc `fontSize ≥ 13` (đảm bảo sàn hiển thị $\ge 8.5\text{px}$ sau scale), kèm Bảng Đặc Tả Ma Trận bên dưới.

---

## 💻 Cú Pháp Lệnh & Tham Số

```bash
/ccba-book-compiler <đường-dẫn-sách> [--canonical-name <Ten_Sach.epub>] [--domain <lĩnh-vực>] [--apply-to <quy-trình>] [--max-concepts <N>]
```

- `<đường-dẫn-sách>`: Đường dẫn tệp `.epub` hoặc `.pdf` (nội bộ `03 - Resources/books/` hoặc tệp tải lên từ bên ngoài).
- `--canonical-name <Ten_Sach.epub>`: Tên tệp chuẩn hóa khi nạp sách từ đường dẫn tạm bên ngoài (ví dụ `The_Skills_Powered_Organization.epub`).
- `--domain <lĩnh-vực>`: Nhãn domain MOC (`management`, `bim`, `law`, `lean`, `software`; mặc định: `management`).
- `--apply-to <quy-trình>`: Quy trình doanh nghiệp mục tiêu để đóng gói Bộ công cụ thực chiến Pha 5.
- `--max-concepts <N>`: Số lượng khái niệm nguyên tử 20/80 cần bóc tách (mặc định: `12` đến `16`).

---

## 🔄 Quy Trình Thực Thi 6 Pha Chuẩn Hóa (6-Phase SOP v1.5.0)

### Pha 1: Staging Chống Đua Daemon, Nén WebP & Metadata SSoT Gate
1. **Chạy trình điều phối Staging lũy đẳng (`pipeline.book_staging`)**:
   ```bash
   PYTHONPATH=scripts scripts/.venv/bin/python scripts/pipeline/book_staging.py "<file_path>" --canonical-name "<Ten_Sach_Chuan.epub_hoac_pdf>"
   ```
   - Nếu cần gọi lẻ bộ chuyển đổi PDF qua CLI (tự động từ chối PDF scan ảnh và dọn sạch thư mục dở dang):
     ```bash
     PYTHONPATH=scripts scripts/.venv/bin/python scripts/pdf_convert.py "<pdf_path>" "03 - Resources/books/<Book_Stem>_MD" --workspace "05 - Fleeting/<Book_Stem>"
     ```
2. **Hậu kiểm nén ảnh WebP cho corpus cũ (nếu có)**:
   ```bash
   scripts/.venv/bin/python .agents/skills/ccba-book-compiler/scripts/compress_images_to_webp.py --dir "03 - Resources/books/<Book_Stem>_MD"
   ```
3. **Metadata SSoT & Bilingual Glossary Gate**:
   - Đọc 5 tệp `.md` đầu tiên trong `03 - Resources/books/<Book_Stem>_MD/` và `05 - Fleeting/<Book_Stem>/_toc.json` để xác thực chính xác nhan đề đầy đủ, tác giả, nhà xuất bản, năm xuất bản và danh sách chương cốt lõi.
   - Quét `04 - Permanent/sources/` và `05 - Fleeting/*/_context.txt` theo tên tác giả / nhan đề gốc, đồng thời kích hoạt Hệ Từ Điển Liên Hợp 2 Tầng (`core.lexicon.sync_workspace_glossary(workspace_dir)` & `lookup_glossary_for_text()`, đối chiếu `00 - Maps of Content/Vault_Terminology_Glossary.md`): nếu Vault đã có ấn bản dịch tiếng Việt hoặc bản gốc đối ứng, **bắt buộc kế thừa khối `<GLOSSARY>` chuẩn hóa** sang `_context.txt` của sách mới, gắn thuật ngữ ấn bản đối ứng vào `aliases` của Concept Notes (`Alias-First Resolution` + Cầu Ngữ Nghĩa BGE-M3), và liên kết hai chiều giữa hai `Source Note`.
   - Với sách thuộc lĩnh vực pháp luật, xây dựng, đấu thầu, QCVN/TCVN hoặc BIM, ưu tiên đối chiếu thuật ngữ Tầng 1 bất biến từ SSoT `ccba_legal.lexicon` / `ccba-legal-knowledge` qua `core.lexicon` (ADR-0059 & ADR-0061), tuyệt đối không dùng các cụm trong `vi_forbidden` hoặc tự dịch lệch thuật ngữ luật định.
- **Tiêu chí hoàn thành:** `stage_book_for_compilation` trả JSON thành công; `_toc_original.json`, `_toc.json`, `_context.txt` và stub `Source Note` đã sẵn sàng; 0 ảnh PNG/JPG thô.

### Pha 2: Làm Giàu Source Note & Đồng Bộ `<BOOK_CONTEXT>` (Cấm Tạo MOC Sớm)
1. **Nâng cấp trực tiếp `Source Note` do Pha 1 khởi tạo** (`04 - Permanent/sources/YYYY-MM-DD_<book_name_lower>.md`) theo [`source_note_template.md`](resources/templates/source_note_template.md):
   - Khai báo đầy đủ `tags: [knowledge, source/book, domain/<domain>, type/source]`, `type: source`, `origin: book`, `source: "<book_filename>"`, `aliases: ["<Nhan Đề Ngắn>", "<Original Title>"]`.
   - Ghi đĩa qua `clean_wikilink_quotes()` + `safe_write_text()`, cập nhật SSD cache và làm tươi `<SUMMARY>` trong `_context.txt`:
     ```python
     from core.fuse_guard import safe_write_text
     from core.markdown_sanitizer import clean_wikilink_quotes
     from core.vault import update_source_cache
     from pipeline.map_reduce import refresh_book_context_summary

     clean_src = clean_wikilink_quotes(source_markdown)
     safe_write_text(source_note_path, clean_src)
     update_source_cache(source_note_path, text=clean_src)
     refresh_book_context_summary(workspace_dir, summary_str)
     ```
2. **Quy tắc cấm ở Pha 2**: Tuyệt đối **KHÔNG** tạo tay tệp `MOC_*.md`, **KHÔNG** sửa tay `00 - Maps of Content/index.md`, và **KHÔNG** chạy `wiki_maintain.py` khi chưa có Concept Notes.
- **Tiêu chí hoàn thành:** `Source Note` đạt chuẩn Schema `AGENTS.md §3.1`, cache `_vault_sources_cache.json` và `<BOOK_CONTEXT>` đã đồng bộ tóm tắt mới.

### Pha 3: Bóc Tách 12–16 Concept Notes Qua Seam Chính Thống & Batch `.npz`
1. Tuyển chọn 12–16 nguyên lý đòn bẩy 20/80 từ các chương cốt lõi theo [`concept_note_template.md`](resources/templates/concept_note_template.md) (`origin: book`, Evidence Hook tiếng Việt + Citation Line + `## Core Idea` + `## 📖 Bản gốc & Ngữ cảnh mở rộng (Ground Truth)` nguyên văn).
2. **Thực thi đối soát Ground Truth, Stage 4 & Lưu Batch**:
   ```python
   from core.vector_store import VectorStore
   from pipeline.ground_truth import find_ground_truth, find_images_around_ground_truth
   from pipeline.post_process import save_concept
   from pipeline.self_correct import verify_and_correct

   saved_concepts = []
   with VectorStore.get_instance().batch():
       for draft_md, gt_verbatim in compiled_drafts:
           verified_md = verify_and_correct(draft_md, gt_verbatim)
           out_path = save_concept(verified_md, book_name=book_name)
           if out_path is not None:
               saved_concepts.append(out_path)
   ```
   - `find_ground_truth()` và `find_images_around_ground_truth()` hỗ trợ truy hồi đoạn gốc và ảnh minh họa chương sách; `save_concept(..., book_name=book_name)` tự động gắn sơ đồ `.webp` qua `align_book_diagrams()`, kiểm định `_validate_quality()`, hợp nhất trùng lặp ngữ nghĩa và ghi nhận vector để flush `.npz` 1 lần khi thoát khối `with`.
- **Tiêu chí hoàn thành:** Toàn bộ Concept Notes vượt qua 5 cổng chất lượng, 0 tệp `_[2-9].md`, SSD cache & chỉ mục vector BGE-M3 được đồng bộ sạch sẽ.

### Pha 4: Luận Giải Kiến Trúc & Sinh Sơ Đồ Excalidraw 16:9 (`1.000px ≤ W ≤ 1.150px`)
1. **Sinh Sơ Đồ Hệ Thống 16:9** tại `03 - Resources/attachments/<so_do_slug>.excalidraw.md`:
   - Bố cục qua `ccba_diagram:apply_smart_layout` (hoặc container cụm phân tầng cho đồ thị chuỗi/đồng tâm để tránh sụp về cột dọc `W ≈ 260px`) kết hợp `services.excalidraw_worker.clean_and_repair_excalidraw_json()`.
   - Khóa hộp bao ngang `1.000px ≤ W ≤ 1.150px`, cỡ chữ `fontSize ≥ 13`, đầy đủ `## Text Elements` `^id` và `## Drawing`.
2. **Soạn Master Topic Note** (`> 2.500` từ) tại `04 - Permanent/topics/kien_truc_<chu_de>.md` (`type: topic`, `origin: book`, `source_type: compiled`), nhúng trần sơ đồ kèm Bảng Đặc Tả Ma Trận ngay bên dưới:
   ```markdown
   ![[so_do_slug.excalidraw.md|100%]]
   ```
   Ghi đĩa bắt buộc qua `clean_wikilink_quotes()` + `safe_write_text()`.
- **Tiêu chí hoàn thành:** Master Topic Note và sơ đồ `.excalidraw.md` đạt chuẩn bề ngang `[1000..1150px]` và `fontSize >= 13`.

### Pha 5: Đóng Gói Bộ Công Cụ Thực Chiến & Tự Động Hóa MOC / Master Index
1. **Bộ Công Cụ Thực Chiến** (với sách quản trị/quy trình/kỹ thuật ứng dụng): Soạn `04 - Permanent/topics/bo_cong_cu_thuc_chien_<quy_trinh>.md` theo [`fba_toolkit_template.md`](resources/templates/fba_toolkit_template.md) (`type: topic`, `origin: book`, `source_type: compiled`, 100% bảng Markdown bản địa, 0 ASCII box art), lọc qua `clean_wikilink_quotes()` + `safe_write_text()`.
2. **Liên kết ngược & Chạy `wiki_maintain.py`**:
   - Cập nhật danh sách wikilinks của toàn bộ Concept Notes, Topic Notes, Sơ đồ Excalidraw và MOC đích `[[MOC_<moc_slug>|MOC <Book Title>]]` (`moc_slug = normalize_moc_name(aliases[0])` từ `services.moc_builder`) vào `Source Note`, rồi gọi lại `update_source_cache()`.
   - Chạy trình bảo trì tự động để sinh `Source MOC`, `Domain MOC` và `00 - Maps of Content/index.md` (dùng `--check-only` nếu chỉ muốn chẩn đoán không ghi đĩa):
     ```bash
     scripts/.venv/bin/python scripts/wiki_maintain.py
     ```
- **Tiêu chí hoàn thành:** `MOC_<moc_slug>.md` và `index.md` được sinh tự động, khớp 100% liên kết hai chiều.

### Pha 6: Cổng Kiểm Định Tất Định C4 (`--verify-book`, `0 broken_body_links`) & Bàn Giao
1. **Chạy cổng kiểm định C4 toàn diện** (kiểm tra corpus WebP, TOC, hồ sơ `source`/`concept`/`topic`, `_validate_quality()`, hộp bao Excalidraw `[1000..1150px]`, `fontSize >= 13`, và đối soát `broken_body_links == 0` đồng bộ `VaultLinter` + media embeds):
   ```bash
   scripts/.venv/bin/python .agents/skills/ccba-book-compiler/scripts/compress_images_to_webp.py \
     --verify-book \
     --dir "03 - Resources/books/<Book_Stem>_MD" \
     --toc "05 - Fleeting/<Book_Stem>/_toc.json" \
     --source "04 - Permanent/sources/YYYY-MM-DD_<book_name_lower>.md" \
     --concepts <danh-sach-file-concepts> \
     --topics <danh-sach-file-topics> \
     --excalidraw "03 - Resources/attachments/<so_do_slug>.excalidraw.md"
   ```
2. **Chạy bộ kiểm thử kiến trúc & vệ sinh kho mã**:
   ```bash
   scripts/.venv/bin/pytest scripts/tests/test_book_compiler_contracts.py scripts/tests/test_codebase_cleanliness.py scripts/tests/test_architectural_budgets.py
   python "${CCBA_HUB_PATH}/scripts/validate_skills.py" --file "<spoke_root>/.agents/skills/ccba-book-compiler/SKILL.md" --enforce-gpi
   ```
3. Xuất Báo cáo Bàn giao (Walkthrough) tóm tắt thành phẩm cho người dùng.
- **Tiêu chí hoàn thành:** `--verify-book` in `[BOOK-VERIFY-OK]`, `pytest` và `validate_skills.py --enforce-gpi` đều đạt `exit code 0`.

---

## 📚 Progressive Disclosure & Reference Index (Level 3)

| Tệp Tham Chiếu / Script | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| [`scripts/compress_images_to_webp.py`](scripts/compress_images_to_webp.py) | CLI nén WebP hồi tố & điều phối cổng `--verify-book` |
| [`scripts/verify_book_artifacts.py`](scripts/verify_book_artifacts.py) | Động cơ kiểm định C4: TOC, hồ sơ `source`/`concept`/`topic`, `_validate_quality()` và `VaultLinter` link parity |
| [`scripts/verify_excalidraw_map.py`](scripts/verify_excalidraw_map.py) | Bộ giải mã `compressed-json` LZString & kiểm định hộp bao Excalidraw 16:9 (`[1000..1150px]`, `fontSize >= 13`) |
| [`references/canonical_v83_concept_note.md`](references/canonical_v83_concept_note.md) | Quy cách Frontmatter, Evidence Hook (VN) và Ground Truth (EN) |
| [`references/visual_and_diagramming_rules.md`](references/visual_and_diagramming_rules.md) | Quy chuẩn Excalidraw 16:9, Executive Typography và Bảng Markdown bản địa |
| [`resources/templates/toc_schema_v80.json`](resources/templates/toc_schema_v80.json) | Schema JSON mục lục sách song ngữ Canonical v8.0 |
| [`resources/templates/source_note_template.md`](resources/templates/source_note_template.md) | Bản mẫu Source Note chuẩn Schema `AGENTS.md §3.1` |
| [`resources/templates/concept_note_template.md`](resources/templates/concept_note_template.md) | Bản mẫu Concept Note nguyên tử Canonical v8.3 |
| [`resources/templates/fba_toolkit_template.md`](resources/templates/fba_toolkit_template.md) | Bản mẫu Bộ công cụ thực chiến 20/80 (`source_type: compiled`) |

---
*Tác tạo bởi CCBA & VvC Second Brain — Hệ Điều Hành Tri Thức Tự Trị*
