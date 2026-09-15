# Walkthrough: Nghiệm Thu Thẩm Định & Hợp Nhất PR #278 (Issue #277)

**Mã Đề Xuất:** PR [#278](https://github.com/vvChu/ccba-agent-platform/pull/278)  
**Tiêu đề:** `feat(legal-intel): Multi-Factor Layout Table Scoring Engine & OKF v2.4 Universal Converters (#277)`  
**Nhánh nguồn:** `proposal/issue-277-multi-factor-layout-scoring`  
**Nhánh đích:** `main` (Squash Merge Commit: `62bbbbbc`)  
**Tệp RFC Proposal:** `.agents/proposals/2026-09-15_multi-factor-layout-scoring-and-okf-v24-converters.md` (Merged Status Commit: `ee80d976`)  
**Quy chuẩn áp dụng:** ADR 0038, ADR 0042, ADR 0043, ADR 0044, ADR 0045, ADR 0047, ADR 0049, ADR 0058  
**Copilot Review Audit:** Review ID `5203253042` (`COMMENTED`, 0 inline comments)

---

## 1. Tóm Tắt Nghiệp Vụ & Thành Tựu Cốt Lõi

PR #278 giải quyết triệt để 4 điểm nghẽn kỹ thuật trong quy trình nạp tài liệu quy chuẩn/tiêu chuẩn xây dựng (OKF v2.4) tại Spoke `ccba-legal-knowledge`:
1. **Động cơ Đa Nhân tố (Multi-Factor Scoring Engine) & Zero-Loss Guard (ADR 0042):**
   - Thay thế heuristic cứng nhắc `rows <= 3` bằng ma trận 4 nhân tố: Mật độ số liệu / công thức (`NUMERIC_CELL_PATTERN`), Phân vùng biên tài liệu (Topology $P \le 0.12$ hoặc $P \ge 0.88$), Viền bảng (Borderless & style `TableNormal`), và Khung công thức (Formula Frames).
   - Khắc phục lỗi rò rỉ khối chữ ký / nơi nhận trong văn bản hành chính Việt Nam (giải quyết xung đột từ khóa `"đơn vị"` trong nơi nhận).
   - Bảo toàn $100\%$ các bảng số liệu kỹ thuật ngắn nhờ Zero-Loss Guard ($\ge 30\%$ mật độ số liệu).
2. **Khung Công Thức Toán & Chuẩn Hóa Cú Pháp KaTeX Đa Dòng (ADR 0038, ADR 0044):**
   - Phân biệt bảng khung công thức 1-2 hàng x 2 cột chứa nhãn `(1)`, `(B.1)` và unwrap thành các đoạn văn phục vụ bóc tách công thức.
   - Chuẩn hóa môi trường KaTeX đa dòng (`aligned`, `cases`, `gather`, `split`) sang dùng `\qquad (X)` ở cuối dòng, giữ `\tag{X}` cho khối đơn dòng, triệt tiêu $100\%$ lỗi bôi đỏ KaTeX.
   - Tích hợp bộ lọc từ chối $100\%$ chuỗi suy luận rác từ Vision OCR (`let's`, `the prompt`, `delimiters`...).
3. **Bảo Tồn Nguồn Gốc Kép (Dual-PDF Archive Protocol - ADR 0043, ADR 0049):**
   - Lưu trữ song song bản scan gốc `sources/<doc_slug>_raw_scan.pdf` và Vector PDF độ nét tuyệt đối `sources/<doc_slug>.pdf`.
4. **Làm Sạch Bảng Biểu & Khử Trùng Lặp Đoạn Văn:**
   - Tự động chuyển đổi các chú dẫn chân bảng `1)` thành `<sup>1)</sup>`.
   - Khử trùng lặp đoạn văn khi unwrap bảng 1 cột có `<w:vMerge>` qua `seen_cell_ids`.

---

## 2. Kết Quả Kiểm Chứng Thực Nghiệm Trên Cơ Sở Tri Thức (`[đo thực tế]`)

| Hạng mục đối soát | Dữ liệu kiểm tra thực tế | Kết quả đo lường (`[đo thực tế]`) | Đánh giá |
| :--- | :--- | :--- | :--- |
| **Bảng chữ ký hành chính** | 71 tệp DOCX toàn kho tri thức | 100% khối chữ ký có 1-2 hàng x 2 cột. Sau khi xử lý ngoại lệ `"đơn vị"`, 100% bảng nơi nhận được unwrap sạch. | ✅ ĐẠT |
| **Bảo vệ bảng kỹ thuật ngắn** | 125 bảng ngắn $\ge 30\%$ số liệu | 16/16 bảng số liệu kỹ thuật thực sự được bảo vệ tuyệt đối (mật độ $41.7\% \div 83.3\%$). 109 khung công thức được nhận diện qua style `TableNormal`. | ✅ ĐẠT |
| **Cú pháp KaTeX** | 1.256 khối công thức / 684 tệp MD | **1.251 / 1.256 công thức hợp lệ (99.60%)**. 0 công thức dùng `\tag` trong đa dòng. | ✅ ĐẠT |
| **Bộ lọc suy luận Vision** | 5 mẫu chuỗi suy luận rác OCR | 100% chuỗi rò rỉ bị phát hiện và từ chối nạp cache. | ✅ ĐẠT |
| **Định dạng `<sup>X)</sup>`** | 267 hàng bảng Markdown | Format chuẩn `<sup>X)</sup>`, không lệch cột bảng Markdown. | ✅ ĐẠT |

---

## 3. Bản Vá Tự Sửa Lỗi Tối Ưu (Supervised Self-Healing)

Đã áp dụng commit `b4b849c0` trước khi squash merge:
- **`pyproject.toml`:** Bổ sung `"lxml.*"` vào `[[tool.mypy.overrides]]`, bổ sung `"packages/ccba-legal-intel/src"` vào `mypy_path`.
- **`provenance.py:279`:** Ép kiểu `doc = Document(str(docx_files[0]))`.
- **`formula_harvester.py`:** Type hint `re.Match[str]`, type-guard cho `_read_cache`, sửa gán kiểu `Image.Image`, hoàn thiện `_postprocess_formula`.
- **`table_extractor.py`:** Đồng bộ regex nhãn phụ lục `|^\([A-Z]\.\d+\)$`, import chuẩn `Paragraph` và `Table`, tái sử dụng `NUMERIC_CELL_PATTERN`.
- **`docx_sanitizer.py`:** Nhận diện viền `TableNormal`, ngoại lệ từ khóa `"đơn vị"` cho nơi nhận vùng biên, fallback an toàn vị trí bảng lồng.
- **`table_handler.py`:** Khử trùng lặp đoạn văn khi unwrap bảng 1 cột có `<w:vMerge>` bằng `seen_cell_ids`.

---

## 4. Bằng Chứng Thẩm Định Tất Định (Deterministic Verification)

Chạy bộ điều phối tất định `python -m ccba_harness verify-patch` với **Exit Code = 0**:

```text
# 🛡️ Deterministic Patch Verification Report: ✅ ALL PASSED

- Overall Status: PASS
- Commands Executed: 5/5 passed
- Total Duration: 26290.9 ms

| Status | Exit Code | Duration | Command |
| :---: | :---: | :---: | :--- |
| PASS | 0 | 327.6ms | python -m ruff check packages/ccba-legal-intel |
| PASS | 0 | 4813.3ms | python -m mypy ... --config-file pyproject.toml |
| PASS | 0 | 17511.2ms | uv run pytest ... (40/40 tests) |
| PASS | 0 | 2078.8ms | python scripts/governance/check_spoke_leakage.py --strict |
| PASS | 0 | 1560.1ms | python scripts/governance/compile_catalog.py --check |
```

---

## 5. Quản Trị Hậu Merge & Hướng Dẫn Đồng Bộ Spoke

1. **Trạng thái Proposal:** `.agents/proposals/2026-09-15_multi-factor-layout-scoring-and-okf-v24-converters.md` đã chuyển sang `status: "merged"`, ghi nhận commit `62bbbbbc`.
2. **Catalog SSoT:** Đã tái biên dịch `catalog.yaml` thành công (72 skills, 0 workflows).
3. **Đóng vòng đóng góp thượng nguồn (Closed-Loop Sync):**
   - Đề nghị Spoke `ccba-legal-knowledge` kích hoạt workflow:
     ```bash
     python scripts/sync_spoke.py --spoke ../ccba-legal-knowledge --verify
     ```
     hoặc sử dụng lệnh `/ccba-update-spoke` tại Spoke để kéo toàn bộ các bộ chuyển đổi và động cơ tính điểm layout mới nhất về sử dụng.
