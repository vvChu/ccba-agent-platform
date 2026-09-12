---
name: ccba-append-only-logger
description: Thread-safe, append-only logging pattern cho Python pipeline multi-daemon.
  Tránh race condition và encoding corruption khi nhiều process ghi cùng lúc vào shared
  log file.
applies_to:
- Phần mềm
- Kiểm định
bundle: _core
tier: kernel
command: /ccba-append-only-logger
metadata:
  version: "1.1.0"
  author: "CCBA Hub"
dependencies:
- ccba-ai-gateway-sdk
gpi:
  s: 2.0
  k: 3.0
  a: 4.0
  p: 1.0
triggers:
- logging
- logger
- log file
- thread safe
- daemon log
- pipeline log
- append log
---
# Append-Only Logger

Thread-safe logging pattern cho các pipeline chạy nhiều daemon/process đồng thời. Thay thế pattern **read → regex → rewrite** (dễ corrupt) bằng **pure append** với thread lock.

> **Nguồn**: VvC LLM OS v2.0 Logger (2026) — giải quyết 3 lỗi thực tế: mojibake tiếng Việt dưới `pythonw.exe`, race condition khi 2 daemon ghi đồng thời, và mất 70% pipeline events do cấu trúc log cũ.

---

## Kiến trúc & Triển khai

Mã nguồn triển khai chi tiết của lớp logger thread-safe được tách biệt hoàn toàn ra tệp tin mô-đun:
👉 **Mã nguồn:** [append_only_logger.py](resources/append_only_logger.py)

Kỹ sư hoặc Agent tại dự án Spoke có thể dễ dàng import và sử dụng trực tiếp:
```python
from resources.append_only_logger import update_log, rotate_log
```

---

## Anti-Pattern cần tránh

```python
# ❌ SAI LẦM — read → regex → rewrite: dễ corrupt, encoding bug, race condition
with open("log.md", "r", encoding="utf-8") as f:
    content = f.read()
content = re.sub(r"old_entry", new_entry, content)
with open("log.md", "w", encoding="utf-8") as f:
    f.write(content)
```

**Vấn đề thực tế**:
* Tiếng Việt thành mojibake khi `pythonw.exe` chạy headless (không có terminal encoding).
* Daemon A đọc file → Daemon B ghi đè → Daemon A ghi đè lại → mất log của Daemon B.
* Tốc độ ghi chậm hơn 10-50x so với pure append trên file lớn.

---

## Quy ước Event Category

Dùng categories nhất quán để dễ grep/filter:

| Category | Ý nghĩa | Ví dụ |
|---|---|---|
| `lifecycle` | Khởi động/dừng daemon | `Daemon v2.0 started` |
| `ingest` | Trạng thái nạp & xử lý file | `Created: concept_xyz (from image.jpg)` |
| `error` | Lỗi nghiêm trọng, Exception | `Vision API returned empty` |
| `warn` | Cảnh báo không nghiêm trọng | `Garbled output detected, retrying` |
| `skip` | Bỏ qua dữ liệu đầu vào | `OCR text too short (12 chars)` |
| `timeout` | Quá thời gian xử lý | `Stage 3 timed out after 120s` |

```python
# Ví dụ gọi ghi log
update_log("lifecycle", "Daemon v2.0 started — watching: /input/folder")
update_log("ingest", f"Created: {concept_name} (from {source_file})")
update_log("error", f"Vision API empty for {image_name}", level="error")
update_log("skip", f"OCR too short ({len(text)} chars): {image_name}", level="warn")
```

---

## Tự động kiểm soát và sửa lỗi (Self-Healing)

Khi quá trình ghi log hoặc rotate log gặp lỗi (như lock file do tiến trình ngoài, đầy bộ nhớ), logger không gây crash ứng dụng mà tự động xuất ra luồng `stderr` phản hồi lỗi JSON chuẩn:
```json
{
  "status": "error",
  "error_code": "LOGGER_WRITE_FAIL",
  "message": "Failed to write log entry to log.md: [Errno 13] Permission denied: 'log.md'",
  "recovery_suggestion": "Check if log file 'log.md' is read-only, locked by another process, or disk is full."
}
```
Giúp các Agent tự động khắc phục bằng cách thử ghi vào file backup, hoặc thông báo cảnh báo rõ ràng cho kỹ sư.

---

## Tương thích PowerShell

Khi script chạy trực tiếp từ PowerShell terminal (không phải headless daemon), Python `logging` mặc định ghi vào `stderr` khiến PowerShell trả exit code 1.
Để sửa lỗi này, cấu hình ghi ra `stdout`:
```python
import sys
import logging

sys.stdout.reconfigure(encoding='utf-8')  # Gọi TRƯỚC basicConfig
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,  # Key: ghi ra stdout
    format="%(asctime)s [%(levelname)s] %(message)s"
)
```
