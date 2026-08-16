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
