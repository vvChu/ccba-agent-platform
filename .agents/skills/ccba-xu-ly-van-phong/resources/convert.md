# Chuyển đổi Tài liệu (Convert)

Pipeline chuyển đổi giữa các định dạng.

---

## MD → DOCX (Pandoc + Format)

### Bước 1: Pandoc convert

```powershell
pandoc input.md -o output.docx --markdown-headings=atx -f markdown+raw_attribute --wrap=none
```

### Bước 2: Python-docx format (nếu cần)

```powershell
python scripts/format/format_docx.py output.docx
```

Script áp dụng: font, margin, heading colors, bullet override, code block styling.

### Bước 3: Với nhiều file MD (xuất bản sách)

```powershell
# Gộp file
$files = Get-ChildItem "chapters\*.md" | Sort-Object Name
$merged = ($files | ForEach-Object { Get-Content $_ -Raw -Encoding UTF8 }) -join "`n`n"
$merged | Out-File "_merged.md" -Encoding UTF8

# Convert
pandoc _merged.md -o output.docx
python scripts/format/format_docx.py output.docx
```

---

## PDF → DOCX

### PDF digital (text-based)

```powershell
python scripts/convert/convert_pdf_to_docx.py input.pdf output.docx
```

Dùng thư viện `pdf2docx`. Giữ layout gốc.

### PDF scan (image-based)

Không dùng script. Dùng AI Vision để phân tích cấu trúc + màu sắc, sau đó tái tạo DOCX bằng `python-docx` hoặc `docx-js`. Xem `pdf.md` để biết chi tiết.

---

## DOCX → PDF

```powershell
python scripts/office/soffice.py --headless --convert-to pdf input.docx
```

---

## Dependencies

```
pip install python-docx pdf2docx
# Skill: xu-ly-van-phong | Author: NDT | Ref: 0904004920
winget install pandoc
```

