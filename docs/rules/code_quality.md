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

---

## 4. Cognitive Skills Quality & Invariant Gates (Layer 2)
- Mọi Agent Skill thuộc hệ sinh thái CCBA phải tuân thủ Khung Quyết Định Hai Giai Đoạn (ADR-0057).
- Kỹ năng có nhiều chế độ hoạt động (multi-mode) bắt buộc phải xây dựng Tiêu chí hoàn thành động kiểm chứng đầy đủ từng mode, không để xảy ra tình trạng thiên lệch luồng mặc định gây hoàn thành non.
- Tuân thủ nguyên tắc Single Source of Truth trong các tài liệu tham chiếu vệ tinh (`references/*.md`, `MODES.md`), tuyệt đối không nhân bản các cảnh báo ràng buộc cờ.
- **Recompilation & Asset Synchronization Gate (HUB-ADR-0047, HUB-ADR-0058):**
  Khi tạo mới, chỉnh sửa nội dung hoặc bump version bất kỳ tệp `SKILL.md` nào, Agent **BẮT BUỘC** phải kích hoạt chuỗi 3 lệnh tái biên dịch và đồng bộ hóa tài sản nền tảng:
  1. `python scripts/governance/compile_catalog.py` (Cập nhật catalog SSOT `catalog.yaml`).
  2. `python scripts/governance/compile_skills_docs.py --write` (Đồng bộ Web Docs Portal, Markdown docs, và llms.txt).
  3. `python scripts/sync_hub_adr_matrix.py` (Đồng bộ Living Traceability Matrix nếu kỹ năng có viện dẫn hoặc điều chỉnh phạm vi ADR).

