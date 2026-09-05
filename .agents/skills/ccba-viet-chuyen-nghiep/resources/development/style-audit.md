# Phân Tích Phong Cách Viết

**Module:** M2 — Meta  
**Loại:** ⚪ Tùy chọn  
**Mục đích:** Phương pháp phân tích có hệ thống một bài viết (output hoặc bài mẫu bên ngoài) để rút ra kỹ thuật, pattern, style DNA.  
**Được gọi bởi:** `meta/upgrade.md` hoặc trực tiếp khi user đưa bài mẫu.

---

## Khi Nào Gọi

- Sau khi viết xong bài phức tạp → phân tích để rút kinh nghiệm
- User đưa bài mẫu: "Phân tích bài này", "Viết theo style của bài này"
- Cần rút style DNA trước khi mô phỏng phong cách

---

## Quy Trình Phân Tích — 4 Bước

### Bước 1: Đánh giá sơ bộ (Staged Assessment)

Đánh giá từng tầng trước khi quyết định phân tích sâu đến đâu:

```
Level 1: Có phong cách đặc biệt không?
├── Có  → Tiến sang Level 2
└── Không → Văn bản chuẩn, chỉ ghi nhận cấu trúc cơ bản

Level 2: Có kỹ thuật nghệ thuật không?
├── Có  → Xác định loại kỹ thuật cụ thể
├── Một phần → Xác định mức độ và phạm vi
└── Không → Chỉ phân tích cấu trúc và ngôn ngữ

Level 3: Có tầng nghĩa ẩn không?
├── Có  → Phân tích từng tầng với evidence
├── Nghi ngờ → Đưa evidence và khả năng
└── Không → Tập trung vào nghĩa trực tiếp

Level 4: Mức độ phức tạp nghệ thuật?
├── Cao → Phân tích chuyên sâu
├── Trung bình → Phân tích cơ bản
└── Thấp → Chỉ ghi nhận điểm nổi bật
```

**Nguyên tắc:** Không ép phân tích sâu khi văn bản đơn giản. Mức phân tích tỷ lệ với độ phức tạp thực tế.

---

### Bước 2: Phân tích cấu trúc (Evidence-Based)

**Cây cấu trúc** — chỉ phân tích những gì có thật trong văn bản:

```
├── [Phần] : [Chức năng] — "[Trích dẫn cụ thể]"
├── [Phần] : [Chức năng] — "[Trích dẫn]"
└── [Phần] : [Chức năng] — "[Trích dẫn]"
```

**Phân tích chi tiết:**
- **Kỹ thuật mở đầu:** Trích dẫn câu đầu, xác định loại hook
- **Cách chuyển tiếp:** Liệt kê từ nối, cụm liên kết thực tế
- **Nhịp đoạn văn:** Đếm số câu/đoạn, xác định pattern biến thiên
- **Phương thức kết thúc:** Trích dẫn câu cuối, xác định loại closing

---

### Bước 3: Phân tích nội dung cốt lõi (Chỉ khi có evidence)

```
NGHĨA TRỰC TIẾP: "[Trích dẫn]" → Giải thích

NGHĨA HÀM Ý (nếu có):
"[Trích dẫn]" → Hàm ý gì? Dựa trên ngữ cảnh nào?

KỸ THUẬT ĐÃ DÙNG (nếu có):
├── [Tên kỹ thuật]: "[Trích dẫn]" → Tác dụng gì?
├── [Tên kỹ thuật]: "[Trích dẫn]" → Tác dụng gì?
└── Đã có trong module nào của skill chưa?
```

**Cấm:** Over-interpretation — không đọc quá sâu vào văn bản đơn giản.

---

### Bước 4: Rút Style DNA

```
ĐẶC ĐIỂM CỐT LÕI:
├── Đặc điểm 1: [Tên]
│   Evidence: "[Trích dẫn]"
│   Cách áp dụng: [Hướng dẫn cụ thể]
│
├── Đặc điểm 2: [Tên]
│   Evidence: "[Trích dẫn]"
│   Cách áp dụng: [Hướng dẫn cụ thể]
│
└── Chỉ liệt kê đặc điểm CÓ EVIDENCE thật sự
```

**Output cho upgrade.md:**
- Kỹ thuật mới chưa có trong skill → đề xuất bổ sung
- Quy tắc mới phát hiện → đề xuất cho `quality/`
- Pattern đáng ghi nhận → đề xuất cho `style/`

---

## Đánh Giá Dấu Hiệu AI (Self-Check)

Khi phân tích output của chính mình, kiểm tra thêm:

**Dấu hiệu AI trong cách trình bày:**
- Template rigidity: Bố cục theo khuôn mẫu cố định?
- Paragraph uniformity: Các đoạn đều đặn về độ dài?
- Transition overuse: Lạm dụng "Tuy nhiên", "Bên cạnh đó", "Ngoài ra"?
- Cautious hedging: Quá nhiều "có thể", "thường", "một cách nào đó"?
- Artificial chaos: Cố viết "tự nhiên" nhưng vẫn lộ cấu trúc ẩn?

**Dấu hiệu AI trong nội dung:**
- Generic specificity: Chi tiết cụ thể nhưng quá an toàn, thiếu personal depth?
- Emotional flatness: Nhiều sự kiện nhưng thiếu đầu tư cảm xúc thật?
- Encyclopedic knowledge: Biết rộng nhưng thiếu chiều sâu đặc thù?
- Cultural genericism: Tham chiếu văn hóa quá chung chung?

→ Nếu phát hiện → sửa bài viết hoặc ghi nhận vào `quality/natural.md` để tránh lần sau.

---

## Nguyên Tắc

- **Evidence-first:** Chỉ phân tích có dẫn chứng, trích dẫn chính xác
- **Không suy đoán:** Phân biệt rõ quan sát vs diễn giải
- **Tỷ lệ phù hợp:** Văn bản đơn giản → phân tích ngắn
- **Không có = không phân tích:** Nếu không có kỹ thuật đặc biệt, nói thẳng
