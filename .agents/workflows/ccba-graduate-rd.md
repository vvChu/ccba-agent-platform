---
description: >-
  Quy trình cưỡng chế chuyển hóa mã nguồn R&D / Scratch Script
  thành Deep Seam Production trong Hub Platform.
applies_to:
  - Phần mềm
  - Kiểm định
bundle: _core
disable-model-invocation: true
command: /ccba-graduate-rd
triggers:
  - graduate
  - tốt nghiệp
  - hợp nhất vào hub
  - consolidate
  - deep seam
  - chuyển scratch vào production
  - ccba-graduate-rd
---
# Workflow: Tốt Nghiệp R&D → Deep Seam Production (/ccba-graduate-rd)

Quy trình cưỡng chế 5 bước chuyển hóa mã nguồn thử nghiệm (scratch script, prototype, patch script) thành module Production chuẩn mực trong Hub Platform (`packages/ccba-*/src/`).

> [!CAUTION]
> **3 Bất Biến Tuyệt Đối (Invariants):**
> 1. **Không để script vá tồn tại qua phiên:** Mọi scratch script phải nằm trong `.md/scratch/` hoặc artifacts `brain/*/scratch/`, tuyệt đối cấm commit vào `scripts/` của Spoke mà không qua quy trình này.
> 2. **Upstream Promotion bắt buộc:** Khi scratch script chứng minh hiệu quả → Bắt buộc refactor logic vào Hub `packages/` trong **cùng phiên**.
> 3. **1-Pass Clean Run bắt buộc:** Sau hợp nhất, xóa scratch script và chạy lại lệnh gốc từ đầu vào ban đầu để chứng minh lõi tự xử lý hoàn hảo.

---

## 📋 Bước 1: Kiểm Kê & Phân Loại R&D Artifacts

Quét và liệt kê toàn bộ scratch scripts / prototype files liên quan:
- Thư mục `brain/*/scratch/` (artifacts phiên hiện tại)
- Thư mục `.md/scratch/` (scratch workspace)
- Thư mục `scripts/` (kiểm tra xem có script vá ngoại lệ nào không)

Với mỗi file, phân loại:

| Loại | Hành động |
| :--- | :--- |
| **Thuật toán cốt lõi** (regex, parser, classifier, KaTeX) | → Bước 2: Bóc tách & Nhúng vào Deep Seam |
| **Glue code** (CLI wrapper, `print`, `tempfile`, argparser) | → Bỏ qua, không nhúng vào lõi |
| **Dữ liệu mẫu / fixture** | → Bước 3: Chuyển thành test fixture |
| **Báo cáo / ghi chú** | → `.md/archive/` theo chuẩn ADR 0033 |

---

## 🔧 Bước 2: Bóc Tách Thuật Toán & Nhúng Vào Deep Seam

1. **Xác định vị trí đích trong Hub:** Thuật toán thuộc Converter nào? Engine nào? Package nào trong `packages/ccba-*/src/`?
2. **Áp dụng 5 Cổng Phản Biện** từ `improve-codebase-architecture`:
   - **Cổng 1 (Glue vs Domain):** Tỷ lệ $\\ge 70\%$ Glue Code $\\rightarrow$ KHÔNG nhúng vào lõi Seam.
   - **Cổng 2 (Hard Caller Gate):** Đếm số callers thực tế và xác minh implementation.
   - **Cổng 3 (SDK Signatures):** Kiểm tra signature tương thích với hệ thống hiện có.
   - **Cổng 4 (Unique Naming):** Đảm bảo symbol name không xung đột toàn cục.
   - **Cổng 5 (Measurable Friction):** Bằng chứng lỗi runtime hoặc số đo benchmark thực tế.
3. **Refactor & Nhúng Lõi:**
   - Loại bỏ mọi `print`, `sys.path.insert`, `tempfile`, hardcoded paths.
   - Thêm type hints đầy đủ (parameters + return types).
   - Thêm docstring Google style cho mọi public function/class.
   - Khai báo rõ ràng trong `__init__.py` / `__all__` nếu là public interface của Deep Seam.

---

## 🧪 Bước 3: Xây Dựng Test Harness

1. Chuyển đổi dữ liệu mẫu từ phiên R&D thành **test fixtures** trong `packages/ccba-*/tests/fixtures/` hoặc test inputs.
2. Viết **ít nhất 1 unit test** cho mỗi hàm public / feature mới đã nhúng.
3. Chạy test suite đầy đủ của package:
   ```powershell
   python -m pytest packages/ccba-*/tests/ -v
   ```
   *Tiêu chuẩn:* **100% tests passed, 0 failures**.

---

## 🔁 Bước 4: Kiểm Chứng 1-Pass Clean Run

Đây là bước **cốt lõi nhất** — chứng minh lõi nền tảng tự xử lý hoàn hảo:

1. **Xóa scratch script gốc** (file `.py` trong `scripts/` hoặc `scratch/`).
2. **Chạy lại lệnh gốc từ đầu vào ban đầu:**
   ```powershell
   # Ví dụ với bộ chuyển đổi TCVN:
   python -m ccba_legal convert "ten_van_ban.docx" "legal_docs/03_tcvn/ten_van_ban"
   ```
3. **So sánh output:** Kết quả phải **tương đương hoặc tốt hơn** so với khi chạy script vá bên ngoài.
4. **Chạy Master CI Gate:**
   ```powershell
   python scripts/validate_legal_spoke.py
   ```
   *Tiêu chuẩn:* `0 Errors, 0 Warnings, 100% Pass`.

---

## 📦 Bước 5: Lưu Trữ & Đóng Vòng

1. **Lưu trữ ghi chú R&D** vào `.md/archive/` theo chuẩn ADR 0033.
2. **Cập nhật `session_learnings.md`** với bài học rút ra từ quá trình tốt nghiệp (pattern mới phát hiện, edge case, v.v.).
3. **Commit theo chuẩn Git:**
   - Hub: `refactor(scope): consolidate R&D [feature] into Deep Seam`
   - Spoke: `chore(scope): remove obsolete patch script [name]`
4. Nếu thay đổi ảnh hưởng đến kiến trúc nền tảng $\\rightarrow$ Đề xuất ghi nhận ADR mới.
