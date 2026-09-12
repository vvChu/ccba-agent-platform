---
name: ccba-tdd
description: Phát triển hướng kiểm thử (Red-Green-Refactor) giúp tạo mã nguồn ổn định,
  tin cậy thông qua các giao diện công khai (seams).
user-invocable: true
command: /ccba-tdd
when_to_use: Dùng khi người dùng yêu cầu phát triển tính năng mới hoặc sửa lỗi bằng
  phương pháp viết test trước (test-first).
category: utilities
gpi:
  s: 3.0
  k: 2.0
  a: 1.0
  p: 1.0
triggers:
- ccba-tdd
- test
- refactor
- quality
metadata:
  author: CCBA
  version: 1.2.0
disable-model-invocation: true
bundle: _software
tier: kernel
---
# Quy trình Phát triển Hướng Kiểm thử (Test-Driven Development)

TDD là chu kỳ lặp Red → Green → Refactor. Kỹ năng này cung cấp quy trình và tiêu chuẩn để chu kỳ đó tạo ra những bộ test chất lượng cao, dễ bảo trì và bám sát ngôn ngữ nghiệp vụ của dự án.

Khi khám phá codebase, đọc `CONTEXT.md` (nếu có) để tên test và từ vựng giao diện đồng bộ với ngôn ngữ nghiệp vụ của dự án, và tuân thủ các ADRs trong khu vực bạn đang can thiệp.

## Quy trình Thực hiện (Process)

### 1. Xác định Seam và viết Test thất bại (Red Phase)
- Xác định giao diện công khai (seam) cần kiểm thử và thống nhất với người dùng trước khi viết test. Chỉ test tại seams, không viết test cho private internals.
- Viết một test case nhỏ nhất chứng minh tính năng mới chưa hoạt động (hoặc bug chưa được sửa).
- Chạy lệnh test và xác nhận test thất bại (Red).
- **Tiêu chí hoàn thành:** Lệnh test chạy thất bại và lý do thất bại đúng do logic mong muốn chưa được cài đặt (không phải do lỗi cú pháp hoặc lỗi môi trường).

### 2. Viết mã nguồn tối giản để Pass test (Green Phase)
- Viết lượng mã nguồn tối thiểu để test chuyển sang màu xanh (Green). Không cố đoán trước các tính năng tương lai hoặc viết code thừa ngoài spec.
- Chạy lệnh test và xác nhận test thành công (Green).
- **Tiêu chí hoàn thành:** Bộ test chạy thành công 100% với 0 lỗi thất bại.

### 3. Tái cấu trúc mã nguồn (Refactor Phase & Deterministic Gate)
- Tối ưu hóa cấu trúc code, loại bỏ trùng lặp và làm sạch mã nguồn mà không làm thay đổi hành vi bên ngoài của seam.
- Chạy cổng kiểm định máy tính một chạm:
  ```bash
  python -m ccba_harness verify-patch --preset code --target <package_or_dir>
  ```
  *(Tự động kiểm tra ruff linting, mypy typing và pytest hồi quy).*
- **Tiêu chí hoàn thành:** Mã nguồn sau refactor sạch sẽ, vượt qua lệnh kiểm định khách quan `python -m ccba_harness verify-patch --preset code --target <package_or_dir>` với **Exit Code 0** (100% ruff, mypy, pytest passed). Quy tắc Khóa Cứng (ADR-0058): Cấm tuyệt đối Agent kết thúc chu kỳ TDD nếu kiểm định máy tính chưa đạt mã thoát 0.

## Seams — Nơi đặt các Test

Một **seam** (mối nối) là ranh giới công khai bạn thực hiện kiểm thử: giao diện nơi bạn quan sát hành vi của module mà không cần can thiệp sâu vào bên trong. Các test phải nằm ở seams, tuyệt đối không nằm ở phần internals.

> [!IMPORTANT]
> **Quy chuẩn Codebase Design khi viết test:**
> Bắt buộc tuân thủ quy tắc thiết kế module sâu. Chỉ viết test tại các seam (giao diện module thực sự). Nghiêm cấm viết các unit test quá sâu vào cấu trúc hoặc implementation private của các module nông (shallow modules) để tránh tình trạng vỡ bộ test khi refactor code sau này.

Hỏi người dùng: *"Giao diện công khai là gì, và chúng ta nên kiểm thử ở những seam nào?"*

## Các mẫu phản hoa tiêu (Anti-patterns) cần tránh

- **Ràng buộc Implementation (Implementation-coupled):** Mock các cộng tác viên nội bộ, kiểm thử các hàm private, hoặc xác minh qua kênh phụ (truy vấn trực tiếp database thay vì dùng giao diện). Dấu hiệu nhận biết: bộ test bị vỡ khi refactor dù hành vi của module không thay đổi.
- **Trùng lặp logic (Tautological):** Assert tính toán lại giá trị mong đợi theo đúng cách mà code thực thi. Giá trị mong đợi phải đến từ một nguồn chân lý độc lập (như literals, Spec).
- **Lát cắt ngang (Horizontal slicing):** Viết tất cả test trước rồi mới viết code sau. Hãy làm theo **lát cắt dọc (vertical slices)**: một test → một implementation tối giản → lặp lại. Mỗi test đóng vai trò như một đường đạn dò tìm (tracer bullet) phản hồi lại những gì chu kỳ trước đã dạy bạn.

## Nguyên tắc của Chu kỳ (Rules of the loop)

- **Đỏ trước Xanh (Red before green):** Luôn viết test thất bại trước, sau đó chỉ viết đủ code để pass test đó.
- **Một lát cắt tại một thời điểm:** Một seam, một test, một lượng code tối giản cho mỗi chu kỳ.
- **Refactoring là một phần bắt buộc:** Phải được thực hiện ngay sau khi test pass (Green) để giữ cho codebase luôn sạch sẽ trước khi chuyển sang chu kỳ tiếp theo.
- **Ngân sách Vòng lặp (Loop Budget):** Tối đa **5 vòng** Red→Green→Refactor cho cùng một seam hoặc test file. Sử dụng `python scripts/safe_pytest.py -f <test_file>` để chạy test an toàn dưới dạng detached process. Nếu sau 5 vòng test vẫn thất bại, Agent phải dừng lại, commit Work-In-Progress (WIP), ghi nhận rõ các blockers chưa giải quyết được, và chuyển sang seam tiếp theo hoặc xin chỉ thị từ người dùng. Quy tắc này ngăn chặn việc đốt cháy context budget qua vòng lặp vô hạn (xem `issue-wayfinder-cancelled-execution`).

## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ kiểm thử và thiết kế seams chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/tests.md` | Bộ đối chiếu kiểm thử tốt vs xấu (Integration-style vs Implementation-detail tests) |
| `references/mocking.md` | Hướng dẫn kỹ thuật mock tại ranh giới hệ thống (system boundaries, DI, SDK-style) |

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
