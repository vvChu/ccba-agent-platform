import re
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path

from ccba_ai import CCBAErrorCode, format_error_json

# Thread lock dùng chung để đồng bộ ghi log giữa các threads
_log_lock = threading.Lock()
DEFAULT_LOG_FILE = Path("log.md")


def update_log(
    category: str, message: str, level: str = "info", log_file: Path = DEFAULT_LOG_FILE
) -> None:
    """Append một log entry vào shared log file — thread-safe.
    Tích hợp tự động in JSON lỗi chuẩn hóa nếu ghi log thất bại.

    Args:
        category: Nhóm event (lifecycle, ingest, error, warn, skip, timeout).
        message:  Nội dung thông điệp log.
        level:    Mức độ lỗi: info | warn | error.
        log_file: Đường dẫn tệp tin log.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"- `{timestamp}` **[{category}]** {message}\n"

    try:
        with _log_lock:
            # Đảm bảo thư mục cha tồn tại
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(entry)
    except Exception as e:
        # In phản hồi lỗi JSON chuẩn hóa ra stderr
        error_json = format_error_json(
            CCBAErrorCode.LOGGER_WRITE_FAIL,
            f"Failed to write log entry to {log_file.name}: {str(e)}",
            f"Check if log file '{log_file.name}' is read-only, locked by another process, or disk is full.",
        )
        print(error_json, file=sys.stderr)


def rotate_log(log_file: Path = DEFAULT_LOG_FILE, max_age_days: int = 30) -> None:
    """Archive log entries cũ hơn max_age_days vào log_archive_YYYY-MM.md.
    Tích hợp tự động in JSON lỗi chuẩn hóa nếu rotate thất bại.

    Args:
        log_file: Đường dẫn tệp tin log chính.
        max_age_days: Số ngày giữ lại log gần nhất.
    """
    if not log_file.exists():
        return

    try:
        cutoff = datetime.now() - timedelta(days=max_age_days)
        archive_name = f"log_archive_{cutoff.strftime('%Y-%m')}.md"
        archive_path = log_file.parent / archive_name

        with _log_lock:
            with open(log_file, encoding="utf-8") as f:
                lines = f.readlines()

            recent, old = [], []
            for line in lines:
                # Parse timestamp dạng: - `2026-05-01 10:30:00`
                match = re.search(r"`(\d{4}-\d{2}-\d{2})", line)
                if match:
                    entry_date = datetime.strptime(match.group(1), "%Y-%m-%d")
                    if entry_date >= cutoff:
                        recent.append(line)
                    else:
                        old.append(line)
                else:
                    recent.append(line)  # Giữ lại nếu không parse được

            # Ghi lại log file chính với các entries gần đây
            with open(log_file, "w", encoding="utf-8") as f:
                f.writelines(recent)

            # Ghi các entries cũ vào tệp archive
            if old:
                with open(archive_path, "a", encoding="utf-8") as f:
                    f.writelines(old)
    except Exception as e:
        error_json = format_error_json(
            CCBAErrorCode.LOGGER_WRITE_FAIL,
            f"Failed to rotate log file {log_file.name}: {str(e)}",
            "Verify write permissions for both main log and archive log files. Check disk space.",
        )
        print(error_json, file=sys.stderr)
