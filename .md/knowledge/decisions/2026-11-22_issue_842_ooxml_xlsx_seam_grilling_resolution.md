# Biên Bản Phỏng Vấn Grilling & Kế Hoạch Triển Khai Issue `#842`: Mở Rộng Seam `ooxml_processor.v1` Hỗ Trợ `.xlsx`

> **Ngày chốt Grilling:** `2026-11-22` | **Baseline Hub:** `main` @ `52b1a65b` (`Python 3.12.3`) | **Issue:** `#842` (`needs-info` $\to$ sẵn sàng triển khai khi có lệnh `proceed`)  
> **Biên lai Đối soát Seam ([ADR-0061](../../../docs/adr/0061-platform-aware-kiss-v2-and-quarantine-governance.md)):**
> - `python scripts/governance/compile_catalog.py --in xlsx --out xlsx --json` $\rightarrow$ `status: "NO_MATCH"` (`count: 0`, `index_sha256: 84408980fb63f7f7f2d4a5f493411abf42c8e35217a36c491de454ee4ea4bc9b`)
> - Seam hiện hữu mở rộng trực tiếp: `ooxml_processor.v1` ([seam-contracts.yaml](../../../seam-contracts.yaml#L19-L31), [packages/ccba-ooxml/src/ccba_ooxml/\_\_init\_\_.py](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), [exceptions.py](../../../packages/ccba-ooxml/src/ccba_ooxml/form_filler/exceptions.py), [calc.py](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py)).  
> **Impact-Based Handoff Gate ([ADR-0067](../../../docs/adr/0067-one-way-door-manifest-and-backpressure-circuit-breaker.md)):** `ONE_WAY_DOOR` (mở rộng Public Deep Seam của `ccba_ooxml`, cập nhật `seam-contracts.yaml`, `pyproject.toml`, và re-anchor `verify-ccba-ooxml`) $\rightarrow$ đã qua **Grok Peer Plan Audit (`2` vòng, `APPROVE_PLAN`, `blocking_conditions: 0`)**; dừng chờ lệnh `proceed` của người dùng trước khi sửa mã sản xuất.

---

## 1. Bước 0 — Mài Sắc Bài Toán & Dữ Kiện Từ Codebase (`Facts`)

1. **Mục tiêu thực chất (`in-your-own-words`):** Khép kín khoảng trống năng lực `.xlsx` trong Seam `ooxml_processor.v1` (`ccba_ooxml`), cho phép đọc/điền template/tạo mới bảng tính `.xlsx` an toàn mà không cần import trực tiếp `openpyxl` bên ngoài package ranh giới `ccba_ooxml` (đang bị khóa bởi [check_dependency_contracts.py](../../../scripts/governance/check_dependency_contracts.py#L57) và Ruff `TID251` tại [pyproject.toml](../../../pyproject.toml#L90)). Nhờ đó, `IBST_UNIFIED_ERP` gỡ được toàn bộ `4/4` tệp quarantine trước hạn `2027-02-19`, đồng thời phục vụ các Spoke đọc/xuất Excel khác (như `IDOP-CCBA-WAY`).
2. **Dữ kiện gốc kiểm chứng trực tiếp trên codebase (`[đo thực tế]`):**
   - **Mẫu hình sử dụng thật ở Spoke (`IBST_UNIFIED_ERP` & `IDOP-CCBA-WAY`):**
     - Fill template `.xlsx` theo tọa độ dòng/cột, sao chép style hàng mẫu (`font`, `border`, `fill`, `alignment`, `number_format`), chuẩn hóa `Decimal` / `date` / `ILLEGAL_CHARACTERS_RE`, xuất in-memory `io.BytesIO` cho FastAPI (`template_export_service.py`).
     - Tạo mới Workbook nhiều sheet (`title[:31]`), tô header `#1F4E78` / chữ trắng đậm / căn giữa, `freeze_panes = "A2"`, xuất `Path` (`excel_report_exporter.py`, `reconcile_export.py`).
     - Đọc dữ liệu `data_only=True`, `iter_rows(min_row=..., values_only=True)` (`sync_ibim_bim31v.py`, trùng mẫu `48` điểm gọi trên `IDOP-CCBA-WAY`).
   - **Ràng buộc hợp đồng & chốt đếm hiện hữu trên Hub:**
     - `ccba_ooxml.__all__` và `_LAZY_EXPORTS` hiện khóa cứng **`64`** symbols tại [test_phase1_ooxml_seams.py](../../../packages/ccba-ooxml/tests/test_phase1_ooxml_seams.py#L276-L277), [test_ooxml_suite.py](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/harness/test_ooxml_suite.py#L74), [run_verify_ooxml.py](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/harness/run_verify_ooxml.py#L75), [verify-ccba-ooxml/SKILL.md](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md#L49), [features/INDEX.md](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/features/INDEX.md#L5), và bản rollup [packages/ccba-harness/features/INDEX.md](../../../packages/ccba-harness/features/INDEX.md#L107).
     - `test_ccba_ooxml_root_and_leaf_subprocess_isolation` ([test_phase1_ooxml_seams.py](../../../packages/ccba-ooxml/tests/test_phase1_ooxml_seams.py#L287-L293)) xác nhận `import ccba_ooxml`, `ccba_ooxml.soffice`, `ccba_ooxml.calc` không kéo thư viện nặng vào `sys.modules`.
     - `validate_seam_exports` ([compile_catalog.py](../../../scripts/governance/compile_catalog.py#L333)) yêu cầu câu `from ccba_ooxml import ...` trong [packages/ccba-ooxml/AGENTS.md](../../../packages/ccba-ooxml/AGENTS.md#L5) là một dòng phẳng không ngoặc, không xuống dòng; `validate_seam_contracts` ([compile_catalog.py](../../../scripts/governance/compile_catalog.py#L515)) tách danh sách symbol trong `import_path` bằng dấu phẩy.
     - [packages/ccba-ooxml/pyproject.toml](../../../packages/ccba-ooxml/pyproject.toml#L12-L19) chưa khai báo `openpyxl` (hiện đang có `openpyxl 3.1.5` trên môi trường Hub).

---

## 2. Bảng Chốt `4/4` Quyết Định Thiết Kế (`Q1`–`Q4`)

| Mã | Chủ đề Frontier | Quyết định đã khóa & Ràng buộc thực thi | Căn cứ |
| :---: | :--- | :--- | :--- |
| **`Q1`** | **Phạm vi Seam `.xlsx`** | Xây dựng deep subpackage `packages/ccba-ooxml/src/ccba_ooxml/xlsx/` gồm **3 bề mặt tối giản**: `XlsxTemplateFiller` (`fill_cells`, `write_styled_row`, `write_styled_rows`, `export`, `export_bytes`), `XlsxWorkbookWriter` (`add_sheet`, `export`, `export_bytes`), và `XlsxReader` (`sheet_names`, `iter_rows`). | Phủ trọn 4/4 tệp quarantine ở `IBST_UNIFIED_ERP` và mẫu đọc ở `IDOP-CCBA-WAY`. |
| **`Q2`** | **Dependency & Lazy Import** | Thêm `"openpyxl>=3.1.0"` vào `dependencies` mặc định của [packages/ccba-ooxml/pyproject.toml](../../../packages/ccba-ooxml/pyproject.toml). Export 8 symbol mới qua `_LAZY_EXPORTS`, `__all__`, và `TYPE_CHECKING` tại [\_\_init\_\_.py](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py) để giữ `import ccba_ooxml` `< 25 ms` (lấy `min` của `3` subprocess) và không nạp `openpyxl` khi import gốc. | Đồng nhất với `python-docx`, `python-pptx`; giữ SLA `< 25 ms` (`RULE-2.20`). |
| **`Q3`** | **Bảo mật & An toàn Dữ liệu Mặc định** | 1. **Preflight `RULE-5.13` dùng chung:** Quét ZIP (`ZipInfo.file_size` — kích thước giải nén) trước mọi `load_workbook()`, chặn `xl/media/* > 2 MiB`, entry đơn `> 50 MiB`, tổng `> 150 MiB`, số entry `> 400`, path traversal (`/`, `\`, `..`), file rỗng / thiếu magic `PK` / `EncryptionInfo`.<br>2. **Sanitize & Chống Formula Injection:** `sanitize_xlsx_value(val, *, allow_formulas=False, date_as_iso=True)` giữ `bool` trước `int`, `Decimal -> float`, `date/datetime -> isoformat()` (khi `date_as_iso=True`), `None -> ""`, xóa control char, `lstrip` rồi gắn tiền tố `'` với đầu `= + - @` hoặc tiền tố `\t`/`\r` khi `allow_formulas=False`.<br>3. **Bảo vệ Template & `MergedCell`:** `TemplateProtectionError` chống ghi đè file template gốc; `on_merged: Literal["error", "skip", "top_left"] = "error"` (`MergedCellWriteError`); `recalc=False` opt-in trên `export()`. | Fail-closed mặc định cho web API xuất Excel từ DB; tương thích `RULE-5.13`. |
| **`Q4`** | **Hợp đồng Công khai & Ranh giới PR** | Xuất đúng **8 symbol công khai mới** (`64 -> 72`): `XlsxTemplateFiller`, `XlsxWorkbookWriter`, `XlsxReader`, `XlsxFillConfig`, `XlsxHeaderStyle`, `sanitize_xlsx_value`, `XlsxMediaLimitError`, `MergedCellWriteError`. Mở rộng `seam-contracts.yaml` (`out` thêm `xlsx`, `import_path` thêm 3 class), cập nhật `pyproject.toml`, `AGENTS.md`, và `verify-ccba-ooxml` (`--merge` theo `RULE-2.21`). Đóng gói PR Hub trước; Spoke migrate sau khi Hub merge. | Giữ PR nguyên tử, dễ kiểm định và không phá parity `compile_catalog.py`. |

---

## 3. Thẩm Định Độc Lập Ngang Hàng (`Grok Peer Plan Audit — ADR-0067`)

| Vòng | Profile | Session ID | Phán quyết | Risk | Blocking | Tóm tắt Kết quả |
| :---: | :--- | :--- | :---: | :-: | :-: | :--- |
| **Pass 1** | `audit_plan` | `057a8692-01cb-4ddc-91dd-6a2e99d0c26d` | `REVISE_PLAN` | `3` | `6` | Chỉ ra 6 điều kiện kỹ thuật cụ thể về chốt đếm `64 -> 72`, `import_path`, `mypy` + module `_`, preflight `RULE-5.13`, `sanitize_xlsx_value` + `on_merged`, và chữ ký `XlsxHeaderStyle` / `XlsxFillConfig`. |
| **Pass 2** | `signoff_diff` | `f23eb1b1-cbc1-41a7-bb73-7342184a4ef4` | **`APPROVE_PLAN`** | `2` | **`0`** | Xác nhận 6/6 điều kiện blocking đã được tiếp thu đúng `file:line`; phát sinh 4 pin thi công không chặn (`blocking: false`). |

### Ma trận Phân loại Điều kiện (`3-Label Triage Matrix`)

| ID | Vòng | Phân loại | Quyết định & Vị trí Khóa Mã Nguồn |
| :--- | :---: | :--- | :--- |
| `COND-842-SYMBOL-PIN` | Pass 1 | `[ADOPT_AS_IS]` | Nâng đồng bộ `64 -> 72` trên `test_phase1_ooxml_seams.py`, `test_ooxml_suite.py`, `run_verify_ooxml.py`, `verify-ccba-ooxml/SKILL.md`, `verify-ccba-ooxml/features/INDEX.md`, giữ parity `TYPE_CHECKING == __all__ == _LAZY_EXPORTS`, tính lại `covered_sha256` LF của `__init__.py` và giữ `sync_commit: 7259350d8020834c52ab88e4c5681e165612cc8b`. |
| `COND-842-SEAM-SYMBOLS` | Pass 1 | `[ADOPT_AS_IS]` | Sửa `import_path` thành `ccba_ooxml:DocxDocument,XlsxTemplateFiller,XlsxWorkbookWriter,XlsxReader` trong `seam-contracts.yaml`; cập nhật `"openpyxl".msg` tại `pyproject.toml:90` nêu 3 class `.xlsx`; thêm 8 tên vào dòng `from ccba_ooxml import ...` phẳng ở `packages/ccba-ooxml/AGENTS.md:5`; giữ nguyên `compile_catalog.py`. |
| `COND-842-LAZY-MYPY` | Pass 1 | `[ADOPT_AS_IS]` | `_LAZY_EXPORTS` trỏ `"ccba_ooxml.xlsx"`; module thực thi dùng tiền tố `_` (`_models.py`, `_safety.py`, `_filler.py`, `_writer.py`, `_reader.py`), import nội bộ từ `ccba_ooxml.form_filler.exceptions`; `XlsxMediaLimitError` & `MergedCellWriteError` kế thừa `Exception`; thêm `openpyxl`, `openpyxl.*` vào `ignore_missing_imports` tại `pyproject.toml:154`, giữ `ccba_ooxml.xlsx.*` dưới `mypy --strict`; mở rộng `test_ccba_ooxml_root_and_leaf_subprocess_isolation` chặn `openpyxl` và benchmark `min` của 3 subprocess `< 25 ms`. |
| `COND-842-PREFLIGHT` | Pass 1 | `[ADOPT_AS_IS]` | Dùng chung `verify_xlsx_zip_safety` thuần stdlib trong `_safety.py` trước mọi `load_workbook()` (gồm `XlsxTemplateFiller`, `XlsxReader`, và nhánh fallback của `calc.recalc_xlsx`); áp đủ 4 trần (`xl/media/* <= 2 MiB` case-insensitive, entry `<= 50 MiB`, tổng `<= 150 MiB`, `<= 400` entries), `posixpath.normpath` chặn `/`, `\`, `..`, kiểm tra magic `PK` & `EncryptionInfo`, map lỗi hỏng/mã hóa sang `zipfile.BadZipFile` (`corrupted_zip`), lỗi vượt trần sang `XlsxMediaLimitError`; cấm `extractall()`; đóng workbook trong `__exit__` / `finally`. |
| `COND-842-SANITIZE-MERGE` | Pass 1 | `[ADOPT_AS_IS]` | `sanitize_xlsx_value` xử lý đúng thứ tự `None -> bool -> Decimal -> int/float -> date/datetime -> ILLEGAL_CHARACTERS_RE -> lstrip` và escape `= + - @` (cùng tiền tố `\t`/`\r`) khi `allow_formulas=False`; quét toàn bộ ô đích trước khi ghi theo `on_merged` (`error` / `skip` / `top_left`); `write_styled_rows` ghi đè tại chỗ không `insert_rows`; `export()` chặn ghi đè template; `__exit__` chỉ gọi `close()`. |
| `COND-842-WRITER-CONFIG` | Pass 1 | `[ADOPT_AS_IS]` | Gắn `XlsxHeaderStyle` & `XlsxFillConfig` vào chữ ký công khai (`add_sheet(name, headers, rows, *, header_style=None, freeze_panes="A2")`, `write_styled_row(row_idx, values, *, style_from_row=None, sheet_name=None)`); kiểm thử round-trip bằng `zipfile` + XML DOM trong `test_xlsx.py`. |
| `COND-842-TEMPLATE-RESOLVE` | Pass 2 | `[ADOPT_AS_IS]` | `XlsxTemplateFiller` gán `self.template_path = Path(template_path).resolve()` và `export()` so sánh `Path(xlsx_out).resolve()` (kèm test đường dẫn tương đối). |
| `COND-842-CALC-IMPORT-SITE` | Pass 2 | `[ADOPT_AS_IS]` | `calc.recalc_xlsx` import `verify_xlsx_zip_safety` bên trong nhánh fallback `openpyxl` (giữ sạch `test_ccba_ooxml_root_and_leaf_subprocess_isolation`), đặt `wb = None` trước `try:` và đóng trong `finally:`, lỗi preflight trả `{"error": ...}`. |
| `COND-842-DATE-PASSTHROUGH` | Pass 2 | `[ADOPT_AS_IS]` | Khi `date_as_iso=False`, `sanitize_xlsx_value` giữ nguyên đối tượng `date`/`datetime`; các kiểu lạ ngoài tập chuẩn chuyển qua `str()` rồi đi qua nhánh làm sạch chuỗi. |
| `COND-842-INDEX-MIRROR` | Pass 2 | `[ADOPT_AS_IS]` | Đồng bộ số đếm `64 -> 72` cả ở bản rollup [packages/ccba-harness/features/INDEX.md](../../../packages/ccba-harness/features/INDEX.md#L107) cùng [features/INDEX.md](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/features/INDEX.md#L5). |

---

## 4. Kế Hoạch Triển Khai Chi Tiết (`Implementation Plan` — Thực Thi Sau Lệnh `proceed`)

### 4.1. Danh sách Tệp Tạo Mới & Sửa Đổi
1. **Subpackage mới `packages/ccba-ooxml/src/ccba_ooxml/xlsx/`:**
   - `__init__.py`: Export đúng 8 public symbols (`__all__`).
   - `_models.py`: `XlsxFillConfig` (`max_media_bytes=2*1024*1024`, `max_entry_bytes=50*1024*1024`, `max_total_bytes=150*1024*1024`, `max_entries=400`, `allow_formulas=False`, `date_as_iso=True`, `on_merged="error"`), `XlsxHeaderStyle` (`fill_color="1F4E78"`, `font_color="FFFFFF"`, `bold=True`, `horizontal="center"`, `vertical="center"`, `wrap_text=True`), `XlsxMediaLimitError(Exception)`, `MergedCellWriteError(Exception)`.
   - `_safety.py`: Thuần stdlib (không import `openpyxl`), cung cấp `verify_xlsx_zip_safety(path, config)` và `sanitize_xlsx_value(val, *, allow_formulas=False, date_as_iso=True)`.
   - `_filler.py`: `XlsxTemplateFiller` (`fill_cells`, `write_styled_row`, `write_styled_rows`, `export`, `export_bytes`, context manager).
   - `_writer.py`: `XlsxWorkbookWriter` (`add_sheet`, `export`, `export_bytes`, context manager).
   - `_reader.py`: `XlsxReader` (`sheet_names`, `iter_rows`, `close`, context manager với `read_only=True`, `data_only=True`).
2. **Tệp sửa đổi trên `ccba-ooxml`:**
   - `packages/ccba-ooxml/pyproject.toml`: Thêm `"openpyxl>=3.1.0"` vào `dependencies`.
   - `packages/ccba-ooxml/src/ccba_ooxml/__init__.py`: Khai báo 8 symbol trong `TYPE_CHECKING`, `__all__`, `_LAZY_EXPORTS` (`72` symbols).
   - `packages/ccba-ooxml/src/ccba_ooxml/calc.py`: Gọi `verify_xlsx_zip_safety` trong nhánh fallback `openpyxl` và đóng `wb` trong `finally:`.
   - `packages/ccba-ooxml/AGENTS.md`: Bổ sung 8 symbol vào dòng `from ccba_ooxml import ...` phẳng.
3. **Hợp đồng Seam, Linter & Verification Harness:**
   - `seam-contracts.yaml`: Cập nhật `ooxml_processor.v1` (`capability.out` thêm `xlsx`, `import_path` thành `ccba_ooxml:DocxDocument,XlsxTemplateFiller,XlsxWorkbookWriter,XlsxReader`).
   - `pyproject.toml`: Cập nhật `"openpyxl".msg` (`L90`) và thêm `"openpyxl"`, `"openpyxl.*"` vào `ignore_missing_imports` (`L154`).
   - `packages/ccba-ooxml/tests/test_phase1_ooxml_seams.py`, `packages/ccba-ooxml/tests/test_xlsx.py`: Nâng `64 -> 72`, mở rộng isolation probe + latency `< 25 ms`, và bộ round-trip test `zipfile` + XML DOM toàn diện.
   - `packages/ccba-harness/.agents/skills/verify-ccba-ooxml/` (`SKILL.md`, `features/INDEX.md`, `harness/test_ooxml_suite.py`, `harness/run_verify_ooxml.py`) + `packages/ccba-harness/features/INDEX.md`: Cập nhật `64 -> 72` và re-anchor `covered_sha256` LF của `__init__.py` (giữ `sync_commit` `7259350d`).

### 4.2. Cơ Chế Kiểm Chứng Độc Lập (`Outside Checks` & `Verification Gates`)
1. **Round-trip `.xlsx` thật qua `zipfile` + XML DOM (`test_xlsx.py`):** Kiểm chứng style copy, 3 mode `on_merged` (`error` / `skip` / `top_left`), chặn `xl/media/* > 2 MiB` trước khi gọi `load_workbook`, chặn file rỗng/non-ZIP/`EncryptionInfo`/path traversal, xóa `\x0b`, escape `=CMD()` và ` =CMD()` khi `allow_formulas=False` vs giữ nguyên khi `allow_formulas=True`, `TemplateProtectionError` với cả đường dẫn tương đối, `XlsxReader` `with` lifecycle, và `calc.recalc_xlsx` fallback preflight.
2. **Import Isolation & Latency (`test_phase1_ooxml_seams.py`):** `openpyxl` không xuất hiện trong `sys.modules` khi import `ccba_ooxml`, `ccba_ooxml.soffice`, `ccba_ooxml.calc`; `min` của `3` subprocess `import ccba_ooxml` `< 25 ms`.
3. **Platform CI Gates:** `compile_catalog.py --check`, `test_dependency_contracts.py`, `test_module_budget_ratchet.py`, `test_ooxml_suite.py`, `pytest packages/ccba-ooxml/tests`, `verify-patch --preset ci`, và hợp nhất PR bằng `--merge` theo `RULE-2.21`.
