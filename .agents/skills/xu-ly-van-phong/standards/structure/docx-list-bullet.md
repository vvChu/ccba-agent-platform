# Danh sách & Bullet

Quy chuẩn bullet, numbered list, indent cho văn bản Office.

---

## Bullet mặc định

Bullet trong DOCX dùng **dấu gạch ngang** `-` (hyphen) — ký tự mặc định của built-in style `List Bullet` trong Word.

```
- Triển khai nhanh, mỗi tác vụ hoàn thành trong 1 đến 2 tuần.
- Đo lường được ngay, quy ra giờ công tiết kiệm theo từng tuần.
- Dễ nhân bản, cùng một công thức áp dụng cho nhiều phòng ban.
```

Sub-bullet dùng **dấu cộng** `+`:

```
- Ranh giới tiếp giáp các khu vực:
    + Phía Bắc giáp khu công nghiệp
    + Phía Nam giáp biển
```

---

## Khi nào dùng gì

| Tình huống | Ký hiệu |
|---|---|
| Liệt kê không thứ tự | Bullet `-` |
| Liệt kê có thứ tự thực hiện | Số `1.` `2.` `3.` |
| Mục con trong cấp lớn | Chữ cái `a.` `b.` `c.` |
| Mệnh đề nhỏ inline | Ngoặc số `(1)` `(2)` `(3)` |
| Bullet nhấn mạnh | `-` kèm **bold đầu dòng** |
| Sub-bullet | `+` dấu cộng |

### Mẫu bullet nhấn mạnh:

```
- **Triển khai nhanh**, mỗi tác vụ hoàn thành trong 1 đến 2 tuần.
- **Đo lường được ngay**, quy ra giờ công tiết kiệm theo từng tuần.
```

---

## Indent chuẩn

| Cấp | Indent trái | Hanging indent |
|---|---|---|
| Bullet cấp 1 (`-`) | 0.63 cm (hoặc 1 cm cho VB dài) | 0.5 cm |
| Sub-bullet (`+`) | 1.27 cm (hoặc 2 cm) | 0.5 cm |

### Spacing:

| Yếu tố | Giá trị |
|---|---|
| Space giữa bullets | 4pt |
| Space trước bullet đầu | 6pt |
| Space sau bullet cuối | 6pt |

---

## Điều cấm

| Điều cấm | Lý do |
|---|---|
| Không gõ tay ký tự `•` (chấm đậm) vào nội dung văn bản | Có độ phụ thuộc font cao nếu gõ text thô; thay vào đó hãy dùng định dạng style List Bullet trong Word. |
| Không dùng em dash `—` làm bullet | Em dash là dấu câu, không phải ký tự danh sách |
| Không dùng `*` hay `+` làm bullet cấp 1 | Ký tự markdown, render không ổn định trong Word |
| Không trộn nhiều kiểu bullet cùng danh sách | Phá vỡ cấu trúc thị giác |
| Không dùng bullet cho dưới 3 mục | Viết thành câu: "bao gồm: x, y và z" |

---

## Lập trình: Bullet trong docx-js

Dùng `LevelFormat.BULLET` + `numbering.reference` để cấu hình ký hiệu bullet, **không gõ tay ký tự `•` vào phần nội dung văn bản thô (content text)**:

```javascript
numbering: {
  config: [{
    reference: "bullets",
    levels: [{
      level: 0,
      format: LevelFormat.BULLET,
      text: "•",
      alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 560, hanging: 280 } } },
    }],
  }],
}
```
