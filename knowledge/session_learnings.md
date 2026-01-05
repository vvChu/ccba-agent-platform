## Session Learnings - Kiến thức tích lũy

## Cập nhật gần nhất: 2026-01-05

---

## Patterns (Mẫu tốt)

### [Antigravity Workflow Automation]

- **Ngữ cảnh**: Cần chuẩn hóa quy trình lặp lại (tạo branch, cleanup, release).
- **Vấn đề giải quyết**: User hay quên lệnh Git, đặt tên branch sai convention, quên xóa branch cũ gây rác.
- **Giải pháp**: Tạo file `.md` trong `.agent/workflows/` định nghĩa các bước Git automation + AI prompting.
- **Ví dụ code**:

```markdown
# .agent/workflows/new-feature.md
// turbo
1. git checkout main && git pull
2. git branch -d [merged-branch]
3. Ask user for name -> Suggest convention
```

- **Nguồn**: Session [setup-workflow], 2026-01-05

### [Watchdog Debounce Pattern]

- **Ngữ cảnh**: Implement chức năng `--watch` để file monitoring.
- **Vấn đề giải quyết**: File editor thường ghi file nhiều lần (temp file, atomic write) gây multiple triggers cho 1 save action.
- **Giải pháp**: Implement `DEBOUNCE_SECONDS` trong Event Handler để ignore các event quá gần nhau.
- **Ví dụ code**:

```python
# src/mdconverter/core/watcher.py
def _should_process(self, path: Path) -> bool:
    now = time.time()
    if now - self._last_triggered.get(path, 0) < self.DEBOUNCE_SECONDS:
        return False
    self._last_triggered[path] = now
    return True
```

- **Nguồn**: Session [feature-watch-mode], 2026-01-05

### [Python Cross-Version Entry Points Access]

- **Ngữ cảnh**: Plugin discovery using `importlib.metadata.entry_points()`.
- **Vấn đề giải quyết**: API thay đổi giữa Python 3.9 (dict-like) và 3.10+ (group keyword).
- **Giải pháp**: Với project yêu cầu Python 3.10+, sử dụng trực tiếp `entry_points(group=name)`. Không cần version check.
- **Ví dụ code**:

```python
# src/mdconverter/plugins/manager.py
def load_plugins(self) -> None:
    # Python 3.10+ supports group keyword directly
    eps = importlib.metadata.entry_points(group=self.group)
    for ep in eps:
        plugin_module = ep.load()
```

- **Nguồn**: Session [fix-ci-failures], 2026-01-05

### [Async Converter Refactoring Pattern]

- **Ngữ cảnh**: Refactor sync converter (subprocess, HTTP calls) to async.
- **Vấn đề giải quyết**: CLI gọi `await converter.convert()` nhưng converter thực thi sync gây lỗi.
- **Giải pháp**:
  1. Subprocess: Dùng `asyncio.create_subprocess_exec()` + `await process.communicate()`
  2. HTTP calls: Dùng `httpx.AsyncClient` thay `requests`
- **Ví dụ code**:

```python
# Async subprocess pattern
process = await asyncio.create_subprocess_exec(
    "pandoc", str(source), "-o", str(output),
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
```

- **Nguồn**: Session [fix-ci-failures], 2026-01-05

---

## Anti-patterns (Cách tránh)

### [Untyped Third-Party Decorators in Strict MyPy]

- **Vấn đề**: Dùng decorator từ library không có type stubs (e.g., `tenacity.retry`) trong strict mode MyPy gây lỗi `untyped-decorator`.
- **Hậu quả**: CI fail với `error: Untyped decorator makes function "X" untyped`.
- **Thay thế bằng**: Thêm MyPy override trong `pyproject.toml`:

```toml
[[tool.mypy.overrides]]
module = ["module_using_untyped_decorator"]
disallow_untyped_decorators = false
```

- **Nguồn**: Session [fix-ci-failures], 2026-01-05

### [Unused Type Ignore Comments]

- **Vấn đề**: Thêm `# type: ignore[misc]` để fix MyPy local nhưng CI dùng Python version khác lại báo `Unused "type: ignore" comment`.
- **Hậu quả**: CI fail vì `warn_unused_ignores = true` trong strict mode.
- **Thay thế bằng**: Dùng module-level override thay vì inline ignore:

```toml
[[tool.mypy.overrides]]
module = ["specific_module"]
disallow_untyped_decorators = false  # or other specific option
```

- **Nguồn**: Session [fix-ci-failures], 2026-01-05

### [Missing Dependencies for Refactored Code]

- **Vấn đề**: Import library mới (e.g., `tenacity`) trong code refactor nhưng quên add vào `pyproject.toml`.
- **Hậu quả**: CI fail với `ModuleNotFoundError` dù local chạy được (vì đã install global).
- **Thay thế bằng**: Luôn chạy `pip install -e .` trong fresh venv hoặc check `pyproject.toml` dependencies khi thêm import mới.
- **Nguồn**: Session [fix-ci-failures], 2026-01-05

---

## Configurations (Cấu hình tối ưu)

### [GitHub Actions Trigger Rules]

- **Vấn đề**: CI không chạy khi push lên feature branch mới.
- **Lý do**: File `.github/workflows/ci.yml` thường được cấu hình chỉ trigger `on: [push]` cho main/master hoặc `on: [pull_request]`.
- **Giải pháp**: Phải tạo Pull Request (thậm chí là Draft PR) để kích hoạt CI cho feature branch. Push đơn thuần sẽ không trigger.
- **Áp dụng khi**: Debug tại sao GitHub Actions không hiện status check xanh/đỏ.
- **Nguồn**: Session [debug-ci], 2026-01-05

### [MyPy Strict Mode with Third-Party Libraries]

| Setting | Value | File | Lý do |
|---------|-------|------|-------|
| `disallow_untyped_decorators` | `false` | Per-module override | Cho module dùng untyped decorators (tenacity, etc) |
| `ignore_missing_imports` | `true` | Per-module override | Cho libraries không có stubs (llama_index, tenacity) |

- **Nguồn**: Session [fix-ci-failures], 2026-01-05

---

## Solutions (Giải pháp tham chiếu)

### [Typer + Watchdog Integration]

- **Vấn đề**: Hàm `watcher.wait()` của watchdog block main thread, làm sao tích hợp vào Typer CLI command?
- **Giải pháp**:
    1. Start observer (`watcher.start()`)
    2. Dùng `try/except KeyboardInterrupt` bọc quanh `watcher.wait()` (hoặc vòng `while True: sleep(1)`).
    3. Hứng `Ctrl+C` để gọi `watcher.stop()` shutdown graceful.
- **Liên kết**: `src/mdconverter/cli.py` (convert command)
- **Nguồn**: Session [feature-watch-mode], 2026-01-05

### [CI Failures Debugging Workflow]

- **Vấn đề**: CI fail nhưng local tests pass.
- **Giải pháp**:
  1. Check GitHub Actions logs: Navigate to Actions → Click failed run → Expand failing step
  2. Compare Python versions: Local vs CI matrix (3.10, 3.11, 3.12)
  3. Common culprits:
     - **Ruff linter**: Run `ruff check .` locally
     - **Ruff formatter**: Run `ruff format --check .` locally  
     - **MyPy**: Run `mypy --python-version 3.X src/` for each CI Python version
     - **Missing deps**: Check all imports have matching entries in `pyproject.toml`
- **Liên kết**: `.github/workflows/ci.yml`, `pyproject.toml`
- **Nguồn**: Session [fix-ci-failures], 2026-01-05

### [Async Function in Sync Context (Watch Mode)]

- **Vấn đề**: Watch mode callback là sync function nhưng cần gọi async converter.
- **Giải pháp**: Nest async function bên trong sync callback, wrap với `asyncio.run()`:

```python
def on_file_change(file: Path) -> None:
    async def convert_single() -> ConversionResult:
        converter = GeminiConverter(output_dir)
        return await converter.convert(file)
    
    result = asyncio.run(convert_single())
```

- **Liên kết**: `src/mdconverter/cli.py` (watch mode section)
- **Nguồn**: Session [fix-ci-failures], 2026-01-05
