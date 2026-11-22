# Mẫu Biểu: Bảng Tính Toán Kỹ Thuật Song Ngữ Việt – Anh (A4 Portrait)

> **Mô tả**: Quy chuẩn thiết kế và quy trình chuẩn hóa bảng tính toán kỹ thuật song ngữ Việt – Anh dùng chung cho các bộ môn (PCCC, Thủy lực, MEP, Kết cấu, HVAC) của IBST - CCBA.  
> **Cấp độ kiến trúc**: Tier 2A Canonical Engineering Reference & Template (`GPI = 9.50 < 12.0` theo `ADR-0057`)  
> **Áp dụng**: Kỹ năng `/ccba-xu-ly-van-phong` kết hợp Deep Seam `ccba_ooxml:CalculationSheetBuilder` / `ccba-ooxml calc-sheet`.

---

## 1. Quy Chuẩn Thương Hiệu & Header (`RULE-6.1` + Brand Identity v3.4)

1. **Header 2 cấp chuẩn (dòng 1–4):**
   - Cấp trên: `VIỆN KHOA HỌC CÔNG NGHỆ XÂY DỰNG` / phụ đề tiếng Anh nghiêng `Institute for Building Science and Technology`.
   - Đơn vị trực thuộc: `TRUNG TÂM TƯ VẤN VÀ ỨNG DỤNG BIM TRONG XÂY DỰNG` / phụ đề `Center for Consulting Services and BIM Application in Construction (CCBA)`.
   - Logo chính thức (`logo_ccba_full.png`) căn phải bên trên đường viền phân cách đỏ IBST `#DA251C` ở hàng 4.
   - Không đưa "BỘ XÂY DỰNG" lên tiêu đề biểu mẫu kỹ thuật dự án; đơn vị gửi ghi thống nhất **`IBST - CCBA`** (cấm dùng dấu gạch chéo giữa hai đơn vị).
2. **Bảng phối màu chuẩn:** Dùng **Palette X4 (`#363883`, `#DA251C`, `#0093DD`, `#005A9C`)** và font thống nhất **`Segoe UI`** trong [xlsx-palettes.md](../standards/color/xlsx-palettes.md).
3. **Song ngữ xếp dọc (`CellRichText`):** Thay vì nhân đôi số cột gây vỡ khổ A4 dọc, mọi nhãn và diễn giải ghép dọc trong cùng ô: dòng tiếng Việt ở trên (`Regular`/`Bold`, `#1A202C`) + dòng tiếng Anh nghiêng ở dưới (`Italic`, `#595959`).

---

## 2. Kiến Trúc 2 Sheet Chuẩn (`01-Calculation` & `02-References`)

1. **`01-Calculation` (6 cột, tổng rộng `116` đơn vị, khổ A4 Portrait):** `[6, 44, 21, 11, 9, 25]`
   - Header 2 cấp + Logo + Banner tiêu đề nền `#363883` chữ trắng.
   - **Ma trận Kiểm soát Dự án (`A:C` | `D:F`):** 4 hàng ghép ngang dùng `CellRichText` nhãn đậm + giá trị (tránh kẹt chữ tại cột A hẹp `width=6`).
   - **Mục A — Thông số Thiết kế Đầu vào (`inputs`):** Nền `#F0F6FC`, chữ xanh nhập liệu `#005A9C`, ghi nhận tọa độ `D<row>` theo `id` làm nguồn tham chiếu sống.
   - **Mục B — Bảng Tính toán Chi tiết (`sections`):** Phân nhóm theo chương `code`, công thức Excel sống qua cú pháp `{key}` (như `=ROUND({area}*{rate}, 2)`), phân cấp style `calc` / `subtotal` / `key_result` / `grand_total`.
   - **Mục C — Tổng hợp KPI 3 thẻ (`summary_kpis`) + Khối Ký 3 cấp (`signoff`) + Footer 3 màu CCBA.**
2. **`02-References` (4 cột, tổng rộng `116` đơn vị, khổ A4 Portrait):** `[15, 36, 13, 52]`
   - **Bảng 1:** Quy chuẩn & Tiêu chuẩn áp dụng (đọc `scope_vi`/`scope_en` trên từng mục, mặc định kế thừa `document.discipline_vi`/`document.discipline_en`, có thể kèm trích dẫn điều khoản đã kiểm chứng nguyên văn).
   - **Bảng 2:** Chú giải Ký hiệu & Đơn vị (`symbol`, `meaning_vi`, `unit`, `meaning_en`).
   - **Bảng 3:** Quy ước Bảng tính (màu Input / Formula / Total).
   - **Bảng 4 (tùy chọn):** Ghi chú Kỹ thuật & Phạm vi Áp dụng (`technical_notes`, mã `GC-01`, `GC-02`...).

---

## 3. Quy Trình 6 Bước Chuẩn Hóa (`Workflow Distillation`)

| Bước | Thao tác chuẩn hóa | Độ cứng | Chính sách lỗi | Công cụ / Skill tái sử dụng |
| :---: | :--- | :---: | :---: | :--- |
| 1 | Khảo sát `.xlsx` gốc + phỏng vấn khóa phạm vi (song ngữ, khổ giấy, sign-off, quy tắc sửa/giữ công thức) | `Flexible` | `ask` | `/ccba-grilling`, `ccba-xu-ly-van-phong` |
| 2 | Đối soát dẫn chiếu QCVN/TCVN nguyên văn theo `ADR-0059`; thu thập bổ sung nếu kho thiếu | `Strict` | `fail-loud` / `ask` | `ccba-legal-intel`, `ccba-legal-ingest` |
| 3 | Chuẩn hóa dữ liệu vào YAML IR theo [calc_sheet_template_schema.yaml](calc_sheet_template_schema.yaml) (`item_no:`, `{key}`, `technical_notes`) | `Strict` | `fail-loud` | `calc_sheet_template_schema.yaml` |
| 4 | Dựng `.xlsx` tất định qua Deep Seam Tầng 1 (`ccba-ooxml`) | `Strict` | `fail-loud` | `ccba_ooxml:CalculationSheetBuilder`, `ccba-ooxml calc-sheet` |
| 5 | Tính lại công thức + xuất PDF A4 (Windows Excel COM / LibreOffice) & quét 0 lỗi công thức | `Strict` | `fallback` $\rightarrow$ `fail-loud` | `ccba_ooxml:recalc_xlsx`, `audit_xlsx_formula_errors`, `xlsx_to_pdf` |
| 6 | Vòng lặp kiểm định trực quan bắt buộc: render PDF sang ảnh PNG qua `ccba-pdf-prep` và soi cắt chữ, ngắt trang, khối ký | `Strict` | `ask` / lặp tối đa 2 vòng | `ccba_pdf_prep` + kiểm định trực quan trang in |

### Điểm vào Deep Seam Tầng 1 (`ccba-ooxml`)
```bash
ccba-ooxml calc-sheet path/to/calc_spec.yaml -o path/to/output.xlsx --pdf path/to/preview.pdf --recalculate --check-errors --output report.json
```

---

## 4. Hợp Đồng In Ấn & Kiểm Thức Hoàn Thành (`Done Means`)

- [ ] Cấu hình YAML IR hợp lệ, dùng khóa **`item_no:`** (tuyệt đối không dùng `no:` chưa đặt ngoặc kép).
- [ ] Trang in đặt **A4 Portrait**, `fitToWidth = 1`, **`fitToHeight = 0`**, `print_title_rows = "1:5"`, có `Break` tường minh trước Mục B (và trước Quy ước/Ghi chú trên sheet tham chiếu khi có `technical_notes`).
- [ ] Mọi dẫn chiếu tiêu chuẩn/quy chuẩn đã đối soát khớp văn bản gốc OKF (`ADR-0059`), công thức nối sống 100% qua `{key}`.
- [ ] Đã chạy `recalc_xlsx(..., check_errors=True)` cho **0** lỗi `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, `#N/A`, `#NUM!`, `#NULL!`.
- [ ] Đã kiểm định trực quan 100% số trang PDF xuất ra (không mồ côi tiêu đề mục, không tách đôi khối ký 3 cấp, không cụt chữ ở cột hẹp).
