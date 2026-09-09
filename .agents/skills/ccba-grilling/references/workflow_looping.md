# ccba-loop-me — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Kỹ thuật phỏng vấn vòng lặp chuyên sâu nhằm khai thác tường tận yêu cầu quy trình
> **Mô tả gốc:** Grill me about specs for the workflows I want to build, within this workspace. Adapted for CCBA Information Governance.

---

# Loop-Me: Thiết kế chu trình lặp của Người dùng

Chạy một phiên `/ccba-grilling` trạng thái với kết quả đầu ra duy nhất là đặc tả **workflow** tự động hóa. Áp dụng kỷ luật phỏng vấn Socrates — hỏi từng câu hỏi một, đi kèm một phương án trả lời khuyến nghị — nhằm làm rõ mục tiêu và các thuật ngữ chu trình dưới đây.

Tạo mới, sửa đổi hoặc xóa bỏ các đặc tả workflow tùy thuộc vào kết quả thảo luận.

## Nguyên tắc quản trị thông tin CCBA (Rule 1)

Để tuân thủ hiến pháp CCBA, skill này bắt buộc phải ghi nhận thông tin theo các đường dẫn sau:

- **Ghi chú thô & Thuật ngữ**: Ghi nhận vào `.md/knowledge/user_loops.md` (thay vì `NOTES.md` ở root). Hãy phỏng vấn người dùng về các công cụ họ dùng, kênh thông tin họ xử lý và thuật ngữ đặc thù của họ. Làm sắc nét các từ khóa mơ hồ thành các từ khóa chuẩn hóa.
- **Tệp Đặc tả Kỹ năng Chu trình (Loop Skill)**: Sinh trực tiếp vào thư mục [.agents/skills/ccba-<slug>/SKILL.md](../) (chuẩn Antigravity Skill) mang định dạng tên `ccba-<slug>`.

## Metadata của Kỹ năng Chu trình CCBA
Mọi tệp `SKILL.md` chu trình được tạo ra bắt buộc phải có frontmatter YAML chuẩn sau:

```yaml
---
name: ccba-[slug]
description: [Mô tả ngắn gọn chức năng của lệnh <= 180 ký tự]
bundle: "_core"     # Hoặc tên bundle tương ứng (_qc, _consulting, _software...)
disable-model-invocation: true
triggers:
  - ccba-[slug]
---
```

## Khung tư duy thiết kế chu trình (The Loop Lens)

Một **chu trình (loop)** là một mô thức lặp đi lặp lại trong công việc hoặc đời sống của người dùng: sự nghiệp, tuần làm việc, buổi sáng, hoặc một công việc lặp lại đơn lẻ. Việc mô hình hóa cuộc sống thành các chu trình giúp phát hiện các phần việc mang tính dự đoán được — và đó chính là thứ đáng để **ủy quyền cho AI**.

## Từ vựng dùng chung (Vocabulary)

Chỉ sử dụng các thuật ngữ này khi thiết kế workflow yêu cầu:

- **Trigger (Điểm kích hoạt)** — điều gì làm chạy workflow: một **sự kiện (event)** (ví dụ: email mới, issue mới) hoặc một **lịch trình (schedule)** (ví dụ: mỗi buổi sáng).
- **Checkpoint (Điểm kiểm soát)** — điểm dừng yêu cầu con người xác nhận hoặc quyết định (Human-in-the-loop). Một số workflow chạy tự động hoàn toàn không có checkpoint.
- **Push right (Đẩy về bên phải)** — trì hoãn checkpoint xa nhất có thể. Hãy để AI làm tối đa phần việc trước khi hỏi con người, để họ chỉ cần xem xét một lần duy nhất vào lúc cuối cùng.
- **Brief (Bản tóm tắt)** — những gì checkpoint trình bày cho con người: một bản tóm tắt súc tích, đã sẵn sàng để ra quyết định — bao gồm kết quả là gì, tại sao, và link đến asset thô bên dưới. Người dùng đọc brief chứ không đọc bản nháp thô.

## Định nghĩa Hoàn thành (Definition of Done)

Một đặc tả workflow được coi là hoàn thành khi một agent triển khai khác có thể đọc nó và code lại mà không cần hỏi thêm bất kỳ câu hỏi nào. Hãy phỏng vấn dồn dập cho đến khi làm rõ mọi khía cạnh.
