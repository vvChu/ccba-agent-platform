# Hướng dẫn Tra chéo 3 Chiều

> **Mục đích:** Hướng dẫn chi tiết cách trace keyword qua các tầng VBQPPL, phát hiện VB sửa đổi/thay thế, và xác định đúng phiên bản tại mốc thời gian. Đây là kỹ năng cốt lõi phân biệt tra cứu nghiệp dư với tra cứu chuyên nghiệp.

---

## Chiều 1: Tra XUỐNG (Vertical Down)

**Mục đích:** Từ Luật (nguyên tắc chung) → tìm NĐ (quy định chi tiết) → TT (hướng dẫn cụ thể). Vì Luật chỉ quy định khung, chi tiết thực thi nằm ở NĐ và TT.

### Cách tra

1. Đọc nội dung Luật → tìm cụm "Chính phủ quy định chi tiết" hoặc "Bộ trưởng hướng dẫn thi hành".
2. Search NĐ tương ứng:
   ```
   search_web: site:thuvienphapluat.vn "quy định chi tiết" "[tên luật]" nghị định
   ```
3. Trong NĐ → tìm cụm "Bộ trưởng Bộ [X] hướng dẫn" → search TT:
   ```
   search_web: site:thuvienphapluat.vn "hướng dẫn" "[số hiệu NĐ]" thông tư
   ```

### Pattern nhận diện trên thuvienphapluat.vn

- Mục **"Văn bản được hướng dẫn"** trong trang chi tiết VB → liệt kê Luật/NĐ mà VB này hướng dẫn
- Phần mở đầu NĐ luôn có dòng: "Căn cứ Luật số xx/yyyy/QHzz ngày..." → xác nhận đúng Luật gốc

### Ví dụ

```
Luật Đất đai 2024 (31/2024/QH15)
  → NĐ 102/2024/NĐ-CP (quy định chi tiết)
    → NĐ 71/2024 (khung giá đất)
    → NĐ 88/2024 (bồi thường, TĐC)
    → NĐ 101/2024 (đăng ký, GCN)
      → Các TT hướng dẫn (tra theo từng NĐ)
```

---

## Chiều 2: Tra NGANG (Horizontal — Sửa đổi/Thay thế/Bãi bỏ)

**Mục đích:** Xác định VB gốc còn nguyên vẹn hay đã bị sửa đổi. Áp dụng VB đã bị sửa đổi mà không biết = tư vấn sai — đây là lỗi nghiêm trọng nhất.

### Cách tra

1. Search VB sửa đổi:
   ```
   search_web: site:thuvienphapluat.vn "sửa đổi" "[số hiệu VB gốc]"
   search_web: site:thuvienphapluat.vn "thay thế" "[số hiệu VB gốc]"
   ```
2. Trên thuvienphapluat.vn → kiểm tra 3 mục:
   - **"Văn bản sửa đổi"**: Liệt kê VB nào đã sửa VB này
   - **"Văn bản bị thay thế"**: VB cũ mà VB này thay thế
   - **"Tình trạng hiệu lực"**: Banner đầu trang — "Còn hiệu lực" / "Hết hiệu lực" / "Hết hiệu lực một phần"

### Cách đọc VB sửa đổi

VB sửa đổi thường có cấu trúc:
```
"Điều X. Sửa đổi, bổ sung một số điều của [VB gốc]:
  1. Sửa đổi khoản Y Điều Z như sau: [nội dung mới]
  2. Bổ sung điểm A vào sau điểm B khoản C Điều D"
```

Khi đọc, cần ghép: VB gốc (phần chưa sửa) + VB sửa đổi (phần đã sửa) = bản hợp nhất thực tế.

### Pattern nhận diện VB "sửa đổi nhiều luật cùng lúc"

VN có xu hướng ban hành Luật sửa nhiều luật (VD: Luật 90/2025/QH15 sửa 8 luật). Khi gặp loại VB này:
- Đọc mục lục → xác định Luật nào bị sửa
- Chỉ trích dẫn điều/khoản liên quan đến vấn đề đang tra, không đọc hết

### Ví dụ

```
Luật Đầu tư 61/2020/QH14 (gốc)
  ← sửa đổi bởi: Luật 57/2024/QH15 (sửa 1 số điều)
  ← sửa đổi bởi: Luật 90/2025/QH15 (sửa nhiều luật cùng lúc)
  → Phải đọc 3 VB để ghép thành bản đang hiệu lực
```

---

## Chiều 3: Tra THỜI GIAN (Temporal)

**Mục đích:** Xác định phiên bản VB nào áp dụng tại mốc thời điểm của user. Vì cùng 1 vấn đề, tháng 7/2024 và tháng 8/2024 có thể áp dụng Luật hoàn toàn khác.

### Quy tắc áp dụng

| Mốc user | So với ngày hiệu lực VB mới | Áp dụng |
|---|---|---|
| Trước ngày hiệu lực VB mới | Mốc < ngày HL | VB cũ (trừ khi có chuyển tiếp) |
| Sau ngày hiệu lực VB mới | Mốc ≥ ngày HL | VB mới |
| Đúng giai đoạn chuyển tiếp | Trong khoảng chuyển tiếp | Theo điều khoản chuyển tiếp |

### Cách kiểm tra

1. Xác định mốc thời điểm user (hỏi nếu chưa rõ).
2. Kiểm tra ngày hiệu lực VB trên thuvienphapluat.vn → mục "Ngày có hiệu lực".
3. Nếu VB mới có hiệu lực SAU mốc user → vẫn áp dụng VB cũ.
4. Kiểm tra điều khoản chuyển tiếp (thường ở cuối VB mới).

### Điều khoản chuyển tiếp — Những gì cần tìm

VB mới thường có 1 điều cuối cùng quy định:
- "Dự án đã được phê duyệt trước ngày Luật này có hiệu lực → tiếp tục thực hiện theo quy định tại thời điểm phê duyệt"
- "Hợp đồng đã ký trước ngày Luật này có hiệu lực → thực hiện theo hợp đồng đã ký"
- "Trong thời hạn X tháng kể từ ngày Luật này có hiệu lực, [chủ thể] phải [hành động]"

### Ví dụ

```
Vấn đề: Tranh chấp đất đai xảy ra tháng 5/2024
  → Luật Đất đai 2024 có hiệu lực 01/08/2024
  → Mốc user (05/2024) < 01/08/2024
  → Áp dụng Luật Đất đai 2013 (VB cũ)
  → NHƯNG kiểm tra: có điều khoản chuyển tiếp trong Luật 2024 không?
```

---

## Checklist Tra chéo

Hoàn thành cho mỗi keyword/VB trước khi đưa vào SOT:

- [ ] Tìm được VB gốc (Luật/Bộ luật)?
- [ ] Tra XUỐNG: NĐ chi tiết? TT hướng dẫn?
- [ ] Tra NGANG: VB sửa đổi? Thay thế? Bãi bỏ?
- [ ] Tra THỜI GIAN: Phiên bản đúng mốc user?
- [ ] Điều khoản chuyển tiếp (nếu có)?
- [ ] Trích dẫn nguyên văn + tọa độ đầy đủ?
