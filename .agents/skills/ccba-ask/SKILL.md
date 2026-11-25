---
name: ccba-ask
description: Tư vấn định hướng kỹ năng theo trạng thái phiên, điều phối động não và giải thích đơn giản hóa.
disable-model-invocation: true
bundle: _core
scope: universal
posture: seam-exempt
tier: kernel
user-invocable: true
command: /ccba-ask
gpi:
  s: 3.0
  k: 3.0
  a: 1.0
  p: 1.0
triggers:
- ccba-ask
- tư vấn
- định hướng
- luồng công việc
- bản đồ kỹ năng
- ccba-wait-what
- wait-what
- ccba-brainstorm
- brainstorm
metadata:
  author: CCBA
  version: "1.4.0"
---

# Bản Đồ Định Hướng Kỹ Năng & Tư Vấn Trạng Thái Nền Tảng (CCBA Ask v1.4.0)

Kỹ năng này hoạt động như **Copilot Định hướng Trạng thái (State-Aware Router)**, **Huấn luyện viên Động não (Brainstorm Coach)** và **Bộ Giải thích & Tóm lược (Clarify & Explain)** cho toàn hệ sinh thái Hub–Spoke CCBA.

> [!IMPORTANT]
> **Khóa Cứng Chỉ Đọc (`Read-Only Consultation — Mention ≠ Invoke`):**
> Khi người dùng gọi `/ccba-ask` để hỏi, so sánh hoặc kiểm tra tính phù hợp có nhắc tên lệnh khác (lệnh built-in của host như `plan`, `/grill-me`, `/learn`, `teamwork`, `swarm` hoặc các lệnh `/ccba-*`), Agent **CHỈ TƯ VẤN — TUYỆT ĐỐI CẤM tự ý thực thi lệnh bị nhắc và CẤM ghi/sửa tệp hay chạy lệnh biến đổi trạng thái**. Ngoại lệ ghi tệp duy nhất là xuất *Session Document* tại Bước 5 Chế độ B sau khi người dùng xác nhận rõ ràng.
>
> **Nguồn tin cậy:** Đối chiếu bản đồ cốt lõi bên dưới; chỉ đọc [catalog.yaml](../platform-loader/catalog.yaml) khi người dùng nhắc tên kỹ năng chuyên ngành nằm ngoài bản đồ này hoặc cần kiểm tra lệnh hợp lệ tại repo hiện tại.

## 🧭 Bảng Phân Tuyến 3 Chế Độ Hoạt Động (3-Mode Intent Dispatch)

| Chế độ (Mode) | Tín hiệu kích hoạt (Trigger Signals) | Hành động bắt buộc của Agent |
| :--- | :--- | :--- |
| **Chế độ A: Định hướng & Tư vấn Trạng thái (`State-Aware Router`)** | Gọi trơn `/ccba-ask`, *"tiếp theo?"*, *"ở đây hay mở phiên mới?"*, *"nên chọn phương án nào?"*, so sánh lệnh built-in vs `/ccba-*`, hoặc hỏi *"dùng skill nào?"* | Chỉ kiểm tra trạng thái thật làm thay đổi câu trả lời (`git status` và nhánh, `tickets.md` hoặc `map.md`, `verify-*`), đối chiếu bản đồ **Idea $\to$ Ship**, nạp [`references/phase_boundaries.md`](references/phase_boundaries.md) hoặc [`references/builtin_vs_ccba.md`](references/builtin_vs_ccba.md) khi cần, và xuất đúng **Hợp đồng Đầu ra 4 Khối**. |
| **Chế độ B: Huấn luyện viên Động não (`Brainstorm Coach`)** | Gọi `/ccba-ask brainstorm [chủ đề]`, `-- <topic_id>`, truyền thẳng URL YouTube / ghi chú ngoài kèm yêu cầu *brainstorm / phát tán ý tưởng / party mode* | **Nạp ngay** [`references/brainstorm_templates.md`](references/brainstorm_templates.md), [`references/brainstorm_techniques.md`](references/brainstorm_techniques.md) và [`resources/brainstorm_topics.yaml`](resources/brainstorm_topics.yaml). Điều phối URL YouTube qua [`/ccba-youtube-learn`](../ccba-youtube-learn/SKILL.md), đọc tại chỗ ghi chú `.md`/`.txt` ngoài, rồi chạy **Hybrid Rhythm 4 nhịp**, **Party Mode**, **Problem-First** hoặc **Reframe**. |
| **Chế độ C: Giải thích & Tóm lược (`Clarify & Explain`)** | Gõ `wait-what`, *"khoan đã, chưa hiểu"*, *"giải thích skill X"*, hoặc *"ý nghĩa đợt nâng cấp/phiên trước?"* | **Dừng thực thi ngay lập tức**, nạp [`references/clarification_patterns.md`](references/clarification_patterns.md). Nếu giải thích kỹ năng: **quy chuẩn CCBA bắt buộc đọc tệp `SKILL.md` đích trước khi kết luận**. Nếu tóm lược phiên/PR: ưu tiên *Waiting Calls + 1 khuyến nghị chính + rủi ro*. |

---

## Luồng Công Việc Chính: Ý Tưởng $\to$ Phát Hành (`Idea → Ship`)

1. **Khơi nguồn, Bản đồ & Phản biện (Ideation & Convergence):**
   - Phát tán ý tưởng sáng tạo / đa góc nhìn: **Chế độ B của `/ccba-ask`** ([`brainstorm_templates.md`](references/brainstorm_templates.md)).
   - Bài toán lớn, mơ hồ trải nhiều sóng hoặc nhiều kho: lập bản đồ quyết định bằng [`/ccba-wayfinder`](../ccba-wayfinder/SKILL.md) (trước khi bẻ spec).
   - Phỏng vấn xoáy & stress-test từng lát cắt/thiết kế UI: [`/ccba-grilling`](../ccba-grilling/SKILL.md).
2. **Khởi tạo nhánh & Quản lý ranh giới phiên (Branch & Context Hygiene):**
   - Tạo nhánh, khóa nhận việc (`Claim Lock`) và kiểm toán kế hoạch: [`/ccba-new-feature`](../ccba-new-feature/SKILL.md).
   - Đóng gói bàn giao sang phiên/kho/công cụ khác: [`/ccba-handoff`](../ccba-handoff/SKILL.md) (xem cây quyết định tại [`references/phase_boundaries.md`](references/phase_boundaries.md)).
3. **Đặc tả & Phân rã lát cắt dọc (Spec & Slicing):**
   - Tổng hợp PRD/Spec và bẻ ticket độc lập (**Atomic Micro-PR $\le 200$ LOC**): [`/ccba-to-spec`](../ccba-to-spec/SKILL.md).
4. **Triển khai & Ủy quyền Tác nhân (Coding & Delegation):**
   - Thực thi từng ticket trên phiên sạch: [`/ccba-implement`](../ccba-implement/SKILL.md); thực thi song song đa seam: [`/ccba-teamwork`](../ccba-teamwork/SKILL.md).
   - **Chỉ thị nạp bắt buộc về ủy quyền:** Trước mọi lời gọi `invoke_subagent`, `run_workflow`, hoặc [`/ccba-teamwork`](../ccba-teamwork/SKILL.md), Agent **BẮT BUỘC** nạp [`references/delegation_matrix.md`](references/delegation_matrix.md) và tuân thủ nguyên vẹn các khóa an toàn (`ADR-0035`, `type_name="research"`, `workspace="inherit"`, 3 công cụ đọc, `parallel <= 3`, `finish`).
5. **Kiểm định & Đánh giá Chất lượng (Review & Verification):**
   - Soát diff 2 trục (Tiêu chuẩn + Spec): [`/ccba-code-review`](../ccba-code-review/SKILL.md); xây dựng/bảo trì bộ kiểm chứng ứng dụng `verify-*`: [`/ccba-create-verification-skill`](../ccba-create-verification-skill/SKILL.md); chạy cổng kiểm định tất định: `python -m ccba_harness verify-patch` ([`/ccba-eval-gate`](../ccba-eval-gate/SKILL.md)).
6. **Mở PR, Phát hành & Đúc kết (Ship & Retro):**
   - Mở PR và làm xanh CI/Review cho repo hiện tại (Hub/nội bộ Spoke) qua [`/ccba-create-pr`](../ccba-create-pr/SKILL.md); chỉ đóng góp ngược Spoke → Hub qua [`/ccba-contribute-to-hub`](../ccba-contribute-to-hub/SKILL.md).
   - Hợp nhất PR, dọn nhánh và chốt walkthrough: [`/ccba-release-feature`](../ccba-release-feature/SKILL.md).
   - Đúc kết bài học vào `session_learnings.md` và vệ sinh phiên: [`/ccba-session-retrospective`](../ccba-session-retrospective/SKILL.md).

## Luồng Bổ Trợ & Vận Hành Hub–Spoke (On-ramps & Upkeep)

* **Đồng bộ Spoke & Đánh giá Thượng nguồn:** Cập nhật Spoke từ Hub qua [`/ccba-update-spoke`](../ccba-update-spoke/SKILL.md); thẩm định đề xuất từ Spoke qua [`/ccba-review-proposal`](../ccba-review-proposal/SKILL.md); so sánh/chuyển hóa kho thượng nguồn qua [`/ccba-xia`](../ccba-xia/SKILL.md); sàng lọc backlog/issue thô qua [`/ccba-issue-to-hub`](../ccba-issue-to-hub/SKILL.md).
* **Nghiên cứu & Cải tiến Kiến trúc:** Nghiên cứu sâu nguồn gốc/tài liệu qua [`/ccba-research`](../ccba-research/SKILL.md); làm sâu module và tối ưu kiến trúc codebase qua [`/ccba-codebase-design`](../ccba-codebase-design/SKILL.md).
* **Kỹ năng chuyên ngành khác** (PCCC, BIM, Pháp lý, TDD, Issue Tree, Văn phòng, Seminar): tra trực tiếp trong [catalog.yaml](../platform-loader/catalog.yaml) khi yêu cầu thuộc đúng chuyên ngành đó.

---

## Quy Trình Tư Vấn Định Hướng & Điều Phối (Process)

1. **Nhận diện Chế độ & Kiểm tra Trạng thái tối thiểu (State-Check):**
   - Phân loại yêu cầu vào **Chế độ A**, **Chế độ B**, hoặc **Chế độ C** và áp dụng tuyệt đối khóa **Read-Only (`Mention ≠ Invoke`)**.
   - Với **Chế độ B** hoặc **Chế độ C**: nạp ngay tệp Level 3 tương ứng và thực thi quy trình chuyên biệt đó.
   - Với **Chế độ A**: chỉ kiểm tra trạng thái thật có thể làm đổi khuyến nghị (nhánh git/working tree, tiến độ `tickets.md`/`map.md`, tình trạng đồng bộ Spoke/Hub); nếu câu hỏi so sánh built-in hoặc gặp triệu chứng lệch luồng, nạp [`references/builtin_vs_ccba.md`](references/builtin_vs_ccba.md).
   - **Tiêu chí hoàn thành:** Phân loại đúng chế độ (A/B/C), giữ nguyên trạng thái chỉ đọc (không tự chạy lệnh bị nhắc), và chỉ đọc đúng tệp ngữ cảnh cần thiết.

2. **Kết xuất Đầu ra Chuẩn hóa (Output Contract):**
   - Với **Chế độ A**, trình bày ngắn gọn theo đúng **4 khối chuẩn**:
     - **(1) Khuyến nghị chính (1 lựa chọn mặc định):** Chốt rõ nên làm gì nhất lúc này kèm lý do 1–2 dòng (nếu đang giữa phiên dài, liệt kê gọn *Waiting Calls* và rủi ro).
     - **(2) Ranh giới phiên (`Continue` vs `Mở phiên mới`):** Nêu dứt khoát nên tiếp tục tại đây, `/compact`, `/ccba-handoff`, hay mở phiên mới theo [`references/phase_boundaries.md`](references/phase_boundaries.md).
     - **(3) Khối lệnh/Prompt 1-Click (tối đa 1 khối):** Xuất đúng 1 lệnh hoặc prompt mẫu copy-paste sẵn (gồm `Goal + Done Check`) để người dùng gửi thẳng.
     - **(4) Sơ đồ Mermaid có điều kiện:** Chỉ vẽ khi luồng có rẽ nhánh hoặc chuỗi $\ge 3$ bước; tối đa **6 nút**, mỗi nút **$\le 8$ từ**; **CẤM** vẽ danh sách trạng thái thành sơ đồ.
   - Với **Chế độ B**: hiển thị chủ đề từ [`resources/brainstorm_topics.yaml`](resources/brainstorm_topics.yaml), gợi ý kỹ thuật từ [`references/brainstorm_techniques.md`](references/brainstorm_techniques.md) và đặt đúng **1 câu hỏi mở đầu tiên**.
   - Với **Chế độ C**: trả lời trực diện bằng ngôn ngữ đời thường (sau khi đọc `SKILL.md` đích nếu giải thích skill) và hỏi xác nhận trước khi bước tiếp.
   - **Tiêu chí hoàn thành:** Hoàn tất đủ 4 khối đầu ra Chế độ A (có chốt 1 phương án mặc định và 1 lệnh/prompt mẫu) hoặc khởi chạy đúng vòng tương tác đầu tiên của Chế độ B/C mà không phát sinh ghi tệp trái phép.

---

## Progressive Disclosure & Reference Index (Level 3)

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/phase_boundaries.md` | Cây quyết định ranh giới pha: Continue, `/clear`, `/ccba-handoff`, Subagent, `/compact` |
| `references/builtin_vs_ccba.md` | So sánh Built-in Antigravity vs `/ccba-*`, *Close Calls*, bảng *Symptom $\to$ Fix* và *Prompt Recipes 1-Click* |
| `references/delegation_matrix.md` | Ma trận Định tuyến Ủy quyền 3 Cấp (`invoke_subagent`, `run_workflow`, `/ccba-teamwork`) kèm khóa an toàn bắt buộc |
| `references/clarification_patterns.md` | Mẫu Chế độ C: *Wait-What* đời thường, *Explain Skill* (đọc đích trước) và *Catch-Up Phiên/PR* |
| `references/brainstorm_templates.md` | Quy trình 6 bước Brainstorming (nạp URL YouTube / note ngoài, Hybrid Rhythm 4 nhịp, Party Mode, Pre-Flight Conviction) |
| `references/brainstorm_techniques.md` | Thư viện 15 kỹ thuật động não (gồm SCAMPER, 6 Hats, Reversal, 5 Whys, Problem-First, Reframe) |
| `resources/brainstorm_topics.yaml` | Danh mục chủ đề, từ khóa nhận diện và kỹ năng đi kèm cho phiên Brainstorming |

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
