# Bản đồ Wayfinder: Nâng cấp `/ccba-brainstorm` từ phân tích `brainstorm-coach`

## Điểm đích (Destination)

Workflow `/ccba-brainstorm` được bổ sung 6 cải tiến rút ra từ phân tích so sánh (`--compare`) với `tronghieu/agent-skills/brainstorm-coach`, biến nó từ workflow setup thuần túy thành **facilitator tương tác** với thư viện kỹ thuật brainstorm và cơ chế luân phiên user-AI.

## Ghi chú (Notes)

- **License:** Repo nguồn `tronghieu/agent-skills` KHÔNG có file LICENSE → All Rights Reserved. Mọi nội dung phải **viết mới 100%**, chỉ học kiến trúc và áp dụng kỹ thuật public domain.
- **Branch:** Tạo branch riêng `feat/brainstorm-upgrade` từ `main` (sau khi merge `research-ccba-skill-evaluation`).
- Kỹ năng bổ trợ cần nạp: `writing-great-skills`, `grilling`.

---

## Tickets

### T1: Viết Hybrid Rhythm Rules [Task — AFK]

- **Câu hỏi:** Thêm quy tắc tương tác luân phiên user-AI vào workflow.
- **Đầu ra:**
  - [x] Mục "Quy tắc tương tác (Hybrid Rhythm)" trong Bước 4
  - [x] 4 nhịp: Prompt (1 câu) → User first (ghi verbatim) → AI Build (2-4 ý, tagged `(AI)`) → Return floor (1 câu hỏi)
- **Trạng thái:** ✅ Hoàn tất — Commit `554520b`
- **Blocked by:** Không (Frontier ✅)
- **Effort:** ~5-7 dòng Markdown

---

### T2: Viết Deferred Judgment Rule [Task — AFK]

- **Câu hỏi:** Thêm quy tắc không đánh giá trong giai đoạn phát tán ý tưởng.
- **Đầu ra:**
  - [x] Quy tắc: *"Trong giai đoạn phát tán, không đánh giá, xếp hạng hoặc phê phán"*
- **Trạng thái:** ✅ Hoàn tất — Commit `554520b`
- **Blocked by:** Không (Frontier ✅)
- **Effort:** 1-2 dòng

---

### T3: Viết Energy Checkpoint [Task — AFK]

- **Câu hỏi:** Thêm cơ chế kiểm tra năng lượng phiên brainstorm.
- **Đầu ra:**
  - [x] Sau 3-4 vòng: tiếp tục / đổi hướng / tổng hợp?
- **Trạng thái:** ✅ Hoàn tất — Commit `554520b`
- **Blocked by:** Không (Frontier ✅)
- **Effort:** 2-3 dòng

---

### T4: Viết Session Document Format [Task — AFK]

- **Câu hỏi:** Định nghĩa format ghi nhận phiên brainstorm.
- **Đầu ra:**
  - [ ] Mục "Session Document" mô tả artifact Markdown output
  - [ ] Tags: `(user)` cho ý tưởng người dùng (verbatim), `(AI)` cho ý tưởng Agent
  - [ ] Cấu trúc: Intake → Ý tưởng phát tán → Nhóm phân loại → Xếp hạng → Action items
- **Blocked by:** [T1] (cần rhythm trước khi định format)
- **Effort:** ~10 dòng

---

### T5: Viết Technique Library (Original) [Research + Task — AFK]

- **Câu hỏi:** Tạo thư viện kỹ thuật brainstorm viết mới 100% (không copy từ nguồn).
- **Đầu ra:**
  - [ ] File `references/brainstorm_techniques.md` (~4KB) — router: danh sách 10-15 kỹ thuật public domain, mỗi cái 2-3 dòng mô tả + gợi ý khi nào dùng
  - [ ] Phân nhóm: Structured (SCAMPER, Six Hats), Creative (Reversal, What-if, Analogy), Deep (5 Whys, Question Storming)
  - [ ] Tích hợp vào Bước 4: Agent đề xuất technique phù hợp dựa trên topic
- **Blocked by:** [T1], [T3] (cần rhythm và checkpoint trước)
- **Effort:** ~4KB file mới + 3-5 dòng sửa workflow

---

### T6: Viết Party Mode (Multi-role Ideation) [Task — HITL]

- **Câu hỏi:** Thêm chế độ brainstorm đa vai trò.
- **Đầu ra:**
  - [ ] Mục "Party Mode" trong workflow hoặc file sibling
  - [ ] Khi user yêu cầu "nhiều góc nhìn" / "phản biện" → Agent tạo 2-3 persona ảo (khách hàng, đối thủ, skeptic) luân phiên phát biểu
  - [ ] Phân biệt rõ với `/ccba-grilling` (sinh ý tưởng ≠ stress-test kế hoạch)
- **Blocked by:** [T1], [T4] (cần rhythm + session doc trước)
- **Effort:** ~10-15 dòng

---

### T7: Grilling Đánh giá Tổng thể [Grilling — HITL]

- **Câu hỏi:** Workflow sau khi cập nhật có tuân thủ `writing-great-skills` không?
- **Đầu ra:**
  - [ ] Phiên `/ccba-grill-with-docs` trên bản cập nhật
  - [ ] Báo cáo PASS hoặc danh sách sửa bổ sung
- **Blocked by:** [T1], [T2], [T3], [T4], [T5], [T6]

---

## Quyết định đã chốt (Decisions so far)

- **License gate:** `--compare` only — không copy text, chỉ học kiến trúc + viết mới. (Nguồn: phiên xia `462ca93`)
- **Scope:** 4 cải tiến core (T1-T4) + 2 features mới (T5-T6).
- **Không tách skill:** Giữ `/ccba-brainstorm` inline trong workflow (QĐ từ phiên grilling trước).

## Sương mù chiến trận (Not yet specified)

- **Tích hợp `brainstorm_topics.yaml`:** T5 (technique library) có thể cần thêm field `suggested_techniques` vào config YAML cho mỗi topic. Phụ thuộc T5.
- **Convergence protocol:** Giai đoạn tổng hợp sau diverge (group → rank → action items) chưa chi tiết. Phụ thuộc T4.
- **Kích thước file:** Sau T1-T6, workflow có thể phình >100 dòng → cần đánh giá lại quyết định "giữ inline" hay tách skill.

## Ngoài phạm vi (Out of scope)

- Port nội dung text từ `tronghieu/agent-skills` (vi phạm license).
- Viết tests cho workflow brainstorm.
- Cập nhật `platform-loader/catalog.yaml` (thuộc quy trình release).
- Bản dịch đa ngôn ngữ (README.vi.md, README.zh.md).

---
*Wayfinder map — Tạo bởi Agent, cần review bởi chuyên gia.*
