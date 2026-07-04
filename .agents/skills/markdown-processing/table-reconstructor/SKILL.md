---
name: table-reconstructor
description: Sub-skill dựng lại các bảng biểu Markdown bị vỡ dọc hoặc lệch cột bằng file đối chiếu .docx hoặc thuật toán Python.
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Sub-skill: Table Reconstructor

Kỹ năng này chịu trách nhiệm phục hồi nguyên trạng hệ thống bảng biểu bị vỡ dọc hoặc mất cấu trúc hàng/cột trong quá trình chuyển đổi Markdown.

## Lệnh CLI Tự động
Sử dụng lệnh CLI sau khi có file Word `.docx` gốc để đối chiếu:
```bash
python -m mdconverter.cli process-table --file [đường_dẫn_tệp_markdown] --docx [đường_dẫn_tệp_docx_gốc]
```

## SOP Xử lý Thủ công (Khi không có file .docx gốc)
Nếu không có tệp `.docx` gốc để đối chiếu, Agent bắt buộc phải viết script Python hoặc dùng Regex để gộp các dòng bị vỡ dọc dựa trên ký tự tab `\t`:

1. **Nhận dạng mẫu vỡ:**
   * Một hàng gồm các cột $A, B, C$ bị tách thành:
     ```
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
3. **Mẫu script Python xử lý thô nhanh (KISS):**
   ```python
   def reconstruct_simple_table(lines):
       reconstructed = []
       current_row = []
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
