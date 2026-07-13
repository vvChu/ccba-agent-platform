---
name: ccba-setup-skills
description: Thiết lập cấu hình dự án (Spoke/Hub) cho các công cụ kỹ thuật — cấu hình issue tracker, nhãn phân loại (triage), và bố cục tài liệu tri thức (Domain Docs). Chạy một lần trước khi sử dụng các kỹ năng phát triển phần mềm.
disable-model-invocation: true
---

# Kỹ năng Thiết Lập Cấu Hình Phát Triển (Setup CCBA Skills)

Dựng khung cấu hình cho repository hiện tại để các kỹ năng phát triển phần mềm khác (`triage`, `to-tickets`, `to-spec`, `tdd`, `improve-codebase-architecture`, v.v.) hoạt động chính xác:

- **Issue tracker** — Nơi theo dõi công việc (GitHub, GitLab, hoặc Local Markdown lưu offline).
- **Triage labels** — Từ vựng nhãn tương ứng với 5 vai trò trạng thái của triage.
- **Domain docs** — Cấu trúc tài liệu miền tri thức (`CONTEXT.md` và ADRs).

Đây là kỹ năng tương tác và tự động hóa. Agent sẽ trinh sát trước, đưa ra gợi ý, xác nhận với người dùng rồi tiến hành ghi cấu hình.

---

## Quy trình thực hiện (Process)

### 1. Trinh sát (Explore)

Quét dự án hiện tại để nhận diện trạng thái ban đầu:
- Chạy lệnh `git remote get-url origin` hoặc `git remote -v` để nhận diện repo có sử dụng GitHub, GitLab hay không.
- Đọc file `.md/workspace_context.yaml` tại thư mục gốc để xem đã có cấu hình `issue_tracker` hoặc các cấu hình khác chưa.
- Kiểm tra sự tồn tại của file hiến pháp `.agents/AGENTS.md` hoặc `AGENTS.md`.
- Kiểm tra sự tồn tại của `CONTEXT.md` / `CONTEXT-MAP.md` ở thư mục gốc hoặc `.md/knowledge/`.
- Kiểm tra sự tồn tại của thư mục cấu hình đích `.md/knowledge/agents/`.

### 2. Gợi ý cấu hình & Phỏng vấn (Present findings and ask)

Tóm tắt kết quả trinh sát và đưa ra cấu hình đề xuất cho người dùng:
- **Nếu đã có cấu hình trong `workspace_context.yaml`**: Hiển thị cấu hình hiện tại và hỏi người dùng có muốn thay đổi không. Nếu không, đề xuất dùng tiếp cấu hình này (bỏ qua phỏng vấn từng bước).
- **Nếu chưa có cấu hình**: Hỏi người dùng từng quyết định một (one-by-one):

  **Câu A — Issue tracker**:
  Giải thích: Đây là nơi theo dõi task/bug. Lựa chọn:
  - **GitHub** — Sử dụng GitHub Issues (yêu cầu `gh` CLI). Tự động đề xuất nếu git remote là github.com.
  - **GitLab** — Sử dụng GitLab Issues (yêu cầu `glab` CLI). Tự động đề xuất nếu git remote là gitlab.com.
  - **Local markdown** — Lưu issue thành các file md dưới `.md/knowledge/issues/` (phù hợp chạy offline hoặc dự án solo).
  - **Khác** — Nhận mô tả quy trình dạng văn bản tự do từ người dùng.
  
  Nếu chọn GitHub/GitLab, hỏi thêm:
  - *Xem PR như yêu cầu tính năng?* (yes / no - Mặc định: no). Nếu yes, `/triage` sẽ quét cả PR của cộng tác viên ngoài để xếp hàng phân loại.

  **Câu B — Nhãn Triage**:
  Cấu hình ánh xạ cho 5 vai trò nhãn triage:
  - `needs-triage` (Cần đánh giá)
  - `needs-info` (Cần thông tin)
  - `ready-for-agent` (Sẵn sàng cho Agent)
  - `ready-for-human` (Cần lập trình viên xử lý)
  - `wontfix` (Từ chối/Không làm)
  (Mặc định: Giữ nguyên tên vai trò làm nhãn. Hỏi người dùng xem có muốn ghi đè nhãn nào theo thói quen cũ của repo không).

  **Câu C — Cấu trúc tài liệu miền (Domain layout)**:
  Xác định cấu trúc lưu trữ tri thức:
  - **Single-context** — Chỉ có 1 file `CONTEXT.md` và `docs/adr/` ở root (phù hợp với hầu hết dự án).
  - **Multi-context** — Có file `CONTEXT-MAP.md` dẫn tới nhiều folder con chứa `CONTEXT.md` riêng (phù hợp monorepo).

### 3. Xác nhận (Confirm)

Hiển thị cho người dùng xem bản nháp của:
- Khối cấu hình `## Agent skills` sẽ được ghi vào file `.agents/AGENTS.md` (hoặc `AGENTS.md` ở root).
- Nội dung chi tiết của các file sẽ được tạo ra tại `.md/knowledge/agents/`:
  - `issue_tracker.md`
  - `triage_labels.md`
  - `domain.md`

### 4. Ghi cấu hình (Write)

**Bước A: Cập nhật Hiến pháp**:
- Xác định file ghi hiến pháp: Ưu tiên `.agents/AGENTS.md`, sau đó đến `AGENTS.md` ở root.
- Cập nhật (hoặc thêm mới) block `## Agent skills` vào file đó mà không làm mất các quy định khác:
  ```markdown
  ## Agent skills

  ### Issue tracker

  [Tóm tắt ngắn gọn tracker và trạng thái PR]. Xem `.md/knowledge/agents/issue_tracker.md`.

  ### Triage labels

  [Tóm tắt ngắn gọn nhãn triage]. Xem `.md/knowledge/agents/triage_labels.md`.

  ### Domain docs

  [Tóm tắt ngắn gọn bố cục]. Xem `.md/knowledge/agents/domain.md`.
  ```

**Bước B: Cập nhật `workspace_context.yaml`**:
- Ghi nhận hoặc cập nhật trường `project.issue_tracker` trong file `.md/workspace_context.yaml` (ví dụ: `github`, `gitlab` hoặc `local_markdown`).

**Bước C: Tạo các file chỉ dẫn chi tiết**:
Tạo thư mục `.md/knowledge/agents/` (nếu chưa có) và ghi 3 file cấu hình chi tiết từ các file template tương ứng của skill:
- Hướng dẫn Issue Tracker: Lấy từ `issue-tracker-github.md`, `issue-tracker-gitlab.md`, hoặc `issue-tracker-local.md`.
- Hướng dẫn nhãn Triage: Lấy từ `triage-labels.md`.
- Hướng dẫn Domain: Lấy từ `domain.md`.

### 5. Hoàn tất (Done)

Thông báo cho người dùng việc thiết lập đã hoàn thành. Nhắc nhở người dùng rằng họ có thể chỉnh sửa trực tiếp các file trong `.md/knowledge/agents/` sau này để thay đổi cấu hình, không cần chạy lại lệnh setup trừ khi muốn thay đổi hoàn toàn Issue Tracker.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
