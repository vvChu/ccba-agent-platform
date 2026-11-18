"""conftest.py - Pytest Pre-Execution Enforcement Hook cho CCBA Agent Platform.

Cưỡng chế thực thi test scoped (chỉ định file test cụ thể) để tránh bùng nổ
context và gây ra lỗi ngắt phiên "User cancelled agent execution".
"""

import os
import sys
from pathlib import Path
from typing import Any

import pytest

_INFO_FLAGS: frozenset[str] = frozenset(
    {"--version", "-V", "--help", "-h", "--fixtures", "--markers"}
)
_TRUTHY_VALUES: frozenset[str] = frozenset({"true", "1", "yes"})


def pytest_addoption(parser: Any) -> None:
    """Đăng ký tùy chọn cho phép chạy unscoped khi thực sự cần thiết (ví dụ: CI)."""
    parser.addoption(
        "--allow-unscoped",
        action="store_true",
        default=False,
        help="Cho phép chạy pytest unscoped trên toàn bộ workspace.",
    )


def _is_truthy_ci_env() -> bool:
    """Return True when CI or GITHUB_ACTIONS indicates a non-interactive CI environment."""
    ci_val = os.getenv("CI", "").strip().lower()
    gh_val = os.getenv("GITHUB_ACTIONS", "").strip().lower()
    return ci_val in _TRUTHY_VALUES or gh_val in _TRUTHY_VALUES


def _resolve_positional_targets(config: Any, raw_args: list[str]) -> list[str]:
    """Resolve positional test targets from pytest's parsed file_or_dir, with mock fallback."""
    known_ns = getattr(config, "known_args_namespace", None)
    ns_targets = getattr(known_ns, "file_or_dir", None)
    if ns_targets is not None:
        return [str(p) for p in ns_targets]
    return [a for a in raw_args if not a.startswith("-")]


def _print_unscoped_pytest_error(project_root: Path) -> None:
    """Emit bilingual unscoped-pytest blocking guidance referencing hub/spoke safe_pytest path."""
    safe_pytest_rel = (
        "scripts/_guardrails/safe_pytest.py"
        if (project_root / "scripts" / "_guardrails" / "safe_pytest.py").is_file()
        else "scripts/safe_pytest.py"
    )
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
    sys.stderr.write(f"     python {safe_pytest_rel} -f <path/to/test_file.py>\n")
    sys.stderr.write("  3. Để chạy toàn bộ test suite (chỉ ở bước nghiệm thu cuối):\n")
    sys.stderr.write("     pytest --allow-unscoped\n")
    sys.stderr.write("=" * 65 + "\n\n")


def pytest_cmdline_main(config: Any) -> int | None:
    """Hook kiểm tra các tham số đầu vào trước khi tiến hành chạy pytest."""
    raw_args = [str(a) for a in getattr(config.invocation_params, "args", [])]
    if any(a in _INFO_FLAGS for a in raw_args):
        return None
    if config.getoption("--allow-unscoped", default=False) or _is_truthy_ci_env():
        return None
    if os.environ.get("PYTEST_XDIST_WORKER", "").strip():
        return None

    project_root = Path(config.rootpath).resolve()
    positional_args = _resolve_positional_targets(config, raw_args)

    is_unscoped = not positional_args
    if len(positional_args) == 1:
        target = positional_args[0]
        try:
            if Path(target).resolve() == project_root or target in (".", "./", ".\\"):
                is_unscoped = True
        except (OSError, ValueError):
            pass

    if is_unscoped:
        _print_unscoped_pytest_error(project_root)
        return 1
    return None


@pytest.fixture(autouse=True)
def isolate_ccba_hub_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cô lập biến môi trường Hub máy trạm khỏi toàn bộ test suites (RULE-2.9)."""
    monkeypatch.delenv("CCBA_HUB_PATH", raising=False)
    monkeypatch.delenv("HUB_PATH", raising=False)
