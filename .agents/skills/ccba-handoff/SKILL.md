---
name: ccba-handoff
description: Đóng gói và tổng hợp phiên làm việc hiện tại thành tài liệu Handoff chuẩn
  mực để Agent tiếp theo tiếp quản liền mạch.
argument-hint: Mục tiêu hoặc nhiệm vụ trọng tâm cho phiên làm việc tiếp theo?
bundle: _core
disable-model-invocation: true
metadata:
  author: CCBA
  version: 2.0.0
triggers:
- ccba-handoff
- đóng gói phiên
- transfer context
- chuyển tiếp
---
# 🤝 Kỹ Năng: Handoff Phiên Làm Việc (`handoff`)

Kỹ năng này chịu trách nhiệm nén toàn bộ ngữ cảnh, quyết định kiến trúc, tiến độ công việc và trạng thái môi trường của phiên hiện tại thành một tài liệu bàn giao chuẩn mực tại `.md/scratch/handoffs/handoff-<timestamp>.md`.

Mục tiêu tối thượng là giúp **Agent ở phiên làm việc tiếp theo nắm bắt 100% ngữ cảnh trong 30 giây** mà không cần đọc lại toàn bộ hàng nghìn dòng lịch sử trò chuyện.

---

## 📋 Tiêu Chí Hoàn Thành (Completion Criteria)
- [x] Tạo thành công tệp bàn giao tại: `.md/scratch/handoffs/handoff-<YYYY-MM-DD-HHMMSS>.md`.
- [x] Thư mục `.md/scratch/` đã được cấu hình trong `.gitignore` (không đẩy dữ liệu nháp lên remote).
- [x] Tài liệu tuân thủ đầy đủ **Cấu trúc 5 Phần Tiêu chuẩn CCBA**.
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

## 1. Outstanding User Requests (Nhiệm vụ còn dang dở & Yêu cầu người dùng)
- **Danh sách yêu cầu mở:** Liệt kê theo thứ tự ưu tiên (P1, P2, P3).
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

## 🔒 Quy Tắc An Toàn & Bảo Mật
1. **Không trùng lặp tài liệu tĩnh:** Không sao chép lại toàn bộ nội dung của các file spec, ADR hay kế hoạch lớn; thay vào đó hãy sử dụng liên kết Markdown dẫn tới file đó.
2. **Khử lộ lọt dữ liệu:** Tuyệt đối không lưu API Key, bí mật hay thông tin nhạy cảm vào file handoff.
3. **Cá nhân hóa theo tham số:** Nếu người dùng truyền thêm tham số (argument) khi gọi lệnh (ví dụ: `/ccba-handoff chuẩn bị seminar PCCC`), hãy tập trung phần `Immediate Next Steps` vào đúng chủ đề đó.
