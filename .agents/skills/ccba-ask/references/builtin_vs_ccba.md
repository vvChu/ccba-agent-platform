# Đối Chiếu Built-in Antigravity vs CCBA, Close Calls & Prompt Recipes

> **Tài liệu tham chiếu Chế độ A của `/ccba-ask`.** Nạp tệp này khi người dùng so sánh lệnh tích hợp của host với kỹ năng `/ccba-*`, phân vân giữa 2 kỹ năng gần nghĩa (*Close Calls*), hỏi cách sửa phiên chạy chệch hướng, hoặc cần công thức prompt mẫu 1-click.

---

## 1. Bảng Đối Chiếu: Lệnh Built-in Antigravity vs Kỹ Năng `/ccba-*`

| Nhu cầu người dùng | Lệnh Built-in của Host | Kỹ năng CCBA tương ứng | Khi nào chọn cái nào? |
| :--- | :--- | :--- | :--- |
| **Lập kế hoạch triển khai** | Lệnh built-in `plan` | [`/ccba-new-feature`](../../ccba-new-feature/SKILL.md) $\to$ [`/ccba-to-spec`](../../ccba-to-spec/SKILL.md) | Dùng `plan` của host cho tác vụ cục bộ gọn trong 1 phiên; dùng `/ccba-new-feature` + `/ccba-to-spec` khi cần tách nhánh chuẩn, khóa nhận việc (`Claim Lock`), biên lai Seam (`ADR-0061`) và bẻ Micro-PR $\le 200$ LOC. |
| **Phỏng vấn phản biện thiết kế** | `/grill-me` | [`/ccba-grilling`](../../ccba-grilling/SKILL.md) | `/grill-me` là phỏng vấn nhanh không lưu dấu vết; `/ccba-grilling` có Bước 0 (`sharpen`), tự tra cứu codebase, lưu Decision Log và kích hoạt cổng thẩm định ngang hàng `ADR-0067` (luôn ưu tiên trong repo dự án). |
| **Ghi nhớ bài học cuối phiên** | `/learn` | [`/ccba-session-retrospective`](../../ccba-session-retrospective/SKILL.md) | `/learn` lưu thói quen ngắn cục bộ của IDE; `/ccba-session-retrospective` tổng hợp tri thức vào `session_learnings.md`, đối soát cổng CI/governance và vệ sinh workspace (luôn chạy khi chốt phiên làm việc trên repo). |
| **Điều phối đa tác nhân** | Lệnh built-in `teamwork` / `swarm` | [`/ccba-teamwork`](../../ccba-teamwork/SKILL.md) | `teamwork` / `swarm` của host dùng điều phối chung; `/ccba-teamwork` cưỡng chế giao thức **Single-Writer `apply_worker_patch.py` (`ADR-0053`)** và khóa kiểm định chống xung đột git trên monorepo CCBA. |
| **Suy luận sâu & gỡ nút thắt** | `/boost` | [`/ccba-codebase-design`](../../ccba-codebase-design/SKILL.md) / [`/ccba-research`](../../ccba-research/SKILL.md) | Dùng `/boost` để tăng độ sâu suy luận chung; dùng `/ccba-research` khi cần báo cáo trích dẫn nguồn gốc hoặc `/ccba-codebase-design` khi khảo sát kiến trúc Deep Module. |
| **Quản lý cửa sổ ngữ cảnh** | `/compact`, `/clear`, `/goal` | [`/ccba-handoff`](../../ccba-handoff/SKILL.md) | `/clear` khi đổi hẳn chủ đề; `/compact` khi sắp chạm ngưỡng Smart Zone trên cùng chuỗi việc; `/ccba-handoff` khi chuyển sang kho/công cụ/phiên mới cần giữ nguyên lý do thiết kế (*the why*). |

---

## 2. Close Calls — Phân Ranh Các Cặp Kỹ Năng Dễ Nhầm

- **Brainstorm (`/ccba-ask` Chế độ B) vs [`/ccba-wayfinder`](../../ccba-wayfinder/SKILL.md) vs [`/ccba-grilling`](../../ccba-grilling/SKILL.md):**
  - *Brainstorm*: mở rộng ý tưởng, phá lối mòn, đa góc nhìn (chưa chốt phạm vi).
  - *Wayfinder*: bài toán quá lớn/mờ trải nhiều sóng hoặc nhiều kho, cần lập `map.md` gồm các *Decision Tickets* để đẩy lùi sương mù.
  - *Grilling*: đã có đề xuất/lát cắt cụ thể, cần hỏi xoáy từng câu một để khóa thiết kế trước khi viết code.
- **[`/ccba-create-pr`](../../ccba-create-pr/SKILL.md) vs [`/ccba-release-feature`](../../ccba-release-feature/SKILL.md) vs [`/ccba-contribute-to-hub`](../../ccba-contribute-to-hub/SKILL.md):**
  - `/ccba-create-pr`: mở PR trên **repo hiện tại** (Hub hoặc nội bộ Spoke) kèm bằng chứng kiểm định.
  - `/ccba-release-feature`: **merge PR đã xanh**, dọn nhánh cũ và cập nhật walkthrough.
  - `/ccba-contribute-to-hub`: **chỉ dùng** khi đóng góp ngược tài sản tổng quát từ Spoke về Hub trung tâm.
- **[`/ccba-ask`](../SKILL.md) Chế độ B vs [`/ccba-knowledge-loop`](../../ccba-knowledge-loop/SKILL.md):**
  - `/ccba-ask` Chế độ B: thảo luận 1 phiên, nạp nhanh 1 URL YouTube (qua `/ccba-youtube-learn`) hoặc 1 tệp ghi chú ngoài.
  - `/ccba-knowledge-loop`: chu trình đa nguồn có subagent nghiên cứu ngầm, nuôi kho `.md/knowledge/wiki/` dài hạn và lập `map.md`.
- **[`/ccba-research`](../../ccba-research/SKILL.md) vs [`/ccba-codebase-design`](../../ccba-codebase-design/SKILL.md):**
  - `/ccba-research`: điều tra tài liệu/API/bằng chứng nguồn gốc thành báo cáo trích dẫn.
  - `/ccba-codebase-design`: rà soát module nông (*shallow modules*) và đề xuất tái cấu trúc kiến trúc codebase.

---

## 3. Khắc Phục Phiên Chạy Chệch Hướng (`Symptom → Fix`)

| Triệu chứng gặp phải | Cách xử lý chuẩn ngay lập tức |
| :--- | :--- |
| Gọi `/ccba-ask` hỏi về lệnh khác nhưng lo Agent tự chạy lệnh đó | Khóa `Mention ≠ Invoke` đã bật; nếu Agent có dấu hiệu triển khai, nhắc 1 câu: *"Chỉ tư vấn, chưa sửa mã hay chạy lệnh."* |
| Phiên quá dài, phản hồi bắt đầu lặp hoặc quên ràng buộc | Đứng tại ranh giới pha gần nhất $\to$ chạy [`/ccba-handoff`](../../ccba-handoff/SKILL.md) (nếu cần giữ ngữ cảnh sang phiên mới) hoặc `/clear` (nếu đổi việc hoàn toàn); chỉ dùng `/compact` làm phương án cuối. |
| Nhiều ứng viên cải tiến quá lớn không thể gộp 1 PR | Chạy [`/ccba-wayfinder`](../../ccba-wayfinder/SKILL.md) lập bản đồ theo Sóng, sau đó chạy [`/ccba-grilling`](../../ccba-grilling/SKILL.md) và [`/ccba-to-spec`](../../ccba-to-spec/SKILL.md) cho từng Sóng độc lập. |
| Agent báo "xong rồi" chỉ dựa trên phán đoán hoặc build tĩnh | Yêu cầu bằng chứng tất định thực tế (`python -m ccba_harness verify-patch`, `pytest` exit `0`, hoặc chạy bộ `verify-*` cục bộ). |
| Spoke thiếu kỹ năng mới vừa phát hành ở Hub | Tại Spoke, chạy [`/ccba-update-spoke`](../../ccba-update-spoke/SKILL.md) (hoặc đọc tạm qua `$CCBA_HUB_PATH` ở chế độ chỉ đọc). |

---

## 4. Công Thức Viết Khối Prompt 1-Click (Cho Khối 3 Chế Độ A)

Mọi prompt mẫu mà `/ccba-ask` xuất cho người dùng copy-paste (tối đa **1 khối** mỗi lượt) nên gói gọn theo cấu trúc **`Lệnh + Mục tiêu (Goal) + Tệp neo (Pointers) + Tiêu chí xong (Done Check)`**:

- **Khởi động nghiên cứu / rà soát trên phiên mới:**
  ```text
  /ccba-research Đọc .md/workspace_context.yaml, .md/knowledge/session_learnings.md và <đường-dẫn-map-hoặc-báo-cáo>. Khảo sát code-first <phạm-vi>, lập ma trận Giá trị × Độ phức tạp × Rủi ro × KISS (chỉ đọc, chưa sửa mã).
  ```
- **Chốt thiết kế lát cắt trước khi mở nhánh:**
  ```text
  /ccba-grilling Chốt thiết kế cho <tên-lát-cắt> bám <tài-liệu-nguồn>. Tự tra cứu codebase trước, hỏi từng câu một ở Frontier kèm đề xuất mặc định.
  ```
- **Thực thi 1 ticket độc lập trên phiên sạch:**
  ```text
  /ccba-implement Triển khai <mã-ticket> trên nhánh <tên-nhánh> theo <đường-dẫn-tickets.md>. Done means: pytest + verify-patch exit 0, diff <= 200 LOC.
  ```
- **Chốt phiên & phát hành:**
  ```text
  /ccba-create-pr Đóng gói các commit đã kiểm định trên nhánh hiện tại thành PR kèm bằng chứng verify-patch (sau khi CI xanh, chạy tiếp /ccba-release-feature rồi /ccba-session-retrospective).
  ```

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
