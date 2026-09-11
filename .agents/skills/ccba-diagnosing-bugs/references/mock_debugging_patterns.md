# ccba-mock-debugger — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Mẫu hình mock dữ liệu và tạo ca kiểm thử mô phỏng khi chẩn đoán lỗi phần mềm
> **Mô tả gốc:** Automated debugger and self-healing trace analyzer. Runs scripts, captures tracebacks, and provides root cause analysis and code patch suggestions via AI.

---

# Bộ Tự Động Gỡ Lỗi & Tự Phục Hồi Mã Nguồn (/ccba-diagnosing-bugs)

Kích hoạt hệ thống phân tích vết traceback tự động, truy vết nguyên nhân gốc rễ (RCA) và đề xuất bản vá mã nguồn tối thiểu (Self-Healing Debugger) cho các script Python trên nền tảng CCBA.

## Nguyên tắc gỡ lỗi (Debugging Principles)
- **Tái lập lỗi trước khi sửa (Reproduce First):** Không đoán mò nguyên nhân, luôn chạy script trong môi trường cô lập để chụp trọn vẹn traceback.
- **Giải pháp tối thiểu (KISS Patching):** Ưu tiên bản vá từ 5-15 dòng mã nguồn, tránh tái cấu trúc lan man không cần thiết.
- **Không làm suy yếu kiểm thử:** Tuyệt đối không nới lỏng assertions hoặc xóa bỏ unit test để làm bài kiểm thử pass giả tạo.

---

## Các bước thực hiện

### Bước 1: Thu thập vết traceback và bối cảnh thực thi (Traceback Capture)
1. Chạy kịch bản gỡ lỗi tự động trên tệp mục tiêu bị lỗi:
   ```bash
   python scripts/security/mock_debugger.py path/to/failing_script.py [arguments]
   ```
2. Thu thập mã lỗi thoát (exit code), toàn bộ nội dung `stderr` và cấu trúc dòng gọi hàm (`Call Stack`).
3. Xác định phạm vi biến cục bộ và trạng thái môi trường lúc xảy ra exception.
- **Tiêu chí hoàn thành:** Bắt trọn vẹn traceback, định vị chính xác tệp nguồn và số dòng xảy ra exception.

### Bước 2: Phân tích nguyên nhân gốc rễ (Root Cause Analysis - RCA)
1. Đọc nội dung mã nguồn xung quanh vị trí dòng lỗi (ít nhất 20 dòng trước và sau).
2. Phân loại dạng lỗi: cú pháp (`SyntaxError`), kiểu dữ liệu (`TypeError`), logic điều kiện (`KeyError`, `IndexError`), hay tài nguyên (`FileNotFoundError`).
3. Đối chiếu với các thay đổi commit gần đây trên tệp thông qua `git diff` hoặc `git log -p -n 1`.
- **Tiêu chí hoàn thành:** Xác định rõ ràng cơ chế gây lỗi và điều kiện biên chưa được bao quát.

### Bước 3: Đề xuất bản vá thử nghiệm (Minimal Patch Synthesis)
1. Xây dựng bản vá mã nguồn dạng Git diff tuân thủ nghiêm ngặt nguyên tắc KISS.
2. Đảm bảo bản vá bổ sung guardrail hoặc xử lý ngoại lệ tường minh (specific exception handling).
3. Đảm bảo toàn bộ type hints và docstrings được giữ nguyên hoặc cập nhật chính xác.
- **Tiêu chí hoàn thành:** Bản vá tối thiểu được tạo dưới dạng unified diff rõ ràng, sẵn sàng áp dụng.

### Bước 4: Kiểm thử hồi quy cô lập (Regression Verification)
1. Áp dụng bản vá tạm thời vào tệp mã nguồn liên quan.
2. Chạy lại script ban đầu để xác minh lỗi crash đã được khắc phục triệt để.
3. Chạy kiểm thử tự động trên test suite của module: `pytest path/to/tests/test_affected.py`.
- **Tiêu chí hoàn thành:** Script chạy thành công không còn crash và toàn bộ scoped tests đều pass.

### Bước 5: Ghi nhận bài học và báo cáo giải pháp (Learning Retrospective)
1. Trình bày báo cáo tóm tắt cho người dùng: Bản chất lỗi, giải pháp đã áp dụng và kết quả kiểm thử.
2. Nếu lỗi liên quan đến kiến trúc hoặc mẫu phổ biến, cập nhật kinh nghiệm vào `.md/knowledge/session_learnings.md`.
- **Tiêu chí hoàn thành:** Báo cáo hoàn tất gửi người dùng và nhật ký bài học được cập nhật nếu có.
