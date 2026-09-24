"""conftest.py - Pytest Pre-Execution Enforcement Hook cho CCBA Agent Platform.

Cưỡng chế thực thi test scoped (chỉ định file test cụ thể) để tránh bùng nổ
context và gây ra lỗi ngắt phiên "User cancelled agent execution".
"""

import sys
from pathlib import Path
from typing import Any

import pytest


def pytest_addoption(parser: Any) -> None:
    """Đăng ký tùy chọn cho phép chạy unscoped khi thực sự cần thiết (ví dụ: CI)."""
    parser.addoption(
        "--allow-unscoped",
        action="store_true",
        default=False,
        help="Cho phép chạy pytest unscoped trên toàn bộ workspace.",
    )


def pytest_cmdline_main(config: Any) -> int | None:
    """Hook kiểm tra các tham số đầu vào trước khi tiến hành chạy pytest."""
    import os

    if (
        config.getoption("--allow-unscoped", default=False)
        or os.getenv("CI") == "true"
        or os.getenv("GITHUB_ACTIONS") == "true"
    ):
        return None

    project_root = Path(config.rootpath).resolve()
    raw_args = list(getattr(config.invocation_params, "args", []))

    # Tách các positional args (không bắt đầu bằng '-')
    positional_args = [a for a in raw_args if not a.startswith("-")]

    is_unscoped = False
    if not positional_args:
        is_unscoped = True
    elif len(positional_args) == 1:
        try:
            arg_path = Path(positional_args[0]).resolve()
            if arg_path == project_root or positional_args[0] in (".", "./", ".\\"):
                is_unscoped = True
        except Exception:
            pass

    if is_unscoped:
        sys.stderr.write("\n" + "=" * 65 + "\n")
        sys.stderr.write("❌ [CCBA Guardrail Error] Lệnh 'pytest' unscoped đã bị chặn tự động!\n")
        sys.stderr.write("=" * 65 + "\n")
        sys.stderr.write(
            "Lý do: Chạy pytest trên toàn repo gây bùng nổ context budget và làm ngắt phiên.\n\n"
        )
        sys.stderr.write("💡 Hướng dẫn thực thi an toàn:\n")
        sys.stderr.write("  1. Chỉ định file test cụ thể:\n")
        sys.stderr.write("     pytest <path/to/test_file.py>\n")
        sys.stderr.write("  2. Hoặc sử dụng CLI Wrapper tự động:\n")
        sys.stderr.write("     python scripts/safe_pytest.py -f <path/to/test_file.py>\n")
        sys.stderr.write("  3. Để chạy toàn bộ test suite (chỉ ở bước nghiệm thu cuối):\n")
        sys.stderr.write("     pytest --allow-unscoped\n")
        sys.stderr.write("=" * 65 + "\n\n")
        return 1

    return None


@pytest.fixture(autouse=True)
def isolate_ccba_hub_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cô lập biến môi trường Hub máy trạm khỏi toàn bộ test suites (RULE-2.9)."""
    monkeypatch.delenv("CCBA_HUB_PATH", raising=False)
    monkeypatch.delenv("HUB_PATH", raising=False)
