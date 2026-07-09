---
description: Tạo feature branch mới với quy trình lập kế hoạch và phân tách session sạch (Factory Model)
applies_to:
  - "Phần mềm"
bundle: "_software"
---

# Workflow: Tạo Feature Branch Mới & Phân Tách Session (Factory Model)

Quy trình tự động hóa dọn dẹp các branch cũ, khởi tạo branch tính năng mới và cưỡng chế áp dụng mô hình Nhà máy (**The Factory Model**) tách biệt giữa **Planning** và **Coding** để tối ưu hóa chi phí Token (OpEx) và ngăn ngừa lỗi mã nguồn.

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

### Bước 6: Lập kế hoạch thiết kế (Planning Phase - Socrates Grill)
Agent **bắt buộc** phải chuyển sang **Planning Mode**, tuyệt đối không được viết code ở bước này:
1. Kích hoạt kỹ năng `/ccba-grilling` để phỏng vấn người dùng, stress-test các giả định kiến trúc và xác định seam (khớp nối) tích hợp.
2. Tạo tệp [implementation_plan.md](file:///C:/Users/chuvu/.gemini/antigravity/brain/c64af3c1-a210-4fbc-8ae2-2cd50fd53731/implementation_plan.md) đạt chuẩn (phải có mục `## Đánh giá khả năng tái sử dụng (Reuse Assessment)`).
3. Đợi người dùng nhấn **Proceed** phê duyệt bản kế hoạch.

### Bước 7: Bàn giao cô lập ngữ cảnh (Factory Model Hand-off)
Sau khi bản kế hoạch được duyệt, để ngăn ngừa phình to ngữ cảnh hội thoại (Context Rot) và giảm OpEx:
*   **Phương án 1 (Khuyên dùng - Tiết kiệm Token tối đa):** Agent hướng dẫn người dùng tạo một session chat mới hoàn toàn sạch sẽ. Người dùng dán nội dung file `implementation_plan.md` vào lượt chat đầu tiên và ra lệnh cho Coding Agent thực thi.
*   **Phương án 2 (Tự động hóa ngầm):** Agent chính khởi chạy một **Coding Subagent** ngầm thông qua công cụ `invoke_subagent` trên workspace nhánh để thực thi kế hoạch mà không làm ảnh hưởng đến chat log chính.

### Bước 8: Lập trình, Kiểm chứng & Tự sửa lỗi (Coding & Verification Phase)
Coding Agent thực hiện nhiệm vụ:
1. Khởi tạo danh mục theo dõi `task.md`.
2. Viết mã nguồn tương thích, áp dụng type hints và docstring theo chuẩn CCBA.
3. Chạy `/ccba-eval-gate` (hoặc `python scripts/run_harness_evals.py`) để xác thực.
4. Nếu phát hiện linter hoặc type check báo lỗi, tự động kích hoạt **Self-Healing Loop** tối đa 3 lần.
5. Khi tất cả các Gates đều `PASS`, bàn giao kết quả qua tệp `walkthrough.md` cho người dùng nghiệm thu trước khi merge PR.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
