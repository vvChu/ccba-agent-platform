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
> - **Chia sẻ tài liệu giữa các kỹ năng User-invoked (`Shared Reference` — `SKILL-MECHANICS.md` v1.3.2):** Vì các kỹ năng `disable-model-invocation: true` không thể tự kích hoạt lẫn nhau, mọi tài liệu tham chiếu dùng chung giữa hai kỹ năng User-invoked bắt buộc phải được tách ra thành tệp tham chiếu độc lập bên ngoài (`references/*.md` hoặc `docs/`) để cả hai cùng dẫn chiếu tới.

---

## 2. Con Trỏ Ngữ Cảnh (`Context Pointers`), Từ Khóa Dẫn Đường (`Leading Words`) & Frontmatter

Một dòng mô tả (`description`) của kỹ năng Model-invoked hoặc một dòng chỉ dẫn trong `AGENTS.md` chính là một **Con trỏ ngữ cảnh (`Context Pointers` — `writing-for-agents` v1.3.2)**: nó vừa nêu tên tài liệu đích, vừa mã hóa điều kiện kích hoạt để Agent tìm đến tài liệu đó. **Từ ngữ của con trỏ** (chứ không phải nội dung tài liệu đích) quyết định độ tin cậy khi Agent triệu hồi tài liệu. Một tài liệu quan trọng nằm sau một con trỏ diễn đạt yếu ớt là một **lỗi biến thiên hành vi (variance bug)**: hãy mài sắc từ ngữ của con trỏ trước, và chỉ nhúng thẳng (inline) nội dung khi việc mài sắc không đủ.

- **Đặt từ khóa dẫn đường lên đầu (`Leading Words`):** Một *leading word* (như `tight`, `red`, `relentless`, `tracer bullets`) là khái niệm cô đọng đã có sẵn trong tiền huấn luyện của mô hình. Khi lặp lại nhất quán dưới dạng một token đơn lẻ trong cả prompt, tài liệu và codebase, nó neo chặt cả **khả năng kích hoạt (invocation)** ở con trỏ lẫn **hành vi thực thi (execution)** trong thân bài với chi phí token thấp nhất.
- **Mỗi nhánh công việc chỉ có một trigger duy nhất.** Tránh trùng lặp từ đồng nghĩa (Ví dụ: viết "xây dựng tính năng bằng TDD ... yêu cầu phát triển hướng test-first" là lặp lại một nhánh hai lần).
- **Cắt tỉa các thông tin thừa đã có sẵn trong body.** Giữ phần mô tả tập trung tuyệt đối vào triggers và điều kiện gọi.

---

## 3. Phân tầng thông tin (Information Hierarchy) & Chống Kéo Sớm (`Post-Completion Pull`)

Nội dung của một kỹ năng được xây dựng từ hai thành phần: **các bước (steps)** và **tài liệu tham chiếu (reference)**:

1.  **Bước trong kỹ năng (In-skill step) — Độ rõ ràng (`Clarity`) & Độ đòi hỏi (`Demand`):**
    - Các hành động tuần tự trong `SKILL.md`. Mỗi bước bắt buộc phải kết thúc bằng **Tiêu chí hoàn thành (Completion Criterion)** hội tụ đủ 2 thuộc tính:
      - **Độ rõ ràng (`Clarity`) chống Sức hút Hậu hoàn thành (`Post-Completion Pull`):** Các bước kế tiếp đang hiển thị trước mắt luôn tạo ra lực hút kéo sự chú ý của Agent sang việc *"sắp xong rồi"*, gây ra lỗi **Hoàn thành non (Premature Completion)**. Hãy bảo vệ bước hiện tại bằng cách mài sắc ranh giới hoàn thành trước; nếu tác vụ vẫn bị vội vã, hãy tách chuỗi bước qua một **ranh giới ngữ cảnh thực sự** (ủy quyền cho subagent với `fresh context window` hoặc handoff, vì gọi inline vẫn để lộ các bước sau trong cùng ngữ cảnh).
      - **Độ đòi hỏi (`Demand`) thúc đẩy Đào sâu (`Legwork`):** Viết tiêu chí đòi hỏi tính vét cạn (*"mọi model sửa đổi đều được đối soát"* thay vì *"xuất danh sách thay đổi"*) để buộc Agent tự đào sâu kiểm chứng.
2.  **Tham chiếu trong kỹ năng (In-skill reference):** Định nghĩa, quy tắc hoặc sự thật được tra cứu khi cần thiết trong `SKILL.md`. Giữ nguyên tắc **Đồng định vị (Co-location)**: gom định nghĩa, quy tắc và ngoại lệ của cùng một khái niệm dưới một tiêu đề duy nhất thay vì rải rác nhiều nơi.
3.  **Tham chiếu ngoài (Disclosed / External reference):** Các tài liệu được đẩy ra ngoài `SKILL.md` và dẫn chiếu qua **Liên kết tương đối (Relative Link)** đến các file Markdown sibling hoặc thư mục `references/` để giữ cho tệp tin chính gọn gàng (**Progressive Disclosure**). Nhánh nào mọi lần chạy đều cần thì giữ inline; nhánh nào chỉ một số trường hợp mới chạm tới thì đẩy ra sau con trỏ.
4.  **Môi trường là Nguồn chân lý (`Environment as SSoT` vs Document as Cache):** Môi trường thực thi (`pyproject.toml`, `package.json`, cấu trúc thư mục, đầu ra `--help`) tự thân là nguồn chân lý sống. Một tài liệu chép lại các thông tin tra cứu 1 lệnh từ môi trường chỉ là một **bản cache dễ lỗi thời**. Chỉ ghi vào tài liệu những quy ước bất thành văn, lý do đằng sau quyết định thiết kế, và các bẫy ngầm (gotchas) mà cấu hình không tự nói ra.

5.  **Nhánh xử lý (Branch):** Khi skill có nhiều nhánh xử lý (branches), mỗi nhánh được coi là một mini-process riêng biệt. Nếu nhánh chứa steps, mỗi nhánh phải có **Tiêu chí hoàn thành** riêng. Nếu nhánh phức tạp hoặc có nhiều tham số, tách chi tiết ra file sibling (ví dụ: `MODES.md`) theo Progressive Disclosure.

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

## 8. Quy Chuẩn Vận Hành Của Nhà Máy Tạo Kỹ Năng (`ccba-build-skill` v1.1.0)

Để đảm bảo tính nhất quán toàn diện khi tác tạo kỹ năng mới, quy trình `/ccba-build-skill` bắt buộc phải tuân thủ 6 hợp đồng kiến trúc bất biến sau:

1. **Pre-flight Môi Trường & Bảo Tồn Upstream (Hub vs. Spoke):**
   - Đọc `git remote get-url origin`.
   - Nếu ở Spoke: Kiểm tra bắt buộc biến môi trường `CCBA_HUB_PATH`. Thư mục Hub phải tồn tại, là checkout git sạch (`git status --porcelain` rỗng), khác toplevel Spoke, và chưa có nhánh `proposal/<tên-skill>`. Nếu thiếu điều kiện, DỪNG ngay. Cấm tự ý `git checkout main` hay `git pull` trên Hub. Định tuyến tạo file sang `$CCBA_HUB_PATH` trên nhánh `proposal/<tên-skill>`. Việc mở PR về Hub phải có xác nhận tường minh của người dùng qua `/ccba-contribute-to-hub`.
2. **Định Tuyến Nguồn Theo Phân Loại Bảo Mật (Per-Source Ingestion & Privacy Guard):**
   - Quét `scripts/maskara.py` từng tệp nguồn. Có findings $\rightarrow$ DỪNG nguồn đó.
   - Nguồn công khai $\rightarrow$ Cloud RAG (`notebooklm_rag.v1`). Nguồn mật / nhạy cảm / `--local` $\rightarrow$ Local Fallback qua pipeline tài liệu (`ccba-markdown-document-processing`) và `model_routing.v1` (`choose_model()`).
   - Cẩm nang tri thức tạm thời bắt buộc lưu tại buffer `.md/scratch/build-skill/<tên-skill>/summary.md`. CẤM ghi trực tiếp vào `.md/knowledge/` dài hạn của repo trước khi hoàn tất nghiệm thu. Văn bản quy phạm pháp luật chuyển `/ccba-legal-ingest`.
3. **Cổng Kiến Trúc Định Lượng Bằng JSON CLI Tất Định:**
   - Bắt buộc thực thi: `python -m ccba_harness evaluate-gpi --name <name> --s <S> --k <K> --a <A> --p <P> --json` kèm 4 dòng bằng chứng quan sát được.
   - Greenfield bỏ `--existing-tier` và `--force-tier-flip`.
   - Quyền tạo skill độc lập nằm ở trường JSON: `tier == "tier-2b"` và `allow_standalone_skill == true`. Nếu không thỏa mãn, DỪNG tạo Standalone Kernel Skill và chuyển sang Tier 2A Reference (`references/<name>.md`). Sao chép chính xác 4 số $S, K, A, P$ từ JSON vào frontmatter.
4. **Full-Stack Scaffolding & Naming Contract cho `resolve_domain_dataset()`:**
   - Khi tạo Standalone Kernel Skill (Tier 2B), bắt buộc sinh kèm tệp ca kiểm thử mẫu tại:
     `.agents/skills/ccba-eval-gate/test_cases/eval_<stem>.json`
   - Quy ước tên: `<stem>` là tên skill đã bỏ tiền tố `ccba-`/`bigbim-` và đổi dấu gạch ngang `-` thành gạch dưới `_` (ví dụ: `ccba-legal-intel` $\rightarrow$ `eval_legal_intel.json`).
   - Kiểm tra chống ghi đè: Nếu tệp đã tồn tại, DỪNG LẠI và cảnh báo.
   - Schema JSON là mảng 2 phần tử: 1 ca happy-path (yêu cầu các token vận hành thật: `evaluate-gpi --json`, `allow_standalone_skill`, Maskara) và 1 ca red-team test (yêu cầu Agent dừng khi gặp tác vụ tất định, tài liệu mật, hoặc Spoke thiếu Hub path).
5. **Vòng Lặp Tự Phục Hồi (Self-Healing Loop) Có Allowlist Nghiêm Ngặt:**
   - Khi `verify-patch --preset skill` thất bại: Tối đa 2 lần thử lại, kiểm soát bộ đếm ngoài prompt.
   - **Allowlist được sửa:** Cú pháp YAML frontmatter, liên kết tương đối hỏng, tiêu chí hoàn thành, chạy lại `compile_catalog.py`.
   - **Danh mục CẤM:** CẤM sửa các hệ số $S, K, A, P$ trong khối `gpi:`, CẤM đảo ngược Cổng 0/1, CẤM gọi lại đệ quy `/ccba-build-skill`.
   - Nếu sau 1 lần sửa mà hash SHA-256 của tệp không đổi $\rightarrow$ DỪNG NGAY. Hết 2 lần vẫn lỗi $\rightarrow$ Dừng theo ADR-0058 Hard Completion Lock.
6. **Kiểm Định Toàn Diện của Bản Thân Kỹ Năng:**
   - Mọi thay đổi đối với `ccba-build-skill` phải vượt qua `verify-patch --preset skill --target .agents/skills/ccba-build-skill`, đồng bộ catalog (`compile_catalog.py`), đồng bộ portal (`compile_skills_docs.py --write`), và kiểm thử hợp đồng tự động.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
