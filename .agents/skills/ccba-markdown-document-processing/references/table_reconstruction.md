# Table Reconstruction Reference

Tài liệu này quy định chi tiết thuật ngữ, mẫu hình nhận diện và giải thuật phục hồi hệ thống bảng biểu Markdown bị vỡ dọc hoặc lệch cột.

---

## 1. Mẫu hình Bảng Vỡ Dọc (Pattern Recognition)

Một hàng gồm các cột $A, B, C$ bị tách thành nhiều dòng cách quãng do lỗi ngắt dòng khi chuyển đổi từ Word/PDF:

```text
Dòng n: A
Dòng n+1: (trống)
Dòng n+2: \t B
Dòng n+3: (trống)
Dòng n+4: \t C
```

---

## 2. Giải Thuật Gộp Dòng (KISS Algorithm)

1. **Quy tắc gộp:**
   * Loại bỏ các dòng trống dư thừa.
   * Gộp các dòng text có dấu tab `\t` thụt lề liền kề thành một hàng Markdown duy nhất: `| A | B | C |`.

2. **Mã nguồn mẫu Python:**
```python
def reconstruct_simple_table(lines: list[str]) -> list[str]:
    """Reconstruct vertically fractured tables into single-line markdown rows."""
    reconstructed: list[str] = []
    current_row: list[str] = []
    for line in lines:
        clean = line.strip()
        if not clean:
            continue
        if line.startswith("\t") or len(line) - len(line.lstrip()) >= 2:
            current_row.append(clean)
        else:
            if current_row:
                reconstructed.append("| " + " | ".join(current_row) + " |")
            current_row = [clean]
    if current_row:
        reconstructed.append("| " + " | ".join(current_row) + " |")
    return reconstructed
```

---

## 3. Lệnh CLI Đối Chiếu Tự Động (Khi có file .docx gốc)

```bash
python -m mdconverter.cli process-table --file [đường_dẫn_tệp_markdown] --docx [đường_dẫn_tệp_docx_gốc]
```


---

## 4. Rào Chắn Phân Tách 2 Vùng Chú Thích (Dual-Zone Decoupling Engine — ADR 0041)

Khi bảng có cả chú thích theo ô và chú thích giải nghĩa chung (như Bảng 2 QCVN 10:2025/BCA):
1. **Phân tách 2 vùng độc lập:**
   * **Vùng 1 (Cell Footnotes):** Các dòng `(1) ...`, `(2) ...` đặt ngay dưới bảng Markdown, không có header `CHÚ THÍCH:`.
   * **Vùng 2 (General Legend):** Khối giải thích ký hiệu chung, mở đầu bằng `**CHÚ THÍCH:**`, mỗi gạch đầu dòng dùng thụt lề cấp 1 `&nbsp;&nbsp;\- `.
2. **Gán nhãn ngữ nghĩa cho ô gộp ngang (`gridSpan`):**
   * Hàng gộp ngang toàn bộ phân nhóm bắt buộc có nhãn `*(Áp dụng chung)*` (Markdown) / `Áp dụng chung` (CSV/JSON).
3. **Chuẩn hóa chân mỏ neo Heuristic (`<sup>` Normalization):**
   * Tự động nhận diện các mẫu `+(\d+)`, `++(\d+)`, `Từ(\d+)` để bọc thẻ `<sup>(\d+)</sup>` khi Word/PDF scan bị mất thuộc tính run `superscript`.

---

## 5. Quy Tắc An Toàn Dữ Liệu Bảng Biểu (ADR 0041 & ADR 0044)

Khi bóc tách hoặc tái tạo bảng số liệu, Agent và bộ chuyển đổi bắt buộc phải tuân thủ nghiêm ngặt 3 rào chắn toàn vẹn dữ liệu:

1. **Rào chắn Chống Gộp Hàng Số Liệu Thuần (Numeric Subheader Collision Guard - RULE-3.3):**
   * *Nguyên nhân:* Khi một hàng có nhiều cột mang cùng giá trị số (ví dụ: `['50', '50']` cho tốc độ 50 km/h và khoảng cách dừng 50 m), thuật toán kiểm tra trùng ô `len(set(non_empty)) == 1` rất dễ nhầm lẫn đây là dòng tiêu đề phân nhóm (category/subheader) và gộp thành `['**50**', '']`, làm mất mát dữ liệu thực tế của các cột sau.
   * *Quy tắc:* Bắt buộc kiểm tra `not is_numeric` (`not re.match(r"^[0-9\.,\-\+±%\s]+$", cell)`) trước khi thực hiện gộp dòng subheader. Tuyệt đối cấm gộp dòng nếu ô chứa số thuần túy hoặc đơn vị đo.

2. **Khử Trùng Lặp Chú Thích Ô Gộp Ngang (Merged-Cell Footnote Deduplication - RULE-3.4):**
   * *Nguyên nhân:* Trong OpenXML DOCX, khi một ô bảng bị gộp ngang (`gridSpan`), `row.cells` trả về chuỗi text lặp lại cho từng ô thành phần. Nếu hàng chứa chú thích (`<br>CHÚ THÍCH 2:...`), vòng lặp quét cell sẽ append chú thích nhiều lần, gây trùng lặp trong metadata JSON (`fn_1` và `fn_2` giống hệt nhau).
   * *Quy tắc:* Bắt buộc kiểm tra `if nl not in footnotes` trước khi nạp vào danh sách chú thích bảng.

3. **Chuẩn Hóa Tiền Tố Bảng Đa Phần (Multipart Table Disambiguation - ADR 0044):**
   * Đối với các quy chuẩn kỹ thuật có nhiều phần độc lập (như QCVN 07:2023/BXD), bảng biểu bắt buộc phải mang tiền tố phần `bang_pXX_YY.csv` (ví dụ `bang_p04_01.csv` thay vì `bang_01.csv`) và khai báo trường `part_id: "pXX"` trong `tables_catalog.json` để ngăn chặn triệt để tình trạng ghi đè tệp dữ liệu trên đĩa.

