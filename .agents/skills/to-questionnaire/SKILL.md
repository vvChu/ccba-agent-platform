---
name: to-questionnaire
description: Chuyển đổi một quyết định chưa có đủ thông tin thành Bảng hỏi (Questionnaire) dạng Markdown để gửi cho đối tác/chuyên gia điền bất đồng bộ.
disable-model-invocation: true
category: productivity
keywords: [questionnaire, async, interview, discovery, decision, handoff]
metadata:
  author: CCBA
  version: "1.0.0"
---

# Kỹ năng: Tạo Bảng Hỏi Bất Đồng Bộ (To Questionnaire)

Kỹ năng này giúp biến một bài toán hoặc quyết định mà người dùng không thể tự trả lời một mình thành một **Bảng hỏi (Questionnaire)** dạng Markdown. Tệp này có thể gửi cho người khác điền bất đồng bộ (async) hoặc dùng làm tài liệu thảo luận trong cuộc họp.

Nguyên tắc cốt lõi: **"Grill the send, not the subject"** — Chỉ phỏng vấn người dùng về *đối tượng gửi và thông tin cần thu về* (những gì người dùng luôn biết), từ đó đặt ra các câu hỏi nhằm khỏa lấp khoảng trống thông tin (*gap*) giữa người nhận và nhu cầu của người dùng.

---

## Quy trình Thực hiện (3 Bước)

### 1. Người nhận là ai? (Who is it going to?)
Trong một lượt trao đổi duy nhất, hãy làm rõ:
- Vai trò, chuyên môn của người nhận (recipient's role & expertise).
- Mối quan hệ giữa người nhận và người dùng.
- *Mục đích:* Xác định văn phong, giọng điệu và lượng ngữ cảnh (context) cần đưa vào bảng hỏi.

### 2. Cần thu về những gì? (What do you need back?)
Trong một lượt trao đổi duy nhất, xác định:
- Danh sách các quyết định hoặc sự thật cụ thể mà người dùng chưa thể tự chốt và cần người nhận giải đáp.
- *Mục đích:* Lập danh sách kết quả đầu ra cụ thể mà người dùng cần nhận được sau khi thu thập xong bảng hỏi.

### 3. Soạn thảo Bảng hỏi (Write the questionnaire)
Dựa trên khoảng trống thông tin từ Bước 1 và 2, soạn thảo tệp bảng hỏi theo cấu trúc chuẩn dưới đây:
- Ghi tệp ra đường dẫn: `to-questionnaire-<slug>.md` (slug lấy từ chủ đề) tại thư mục hiện tại hoặc `.md/knowledge/` tùy ngữ cảnh.
- Đảm bảo mọi điểm cần thu về ở Bước 2 đều được bao phủ bởi ít nhất một câu hỏi cụ thể.

---

## Cấu trúc Tài liệu (Document Structure)

Đặt câu hỏi theo thứ tự **quan trọng nhất lên trước** (vì làm việc bất đồng bộ có thể chỉ có 1 lượt phản hồi). Nhóm các câu hỏi theo từng chủ đề `##` nếu có nhiều hơn 4-5 câu hỏi.

```markdown
# <Tiêu đề Bảng hỏi>

**Mục đích:** Lý do bảng hỏi này tồn tại và quyết định phụ thuộc vào nó.
**Người gửi:** <Người dùng> — **Người nhận:** <Đối tác/Chuyên gia> — **Mục đích sử dụng phản hồi:** <Nơi phản hồi sẽ được xử lý>

## Ngữ cảnh (Context)
Một đoạn văn ngắn định hướng cho người nhận (người chưa nằm trong luồng suy nghĩ của người dùng). Đủ để trả lời tốt, không viết quá dài.

## Hướng dẫn Trả lời (How to answer)
Thời hạn và mức độ nỗ lực ước tính. Phản hồi một phần hoặc "Tôi chưa rõ" vẫn rất có giá trị — hãy đánh dấu bất kỳ điểm nào chưa chắc chắn thay vì bỏ qua.

## <Chủ đề 1>
Mỗi chủ đề là một mục `##`. Bên dưới là các câu hỏi, ưu tiên câu hỏi quan trọng nhất lên đầu. Mỗi câu hỏi chỉ chứa MỘT ý duy nhất — không dùng câu hỏi kép — kèm khung nhập phản hồi bên dưới:

### <Nội dung câu hỏi cụ thể?>
*Tại sao điều này quan trọng: giải thích ngắn gọn tại sao câu hỏi này quyết định đến giải pháp.*

> [Nhập câu trả lời tại đây]

## Ý kiến khác (Anything else?)
Câu hỏi mở cuối cùng: Còn điều gì chúng tôi chưa hỏi mà ông/bà nghĩ chúng tôi cần biết không?
```

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
