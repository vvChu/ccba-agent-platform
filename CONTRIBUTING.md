# Hướng Dẫn Đóng Góp (Contributing Guide)

Chào mừng bạn đến với dự án **CCBA Agent Services Platform**! 👋
Dưới đây là một số quy tắc và hướng dẫn để giúp quá trình làm việc nhóm hiệu quả và an toàn.

## 🚀 Quy Trình Phát Triển (Workflow)

Dự án này áp dụng quy trình **Branch Protection** nghiêm ngặt trên nhánh `main`. Bạn **không thể push trực tiếp** vào `main`.

### Bước 1: Tạo Branch

---

Luôn tạo branch mới cho mọi thay đổi. Không code trên `main`.
Sử dụng Agent Workflow: `/ccba-new-feature` để tự động hóa.

**Quy tắc đặt tên:**

- `feature/ten-tinh-nang`: Tính năng mới
- `fix/ten-loi`: Sửa bug
- `docs/ten-tai-lieu`: Cập nhật tài liệu
- `refactor/ten-module`: Tối ưu code
- `experiment/ten-thu-nghiem`: Thử nghiệm

### Bước 2: Commit & Push

---

Commit thường xuyên với message rõ ràng.

```bash
git commit -m "Add login feature"
git push origin feature/login
```

### Bước 3: Tạo Pull Request (PR)

---

Khi hoàn thành hoặc cần review, hãy tạo Pull Request vào `main`.
Sử dụng Agent Workflow: `/ccba-create-pr` để tạo nhanh.

⚠️ **Yêu cầu bắt buộc để Merge:**

1. **CI Checks Passed**: Tất cả tests phải xanh (Python 3.10/3.11/3.12, Lint).
2. **Review Approved**: Phải được ít nhất 1 maintainer review và approve.

### Bước 4: Merge & Cleanup

---

Sau khi merge, hãy xóa branch cũ.
Sử dụng Agent Workflow: `/ccba-release-feature` để tự động merge và dọn dẹp.

---

## 🤖 Agent Workflows

Dự án có sẵn các workflow tự động hóa (trong `.agents/workflows/`):

| Lệnh | Chức năng | Khi nào dùng? |
| :--- | :--- | :--- |
| `/ccba-new-feature` | Tạo branch mới chuẩn naming, xóa branch rác | Bắt đầu task mới |
| `/ccba-create-pr` | Push code hiện tại và mở trang tạo PR | Code xong, cần review |
| `/ccba-release-feature` | Merge PR, xóa branch local/remote, update docs | Khi CI xanh + Approved |
| `/ccba-discard-feature` | Xóa bỏ branch thử nghiệm (Local + Remote) | Khi thử nghiệm thất bại |

---

## 🛠️ Môi Trường Dev

1. **Cài đặt nhanh (Windows)**: Chạy `./install.ps1`
2. **Cài đặt thủ công**: `pip install -e ".[dev,llm]"`
3. **Chạy Test**: `pytest`
4. **Lint Code**: `ruff check .`
5. **Format Code**: `ruff format .`

Cảm ơn bạn đã đóng góp! 🎉
