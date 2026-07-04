---
name: architecture-sync
description: "Đồng bộ hóa toàn bộ tài liệu kiến trúc (AGENTS.md, GEMINI.md, README.md) sau khi refactor codebase."
---

# Tên Workflow: Architecture Sync

**Workflow này được gọi khi User yêu cầu:** "Đồng bộ kiến trúc", "Cập nhật tài liệu kiến trúc", hoặc dùng trigger `@AI: /architecture-sync`.

## Mục đích
Khi một dự án vừa trải qua đợt refactor cấu trúc thư mục, module code, hoặc thay đổi thiết kế hệ thống, AI Agent cần tự động quét lại toàn bộ codebase và cập nhật các file "Hiến pháp" (Constitution) để tránh sinh ra code/rác không tương thích ở các phiên làm việc sau.

## Quy trình thực hiện (Dành cho AI Agent)

Khi được gọi bằng Workflow này, AI Agent **BẮT BUỘC** phải thực hiện trình tự sau:

### Bước 1: Khảo sát Codebase Mới
- Không sử dụng kiến thức cũ. Sử dụng công cụ `list_dir` hoặc lệnh Terminal (như `dir /s /b AGENTS.md GEMINI.md README.md` trên Windows) để quét **TOÀN BỘ CÂY THƯ MỤC** hiện hành.
- **Lưu ý quan trọng**: Tuyệt đối không chỉ tìm ở thư mục gốc (Root). Rất nhiều dự án có các file context nằm ẩn bên trong các thư mục con (Ví dụ: `scripts/GEMINI.md` hoặc `scripts/README.md`). Bạn phải tìm ra **tất cả** các bản sao của chúng.
- Phân tích ngắn gọn (trong suy nghĩ hoặc báo cáo cho User) về sự thay đổi của cấu trúc file, sự phân chia module mới, các dependency mới.

### Bước 2: Cập nhật "Hiến pháp" & Context Files
Bạn phải chỉnh sửa/ghi đè **TẤT CẢ** các file đã tìm thấy ở Bước 1 để chúng phản ánh đúng 100% codebase mới:
1. **`AGENTS.md` (nếu có)**: Cập nhật sơ đồ thư mục (Directory Structure), quy tắc viết file (YAML schemas), và các mode hoạt động.
2. **`GEMINI.md` / `COPILOT.md`**: Cập nhật Model Routing (model nào xử lý việc gì) và cấu trúc thư mục để Agent có context chuẩn khi mở bằng CLI. Lưu ý cập nhật cả file ở root và file ở các thư mục con (nếu có).
3. **`README.md`**: Cập nhật Architecture Overview, Pipeline Flow (nếu có vẽ Mermaid), và cách chạy các script khởi động. Nhớ cập nhật tất cả README tìm thấy.

### Bước 3: Lưu trữ Knowledge Item (KI)
- Tạo một artifact (ví dụ: `walkthrough.md` hoặc `architecture_summary.md`) tóm tắt những gì vừa cập nhật.
- File này sẽ được hệ thống biến thành **Persistent Knowledge Item**, giúp các phiên làm việc sau (New Sessions) nhớ được trạng thái kiến trúc hiện tại mà không bị ảo giác (hallucination).

## Báo cáo kết quả
Sau khi hoàn thành 3 bước trên, trả lời cho User biết:
- File nào đã được cập nhật.
- Những module/thành phần kiến trúc chính nào được ghi nhận vào hệ thống.
- Xác nhận rằng các phiên làm việc sau đã an toàn.
