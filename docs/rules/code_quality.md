# CCBA Code Quality & Engineering Standards

> **Tài liệu Tham chiếu Quy chuẩn Lập trình (Layer 2)**  
> Áp dụng cho phát triển mã nguồn Python, TypeScript, và thiết kế Deep Modules trên CCBA Platform.

---

## 1. Automation-First Quality Gate
- Mọi thay đổi mã nguồn Python bắt buộc phải pass qua hai cổng kiểm tra tự động trước khi hoàn tất:
  1. **Linter & Formatter**: `ruff check` (tuân thủ cấu hình trong `pyproject.toml`).
  2. **Static Type Checker**: `mypy` (chế độ strict mode, 100% type hints cho parameters và return types).

---

## 2. Deep Seams & Module Depth (KISS)
- **Deep Modules**: Thiết kế giao diện công khai phẳng, đơn giản (1-3 public functions/classes) ẩn giấu toàn bộ độ phức tạp nghiệp vụ bên trong (high depth, low surface area).
- **Tránh Shallow Modules**: Không tạo các class/wrapper mỏng chỉ ủy quyền 1-1 mà không thêm giá trị xử lý.
- **KISS**: Ưu tiên giải pháp đơn giản nhất. Nếu một vấn đề có thể giải quyết bằng 10-15 dòng code sạch trong file hiện có, hãy làm vậy thay vì tạo abstraction mới.

---

## 3. SDLC Implementation Loop
Khi triển khai mã nguồn dựa trên đặc tả (Spec):
1. **TDD (Test-Driven Development)**: Viết unit tests trước tại các điểm khớp nối công khai (seams).
2. **Continuous Validation**: Chạy kiểm tra kiểu (`mypy`) và chạy test suite liên tục.
3. **Review before Merge**: Chạy `/ccba-code-review` để quét code smells trước khi tạo PR.
