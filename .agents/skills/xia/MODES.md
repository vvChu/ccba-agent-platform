# Xia CLI Options & Modes Reference

Đây là tài liệu tham khảo chi tiết về các chế độ chạy, tham số dòng lệnh và cơ chế nhận diện ý định của kỹ năng `ccba-xia`.

## Cú pháp Lệnh

```text
/ccba-kit xia <github-url|owner/repo|local-path> [feature-description] [--compare|--copy|--improve|--port] [--auto|--fast]
```

## Các chế độ chạy (Modes)
- `--compare`: chỉ phân tích so sánh song song (side-by-side) kiến trúc và các bài toán đánh đổi, không lập kế hoạch triển khai.
- `--copy`: cấy ghép tính năng với số lượng thay đổi tối thiểu, bỏ qua việc sửa cấu trúc.
- `--improve`: sao chép kèm theo tái cấu trúc (refactor) cho phù hợp codebase hiện tại của platform.
- `--port`: viết lại hoàn toàn một cách tự nhiên (idiomatic) theo stack của dự án (mặc định).

## Kiểm soát tốc độ (Speed)
- `--fast`: bỏ qua các pha nghiên cứu và phản biện chi tiết, tự động phê duyệt các cổng kiểm soát.
- `--auto`: giữ nguyên quy trình đầy đủ nhưng tự động phê duyệt các cổng kiểm soát không cần dừng lại hỏi.
- Mặc định: quy trình đầy đủ và dừng lại xin phê duyệt thủ công ở các cổng kiểm soát (Hard Gate).

## Nhận diện ý định (Intent detection)
- "compare" hoặc "vs" -> `--compare`
- "copy", "exact", hoặc "as-is" -> `--copy`
- "improve", "better", hoặc "adapt" -> `--improve`
- "port", "convert", hoặc "rewrite" -> `--port`
- Đường dẫn/file cụ thể -> tự động thu hẹp phạm vi quét.
