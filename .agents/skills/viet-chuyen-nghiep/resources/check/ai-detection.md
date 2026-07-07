# Phát Hiện Dấu Vết AI — AI Detection

**Module:** check/ai-detection
**Mục đích:** Phát hiện và loại bỏ patterns đặc trưng của nội dung do AI tạo ra.

---

## 1. Over-formatting

```
❌ **Điểm 1**: Bla bla / **Điểm 2**: Bla bla / **Kết luận**: ...
✅ Điểm thứ nhất là... Tiếp theo, chúng ta thấy... Cuối cùng...
```

## 2. Nhãn kiểu AI

```
❌ "Key insights:", "Note:", "Summary:"
✅ "Điểm nổi bật:", "Lưu ý:", "Tóm lại:"
```

## 3. Dấu hiệu AI nâng cao

| Pattern | Mô tả | Cách phát hiện |
|---------|--------|----------------|
| **Paragraph uniformity** | Đoạn văn đều đặn 80-120 từ | Đếm số câu/đoạn — nếu quá đều → sai |
| **Transition overuse** | Lạm dụng "Tuy nhiên", "Bên cạnh đó" | >3 lần/bài cùng 1 từ nối → sai |
| **Cautious hedging** | Quá nhiều "có thể", "thường" | Nếu mọi claim đều hedge → thiếu cam kết |
| **Balanced structure** | Mỗi point phát triển đều đặn | Real writing: có ý nói nhiều, ý lướt qua |
| **Professional smoothness** | Quá mượt mà, thiếu gồ ghề | Real writing: có chỗ rough, quirky |
| **Artificial chaos** | Cố viết "tự nhiên" nhưng random có kiểm soát | Grammar vẫn hoàn hảo dù văn "rối" |

---

## Grep Patterns

| Pattern | Search | Quy tắc |
|---------|--------|---------|
| Transition overuse | `Tuy nhiên,` | >3 lần/bài → nghi AI |
| Transition overuse | `Bên cạnh đó,` | >3 lần/bài → nghi AI |
| Transition overuse | `Ngoài ra,` | >3 lần/bài → nghi AI |
| Transition overuse | `Hơn nữa,` | >3 lần/bài → nghi AI |
| AI labels | `Key ` / `Note:` / `Summary:` | Cấm — dùng tiếng Việt |
| Over-formatting | `**` trong content storytelling | Nghi over-formatting |
| Exclamation spam | `!` | >2 lần liên tiếp → nghi AI |
| Emoji | `🚀` / `✨` / `💡` (ngoài formula box) | Nghi AI-generated |

## Checklist

- [ ] Không có nhãn AI (Key, Note, Summary)
- [ ] Không over-formatting (bold labels trong storytelling)
- [ ] Đoạn văn biến thiên (không đều nhau)
- [ ] Từ nối đa dạng (không lặp >3 lần)
- [ ] Không quá mượt mà — có chỗ rough tự nhiên
