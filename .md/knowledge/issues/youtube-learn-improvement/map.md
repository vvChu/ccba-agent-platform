# Bản đồ Wayfinder: Cải tiến Kỹ năng `youtube-learn` theo kết quả Review

## Điểm đích (Destination)

Kỹ năng [youtube-learn/SKILL.md](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/youtube-learn/SKILL.md) được cập nhật hoàn chỉnh, tích hợp đầy đủ các tiêu chí hoàn thành (Completion Criteria) cho từng Phase, chuyển dịch rào chắn phủ định (Negation) sang hướng tích cực, vượt qua kiểm định chất lượng của `/ccba-review-skill`.

## Ghi chú (Notes)

- Kỹ năng bổ trợ cần nạp: `/ccba-review-skill` (kiểm định chất lượng cuối cùng).
- File cần sửa đổi: `.agents/skills/youtube-learn/SKILL.md`.

---

## Tickets

### T1: Bổ sung Completion Criteria và sửa lỗi Negation [AFK / Task]

- **Câu hỏi:** Cập nhật các Phase trong `SKILL.md` để bổ sung tiêu chí hoàn thành riêng biệt và tích cực hóa rào chắn ở Phase 1?
- **Đầu ra:**
  - [x] Bổ sung `user-invocable: true` vào frontmatter.
  - [x] Bổ sung `Tiêu chí hoàn thành:` định lượng cho Phase 1, Phase 2, Phase 3, Phase 4.
  - [x] Sửa đổi rào chắn API Key ở Phase 1 để hướng dẫn in thông báo lỗi và thoát an toàn thay vì ghi "dừng ngay lập tức".
- **File:** [SKILL.md](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/youtube-learn/SKILL.md)
- **Trạng thái:** ✅ Hoàn tất
- **Blocked by:** Không

---

### T2: Kiểm định chất lượng qua `/ccba-review-skill` [HITL / Grilling]

- **Câu hỏi:** File sau khi chỉnh sửa có hoàn toàn PASS kiểm định chất lượng viết skill không?
- **Đầu ra:**
  - [x] Báo cáo kiểm định PASS từ `/ccba-review-skill`.
- **Trạng thái:** ✅ Hoàn tất
- **Blocked by:** Không

---

### T3: Commit & Bàn giao thay đổi [AFK / Task]

- **Câu hỏi:** Đóng gói thay đổi và commit theo quy chuẩn Git?
- **Đầu ra:**
  - [ ] Commit với message: `refactor(youtube-learn): add completion criteria and fix negation from review`
  - [ ] Đẩy (push) thay đổi lên remote.
- **Trạng thái:** 🟢 Frontier — sẵn sàng thực thi
- **Blocked by:** Không (Frontier ✅)

---

## Sơ đồ Dependency

```mermaid
flowchart TD
    T1["T1: Cập nhật SKILL.md<br/>(Bổ sung CC & Sửa Negation)"]
    T2["T2: Kiểm định chất lượng<br/>(ccba-review-skill)"]
    T3["T3: Commit & Bàn giao"]

    T1 --> T2 --> T3

    style T1 fill:#264653,color:#fff
    style T2 fill:#e76f51,color:#fff
    style T3 fill:#6c757d,color:#fff
```

> 🟢 **Frontier (unblocked):** T1
> 🔴 **Blocked:** T2, T3

---

## Quyết định đã chốt (Decisions so far)

- Chưa có quyết định nào được chốt (bản đồ mới khởi lập).

## Chưa xác định rõ (Not yet specified)

- Không có. Lộ trình cải tiến kỹ năng này cực kỳ rõ ràng và ngắn gọn.

## Ngoài phạm vi (Out of scope)

- Chỉnh sửa logic Python thực tế của package `ccba-youtube-learn` (chỉ tập trung tối ưu hóa tài liệu kỹ năng `SKILL.md`).
- Thay đổi workflow wrapper `ccba-youtube-learn.md` (vì wrapper đã tuân thủ chuẩn mỏng).

---
*Tạo bởi CCBA Wayfinder — 2026-07-20*
