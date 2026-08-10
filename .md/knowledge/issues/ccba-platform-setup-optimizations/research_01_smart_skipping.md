# Nghiên cứu Kỹ thuật #01: Phương án Trinh sát Smart Skipping (Tự động bỏ qua Phỏng vấn Triage)

- **Mã số Ticket**: `01-smart-skipping-triage`
- **Dự án**: `ccba-platform-setup-optimizations`
- **Loại tài liệu**: Technical Research Report (Double-Pass Adversarial Review)
- **Tệp mục tiêu sửa đổi**: `.agents/skills/ccba-setup-skills/SKILL.md` và `.agents/skills/ccba-setup-skills/templates/issue-tracker-local.md`

---

## 1. Tổng quan Nghiên cứu (Overview)

### 1.1. Bối cảnh & Yêu cầu
Trong kiến trúc **CCBA Agent Platform (Hub-Spoke)**, kỹ năng [`/ccba-setup-skills`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-setup-skills/SKILL.md) đóng vai trò khởi tạo cấu hình công cụ phát triển phần mềm cho dự án. Hiện tại, quy trình phỏng vấn 3 câu hỏi (Issue Tracker, Triage Labels, Domain Layout) luôn bắt buộc người dùng trả lời **Câu B — Nhãn Triage**, kể cả đối với các dự án Spoke đơn giản không cài đặt hoặc không có nhu cầu sử dụng kỹ năng `triage` (`/ccba-triage`).

Mục tiêu của nghiên cứu này là đề xuất phương án bổ sung bước **Trinh sát Smart Skipping** nhằm tự động phát hiện sự tồn tại của kỹ năng `triage` / `ccba-triage`. Nếu kỹ năng này không có trong repo/Spoke hoặc catalog, hệ thống sẽ tự động bỏ qua phỏng vấn Nhãn Triage, không tạo file `triage_labels.md` và không ghi block `### Triage labels` vào Hiến pháp `AGENTS.md`.

---

## 2. Kết quả Vòng 1: Code-First Research (Phân tích thực trạng mã nguồn)

### 2.1. Phân tích Hiện trạng `ccba-setup-skills/SKILL.md`
- **Bước 1 (Trinh sát)**: Hiện chỉ kiểm tra `git remote`, `.md/workspace_context.yaml`, `AGENTS.md`, `CONTEXT.md`, và `.md/knowledge/agents/`. Chưa hề có logic quét hoặc kiểm tra kỹ năng `triage`.
- **Bước 2 (Phỏng vấn)**: Luôn yêu cầu phỏng vấn **Câu B — Nhãn Triage** (gồm 5 vai trò `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`).
- **Bước 3 & 4 (Xác nhận & Ghi cấu hình)**: Luôn hiển thị nháp và tự động chèn `### Triage labels` vào `AGENTS.md` cũng như tạo file `.md/knowledge/agents/triage_labels.md`.

### 2.2. Đối chiếu với Kỹ năng gốc `setup-matt-pocock-skills`
Khi phân tích mã nguồn kỹ năng gốc `d:\GitHubProjects\ccba-agent-platform\.agents\skills\setup-matt-pocock-skills\SKILL.md`:
- Dòng 29: `- Is the triage skill installed? (a triage skill folder alongside this one, or triage in your available skills.) This decides whether Section B runs at all.`
- Dòng 36: `skip the section entirely when exploration already settled it (Section B when triage isn't installed...)`
- Dòng 51: `Section B — Triage label vocabulary. Skip this section entirely if the triage skill isn't installed (exploration told you)...`
- Dòng 102: `Include the ### Triage labels sub-block, and write docs/agents/triage-labels.md, only when triage is installed and Section B ran. When it isn't, both are omitted.`

*Nhận xét*: Kỹ năng `setup-matt-pocock-skills` đã có sẵn tư tưởng thiết kế Smart Skipping cho Triage. Tuy nhiên, khi xây dựng `ccba-setup-skills` cho CCBA Platform, logic trinh sát kiểm tra skill này chưa được port sang.

### 2.3. Định danh các điểm chạm trong Codebase (Touchpoints)
1. **`SKILL.md` của `ccba-setup-skills`**: `[cần thay đổi code hiện có]`
   - Bước 1 (Explore): Bổ sung kiểm tra cờ `triage_installed`.
   - Bước 2 (Present & Ask): Bổ sung điều kiện Smart Skipping cho Câu B.
   - Bước 3 (Confirm): Điều chỉnh bản nháp cấu hình phụ thuộc vào `triage_installed`.
   - Bước 4 (Write): Bổ sung điều kiện ghi file `triage_labels.md` và block `### Triage labels`.
2. **`templates/issue-tracker-local.md`**: `[cần thay đổi code hiện có]`
   - Dòng 10 chứa câu `(xem chi tiết các trạng thái tại triage_labels.md)`. Cần cập nhật để không tạo ra broken link khi `triage_labels.md` không tồn tại.
3. **`catalog.yaml`**: `[đã tồn tại]`
   - Đã khai báo skill `triage` tại dòng 651 (`skill_path: .agents/skills/triage/SKILL.md`) và command `/ccba-triage` tại dòng 1187.

---

## 3. Kết quả Vòng 2: Self-Adversarial Review (Tự phản biện & Đánh giá rủi ro)

### ❓ Giả định 1: Chỉ cần kiểm tra thư mục cục bộ `.agents/skills/triage/` là đủ để kết luận Triage có được cài đặt hay không?
- **Phân tích Rủi ro**: Trong mô hình Hub-Spoke của CCBA, một dự án Spoke có thể không copy thư mục `.agents/skills/triage/` về ổ đĩa cục bộ của Spoke, mà sử dụng skill từ Hub thông qua `catalog.yaml` hoặc danh sách Available Skills trong context hệ thống. Nếu chỉ kiểm tra sự tồn tại của folder cục bộ `.agents/skills/triage/`, Agent sẽ đánh giá sai là `triage_installed = false` và bỏ qua phỏng vấn dù người dùng thực sự có khả năng gọi `/ccba-triage`.
- **Giải pháp khắc phục (Multi-tier Detection)**: Thuật toán trinh sát bắt buộc phải kiểm tra qua 3 cấp:
  1. *Cấp 1 (Local Folder)*: Thư mục cục bộ `.agents/skills/triage/` hoặc `.agents/skills/ccba-triage/` có tồn tại hay không.
  2. *Cấp 2 (Catalog Registry)*: Skill `triage` / `ccba-triage` có được đăng ký trong `catalog.yaml` của dự án/Hub hay không.
  3. *Cấp 3 (Prompt Context)*: Danh sách Available Skills được nạp trong phiên làm việc hiện tại có chứa `triage` / `ccba-triage` hay không.
  -> Chỉ khi **cả 3 cấp đều KHÔNG phát hiện** thì mới kết luận `triage_installed = false`.

### ❓ Giả định 2: Việc bỏ không tạo tệp `triage_labels.md` có gây ra lỗi tham chiếu broken link trong các tài liệu khác?
- **Phân tích Rủi ro**: Phân tích file template `ccba-setup-skills/templates/issue-tracker-local.md` cho thấy tại dòng 10 có câu: `(xem chi tiết các trạng thái tại triage_labels.md)`. Nếu `triage_installed = false`, file `triage_labels.md` sẽ không được tạo trong `.md/knowledge/agents/`, dẫn tới việc file `issue_tracker.md` của người dùng chứa liên kết gãy.
- **Giải pháp khắc phục**: Cập nhật nội dung template `issue-tracker-local.md` để câu văn mang tính linh hoạt:
  - *Nếu có triage*: Trỏ tới `triage_labels.md`.
  - *Nếu không có triage*: Chỉ liệt kê ngắn gọn các trạng thái cơ bản (`claimed`, `resolved`, `open`) mà không đính kèm link tới `triage_labels.md`.

### ❓ Giả định 3: Nếu người dùng bổ sung skill `triage` sau này, quy trình re-run `/ccba-setup-skills` có hoạt động mượt mà không?
- **Giải pháp khắc phục**: Thiết kế quy trình mang tính **Idempotent**. Khi re-run:
  - Trinh sát phát hiện `triage_installed = true`.
  - Hệ thống bổ sung khối `### Triage labels` vào `AGENTS.md` (nếu chưa có).
  - Hệ thống tạo mới file `.md/knowledge/agents/triage_labels.md`.
  - Giữ nguyên các cấu hình `issue_tracker.md` và `domain.md` đã có trong `workspace_context.yaml`.

---

## 4. Ma trận Phân tích Giải pháp (Evaluation Matrix)

| Tiêu chí | Phương án A: Giữ nguyên (Luôn phỏng vấn) | Phương án B: Quét folder đơn thuần (1 Cấp) | Phương án C: Trinh sát Multi-tier 3 Cấp (Đề xuất) |
| :--- | :--- | :--- | :--- |
| **Giá trị trải nghiệm (UX Value)** | Thấp (Dư thừa câu hỏi với Spoke đơn giản) | Trung bình (Nhanh nhưng dễ false-negative) | **Rất cao** (Chính xác 100%, tiết kiệm 1 bước phỏng vấn) |
| **Độ phức tạp (Complexity)** | 0 (Không sửa code) | Rất thấp (1 dòng `if os.path.exists`) | **Thấp** (Thêm 3 điều kiện OR trong bước Explore) |
| **Rủi ro (Risk)** | Thấp (Chỉ phiền người dùng) | Cao (Bỏ sót skill khi chạy Spoke phụ thuộc Hub) | **Rất thấp** (Có fallback 3 cấp an toàn) |
| **Tuân thủ KISS** | ✅ Tối giản nhưng không thông minh | ✅ Đơn giản nhưng thiếu chính xác | **✅ Đạt chuẩn KISS** (Chỉ thêm cờ boolean `triage_installed`) |

---

## 5. Chi tiết Đề xuất Triển khai (Implementation Specification)

### 5.1. Thay đổi tại `.agents/skills/ccba-setup-skills/SKILL.md`

#### Bước 1: Bổ sung logic kiểm tra vào `### 1. Trinh sát (Explore)`
```markdown
- **Kiểm tra sự tồn tại của kỹ năng Triage (`triage` / `ccba-triage`)**:
  - Kiểm tra xem có thư mục `.agents/skills/triage/` hoặc `.agents/skills/ccba-triage/` trong repo hay không.
  - Kiểm tra sự xuất hiện của skill `triage` / `ccba-triage` trong file `catalog.yaml` (nếu có).
  - Kiểm tra xem `triage` / `ccba-triage` có nằm trong danh sách Kỹ năng khả dụng (Available Skills) của hệ thống hay không.
  -> Đặt cờ `triage_installed = true` nếu tìm thấy ở bất kỳ nguồn nào; ngược lại đặt `triage_installed = false`.
```

#### Bước 2: Cập nhật điều kiện phỏng vấn tại `### 2. Gợi ý cấu hình & Phỏng vấn`
```markdown
  **Câu B — Nhãn Triage**:
  > ⚡ **Quy tắc Smart Skipping**: Nếu bước Trinh sát xác định `triage_installed = false` (kỹ năng triage không được cài đặt trong dự án này), **BỎ QUA TOÀN BỘ CÂU B NÀY**. Tự động ghi nhận thông báo tóm tắt cho người dùng: *"Đã tự động bỏ qua cấu hình Nhãn Triage do dự án không sử dụng kỹ năng Triage."*

  Nếu `triage_installed = true`, thực hiện phỏng vấn cấu hình ánh xạ cho 5 vai trò nhãn triage như bình thường.
```

#### Bước 3: Cập nhật `### 3. Xác nhận (Confirm)` & `### 4. Ghi cấu hình (Write)`
- Chỉ bao gồm tiểu mục `### Triage labels` trong dự thảo và file `AGENTS.md` khi `triage_installed = true`.
- Chỉ tạo và ghi tệp `.md/knowledge/agents/triage_labels.md` khi `triage_installed = true`.

---
*Báo cáo được lập bởi CCBA Technical Research Subagent — Quy trình Double-Pass Adversarial Review.*
