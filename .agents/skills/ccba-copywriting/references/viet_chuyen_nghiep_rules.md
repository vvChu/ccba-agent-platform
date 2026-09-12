# ccba-viet-chuyen-nghiep — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Cẩm nang quy tắc ngữ pháp, văn phong chuyên nghiệp và kiểm tra chất lượng bài viết
> **Mô tả gốc:** Viết tiếng Việt chuyên nghiệp — nhà xuất bản AI. Hỗ trợ soạn thảo, review, biên tập, và xuất bản nội dung chuẩn phong cách.
> **Router Index (Level 3):** Tra cứu chi tiết 27 submodules tại [viet_chuyen_nghiep/INDEX.md](./viet_chuyen_nghiep/INDEX.md).

---

# Nhà Xuất Bản AI — v3.0

## ⚠️ Always Check (mọi output tiếng Việt)

TRƯỚC KHI XUẤT bất kỳ nội dung nào, LUÔN kiểm tra 3 lỗi (ngoại trừ khi soạn thảo văn bản hành chính theo chuẩn Nghị định 30/2020/NĐ-CP hoặc trích dẫn văn bản pháp luật VBPL):

1. **Cấm em-dash `—`** → thay bằng ` - ` (cách hai bên) hoặc viết lại câu (ngoại trừ dấu gạch đầu dòng liệt kê trong văn bản hành chính).
2. **Hạn chế dấu hai chấm `:`** → thay bằng từ nối: `là`, `rằng`, `như sau` (ngoại trừ dấu hai chấm sau phần căn cứ pháp lý hoặc trước phần danh sách liệt kê).
3. **Cấm Oxford comma** → `A, B và C` (không phải `A, B, và C`).

---

## Bước 1: Keyword Router

Scan request → match keyword → xác định modules bắt buộc.

| Keyword trong request | Module BẮT BUỘC load |
|---|---|
| viết blog, storytelling | `write/story-core` + `write/hook-close` + `write/rhythm` |
| viết sách, viết chương | `write/book-chapter` |
| viết kỹ thuật, whitepaper, academic | `write/technical` |
| phản bác, debunk | `write/debunk` + (`write/story-core` hoặc `write/book-chapter`) |
| review, kiểm tra, rà soát, duyệt | → Chạy **Quy trình SCAN** |
| format facebook, đăng fb | `publish/facebook` |
| format sách | `publish/book` |
| nghiên cứu, research | `research/research` |
| phân tích data, dữ liệu | `research/analysis` |
| liên chương, cross-doc, nhất quán | `check/cross-doc` |
| fact-check, số liệu | `check/fact-check` |
| ẩn dụ, metaphor | `write/metaphor` |
| công thức, formula | `write/formula-box` |
| audit, phân tích bài mẫu | `development/style-audit` |
| nâng cấp skill, cập nhật pattern | `development/upgrade` |

---

**Tiêu chí hoàn thành:** Xác định đúng danh sách modules bắt buộc.

---

## Bước 2: Đọc danh sách & Suy luận sâu

**BẮT BUỘC** sau bước 1. Không được bỏ qua.

### 2a. Đọc lướt Module Registry

Đọc lại toàn bộ bảng Module Registry (cuối file này) để nắm rõ khả năng của từng module. Mục đích: biết MỌI công cụ trước khi quyết định dùng công cụ nào.

### 2b. Phân tích yêu cầu (5 câu hỏi)

| # | Câu hỏi | Quyết định |
|---|---------|-----------|
| 1 | **User cung cấp gì?** Data thô, ý tưởng, hay topic trống? | Cần `research/research` hoặc `research/analysis`? |
| 2 | **Mục đích?** Inspire, educate, instruct, inform, debunk? | `write/story-core` hay `write/technical` hay `write/debunk`? |
| 3 | **Độc giả?** Công chúng, professionals, technical? | Tone, depth, + `write/reframe` hay `write/emphasis`? |
| 4 | **Platform?** Facebook, blog, sách, tài liệu? | Cần `publish/facebook` hay `publish/book`? |
| 5 | **Có claims/số liệu?** Statistics, quotes, facts? | Cần `check/fact-check`? Cần `write/formula-box`? |

### 2c. Chọn modules (cần và đủ)

Từ kết quả 2a + 2b, lập danh sách modules cuối cùng. Nguyên tắc:
- **Cần:** Thiếu module này thì output bị lỗi hoặc thiếu
- **Đủ:** Thêm module nào nữa thì dư thừa, làm chậm
- Nếu cần kỹ thuật viết cụ thể → tra `pattern-catalog` để chọn đúng pattern

---

**Tiêu chí hoàn thành:** Hoàn thành phân tích 5 câu hỏi và chốt danh sách modules.

---

## Bước 3: Xây dựng Pipeline

### Quy tắc kích hoạt

- **< 3 modules HOẶC cùng 1 nhóm** → thực thi trực tiếp, không cần pipeline
- **≥ 3 modules VÀ thuộc ≥ 2 nhóm** → BẮT BUỘC xây pipeline

### 4 dạng pipeline (AI tự quyết định dạng phù hợp)

**1. Tuyến tính (Linear)** — mặc định, dùng khi các bước phụ thuộc tuần tự.
```
RESEARCH → WRITE → CHECK → PUBLISH
```

**2. Song song (Parallel)** — dùng khi nhiều write modules độc lập, gộp kết quả sau.
```
              ┌→ write/metaphor ──┐
RESEARCH → ──┤→ write/debunk   ──├→ GỘP → CHECK → PUBLISH
              └→ write/emphasis ──┘
```

**3. Điều kiện (Conditional)** — dùng khi CHECK quyết định bước tiếp.
```
WRITE → CHECK ──┬→ ✅ pass → PUBLISH
                └→ ❌ fail → SỬA → CHECK lại
```

**4. Vòng lặp (Loop)** — dùng khi viết nhiều chương/sections lặp đi lặp lại.
```
for mỗi chương:
    WRITE(chương N) → CHECK(chương N) → GATE
    └→ ❌ → sửa → lặp lại
end
PUBLISH(toàn bộ)
```

### GATE check (cổng bàn giao)

Mỗi mũi tên `→` trong pipeline là 1 GATE check:

```
[GATE] ✅ → output đạt → chuyển giai đoạn tiếp
[GATE] ❌ → liệt kê vấn đề → sửa → thử lại
```

Chi tiết GATE cho từng giai đoạn:

| Giai đoạn | GATE ✅ khi | GATE ❌ khi |
|-----------|-----------|-----------|
| RESEARCH → WRITE | Content Brief đầy đủ (5W1H, sources, angle) | Thiếu thông tin then chốt |
| WRITE → CHECK | Draft hoàn chỉnh, đủ nội dung theo yêu cầu | Thiếu sections, logic đứt |
| CHECK → PUBLISH | SCAN pass, không vi phạm | Còn vi phạm → sửa → SCAN lại |
| PUBLISH → Output | Đúng format platform | Lỗi format → sửa |

### 5 quy tắc pipeline

1. **Không nhảy giai đoạn:** WRITE xong phải qua CHECK
2. **Không trộn giai đoạn:** Viết xong rồi mới check
3. **CHECK luôn chạy SCAN:** Mọi output viết đều phải SCAN
4. **Bỏ qua RESEARCH:** Nếu user đã cung cấp đủ thông tin
5. **Bỏ qua PUBLISH:** Nếu không cần format đặc biệt (FB, sách)

### Ví dụ

```
Request: "Viết chương sách phản bác quan điểm X, format sách, có ẩn dụ"

Bước 1 (keyword): write/book-chapter, write/debunk, write/metaphor, publish/book
Bước 2 (suy luận): + check/* (bắt buộc), kiểm tra pattern-catalog
→ 6+ modules, 3 nhóm → BẮT BUỘC pipeline

Pipeline (song song + tuyến tính):
  WRITE ─┬→ book-chapter (cấu trúc chương) ──┐
         ├→ debunk (5 bước phản bác)          ├→ GỘP Draft 1
         └→ metaphor (ẩn dụ mở rộng)         ┘
  [GATE] Draft 1 → đủ nội dung? ✅
  CHECK → SCAN (consistency→fact-check→...→punctuation) → Draft 2
  [GATE] Draft 2 → SCAN pass? ✅
  PUBLISH → book format → Output
```

---

**Tiêu chí hoàn thành:** Thiết lập pipeline phù hợp với đầy đủ GATE checks.

---

## Quy trình SCAN (review 4 bước)

Áp dụng khi: (1) keyword "review/kiểm tra/rà soát" hoặc (2) GATE CHECK.

```
SCAN  → grep_search theo Grep Patterns trong các file check/
LIST  → lập bảng: | Dòng | Nội dung vi phạm | Quy tắc |
CHECK → kiểm tra thủ công từng dòng (loại false positive)
PASS  → Đạt/Không đạt → phiếu sửa nếu Fail
```

**Thứ tự scan (logic → nội dung → hình thức → ký tự):**

| Tầng | Module | Kiểm tra | Phương pháp |
|------|--------|----------|-------------|
| 1. Logic | `check/consistency` | Tone nhất quán, thuật ngữ xuyên suốt, xung đột nội bộ | đọc |
| 2. Nội dung | `check/fact-check` | Số liệu, trích dẫn, claims (nếu có) | đọc |
| 3. Nội dung | `check/cross-doc` | Nhất quán liên chương (nếu ≥2 file) | đọc |
| 4. Chất lượng | `check/ai-detection` | Over-formatting, transition overuse, hedging | grep + đọc |
| 5. Hình thức | `check/prose-format` | Bullet→prose, inline enum, biến thiên đoạn | grep + đọc |
| 6. Hình thức | `check/english-mixing` | Trộn tiếng Anh, chuẩn Việt-Anh | grep |
| 7. Ký tự | `check/capitalization` | Title Case, heading hierarchy | grep |
| 8. Ký tự | `check/punctuation` | Em-dash, colon, Oxford comma, spacing | grep |

---

## Module Registry

Sắp xếp theo thứ tự pipeline: research → write → check → publish → tra cứu → phát triển.

### research/ — Thu thập (2 modules)

| Module | Mục đích | Dòng |
|--------|----------|------|
| `research/research` | Thu thập 5W1H, 3-tier research, content brief | 81 |
| `research/analysis` | Rút insights từ data thô, ICE scoring, paper mining | 72 |

### write/ — Viết nội dung (10 modules)

| Module | Mục đích | Dòng |
|--------|----------|------|
| `write/story-core` | Xây dựng câu chuyện từ insight - logic chain, show/tell, dịch thuật ngữ | 116 |
| `write/hook-close` | Mở bài + kết bài - 4 hook mở, 3 kỹ thuật kết | 72 |
| `write/rhythm` | Phân bố đoạn văn, nhịp cảm xúc, tạo biến thiên 70-20-10 | 72 |
| `write/book-chapter` | Viết chương sách dài >5.000 từ, Cold Pedagogy, Recap-Build-Bridge, RAC | 154 |
| `write/technical` | Tài liệu kỹ thuật/academic - topic sentence, logic flow, heading | 107 |
| `write/formula-box` | Format công thức hộp 💡 trong bảng viền | 34 |
| `write/metaphor` | Ẩn dụ mở rộng, chồng lớp, vòng lặp, liên chương, tổng hợp | 120 |
| `write/reframe` | Concept naming, paradox flip, parallel analogy | 95 |
| `write/debunk` | Phản bác 5 bước, gentle debunk, trích dẫn tiếng Anh nguyên văn | 87 |
| `write/emphasis` | Strategic caps (IN HOA), tách dòng nhấn mạnh, lật khung nhìn | 57 |

### check/ — Kiểm tra chất lượng (8 modules)

| Tầng | Module | Mục đích | Phương pháp | Dòng |
|------|--------|----------|-------------|------|
| Logic | `check/consistency` | Tone nhất quán, thuật ngữ xuyên suốt | đọc | 70 |
| Nội dung | `check/fact-check` | Kiểm chứng số liệu, trích dẫn, claims | đọc | 72 |
| Nội dung | `check/cross-doc` | Nhất quán liên chương - thuật ngữ, case study | đọc | 101 |
| Chất lượng | `check/ai-detection` | Over-formatting, transition overuse, hedging | grep + đọc | 54 |
| Hình thức | `check/prose-format` | Bullet→prose, inline enumeration, ký hiệu nối | grep + đọc | 78 |
| Hình thức | `check/english-mixing` | Trộn tiếng Anh, chuẩn Việt trước English sau | grep | 43 |
| Ký tự | `check/capitalization` | Title Case, heading H1/H2+ | grep | 59 |
| Ký tự | `check/punctuation` | Em-dash, colon, Oxford comma, spacing, ngoặc | grep | 128 |

### publish/ — Xuất bản (2 modules)

| Module | Mục đích | Dòng |
|--------|----------|------|
| `publish/facebook` | FB cá nhân: plaintext, IN HOA chiến lược. FB page: giữ markdown | 107 |
| `publish/book` | Heading hierarchy sách, italic summary, disclaimer, RAC | 90 |

### Tra cứu & Phát triển

| File | Mục đích | Khi nào dùng | Dòng |
|------|----------|-------------|------|
| `pattern-catalog` | 54 patterns viết, 8 nhóm | Bước 2c: tra cứu kỹ thuật viết cụ thể khi chọn modules | 105 |
| `development/style-audit` | Phân tích bài viết → rút pattern, đánh giá style DNA | Keyword: audit, phân tích bài mẫu | 133 |
| `development/upgrade` | Rút pattern từ output → bổ sung vào skill | Keyword: nâng cấp skill, cập nhật pattern | 119 |
| `development/research-framework` | Phương pháp nghiên cứu có hệ thống | Cần research approach mới | 146 |
| `development/research-results` | Kết quả nghiên cứu đã thực hiện | Tham khảo kết quả cũ | 29 |
