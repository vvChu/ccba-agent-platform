# Chuẩn Trích dẫn Máy móc & Template SOT

> **Mục đích:** Format trích dẫn nguyên văn VBQPPL và template bảng Source of Truth (SOT). Trích dẫn chính xác là nền tảng — thiếu tọa độ hoặc sai nguyên văn thì toàn bộ tư vấn mất giá trị.

---

## 1. Format Trích dẫn Đơn lẻ

Mỗi trích dẫn từ VBQPPL phải có đủ 4 thành phần:

### Tọa độ pháp lý

```
[Cấp VB] [Số hiệu] – Điều X, Khoản Y, Điểm Z
```

Ví dụ:
- `Luật 45/2019/QH14 – Điều 36, Khoản 1, Điểm a`
- `NĐ 145/2020/NĐ-CP – Điều 12, Khoản 3`
- `TT 10/2021/TT-BXD – Điều 5`

Quy ước viết tắt cấp VB:
| Viết đầy đủ | Viết tắt |
|---|---|
| Bộ luật | BL |
| Luật | Luật |
| Nghị định | NĐ |
| Thông tư | TT |
| Quyết định | QĐ |
| Nghị quyết | NQ |

### Nguyên văn (Verbatim)

Copy chính xác từ nguồn. Giữ nguyên:
- Dấu câu gốc (dấu chấm, phẩy, hai chấm)
- Chữ hoa/thường
- Số thứ tự (a, b, c hoặc 1, 2, 3)

Nếu đoạn dài, trích phần liên quan trực tiếp. Dùng `[...]` để đánh dấu phần bỏ qua.

Ví dụ đúng:
```
"Người sử dụng lao động phải báo trước cho người lao động biết trước ít nhất 
45 ngày đối với hợp đồng lao động không xác định thời hạn [...]"
```

### Trạng thái hiệu lực

| Trạng thái | Ý nghĩa | Khi nào dùng |
|---|---|---|
| `đang hiệu lực` | VB/điều khoản còn nguyên vẹn, chưa bị sửa | VB gốc chưa sửa |
| `đã sửa đổi bởi [VB]` | Nội dung đã thay đổi, cần đọc bản sửa | VB gốc bị sửa 1 phần |
| `hết hiệu lực` | Toàn bộ VB/điều khoản không còn áp dụng | VB bị thay thế/bãi bỏ |
| `chuyển tiếp` | Áp dụng theo điều khoản chuyển tiếp | Giai đoạn chuyển giao |

### Ngày hiệu lực

Format: DD/MM/YYYY. Ghi ngày VB bắt đầu có hiệu lực, không phải ngày ban hành.

---

## 2. Template Bảng SOT

SOT là bảng tổng hợp TẤT CẢ trích dẫn đã thu thập, sắp theo thứ bậc VB.

### Format Markdown

```markdown
## Source of Truth (SOT)

**Vấn đề:** [Mô tả vấn đề pháp lý]
**Mốc thời điểm:** [DD/MM/YYYY]
**Lĩnh vực:** [Tên lĩnh vực]

| # | Tọa độ pháp lý | Trích dẫn nguyên văn | Trạng thái | Hiệu lực | Vai trò |
|---|---|---|---|---|---|
| 1 | [Cấp] [Số hiệu] – Đ.X, K.Y | "[copy nguyên văn]" | [trạng thái] | [DD/MM/YYYY] | [vai trò trong vấn đề] |
| 2 | ... | ... | ... | ... | ... |

### Xung đột (nếu có)
⚠️ Trích dẫn #X và #Y mâu thuẫn về [nội dung]. 
Áp dụng [lex superior/posterior/specialis] → ưu tiên #[X/Y].
Lý do: [giải thích].
```

### Cột "Vai trò"

Ghi ngắn gọn trích dẫn này đóng vai trò gì trong vấn đề đang phân tích:
- "Quy định điều kiện [X]"
- "Xác định thẩm quyền [cơ quan]"
- "Quy định thời hạn [Y ngày]"
- "Chế tài nếu vi phạm"
- "Sửa đổi điều kiện tại #[trích dẫn gốc]"

---

## 3. Ví dụ SOT Hoàn chỉnh

**Vấn đề:** Công ty sa thải NLĐ vì lý do "tái cơ cấu" — không báo trước 45 ngày.
**Mốc thời điểm:** 15/03/2025
**Lĩnh vực:** Lao động

| # | Tọa độ pháp lý | Trích dẫn nguyên văn | Trạng thái | Hiệu lực | Vai trò |
|---|---|---|---|---|---|
| 1 | BLLĐ 45/2019/QH14 – Đ.36, K.1 | "Người sử dụng lao động có quyền đơn phương chấm dứt hợp đồng lao động trong trường hợp sau đây: a) Người lao động thường xuyên không hoàn thành công việc theo hợp đồng lao động [...]" | đang hiệu lực | 01/01/2021 | Liệt kê căn cứ NSDLĐ đơn phương chấm dứt HĐLĐ |
| 2 | BLLĐ 45/2019/QH14 – Đ.36, K.1, Đ.c | "Người sử dụng lao động [...] do thay đổi cơ cấu, công nghệ hoặc vì lý do kinh tế theo quy định tại Điều 42 [...]" | đang hiệu lực | 01/01/2021 | Căn cứ "tái cơ cấu" phải theo Điều 42 |
| 3 | BLLĐ 45/2019/QH14 – Đ.42, K.1 | "Trường hợp thay đổi cơ cấu, công nghệ mà ảnh hưởng đến việc làm của nhiều người lao động thì người sử dụng lao động phải xây dựng và thực hiện phương án sử dụng lao động [...]" | đang hiệu lực | 01/01/2021 | Yêu cầu phải có phương án sử dụng LĐ |
| 4 | BLLĐ 45/2019/QH14 – Đ.36, K.2 | "Khi đơn phương chấm dứt hợp đồng lao động, người sử dụng lao động phải báo trước cho người lao động: a) Ít nhất 45 ngày đối với hợp đồng lao động không xác định thời hạn [...]" | đang hiệu lực | 01/01/2021 | Nghĩa vụ báo trước 45 ngày |
| 5 | BLLĐ 45/2019/QH14 – Đ.41, K.1 | "Khi đơn phương chấm dứt hợp đồng lao động trái pháp luật thì người sử dụng lao động [...] phải trả tiền lương, đóng bảo hiểm xã hội, bảo hiểm y tế, bảo hiểm thất nghiệp trong những ngày người lao động không được làm việc [...]" | đang hiệu lực | 01/01/2021 | Hệ quả sa thải trái luật |

### Xung đột
Không có xung đột trong SOT này.

### Kết luận từ SOT
- NSDLĐ có quyền đơn phương do "tái cơ cấu" (Đ.36 K.1 Đ.c) NHƯNG phải theo Đ.42 (phương án sử dụng LĐ) VÀ Đ.36 K.2 (báo trước 45 ngày).
- Nếu không báo trước 45 ngày → đơn phương trái pháp luật → Đ.41 (bồi thường).

---

## 4. Lỗi Trích dẫn Phổ biến (Tránh)

| Lỗi | Tại sao sai | Cách đúng |
|---|---|---|
| Tóm tắt thay vì copy nguyên văn | Mất chi tiết quan trọng, có thể diễn giải sai | Copy verbatim, dùng `[...]` nếu dài |
| Thiếu Khoản/Điểm | 1 Điều có nhiều Khoản quy định khác nhau | Ghi đủ Điều-Khoản-Điểm |
| Không ghi trạng thái | Có thể trích VB đã sửa đổi | Luôn kiểm tra + ghi trạng thái |
| Trích VB hết hiệu lực | Tư vấn dựa trên luật cũ = sai | Kiểm tra "Tình trạng hiệu lực" trước |
| Nhầm ngày ban hành ↔ ngày hiệu lực | Nhiều VB ban hành trước nhưng có hiệu lực sau | Ghi ngày hiệu lực, không phải ngày ban hành |
