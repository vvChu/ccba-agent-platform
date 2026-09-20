---
name: ccba-implement
description: Implement a piece of work based on a spec or set of tickets.
tier: orchestrator
is-orchestrated: true
user-invocable: true
command: /ccba-implement
disable-model-invocation: true
bundle: _core
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
triggers:
- ccba-implement
- ccba-implement spec
- ccba-implement ticket
- ccba-discard-feature
- discard-feature
- ccba-prototype
- prototype
---

# Quy Trình Hiện Thực Hóa Tính Năng & Mã Nguồn (/ccba-implement)

Quy trình chuẩn hóa triển khai mã nguồn dựa trên đặc tả kỹ thuật (spec) hoặc danh sách công việc (tickets), kết hợp phương pháp Test-Driven Development (TDD) và kiểm soát nghiêm ngặt ngân sách ngữ cảnh (Context Budget).

## Quản trị ngân sách ngữ cảnh & Bậc thang leo thang (Context Budget & Escalation)
1. **Chỉ chạy Scoped Tests:** Luôn chạy pytest trên từng tệp kiểm thử riêng lẻ (`python scripts/safe_pytest.py -f tests/test_specific.py`), không chạy toàn bộ thư mục trong chu kỳ phát triển.
2. **Hạn mức chu kỳ (Loop Budget):** Tối đa 5 chu kỳ chỉnh sửa $\rightarrow$ kiểm thử cho mỗi seam.
   - **Leo thang sớm (Chu kỳ 3):** Nếu test vẫn thất bại sau 3 lần do lỗi logic sâu, hãy dừng đoán mò và tổng hợp **Deep Problem Brief**.
   - **Dừng cứng (Chu kỳ 5):** Dừng ngay lập tức, commit WIP và kích hoạt **Boost Escalation Gate** (`/boost [brief]`).
3. **Bộ kiểm thử toàn diện:** Chỉ chạy toàn bộ test suite một lần duy nhất tại bước kết thúc công việc.

---

## Các bước thực hiện

### Bước 1: Phân tích đặc tả và thiết kế Deep Seams (Spec Breakdown)
1. Đọc kỹ đặc tả hoặc danh sách ticket do người dùng cung cấp.
2. Kiểm tra `catalog.yaml` để áp dụng nguyên tắc Reuse-First, tránh viết lại các tiện ích đã tồn tại.
3. Xác định các Deep Seams cần sửa đổi hoặc tạo mới, vạch rõ phạm vi thay đổi (blast radius).
- **Tiêu chí hoàn thành:** Bản tóm tắt yêu cầu, danh sách module bị tác động và các interfaces cần tuân thủ được xác lập rõ ràng.

### Bước 2: Thiết lập kiểm thử dẫn dắt (TDD Seam Definition)
1. Tạo hoặc cập nhật tệp kiểm thử chuyên biệt phản ánh đúng các tiêu chí nghiệm thu của spec.
2. Viết các ca kiểm thử cho cả trường hợp bình thường (happy path) và các điều kiện biên (edge cases).
3. Chạy kiểm thử ban đầu để xác nhận test thất bại đúng lý do mong đợi (Red phase).
- **Tiêu chí hoàn thành:** Scoped unit test được viết hoàn tất và ghi nhận trạng thái Red ban đầu.

### Bước 3: Triển khai mã nguồn tối thiểu (KISS Implementation)
1. Hiện thực hóa mã nguồn trong các file liên quan để làm các test case chuyển sang trạng thái Green.
2. Tuân thủ chuẩn mực mã nguồn: Type hints đầy đủ, docstrings phong cách Google, hàm không vượt quá 50 dòng.
3. Không tự ý thêm abstraction hoặc lớp trung gian nếu bài toán giải quyết được bằng 10-15 dòng code.
- **Tiêu chí hoàn thành:** Toàn bộ scoped unit test chuyển sang trạng thái Green với mã nguồn đơn giản, mạch lạc.

### Bước 4: Kiểm tra tĩnh và kiểm thử hồi quy (Deterministic Gate & Regression)
1. Kích hoạt cổng kiểm định máy tính một chạm:
   ```bash
   python -m ccba_harness verify-patch --preset code --target <package_or_dir>
   ```
   *Lệnh này tự động thực thi chuỗi: `ruff check`, `mypy --follow-imports=silent`, và `pytest -q`.*
2. Chạy kiểm thử hồi quy cho các module lân cận nếu có ảnh hưởng liên vùng.
3. Nếu phát hiện lỗi (Exit Code $\ne 0$), kích hoạt vòng lặp Fix Loop để giải quyết triệt để lỗi kiểu và linter.
- **Tiêu chí hoàn thành:** Lệnh `python -m ccba_harness verify-patch --preset code --target <package_or_dir>` trả về **Exit Code 0** (Overall Status: PASS). Theo quy tắc Khóa Cứng (HUB-ADR-0058): Cấm tuyệt đối Agent tuyên bố hoàn thành hoặc chuyển sang Bước 5 nếu có bất kỳ lệnh nào fail.

### Bước 5: Kiểm toán kiến trúc và đóng gói (Architecture Audit & Handover)
1. Kiểm tra xem có thay đổi cấu trúc monorepo hay không (thêm/xóa/đổi tên thư mục, packages, scripts).
2. Nếu có thay đổi cấu trúc, chạy `python scripts/update_arch_stats.py` để cập nhật số liệu kiến trúc tự động.
3. Chạy lệnh `/ccba-code-review` để thực hiện phản biện đa chiều trước khi commit.
4. Tạo git commit theo chuẩn Conventional Commits cục bộ.
- **Tiêu chí hoàn thành:** Báo cáo kiểm toán kiến trúc cập nhật đầy đủ, mã nguồn được commit tại local và sẵn sàng bàn giao.


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/discard_feature_sop.md` | Quy trình chuẩn thao tác Git hủy bỏ tính năng an toàn |
| `references/prototyping_patterns.md` | Mẫu hình tạo spike / prototype nhanh để kiểm chứng giải pháp kỹ thuật |
| `references/prototype_logic.md` | Hướng dẫn tạo prototype logic dòng lệnh và thuật toán kiểm chứng nhanh |
| `references/prototype_ui.md` | Hướng dẫn tạo prototype giao diện người dùng tương tác trực quan |

## Kỷ Luật Rà Soát Hai Vòng (Double-Pass Adversarial Review)
* **Vòng 1 (Code-First Research):** Luôn đọc implementation thực tế và kiểm tra data flow end-to-end trước khi sửa đổi. Không suy đoán hành vi từ tên hàm hay docstring.
* **Vòng 2 (Self-Adversarial Review):** Tự đặt câu hỏi: *Đề xuất này có thể SAI ở đâu?* Kiểm chứng tối thiểu 3 giả định cốt lõi bằng dữ liệu và kiểm thử thực tế trước khi bàn giao.
* **Bảo tồn Invariants:** Không bao giờ xóa hoặc nới lỏng (weaken) các bài test hiện có để làm cho bài test vượt qua.
