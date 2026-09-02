---
description: Tạo feature branch mới với quy trình lập kế hoạch và phân tách session sạch (Factory Model)
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-new-feature
triggers:
- new feature
- feature mới
- tạo branch
---
# Workflow: Tạo Feature Branch Mới & Phân Tách Session (Factory Model)

Quy trình tự động hóa dọn dẹp các branch cũ, khởi tạo branch tính năng mới và cưỡng chế áp dụng mô hình Nhà máy (**The Factory Model**) tách biệt giữa **Planning** và **Coding** để tối ưu hóa chi phí Token (OpEx) và ngăn ngừa lỗi mã nguồn.

## Các bước thực hiện:

### Bước 1: Chuẩn bị môi trường & Pre-Flight Check
1. **Kiểm tra trạng thái Working Tree:**
   ```bash
   git status --short
   ```
   *Nếu có uncommitted changes dở dang, yêu cầu `git commit` hoặc `git stash` trước khi chuyển nhánh.*
2. **Quay về branch `main` và kéo code mới nhất:**
   ```bash
   git checkout main && git pull origin main
   ```

### Bước 2: Dọn dẹp các branch cũ đã merge
Dọn dẹp các branch cục bộ đã được tích hợp vào `main` (hỗ trợ cả merge thông thường và dọn dẹp prune):
- **Windows PowerShell:**
  ```powershell
  git fetch -p
  git branch --merged main | Where-Object { $_ -notmatch 'main' -and $_ -notmatch '^\*' } | ForEach-Object { git branch -d $_.Trim() }
  ```
- **Bash (Linux / macOS / Git Bash):**
  ```bash
  git fetch -p
  git branch --merged main | grep -vE '^\*|main$' | xargs -r git branch -d
  ```

### Bước 3: Thu thập thông tin & Bóc tách Issue tự động (Hỗ trợ Offline Fallback)
- **Trường hợp 1 (Có mã Issue, ví dụ `/ccba-new-feature #228`):**
  1. Agent ưu tiên gọi GitHub CLI để trích xuất thông tin:
     ```bash
     gh issue view <issue_id> --json title,body,labels
     ```
  2. **Offline / Local Fallback:** Nếu mất mạng hoặc `gh` chưa đăng nhập, Agent tự động đọc tệp cục bộ `.md/knowledge/issues/issue-<issue_id>.md`.
  3. **Nhận diện tự động:**
     - Tự động nhận diện loại công việc từ tiêu đề hoặc labels: `feat(...)` $\rightarrow$ `feat`, `fix(...)` $\rightarrow$ `fix`, `docs(...)` $\rightarrow$ `docs`, `refactor(...)` $\rightarrow$ `refactor`.
     - Tự động trích xuất nội dung **Agent Brief** (nếu đã qua `/ccba-triage`) để chuyển thẳng sang Bước 6.
     - Tự động đề xuất tên branch ở Bước 4 mà **không cần hỏi lại người dùng**.
- **Trường hợp 2 (Không cung cấp mã Issue):**
  Hỏi người dùng lần lượt các thông tin:
  1. Loại công việc cần thực hiện: `feat` (tính năng mới), `fix` (sửa lỗi), `docs` (tài liệu), `refactor` (cải tiến cấu trúc), hoặc `experiment` (thử nghiệm).
  2. Mô tả ngắn gọn tính năng (3-5 từ).

### Bước 4: Đề xuất tên branch chuẩn định danh
Dựa trên thông tin thu thập được, đề xuất tên branch theo định dạng chuẩn CCBA có gắn mã Issue:
- `feat/issue-<id>-<ten-ngan-gon>` (hoặc `feat/<ten-tinh-nang>` nếu không có issue)
- `fix/issue-<id>-<ten-loi>` (hoặc `fix/<ten-loi>` nếu không có issue)
- `docs/issue-<id>-<ten-tai-lieu>`
- `refactor/issue-<id>-<ten-module>`
- `experiment/<ten-thu-nghiem>`

*Quy tắc đặt tên branch:* Viết thường hoàn toàn (lowercase), sử dụng dấu gạch ngang `-` thay cho khoảng trắng, ngắn gọn, có thể truy vết ngược về Issue.

### Bước 5: Khởi tạo branch mới
Sau khi chốt tên branch, tạo và chuyển sang branch mới:
```bash
git checkout -b [ten_branch_da_chot]
```

### Bước 6: Lập kế hoạch thiết kế (Planning Phase — Triage Fast-Path & Socrates Grill)
Agent **bắt buộc** phải chuyển sang **Planning Mode**, tuyệt đối không được viết code ở bước này:
1. **Triage Fast-Path (Smart Skipping):**
   - Nếu Issue đã có sẵn **Agent Brief** chuẩn từ `/ccba-triage`: Agent tự động nạp yêu cầu, bỏ qua các câu hỏi phỏng vấn cơ bản và chỉ chất vấn 1-2 câu kiến trúc cốt lõi nếu thực sự cần thiết.
   - Nếu chưa có Agent Brief: Kích hoạt `/ccba-grilling` để phỏng vấn người dùng và stress-test các giả định.
2. **Soạn thảo Kế hoạch Triển khai (`implementation_plan.md`):**
   - Bắt buộc có mục `## Đánh giá khả năng tái sử dụng (Reuse Assessment)` tra cứu `catalog.yaml` (ADR 0047).
   - Xác định rõ các Deep Seams (khớp nối) và Scoped Verification Plan.
3. **Phê duyệt:** Đợi người dùng nhấn **Proceed** phê duyệt bản kế hoạch.

### Bước 7: Bàn giao cô lập ngữ cảnh (Factory Model Hand-off & Smart Routing)
Sau khi bản kế hoạch được duyệt, để ngăn ngừa phình to ngữ cảnh hội thoại (Context Rot) và giảm OpEx:
- **Định tuyến thực thi (Execution Routing):** Đọc khuyến nghị từ Agent Brief:
  - 🟢 **Standard** (`/ccba-implement`): Mở session chat mới sạch sẽ và gọi `/ccba-implement`.
  - 🟣 **Deep Reasoning** (`/boost`): Kích hoạt điều tra chuyên sâu cho logic thuật toán phức tạp.
  - 🔵 **Multi-Agent Orchestration** (`/ccba-teamwork` hoặc `invoke_subagent`): Phân rã Seams và chạy đa tác nhân song song.

### Bước 8: Lập trình, Kiểm chứng & Tự sửa lỗi (Coding & Verification Phase)
Coding Agent thực hiện nhiệm vụ:
1. Khởi tạo danh mục theo dõi `task.md`.
2. Viết mã nguồn tương thích, áp dụng type hints và docstring chuẩn Google/CCBA.
3. **Thực thi Cổng Kiểm định Tự động (Automation-First Quality Gates):**
   - `python scripts/safe_pytest.py -f tests/test_xxx.py` (chạy scoped test an toàn).
   - `ruff check packages/ scripts/ tests/` (linter & format).
   - `mypy packages/ scripts/` (static type checker).
   - `python scripts/spoke/check_hub_import_depth.py` & `check_spoke_cleanliness.py` (ADR 0044).
   - `python scripts/eval/run_harness_evals.py` (hoặc `/ccba-eval-gate`).
4. Nếu phát hiện linter hoặc type check báo lỗi, tự động kích hoạt **Self-Healing Loop** tối đa 3 lần.
5. Khi tất cả các Gates đều vượt qua thành công (PASS), bàn giao kết quả qua tệp `walkthrough.md` cho người dùng nghiệm thu trước khi tạo PR (`/ccba-create-pr`).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
