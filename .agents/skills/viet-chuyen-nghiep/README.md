# Viết Chuyên Nghiệp v3.0 — Nhà Xuất Bản AI

Skill viết tiếng Việt chuyên nghiệp. Phân tích yêu cầu → xác định modules → tự xây pipeline → GATE check → xuất bản.

---

## 0. Cảm hứng thiết kế

Skill này được thiết kế theo mô hình **nhà xuất bản** (publishing house) - nơi một bản thảo đi qua nhiều giai đoạn chuyên môn trước khi trở thành ấn phẩm hoàn chỉnh.

### Tại sao nhà xuất bản?

Các phiên bản trước (v1-v2) dùng ẩn dụ **tòa soạn báo** (newsroom) với phòng ban và trưởng ban. Mô hình đó phù hợp khi có nhiều AI agent phối hợp, nhưng thực tế chỉ có 1 agent xử lý → hệ thống phân cấp trở nên dư thừa.

Nhà xuất bản phù hợp hơn vì hoạt động theo **quy trình tuần tự có kiểm soát** - đúng bản chất của skill:

| Nhà xuất bản thực tế | Skill v3.0 |
|----------------------|------------|
| Nhận đề tài, nghiên cứu thị trường | `research/` — thu thập thông tin, phân tích data |
| Viết bản thảo (manuscript) | `write/` — 10 modules viết chuyên biệt |
| Hiệu đính, đọc bông (proofreading) | `check/` — 8 tầng kiểm tra (logic→ký tự) |
| Duyệt bản thảo giữa các lần đọc bông | GATE check — cổng bàn giao giữa giai đoạn |
| Dàn trang, trình bày ấn phẩm | `publish/` — format cho Facebook, sách |
| Xuất bản, phát hành | Output cuối cùng |
| Kho kỹ thuật viết của tòa soạn | `pattern-catalog` — 54 patterns, 8 nhóm |
| Đào tạo nội bộ, nâng cao tay nghề | `development/` — audit, upgrade, research |

### Khác biệt với Swarm v2.0 (Tòa Soạn Báo)

| Tiêu chí | Swarm v2.0 | Nhà Xuất Bản v3.0 |
|----------|-----------|-------------------|
| Đơn vị cơ bản | Con người (BTV, trưởng ban) | Module (hàm xử lý) |
| Routing | Model tự đoán gọi ban nào | Keyword deterministic → THINK → pipeline |
| Quality check | Đọc lướt (chủ quan) | SCAN tự động (grep) + đọc thủ công |
| Pipeline | Cố định 3 bước | 4 dạng linh hoạt, tự xây theo request |
| Trùng lặp | Có (rules ở nhiều file) | 0 trùng lặp |
| Context window | Nặng (load lead + manager + worker) | Nhẹ (chỉ load modules cần) |
| Tự nâng cấp | Không | development/ modules |

---

## 1. Cấu trúc thư mục

```
viet-chuyen-nghiep/
├── SKILL.md                              ← Routing + Pipeline + GATE + SCAN
├── README.md                             ← File này
│
└── resources/
    ├── research/                         ← Thu thập (2 modules)
    │   ├── research.md            (81)   ← 5W1H, 3-tier, content brief
    │   └── analysis.md            (72)   ← Rút insights, ICE scoring
    │
    ├── write/                            ← Viết nội dung (10 modules)
    │   ├── story-core.md         (116)   ← Insight, logic chain, show/tell
    │   ├── hook-close.md          (72)   ← 4 hook mở + 3 kỹ thuật kết
    │   ├── rhythm.md              (72)   ← Pacing 70-20-10, biến thiên đoạn
    │   ├── book-chapter.md       (154)   ← Kiến trúc chương dài, Cold Pedagogy
    │   ├── technical.md          (107)   ← Academic: topic sentence, logic flow
    │   ├── formula-box.md         (34)   ← Format công thức hộp 💡
    │   ├── metaphor.md           (120)   ← Ẩn dụ mở rộng + liên chương
    │   ├── reframe.md             (95)   ← Concept naming, paradox flip
    │   ├── debunk.md              (87)   ← Phản bác 5 bước, gentle debunk
    │   └── emphasis.md            (57)   ← Strategic caps, tách dòng
    │
    ├── check/                            ← Kiểm tra chất lượng (8 modules)
    │   ├── punctuation.md        (128)   ← Em-dash, colon, Oxford comma
    │   ├── capitalization.md      (59)   ← Title Case, heading hierarchy
    │   ├── english-mixing.md      (43)   ← Trộn Anh, chuẩn Việt-Anh
    │   ├── prose-format.md        (78)   ← Bullet→prose, inline enum
    │   ├── ai-detection.md        (54)   ← Over-formatting, transition, hedging
    │   ├── consistency.md         (70)   ← Tone, thuật ngữ nhất quán
    │   ├── fact-check.md          (72)   ← Số liệu, trích dẫn, claims
    │   └── cross-doc.md          (101)   ← Nhất quán liên chương (≥2 file)
    │
    ├── publish/                          ← Xuất bản (2 modules)
    │   ├── facebook.md           (107)   ← FB cá nhân (plaintext) + FB page
    │   └── book.md                (90)   ← Heading, summary, disclaimer, RAC
    │
    ├── pattern-catalog.md        (105)   ← 54 patterns, 8 nhóm
    │
    └── development/                      ← Nâng cấp skill (4 files)
        ├── style-audit.md        (133)
        ├── upgrade.md            (119)
        ├── research-framework.md (146)
        └── research-results.md    (29)
```

**Tổng:** 27 files · ~2.600 dòng · Thứ tự cây theo pipeline: research → write → check → publish

---

## 2. Cách hoạt động

### 2.1. Quy trình xử lý request

```
Request
  │
  ▼
Bước 1: KEYWORD ROUTER ──── match keyword → modules bắt buộc
  │
  ▼
Bước 2: ĐỌC & SUY LUẬN
  2a. Đọc lướt Module Registry → nắm toàn bộ khả năng
  2b. 5 câu hỏi phân tích → xác định modules bổ sung
  2c. Chọn modules CẦN VÀ ĐỦ (tra pattern-catalog nếu cần)
  │
  ▼
Bước 3: XÂY PIPELINE
  ≥3 modules + ≥2 nhóm → xây pipeline (4 dạng) + GATE check
  <3 modules hoặc 1 nhóm → thực thi trực tiếp
  │
  ▼
Always Check (3 rules) + Output
```

### 2.2. Bước 2 - Đọc & Suy luận

**Bắt buộc** sau keyword router. Không được nhảy thẳng vào viết.

1. **Đọc lướt** toàn bộ Module Registry (SKILL.md cuối file) để biết MỌI công cụ
2. **Trả lời 5 câu hỏi:** User cung cấp gì? Mục đích? Độc giả? Platform? Có claims?
3. **Chọn đúng mức:** Cần = thiếu thì lỗi. Đủ = thêm thì dư. Tra `pattern-catalog` khi cần kỹ thuật viết cụ thể

### 2.3. Pipeline & GATE

**Khi nào cần pipeline:**
- **< 3 modules HOẶC cùng 1 nhóm** → thực thi trực tiếp
- **≥ 3 modules VÀ ≥ 2 nhóm** → xây pipeline + GATE check

**4 dạng pipeline (AI tự quyết định):**

| Dạng | Khi nào | Ví dụ |
|------|---------|-------|
| **Tuyến tính** | Các bước phụ thuộc tuần tự | RESEARCH → WRITE → CHECK → PUBLISH |
| **Song song** | Nhiều write modules độc lập | debunk + metaphor + emphasis chạy song song, gộp |
| **Điều kiện** | CHECK quyết định bước tiếp | CHECK pass → PUBLISH, fail → SỬA → CHECK lại |
| **Vòng lặp** | Viết nhiều chương lặp lại | for mỗi chương: WRITE → CHECK → GATE |

**GATE check** = cổng bàn giao giữa giai đoạn:
```
[GATE] ✅ → đạt → chuyển tiếp
[GATE] ❌ → liệt kê vấn đề → sửa → thử lại
```

**5 quy tắc cứng:**
1. Không nhảy giai đoạn - WRITE xong phải qua CHECK
2. Không trộn giai đoạn - viết xong rồi mới check
3. CHECK luôn chạy SCAN - dù không nói "review"
4. Bỏ qua RESEARCH nếu user đã cung cấp đủ thông tin
5. Bỏ qua PUBLISH nếu không cần format đặc biệt

### 2.4. Quy trình SCAN

Chạy trong giai đoạn CHECK hoặc khi keyword "review/kiểm tra/rà soát".

```
SCAN  → grep_search theo Grep Patterns trong check/ files
LIST  → lập bảng: | Dòng | Nội dung vi phạm | Quy tắc |
CHECK → kiểm tra thủ công từng dòng (loại false positive)
PASS  → Đạt/Không đạt → phiếu sửa nếu Fail
```

**Thứ tự (logic → nội dung → hình thức → ký tự):**
consistency → fact-check → cross-doc → ai-detection → prose-format → english-mixing → capitalization → punctuation

---

## 3. Quy ước file

### 3.1. Header chuẩn

```markdown
# [Tên Tiếng Việt] — [English Name]

**Module:** [thư-mục/tên-file]
**Mục đích:** [Mô tả 1 dòng]
```

### 3.2. Tên file

- Tất cả tiếng Anh, kebab-case: `story-core.md`, `ai-detection.md`
- Tiêu đề H1: Việt trước — English sau, viết hoa chữ đầu mỗi từ

### 3.3. Không trùng lặp

Mỗi quy tắc chỉ trong 1 file. Tham chiếu bằng:
```markdown
→ Format chi tiết: xem `write/formula-box`
```

---

## 4. Chi tiết modules

### 4.1. research/ (2 modules)

- **research** — 5W1H, 3-tier (primary/secondary/tertiary), xuất Content Brief
- **analysis** — ICE scoring, pattern recognition, rút insights

### 4.2. write/ (10 modules)

3 chế độ chính, KHÔNG trộn:

| Chế độ | Khi nào | Modules |
|--------|---------|---------|
| Blog/storytelling | Bài ngắn, phân tích | story-core + hook-close + rhythm |
| Sách/chương dài | >5.000 từ | book-chapter |
| Kỹ thuật | Academic, whitepaper | technical |

Bổ sung (thêm vào bất kỳ chế độ): metaphor, reframe, debunk, emphasis, formula-box.

### 4.3. check/ (8 modules)

Thứ tự theo tầng kiểm tra: logic → nội dung → hình thức → ký tự.

| Tầng | Module | Phương pháp | Grep Patterns? |
|------|--------|-------------|----------------|
| Logic | consistency | đọc | ❌ |
| Nội dung | fact-check | đọc | ❌ |
| Nội dung | cross-doc | đọc | ❌ |
| Chất lượng | ai-detection | grep + đọc | ✅ `Tuy nhiên,`, `**`, `!` |
| Hình thức | prose-format | grep + đọc | ✅ `^- ` |
| Hình thức | english-mixing | grep | ✅ English words |
| Ký tự | capitalization | grep | ✅ Title Case regex |
| Ký tự | punctuation | grep | ✅ `—`, `, và `, `: ` |

### 4.4. publish/ (2 modules)

- **facebook** — FB cá nhân: plaintext, IN HOA, "mình/tôi". FB page: giữ markdown
- **book** — Heading hierarchy, italic summary, disclaimer, RAC

---

## 5. Pattern Catalog

File `pattern-catalog.md` — 54 kỹ thuật viết, 8 nhóm. Dùng trong **Bước 2c** khi cần chọn kỹ thuật viết cụ thể.

| Nhóm | Số | Ví dụ patterns |
|------|----|---------------|
| 🎯 Mở bài | 5 | Behavioral hook, shock data, prediction |
| 🏗️ Cấu trúc | 9 | Logic chain A→B→C, Recap-Build-Bridge |
| 📊 Dẫn chứng | 9 | Paper mining, show-don't-tell |
| ⚡ Tương phản | 6 | Paradox flip, gentle debunk |
| ✍️ Ngôn ngữ | 7 | Vernacular translation, Strategic caps |
| 🎬 Kết bài | 3 | Callback close, open loop |
| 🔬 Phân tích | 9 | ICE scoring, theory anchor |
| 📖 Sư phạm | 12 | Cold Pedagogy, Running Case Study, RAC |

---

## 6. Development (tự nâng cấp)

4 files trong `development/` — kích hoạt khi keyword "audit/nâng cấp/phân tích bài mẫu".

| File | Mục đích |
|------|----------|
| `style-audit` | Phân tích bài viết → rút pattern, đánh giá style DNA |
| `upgrade` | Rút pattern từ output đã viết → bổ sung vào skill |
| `research-framework` | Phương pháp nghiên cứu có hệ thống |
| `research-results` | Kết quả nghiên cứu đã thực hiện |

**Quy trình nâng cấp:**
1. User nói "phân tích bài mẫu X" → load `style-audit` → rút patterns
2. User nói "nâng cấp skill" → load `upgrade` → bổ sung patterns mới vào `pattern-catalog`

---

## 7. Lịch sử phiên bản

| Version | Ngày | Tính chất | Thay đổi chính |
|---------|------|-----------|----------------|
| v1.0 | 2026-02 | Draft | File đơn, tất cả rules trong 1 SKILL.md |
| v2.0 | 2026-03 | Draft | Newsroom model (Tòa Soạn Báo), lead-staff hierarchy |
| v2.x | 2026-03 | Draft | Swarm routing, 6 lead files, 42→54 patterns |
| **v3.0** | **2026-04-03** | **Official** | **Nhà Xuất Bản AI — bản chính thức đầu tiên** |

### Tính năng v3.0 (Official)

- Keyword Router + Bước THINK bắt buộc (đọc registry → 5Q → chọn cần-đủ)
- 4 dạng pipeline (linear/parallel/conditional/loop) + GATE check
- SCAN protocol (grep tự động, 8 tầng: logic → nội dung → hình thức → ký tự)
- 3 Always Check rules (em-dash, colon, Oxford comma)
- 22 modules (0 trùng lặp, header chuẩn hóa)
- Pattern catalog (54 patterns, 8 nhóm)
- Development modules (audit, upgrade, research)
