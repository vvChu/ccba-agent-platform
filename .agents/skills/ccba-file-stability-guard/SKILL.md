---
name: ccba-file-stability-guard
description: Phát hiện file đã sync hoàn toàn trước khi xử lý. Kiểm tra kích thước
  thực tế thay vì time.sleep() — dành cho Google Drive, OneDrive, SharePoint.
applies_to:
- Phần mềm
- Kiểm định
bundle: _core
gpi:
  s: 2.0
  k: 3.0
  a: 4.0
  p: 1.0
triggers:
- file stability
- cloud sync
- watchdog
- race condition
- google drive sync
- onedrive sync
- file incomplete
---
# File Stability Guard

Pattern phát hiện **file đã sync xong** trước khi pipeline xử lý. Giải quyết triệt để lớp lỗi **Cloud Sync Race Condition** mà `time.sleep()` không thể giải quyết.

> [!IMPORTANT]
> Áp dụng bất kỳ pipeline nào xử lý file đến từ: Google Drive Desktop, OneDrive, SharePoint Sync, hay bất kỳ cloud junction nào. **Bắt buộc** khi có `watchdog` / `FileSystemWatcher`.

---

## Vấn đề: Cloud Sync Race Condition

```
[User upload file từ điện thoại]
         ↓
  Google Drive Cloud
         ↓
  Google Drive Desktop (PC)  ← Đang sync dần dần
         ↓
  Directory Junction / Symlink
         ↓
  Watchdog phát hiện file xuất hiện  ← ⚠️ FILE CHƯA HOÀN CHỈNH
         ↓
  Pipeline đọc file → OCR/parse file dang dở
         ↓
  ❌ Empty output / corrupt content / silent failure
```

**Anti-pattern phổ biến**: `time.sleep(2)` — hardcode 2 giây mà không biết file cần bao lâu để sync.

---

## Giải pháp: `is_file_stable()`

```python
import time
from pathlib import Path

def is_file_stable(
    path: Path,
    check_interval: float = 1.5,
    max_retries: int = 20
) -> bool:
    """Xác nhận file đã sync xong bằng cách so sánh kích thước.

    Args:
        path: Đường dẫn tới file cần kiểm tra.
        check_interval: Khoảng cách giữa hai lần check (giây). Default: 1.5s.
        max_retries: Số lần check tối đa. Default: 20 (= 30 giây timeout).

    Returns:
        True nếu kích thước ổn định (file sync xong).
        False nếu vẫn đang thay đổi sau max_retries lần check.
    """
    prev_size = -1
    for _ in range(max_retries):
        try:
            current_size = path.stat().st_size
        except FileNotFoundError:
            return False  # File bị xóa trong lúc chờ

        if current_size == prev_size and current_size > 0:
            return True  # Kích thước ổn định, file đã sync xong

        prev_size = current_size
        time.sleep(check_interval)

    return False  # Vẫn đang thay đổi sau timeout
```

---

## Tích hợp vào Watchdog Pipeline

```python
from watchdog.events import FileSystemEventHandler

class PipelineHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)

        # ✅ Gate: chờ file ổn định trước khi xử lý
        if not is_file_stable(path):
            logger.warning(f"File không ổn định sau timeout, bỏ qua: {path.name}")
            return

        # Safe: file đã sync xong hoàn toàn
        process_file(path)
```

---

## Tham số Tham Khảo

| Tình huống | `check_interval` | `max_retries` | Tổng timeout |
|---|---|---|---|
| File nhỏ (< 5MB, ảnh điện thoại) | 1.5s | 20 | 30 giây |
| File lớn (PDF, ZIP) | 3.0s | 20 | 60 giây |
| LAN nhanh | 0.5s | 10 | 5 giây |
| Mobile upload qua 4G | 2.0s | 30 | 60 giây |

---

## Tại sao không dùng `time.sleep()`?

| Tiêu chí | `time.sleep(N)` | `is_file_stable()` |
|---|---|---|
| Correctness | ❌ Giá trị N tùy tiện, không phản ánh thực tế | ✅ Dựa trên trạng thái thực |
| Performance | ❌ Luôn chờ N giây dù file đã xong | ✅ Return ngay khi ổn định |
| Large files | ❌ N có thể chưa đủ → vẫn đọc file dở | ✅ Chờ bất kể file to cỡ nào |
| Reliability | ❌ Fail silently, khó debug | ✅ Log rõ ràng, return False khi timeout |

---

## Ứng dụng trong CCBA Hub

| Service | Rủi ro race condition |
|---|---|
| `ccba-ai-pdf-preprocessor` | PDF lớn upload từ SharePoint / email attachment |
| `ccba-ai-qc-batch-orchestrator` | Nhiều bản vẽ sync cùng lúc từ cloud storage |
| Bất kỳ service nào có `watchdog` | Mặc định nên áp dụng pattern này |

---

## Reference Implementation

Full production code (bao gồm logging, threading, retry backoff):

```
D:\VvC_Notes\scripts\daemon.py  →  hàm _is_file_stable()
```

Đây là implementation đã vận hành ổn định 6+ tháng với Google Drive Desktop Junction trên Windows 11.
