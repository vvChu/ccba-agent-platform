## Session Learnings - Kiến thức tích lũy

## Cập nhật gần nhất: 2026-01-06

---

## Patterns (Mẫu tốt)

### Atomic File Writes

- **Ngữ cảnh**: Ghi dữ liệu quan trọng (như index cache) xuống đĩa.
- **Vấn đề giải quyết**: Tránh file bị corrupt nếu quá trình ghi bị ngắt quãng hoặc lỗi I/O.
- **Giải pháp**: Ghi vào file tạm (`tempfile.mkstemp`), sau đó dùng `Path.replace()` để atomic rename.
- **Ví dụ code**:

```python
    def _save_index(self) -> None:
        try:
            temp_fd, temp_path = tempfile.mkstemp(dir=self.cache_dir, suffix=".tmp")
            try:
                with open(temp_fd, "w", encoding="utf-8") as f:
                    json.dump(self._index, f, ensure_ascii=False)
                Path(temp_path).replace(self.index_path)
            except Exception:
                Path(temp_path).unlink(missing_ok=True)
                raise
        except OSError:
            pass
```

- **Nguồn**: Session [Fixing Copilot Suggestions - Cache I/O Safety]

### Streaming File Hashing

- **Ngữ cảnh**: Hash nội dung các file có thể rất lớn (GBs).
- **Vấn đề giải quyết**: Tránh đọc toàn bộ file vào RAM gây `MemoryError`.
- **Giải pháp**: Đọc file theo chunk (ví dụ 64KB) và update hash object.
- **Ví dụ code**:

```python
    def get_file_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()[:32]
```

- **Nguồn**: Session [Fixing Copilot Suggestions - Large File Handling]

### Async Non-blocking I/O in CLI

- **Ngữ cảnh**: CLI tool sử dụng `asyncio` nhưng cần gọi các hàm I/O đồng bộ (đọc/ghi file).
- **Vấn đề giải quyết**: Tránh block event loop chính, giúp concurrency hoạt động hiệu quả.
- **Giải pháp**: Sử dụng `loop.run_in_executor(None, func, *args)`.
- **Nguồn**: Session [Fixing Copilot Suggestions - CLI Async]

---

## Anti-patterns (Cách tránh)

### Blindly Following Copilot Suggestions

- **Vấn đề**: Copilot áp dụng generic best practices mà không hiểu context cụ thể của project (CLI vs server, internal tool vs public library).
- **Ví dụ**: Thread safety suggestions cho CLI tool chạy single-threaded, handler verification cho internal logging module.
- **Thay thế bằng**: Đánh giá mỗi suggestion dựa trên:
  1. **Use case thực tế** - CLI tool hay web server?
  2. **Scope của project** - Internal tool hay public library?
  3. **Trade-off** - Complexity thêm vào có worth it không?
- **Khi nào nên fix**: Critical bugs, security vulnerabilities, code correctness issues
- **Khi nào defer**: Style preferences, edge case optimizations, over-engineering suggestions
- **Nguồn**: Session [PR #10 Copilot Review]

### Cache Hit Without Disk Write

- **Vấn đề**: Khi cache hit, chỉ trả về nội dung trong memory mà không đảm bảo file output tồn tại trên đĩa. Điều này gây lỗi nếu user mong đợi file output.
- **Thay thế bằng**: Luôn kiểm tra và ghi lại file output từ nội dung cache nếu file đích chưa tồn tại hoặc cần cập nhật.
- **Nguồn**: Session [Fixing Copilot Suggestions - Critical Cache Bug]

### Content-Addressable Cache Collision

- **Vấn đề**: Sử dụng hash content làm key độc nhất cho file cache. Nếu 2 file nguồn khác nhau có cùng nội dung (trùng hash) sẽ trỏ vào cùng 1 file cache. Khi invalidate 1 file sẽ xoá mất file cache của file kia.
- **Thay thế bằng**: Dùng source path (hash của absolute path) làm key chính cho file cache để đảm bảo tính duy nhất 1-1, content hash chỉ để check change.
- **Nguồn**: Session [Fixing Copilot Suggestions - Cache Collision]

### Direct Dict Manipulation for Registry

- **Vấn đề**: Gán trực tiếp `ConverterRegistry._converters["name"] = class`. Phụ thuộc vào implementation detail private, khó bảo trì.
- **Thay thế bằng**: Sử dụng public API `ConverterRegistry.register("name")(class)`.
- **Nguồn**: Session [Fixing Copilot Suggestions - Registry Pattern]

---

## Solutions (Giải pháp tham chiếu)

### Handling Deprecated asyncio.get_event_loop()

- **Vấn đề**: Python 3.12 cảnh báo hoặc lỗi khi dùng `get_event_loop()` mà không có loop chạy.
- **Giải pháp**: Sử dụng `asyncio.get_running_loop()` bên trong hàm async.
- **Nguồn**: Session [Fixing Copilot Suggestions - Python 3.12 Compat]

---

## Configurations (Cấu hình tối ưu)

| Setting | Value | Lý do | Áp dụng khi |
| --------- | ------- | ------- | ------------- |
| HASH_CHUNK_SIZE | 65536 (64KB) | Tối ưu memory vs tốc độ | Mọi thao tác hash file |
| SHA256 Length | 32 chars | Đủ collision resistance cho file hash check, ngắn gọn hơn 64 | Cache filenames |
