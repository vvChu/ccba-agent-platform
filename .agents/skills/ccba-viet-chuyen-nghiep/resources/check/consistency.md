# Nhất Quán — Consistency

**Module:** check/consistency
**Mục đích:** Đảm bảo nội dung tạo ra nhất quán và không xung đột khi nhiều modules được load cùng lúc.

---

## Quy Tắc Ưu Tiên

Khi 2 module cùng nói về 1 chủ đề ở mức chi tiết khác nhau:

```
quality/  = NỀN TẢNG (baseline) — luôn đúng, áp dụng mọi nơi
    ↓
style/   = CỤ THỂ HÓA (override) — thắng khi cùng chủ đề với quality/
    ↓
platform/ = FORMAT-ONLY — chỉ trình bày, không can thiệp nội dung/style
```

**Ví dụ:**
- `natural.md` nói "đoạn văn 1-6 câu" (baseline)
- `emotional.md` nói "70-20-10" (cụ thể hóa cho storytelling)
- → Khi load cả hai: dùng 70-20-10. Không mâu thuẫn — emotional CỤ THỂ HÓA quy tắc chung.

---

## 4 Tiêu Chí Kiểm Tra

### 1. Mâu thuẫn quy tắc (Rule Conflict)

Module A nói "làm X", Module B nói "không làm X".

**Cách phát hiện:** Với mỗi quy tắc "NÊN/KHÔNG NÊN" trong bài viết, kiểm tra xem có module nào đang load nói ngược lại không.

**Xử lý:** Áp dụng quy tắc ưu tiên ở trên. Nếu xung đột nằm trong cùng tầng (2 module style cùng nói khác nhau) → báo cáo user.

### 2. Mức độ ưu tiên không rõ (Priority Ambiguity)

Hai module cùng nói về 1 chủ đề, Agent không biết nghe ai.

**Cách phát hiện:** Sau khi viết xong, đọc lại và hỏi: "Quy tắc này đến từ module nào? Có module khác đang load nói khác không?"

**Xử lý:** Module style/ cụ thể hóa quality/. Nếu vẫn không rõ → mặc định theo quality/ (an toàn hơn).

### 3. Khoảng trống logic (Coverage Gap)

Tình huống thực tế mà không module nào cover.

**Cách phát hiện:** Request không khớp bất kỳ điều kiện kích hoạt nào trong registry.

**Xử lý:** Dùng V1 (emotional) làm fallback mặc định. Ghi nhận gap vào `meta/upgrade.md` để bổ sung module sau.

### 4. Tham chiếu hỏng (Reference Integrity)

Module trỏ đến file/nội dung không còn tồn tại.

**Cách phát hiện:** Kiểm tra mọi cross-reference (tên file `.md`) trong các module đang load → file đó có trong registry không?

**Xử lý:** Sửa reference hoặc báo cáo lỗi.

---

## Checklist (chạy sau khi viết xong)

- [ ] Bài viết không vi phạm quy tắc nào trong Q1 (punctuation)?
- [ ] Bài viết không vi phạm quy tắc nào trong Q2 (natural)?
- [ ] Nếu dùng cả quality/ + style/: style/ CỤ THỂ HÓA chứ không MÂU THUẪN quality/?
- [ ] Tone nhất quán từ đầu đến cuối (không nhảy giữa casual và formal)?
- [ ] Thuật ngữ nhất quán (không dùng 2 từ khác nhau cho cùng 1 khái niệm)?
- [ ] Nếu phát hiện gap → đã ghi vào `meta/upgrade.md`?
