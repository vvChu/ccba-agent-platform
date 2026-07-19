# Bản đồ Wayfinder: Đánh giá & Cải tiến `/ccba-brainstorm`

## Điểm đích (Destination)

Workflow `/ccba-brainstorm` tuân thủ đầy đủ các chuẩn chất lượng `writing-great-skills` và Hiến pháp Layer 1, bao gồm: Completion Criteria rõ ràng, relative links hợp lệ, không Sprawl, không Sediment, và cấu trúc phù hợp cho workflow (không phải skill).

## Ghi chú (Notes)

- `/ccba-brainstorm` là **workflow** (`.agents/workflows/`), không phải skill (`.agents/skills/`). Chuẩn `writing-great-skills` áp dụng ở mức nguyên tắc (CC, links, failure modes), nhưng một số quy tắc chỉ dành cho skill (frontmatter `description` ≤ 180 chars) có thể không áp dụng.
- Workflow này phức tạp nhất trong Platform: 5 bước + 1 bước bypass, config merging 2 nguồn, rẽ nhánh linh hoạt.
- Kỹ năng bổ trợ: `/ccba-review-skill` (vừa cập nhật), `/ccba-grill-with-docs`.

---

## Tickets

### T1: Sửa Absolute Links [Task — AFK]

- **Câu hỏi:** Workflow có chứa đường dẫn tuyệt đối (hardcoded `file:///d:/GitHubProjects/...`) vi phạm §5.3 của `writing-great-skills`?
- **Đầu ra:**
  - [x] Dòng 20: absolute link → `resources/brainstorm_topics.yaml`
  - [x] Dòng 36: absolute link → `../../../input_documents/`
- **Trạng thái:** ✅ Hoàn tất
- **File:** [ccba-brainstorm.md](file:///C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/research-ccba-skill-evaluation/.agents/workflows/ccba-brainstorm.md)
- **Blocked by:** Không (Frontier ✅)

---

### T2: Grilling Đánh giá Chất lượng [Grilling — HITL]

- **Câu hỏi:** Workflow tuân thủ đầy đủ `writing-great-skills` (6 failure modes) và Layer 1 chưa?
- **Đầu ra:**
  - [x] 7 câu grilling, 6 thay đổi đã áp dụng
  - [x] Xóa mục "Cách kích hoạt" (Duplication + No-op)
  - [x] Gộp Bước 1.5 vào Bước 1 (Sediment)
  - [x] Thay routing logic bằng tham chiếu (SoT)
  - [x] Rút gọn Research Legwork (No-op)
  - [x] Thêm Completion Criteria tổng thể
- **Trạng thái:** ✅ Hoàn tất
- **Blocked by:** Không (Frontier ✅)
- **Vùng sương mù cần làm rõ:**
  - Workflow 90 dòng — có Sprawl không? Nên tách ra SKILL.md riêng?
  - Bước 1.5 "Hybrid Branching Logic" — quá phức tạp? Có No-op không?
  - §72-89 "Cách kích hoạt workflow" — có phải Sediment/Duplication không (thông tin đã có trong frontmatter)?
  - Completion Criteria tổng thể — workflow thiếu mục này (giống review_skill trước khi sửa)

---

### T3: Triển khai Sửa chữa [Task — AFK]

- **Câu hỏi:** Áp dụng các thay đổi từ T1 và T2 vào file thật.
- **Đầu ra:**
  - [x] File đã sửa (90 → 70 dòng, -22%)
  - [x] Commit `1c8b072` — Maskara ✅
- **Trạng thái:** ✅ Hoàn tất
- **Blocked by:** [T1], [T2]

---

### T4: Review Skill [Task — AFK]

- **Câu hỏi:** Chạy `/ccba-review-skill` (vừa cập nhật) lên workflow đã sửa để kiểm chứng.
- **Đầu ra:**
  - [ ] Báo cáo review PASS
- **Trạng thái:** 🟢 Frontier — sẵn sàng thực thi
- **Blocked by:** [T3]

---

## Sương mù chiến trận (Not yet specified)

- **Cấu hình `brainstorm_topics.yaml`:** Chưa đánh giá nội dung file config 3.5KB — có thể chứa Sediment (chủ đề lỗi thời) hoặc thiếu validation schema. Phụ thuộc kết quả T2.
- **Tách workflow thành skill + workflow wrapper:** Nếu T2 xác nhận Sprawl, có thể cần tách logic chính ra `.agents/skills/brainstorm/SKILL.md` và giữ workflow wrapper mỏng. Phụ thuộc kết quả T2.

## Ngoài phạm vi (Out of scope)

- Viết unit tests cho workflow brainstorm.
- Đánh giá các skill nghiệp vụ mà brainstorm nạp (`required_skills` trong config).
- Cập nhật `platform-loader/catalog.yaml` (thuộc quy trình release).

---
*Wayfinder map — Tạo bởi Agent, cần review bởi chuyên gia.*
