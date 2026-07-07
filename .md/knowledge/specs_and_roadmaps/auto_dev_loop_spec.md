# Đặc tả Kiến trúc Thiết kế: Vòng lặp phát triển tự động (Auto-Dev Loop)

Tài liệu này lưu trữ các quyết định thiết kế kỹ thuật đã được thống nhất thông qua phiên phản biện (`grilling`) ngày 02/07/2026. Thiết kế này hướng tới việc tự động hóa hoàn toàn quy trình đóng gói mã nguồn tiện ích thành AI Agent Skill chính thức trên CCBA Platform.

---

## 1. Nguyên tắc cốt lõi & Single Source of Truth (SSOT)

Để tránh vi phạm nguyên tắc SSOT và giảm thiểu việc nhân bản thông tin, cấu trúc tài liệu được phân tách rõ ràng làm hai phần độc lập:

1.  **`SKILL.md` (Viết tay thủ công - Source of Truth):**
    *   Chỉ chứa các chỉ dẫn nghiệp vụ, usecases, tài liệu mô tả do con người viết hoặc do LLM tự suy luận (infer) tại thời điểm khởi tạo ban đầu.
    *   Chứa hướng dẫn quy trình tương tác chuẩn hóa: Validate tham số đầu vào -> Chạy quét bảo mật Maskara -> Thực thi terminal -> QC kết quả bằng `validate_docs.py`.
2.  **`cli_spec.yaml` (Tự động sinh 100%):**
    *   Chứa toàn bộ đặc tả kỹ thuật của các tham số CLI dòng lệnh.
    *   Được đồng bộ và cập nhật tự động bằng code phân tích tự động.
    *   **Vị trí lưu trữ:** Nằm cùng cấp trong thư mục của Skill tương ứng (theo nguyên lý đóng gói cục bộ - Locality).

---

## 2. Đặc tả Kỹ thuật của `cli_spec.yaml` (MCP-Ready JSON Schema)

Tệp tin `cli_spec.yaml` sử dụng định dạng YAML nhưng cấu trúc các tham số đầu vào tuân thủ 100% đặc tả **JSON Schema** của MCP Tools. Điều này giúp platform sẵn sàng chuyển dịch các CLI scripts thành MCP Tools trong tương lai mà không cần thay đổi cấu trúc dữ liệu.

### Cấu trúc mẫu của `cli_spec.yaml`:
```yaml
commands:
  quiz:
    command_base: "python scripts/notebooklm_helper.py quiz"
    input_schema:
      type: "object"
      properties:
        source:
          type: "string"
          description: "Đường dẫn file hoặc URL đầu vào"
        quantity:
          type: "string"
          enum: ["fewer", "standard"]
          default: "standard"
          description: "Số lượng câu hỏi cần sinh"
      required:
        - source
  slides:
    command_base: "python scripts/notebooklm_helper.py slides"
    input_schema:
      type: "object"
      properties:
        source:
          type: "string"
          description: "Tài liệu nguồn"
        language:
          type: "string"
          default: "en"
      required:
        - source
```

---

## 3. Cơ chế Tự động hóa & Phân tích Động (Dynamic Inspection)

Tác vụ tự động hóa đồng bộ (thông qua subcommand `python scripts/notebooklm_helper.py sync-skills` hoặc Git hook) hoạt động theo cơ chế:

1.  **Suy luận nghiệp vụ ban đầu (Initial Inference):**
    *   Khi tạo mới một Skill, Agent sẽ đọc kết hợp Module Docstring của Python script + phân tích cây cú pháp AST của các hàm chính.
    *   Gửi thông tin này qua `ccba-ai` để LLM tự suy luận mục đích nghiệp vụ và viết nháp file `SKILL.md` ban đầu.
2.  **Đồng bộ tham số kỹ thuật tự động (Automatic CLI Sync):**
    *   Khi chạy lệnh `sync-skills`, hệ thống sẽ import trực tiếp các module Python vào bộ nhớ (Runtime Import).
    *   Quét và duyệt qua các đối tượng Parser thực tế của thư viện CLI (như duyệt `parser._actions` trong `argparse` hoặc `cli.params` trong `click`).
    *   Tự động sinh ra cấu trúc `cli_spec.yaml` chính xác 100% so với mã nguồn thực tế mà không lo lỗi cú pháp định dạng tĩnh.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
