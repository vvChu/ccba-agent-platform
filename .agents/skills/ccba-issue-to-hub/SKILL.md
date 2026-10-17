---
name: ccba-issue-to-hub
description: Soạn thảo và gửi đề xuất ý tưởng/tính năng/báo lỗi (RFC Proposal) từ
  Spoke lên Hub dưới dạng GitHub Issue
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
tier: kernel
disable-model-invocation: true
command: /ccba-issue-to-hub
user-invocable: true
metadata:
  version: "1.1.0"
  author: "CCBA Hub"
gpi:
  s: 3.0
  k: 3.0
  a: 1.0
  p: 1.0
triggers:
- issue to hub
- đề xuất ý tưởng
- rfc
- tạo issue
- feature request
- ccba-issue-to-hub
- ccba-triage
- triage
---

# Workflow: Đề Xuất Ý Tưởng & Tính Năng Lên Hub (/ccba-issue-to-hub)

Quy trình tự động hóa bóc tách ngữ cảnh thảo luận tại dự án Spoke, biên soạn bản đề xuất cải tiến (**RFC Proposal**) chuẩn chỉnh và tạo GitHub Issue trực tiếp lên repository trung tâm CCBA Hub (`ccba-agent-platform`).

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`seam-exempt`** (SOP tạo GitHub Issue chuẩn từ Spoke lên Hub). Skill hướng dẫn quy trình 5 bước trích xuất ngữ cảnh, kiểm tra trùng lặp và mở RFC Issue trên kho Hub; không đóng gói pipeline xử lý dữ liệu hay phụ thuộc Seam Contract ứng dụng cụ thể.

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
- **Tiêu chí hoàn thành:** Thu thập đầy đủ ngữ cảnh bài toán, phạm vi đề xuất và giải pháp dự kiến.

---

### Bước 2: Kiểm tra Trùng lặp, Quy mô Thực tế & Biên giới Liên bang trên Hub
Trước khi tạo Issue mới, Agent chủ động kiểm tra xem vấn đề đã được ghi nhận, giải quyết hoặc thuộc phạm vi của repo khác hay chưa:
1. **Kiểm tra Issues hiện có:**
   ```bash
   gh issue list --repo vvChu/ccba-agent-platform --limit 30
   ```
2. **Kiểm tra Catalog Hub & Seam Contracts:**
   Đọc tệp `catalog.yaml` qua biến môi trường `$CCBA_HUB_PATH/.agents/skills/platform-loader/catalog.yaml` (PowerShell: `$env:CCBA_HUB_PATH`) và chạy `python scripts/governance/compile_catalog.py --in <types> --out <types> --json` để xác nhận kỹ năng/seam tương tự chưa tồn tại.
3. **Kiểm tra Biên giới Liên bang, Quy mô Thực tế & Chống Dual-SSOT (Federated Boundary, Scale & Anti-Dual-SSOT Guard):**
   - Đối chiếu xem đề xuất có thuộc phạm vi nội bộ của repo liên bang khác (như bảng 15 `ROLE_ID` phân quyền SharePoint Entra ID của `IDOP-CCBA-WAY` hay kho văn bản pháp quy của `ccba-legal-knowledge`) gây chồng chéo với cấu hình `seat_role` / `qc_governance` hiện hữu trên Hub hay không.
   - Không đề xuất dịch cơ học các khái niệm quản trị nhân sự con người (như khung tuyển dụng *GWC: Get it - Want it - Capacity*) thành class phần mềm trùng lặp với các Seams đã có (`MaskaraScanner`, `choose_model`, `SandboxPromoter`) hoặc yêu cầu tiêm tĩnh metadata vào System Prompt của mọi phiên làm việc.
   - Không đề xuất xây dựng CLI parser/SQLite/AST validator cho dữ liệu cấu hình tĩnh quy mô nhỏ ($N \le 20$ dòng) khi đã giải quyết trọn vẹn bằng grep/dict/JSONL phẳng (< 50ms).

*Nếu phát hiện đã có Issue/Seam tương tự, lệch biên giới Repo hoặc dư thừa quy mô ($N \le 20$):* Gợi ý người dùng tái sử dụng Seam sẵn có, mở Issue ở đúng Repo đích, hoặc bổ sung thảo luận vào Issue cũ thay vì tạo mới.
- **Tiêu chí hoàn thành:** Xác nhận tính độc nhất, đúng quy mô thực tế và đúng biên giới kiến trúc của đề xuất, không trùng lặp với các Issue/Seams đã có trên Hub và không tạo Dual-SSOT.

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
- **Tiêu chí hoàn thành:** Bản thảo RFC Issue hoàn chỉnh được người dùng phê duyệt trước khi gửi.

---

### Bước 4: Mở GitHub Issue Trực Tiếp Trên Hub Repo
Thực thi tạo Issue thông qua GitHub CLI:

```bash
gh issue create --repo vvChu/ccba-agent-platform --title "[Tiêu đề]" --body "[Nội dung RFC]"
```

*Trường hợp không có kết nối `gh` CLI hoặc thiếu token:*
Cung cấp toàn bộ nội dung markdown đã định dạng kèm đường dẫn tạo issue thủ công:
👉 `https://github.com/vvChu/ccba-agent-platform/issues/new`
- **Tiêu chí hoàn thành:** Issue được tạo thành công trên GitHub Hub repo với mã Issue cụ thể (hoặc cung cấp link tạo thủ công).

---

### Bước 5: Báo Cáo & Hướng Dẫn Vòng Đời Tiếp Theo
Sau khi tạo thành công, Agent gửi phản hồi tổng kết:
1. **Mã số & Link Issue:** Ví dụ `#209 - https://github.com/vvChu/ccba-agent-platform/issues/209`.
2. **Hướng dẫn chu trình khép kín tiếp theo:**
   - Khi có prototype/script nháp tại Spoke $\to$ Tốt nghiệp mã nguồn: `/ccba-graduate-rd --issue #[ISSUE_ID]`
   - Khi mở PR chính thức lên Hub $\to$ Đóng gói & mở PR: `/ccba-contribute-to-hub --issue #[ISSUE_ID]` (Tự động gắn mã `Closes #[ISSUE_ID]`).
- **Tiêu chí hoàn thành:** Hiển thị mã số Issue, link GitHub và hướng dẫn các bước tiếp theo của vòng đời đề xuất.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/issue_triage_flow.md` | Quy trình phân loại, gắn nhãn và sàng lọc sự cố kỹ thuật (issues) |
| `references/agent-brief.md` | Mẫu chỉ dẫn tóm tắt nhiệm vụ và phạm vi kỹ thuật (Agent Brief) cho Issue |
| `references/out-of-scope.md` | Hướng dẫn nhận diện và cách ly các yêu cầu nằm ngoài phạm vi giải quyết (Out of Scope) |

