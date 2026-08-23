---
description: Soạn thảo và gửi đề xuất ý tưởng/tính năng/báo lỗi (RFC Proposal) từ
  Spoke lên Hub dưới dạng GitHub Issue
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
disable-model-invocation: true
command: /ccba-issue-to-hub
triggers:
- issue to hub
- đề xuất ý tưởng
- rfc
- tạo issue
- feature request
- ccba-issue-to-hub
---
# Workflow: Đề Xuất Ý Tưởng & Tính Năng Lên Hub (/ccba-issue-to-hub)

Quy trình tự động hóa bóc tách ngữ cảnh thảo luận tại dự án Spoke, biên soạn bản đề xuất cải tiến (**RFC Proposal**) chuẩn chỉnh và tạo GitHub Issue trực tiếp lên repository trung tâm CCBA Hub (`ccba-agent-platform`).

---

## 🎯 Mục Đích & Vai Trò
- **Giai đoạn Ý tưởng (Idea & RFC Phase):** Khi phát hiện bài toán mới, nhu cầu cải tiến công cụ, chuẩn hóa quy trình hoặc phát hiện lỗi ở cấp nền tảng nhưng chưa cần đóng gói mã nguồn ngay.
- **Tính đối xứng:** Là bước đi trước của `/ccba-contribute-to-hub` (đóng gói code & mở PR) trong chu trình đóng góp ngược (Upstream Contribution Loop).

---

## 📋 Các Bước Thực Hiện:

### Bước 1: Trích xuất Ngữ cảnh & Đánh giá Nhu cầu
Agent thu thập thông tin từ ngữ cảnh hội thoại hiện tại hoặc tài liệu tại Spoke:
1. **Loại đề xuất:** `feat` (tính năng/kỹ năng mới), `fix` (sửa lỗi nền tảng), `refactor` (tối ưu kiến trúc/deep seams), `docs` (chuẩn hóa tài liệu/hiến pháp).
2. **Tiêu đề ngắn gọn:** Dưới 10 từ theo định dạng `type(scope): mô tả ngắn`.
3. **Nỗi đau thực tế (Pain Point):** Vấn đề cụ thể gặp phải tại dự án Spoke hiện tại.
4. **Giải pháp kỹ thuật dự kiến:** Ý tưởng module, skill, workflow, rules, hoặc API contract cần bổ sung trên Hub.

---

### Bước 2: Kiểm tra Trùng lặp trên Hub
Trước khi tạo Issue mới, Agent chủ động kiểm tra xem vấn đề đã được ghi nhận hoặc giải quyết trên Hub hay chưa:
1. **Kiểm tra Issues hiện có:**
   ```bash
   gh issue list --repo vvChu/ccba-agent-platform --limit 30
   ```
2. **Kiểm tra Catalog Hub:**
   Đọc tệp `catalog.yaml` (qua đường dẫn `hub_path` trong `.md/workspace_context.yaml` nếu có) để xác nhận kỹ năng/công cụ tương tự chưa tồn tại.

*Nếu phát hiện đã có Issue tương tự:* Gợi ý người dùng bổ sung thảo luận vào Issue cũ thay vì tạo mới.

---

### Bước 3: Soạn Thảo Bản Đề Xuất (RFC Proposal Body)
Soạn thảo nội dung Issue theo cấu trúc chuẩn CCBA RFC:

```markdown
### 1. Bối cảnh & Vấn đề (Context & Problem):
- Mô tả thực trạng và lý do phát sinh nhu cầu từ dự án Spoke.
- Tác động tiêu cực nếu không xử lý (Token OpEx, lỗi dữ liệu, thiếu tính năng).

### 2. Đề xuất giải pháp (RFC Proposal):
- Kiến trúc / Kỹ năng / Package / Workflow dự kiến triển khai trên Hub.
- Phân tích tính tương thích và khả năng tái sử dụng cho các Spokes khác.

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [ ] Tiêu chí 1 (Code / Package / Seam)
- [ ] Tiêu chí 2 (Workflow / Skills Catalog)
- [ ] Tiêu chí 3 (Tài liệu Hiến pháp & Tests)

---
*Được đề xuất tự động từ Spoke `[tên-spoke]` qua workflow `/ccba-issue-to-hub`.*
```

Agent trình bày bản thảo cho người dùng xem và xác nhận trước khi gửi.

---

### Bước 4: Mở GitHub Issue Trực Tiếp Trên Hub Repo
Thực thi tạo Issue thông qua GitHub CLI:

```bash
gh issue create --repo vvChu/ccba-agent-platform --title "[Tiêu đề]" --body "[Nội dung RFC]"
```

*Trường hợp không có kết nối `gh` CLI hoặc thiếu token:*
Cung cấp toàn bộ nội dung markdown đã định dạng kèm đường dẫn tạo issue thủ công:
👉 `https://github.com/vvChu/ccba-agent-platform/issues/new`

---

### Bước 5: Báo Cáo & Hướng Dẫn Vòng Đời Tiếp Theo
Sau khi tạo thành công, Agent gửi phản hồi tổng kết:
1. **Mã số & Link Issue:** Ví dụ `#209 - https://github.com/vvChu/ccba-agent-platform/issues/209`.
2. **Hướng dẫn phát triển tiếp:**
   - Khi sẵn sàng lập trình: Tạo feature branch bằng `/ccba-new-feature #[ISSUE_ID]`.
   - Khi hoàn thành code và tests tại Spoke: Đóng gói và mở PR lên Hub bằng `/ccba-contribute-to-hub`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
