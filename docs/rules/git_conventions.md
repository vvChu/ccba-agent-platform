# CCBA Git Conventions

> **Tài liệu Tham chiếu Quy chuẩn Git (Layer 2)**  
> Áp dụng cho mọi hoạt động commit, tạo branch, và gửi Pull Request trên Platform (Hub & Spokes).

---

## 1. Branch Naming
- Format: `type/short-description`
- Ví dụ:
  - `feat/add-auth`
  - `fix/query-timeout`
  - `refactor/deepen-pdf-pipeline`

---

## 2. Commit Message Standard
- Format: `type(scope): description` (bằng tiếng Anh).
- **Valid Types**:
  - `feat`: Tính năng mới hoặc mở rộng chức năng.
  - `fix`: Sửa lỗi (bug fix).
  - `docs`: Cập nhật tài liệu kỹ thuật, ADR, hoặc knowledge base.
  - `refactor`: Tái cấu trúc mã nguồn không làm đổi hành vi bên ngoài.
  - `test`: Thêm hoặc chỉnh sửa unit/integration tests.
  - `chore`: Bảo trì phụ thuộc, build config, workflows.
  - `ci`: Cấu hình automation, pre-commit hooks, CI gates.

---

## 3. Atomic Logical Commits
- Luôn commit theo từng logical unit độc lập và khép kín.
- Tuyệt đối không gom toàn bộ các thay đổi không liên quan vào một commit lớn (`git add . && git commit`).

---

## 4. Repository Protection & Safety SOP
- Mọi kho chứa mã nguồn (Repositories) thuộc Hub và Spoke bắt buộc tuân thủ chuẩn thiết lập bảo vệ đa tầng theo quy trình: [CCBA-SOP-SEC-001: Hướng Dẫn Thiết Lập Bảo Vệ Repository Trên GitHub](../sop/github_repo_protection_guide.md).
- Nhánh `main` được bảo vệ tuyệt đối bằng GitHub Rulesets: cấm direct push, cấm force-push, bắt buộc PR có review từ Code Owners (`.github/CODEOWNERS`) và bắt buộc vượt qua 100% status checks (`scan`, `Test - Python 3.12`, `Deterministic Parity & Schema Audit`).
- Phía máy trạm (Client-side), kỹ sư kích hoạt rào chắn cục bộ từ thư mục hooks đã được đóng gói sẵn trong repo: `git config core.hooksPath .githooks && chmod +x .githooks/*`.


