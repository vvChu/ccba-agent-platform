---
name: table-reconstructor
description: Sub-skill dựng lại các bảng biểu Markdown bị vỡ dọc hoặc lệch cột (tích hợp trong ConversionPipeline).
role: sub_skill
master_skill: markdown-document-processing
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Sub-skill: Table Reconstructor

Kỹ năng này chịu trách nhiệm phục hồi nguyên trạng hệ thống bảng biểu bị vỡ dọc hoặc mất cấu trúc hàng/cột trong quá trình chuyển đổi Markdown. Kỹ năng đã được **tích hợp tự động** vào Deep Seam `ConversionPipeline` ([`packages/mdconverter`](../../packages/mdconverter)).

---

## 1. Tích hợp Tự động trong Pipeline

Khi sử dụng `ConversionPipeline.convert()`, bộ xử lý bảng tự động chạy đối chiếu để khôi phục cấu trúc bảng mà không cần gọi lệnh thủ công.

---

## 2. Lệnh CLI & Can thiệp Độc lập

Sử dụng lệnh CLI sau khi cần xử lý riêng lẻ một tệp Markdown có file Word `.docx` gốc để đối chiếu:

```bash
python -m mdconverter.cli process-table --file [đường_dẫn_tệp_markdown] --docx [đường_dẫn_tệp_docx_gốc]
```

---

## 3. SOP Xử lý Thủ công (Khi không có file .docx gốc)

Nếu không có tệp `.docx` gốc để đối chiếu, Agent áp dụng thuật toán gộp các dòng bị vỡ dọc dựa trên ký tự tab `\t`:

1. **Nhận dạng mẫu vỡ:**
   * Một hàng gồm các cột $A, B, C$ bị tách thành nhiều dòng cách quãng:
     ```text
     Dòng n: A
     Dòng n+1: (trống)
     Dòng n+2: \t B
     Dòng n+3: (trống)
     Dòng n+4: \t C
     ```
2. **Quy tắc gộp:**
   * Loại bỏ các dòng trống dư thừa.
   * Gộp các dòng text có dấu tab thụt lề liền kề thành một hàng Markdown duy nhất:
     `| A | B | C |`
3. **Mẫu script Python xử lý nhanh (KISS):**
   ```python
   def reconstruct_simple_table(lines: list[str]) -> list[str]:
       reconstructed: list[str] = []
       current_row: list[str] = []
       for line in lines:
           clean = line.strip()
           if not clean:
               continue
           if line.startswith('\t') or len(line) - len(line.lstrip()) >= 2:
               current_row.append(clean)
           else:
               if current_row:
                   reconstructed.append("| " + " | ".join(current_row) + " |")
               current_row = [clean]
       if current_row:
           reconstructed.append("| " + " | ".join(current_row) + " |")
       return reconstructed
   ```
