# CCBA Runtime Debugging & Diagnostics — Dynamic Rule

## 1. Dev Server Logs (Log của máy chủ phát triển)
Toàn bộ đầu ra log của dev server đang chạy được ghi nhận tại tệp tin cục bộ `.md/scratch/logs/dev_server.log` (tệp tin này chỉ xuất hiện khi dev server được chạy và xuất log).

## 2. Quy tắc đọc log
Khi người dùng báo cáo lỗi runtime, crash ứng dụng, hoặc hành vi không mong muốn khi đang chạy thử nghiệm, Agent **bắt buộc** phải đọc tệp tin log này. Để tránh quá tải token ngữ cảnh, Agent chỉ được đọc tối đa 200 dòng cuối cùng của tệp tin này bằng cách chỉ định các tham số dòng thích hợp trong công cụ đọc file.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
