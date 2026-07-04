---
description: Tạo feature branch mới với cleanup tự động
applies_to:
  - "Phần mềm"
bundle: "_software"
---

# Workflow: Tạo Feature Branch Mới

Quy trình tự động hóa dọn dẹp các branch cũ đã được tích hợp và khởi tạo một branch tính năng/sửa lỗi mới.

## Các bước thực hiện:

### Bước 1: Chuẩn bị môi trường
Quay về branch `main` và kéo code mới nhất từ remote:
```bash
git checkout main && git pull origin main
```

### Bước 2: Dọn dẹp các branch cũ đã merge
Dọn dẹp các branch cục bộ đã được tích hợp vào `main` để giải phóng bộ nhớ. Lệnh này tương thích đa nền tảng (bao gồm Windows PowerShell và Linux):
```powershell
git fetch -p
git branch --merged main | Where-Object { $_ -notmatch 'main' } | ForEach-Object { git branch -d $_.Trim() }
```

### Bước 3: Thu thập thông tin tính năng mới
Hỏi người dùng lần lượt các thông tin:
1. Loại công việc cần thực hiện: `feature` (tính năng mới), `fix` (sửa lỗi), `docs` (tài liệu), `refactor` (cải tiến cấu trúc), hoặc `experiment` (thử nghiệm).
2. Mô tả ngắn gọn tính năng (3-5 từ).

### Bước 4: Đề xuất tên branch
Dựa trên câu trả lời, đề xuất tên branch theo định dạng chuẩn CCBA:
- `feature/ten-tinh-nang`
- `fix/ten-loi`
- `docs/ten-tai-lieu`
- `refactor/ten-module`
- `experiment/ten-thu-nghiem`

*Quy tắc đặt tên branch:* Viết thường hoàn toàn (lowercase), sử dụng dấu gạch ngang `-` thay cho khoảng trắng, ngắn gọn và tường minh.
Yêu cầu người dùng xác nhận tên branch đề xuất (`yes/no`).

### Bước 5: Khởi tạo branch mới
Sau khi người dùng đồng ý, tạo và chuyển sang branch mới:
```bash
git checkout -b [ten_branch_da_chot]
```

### Bước 6: Thông báo hoàn tất
Thông báo cho người dùng:
- ✅ Branch mới đã được khởi tạo cục bộ thành công.
- 📉 Đã dọn dẹp các branch cục bộ cũ đã merged.
- 🚀 Sẵn sàng bắt đầu phát triển tính năng.
