# Phân Tích Dữ Liệu — Analysis

**Module:** research/analysis
**Mục đích:** Chuyển đổi dữ liệu thô thành insights có ý nghĩa để viết content.

---

## Khi Nào Dùng

- ✅ User cung cấp dữ liệu thô (số liệu, bảng)
- ✅ Data có nhưng chưa rõ ý nghĩa/insight
- ✅ Cần trả lời "So what?" từ một tập số liệu
- ❌ User đã cung cấp insights sẵn
- ❌ Data đơn giản, insight rõ ràng

---

## Quy Trình

### Bước 1: Hiểu Data

4 câu hỏi: Đo lường gì? Phạm vi thời gian? Context/benchmark? Độ tin cậy?

### Bước 2: Tìm Patterns

| Pattern | Hỏi | Ví dụ |
|---------|-----|-------|
| Trends | Tăng/giảm? Tốc độ? | Tăng trưởng gia tốc 20% → 25% → 27% |
| Comparisons | Cao/thấp hơn benchmark? | Thấp hơn 33% so với trung bình ngành |
| Distributions | Tập trung ở đâu? 80/20? | 80% doanh thu từ 20% khách hàng |
| Correlations | Hai metrics liên hệ? | Tăng 10% ads → tăng 5% conversions |
| Anomalies | Điểm bất thường? | Sales tháng 11 tăng 300% (Black Friday) |
| Paper Mining | Paper gốc nói gì khác? | Đào sâu paper arXiv, rút chi tiết bất ngờ thay vì tổng hợp bề mặt |
| Theory Anchor | Lý thuyết/nguyên lý nào áp dụng? | Neo vào Goodhart's Law, Perrow "normal accidents" |

### Bước 3: Extract Insights

**Insight = Pattern + Context + Implication**

Cho mỗi pattern: "Điều này có nghĩa gì?" → "Tại sao?" → "Quan trọng như thế nào?" → "Nên làm gì?"

### Bước 4: Prioritize

**ICE Score:** Impact (1-10) × Clarity (1-10) × Evidence (1-10)

Chọn top 3-5 insights để viết content.

---

## Output

```
## Key Findings

1. **[Insight Title]**
   - Pattern: [Mô tả]
   - Data: [Số liệu]
   - Implication: [Ý nghĩa]
   - Action: [Đề xuất]
```

Sau đó chuyển sang style module phù hợp (V1/V3).

---

## Anti-Patterns

```
❌ Chỉ liệt kê số liệu → ✅ Extract insight ("so what?")
❌ Insight quá obvious → ✅ Dig deeper
❌ Data dump → ✅ Synthesize: "Từ 100 data points, 3 insights nổi bật..."
```
