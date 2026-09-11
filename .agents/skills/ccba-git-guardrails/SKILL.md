---
name: ccba-git-guardrails
description: Guardrails to block or request explicit user permission before executing
  dangerous git operations (force push, hard reset, clean, etc.) via terminal.
disable-model-invocation: true
bundle: _software
tier: kernel
user-invocable: true
command: /ccba-git-guardrails
gpi:
  s: 3.0
  k: 2.0
  a: 1.0
  p: 1.0
triggers:
- ccba-git-guardrails
- git guardrails
- git
- guardrails
- safety
- ccba-resolving-merge-conflicts
- resolving-merge-conflicts
---

# Thiết Lập Rào Chắn An Toàn Git (/ccba-git-guardrails)

Thiết lập rào chắn bảo vệ trong thời gian chạy (Runtime Guardrails) nhằm ngăn chặn Agent tự ý thực thi các lệnh Git có tính chất hủy diệt hoặc làm mất mát dữ liệu uncommitted của người dùng.

## Danh mục câu lệnh nguy hiểm (Destructive Operations)
Các câu lệnh sau bắt buộc phải có sự chấp thuận tường minh từ người dùng trước khi gọi qua terminal:
- `git push` (bao gồm mọi biến thể `--force`, `--force-with-lease`, `--delete`).
- `git reset --hard` (hủy bỏ toàn bộ thay đổi chưa commit).
- `git clean -f` / `git clean -fd` (xóa vĩnh viễn các tệp untracked).
- `git branch -D` (xóa nhánh cưỡng bức khi chưa merge).
- `git checkout .` hoặc `git restore .` (hoàn nguyên dữ liệu trên toàn bộ workspace).

---

## Các bước thực hiện

### Bước 1: Nhận diện và đánh chặn câu lệnh nguy hiểm (Command Interception)
1. Trước khi đề xuất hoặc thực thi bất kỳ câu lệnh git nào qua terminal, đối chiếu cú pháp với danh mục câu lệnh nguy hiểm.
2. Phân tích tham số đi kèm (flags như `-f`, `--hard`, `--delete`).
3. Nếu câu lệnh thuộc danh mục nguy hiểm, chặn ngay lập tức quá trình thực thi tự động.
- **Tiêu chí hoàn thành:** Câu lệnh nguy hiểm được phát hiện và tạm dừng thực thi trước khi gửi đến shell.

### Bước 2: Yêu cầu phê duyệt rõ ràng từ người dùng (Permission Request Protocol)
1. Xác định phạm vi tác động cụ thể (danh sách tệp sẽ bị xóa hoặc nhánh bị ảnh hưởng).
2. Kích hoạt công cụ `ask_permission` với Action `command` và Target là tiền tố câu lệnh cụ thể, hoặc gửi tin nhắn giải trình rõ lý do kỹ thuật.
3. Chờ đợi phản hồi chính thức từ người dùng, tuyệt đối không suy diễn sự đồng thuận ngầm định.
- **Tiêu chí hoàn thành:** Yêu cầu phê duyệt được hiển thị rõ ràng kèm lý do và câu lệnh chính xác cho người dùng.

### Bước 3: Kiểm tra trạng thái an toàn trước thực thi (Pre-execution Safety Check)
1. Chạy `git status` để kiểm tra có tệp unstaged hoặc tệp tạm nào quan trọng có nguy cơ bị ghi đè hay không.
2. Nếu có tệp nhạy cảm (như `.env`, logs, tệp cấu hình Spoke), tạo bản sao lưu tạm thời trước khi tiến hành.
3. Xác minh nhánh hiện tại đang đứng có đúng là nhánh dự kiến thao tác hay không.
- **Tiêu chí hoàn thành:** Trạng thái workspace an toàn, không có nguy cơ mất mát dữ liệu ngoài ý muốn.

### Bước 4: Thực thi có giám sát và kiểm tra hậu kỳ (Controlled Execution & Audit)
1. Thực thi câu lệnh đã được người dùng cấp quyền với tham số tối thiểu cần thiết.
2. Kiểm tra mã thoát (exit code) và thông báo phản hồi từ Git.
3. Chạy lại `git status` hoặc `git log -n 1` để xác nhận kết quả sau khi lệnh hoàn tất.
4. Ghi nhận nhật ký thao tác an toàn vào hệ thống theo dõi kiểm toán.
- **Tiêu chí hoàn thành:** Lệnh được thực thi thành công, kết quả được xác minh và nhật ký kiểm toán ghi nhận đầy đủ.


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/merge_conflict_resolution.md` | Cẩm nang giải quyết xung đột mã nguồn Git merge an toàn |

