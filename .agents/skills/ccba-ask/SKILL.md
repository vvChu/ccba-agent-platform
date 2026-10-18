---
name: ccba-ask
description: Tư vấn và định hướng lựa chọn kỹ năng hoặc workflow phù hợp với nhu cầu
  phát triển.
disable-model-invocation: true
bundle: _core
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
  version: "1.2.0"
---

# Bản đồ Định hướng Kỹ năng & Điều phối Tư duy Nền tảng (CCBA Ask & Brainstorm Guide)

Kỹ năng này giúp định tuyến, định hướng cho cả AI Agent và Nhà phát triển để lựa chọn đúng Slash Command hoặc Kỹ năng (Skill) phù hợp nhất với trạng thái công việc hiện tại, đồng thời tích hợp trực tiếp **Huấn luyện viên Động não (Brainstorm Coach)** và **Giải thích Đơn giản hóa (Wait-What)**.

> [!IMPORTANT]
> **Nguồn tin cậy (Source of Truth):**
> Tất cả các Slash Command trong tài liệu này đều được định tuyến dựa trên danh mục dịch vụ tại [catalog.yaml](../platform-loader/catalog.yaml). Vui lòng kiểm tra danh mục này trước khi thực thi để đảm bảo lệnh đã được đăng ký thành công trong phân vùng (spoke) hiện tại.

## 🏛️ Platform-Aware Architecture Posture

- **Phân loại**: Kỹ năng hạt nhân định hướng quy trình (seam-exempt kernel skill).
- **Lý do miễn trừ seam**: SOP điều phối và tư vấn Slash Command / Kỹ năng phù hợp cho người dùng và Agent, tích hợp quy trình động não (Brainstorming) và làm rõ ngữ cảnh (Wait-What), không trực tiếp ràng buộc API package runtime.
- **Đặc tính quản trị**: Cung cấp bảng phân tuyến 3 chế độ hoạt động, bản đồ luồng công việc từ ý tưởng đến phát hành (Idea -> Ship) theo Factory Model và các luồng bổ trợ upkeep kiến trúc theo danh mục `catalog.yaml` chuẩn hóa.
- **Chỉ số năng lực quản trị (GPI)**: Đạt mức điểm chuẩn hóa (s=3.0, k=3.0, a=1.0, p=1.0) -> GPI = 14.0 (Tier 2B kernel), tuân thủ phân lớp governance và hướng dẫn tương tác người dùng.

---

## 🧭 Bảng Phân Tuyến 3 Chế Độ Hoạt Động (3-Mode Intent Dispatch)

Khi người dùng gọi `/ccba-ask`, Agent **BẮT BUỘC** nhận diện ý định đầu vào để kích hoạt đúng chế độ ngay lập tức:

| Chế độ (Mode) | Tín hiệu kích hoạt (Trigger Signals) | Hành động bắt buộc của Agent |
| :--- | :--- | :--- |
| **Chế độ A: Định hướng Kỹ năng (Skill & Workflow Router)** | Người dùng hỏi *"Dùng skill nào?", "Luồng công việc là gì?", "Bắt đầu từ đâu?"* | Đối chiếu bản đồ **Idea $\to$ Ship** bên dưới và `catalog.yaml` để tư vấn Slash Command kèm sơ đồ luồng công việc. |
| **Chế độ B: Huấn luyện viên Động não (Interactive Brainstorm Coach)** | Người dùng gọi `/ccba-ask brainstorm [chủ đề]`, `-- <topic_id>`, hoặc yêu cầu *brainstorm / phát tán ý tưởng / party mode* | **Nạp ngay** [`references/brainstorm_templates.md`](references/brainstorm_templates.md), [`references/brainstorm_techniques.md`](references/brainstorm_techniques.md) và [`resources/brainstorm_topics.yaml`](resources/brainstorm_topics.yaml) để khởi chạy vòng lặp **Hybrid Rhythm 4 nhịp** (1 câu hỏi mở $\to$ User trả lời $\to$ AI mở rộng 2-4 ý tưởng `yes-and` $\to$ Trả sàn) hoặc **Party Mode** đa vai. |
| **Chế độ C: Giải thích Đơn giản hóa (Wait-What Clarification)** | Người dùng gõ `wait-what`, *"Khoan đã, chưa hiểu"*, hoặc yêu cầu giải thích lại tin nhắn trước | **Dừng thực thi ngay lập tức**, nạp [`references/clarification_patterns.md`](references/clarification_patterns.md) và trình bày lại ý chính bằng ngôn ngữ đơn giản kèm thuật ngữ chuẩn trong `CONTEXT.md`. |

---

## Luồng công việc chính: Từ Ý tưởng đến Phát hành (Idea → Ship — Factory Model)

Đây là lộ trình chuẩn của mọi yêu cầu phát triển tính năng mới trong Platform:

1. **Khơi nguồn & Làm sắc nét ý tưởng (Ideation & Stress-Test):**
   - **Phát tán ý tưởng sáng tạo (Divergent Brainstorming):** Kích hoạt **Chế độ B của `/ccba-ask`** ([`brainstorm_templates.md`](references/brainstorm_templates.md)) để chạy Hybrid Rhythm 4 nhịp hoặc Party Mode đa góc nhìn mà không phán xét sớm (*Deferred Judgment*).
   - **Phân rã cấu trúc MECE:** Với bài toán đa chiều phức tạp, chẩn đoán nguyên nhân gốc rễ (Why-Tree) hoặc so sánh chiến lược (How/What-Tree), triệu hồi [`/ccba-issue-tree`](../ccba-issue-tree/SKILL.md).
   - **Phỏng vấn xoáy & hội tụ thiết kế (Convergent Grilling):** Gọi [`/ccba-grilling`](../ccba-grilling/SKILL.md) để phỏng vấn Socrates dồn dập, hội tụ UI prototype (Nhánh C) và ghi nhận quyết định vào `CONTEXT.md` / ADRs.
2. **Khởi tạo nhánh & Lập kế hoạch Nhà máy (Factory Branch & Pre-Plan Gate):**
   - Chạy [`/ccba-new-feature`](../ccba-new-feature/SKILL.md) để dọn nhánh cũ, khóa nhận việc (`Claim Lock`), kiểm toán tính hợp lý (**Problem-Validity, Scale & OBE Gate**) và lập kế hoạch thiết kế.
   - Nếu cần bàn giao ngữ cảnh giữa các pha, tham khảo [`references/phase_boundaries.md`](references/phase_boundaries.md) và dùng [`/ccba-handoff`](../ccba-handoff/SKILL.md).
3. **Đặc tả & Phân rã tác vụ (Spec & Tracer-Bullet Slicing):**
   - Sử dụng [`/ccba-to-spec`](../ccba-to-spec/SKILL.md) để tổng hợp thành Đặc tả Kỹ thuật (PRD/Spec) và bẻ nhỏ thành các ticket độc lập dạng lát cắt dọc (**Atomic Micro-PR $\le 200$ LOC**).
4. **Triển khai lập trình (Coding & Multi-Agent Execution):**
   - Mở cửa sổ Agent sạch và chạy [`/ccba-implement`](../ccba-implement/SKILL.md) (hoặc [`/ccba-tdd`](../ccba-tdd/SKILL.md)) cho từng ticket độc lập.
   - Với dự án lớn đa gói/đa bộ môn cần chạy song song trên các nhánh cô lập: Triệu hồi [`/ccba-teamwork`](../ccba-teamwork/SKILL.md).
5. **Kiểm soát chất lượng & Cổng Kiểm định Tự động (QC & Deterministic Verification):**
   - Với mã nguồn/kỹ năng: Chạy [`/ccba-eval-gate`](../ccba-eval-gate/SKILL.md) (hoặc `python -m ccba_harness verify-patch`).
   - Với hồ sơ thiết kế xây dựng đa bộ môn: Chạy [`/ccba-ai-qc`](../ccba-ai-qc/SKILL.md) và [`/ccba-ai-qc-pccc-audit`](../ccba-ai-qc-pccc-audit/SKILL.md).
6. **Đóng góp PR & Đúc kết cuối phiên (Ship & Retrospective):**
   - Đóng gói Pull Request và tự động làm xanh CI/Review qua [`/ccba-contribute-to-hub`](../ccba-contribute-to-hub/SKILL.md).
   - Kết thúc phiên làm việc bằng [`/ccba-session-retrospective`](../ccba-session-retrospective/SKILL.md) để đúc kết bài học vào `session_learnings.md` và dọn sạch workspace.

> [!TIP]
> **Context Hygiene (Vệ sinh Context):** Giữ Bước 1–3 trong cùng một cửa sổ context liên tục trước khi bẻ ticket. Mỗi ticket triển khai ở Bước 4 nên chạy trên một phiên làm việc/agent sạch riêng biệt (xem [`references/phase_boundaries.md`](references/phase_boundaries.md)) để tránh cạn kiệt Context Budget.

---

## Các luồng bổ trợ (On-ramps & Upkeep)

*   **Phân rã bài toán phức tạp / Chẩn đoán gốc rễ:** Chạy [`/ccba-issue-tree`](../ccba-issue-tree/SKILL.md) để phân rã vấn đề theo chuẩn MECE (Why-tree chẩn đoán sự cố, How-tree tìm kiếm giải pháp, What-tree lập kế hoạch hành động).
*   **Tiếp nhận yêu cầu thô / Sàng lọc Backlog (Triage):** Chạy [`/ccba-issue-to-hub`](../ccba-issue-to-hub/SKILL.md) để kiểm tra trùng lặp Seam, kiểm toán biên giới Liên bang (`Rule 5 KISS` & `Rule 8`) và tạo RFC Issue hoặc Agent Brief.
*   **Xử lý lỗi hóc búa / Regression:** Sử dụng kỹ năng [`/ccba-diagnosing-bugs`](../ccba-diagnosing-bugs/SKILL.md) để xây dựng vòng phản hồi nhanh và viết test hồi quy trước khi vá lỗi.
*   **Upkeep kiến trúc hệ thống:** Chạy [`/ccba-codebase-design`](../ccba-codebase-design/SKILL.md) để phát hiện các module nông và deepening cấu trúc code.
*   **Không gian học tập & Đào tạo:** Chạy [`/ccba-seminar-builder`](../ccba-seminar-builder/SKILL.md) để khởi động không gian bài giảng/nghiên cứu trong thư mục `.md/teach/`.

---

## Quy trình tư vấn định hướng & điều phối (Process)

1. **Nhận diện Chế độ (Mode Dispatch) & Phân tích trạng thái hiện tại:**
   - Đọc kỹ yêu cầu của người dùng để phân loại vào **Chế độ A (Định hướng Kỹ năng)**, **Chế độ B (Brainstorm Coach)**, hoặc **Chế độ C (Wait-What Clarification)**.
   - Nếu thuộc **Chế độ B** hoặc **Chế độ C**: Nạp ngay tệp tham chiếu Level 3 tương ứng ([`references/brainstorm_templates.md`](references/brainstorm_templates.md) hoặc [`references/clarification_patterns.md`](references/clarification_patterns.md)) và thực thi trực tiếp quy trình đó.
   - Nếu thuộc **Chế độ A**: Xác định xem công việc thuộc luồng chính (`Idea -> Ship`) hay luồng bổ trợ (`Triage / Diagnose / Upkeep`).
   - **Tiêu chí hoàn thành:** Phân loại chính xác chế độ hoạt động (A/B/C) và nạp đúng tài liệu tham chiếu hoặc xác định đúng vị trí công việc trên bản đồ nền tảng.

2. **Khuyến nghị Slash Command hoặc Khởi chạy Phiên Tương tác:**
   - Với **Chế độ A**: Trình bày rõ ràng Slash Command nên chạy tiếp theo (nhúng link file `SKILL.md` tương ứng) kèm tóm tắt 1 dòng lý do lựa chọn và sơ đồ Mermaid luồng công việc kế tiếp.
   - Với **Chế độ B**: Hiển thị danh sách chủ đề từ [`resources/brainstorm_topics.yaml`](resources/brainstorm_topics.yaml), gợi ý kỹ thuật từ [`references/brainstorm_techniques.md`](references/brainstorm_techniques.md) và đặt ngay **1 câu hỏi mở đầu tiên** theo quy tắc Hybrid Rhythm.
   - **Tiêu chí hoàn thành:** Đưa ra đề xuất Slash Command cụ thể kèm sơ đồ luồng (Chế độ A) hoặc khởi chạy thành công vòng tương tác đầu tiên (Chế độ B/C).

---
## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/phase_boundaries.md` | Định vị ranh giới giữa các pha phát triển và thời điểm bàn giao context |
| `references/clarification_patterns.md` | Mẫu câu và kỹ thuật phỏng vấn làm rõ ngữ cảnh khi gặp yêu cầu mơ hồ (`Wait-What`) |
| `references/brainstorm_templates.md` | Quy trình 6 bước khởi chạy phiên Brainstorming (Hybrid Rhythm 4 nhịp & Party Mode) |
| `references/brainstorm_techniques.md` | Các phương pháp tư duy động não (SCAMPER, 6 Thinking Hats, Reversal, 5 Whys) |
| `resources/brainstorm_topics.yaml` | Danh mục chủ đề, từ khóa nhận diện và kỹ năng đi kèm cho phiên Brainstorming |

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

