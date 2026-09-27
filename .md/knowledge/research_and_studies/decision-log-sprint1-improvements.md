# Biên Bản Quyết Định Thiết Kế (Decision Log) — Sprint 1 Cải Tiến Nền Tảng CCBA

> **Quy trình thực hiện:** `/ccba-grilling` (Stress-Test Loop & Rule Compliance)  
> **Chủ đề:** Thống nhất phương án kỹ thuật triển khai các cải tiến từ mô hình Cursor/Bugbot vào CCBA Platform  
> **Ngày phê chuẩn:** 2026-09-27  
> **Trạng thái:** COMMITTED & READY_FOR_IMPLEMENTATION

---

## 1. Bối Cảnh & Mục Tiêu
Sau phiên nghiên cứu chuyên sâu đa tác nhân (`ccba-research`), đội ngũ đã tiến hành vòng lặp chất vấn phản biện Socratic (`ccba-grilling`) để tháo gỡ toàn bộ các giả định mầm, đánh giá sự đánh đổi giữa **Vận tốc (Velocity)**, **Bảo mật (Security)**, và **Độ ổn định (Resilience)**. Biên bản này ghi nhận 3 quyết định kiến trúc then chốt đã được thống nhất chính thức.

---

## 2. Bảng Tổng Hợp Quyết Định Thiết Kế (Design Decisions)

| Hạng Mục Thiết Kế | Lựa Chọn Đã Chốt | Cơ Chế Kỹ Thuật Chi Tiết | Lý Do Lựa Chọn & Đánh Đổi |
| :--- | :--- | :--- | :--- |
| **Quyết định 1: Chính sách Cổng CI Pre-Merge** | **Lựa chọn 3: Danger Triage CI Gate** | • **Nhóm rủi ro cao (One-way door):** Chạm vào core (`packages/ccba-harness`, `AGENTS.md`, `scripts/governance/`) $\to$ **Hard Blocking Gate** (quét toàn bộ, khóa nút Merge nếu fail).<br>• **Nhóm an toàn (Two-way door):** Sửa tài liệu (`.md/`), test cases, docstrings, hoặc 1 package vệ tinh $\to$ **Soft Advisory Check** (quét scoped, xuất markdown diagnostics nhưng không khóa merge). | Cân bằng hoàn hảo giữa việc bảo vệ tính toàn vẹn của Hiến chương Layer 1 và việc giải phóng tốc độ cho các PR bảo trì/tài liệu thường ngày. |
| **Quyết định 2: Cơ Chế Kích Hoạt & Bảo Mật Bugbot** | **Lựa chọn 1: Explicit Opt-in + Bắt buộc Maskara** | • **Kích hoạt có chủ đích:** Chỉ chạy AI Review khi PR có nhãn `ai-review-requested` hoặc gõ comment `/ccba-ai-review`. Loại trừ 100% PR tạo bởi bot (`author: [bot]`).<br>• **Làm sạch diff:** Bắt buộc diff phải đi qua `ccba-maskara` để ẩn danh hoá (`[REDACTED_SECRET]`) toàn bộ API keys, tokens, PII trước khi gửi cho LLM.<br>• **Quyền hạn:** AI Review chỉ có quyền Read-only (comment góp ý), CẤM quyền Approve/Merge tự động. | Loại trừ triệt để nguy cơ bão request làm nghẽn LiteLLM Gateway Spark (`:8090`), chống rò rỉ dữ liệu nhạy cảm ra ngoài trust boundary, và ngăn chặn vòng lặp race condition. |
| **Quyết định 3: Rào Chắn Kích Thước PR (Micro-PRs)** | **Lựa chọn 1: Dual Soft Gate (Cưỡng chế Kép Mềm)** | • **Tầng Lập Kế hoạch (`ccba-to-spec`):** Bổ sung quy tắc bắt buộc Agent phải bẻ User Story thành các micro-ticket $\le 150-200$ dòng code thay đổi, neo vào tối đa 1 Seam duy nhất.<br>• **Tầng CI/CD:** GitHub Action gắn nhãn cảnh báo `⚠️ pr-size-large` nếu diff vượt quá 300 dòng code logic (đã trừ test fixtures, data mock, `.md`), nhưng không khóa cứng nút Merge. | Giữ kỷ luật chia nhỏ công việc ngay từ khâu thiết kế spec của Agent, giảm blast radius, trong khi vẫn giữ cửa thoát hiểm linh hoạt cho các đợt refactor hoặc test data lớn. |

---

## 3. Kế Hoạch Triển Khai Chi Tiết (Sprint 1 Implementation Plan)

### Task 1: Soạn Thảo Bộ Quy Tắc Bugbot CCBA
* **Tệp đích:** `.github/bugbot-rules.md`
* **Nội dung:** Chuyển hóa các Invariants từ `AGENTS.md` thành 5 quy tắc máy đọc được:
  1. `[SEAM_REUSE]`: Tái sử dụng Seam từ `catalog.yaml`, cấm tạo utility ad-hoc trùng lặp.
  2. `[MULTI_KEY_SORT]`: Cấm `reverse=True` bao trùm; bắt buộc `key=lambda x: (-round(x.score, 4), x.name)`.
  3. `[DECOUPLED_CONNECTION]`: File `*_client.py` bắt buộc là leaf dependency, cấm import ngược từ Consumer.
  4. `[POSIX_PERMISSIONS]`: Bảo toàn `stat.S_IXUSR` khi ghi file thực thi.
  5. `[VERIFIER_LOCK]`: Cấm merge code logic nếu thiếu hoặc không cập nhật test tương ứng.

### Task 2: Thiết Lập Workflow CI Pre-Merge Gate
* **Tệp đích:** `.github/workflows/pr-verifier.yml`
* **Logic:**
  1. Phân loại đường dẫn thay đổi trong diff (`git diff origin/main...HEAD --name-only`).
  2. Xác định cờ Danger Level: `HIGH` (Core/Harness) vs `LOW` (Docs/Satellite).
  3. Kiểm tra số dòng code logic: Nếu $> 300$ LOC $\to$ gán nhãn `pr-size-large`.
  4. Chạy `python -m ccba_harness verify-patch`:
     - Nếu `HIGH`: Thất bại $\to$ `exit 1` (khóa Merge).
     - Nếu `LOW`: Thất bại $\to$ Post chẩn đoán cảnh báo, `exit 0` (cho phép Merge có kiểm soát).

### Task 3: Cập Nhật Quy Chuẩn Task Slicing Trong `ccba-to-spec`
* **Tệp đích:** `.agents/skills/ccba-to-spec/SKILL.md`
* **Nội dung:** Bổ sung phần **Micro-Task Slicing Invariant**:
  - Mọi User Story khi chuyển thành ticket thực thi phải có dự toán diff $\le 200$ LOC.
  - Mỗi ticket chỉ được phép tương tác với 1 Public Deep Seam duy nhất.
  - Gắn Acceptance Command rõ ràng để agent kiểm chứng tự động (`python -m pytest ...`).

---

## 4. Chữ Ký Phê Chuẩn
* **Chủ trì thẩm tra:** CCBA Architecture & Governance Core
* **Kết quả Grilling:** Đạt 100% đồng thuận, hoàn toàn triệt tiêu các giả định mầm. Sẵn sàng khởi động triển khai thực tế.
