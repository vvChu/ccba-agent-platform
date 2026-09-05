# Dấu Câu — Punctuation

**Module:** check/punctuation
**Mục đích:** Quy tắc dấu câu, spacing — những lỗi kỹ thuật AI thường mắc khi viết tiếng Việt.

---

## 1. Dấu câu — Khác hoàn toàn tiếng Anh

**Dấu câu [. , ! ? : ; ...] LUÔN:**
- ✅ Sát với từ phía trước (không có khoảng cách)
- ✅ Cách với từ phía sau (có khoảng cách)

```
✅ "Xin chào, tôi là An."
❌ "Xin chào , tôi là An ."
```

### Ngoặc đơn ()

- ✅ Trước ngoặc mở: có khoảng cách
- ✅ Sau ngoặc đóng: có khoảng cách (trừ cuối câu)
- ✅ Bên trong ngoặc: sát với nội dung

```
✅ "Ông ta nói (rất to) rằng..."
❌ "Ông ta nói(rất to)rằng..."
```

### Gạch ngang (-)

- ✅ Cả hai bên đều có khoảng cách

```
✅ "Hà Nội - Huế - TP. HCM"
❌ "Hà Nội-Huế-TP. HCM"
```

**Ngoại lệ — compound noun:** `người-mà-ai-cũng-biết`

### Dấu hai chấm (:)

Tiếng Việt **hạn chế** dùng dấu hai chấm. Chỉ phù hợp khi:
- Giờ (14:30)
- Trích dẫn trực tiếp (Ông ấy nói: "...")
- Liệt kê sau "bao gồm", "gồm có"

Các trường hợp khác: ưu tiên dấu chấm hoặc viết lại câu bằng từ nối tự nhiên.

| Cứng nhắc (dùng `:`) | Tự nhiên (dùng từ nối) |
|-----------|----------|
| `không thể nhượng bộ: không dùng AI...` | `không thể nhượng bộ là không dùng AI...` |
| `nói thẳng: "Nhiều bài toán..."` | `nói thẳng rằng "nhiều bài toán..."` |

**Từ nối thay thế dấu hai chấm:**
- Sau động từ tuyên bố/quy định: dùng `là`, `rằng`, `như sau`
- Sau mệnh đề chỉ điều kiện/kết quả: dùng `thì`, `mà`, `nên`

### Oxford comma `, và`

**Cấm.** Trong tiếng Việt, "và" đã đóng vai trò nối, không thêm dấu phẩy trước.

| Sai (kiểu Anh) | Đúng |
|------|------|
| `nhanh hơn, sạch hơn, và đúng hơn` | `nhanh hơn, sạch hơn và đúng hơn` |

### Dấu phẩy giữa các tính từ bổ nghĩa liên tiếp

Khi nhiều tính từ cùng bổ nghĩa cho **một thực thể duy nhất**, không dùng dấu phẩy giữa chúng.

```
❌ "Sự thật hiển nhiên, không thể phủ nhận."
✅ "Sự thật hiển nhiên không thể phủ nhận."
```

### `Mà` đứng đầu câu

Hợp lệ khi nhấn mạnh sự tương phản hoặc mở rộng thông tin bất ngờ.

```
✅ "Họ nói muốn hòa bình. Mà đây là lần thứ ba họ phá vỡ thỏa thuận."
```

### Em-dash `—`

**Cấm.** Em dash `—` không tồn tại trong văn viết tiếng Việt chuẩn. Luôn thay thế bằng phương án phù hợp theo chức năng:

| Chức năng | Thay thế chuẩn | Ví dụ |
|---|---|---|
| Ngắt câu, nhấn mạnh ý tiếp theo | Gạch ngang ` - ` (cách hai bên) | "Anh ta đến muộn - muộn đến ba tiếng." |
| Giải thích / định nghĩa | "tức là", "nghĩa là", "đó là" | "Chỉ một thứ quan trọng - đó là lòng trung thành." |
| Liệt kê sau mệnh đề | Dấu hai chấm có từ dẫn nhập | "Anh ấy có tất cả, gồm: tiền, quyền, danh vọng." |
| Thông tin chêm xen giữa câu | Dấu ngoặc đơn `( )` | "Kế hoạch (nếu có thể gọi như vậy) đã thất bại." |
| Tương phản / đảo chiều | "nhưng", "thế mà", "vậy mà" | "Cô ấy cố gắng - thế mà kết quả bằng không." |
| Kết luận bất ngờ cuối câu | Tách thành câu mới, dùng `. Và` | "Anh ta nỗ lực suốt một năm. Và rồi mọi thứ sụp đổ." |
| Lời thoại bị cắt ngang | Dấu chấm lửng `...` | "Tôi chỉ muốn nói rằng..." |
| Phân cách mục / địa danh | Gạch ngang ` - ` (cách hai bên) | "Hà Nội - Huế - TP. HCM" |

**Lưu ý kỹ thuật:**
- Gạch ngang thay em dash **phải có khoảng cách hai bên**: `từ - từ`, không phải `từ-từ`
- `từ-từ` (không cách) chỉ dùng cho compound noun: `người-mà-ai-cũng-biết`
- Dấu hai chấm chỉ dùng được khi **có từ dẫn nhập** trước: `gồm:`, `như:`, `sau đây:`
- Nếu không chắc → **ưu tiên tách thành câu riêng** (an toàn nhất)
- **Đa số trường hợp** em dash trong văn xuôi tiếng Việt thuộc loại "ngắt câu, nhấn mạnh" → thay bằng ` - `

---

## Grep Patterns

| Pattern | Search | Quy tắc |
|---------|--------|---------|
| Em-dash | `—` | Cấm. Thay ` - ` (cách hai bên) |
| Oxford comma | `, và ` | Cấm. Bỏ dấu phẩy trước "và" |
| Colon sau mệnh đề | `: ` | Kiểm tra — thay từ nối nếu không phải trích dẫn/liệt kê |
| Space trước dấu câu | ` ,` / ` .` / ` !` / ` ?` | Cấm. Dấu câu sát từ trước |

---

## Checklist hoàn thành

- [ ] Dấu câu: sát trước, cách sau
- [ ] Ngoặc đơn: cách trước, cách sau, sát nội dung bên trong
- [ ] Gạch ngang: cách cả hai bên
- [ ] Không có em-dash `—`
- [ ] Không có Oxford comma `, và`
- [ ] Dấu hai chấm: hạn chế — thay bằng từ nối
- [ ] Tính từ bổ nghĩa liên tiếp: không dùng dấu phẩy
