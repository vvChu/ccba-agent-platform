---
name: writing-great-skills
description: Tài liệu cẩm nang hướng dẫn kỹ sư thiết kế và viết các file SKILL.md đạt tiêu chuẩn chất lượng cao.
disable-model-invocation: true
---

# Cẩm nang Viết Kỹ năng chất lượng cao (Writing Great Skills)

Một kỹ năng (Skill) được tạo ra nhằm thiết lập tính nhất quán (determinism) từ một hệ thống xác suất (stochastic system). **Tính khả đoán (Predictability)** — việc Agent thực hiện đúng cùng một *quy trình* (process) trong mọi lần chạy, chứ không phải sinh ra cùng một output — là phẩm chất cốt lõi; mọi nguyên tắc dưới đây đều phục vụ mục đích đó.

Các thuật ngữ in đậm được định nghĩa tại [GLOSSARY.md](GLOSSARY.md); vui lòng đối chiếu để nắm rõ ý nghĩa chi tiết.

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

---

## 4. Các lỗi thường gặp (Failure Modes)

-  **Hoàn thành non (Premature Completion):** Agent vội vàng kết thúc tác vụ khi chưa thực sự hoàn thành đầy đủ các bước.
   - *Cách phòng chống:* Thiết lập **Tiêu chí hoàn thành (Completion Criterion)** cực kỳ rõ ràng, định lượng và kiểm chứng được cho mỗi bước.
-  **Trùng lặp (Duplication):** Cùng một quy tắc được lặp lại ở nhiều nơi. Hãy luôn duy trì **Nguồn chân lý duy nhất (Single Source of Truth)**.
-  **Trôi dạt tri thức (Sediment):** Các tri thức cũ, lỗi thời không được cắt tỉa, dọn dẹp (pruning).
-  **Dài dòng/Phình to (Sprawl):** Tệp tin quá dài làm loãng sự chú ý của Agent. Hãy áp dụng **Progressive Disclosure** để đẩy bớt nội dung tham chiếu ra ngoài.
-  **Vô nghĩa (No-op):** Các câu chỉ dẫn thừa thãi mà Agent mặc định đã biết làm (ví dụ: "Agent hãy suy nghĩ kỹ trước khi viết code").

---

## 5. Quy chuẩn đặc thù của CCBA Platform

Để vượt qua bộ kiểm định linter hệ thống (`validate_skills.py`), kỹ năng phải tuân thủ nghiêm ngặt:
1.  **Độ dài mô tả frontmatter:** Trường `description` bắt buộc phải súc tích và có độ dài tối đa là **180 ký tự**.
2.  **Tiêu chí hoàn thành:** Mọi bước hướng dẫn quy trình (dưới các tiêu đề `Process` hoặc `Quy trình`) phải có một dòng bắt đầu bằng `Tiêu chí hoàn thành:` hoặc `Completion Criterion:` chỉ rõ trạng thái hoàn thành định lượng.
3.  **Liên kết tương đối (Relative links):** Mọi dẫn chiếu sang tệp tin khác trong cùng kỹ năng hoặc workspace phải sử dụng relative link hoạt động được, không dùng link tuyệt đối (absolute link) trừ phi đó là tài liệu web ngoài.
4.  **Đăng ký Slash Command:** Khi tạo skill mới có thuộc tính `user-invocable: true`, bắt buộc phải tạo workflow wrapper mỏng tương ứng tại thư mục `.agents/workflows/` bắt đầu bằng tiền tố `ccba-` và đăng ký vào [catalog.yaml](../platform-loader/catalog.yaml).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
