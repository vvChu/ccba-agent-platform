# Công cụ theo dõi công việc: GitHub Issues

Các lỗi (bugs) và yêu cầu tính năng (Specs) của dự án này được theo dõi trên GitHub Issues. Sử dụng công cụ `gh` CLI cho mọi thao tác.

## Các lệnh thao tác tiêu chuẩn (Conventions)

- **Tạo sự cố (Issue)**:
  *Windows PowerShell (pwsh)*:
  ```powershell
  gh issue create --title "Tiêu đề issue" --body "Mô tả chi tiết issue"
  ```
  *(Để nhập mô tả nhiều dòng, hãy ghi mô tả ra file tạm rồi import: `gh issue create --title "Tiêu đề" --body-file temp.txt`)*

- **Đọc sự cố**:
  ```powershell
  gh issue view <number> --comments
  ```

- **Liệt kê sự cố**:
  Sử dụng filter theo nhãn (labels) và trạng thái (state):
  ```powershell
  gh issue list --state open --json number,title,labels
  ```
  Để lấy toàn bộ JSON thô nhằm xử lý logic:
  ```powershell
  gh issue list --state open --json number,title,body,labels,comments
  ```

- **Viết bình luận**:
  ```powershell
  gh issue comment <number> --body "Nội dung bình luận"
  ```

- **Gán / Gỡ nhãn (Labels)**:
  ```powershell
  gh issue edit <number> --add-label "ready-for-agent"
  gh issue edit <number> --remove-label "needs-triage"
  ```

- **Đóng sự cố**:
  ```powershell
  gh issue close <number> --comment "Đã hoàn thành sửa lỗi"
  ```

*Lưu ý: `gh` CLI sẽ tự động nhận diện repository đích dựa trên thông tin Git remote cấu hình trong thư mục hiện tại.*

---

## Quản lý Pull Requests (PRs) như một nguồn yêu cầu

**Xem PR như yêu cầu tính năng: no.** _(Chuyển thành `yes` nếu dự án của bạn chấp nhận PR từ cộng tác viên ngoài gửi đến như một yêu cầu tính năng cần phân loại; công cụ `/ccba-triage` sẽ đọc cờ này).*

Khi được đặt là `yes`, các PR ngoài dự án sẽ được đưa vào quy trình triage giống như Issue, sử dụng các câu lệnh `gh pr` tương ứng:
- **Đọc PR**: `gh pr view <number> --comments` và `gh pr diff <number>`.
- **Liệt kê PR ngoài để triage**:
  ```powershell
  gh pr list --state open --json number,title,body,labels,author,authorAssociation
  ```
  Sau đó lọc lại và chỉ giữ các PR có `authorAssociation` là `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, hoặc `NONE` (bỏ qua các PR của `OWNER`/`MEMBER`/`COLLABORATOR` đang tự phát triển).
- **Thao tác PR**: Sử dụng `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, và `gh pr close`.

Vì GitHub dùng chung một dải đánh số ID cho cả Issue và PR, hãy kiểm tra loại ticket bằng lệnh `gh pr view <number>` trước, nếu báo lỗi thì fallback sang `gh issue view <number>`.

---

## Các thuật ngữ trong Quy trình Điều phối (Wayfinding)

Sử dụng bởi kỹ năng `/ccba-wayfinder` để quản lý các tác vụ phức tạp (Foggy problems) bằng cách dựng bản đồ nghiệp vụ:

- **Bản đồ (Map)**: Là một Issue duy nhất được gắn nhãn `wayfinder:map`. Nội dung body của nó chứa danh sách các Quyết định đã có (Decisions-so-far) và bảng công việc con.
- **Ticket con (Child ticket)**: Các issue con được tạo ra và liên kết với Map bằng tính năng Sub-issues của GitHub. Nếu repo chưa bật tính năng này, Agent sẽ liên kết thủ công bằng cách liệt kê danh sách checkbox dạng `Task List` ở body của Map (ví dụ `- [ ] #<child_id>`) đồng thời ghi dòng `Part of #<map_id>` ở đầu body của Ticket con.
- **Rào cản/Phụ thuộc (Blocking)**: Để đánh dấu ticket B bị chặn bởi ticket A, sử dụng tính năng Issue Dependencies của GitHub qua API:
  ```powershell
  gh api --method POST repos/{owner}/{repo}/issues/{child}/dependencies/blocked_by -F issue_id={blocker-db-id}
  ```
  *(Lưu ý: `{blocker-db-id}` là ID cơ sở dữ liệu của issue blocker lấy từ trường `.id` qua API, không phải số ID hiển thị `#number`)*. Nếu không khả dụng, ghi nhận bằng văn bản `Blocked by: #<n>` ở đầu body của ticket. Một ticket chỉ được Agent claim khi tất cả blocker của nó đã đóng (`closed`).
- **Claim Ticket**: Gán ticket cho Agent hiện tại:
  ```powershell
  gh issue edit <number> --add-assignee @me
  ```
- **Resolve Ticket**: Trả lời câu hỏi bằng cách post comment `gh issue comment <number> --body "<câu trả lời>"`, đóng issue `gh issue close <number>`, và cập nhật liên kết kết quả vào Decisions-so-far trên Map.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
