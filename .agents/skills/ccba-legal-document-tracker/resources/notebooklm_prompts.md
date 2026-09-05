# NotebookLM Prompt Templates cho VBPL

Hướng dẫn sử dụng NotebookLM để đọc nhanh VBPL và soạn thảo văn bản kỹ thuật.

---

## 1. Setup Notebook

### Cách tổ chức Notebooks

| Notebook | Sources nên upload | Mục đích |
|----------|-------------------|----------|
| `QLCL Công trình` | NĐ 06/2021, NĐ 35/2023, Dự thảo NĐ QLCL 2026 | Tra cứu QLCL |
| `Luật XD 2025` | Luật XD 2025, Luật XD 2014, các NĐ hướng dẫn | Tra cứu luật |
| `Hồ sơ hoàn thành` | Phụ lục VIb NĐ 06/2021, Phụ lục dự thảo NĐ mới | Checklist hồ sơ |

### Tips upload sources:
- Upload bản PDF gốc (không scan) cho chất lượng trích xuất tốt nhất
- Nếu PDF scan → convert sang text (dùng skill `long-form-writer` hoặc LlamaParse) trước khi upload
- Đặt tên source rõ ràng: `NĐ 06/2021 - QLCL Thi công XD`

---

## 2. Prompts: Đọc nhanh VBPL

### 2.1. Trích xuất điểm chính

```
Hãy tóm tắt các điểm chính của văn bản này theo cấu trúc:
1. Phạm vi điều chỉnh và đối tượng áp dụng
2. Các quy định mới quan trọng nhất (top 5)
3. Các thay đổi so với quy định hiện hành
4. Các yêu cầu mà kỹ sư giám sát cần lưu ý đặc biệt
Mỗi điểm kèm trích dẫn điều/khoản cụ thể.
```

### 2.2. Tra cứu theo chủ đề

```
Trong các văn bản đã upload, hãy tìm TẤT CẢ các quy định liên quan đến 
[CHỦ ĐỀ: ví dụ "nghiệm thu hoàn thành công trình"]. Liệt kê theo format:
- Văn bản: [tên]
- Điều/Khoản: [số]
- Nội dung tóm tắt: [tóm tắt]
- Trích dẫn nguyên văn: [quote]
```

### 2.3. So sánh 2 văn bản

```
Hãy so sánh chi tiết giữa [VĂN BẢN CŨ] và [VĂN BẢN MỚI] về các nội dung:
1. Phạm vi điều chỉnh
2. Quy trình QLCL thi công
3. Yêu cầu về hồ sơ hoàn thành
4. Quy trình nghiệm thu
5. Bảo trì công trình

Format bảng so sánh: | Nội dung | Cũ | Mới | Thay đổi |
Đánh dấu: ✅ Không đổi | ⚠️ Thay đổi | ❌ Bỏ | 🆕 Mới
```

---

## 3. Prompts: Soạn thảo Công văn

### 3.1. Công văn góp ý dự thảo VBPL

```
Dựa trên dự thảo [TÊN VĂN BẢN], hãy soạn công văn góp ý với cấu trúc:

CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc

Kính gửi: [CƠ QUAN NHẬN]

Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng (CCBA) - Viện KHCN Xây dựng,
sau khi nghiên cứu dự thảo [TÊN], xin có một số ý kiến góp ý như sau:

1. Về [VẤN ĐỀ 1]: Tại Điều... Khoản... có quy định [trích dẫn].
   Góp ý: [nội dung góp ý dựa trên thực tiễn QLCL]

2. Về [VẤN ĐỀ 2]...

Mỗi ý kiến cần:
- Trích dẫn cụ thể điều/khoản
- Phân tích vấn đề từ góc độ thực tiễn quản lý chất lượng
- Đề xuất sửa đổi cụ thể
```

### 3.2. Công văn hướng dẫn áp dụng VBPL mới

```
Soạn công văn hướng dẫn nội bộ về việc áp dụng [TÊN VBPL] với cấu trúc:

1. Căn cứ pháp lý (liệt kê các văn bản)
2. Phạm vi áp dụng (dự án nào, từ thời điểm nào)
3. Các thay đổi chính cần lưu ý (3-5 điểm)
4. Hướng dẫn cụ thể cho:
   a. Kỹ sư giám sát
   b. Quản lý dự án
   c. Bộ phận hồ sơ
5. Thời hạn chuyển đổi
6. Đầu mối liên hệ
```

---

## 4. Prompts: Soạn Thư kỹ thuật (Technical Letter)

### 4.1. Thư yêu cầu bổ sung hồ sơ

```
Soạn thư kỹ thuật yêu cầu nhà thầu bổ sung hồ sơ, dựa trên:
- Căn cứ: [VBPL liên quan, ví dụ NĐ 06/2021 Điều X Khoản Y]
- Hồ sơ còn thiếu: [danh sách từ checklist]
- Deadline: [thời hạn]

Format formal, trích dẫn chính xác điều khoản VBPL làm căn cứ pháp lý.
```

### 4.2. Thư phản hồi kỹ thuật

```
Soạn thư phản hồi kỹ thuật về [VẤN ĐỀ], dựa trên các quy định trong 
notebook. Cần:
- Trích dẫn quy định áp dụng
- Phân tích kỹ thuật khách quan
- Kết luận và đề xuất
```

---

## 5. Prompts: Audio Overview

### 5.1. Tạo podcast tổng hợp thay đổi VBPL

```
Tạo một buổi thảo luận dạng podcast giữa 2 chuyên gia về:
- Những thay đổi QUAN TRỌNG NHẤT trong [TÊN VBPL MỚI]
- Tác động thực tế đến kỹ sư giám sát tại công trường
- Các deadline quan trọng cần nhớ
- Lời khuyên cho giai đoạn chuyển tiếp
Giọng điệu chuyên nghiệp nhưng dễ hiểu, phù hợp nghe trên đường đi công trường.
```

---

## 6. Tips nâng cao

1. **Pin câu trả lời hay** → "Save to Note" để tạo knowledge base nội bộ
2. **Tạo nhiều notebook nhỏ** thay vì 1 notebook lớn → tránh context dilution
3. **Luôn verify** → NotebookLM cung cấp citations, click vào để kiểm tra nguồn gốc
4. **Kết hợp Gemini** → Share notebook lên Gemini app để hỏi câu hỏi follow-up phức tạp hơn
5. **Cập nhật định kỳ** → Khi có VBPL mới, upload ngay vào notebook tương ứng
