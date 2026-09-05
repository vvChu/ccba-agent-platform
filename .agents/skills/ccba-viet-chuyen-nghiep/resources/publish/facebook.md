# Format Hiển Thị — Facebook

**Module:** publish/facebook
**Mục đích:** Format nội dung cho Facebook. Chỉ xử lý format, không viết nội dung.

**Mặc định:** FB cá nhân. Chỉ dùng FB page/group khi user chỉ định rõ.

---

## 1. FB Cá Nhân (MẶC ĐỊNH)

Facebook cá nhân là văn xuôi chảy liền mạch. Không có cấu trúc nhìn thấy được. Người đọc cuộn và đọc như đọc thư.

### Nguyên tắc cốt lõi

- KHÔNG có tiêu đề (bài bắt đầu thẳng bằng câu đầu tiên)
- KHÔNG có `===`, `---`, hoặc bất kỳ ký hiệu phân đoạn nào
- KHÔNG có heading, sub-heading
- KHÔNG có bullet points, numbered lists
- KHÔNG có markdown, HTML, rich formatting
- Tách đoạn chỉ bằng dòng trống

### Đoạn văn

Đoạn văn trên FB cá nhân được phép DÀI HƠN so với blog/article. Lý do: mạch logic chain trên FB cá nhân cần chảy liền mạch, ngắt đoạn sẽ phá vỡ flow lập luận.

- Đoạn dài (8-15 câu): cho logic chain, chuỗi dẫn chứng, show-don't-tell
- Đoạn trung (3-7 câu): giải thích, bối cảnh
- Đoạn ngắn (1-2 câu): chuyển tiếp, nhấn mạnh, kết luận

Không có giới hạn cứng — đoạn dài bao nhiêu tùy mạch logic. Nếu ngắt giữa chừng mà người đọc mất mạch → đoạn đó cần dài.

### Nhấn mạnh

Trên FB cá nhân không có bold/italic. Dùng:

| Kỹ thuật | Khi dùng | Ví dụ |
|----------|----------|-------|
| IN HOA cụm từ | Phản bác trực tiếp, insight then chốt | "KHÔNG CÓ NGHĨA LÀ 30% NHÂN VIÊN MẤT VIỆC" |
| Ngoặc kép "" | Thuật ngữ, trích dẫn, khái niệm đặt tên | "phán xét mượn danh" |
| Ngoặc đơn () | Giải thích nhanh, con số phụ | (gấp đôi thời lượng) |

IN HOA chiến lược: dùng cho phản bác/insight cốt lõi. Tối đa 8-12 cụm nếu bài debunk, 3-5 cụm nếu bài phân tích.

### Giọng văn

FB cá nhân dùng ngôi "mình" hoặc "tôi", KHÔNG dùng "bạn" (trừ khi hỏi tu từ). Giọng conversational, như đang kể cho bạn bè nghe.

### Tham khảo

Không có phần "Tham khảo" cuối bài. Nếu có nguồn, ghi trong comment hoặc đan xen tự nhiên trong bài ("báo cáo gốc 17 trang, viết bởi...").

### Ví dụ cấu trúc

```
[Câu mở — vào đề thẳng, không giới thiệu]

[Đoạn dài — setup bối cảnh + tóm tắt vấn đề]

[Đoạn trung — phân tích chi tiết]

[Đoạn dài — dẫn chứng + phản bác]

[Đoạn ngắn — insight/kết luận]

[Đoạn trung — liên hệ cá nhân hoặc call-to-action]
```

---

## 2. FB Page / Group

Dùng khi user chỉ định rõ đăng page hoặc group. Bài cho page/group giữ nguyên format markdown gốc:

- Giữ nguyên heading `#`, `##`
- Giữ nguyên bold `**`, italic `*`
- Giữ nguyên cấu trúc sections
- Thêm phần tham khảo cuối bài nếu có nguồn

Page/group hỗ trợ rich text nên không cần chuyển đổi format.

**Lưu ý:** Tất cả file output đều lưu đuôi `.md` (kể cả FB cá nhân). Không dùng `.txt`.

---

## Checklist — FB Cá Nhân

- [ ] Không có tiêu đề/heading
- [ ] Không có `===`, `---`, bullet, numbered list
- [ ] Không có markdown, HTML
- [ ] Tách đoạn chỉ bằng dòng trống
- [ ] Đoạn dài cho logic chain, đoạn ngắn cho insight
- [ ] IN HOA chiến lược (không tràn lan)
- [ ] Giọng "mình/tôi", conversational
- [ ] Nguồn đan xen trong bài hoặc ở comment
- [ ] Copy-paste thẳng vào Facebook được ngay

## Checklist — FB Page/Group

- [ ] Giữ nguyên markdown gốc
- [ ] Có phần tham khảo cuối bài

---

## Bài Mẫu Đã Duyệt

1. **Phản bác bài viết Anthropic** (03/2026) — FB cá nhân, dạng debunk
