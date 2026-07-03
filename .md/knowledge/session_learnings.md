## Session Learnings - Kiến thức tích lũy phiên làm việc CCBA Legal Intel

## Cập nhật gần nhất: 2026-07-02

---

## Patterns (Mẫu tốt)

### 1. Đồng bộ và Tự động cập nhật RAG thời gian thực (Real-time Cloud RAG Sync)

- **Ngữ cảnh**: Khi nạp tài liệu từ Google Drive sang Google NotebookLM.
- **Vấn đề giải quyết**: Tránh việc phải tải lên/tải xuống và chạy lại script đồng bộ mỗi khi nội dung văn bản gốc thay đổi.
- **Giải pháp**: 
  1. Upload tệp Word `.docx` lên Drive dưới dạng **Google Docs trực tuyến** bằng cách chỉ định metadata `mimeType="application/vnd.google-apps.document"` khi gọi API Drive.
  2. Kéo file Google Doc này sang NotebookLM. Do NotebookLM liên kết trực tiếp với Drive Doc, mọi chỉnh sửa của người dùng trên Drive sẽ tự động đồng bộ sang ngữ cảnh RAG Cloud theo thời gian thực mà không cần chạy lại script.

### 2. Tháo gỡ lỗi phân quyền NotebookLM Drive API (Auto-Share Link View)

- **Ngữ cảnh**: Khi NotebookLM API trả về lỗi màu hồng `API returned no data for Drive source` đối với tệp tin vừa upload lên Drive.
- **Vấn đề giải quyết**: Giới hạn bảo mật của Google ngăn cản NotebookLM đọc dữ liệu từ tệp Drive cá nhân qua token API.
- **Giải pháp**: Sử dụng API Drive `permissions().create()` để thiết lập quyền đọc công khai có liên kết (`anyone/reader`) cho file Google Doc/PDF trên Drive trước khi kéo sang NotebookLM.

---

## Anti-patterns (Cách tránh)

### 1. Trích xuất Cookie tự động qua CDP cho các dịch vụ bảo mật cao của Google

- **Vấn đề**: Kể từ Google Chrome 127+, cơ chế mã hóa **App-Bound Encryption** trên Windows khóa chặt cookie của Chrome và chặn các tiến trình bên ngoài giải mã, dẫn đến việc lấy cookie qua CDP bị thiếu các mã bảo mật bắt buộc (`SID`, `__Secure-1PSIDTS`) khiến RAG bị từ chối truy cập.
- **Thay thế bằng**: Sử dụng CLI đăng nhập chính thống của thư viện `python -m notebooklm login` để kích hoạt phiên Chromium chuẩn hóa và lưu trữ `storage_state.json`.

---

## Solutions (Giải pháp tham chiếu)

### 1. Lỗi thiếu tham số bắt buộc trong API `add_drive` của `notebooklm-py`

- **Vấn đề**: Gọi `client.sources.add_drive(notebook_id, file_id)` báo lỗi: `missing 1 required positional argument: 'title'`.
- **Giải pháp**: Bổ sung tham số `title` (tên hiển thị nguồn trên Cloud) làm tham số bắt buộc:
  ```python
  source = await client.sources.add_drive(
      notebook_id=notebook_id,
      file_id=drive_file_id,
      title=file_name_stem,
      wait=True
  )
  ```
- **Liên kết**: [.md/scratch/sync_processed_docs.py](file:///d:/GitHubProjects/ccba-agent-platform/.md/scratch/sync_processed_docs.py)

---

## Configurations (Cấu hình tối ưu)

| Setting | Value | Lý do | Áp dụng khi |
| --------- | ------- | ------- | ------------- |
| AI_MODEL | gemini-3.1-flash-lite | Phản hồi đầy đủ không bị đứt đoạn, tốc độ nhanh, tối ưu token | Chạy AI Gateway đối soát pháp lý |

---
---

## Refactor: `ccba_legal/harness` (2026-07-03)

### Kiến trúc `harness/` package sau khi tách

| Sub-module | Dòng | Trách nhiệm |
|---|---|---|
| `_state.py` | ~150 | Shared mutable state (counters, caches, originals) |
| `_sql_monitor.py` | ~280 | SQLite connection/query interception |
| `_file_monitor.py` | ~1150 | File-open hooks, AST scanning, inode tracking |
| `_process_monitor.py` | ~1230 | Subprocess & OS-call monitoring |
| `_guard.py` | ~550 | `HarnessGuard` class + global hook management |
| `__init__.py` | ~138 | Thin re-export wrapper (`# ruff: noqa: F401`) |

### Patterns

**1. Import stdlib phải copy thủ công khi extract code ra file mới**
- **Vấn đề**: Khi cut-paste code từ `__init__.py` sang sub-module, các stdlib imports ở cấp module (`ast`, `base64`, `fnmatch`, `glob`) không được tự động copy theo.
- **Hậu quả**: `NameError: name 'ast' is not defined` bị catch silently bởi `except Exception` → toàn bộ AST security scanning bị bypass mà không có error nào visible.
- **Phát hiện**: Chạy `ruff check` → F821 `Undefined name 'base64'`, `Undefined name 'ast'`.
- **Bài học**: Sau khi extract code ra file mới, luôn chạy `ruff check` ngay lập tức để phát hiện undefined names.

**2. Mock patch path phải theo đúng namespace thực tế**
- `@patch("ccba_legal.harness._original_popen")` → sai (sau khi tách ra `_process_monitor.py`)
- `@patch("ccba_legal.harness._process_monitor._original_popen")` → đúng
- `@patch("ccba_legal.harness.subprocess.run")` vẫn hoạt động vì `subprocess` là module singleton — patching qua alias `__init__.subprocess` affect cùng object trong `_guard.subprocess`.

**3. Backward-compat re-export module: dùng `# ruff: noqa: F401`**
- Khi `__init__.py` là pure re-export module, F401 warnings là false positives.
- Thêm `# ruff: noqa: F401` ở top file thay vì noqa từng dòng.

**4. `TYPE_CHECKING` cho forward references tránh circular import**
- Khi `_file_monitor.py` và `_process_monitor.py` cần type `HarnessGuard` (defined in `_guard.py` which imports them):
  ```python
  from typing import TYPE_CHECKING
  if TYPE_CHECKING:
      from ccba_legal.harness._guard import HarnessGuard
  ```
- Kết hợp với `from __future__ import annotations` → annotations không được evaluate tại runtime → không có circular import.

**5. Security constraint: strict type check**
- `_get_active_guards()` dùng `type(active_guards) is list` (KHÔNG phải `isinstance`) để block `FakeList` bypass attack.

### Anti-patterns

- **Không chạy ruff sau mỗi bước extract** → silent bug (AST bypass) tồn tại nhiều bước.
- **Copy toàn bộ import block từ `__init__.py` vào sub-module** → leftover migration stubs gây F401, F811.

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Pháp lý xây dựng"
bundle: "_core"
---
