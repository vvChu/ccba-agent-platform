# Mẫu Biểu: Báo Cáo Đánh Giá Kỹ Thuật DOCX (CCBA Brand v3.4)

> **Mô tả**: Quy chuẩn thiết kế, cấu trúc YAML IR trung tính và quy trình 6 bước biên soạn Báo cáo Đánh giá Kỹ thuật Word (`.docx`) chuẩn **CCBA Brand Identity v3.4** dưới danh nghĩa `IBST - CCBA`.  
> **Cấp độ kiến trúc**: Tier 2A Canonical Engineering Reference & Template (`ADR-0057`)  
> **Áp dụng**: Kỹ năng `ccba-xu-ly-van-phong` kết hợp Deep Seam `ccba_ooxml:TechnicalReportBuilder` / `build_tech_report_from_yaml` / CLI `ccba-ooxml tech-report`.

---

## 1. Quy Chuẩn Thương Hiệu & `RULE-6.1` (Brand v3.4)

1. **Header 2 cấp chuẩn trên Trang bìa (Page 1):**
   - Cấp trên: `VIỆN KHOA HỌC CÔNG NGHỆ XÂY DỰNG` / phụ đề tiếng Anh nghiêng `Institute for Building Science and Technology`.
   - Đơn vị trực thuộc: `TRUNG TÂM TƯ VẤN VÀ ỨNG DỤNG BIM TRONG XÂY DỰNG` / phụ đề `Center for Consulting Services and BIM Application in Construction (CCBA)`.
   - Logo chính thức (`logo_ccba_full.png`) phân giải động qua `Path(ccba_ooxml.__file__).resolve().parent` căn phải phía trên đường gạch đỏ IBST `#DA251C`.
   - **Cấm dùng:** Không đưa dòng cơ quan chủ quản `"Bộ Xây dựng"` lên tiêu đề báo cáo kỹ thuật dự án; không gắn đuôi `(IBST)` hay `(CCBA)` vào dòng tiếng Việt; trường Tư vấn thống nhất ghi **`IBST - CCBA`** (cấm dùng dấu gạch chéo giữa hai đơn vị).
2. **Bảng phối màu chuẩn:** Dùng [docx-ccba-brand.md](../standards/color/docx-ccba-brand.md) (`#363883`, `#DA251C`, `#0093DD`, `#005A9C`) và font thống nhất **`Segoe UI`** trên đủ 4 khe OpenXML `w:rFonts` (`w:ascii`, `w:hAnsi`, `w:eastAsia`, `w:cs`).

---

## 2. Hợp Đồng Hình Học A4 & OpenXML Bất Biến (`9071 DXA`)

| Thông số | Giá trị chuẩn | Mục đích & Bất biến OpenXML |
| :--- | :---: | :--- |
| **Khổ giấy** | A4 (`210 × 297 mm`) | `11906 × 16838 DXA` |
| **Lề trang (Margins)** | `L=30 mm, R/T/B=20 mm` | `L=1701`, `R=1134`, `T=1134`, `B=1134 DXA` |
| **Chiều rộng nội dung** | `9071 DXA` | `11906 - 1701 - 1134 = 9071 DXA` (đóng gáy hồ sơ dự án) |
| **Trang bìa (Page 1)** | `different_first_page_header_footer = True` | Trang 1 độc lập (Logo + Tổ chức 2 cấp + Document Control Matrix), ẩn header/footer chạy trang |
| **Header Pages 2+** | `[3571, 5500]` DXA (`sum = 9071`) | Bắt buộc gọn trên **1 dòng duy nhất** (mã hồ sơ + `IBST - CCBA` trái, tên báo cáo rút gọn phải) |
| **Footer Pages 2+** | `[6571, 2500]` DXA (`sum = 9071`) | Slogan 3 màu + `IBST - CCBA` + `contact_email` trái; trường XML Word `PAGE` / `NUMPAGES` phải |
| **Bảng dữ liệu** | `<w:tblLayout w:val="fixed"/>` | `<w:tblGrid>` tổng bằng chính xác `9071 DXA`, `<w:cantSplit/>` mọi hàng, `<w:tblHeader/>` tiêu đề |
| **Khối ký nguyên tử** | `4535 + 4536` (2 cột) / `3024 + 3023 + 3024` (3 cột) | Bắt buộc `<w:cantSplit/>` chống tách đôi qua hai trang |

---

## 3. Bốn Rào Chắn Biên Tập & Bố Cục Thực Chiến

1. **Tiêu đề tóm tắt tiếng Việt tự nhiên:** Dùng **`TÓM TẮT BÁO CÁO / EXECUTIVE SUMMARY`** (hoặc `TÓM TẮT ĐÁNH GIÁ`); cấm dùng cụm dịch máy không tự nhiên `"TÓM TẮT ĐIỀU HÀNH"`.
2. **Khối ký đối xứng nguyên tử (không lặp email/tên tổ chức):** Thông tin email liên hệ chỉ đặt tại Page 1 Document Control Matrix và Footer chạy trang. Mỗi ô trong khối ký chỉ chứa đúng 5 phần: Role Header VI/EN, `(Ký, ghi rõ họ tên)`, khoảng trống ký tươi, Họ tên, và Chức danh chính xác (ví dụ: `Giám đốc / Director`).
3. **Tuân thủ `RULE-6.1` & Tương phản WCAG 2.1:** Không xuất hiện `"Bộ Xây dựng"` trên header 2 cấp; mọi chữ số liệu KPI/metric trên nền `#F8FAFC` / `#FFFFFF` dùng `#005A9C` thay vì `#0093DD`.
4. **Cấu trúc `sections` động (Section-Agnostic):** Lược đồ `sections: [...]` hỗ trợ linh hoạt mọi số lượng chương mục và các khối tổ hợp (`paragraphs`, `subsections`, `tables`, `callouts`, `bullets`, `kpis`) thay vì đóng cứng số mục.

---

## 4. Quy Trình 6 Bước & Điểm Vào CLI (`ccba-ooxml tech-report`)

| Bước | Thao tác chuẩn hóa | Độ cứng | Công cụ / Seam tái sử dụng |
| :---: | :--- | :---: | :--- |
| 1 | Khảo sát phạm vi đánh giá, thống nhất số mục `sections`, KPI và cấu trúc khối ký 2/3 cột | `Flexible` | `ccba-grilling`, `ccba-xu-ly-van-phong` |
| 2 | Đối soát dẫn chiếu QCVN/TCVN nguyên văn (`ADR-0059`); thu thập bổ sung nếu kho thiếu | `Strict` | `ccba-legal-intel`, `ccba-legal-ingest` |
| 3 | Chuẩn hóa nội dung vào YAML IR theo mẫu [tech_report_template_schema.yaml](tech_report_template_schema.yaml) | `Strict` | `tech_report_template_schema.yaml` |
| 4 | Dựng `.docx` tất định qua Deep Seam `ccba-ooxml` (kèm xuất PDF vector) | `Strict` | `TechnicalReportBuilder`, `ccba-ooxml tech-report` |
| 5 | Kiểm tra toàn vẹn OpenXML (`validate_document`) & chuyển đổi PDF qua `docx_to_pdf` | `Strict` | `ccba_ooxml:validate_document`, `docx_to_pdf` |
| 6 | **Visual QA Gate bắt buộc:** Render từng trang PDF sang PNG bằng `ccba-pdf-prep` và soi trực quan: Page 1 không tràn trang, header 1 dòng, 0 heading mồ côi, khối ký không tách trang | `Strict` | `ccba_pdf_prep:render_page_to_image` |

### Điểm vào Deep Seam Tầng 1 (`ccba-ooxml`)
```bash
ccba-ooxml tech-report path/to/report_spec.yaml -o path/to/report.docx --pdf path/to/preview.pdf --output report.json
```

---

## 5. Hợp Đồng Kiểm Thức Hoàn Thành (`Done Means`)

- [ ] Cấu hình YAML IR hợp lệ theo [tech_report_template_schema.yaml](tech_report_template_schema.yaml), không chứa dữ liệu dự án nhạy cảm hoặc đường dẫn máy cục bộ.
- [ ] Trang bìa Page 1 cân đối trên 1 trang, Header 2 cấp tuân thủ `RULE-6.1` (không `"Bộ Xây dựng"`, không đuôi `(IBST)`/`(CCBA)` trên dòng tiếng Việt).
- [ ] Trang 2+ có single-line running header `[3571, 5500]` DXA, tri-color footer kèm `contact_email` và trường Word `PAGE`/`NUMPAGES` hoạt động thực.
- [ ] Mọi bảng đạt `<w:tblLayout w:val="fixed"/>`, `<w:tblGrid>` tổng đúng `9071 DXA`, `<w:cantSplit/>` trên mọi hàng, `<w:tblHeader/>` trên tiêu đề bảng dữ liệu.
- [ ] Đã chạy `docx_to_pdf` và kiểm định trực quan 100% số trang PNG (0 heading mồ côi, 0 tách đôi khối ký, WCAG contrast đạt chuẩn).
