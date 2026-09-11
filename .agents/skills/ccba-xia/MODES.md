# Xia CLI Options & Modes Reference

Đây là tài liệu tham khảo chi tiết về các chế độ chạy, tham số dòng lệnh và cơ chế nhận diện ý định của kỹ năng `ccba-xia`.

## Cú pháp Lệnh

```text
/ccba-xia <github-url|owner/repo|local-path> [feature-description] [--compare|--copy-raw|--improve|--port] [--auto|--fast]
```

## Các chế độ chạy (Modes)
- `--compare`: chỉ phân tích so sánh song song (side-by-side) kiến trúc và các bài toán đánh đổi, không lập kế hoạch triển khai.
- `--copy-raw`: cấy ghép mã nguồn với số lượng thay đổi tối thiểu, đánh dấu tường minh các file chưa tuân thủ tiêu chuẩn Platform (gắn comment header `[XIA-COPY-RAW]`) và bắt buộc tạo follow-up Issue refactor.
- `--improve`: sao chép kèm theo tái cấu trúc (refactor) cho phù hợp codebase hiện tại của platform.
- `--port`: viết lại hoàn toàn một cách tự nhiên (idiomatic) theo stack của dự án (mặc định).

## Kiểm soát tốc độ (Speed)
- `--fast`: rút gọn các pha nghiên cứu và phản biện. Pha 4 (Challenge) vẫn bắt buộc self-challenge ≥3 câu hỏi cốt lõi (không được bỏ qua hoàn toàn). Kế hoạch triển khai sẽ được gắn cảnh báo `[!WARNING]`.
- `--auto`: giữ nguyên quy trình đầy đủ nhưng tự động phê duyệt các cổng kiểm soát không cần dừng lại hỏi.
- Mặc định: quy trình đầy đủ và dừng lại xin phê duyệt thủ công ở các cổng kiểm soát (Hard Gate).

## Kết hợp không hợp lệ (Invalid Combinations)
- `--copy-raw` + `--fast`: **BỊ CẤM**. Nếu đã chọn bỏ qua refactor, phải giữ nguyên quy trình phản biện đầy đủ để đánh giá rủi ro.

## Nhận diện ý định (Intent detection)
- "compare" hoặc "vs" -> `--compare`
- "copy", "exact", hoặc "as-is" -> `--copy-raw`
- "improve", "better", hoặc "adapt" -> `--improve`
- "port", "convert", hoặc "rewrite" -> `--port`
- Đường dẫn/file cụ thể -> tự động thu hẹp phạm vi quét.
