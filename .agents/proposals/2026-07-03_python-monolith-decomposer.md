---
proposal_id: "2026-07-03_python-monolith-decomposer"
type: "skill"
name: "python-monolith-decomposer"
status: "open"
priority: "Trung bình"
proposed_by_project: "ccba-legal-intel"
proposed_date: "2026-07-03"
applies_to:
  - "Phần mềm"
---

## Mô tả

Checklist + quy trình 6 bước tách file Python monolithic (1000+ dòng) thành package sub-modules với **backward compatibility hoàn toàn**: không cần thay đổi bất kỳ caller nào trong bước đầu, test suite xanh sau mỗi bước.

Đúc rút trực tiếp từ việc refactor `ccba_legal/harness/__init__.py` (3172 dòng) thành 5 sub-modules — commit `74b2b1a` trên `ccba-legal-intel`.

---

## Vấn đề giải quyết

Khi một Python file phát triển quá lớn (1000+ dòng), việc tách thành sub-modules thường gây **3 loại regression ẩn**:

1. **Silent stdlib import loss**: Stdlib imports (`ast`, `base64`, `glob`, `fnmatch`) ở cấp module không được tự động copy khi extract code. Hậu quả: `NameError` bị catch silently bởi `except Exception` → logic bảo mật/xử lý bị bypass hoàn toàn, không có error message nào.

2. **Mock patch path drift**: Sau khi tách, `@patch("mymodule.SomeClass")` phải đổi thành `@patch("mymodule._submodule.SomeClass")`. Nếu bỏ sót, tests vẫn xanh nhưng mock không có tác dụng → false confidence.

3. **Circular import with TYPE_CHECKING**: Sub-module A import type từ B, B import logic từ A → circular import. Giải pháp: `TYPE_CHECKING` guard kết hợp `from __future__ import annotations`.

---

## Giải pháp / Cấu trúc đề xuất

### Quy trình 6 bước Incremental Backward-Compat Migration

```
Bước 1: Tạo sub-module đầu tiên (state/config)
  → Copy code + TẤT CẢ stdlib imports liên quan
  → Thêm re-export trong __init__.py
  → pytest → xanh

Bước 2-5: Lặp lại cho từng nhóm chức năng
  → Mỗi bước: tạo sub-module → re-export → pytest
  → Chạy `ruff check` ngay sau mỗi bước (phát hiện F821 = missing import)

Bước 6: Cleanup
  → Xóa unused imports khỏi __init__.py
  → Giữ lại các module cần thiết cho mock patch (e.g., subprocess)
  → Thêm TYPE_CHECKING cho forward references
  → `ruff check --fix` → pytest → commit
```

### Checklist Trap phổ biến

| Trap | Triệu chứng | Fix |
|------|-------------|-----|
| Missing stdlib import | F821 `Undefined name 'ast'`; hoặc silent `NameError` bị catch | Copy tất cả imports từ source file |
| Mock path drift | Test xanh nhưng mock không chặn được call thực | Grep `@patch("old.path")` sau mỗi bước |
| F401 re-export false positive | `__init__.py` bị flag F401 cho intentional exports | `# ruff: noqa: F401` ở top file |
| Circular import | `ImportError: cannot import name 'X'` | `TYPE_CHECKING` guard |
| `subprocess` singleton | Test mock `ccba_legal.harness.subprocess.run` fail | Giữ lại `import subprocess` trong `__init__.py` |

### Security Note

Khi extract security-critical code, bắt buộc verify ngay bằng ruff: `ruff check --select F821 path/to/new_module.py`. F821 là dấu hiệu sớm nhất của silent security bypass do missing import.

---

## Nội dung mẫu / Code mẫu

### Cấu trúc __init__.py sau khi tách

```python
"""Package re-export surface.

All implementation lives in private sub-modules:
  _state.py      — shared state
  _monitor.py    — core logic
  _guard.py      — public API class
"""
# ruff: noqa: F401  ← intentional backward-compat re-exports
from __future__ import annotations

# NOTE: keep subprocess for test mock targets
import subprocess  # noqa: F401

from mypkg._state import _some_state, _some_cache
from mypkg._monitor import _check_something, _scan_something
from mypkg._guard import MyGuard

__all__ = ["MyGuard"]
```

### TYPE_CHECKING cho forward reference

```python
# In _monitor.py (which _guard.py imports)
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypkg._guard import MyGuard  # only for type checkers, never at runtime

def _check(guard: MyGuard, path: str) -> bool:  # annotation safe with PEP 563
    ...
```

---

## Nguồn tham chiếu

- Commit: `74b2b1a` — `refactor(harness): decompose monolithic harness.py into 5 sub-modules`
- Package: `ccba-legal-intel` / `ccba_legal/harness/`
- Session: `cc28b55d-1b52-4833-b55d-05b3fb9bfc8e` — 2026-07-03
- Learnings: `.md/knowledge/session_learnings.md` (mục Refactor: ccba_legal/harness)
