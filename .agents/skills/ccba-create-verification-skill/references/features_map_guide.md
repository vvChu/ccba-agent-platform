# Hướng Dẫn Thiết Lập Features Map (Features Map Pattern - Pstack Upstream)

Features Map là mô hình quản trị tính năng kế thừa từ `pstack`, giúp liên kết trực tiếp giữa các module chức năng của ứng dụng và các bài kiểm định trong `verify-<app>`.

---

## 1. Mục Đích & Cấu Trúc `features/INDEX.md`

Mỗi ứng dụng hoặc Spoke nên duy trì tệp `features/INDEX.md` để:
1. Đảm bảo 100% tính năng trọng yếu đều có kịch bản kiểm thử tự động.
2. Theo dõi trạng thái sức khỏe của từng tính năng: `stable`, `flaky`, `in-progress`, `quarantine`.
3. Cung cấp chỉ mục rõ ràng cho AI Agent khi thực thi `/ccba-code-review` hoặc `verify-patch`.

---

## 2. Bản Mẫu Chuẩn Cho `features/INDEX.md`

```markdown
# Application Features Map & Verification Matrix

| Mã Tính Năng | Tên Tính Năng | Endpoint / CLI / Module | Verification Script | Trạng Thái | Last Verified |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `FEAT-001` | Auth & Session Token | `/api/v1/auth/login` | `.agents/skills/verify-app/harness/test_auth.py` | `stable` | 2026-10-05 |
| `FEAT-002` | Document Conversion | `mdconverter.convert` | `.agents/skills/verify-app/harness/test_convert.py` | `stable` | 2026-10-05 |
| `FEAT-003` | Realtime Streaming | `/api/v1/telemetry/ws` | `.agents/skills/verify-app/harness/test_stream.py` | `in-progress` | 2026-10-05 |
```

---

## 3. Quy Trình Vận Hành Với `verify-<app>`

1. Khi thêm tính năng mới: Thêm dòng mới vào `features/INDEX.md` với trạng thái `in-progress`.
2. Viết kiểm thử tự động trong `.agents/skills/verify-<app>/harness/test_<feat>.py`.
3. Chạy kiểm định qua kỹ năng `verify-<app>`. Khi vượt qua 100%, cập nhật trạng thái thành `stable`.
4. Nếu tính năng phát sinh lỗi trên môi trường CI nhưng chưa sửa ngay: Chuyển sang `quarantine` kèm số issue GitHub giải quyết (`# ccba:quarantine until=YYYY-MM-DD issue=...`).
