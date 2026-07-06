---
name: tdd
description: Phát triển hướng kiểm thử (Red-Green-Refactor) giúp tạo mã nguồn ổn định, tin cậy thông qua các giao diện công khai (seams).
user-invocable: true
when_to_use: "Dùng khi người dùng yêu cầu phát triển tính năng mới hoặc sửa lỗi bằng phương pháp viết test trước (test-first)."
category: utilities
keywords: [tdd, test, refactor, quality]
metadata:
  author: CCBA
  version: "1.1.0"
---

# Quy trình Phát triển Hướng Kiểm thử (Test-Driven Development)

TDD là chu kỳ lặp Red &rarr; Green &rarr; Refactor. Kỹ năng này cung cấp quy trình và tiêu chuẩn để chu kỳ đó tạo ra những bộ test chất lượng cao, dễ bảo trì và bám sát ngôn ngữ nghiệp vụ của dự án.

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

### 3. Tái cấu trúc mã nguồn (Refactor Phase)
- Tối ưu hóa cấu trúc code, loại bỏ trùng lặp và làm sạch mã nguồn mà không làm thay đổi hành vi bên ngoài của seam.
- Chạy lại toàn bộ kiểm thử để đảm bảo refactor không làm vỡ các tính năng cũ.
- **Tiêu chí hoàn thành:** Mã nguồn sau refactor sạch sẽ, tuân thủ các coding standards và bộ test vẫn pass 100%.

## Quy chuẩn viết Test chất lượng

*   **Không móc nối implementation (Implementation-coupled):** Tránh mock các cộng tác viên nội bộ hoặc test các hàm private. Test chỉ nên quan tâm đến đầu vào và đầu ra của seam công khai.
*   **Tránh Test trùng lặp logic (Tautological):** Giá trị mong đợi (expected value) trong assert phải độc lập (ví dụ: hardcoded literal hoặc worked example từ spec), không được tính toán lại bằng công thức giống hệt trong code.
*   **Lát cắt dọc (Vertical slices):** Không viết hàng loạt test rồi mới viết code. Hãy đi theo từng lát cắt dọc: một test &rarr; một implementation tối giản &rarr; lặp lại.

## Tài liệu tham khảo
*   Xem [tests.md](tests.md) để biết các ví dụ thực tế.
*   Xem [mocking.md](mocking.md) để biết hướng dẫn mock chuẩn.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
