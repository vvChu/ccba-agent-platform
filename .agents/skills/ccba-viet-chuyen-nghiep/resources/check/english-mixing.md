# Trộn Tiếng Anh — English Mixing

**Module:** check/english-mixing
**Mục đích:** Kiểm tra việc trộn tiếng Anh không cần thiết và chuẩn thuật ngữ Việt-Anh.

---

## 1. Cấm trộn tiếng Anh trong câu

```
❌ "Performance của team đạt target trong quarter này"
✅ "Hiệu suất của đội ngũ đạt mục tiêu trong quý này"
```

**Ngoại lệ:** Thuật ngữ phổ biến giữ nguyên: CEO, AI, KPI, ROI, marketing, branding, startup, freelancer

---

## 2. Chuẩn thuật ngữ Việt-Anh

| Tình huống | Format | Ví dụ |
|-----------|--------|-------|
| Giới thiệu lần đầu | Tiếng Việt (*English*) | Kiến thức (*Knowledge*) |
| Các lần sau | Tiếng Việt hoặc acronym | Kiến thức, hoặc KB |
| Ngoại lệ phổ biến | Giữ nguyên | AI, CEO, KPI, ROI |

**KHÔNG BAO GIỜ:** English trước, Việt sau. Cấm "Knowledge (Kiến thức)".
**NHẤT QUÁN:** Đã chọn từ Việt nào → dùng xuyên suốt, không đổi.

---

## Grep Patterns

| Pattern | Search | Quy tắc |
|---------|--------|---------|
| English in sentence | `\b(performance|target|quarter|deliver|team|improve|reduce|adapt|training|insight|subscribe|embrace)\b` | Cấm trộn, dịch sang Việt |
| English-first term | Pattern: `English (Tiếng Việt)` | Cấm. Phải Việt trước |

## Checklist

- [ ] Không trộn tiếng Anh không cần thiết
- [ ] Thuật ngữ lần đầu: Việt (*English*)
- [ ] Thuật ngữ các lần sau: nhất quán dùng Việt
