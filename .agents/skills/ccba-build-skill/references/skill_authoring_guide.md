# ccba-writing-great-skills — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Cẩm nang hướng dẫn kỹ sư biên soạn tệp chỉ dẫn SKILL.md chuẩn mực
> **Mô tả gốc:** Tài liệu cẩm nang hướng dẫn kỹ sư thiết kế và viết các file SKILL.md đạt tiêu chuẩn chất lượng cao.

---

# Cẩm nang Viết Kỹ năng chất lượng cao (Writing Great Skills)

Một kỹ năng (Skill) được tạo ra nhằm thiết lập tính nhất quán (determinism) từ một hệ thống xác suất (stochastic system). **Tính khả đoán (Predictability)** — việc Agent thực hiện đúng cùng một *quy trình* (process) trong mọi lần chạy, chứ không phải sinh ra cùng một output — là phẩm chất cốt lõi; mọi nguyên tắc dưới đây đều phục vụ mục đích đó.

> **Lưu ý:** Skill này là tài liệu tham chiếu thuần túy (all-reference), không chứa bước quy trình (steps). Các mục đánh số dưới đây là quy tắc chất lượng, không phải hướng dẫn tuần tự.

Các thuật ngữ in đậm được định nghĩa tại [skill_glossary.md](./skill_glossary.md); vui lòng đối chiếu để nắm rõ ý nghĩa chi tiết.

---

## 1. Cách thức kích hoạt (Invocation)

Chúng ta có hai lựa chọn kích hoạt, tương ứng với việc đánh đổi các loại chi phí khác nhau:

- **Kích hoạt bởi Mô hình (Model-invoked):** Kỹ năng có phần mô tả (`description`) để Agent tự kích hoạt hoặc được nạp động bởi các kỹ năng khác. Kiểu này tiêu tốn **tải ngữ cảnh (Context Load)** vì phần mô tả phải luôn nằm trong cửa sổ ngữ cảnh. 
  - *Cách dùng:* Bỏ dòng `disable-model-invocation: true` ở frontmatter và viết mô tả hướng đến mô hình kèm các từ khóa kích hoạt rõ ràng ("Dùng khi người dùng muốn..., nhắc đến...").
- **Kích hoạt bởi Người dùng (User-invoked):** Loại bỏ phần mô tả khỏi tầm tiếp cận của Agent — chỉ có lập trình viên gõ tên lệnh (Slash Command) mới có thể kích hoạt. Tiết kiệm tối đa **tải ngữ cảnh**, nhưng tiêu tốn **tải nhận thức (Cognitive Load)** vì lập trình viên phải ghi nhớ sự tồn tại của lệnh đó.
  - *Cách dùng:* Đặt `disable-model-invocation: true` ở frontmatter và phần `description` là một dòng tóm tắt súc tích cho người đọc (độ dài dưới 180 ký tự theo quy chuẩn CCBA).

> [!TIP]
> Chỉ chọn **Model-invoked** khi Agent hoặc các kỹ năng khác bắt buộc phải tự gọi nó một cách tự động. Nếu chỉ chạy thủ công bằng tay, hãy để **User-invoked** để tối ưu hóa token ngữ cảnh. Khi số lượng lệnh User-invoked quá nhiều, hãy giải quyết bằng **Kỹ năng điều phối (Router Skill)** như `/ccba-ask` để dẫn đường.

---

## 2. Viết mô tả Frontmatter

Một phần mô tả của kỹ năng **Model-invoked** thực hiện hai nhiệm vụ: định nghĩa kỹ năng đó là gì và liệt kê các nhánh (branches) kích hoạt nó:

- **Đặt từ khóa dẫn đường lên đầu** (Front-load the leading word) để mô hình nhận diện tức thì.
- **Mỗi nhánh công việc chỉ có một trigger duy nhất.** Tránh trùng lặp từ đồng nghĩa (Ví dụ: viết "xây dựng tính năng bằng TDD ... yêu cầu phát triển hướng test-first" là lặp lại một nhánh hai lần).
- **Cắt tỉa các thông tin thừa đã có sẵn trong body.** Giữ phần mô tả tập trung tuyệt đối vào triggers và điều kiện gọi.

---

## 3. Phân tầng thông tin (Information Hierarchy)

Nội dung của một kỹ năng được xây dựng từ hai thành phần: **các bước (steps)** và **tài liệu tham chiếu (reference)**:

1.  **Bước trong kỹ năng (In-skill step):** Các hành động tuần tự trong `SKILL.md`. Mỗi bước bắt buộc phải kết thúc bằng **Tiêu chí hoàn thành (Completion Criterion)** dưới dạng có thể kiểm chứng được (Agent phân biệt được thế nào là hoàn thành và chưa hoàn thành) và triệt để. Một tiêu chí hoàn thành mơ hồ sẽ dẫn đến lỗi **Hoàn thành non (Premature Completion)**.
2.  **Tham chiếu trong kỹ năng (In-skill reference):** Định nghĩa, quy tắc hoặc sự thật được tra cứu khi cần thiết trong `SKILL.md`.
3.  **Tham chiếu ngoài (External reference):** Các tài liệu được đẩy ra ngoài `SKILL.md` và dẫn chiếu qua **Liên kết tương đối (Relative Link)** đến các file Markdown sibling (ví dụ: `GLOSSARY.md`) hoặc thư mục `references/` để giữ cho tệp tin chính gọn gàng. Đây là nguyên tắc **Bộc lộ dần dần (Progressive Disclosure)**.

4.  **Nhánh xử lý (Branch):** Khi skill có nhiều nhánh xử lý (branches), mỗi nhánh được coi là một mini-process riêng biệt. Nếu nhánh chứa steps, mỗi nhánh phải có **Tiêu chí hoàn thành** riêng. Nếu nhánh phức tạp hoặc có nhiều tham số, tách chi tiết ra file sibling (ví dụ: `MODES.md`) theo Progressive Disclosure.

### 3.1. Thiết kế Kỹ Năng Đa Chế Độ (Multi-Mode Skills) & Tiêu Chí Hoàn Thành Động
Khi kỹ năng hỗ trợ nhiều chế độ chạy qua các cờ dòng lệnh (flags/modes được tách ra file sibling như `MODES.md`):
- **Phân định rõ ràng đầu ra theo mode:** Scope và Pha kết thúc (Deliver) phải chỉ rõ sản phẩm đầu ra tương ứng với từng cờ (ví dụ: `--compare` xuất báo cáo so sánh; `--port`/`--improve` xuất kế hoạch triển khai).
- **Tiêu chí hoàn thành đa nhánh:** Trong phần `Tiêu chí hoàn thành:`, bắt buộc phải có ít nhất một tiêu chí kiểm chứng việc Agent đã thực sự áp dụng logic phân tích chuyên sâu của mode được chọn từ file sibling, tránh việc chỉ kiểm chứng luồng mặc định dẫn tới lỗi Hoàn thành non.
- **Khuyến nghị bước tiếp theo (Next Steps) động:** Hướng dẫn bước kế tiếp phải tương thích với mode thực thi (tránh ép người dùng chạy lệnh implement khi họ chỉ yêu cầu so sánh kiến trúc).
- **Single Source of Truth cho quy tắc cấm cờ:** Các mệnh đề cấm kết hợp cờ (như cấm `--fast + --copy-raw`) phải được định nghĩa duy nhất một lần tại mục `Kết hợp không hợp lệ` trong file sibling, không sao chép lặp lại rải rác trong mô tả của từng cờ.

### 3.2. Chuẩn Mực Kiểm Định Xác Định (Deterministic Verification Standards & ADR-0058 Hard Completion Lock)
Để xóa bỏ hoàn toàn hiện tượng Hoàn thành non (Premature Completion) và Tự chứng nhận (Self-Certification), các kỹ năng phải áp dụng cơ chế kiểm thử máy tính khách quan:
1. **Pha Hoàn tất / Nghiệm thu (Verification & Deliver Phase):** Mỗi kỹ năng có tác vụ can thiệp mã nguồn, tạo tài liệu hoặc thẩm tra kiến trúc bắt buộc phải gắn kết với công cụ `ccba-harness verify-patch` hoặc `verify-doc`.
2. **Sử dụng Verification Presets Một Chạm:**
   - Với kỹ năng lập trình / engineering (`ccba-implement`, `ccba-tdd`): Sử dụng `python -m ccba_harness verify-patch --preset code --target <package_or_dir>` để tự động chạy ruff, mypy, pytest.
   - Với kỹ năng sinh tài liệu / tư vấn định tính (`ccba-legal-advisor`, `ccba-completion-checklist`): Sử dụng `python -m ccba_harness verify-patch --preset doc --target <file_path> --min-bytes <n> --required-headings "Heading 1,Heading 2"` để kiểm chứng sự tồn tại, dung lượng tối thiểu và đề mục chuẩn.
   - Với kỹ năng xây dựng / sửa chữa skill (`ccba-build-skill`, `/skill-repair`): Sử dụng `python -m ccba_harness verify-patch --preset skill --target <skill_path>`.
3. **Quy tắc Khóa Hoàn Thành Cứng (Hard Completion Lock):** Tiêu chí hoàn thành phải nêu rõ: Nếu có bất kỳ lệnh nào trả về Exit Code $\ne 0$, Agent bị cấm tuyệt đối tuyên bố hoàn thành hoặc đề xuất người dùng nghiệm thu. Bắt buộc kích hoạt Fix Loop hoặc dừng lại báo cáo lỗi kèm stderr snippet.

---

## 4. Các lỗi thường gặp (Failure Modes)

-  **Hoàn thành non (Premature Completion):** Agent vội vàng kết thúc tác vụ khi chưa thực sự hoàn thành đầy đủ các bước.
   - *Cách phòng chống:* Thiết lập **Tiêu chí hoàn thành (Completion Criterion)** cực kỳ rõ ràng, định lượng và kiểm chứng được cho mỗi bước.
-  **Trùng lặp (Duplication):** Cùng một quy tắc được lặp lại ở nhiều nơi. Hãy luôn duy trì **Nguồn chân lý duy nhất (Single Source of Truth)**.
-  **Trôi dạt tri thức (Sediment):** Các tri thức cũ, lỗi thời không được cắt tỉa, dọn dẹp (pruning).
-  **Dài dòng/Phình to (Sprawl):** Tệp tin quá dài làm loãng sự chú ý của Agent. Hãy áp dụng **Progressive Disclosure** để đẩy bớt nội dung tham chiếu ra ngoài.
-  **Vô nghĩa (No-op):** Các câu chỉ dẫn thừa thãi mà Agent mặc định đã biết làm (ví dụ: "Agent hãy suy nghĩ kỹ trước khi viết code").
-  **Phủ định (Negation):** Việc điều hướng bằng cấm đoán sẽ phản tác dụng: yêu cầu *đừng nghĩ về một con voi* chỉ làm cho hình ảnh con voi hiển thị rõ ràng hơn trong ngữ cảnh. Hãy luôn gợi ý theo hướng **tích cực (positive)** — nêu rõ hành vi mục tiêu để tránh gọi tên hành vi bị cấm; chỉ giữ lệnh cấm như một rào chắn cứng (hard guardrail) khi không thể diễn đạt tích cực, và ngay cả khi đó, hãy luôn ghép nó với hướng dẫn nên làm gì thay thế.

---

## 5. Quy chuẩn đặc thù của CCBA Platform

Để vượt qua bộ kiểm định linter hệ thống (`validate_skills.py`), kỹ năng phải tuân thủ nghiêm ngặt:
1.  **Độ dài mô tả frontmatter:** Trường `description` của các kỹ năng kích hoạt bởi mô hình (model-invoked, không cấu hình `disable-model-invocation: true`) bắt buộc phải súc tích và có độ dài tối đa là **180 ký tự**.
2.  **Tiêu chí hoàn thành:** Mọi bước hướng dẫn quy trình (dưới các tiêu đề `Process` hoặc `Quy trình`) phải có một dòng bắt đầu bằng `Tiêu chí hoàn thành:` hoặc `Completion Criterion:` chỉ rõ trạng thái hoàn thành định lượng.
3.  **Liên kết tương đối (Relative links):** Mọi dẫn chiếu sang tệp tin khác trong cùng kỹ năng hoặc workspace phải sử dụng relative link hoạt động được, không dùng link tuyệt đối (absolute link) trừ phi đó là tài liệu web ngoài.
4.  **Định danh Namespace & Slash Command Native (ADR 0047):** Mọi kỹ năng CCBA phải đặt tên bắt đầu bằng tiền tố `ccba-*` (hoặc `bigbim-*` đối với kỹ năng BIM) trong thuộc tính `name:`. Thuộc tính `name:` này đóng vai trò là Slash Command native (`/ccba-...`) trong IDE Antigravity mà không cần tạo tệp wrapper trong `.agents/workflows/`. Sau khi tạo hoặc sửa skill, luôn chạy `python scripts/governance/compile_catalog.py` để tự động lập chỉ mục vào `catalog.yaml`.
5.  **Attribution (Ghi nhận nguồn gốc):** Khi skill hoặc nhánh được thích ứng từ nguồn bên ngoài, bắt buộc phải ghi blockquote attribution ngay dưới tiêu đề nhánh/skill, bao gồm: tên nguồn, tác giả, loại giấy phép. Ví dụ: `> Nguồn gốc: Thích ứng từ skill-name của Author (License Type).`

---

## 6. Kiến Trúc Monorepo 3 Tầng & Khung Quyết Định Phân Rã (ADR-0057)

Để loại bỏ hoàn toàn tính cảm tính khi thiết kế năng lực mới, CCBA thiết lập chuẩn kiến trúc 3 tầng và Khung Quyết Định Hai Giai Đoạn (Two-Stage Decision Framework):

### 6.1. Ba Tầng Kiến Trúc Monorepo
1. **Tầng 1 — Deterministic Engines / Packages (`packages/*/src`):**
   - Mã nguồn thuần Python/TypeScript giải quyết các bài toán có tính xác định tuyệt đối (deterministic): regex parsing, AST traversal, I/O nhị phân, thuật toán toán học.
   - Kiểm thử tự động 100% bằng Unit Tests trong CI; tuyệt đối **không chứa prompt**.
2. **Tầng 2 — Cognitive Interfaces (`.agents/skills/` & `references/*.md`):**
   - Các module nhận thức tự đóng gói (self-contained) tuân thủ chuẩn mở *Agent Skills*.
   - Phân cấp rõ ràng giữa **Standalone Kernel Skills** (Tier 2B) và **Progressive References** (Tier 2A).
3. **Tầng 3 — Composite Orchestrators (`.agents/workflows/`):**
   - Đồ thị trạng thái (StateGraph), quy trình phân quyền đa tác tử (Multi-Agent Coordination), hoặc các quy trình yêu cầu con người phê duyệt (Human-in-the-loop / HITL).

### 6.2. Giai Đoạn 1: Hai Cổng Bất Biến (Structural Invariant Gates)
- **Cổng 0 (Determinism Gate):** Nếu tác vụ giải quyết được 100% bằng giải thuật xác định $\rightarrow$ Bắt buộc triển khai tại Tầng 1 (`packages/*/src/`). Nghiêm cấm tạo Skill phẳng độc lập.
- **Cổng 1 (Orchestration Gate):** Nếu tác vụ điều phối đa tác tử song song, yêu cầu StateGraph checkpoints hoặc cần HITL $\rightarrow$ Bắt buộc triển khai tại Tầng 3 (`.agents/workflows/`).

### 6.3. Giai Đoạn 2: Chỉ Số Phân Rã Kỹ Năng (Granularity & Placement Index - GPI)
Áp dụng cho các năng lực nhận thức tại Tầng 2:
$$\mathbf{GPI} = (S \times 2.5) + (K \times 2.0) + (A \times 2.0) - (P \times 1.5)$$

#### Bảng Barem Định Lượng Chi Tiết ($S, K, A, P \in [1.0, 5.0]$)

| Chỉ số | Điểm 1.0 | Điểm 2.0 | Điểm 3.0 | Điểm 4.0 | Điểm 5.0 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **$S$ (Reasoning Steps)** | Thao tác cơ bản, xử lý văn bản thuần, 0-1 bước suy luận | Trích xuất thông tin đơn giản, tóm tắt trực tiếp 2-3 bước | Suy luận phân tích nhiều bước, đối chiếu ngữ cảnh 4-6 bước | Thẩm tra chéo đa chiều, tổng hợp lập luận phức tạp >6 bước | Thẩm định pháp lý/kiến trúc đa bộ môn, phản biện chuyên sâu |
| **$K$ (Interface Complexity)** | 0 tham số hoặc chỉ 1 cờ boolean cơ bản | 1-2 tham số kiểu chuỗi/số đơn giản | 3-5 tham số có kiểm tra kiểu hoặc lựa chọn (enum) | Schema JSON/YAML phức tạp, cấu trúc lồng nhau (nested) | Schema động đa tầng, chuyển đổi dữ liệu đa định dạng phức hợp |
| **$A$ (Autonomous Invocation)** | User Ritual thuần túy (`disable-model-invocation: true`) | Hiếm khi gọi tự động, chỉ kích hoạt khi có trigger rất hẹp | Thường xuyên được nạp tự động qua bộ định tuyến Agent | Thiết yếu cho chu trình giải quyết vấn đề tự động (Autonomous loop) | Core engine nền tảng, Agent bắt buộc phải nạp trong system prompt |
| **$P$ (Parent Domain Coupling)** | Hoàn toàn độc lập, không gắn với Master Skill nào (Root skill) | Liên hệ lỏng lẻo với một miền chuyên môn | Phụ thuộc vào quy trình nghiệp vụ của một Master Skill | Gắn kết chặt chẽ vào vòng đời xử lý của Master Skill sở hữu | Là thành phần vi mô phụ trợ, không thể chạy độc lập ngoài Master Skill |

*Lưu ý kiến trúc về trọng số $P$:* Vì $P$ đo lường mức độ gắn kết với Master Skill sở hữu, điểm $P$ càng cao thì năng lực càng nên được đóng gói bên trong Master Skill đó thay vì tách thành kỹ năng độc lập. Do đó, trọng số của $P$ mang dấu âm ($-1.5$). Ví dụ: một tài liệu tham chiếu phụ thuộc cao với $\{s: 2.0, k: 1.0, a: 1.0, p: 2.0\}$ sẽ có $GPI = 5.0 + 2.0 + 2.0 - 3.0 = 6.0 < 12.0$, được định tuyến chính xác về Tier 2A.

#### Quy Tắc Định Tuyến Kiến Trúc
- **$GPI < 12.0$ $\rightarrow$ Tier 2A (Progressive Reference):**
  Lưu trữ dưới dạng tệp tham chiếu tăng tiến tại `.agents/skills/<parent-skill>/references/<name>.md`. Nạp vào ngữ cảnh qua lệnh `view_file` khi Agent thực sự cần đến. Tuyệt đối không tạo thư mục skill riêng.
- **$GPI \ge 12.0$ $\rightarrow$ Tier 2B (Standalone Kernel Skill):**
  Đủ điều kiện tạo thư mục kỹ năng độc lập tại `.agents/skills/ccba-<name>/SKILL.md` và bắt buộc chèn khối frontmatter `gpi:`.

### 6.4. Đặc Tả Khối `gpi:` Bắt Buộc Trong YAML Frontmatter
Mọi Standalone Kernel Skill (Tier 2B) bắt buộc phải khai báo khối `gpi:` định lượng trong YAML frontmatter:
```yaml
---
name: ccba-my-kernel-skill
description: Mô tả ngắn gọn súc tích <= 180 ký tự.
bundle: _software
user-invocable: true
disable-model-invocation: true
command: /ccba-my-kernel-skill
gpi:
  s: 3.5
  k: 2.0
  a: 2.0
  p: 1.0
---
```
*(Cũng hỗ trợ định dạng inline: `gpi: {s: 3.5, k: 2.0, a: 2.0, p: 1.0}`).*

---

## 7. Nguyên Tắc Chống Phình To Mã Nguồn (Script Bloat & Deep Seams)

Nhằm loại bỏ hoàn toàn các "vùng mù kiểm thử" (blind spots) và hiện tượng phình to mã nguồn trong thư mục kỹ năng:
1. **Nghiêm Cấm Script Bloat:** Tuyệt đối không đặt mã nguồn logic nặng, thuật toán phức tạp hoặc vượt quá **100 dòng mã (LOC)** vào thư mục `scripts/` của kỹ năng.
2. **Đưa Logic Về Packages Monorepo:** Toàn bộ mã nguồn giải thuật xác định, thư viện phân tích cú pháp (DOCX/PDF/XML), xử lý regex và kiểm toán dữ liệu bắt buộc phải đóng gói thành các module chuẩn mực trong `packages/*/src/` và được bảo vệ 100% bởi unit test trong CI.
3. **Mô Hình Thin Adapter:** Thư mục `scripts/` bên trong kỹ năng (nếu có) chỉ được đóng vai trò là các thin adapters (tối đa 10–30 LOC), chỉ làm nhiệm vụ nạp tham số CLI và gọi trực tiếp vào các **Deep Seams** của packages monorepo.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
