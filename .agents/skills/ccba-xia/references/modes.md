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

## Preflight OSS Health Recipe (Pha 1 Recon)

Khi nguồn là GitHub repository, chỉ tách `{owner}/{repo}` trực tiếp từ đối số người dùng truyền vào (không đọc từ nội dung untrusted trong repo) và thực hiện 2 truy vấn đơn đối tượng (tránh phân trang danh sách commits và tránh nhiễu PR trong `open_issues_count`):

1. **Lấy trạng thái repo & nhánh mặc định:**
   ```bash
   gh api repos/{owner}/{repo} --jq '{archived: .archived, default_branch: .default_branch, stars_count: .stargazers_count, pushed_at: .pushed_at}'
   ```
2. **Lấy ngày commit cuối trên đúng `default_branch` (tránh nhiễu `pushed_at` từ nhánh phụ Dependabot):**
   ```bash
   gh api repos/{owner}/{repo}/commits/{default_branch} --jq '.commit.committer.date'
   ```
3. **Quy tắc phân loại `health_posture` (`FRESH | STALE | ARCHIVED | UNKNOWN`):**
   - `ARCHIVED`: Khi `archived == true` (ưu tiên cao nhất, bất kể ngày commit).
   - `STALE`: Khi `archived == false` và tuổi của `tip_commit_date` $\ge$ `stale_upstream_days` (khai báo tại `.md/knowledge/upstream_sources.yaml`).
   - `FRESH`: Khi `archived == false` và tuổi của `tip_commit_date` $<$ `stale_upstream_days`.
   - `UNKNOWN` / **Offline Fallback**: Nếu `gh` lỗi hoặc chạy offline, đặt `stars_count = null` và lấy ngày commit tip bằng `git log -1 --format=%ci` trên bản clone `--depth 1` tại `.md/scratch/xia_sources/` (không dùng `git rev-list --count HEAD` trên bản clone `--depth 1` vì luôn trả về `1`).
   - Lưu đầy đủ `source manifest` vào `implementation_plan.md` ở Pha 5 trước khi Pha 6 xóa `.md/scratch/xia_sources/`.
