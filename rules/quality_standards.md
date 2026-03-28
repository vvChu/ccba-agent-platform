# CCBA Quality Standards — Quy chuẩn chất lượng

> Quy định về chất lượng output mà Agent phải tuân thủ.

## Tiêu chuẩn chung

### Output phải đạt

| # | Tiêu chuẩn | Mô tả |
|---|-----------|-------|
| 1 | **Accuracy** | Trích dẫn VBPL phải chính xác số hiệu, điều/khoản, ngày hiệu lực |
| 2 | **Completeness** | Checklist phải đầy đủ theo Phụ lục VBPL, không bỏ sót mục |
| 3 | **Timeliness** | Thông tin VBPL phải là phiên bản mới nhất (kiểm tra registry) |
| 4 | **Traceability** | Mọi claim phải có nguồn: VBPL, TCVN, hoặc session reference |
| 5 | **Validation** | YAML files phải pass `yaml.safe_load()` sau mỗi chỉnh sửa |

### Output KHÔNG được

- ❌ Đưa nội dung VBPL dự thảo (draft) như đã ban hành
- ❌ Bỏ qua disclaimer khi nội dung liên quan pháp luật
- ❌ Tự sáng tạo số hiệu VBPL không tồn tại
- ❌ Pha trộn quy định cũ và mới mà không đánh dấu rõ ràng

## Quy trình review

### Tự động (Agent thực hiện)
1. Validate YAML syntax
2. Kiểm tra cross-reference giữa registry và checklist
3. Kiểm tra file tồn tại khi reference local_files

### Thủ công (User review)
1. Nội dung pháp lý → chuyên gia pháp lý xác nhận
2. Dữ liệu dự án → PM hoặc TVGS xác nhận
3. Tài liệu công khai → Trưởng phòng BIM RD phê duyệt

## Chỉ số chất lượng

| Metric | Target | Đo bằng |
|--------|--------|---------|
| Registry completeness | 100% VBPL liên quan | Đếm entries vs danh sách thực |
| Checklist accuracy | >95% items đúng | So sánh với Phụ lục VIb gốc |
| VBPL currency | <7 ngày lag | last_updated vs ngày hiện tại |
