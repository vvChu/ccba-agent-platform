# Hub Proposals Registry

Thư mục này chứa các đề xuất tích hợp skill/workflow/tool mới từ các dự án (Spoke) gửi lên Hub.

## Quy ước đặt tên file

```
<YYYY-MM-DD>_<tên-đề-xuất>.md
Ví dụ: 2026-04-18_auto-pdf-namer.md
```

## Trạng thái (status)

| Status | Ý nghĩa |
|--------|---------|
| `open` | Đang chờ review từ Platform team |
| `accepted` | Đã chấp thuận, đang triển khai |
| `implemented` | Đã tích hợp vào Hub thành công |
| `rejected` | Không phù hợp, có giải thích lý do |
| `deferred` | Tạm hoãn — xem xét lại sau |

## Quy trình xem xét

1. AI Agent đọc proposals khi chạy `/session-retrospective` hoặc khi được hỏi
2. Platform team (người dùng) review và cập nhật trường `status`
3. Nếu `accepted` → tạo feature branch tại Hub để implement
4. Sau khi merge → cập nhật `status: implemented` và ghi ngày tích hợp

## Lọc proposals

```powershell
# Xem tất cả proposals đang mở
Select-String -Path ".agent\proposals\*.md" -Pattern "status: .open."

# Xem theo loại
Select-String -Path ".agent\proposals\*.md" -Pattern "type: .skill."
```
