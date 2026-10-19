---
name: ccba-handoff
description: Đóng gói và tổng hợp phiên làm việc hiện tại thành tài liệu Handoff chuẩn
  mực để Agent tiếp theo tiếp quản liền mạch.
argument-hint: Mục tiêu hoặc nhiệm vụ trọng tâm cho phiên làm việc tiếp theo?
bundle: _core
tier: kernel
disable-model-invocation: true
metadata:
  author: CCBA
  version: 2.1.0
user-invocable: true
command: /ccba-handoff
gpi:
  s: 3.0
  k: 2.0
  a: 1.0
  p: 1.0
triggers:
- ccba-handoff
- đóng gói phiên
- transfer context
- chuyển tiếp
---
# 🤝 Kỹ Năng: Handoff Phiên Làm Việc (`handoff`)

Kỹ năng này chịu trách nhiệm nén toàn bộ ngữ cảnh, quyết định kiến trúc, tiến độ công việc và trạng thái môi trường của phiên hiện tại thành một tài liệu bàn giao chuẩn mực tại `.md/scratch/handoffs/handoff-<timestamp>.md`.

Mục tiêu tối thượng là giúp **Agent ở phiên làm việc tiếp theo nắm bắt 100% ngữ cảnh trong 30 giây** mà không cần đọc lại toàn bộ hàng nghìn dòng lịch sử trò chuyện.

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `seam-exempt`. Kỹ năng này là SOP kernel đóng gói và tổng hợp phiên làm việc thành tài liệu Handoff chuẩn 5 phần tại `.md/scratch/handoffs/handoff-<timestamp>.md` kèm bước che giấu thông tin nhạy cảm theo chuẩn Maskara. Quy trình bảo đảm tính liên tục của bộ nhớ làm việc giữa các AI Agent mà không phụ thuộc các Seam dữ liệu ứng dụng.
- **Governance Compliance**: Đạt chuẩn thể chế Tier 2B Standalone Kernel Skill với điểm GPI (S: 3.0, K: 2.0, A: 1.0, P: 1.0) = 12.0 >= 12.0 (đi nhánh Tier 2B và nằm trong deadband [11.5, 12.5) được bảo toàn qua hysteresis). Kỹ năng hiện chưa có thư mục `references/` phụ trợ.

---

## 📋 Tiêu Chí Hoàn Thành (Completion Criteria)
- [x] Tạo thành công tệp bàn giao tại: `.md/scratch/handoffs/handoff-<YYYY-MM-DD-HHMMSS>.md`.
- [x] Thư mục `.md/scratch/` đã được cấu hình trong `.gitignore` (không đẩy dữ liệu nháp lên remote).
- [x] Tài liệu tuân thủ đầy đủ **Cấu trúc 5 Phần Tiêu chuẩn CCBA** và chuẩn **Decision-Decidable Catch-up (Pstack v0.15.27)**.
- [x] Đã che giấu (redact) 100% API keys, tokens, mật khẩu qua chuẩn Maskara.

---

## 📐 Cấu Trúc Tài Liệu Handoff 5 Phần Chuẩn CCBA

Tài liệu bàn giao bắt buộc phải tuân theo cấu trúc sau:

```markdown
# 🤝 CCBA Platform Session Continuation Summary

> **Timestamp:** <YYYY-MM-DDTHH:MM:SS+07:00>  
> **Repository:** <owner/repo> (Hub / Spoke)  
> **Active Branch:** <branch_name> (commit `<hash>`)  
> **Target Base:** `main` (commit `<hash>`)  

---

## 1. Outstanding User Requests & Decision-Decidable Calls (Nhiệm vụ mở & Quyết định chờ duyệt)
- **Danh sách quyết định đang chờ người dùng (`riskiest first`):** Liệt kê đầy đủ 100% các mục cần người dùng phê duyệt/lựa chọn (tuyệt đối không cắt bớt vì giới hạn từ), sắp xếp từ rủi ro cao nhất xuống thấp nhất. Mỗi mục (~30 từ) gồm đủ 5 thành tố:
  1. **Call Required:** Quyết định cần người dùng chốt (merge, approve, chọn phương án).
  2. **Recommended Pick:** Phương án Agent khuyến nghị thực hiện đầu tiên.
  3. **User-Visible Impact:** Thay đổi thực tế đối với người dùng/hệ thống.
  4. **Evidence:** Bằng chứng thực nghiệm hoặc kết quả kiểm thử hậu thuẫn.
  5. **Risk:** Mức độ rủi ro cụ thể (ghi rõ cả khi rủi ro thấp).
- **Phân loại giai đoạn:** PLANNING / IMPLEMENTATION / VERIFICATION / REVIEW.
- **Ngữ cảnh bổ sung:** Trích dẫn nguyên văn câu lệnh hoặc định hướng của người dùng.

---

## 2. User Knowledge & Core Directives (Quyết định cốt lõi của Người dùng)
- Các quyết định kiến trúc hoặc giới hạn do người dùng trực tiếp phê duyệt.
- Danh sách các giả định đã được xác nhận hoặc bị bác bỏ.

---

## 3. Work Accomplished (Các công việc đã hoàn thành)
- Danh sách các tính năng, refactor, bug fixes đã thực hiện kèm danh sách files thay đổi.
- Các commits và PRs liên quan (kèm mã commit SHA).

---

## 4. Model Knowledge & Architecture Discoveries (Tri thức & Phát hiện mới)
- Các invariants, CI gates, patterns mới phát hiện trong codebase.
- Các cảnh báo hoặc cạm bẫy kỹ thuật cần lưu ý.

---

## 5. Current Work & Immediate Next Steps (Kế hoạch hành động cho Agent tiếp theo)
- **Nhiệm vụ thực hiện ngay lập tức:** Mô tả chi tiết 1-3 bước hành động cụ thể.
- **Tài liệu tham khảo bắt buộc:** Danh sách các tệp SKILL.md, ADR, spec cần đọc trước khi code.
- **Lệnh kiểm thử xác minh:** Các lệnh CLI / Pytest để kiểm tra lại trước khi bắt đầu.
```

---

## 🔒 Quy Tắc An Toàn, Trình Bày & Bảo Mật
1. **Không trùng lặp tài liệu tĩnh:** Không sao chép lại toàn bộ nội dung của các file spec, ADR hay kế hoạch lớn; thay vào đó hãy sử dụng liên kết Markdown dẫn tới file đó.
2. **Khử lộ lọt dữ liệu:** Tuyệt đối không lưu API Key, bí mật hay thông tin nhạy cảm vào file handoff.
3. **Cá nhân hóa theo tham số:** Nếu người dùng truyền thêm tham số (argument) khi gọi lệnh (ví dụ: `/ccba-handoff chuẩn bị seminar PCCC`), hãy tập trung phần `Immediate Next Steps` vào đúng chủ đề đó.
4. **Quy tắc sơ đồ trực quan tinh gọn (Compact Visuals — `/ketchup` Discipline Pstack v0.15.27):** Khi minh họa kiến trúc, luồng thay đổi hoặc chuỗi phụ thuộc PR bằng sơ đồ Mermaid, giới hạn tối đa $\le 6$ khối (nodes) và $\le 8$ từ trong mỗi khối bằng ngôn ngữ tự nhiên ngắn gọn, không vẽ sơ đồ cho danh sách trạng thái đơn thuần và không lặp lại thông tin đã viết trong văn bản.
   - **Tiêu chí hoàn thành:** Tài liệu bàn giao liệt kê đầy đủ 100% các quyết định chờ người dùng theo 5 thành tố chuẩn (`riskiest first`), sơ đồ Mermaid (nếu có) tuân thủ giới hạn $\le 6$ khối / $\le 8$ từ mỗi khối, và vượt qua kiểm chuẩn bảo mật Maskara.
