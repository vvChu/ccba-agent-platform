# ccba-long-form-writer — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Kỹ thuật phân chia chương mục và viết bài học thuật dung lượng lớn
> **Mô tả gốc:** Tạo lập tài liệu học thuật và báo cáo dung lượng lớn (2000+ từ) bằng kỹ thuật chia nhỏ ngữ cảnh để vượt qua giới hạn đầu ra của LLM.

---

# Hướng Dẫn Soạn Thảo Tài Liệu Học Thuật Dung Lượng Lớn (Long-Form Writing)

Tài liệu này hướng dẫn kỹ thuật tạo lập nội dung học thuật, quy chuẩn kỹ thuật hoặc báo cáo chuyên sâu có dung lượng lớn vượt qua giới hạn token đầu ra tiêu chuẩn của LLM. Thay vì cố gắng sinh toàn bộ tài liệu trong một lượt gọi duy nhất (dễ dẫn đến hiện tượng tóm tắt sơ sài hoặc đứt đoạn), quy trình áp dụng mô hình **Vòng lặp Tiếp nối Nhận thức (Chain of Continuation & Section Chunking)**.

## 1. Khi Nào Cần Áp Dụng

- Soạn thảo **quy chuẩn kỹ thuật**, **luận văn/bài báo khoa học**, **hướng dẫn vận hành chi tiết** (> 10 trang hoặc > 2.000 từ).
- Yêu cầu phân tích chi tiết, mở rộng luận điểm chuyên sâu, tuyệt đối không tóm tắt giản lược.
- Đầu ra của mô hình thường xuyên bị nghẽn (cutoff) hoặc thu hẹp dung lượng ở các mục sau.

---

## 2. Quy Trình Soạn Thảo Đa Nhịp (Chain of Continuation Workflow)

### Bước 1: Xây dựng Đề cương Chi tiết & Phân đoạn (Macro Outline)
Xây dựng cây cấu trúc phân đoạn rõ ràng trước khi viết chi tiết:
- Phân rã bài viết thành các phần độc lập (Mở đầu, Tổng quan lý thuyết, Phương pháp, Phân tích thực nghiệm, Thảo luận, Kết luận).
- Xác định mục tiêu độ dài và các luận điểm chính cho từng phần.

### Bước 2: Sinh Nội Dung Từng Phân Đoạn (Rolling Context Generation)
Tận dụng AI Gateway (`ccba-ai`) hoặc điều phối nhận thức đa lượt của Agent để viết từng phần tuần tự:
- **Rolling Transition Context:** Mỗi khi bắt đầu một phân đoạn mới, cung cấp 1-2 đoạn văn cuối của phân đoạn trước để duy trì tính liền mạch của văn phong và mạch lập luận.
- **Strict Anti-Summarization Directive:** Kèm chỉ dẫn: *"Triển khai chi tiết từng luận cứ, đưa ra số liệu/dẫn chứng cụ thể, không tóm tắt, không nhảy bước."*

```python
from ccba_ai import ai

# Ví dụ điều phối qua AI Gateway
prompt = f"""
[ĐỀ CƯƠNG BÀI VIẾT]: ...
[NGỮ CẢNH PHÂN ĐOẠN TRƯỚC]: {last_paragraphs}
[NHIỆM VỤ HIỆN TẠI]: Viết chi tiết Phân đoạn 3: Phương pháp nghiên cứu.
Yêu cầu: Viết toàn văn không rút gọn, chi tiết các bước thực nghiệm.
"""
chunk = ai.chat(prompt)
```

### Bước 3: Hợp Nhất & Kiểm Soát Tính Nhất Quán
- Ghép nối các phân đoạn vào tệp Markdown tổng hợp (`.md`).
- Chuyển đổi định dạng sang `.docx` chuẩn hành chính thông qua gói `ccba_ooxml` khi cần xuất bản ấn phẩm hoàn chỉnh.
- Rà soát độ nhất quán về thuật ngữ và văn phong trước khi nghiệm thu.
