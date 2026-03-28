# Scripts — Reusable Python/PowerShell scripts

Thư mục chứa các scripts deterministic chạy bởi Agent hoặc user trực tiếp.

## Quy tắc

- Scripts phải có docstring mô tả mục đích
- Input/Output rõ ràng qua arguments hoặc stdin/stdout
- Không hardcode paths — dùng config hoặc arguments
- Dependencies liệt kê trong `requirements.txt` (nếu Python)

## Phân biệt Scripts vs Skills

| | Scripts | Skills |
|---|---------|--------|
| **Bản chất** | Code deterministic | Instructions cho Agent |
| **Chạy bởi** | Python/PowerShell interpreter | AI Agent (LLM) |
| **Output** | Kết quả cố định | Kết quả sáng tạo/phân tích |
| **Ví dụ** | Export YAML→DOCX, validate data | Tạo impact report, soạn công văn |
