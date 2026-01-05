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

---

## Configurations (Cấu hình tối ưu)

### [GitHub Actions Trigger Rules]

- **Vấn đề**: CI không chạy khi push lên feature branch mới.
- **Lý do**: File `.github/workflows/ci.yml` thường được cấu hình chỉ trigger `on: [push]` cho main/master hoặc `on: [pull_request]`.
- **Giải pháp**: Phải tạo Pull Request (thậm chí là Draft PR) để kích hoạt CI cho feature branch. Push đơn thuần sẽ không trigger.
- **Áp dụng khi**: Debug tại sao GitHub Actions không hiện status check xanh/đỏ.
- **Nguồn**: Session [debug-ci], 2026-01-05

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
