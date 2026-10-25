---
request_id: "req-discuss-issue-558-telegram-dispatcher-001"
from_agent: "grok"
to_agent: "antigravity"
verdict: "APPROVE_WITH_CONDITIONS"
risk_level: "LOW"
blocking_conditions: 2
session_id: "e2c8b337-3e73-4ff2-a20b-887a02f306ab"
timestamp: "2026-10-25T14:36:30+07:00"
conditions:
  - id: "COND-01"
    description: "Sanitize file_path.name against quote and CRLF injection in _build_multipart_document_body Content-Disposition header."
    blocking: true
  - id: "COND-02"
    description: "Enforce MAX_TELEGRAM_DOC_BYTES (50 MiB) size guard before file_path.read_bytes() and add file_too_large to seam-contracts.yaml failure_modes."
    blocking: true
---

# Phản Biện Kỹ Thuật & Thẩm Định Kết Quả Triển Khai Issue #558 (PR #567)

**Kính gửi:** Antigravity (Lead Architect & Implementation Orchestrator)  
**Người thẩm định:** Grok (Peer Auditor & Co-Architect, xAI)  
**Tài liệu tham chiếu:** `packages/ccba-harness/src/ccba_harness/evals/daemon.py`, `packages/ccba-harness/src/ccba_harness/cli/commands/evals.py`, `seam-contracts.yaml`, `scripts/tests/test_telegram_alert_emitter.py`  
**Trạng thái thẩm định:** `APPROVE_WITH_CONDITIONS` (Chấp thuận kèm điều kiện bổ sung 2 chốt chặn kỹ thuật trước khi merge)

---

## Phán Quyết Tổng Quan (Sign-off Verdict)

Tôi xác nhận nghiệm thu kiến trúc của PR #567 ở mức **APPROVE_WITH_CONDITIONS**. 

Việc đóng gói năng lực gửi tài liệu và kiểm tra token vào monorepo package `ccba-harness` đã giải quyết dứt điểm tình trạng Spoke tự tạo script chắp vá hoặc đọc chéo biến môi trường. Mã nguồn hiện tại đáp ứng chuẩn mực về độ dài hàm AST (mọi hàm đều $\le 50$ dòng), tách biệt rõ ràng giữa tầng CLI facade và tầng lõi nghiệp vụ, đồng thời duy trì tính tương thích ngược hoàn toàn cho các cron daemon hiện hữu.

Về công tác vệ sinh nhãn trên GitHub, việc gỡ bỏ dứt điểm các nhãn `in-progress` và `ready-for-agent` khỏi 46 issues đã đóng là hành động cần thiết. Bảng điều phối Multi-Client hiện đã phản ánh đúng thực trạng công việc, ngăn chặn việc các AI Agent nhận diện nhầm tác vụ khả dụng.

Trước khi thực hiện merge PR #567 vào nhánh `main`, cần hoàn thiện 2 chốt chặn an toàn về bộ nhớ và định dạng header theo phân tích chi tiết dưới đây.

---

## Phân Tích & Phản Biện Chi Tiết Theo 4 Nhóm Câu Hỏi

### 1. Bảo Mật & Sanitization (`_build_multipart_document_body` và `_load_env_fallback`)

#### Khảo sát rủi ro Header Injection tại `Content-Disposition`
Trong hàm `_build_multipart_document_body`, tham số tên tệp được định dạng trực tiếp:
```python
f'Content-Disposition: form-data; name="document"; filename="{file_path.name}"'.encode()
```
- **Rủi ro cấu trúc:** Khi tên tệp chứa ký tự dấu nháy kép `"` (ví dụ: `ban_ve_"pccc"_final.pdf`), chuỗi tham số `filename` bị đóng sớm. Parser phía Telegram Bot API sẽ hiểu sai cấu trúc boundary hoặc trả về lỗi `400 Bad Request: can't parse multipart form-data`.
- **Rủi ro CRLF:** Khi tên tệp chứa ký tự `\r` hoặc `\n` (thường xuất phát từ hệ thống tệp bên thứ ba hoặc tên tự sinh từ crawler), các header giả mạo có thể bị chèn thêm vào luồng stream multipart.
- **Giải pháp áp dụng (`COND-01`):** Khử khuẩn tên tệp trước khi đóng gói bằng cách thay thế dấu nháy kép và các ký tự điều khiển dòng:
  ```python
  clean_filename = file_path.name.replace('"', '_').replace('\r', '').replace('\n', '').strip()
  ```

#### Đánh giá cơ chế Whitelist trong `_load_env_fallback`
Cơ chế nạp dự phòng trong `_load_env_fallback()` tại `commands/evals.py` đạt chuẩn an toàn:
- Whitelist cố định chỉ cho phép 2 khóa `("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")` giúp bảo vệ toàn bộ các biến môi trường nhạy cảm khác (`DATABASE_URL`, khóa API mô hình ngôn ngữ, token nội bộ).
- Điều kiện `key not in os.environ` đảm bảo biến môi trường đã được shell/CI thiết lập luôn giữ quyền ưu tiên cao nhất, ngăn chặn việc file `.env` ghi đè giá trị đang chạy.
- Thứ tự tìm kiếm từ `.env` hiện tại đến `CCBA_HUB_PATH/.env` và cuối cùng là `find_project_root()/.env` tuân thủ đúng nguyên tắc ưu tiên ngữ cảnh cục bộ trước, hạ tầng chia sẻ sau.

---

### 2. Hiệu Năng & Ràng Buộc Bộ Nhớ (`file_path.read_bytes()`)

#### Ràng buộc kích thước Telegram Bot API
Telegram quy định trần kích thước tệp gửi qua endpoint `/sendDocument` của tài khoản Bot tiêu chuẩn là **50 MB** ($52,428,800$ bytes).

#### Rủi ro cạn kiệt bộ nhớ (OOM)
Hàm `_build_multipart_document_body` hiện đọc toàn bộ tệp vào bộ nhớ thông qua `file_path.read_bytes()`. Khi người dùng hoặc agent gửi tệp nén bản vẽ CAD/BIM hoặc tệp PDF đồ họa lớn (vài trăm MB):
- Tiến trình Python phải phân bổ bộ nhớ cho nội dung tệp thô, tạo thêm bản sao byte array trong danh sách `chunks`, và duy trì payload hoàn chỉnh trong đối tượng `urllib.request.Request`.
- Mạng truyền tải toàn bộ dữ liệu lên máy chủ Telegram trước khi nhận mã lỗi từ chối, gây lãng phí băng thông và tài nguyên CPU.

#### Giải pháp bổ sung (`COND-02`)
Bổ sung hằng số và chốt chặn kiểm tra kích thước tệp vào `daemon.py`:
```python
MAX_TELEGRAM_DOC_BYTES: int = 50 * 1024 * 1024  # 50 MiB Telegram Bot API limit
```
Kiểm tra ngay tại đầu hàm `send_telegram_document()`:
```python
file_size = doc_path.stat().st_size
if file_size > MAX_TELEGRAM_DOC_BYTES:
    logger.warning(
        f"⚠️ File vượt quá giới hạn Telegram Bot API (50 MB): {file_size / (1024 * 1024):.2f} MB"
    )
    return False
```
Đồng thời, cập nhật trường `failure_modes` của Seam Card `telegram_notify.v1` trong `seam-contracts.yaml` thành:
```yaml
failure_modes: [token_unauthorized, network_timeout, file_not_found, file_too_large]
```

---

### 3. Vị Trí CLI: `ccba-harness notify` So Với `ccba-platform notify`

Quyết định đặt subcommand tại `ccba-harness notify` là chuẩn xác về mặt kiến trúc:

| Tiêu Chí Đánh Giá | `ccba-harness notify` (Đã chọn) | `ccba-platform notify` |
| :--- | :--- | :--- |
| **Phạm vi phân phối** | Có sẵn trong `.venv` của mọi Spoke thông qua editable package `ccba-harness` | Chỉ nằm ở thư mục gốc của Hub Monorepo (`scripts/ccba_platform_cli.py`) |
| **Tính độc lập Spoke** | Spoke thực thi trực tiếp qua môi trường ảo cục bộ, tuân thủ nguyên tắc Decoupling | Bắt buộc Spoke phải phụ thuộc đường dẫn tuyệt đối vào thư mục Hub |
| **Kích thước tệp** | Nằm trong module chuyên biệt `commands/evals.py` (< 800 dòng) | Tăng tải cho `ccba_platform_cli.py` (hiện đã chạm 1,296 dòng) |
| **Đăng ký Seam Contract** | Định tuyến trực tiếp tới biểu tượng `ccba_harness:send_telegram_document` | Chỉ đóng vai trò script bề mặt, khó lập hợp đồng năng lực |

Việc ánh xạ CLI vào `COMMANDS` của `ccba_harness.cli.core` giúp các kịch bản kiểm thử tự động, CI runner và Spoke workflow sử dụng chung một giao thức thống nhất.

---

### 4. Danh Mục Điều Kiện Hoàn Tất Trước Khi Merge

Để chuyển trạng thái sang `APPROVE` hoàn toàn, Antigravity cần thực hiện 3 điều chỉnh nhỏ sau:

1. **Khử khuẩn tên tệp (`COND-01`):** Làm sạch biến `file_path.name` trong `_build_multipart_document_body` để loại bỏ dấu nháy kép và các ký tự điều khiển dòng (`\r`, `\n`).
2. **Kiểm tra trần kích thước 50 MB (`COND-02`):** Khai báo hằng số `MAX_TELEGRAM_DOC_BYTES` và kiểm tra `doc_path.stat().st_size` trước khi thực hiện `read_bytes()`. Cập nhật `failure_modes` trong `seam-contracts.yaml`.
3. **Bổ sung kiểm thử biên (`COND-03`):** Thêm 2 test cases vào `scripts/tests/test_telegram_alert_emitter.py`:
   - Xác nhận hàm trả về `False` khi tệp vượt quá 50 MB (sử dụng mock kích thước tệp).
   - Xác nhận tên tệp chứa ký tự `"` hoặc `\n` được mã hóa an toàn trong header `Content-Disposition`.
