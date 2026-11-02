# ccba-implement-spec — Reference Guide (Task Graph & Frontier Execution)

> **Mục đích & Ngữ cảnh sử dụng:** Điều phối triển khai toàn bộ một đặc tả kỹ thuật (Spec) và đồ thị công việc (Task Graph) trên nhánh tích hợp duy nhất (`integration branch`) thông qua các subagent chạy trong Git worktree cô lập.
> **Nguồn gốc:** Thích ứng từ `implement-spec` (`v1.3.0` / `v1.3.2`) của Matt Pocock (MIT License), địa phương hóa theo **Single-Writer Protocol** và **First-Unit Canary** của CCBA Platform (`COND-01`).

---

## 1. Nguyên Lý Cốt Lõi (Core Principles)

Khi người dùng cung cấp một đặc tả kỹ thuật (Spec) đi kèm tập hợp các đơn vị công việc (Tickets / Issues) từ `/ccba-to-spec` hoặc `/ccba-issue-tree`:

1. **Đồ thị công việc (Task Graph) & Đường biên sẵn sàng (Frontier):**
   - Các tickets không phải là một danh sách phẳng tuần tự mà tạo thành một **Task Graph** với các cạnh phụ thuộc chặn (*blocking relationships*).
   - Tại mọi thời điểm, luôn tồn tại một **Frontier** gồm các tickets đã giải phóng hết điều kiện phụ thuộc và sẵn sàng được thực thi ngay.
2. **Mục tiêu Nhánh Tích Hợp (`integration branch`):**
   - Đích đến của quy trình là toàn bộ Spec được hiện thực hóa hoàn chỉnh trên một **integration branch** duy nhất, và mọi ticket được giải quyết theo đúng quy ước đóng việc của Issue Tracker.
3. **Cửa sổ Ngữ cảnh Mới (`fresh context window`) & Giao tiếp qua Con trỏ Ngữ cảnh (`Context Pointers`):**
   - Khởi chạy mọi subagent với một **fresh context window** (tuyệt đối không fork hội thoại cha làm kế thừa nhiễu ngữ cảnh).
   - Giao tiếp giữa Orchestrator và các subagents phải cực kỳ súc tích, truyền thông tin chủ yếu qua **context pointers** (đường dẫn tới tệp Spec, mã Ticket, ghi chú khảo sát tại `.md/scratch/exploration/`, và mã commit trước đó). Không sao chép lặp lại nội dung đã có sẵn qua con trỏ.
4. **Rào chắn `COND-01` — Single-Writer Protocol & First-Unit Canary:**
   - **Độc quyền Ghi trên Nhánh Tích Hợp (`Single-Writer`):** Chỉ **Orchestrator chính** mới có quyền thực hiện lệnh fast-forward merge và chạy cổng kiểm định `verify-patch` trên `integration branch`. Các **Implementer Subagents** chỉ làm việc trong Git worktree cô lập (`.worktrees/ticket-<id>`) trên nhánh riêng của từng ticket.
   - **Thử nghiệm Đơn vị Đầu tiên (`First-Unit Canary`):** Trước khi quạt mở (fan-out) chạy song song nhiều Implementer Subagents trên Frontier, Orchestrator **bắt buộc chọn 1 ticket đầu tiên làm Canary** và chạy tuần tự trọn vẹn chu trình (`Worktree -> /ccba-tdd -> Rebase/Merge Integration Tip -> Orchestrator Fast-Forward Merge -> verify-patch exit 0`). Chỉ khi Canary thành công với mã thoát 0 mới kích hoạt fan-out song song cho các tickets còn lại trên Frontier.

---

## 2. Quy Trình Thực Hiện 9 Bước (Process)

### Bước 1: Đọc Spec & Dựng Đồ Thị Công Việc (Task Graph & Frontier)
- Đọc tệp Spec và truy xuất danh sách các tickets liên kết từ Issue Tracker (nếu chưa cấu hình Issue Tracker, hướng dẫn người dùng chạy `/ccba-setup-skills`).
- Xác định các cạnh phụ thuộc chặn (*blocked-by*) và liệt kê tập hợp các tickets nằm trên **Frontier** đầu tiên.
- **Tiêu chí hoàn thành:** Sơ đồ phụ thuộc Task Graph và danh sách Frontier ban đầu được xác lập rõ ràng.

### Bước 2: Khảo Sát Dùng Chung (Optional Exploration Subagent)
- Nếu các tickets đòi hỏi khảo sát sâu mã nguồn hoặc tài liệu ngoài, khởi chạy một **Exploration Subagent** (với `fresh context window`) để thu thập dữ kiện.
- Subagent lưu ghi chú Markdown vào thư mục `.md/scratch/exploration/<spec-slug>/` để tất cả Implementer Subagents phía sau truy cập qua *context pointers*, giúp Implementer Subagents tập trung 100% vào viết code.
- **Tiêu chí hoàn thành:** Ghi chú khảo sát (nếu cần) được lưu tại `.md/scratch/exploration/` và có đường dẫn con trỏ rõ ràng.

### Bước 3: Khởi Tạo Nhánh Tích Hợp (`integration branch`)
- Tạo nhánh tích hợp mới từ nhánh gốc (ví dụ: `feat/<spec-slug>-integration`).
- *Lưu ý về Draft PR:* Chỉ mở Draft PR (đánh dấu đóng Spec và các tickets) **sau khi lượt merge đầu tiên ở Bước 5 hoàn tất** (vì nhánh chưa có commit nào vượt trước nhánh chính thì không thể mở PR trên GitHub).
- **Tiêu chí hoàn thành:** Nhánh `integration branch` được tạo sạch sẽ tại local.

### Bước 4: Thực Thi Ticket bằng Implementer Subagent (Canary trước, Fan-out sau)
- Với ticket đầu tiên (**First-Unit Canary**) — và sau khi Canary pass thì áp dụng song song cho các tickets trên **Frontier** — khởi chạy một **Implementer Subagent** mới (`fresh context window`) trong worktree riêng (`.worktrees/ticket-<id>`):
  1. Xác nhận worktree đang dựa trên đầu nhánh `integration branch` hiện tại (reset về `integration branch` nếu lệch).
  2. Triệu hồi quy trình [`/ccba-tdd`](../../ccba-tdd/SKILL.md) để xây dựng ticket theo lát cắt dọc (Red $\to$ Green $\to$ Refactor).
  3. Trước khi báo cáo hoàn tất, subagent kéo và hợp nhất đầu nhánh `integration branch` mới nhất vào nhánh worktree của chính nó, tự giải quyết xung đột cục bộ và chạy kiểm thử xác nhận để đảm bảo Orchestrator có thể hợp nhất dạng fast-forward.
- **Tiêu chí hoàn thành:** Implementer Subagent hoàn thành TDD trên nhánh worktree riêng và đồng bộ sạch sẽ với tip của `integration branch`.

### Bước 5: Hợp Nhất Đơn Điểm Ghi (`Single-Writer` Fast-Forward Merge & Gate)
- Khi một Implementer Subagent báo cáo hoàn tất, **Orchestrator chính** (đóng vai trò `Single-Writer` duy nhất trên `integration branch`) thực hiện:
  1. Hợp nhất (fast-forward merge) nhánh của subagent vào `integration branch`.
  2. Chạy cổng kiểm định máy tính:
     ```bash
     python -m ccba_harness verify-patch --preset code --target <package_or_dir>
     ```
  3. Nếu đây là lượt merge đầu tiên và dự án quản lý qua PR (hoặc người dùng yêu cầu), mở Draft PR từ `integration branch`.
- **Tiêu chí hoàn thành:** Nhánh `integration branch` hợp nhất thành công commit mới và vượt qua `verify-patch` với mã thoát 0.

### Bước 6: Cập Nhật Frontier & Mở Rộng Song Song (Frontier Expansion)
- Khi một ticket được hợp nhất và mở khóa các tickets phụ thuộc phía sau, tính toán lại **Frontier** mới.
- Khởi chạy đợt **Implementer Subagents** tiếp theo cho các tickets vừa mở khóa trên Frontier để tối đa hóa độ song song.
- **Tiêu chí hoàn thành:** Toàn bộ các tickets trong Task Graph lần lượt đi qua Frontier và được hợp nhất vào `integration branch`.

### Bước 7: Rà Soát Mã Nguồn Toàn Nhánh (`/ccba-code-review`)
- Khi tất cả tickets trong Spec đã hợp nhất xong, triệu hồi [`/ccba-code-review`](../../ccba-code-review/SKILL.md) trên toàn bộ diff của `integration branch`.
- Nếu phát hiện lỗi chặn (*Verified Findings*), khởi chạy **1 Implementer Subagent mới (`fresh context window`)** để khắc phục triệt để toàn bộ các điểm lỗi đó và chạy lại `verify-patch`.
- **Tiêu chí hoàn thành:** Nhánh `integration branch` vượt qua `/ccba-code-review` và `verify-patch` không còn lỗi chặn.

### Bước 8: Chốt Trạng Thái PR & Giải Quyết Tickets
- Nếu đã mở Draft PR, chuyển trạng thái sang **Ready for Review**. Nếu không dùng PR, đóng từng ticket theo đúng quy ước của Issue Tracker và báo cáo tên nhánh `integration branch` cho người dùng.
- **Tiêu chí hoàn thành:** Trạng thái PR và toàn bộ tickets thuộc Spec được cập nhật chính xác trên Issue Tracker.

### Bước 9: Dọn Dẹp Worktrees (Worktree Cleanup)
- Xóa toàn bộ các thư mục worktree tạm (`.worktrees/ticket-*`) và nhánh tạm của các Implementer Subagents (`git worktree remove` & `git worktree prune`).
- **Tiêu chí hoàn thành:** Không còn worktree mồ côi nào tồn đọng trong kho lưu trữ.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
