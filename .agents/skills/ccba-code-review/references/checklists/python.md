# Python Monorepo Stack Review Checklist

Universal checklist for Python monorepo repositories (`pyproject.toml`). Two-pass model: critical (blocking) + informational (non-blocking).

## Instructions

Review `git diff` for Python changes (`.py`). Be specific — cite `file:line` and suggest fixes. Skip anything that's fine. Only flag real problems.

---

## Pass 1 — CRITICAL (blocking)

### 1. Seam Boundaries & Private Submodules (ADR-0035)
- **Private Module Bypass:** Nghiêm cấm bypass import trực tiếp vào các module private nội bộ (`_internal.py`, `_*.py`, hoặc private subpackages) từ bên ngoài package boundary.
- **Package Interface:** Mọi truy cập cross-package phải đi qua public interface được xuất bản tại `__init__.py` (thông qua `__all__`).
- **Foundation Purity:** Các foundation leaf packages không được import ngược từ domain/application packages cấp cao hơn.

### 2. Type Hints & Type Safety
- **Full Type Annotations:** Toàn bộ hàm, method mới hoặc sửa đổi phải có type hints đầy đủ cho tất cả tham số và kiểu trả về (đạt chuẩn `mypy strict`).
- **Forbidden Overrides:** Cấm sử dụng `type: ignore` không có lý do kỹ thuật cụ thể hoặc cấu hình `ignore_errors = true` trong `pyproject.toml` hay file headers.

### 3. Windows File Encoding & Subprocess (RULE-2.5)
- **Explicit UTF-8 File I/O:** Mọi hàm đọc/ghi tệp (`open()`, `Path.read_text()`, `Path.write_text()`) bắt buộc phải khai báo tường minh `encoding="utf-8"`.
- **Safe Subprocess Output:** Mọi lệnh `subprocess.run(...)`, `subprocess.Popen(...)`, hoặc `subprocess.check_output(...)` khi kích hoạt `text=True` hoặc `capture_output=True` bắt buộc phải kèm `encoding="utf-8"` để chống vỡ encoding (cp1252/cp936) trên Windows.

### 4. Code Quality & KISS Standards
- **Function Length Limit:** Hàm/method không được vượt quá 50 dòng; nếu dài hơn phải refactor tách thành các helper sub-functions chuyên biệt.
- **Composition Over Inheritance:** Ưu tiên composition over inheritance; tránh phân cấp kế thừa sâu quá 2 tầng.
- **No Bare Except:** Tuyệt đối cấm sử dụng bare `except:`; luôn bắt cụ thể exception type (e.g. `except (KeyError, ValueError):`).

---

## Pass 2 — INFORMATIONAL (non-blocking)

### Modern Python Idioms & Clean Code
- Sử dụng f-strings thay vì `.format()` hoặc `%`.
- Khai báo kiểu hiện đại với `from __future__ import annotations` (e.g. `list[str]`, `dict[str, Any]`, `str | None`).
- Public functions, classes, và modules phải có docstrings theo chuẩn Google style.
- Quản lý tài nguyên, file streams, locks bằng context managers (`with` statement).
- Sắp xếp import theo thứ tự chuẩn PEP 8 (standard library $\rightarrow$ third-party $\rightarrow$ local monorepo packages).
