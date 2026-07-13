# ADR 0020: Quyết định Port và Địa hóa nhóm Skill Upstream Ưu tiên cao

## Bối cảnh (Context)
Trong phiên làm việc đối chiếu toàn bộ các skill từ thượng nguồn `mattpocock-skills` (ADR 0019), hệ thống đã xác định được 4 skill ưu tiên cao (High Priority) cần thảo luận và thiết lập phương án triển khai thích ứng với hệ sinh thái Python và mô hình quản trị thông tin của CCBA Agent Platform.

Phiên chất vấn Socrates (Grilling Session) đã thống nhất các nguyên tắc triển khai đối với từng thành phần này.

## Quyết định (Decisions)

### 1. Địa hóa `setup-pre-commit` thành Python-based pre-commit
*   **Quyết định:** Không sử dụng Husky + lint-staged + Prettier (Node.js) từ thượng nguồn vì không tương thích hệ sinh thái Python/uv hiện tại của Platform.
*   **Thích ứng:** Xây dựng `setup-pre-commit` trên Hub để tự động cấu hình bộ công cụ `pre-commit` chạy trên Python, bao gồm:
    *   Tự động khởi tạo tệp cấu hình `.pre-commit-config.yaml` tiêu chuẩn CCBA (chạy Ruff, MyPy, PyMarkdown và các custom validators `validate_docs`/`validate_skills`).
    *   Cài đặt và liên kết **Maskara Pre-commit Hook** để rà quét bảo mật mã nguồn trước khi commit.

### 2. Bỏ qua `claude-handoff`
*   **Quyết định:** Bỏ qua việc port skill `claude-handoff` vì lệnh CLI `claude --bg` không khả dụng và không phù hợp với runtime tích hợp của CCBA.
*   **Giải pháp thay thế:** Bảo toàn và tối ưu hóa skill `handoff` hiện có của CCBA (lưu trữ tệp trạng thái offline dạng `.md/scratch/handoffs/handoff-<timestamp>.md`). Các tác vụ nền song song sẽ được quản lý trực tiếp bằng công cụ hệ thống `invoke_subagent`.

### 3. Port tĩnh `setup-ts-deep-modules` về Hub
*   **Quyết định:** Vẫn port skill `setup-ts-deep-modules` từ thượng nguồn về lưu trữ sẵn trên Hub để hỗ trợ các dự án Spoke sau này nếu có viết Frontend bằng TypeScript.
*   **Cách thức:** Lưu trữ tĩnh trên Hub, không kích hoạt mặc định. Nghiên cứu phát triển phiên bản Python (`setup-py-deep-modules` sử dụng `import-linter`) trong tương lai nếu cần thiết.

### 4. Địa hóa `loop-me` thành `ccba-loop-me`
*   **Quyết định:** Địa hóa hoàn toàn hành vi lưu trữ của skill `loop-me` để tuân thủ hiến pháp quản lý thông tin CCBA Rule 1 và Rule 2.
*   **Thích ứng:**
    *   Lưu các ghi chép nghiên cứu thói quen/chu trình làm việc của người dùng vào tệp `.md/knowledge/user_loops.md` (thay vì `NOTES.md` ở root).
    *   Xuất bản đặc tả các workflow được thiết kế vào thư mục `.agents/workflows/` (thay vì `workflows/` ở root) có đầy đủ metadata và hướng dẫn đăng ký tự động vào `catalog.yaml`.

## Hệ quả (Consequences)
*   Đảm bảo tính nhất quán công nghệ (KISS) của CCBA Platform, tránh cài đặt chồng chéo các package manager của Node.js vào các Spoke thuần Python.
*   Bảo vệ sự sạch sẽ của thư mục gốc (Project Root) theo đúng quy tắc Golden Thread của CCBA.
*   Sẵn sàng mở rộng khả năng kiểm định chất lượng mã nguồn cho cả các Spoke viết bằng TypeScript lẫn Python.
