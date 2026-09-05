# Công cụ theo dõi công việc: GitLab Issues

Các lỗi (bugs) và yêu cầu tính năng (Specs) của dự án này được theo dõi trên GitLab Issues. Sử dụng công cụ `glab` CLI cho mọi thao tác.

## Các lệnh thao tác tiêu chuẩn (Conventions)

- **Tạo sự cố (Issue)**:
  ```powershell
  glab issue create --title "Tiêu đề issue" --description "Mô tả chi tiết"
  ```
- **Đọc sự cố**:
  ```powershell
  glab issue view <number> --comments
  ```
- **Liệt kê sự cố**:
  ```powershell
  glab issue list --label "needs-triage"
  ```
- **Viết bình luận**:
  GitLab gọi các bình luận là "notes".
  ```powershell
  glab issue note <number> --message "Nội dung bình luận"
  ```
- **Gán / Gỡ nhãn (Labels)**:
  ```powershell
  glab issue update <number> --label "ready-for-agent"
  glab issue update <number> --unlabel "needs-triage"
  ```
- **Đóng sự cố**:
  `glab issue close` không nhận tham số bình luận trực tiếp, vì vậy hãy post note giải thích trước rồi đóng:
  ```powershell
  glab issue note <number> --message "Giải trình đóng lỗi"
  glab issue close <number>
  ```

*Lưu ý: `glab` sẽ tự động nhận diện repository đích dựa trên thông tin Git remote cấu hình trong thư mục hiện tại.*

---

## Quản lý Merge Requests (MRs) như một nguồn yêu cầu

**MRs là một request surface: no.** _(Chuyển thành `yes` nếu dự án của bạn chấp nhận MR từ cộng tác viên ngoài gửi đến như một yêu cầu tính năng cần phân loại; công cụ `/ccba-triage` sẽ đọc cờ này).*

Khi được đặt là `yes`, các MR ngoài dự án sẽ được đưa vào quy trình triage giống như Issue, sử dụng các câu lệnh `glab mr` tương ứng:
- **Đọc MR**: `glab mr view <number> --comments` và `glab mr diff <number>`.
- **Liệt kê MR ngoài để triage**:
  ```powershell
  glab mr list
  ```
  Sau đó lọc lại và chỉ giữ các MR có tác giả (`author`) không phải là thành viên/owner dự án.
- **Thao tác MR**: Sử dụng `glab mr note`, `glab mr update --label`/`--unlabel`, và `glab mr close`.

Không giống như GitHub, GitLab đánh số ID riêng biệt cho Issue và MR (nên có thể có cả Issue #42 và MR #42). Agent cần xác định rõ bề mặt đang thao tác để tránh tác động nhầm.

---

## Các thuật ngữ trong Quy trình Điều phối (Wayfinding)

Sử dụng bởi kỹ năng `/ccba-wayfinder` để quản lý các tác vụ phức tạp (Foggy problems) bằng cách dựng bản đồ nghiệp vụ:

- **Bản đồ (Map)**: Là một Issue duy nhất được gắn nhãn `wayfinder:map`. Nội dung body của nó chứa danh sách các Quyết định đã có (Decisions-so-far) và bảng công việc con.
- **Ticket con (Child ticket)**: Các issue con được tạo ra và liên kết với Map bằng cách ghi dòng `Part of #<map_id>` ở đầu mô tả của ticket con, kèm theo nhãn `wayfinder:<loại_task>` (`research`/`prototype`/`grilling`/`task`).
- **Rào cản/Phụ thuộc (Blocking)**: GitLab hỗ trợ tính năng chặn issue (blocking links) ở các gói trả phí. Để thiết lập liên kết chặn, post một note có quick action sau:
  ```powershell
  glab issue note <child> --message "/blocked_by #<blocker>"
  ```
  Đối với gói miễn phí, ghi nhận bằng văn bản `Blocked by: #<n>` ở đầu body của ticket. Một ticket chỉ được Agent claim khi tất cả blocker của nó đã đóng.
- **Claim Ticket**: Gán ticket cho Agent hiện tại:
  ```powershell
  glab issue update <number> --assignee @me
  ```
- **Resolve Ticket**: Trả lời câu hỏi bằng cách post note `glab issue note <number> --message "<câu trả lời>"`, đóng issue `glab issue close <number>`, và cập nhật liên kết kết quả vào Decisions-so-far trên Map.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
