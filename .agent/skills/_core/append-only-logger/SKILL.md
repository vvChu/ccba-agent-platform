---
name: Append-Only Logger
description: Thread-safe, append-only logging pattern cho Python pipeline multi-daemon. Tránh race condition và encoding corruption khi nhiều process ghi cùng lúc vào shared log file.
applies_to:
  - "Phần mềm"
  - "Kiểm định"
bundle: "_core"
---

# Append-Only Logger

Thread-safe logging pattern cho các pipeline chạy nhiều daemon/process đồng thời. Thay thế pattern **read → regex → rewrite** (dễ corrupt) bằng **pure append** với thread lock.

> **Nguồn**: VvC LLM OS v2.0 Logger (2026) — giải quyết 3 lỗi thực tế: mojibake tiếng Việt dưới `pythonw.exe`, race condition khi 2 daemon ghi đồng thời, và mất 70% pipeline events do coverage thấp.

---

## Anti-Pattern cần tránh

```python
# ❌ SAIÔ — read → regex → rewrite: dễ corrupt, encoding bug, race condition
with open("log.md", "r", encoding="utf-8") as f:
    content = f.read()
content = re.sub(r"old_entry", new_entry, content)
with open("log.md", "w", encoding="utf-8") as f:
    f.write(content)
```

**Vấn đề thực tế**:
- Vietnamese text thành mojibake khi `pythonw.exe` chạy headless (không có terminal encoding)
- Daemon A đọc file → Daemon B ghi đè → Daemon A ghi đè lại → mất log của B
- Chậm hơn 10-50x so với pure append trên file lớn

---

## Implementation

```python
import threading
import logging
from datetime import datetime
from pathlib import Path

# === Shared state ===
_log_lock = threading.Lock()
LOG_FILE = Path("log.md")

def update_log(
    category: str,
    message: str,
    level: str = "info"
) -> None:
    """Append một log entry vào shared log file — thread-safe.

    Args:
        category: Nhóm event (lifecycle, ingest, error, warn, ...).
        message:  Nội dung log.
        level:    Severity: info | warn | error.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"- `{timestamp}` **[{category}]** {message}\n"

    with _log_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
```

---

## Log Rotation

Tránh log file phình to vô tận — archive entries cũ theo `max_age_days`.

```python
from datetime import datetime, timedelta
import shutil

def rotate_log(max_age_days: int = 30) -> None:
    """Archive log entries cũ hơn max_age_days vào log_archive_YYYY-MM.md.

    Chạy một lần mỗi tuần (VD: trong weekly sleep daemon).
    """
    if not LOG_FILE.exists():
        return

    cutoff = datetime.now() - timedelta(days=max_age_days)
    archive_name = f"log_archive_{cutoff.strftime('%Y-%m')}.md"
    archive_path = LOG_FILE.parent / archive_name

    with _log_lock:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        recent, old = [], []
        for line in lines:
            # Parse timestamp từ format: - `2026-05-01 10:30:00` **[...]** ...
            match = re.search(r"`(\d{4}-\d{2}-\d{2})", line)
            if match:
                entry_date = datetime.strptime(match.group(1), "%Y-%m-%d")
                (recent if entry_date >= cutoff else old).append(line)
            else:
                recent.append(line)  # Giữ lại nếu không parse được

        # Ghi lại file chỉ với entries mới
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(recent)

        # Append entries cũ vào archive
        if old:
            with open(archive_path, "a", encoding="utf-8") as f:
                f.writelines(old)
```

---

## Event Category Convention

Dùng categories nhất quán để dễ grep/filter:

| Category | Ý nghĩa | Ví dụ |
|---|---|---|
| `lifecycle` | Daemon start/stop | `Daemon v2.0 started` |
| `ingest` | Processing start + completion | `Created: concept_xyz (from image.jpg)` |
| `error` | Failures, exceptions | `Vision API returned empty` |
| `warn` | Non-fatal warnings | `Garbled output detected, retrying` |
| `skip` | Input bị bỏ qua | `OCR text too short (12 chars)` |
| `timeout` | Processing timeout | `Stage 3 timed out after 120s` |

```python
# Usage examples
update_log("lifecycle", "Daemon v2.0 started — watching: /input/folder")
update_log("ingest", f"Created: {concept_name} (from {source_file})")
update_log("error", f"Vision API empty for {image_name}", level="error")
update_log("skip", f"OCR too short ({len(text)} chars): {image_name}", level="warn")
```

---

## PowerShell Compatibility

Khi script chạy từ PowerShell terminal (không phải headless daemon), Python `logging` mặc định ghi vào `stderr` → PowerShell trả exit code 1 dù không có lỗi.

```python
import sys
import logging

# Bắt buộc khi script có __main__ block chạy từ PowerShell
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,  # ← key: stdout thay vì stderr
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Nếu script in ký tự tiếng Việt
sys.stdout.reconfigure(encoding='utf-8')  # gọi TRƯỚC basicConfig
```

**Rule**: Daemon dùng `pythonw.exe` (headless) không cần — chỉ áp dụng cho scripts chạy manual từ terminal.

---

## Tích hợp vào CCBA Pipeline

```python
# Ví dụ tích hợp trong QC batch orchestrator
def process_drawing(drawing_path: Path) -> None:
    update_log("ingest", f"Processing started: {drawing_path.name}")
    try:
        result = run_audit(drawing_path)
        update_log("ingest", f"Audit completed: {drawing_path.name} — {len(result.issues)} issues")
    except TimeoutError:
        update_log("timeout", f"Audit timed out: {drawing_path.name}", level="warn")
    except Exception as e:
        update_log("error", f"Audit failed: {drawing_path.name} — {e}", level="error")
```

---

## Reference Implementation

```
D:\VvC_Notes\scripts\core\log.py  →  update_log() + rotate_log()
```
