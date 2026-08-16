# 📜 Quy Chuẩn Tiêu Chí Thành Công & Bộ Rubrics Định Lượng Đa Miền (CCBA Success Criteria Rubrics)

> **Trạng thái:** Chính thức ban hành (Sau phiên phỏng vấn Socrates /ccba-grilling ngày 2026-08-16)  
> **Cơ sở lý thuyết:** Đúc kết từ [The AI Engineer Mindset](https://www.aihero.dev/the-ai-engineer-mindset), [Anthropic Claude Docs](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests), [Claude Cookbook](https://platform.claude.com/cookbook/misc-building-evals), và [17 Techniques For Improving Your LLM-Powered App](https://www.aihero.dev/how-to-improve-your-llm-powered-app).  
> **Áp dụng cho:** Toàn bộ hệ thống AI Skills, Workflows, và CI Gates của CCBA Platform.

---

## 1. Khung Chấm Điểm & Thang Đo Hỗn Hợp (Hybrid Scoring Framework)

Toàn bộ hệ thống đánh giá của CCBA Platform sử dụng mô hình chấm điểm hỗn hợp kết hợp giữa **Code-based Assertions** và **Model-based Rubrics (Likert 1–5)**:

```
                  ┌─────────────────────────────────────────────────┐
                  │          BÀI KIỂM ĐỊNH NĂNG LỰC (EVAL)          │
                  └────────────────────────┬────────────────────────┘
                                           │
             ┌─────────────────────────────┴─────────────────────────────┐
             ▼                                                           ▼
┌───────────────────────────────┐                       ┌───────────────────────────────┐
│     Code-based Assertions     │                       │     LLM-as-a-Judge Rubrics    │
│  (Exact, Regex, JSON Schema)  │                       │  (Likert Scale 1-5 with CoT)  │
│      Điểm: 0% hoặc 100%       │                       │   Score = (Likert - 1)/4 * 100│
└──────────────┬────────────────┘                       └───────────────┬───────────────┘
               │                                                        │
               └─────────────────────────────┬──────────────────────────┘
                                             ▼
                        ┌────────────────────────────────────────┐
                        │      Tổng Điểm Có Trọng Số (0-100%)    │
                        │    Ngưỡng Đạt: Tổng Điểm >= 85%        │
                        │  VÀ Không Có Tiêu Chí Điểm Liệt (=0/1) │
                        └────────────────────────────────────────┘
```

### Quy tắc Điểm Liệt (Hard Floor / Fail Fast):
- Nếu bất kỳ tiêu chí an toàn, pháp lý hoặc chống ảo giác cốt lõi nào bị đánh giá **Điểm Liệt (Fail)**, toàn bộ bài Eval bị đánh trượt ngay lập tức bất chấp tổng điểm trung bình.

---

## 2. Bảng Rubrics Chi Tiết Cho 3 Miền Nghiệp Vụ Cốt Lõi

### A. Miền 1: Thẩm Tra QC Thiết Kế Đa Bộ Môn (PCCC, Kiến Trúc, MEP)
*Căn cứ quy chuẩn:* QCVN 06:2022/BXD, SĐ 1:2023, TCVN 3890:2023, NĐ 105/2025/NĐ-CP.

| Trọng số | Tiêu chí Đánh giá | Phương pháp Chấm | Quy tắc Điểm Liệt (Hard Floor) |
|---|---|---|---|
| **40%** | **Độ nhạy Bắt lỗi An toàn (False Negative Prevention)**<br>Không bỏ sót lỗi an toàn sinh mạng, lối thoát nạn, bậc chịu lửa. | LLM Rubric + Golden Cases | ❌ **ĐIỂM LIỆT**: Bỏ sót bất kỳ lỗi an toàn nghiêm trọng nào $\rightarrow$ **0 điểm**. |
| **30%** | **Viện dẫn Quy chuẩn Chuẩn xác (Legal Grounding)**<br>Trích dẫn đúng số hiệu Điều, Khoản, Bảng của văn bản đang còn hiệu lực. | Code String / Regex + LLM Judge | ❌ **ĐIỂM LIỆT**: Viện dẫn văn bản hết hiệu lực hoặc sai điều khoản $\rightarrow$ **0 điểm**. |
| **20%** | **Chống Cảnh Báo Ảo (False Positive Control)**<br>Không phát hiện lỗi "ma" làm phiền kỹ sư tư vấn. | Ratio Check: $\frac{FP}{Total} \le 5\%$ | Giảm trừ điểm theo tỷ lệ cảnh báo sai lệch. |
| **10%** | **Định dạng Bảng Kiểm Soát (Matrix Table Format)**<br>Bảng Markdown 5 cột chuẩn (Vị trí, Hiện trạng, Yêu cầu, Đánh giá, Kiến nghị). | Code Parser (Pydantic / Regex) | Đạt 100% nếu đúng cấu trúc bảng; 0% nếu vỡ bảng. |

---

### B. Miền 2: Pháp Điển Xây Dựng & Hợp Nhất Văn Bản (Legal Intel & VBHN Engine)
*Căn cứ quy chế:* Luật Ban hành VBPL, NĐ 34/2016/NĐ-CP, NĐ 154/2020/NĐ-CP, Open Knowledge Format (OKF v2.0).

| Trọng số | Tiêu chí Đánh giá | Phương pháp Chấm | Quy tắc Điểm Liệt (Hard Floor) |
|---|---|---|---|
| **35%** | **Rào chắn Hiệu lực Văn bản (Temporal Grounding)**<br>Nhận diện chuẩn xác ngày ban hành, ngày có hiệu lực, tình trạng sửa đổi bổ sung. | Code Date/Status Check | ❌ **ĐIỂM LIỆT**: Khẳng định văn bản đã hết hiệu lực là "đang áp dụng" $\rightarrow$ **0 điểm**. |
| **35%** | **Độ chính xác Hợp nhất Delta Patch (AST Integrity)**<br>Thao tác `replace`, `insert`, `abrogate` khớp 100% từng từ ngữ pháp lý gốc. | AST Diff Exact Match | ❌ **ĐIỂM LIỆT**: Làm sai lệch ngữ nghĩa pháp lý (ví dụ: "phải" thành "có thể") $\rightarrow$ **0 điểm**. |
| **20%** | **Độ sâu Căn cứ Pháp lý (Citation Depth)**<br>Dẫn chiếu chi tiết đến tận cấp Khoản, Điểm (ví dụ: *Điểm b Khoản 2 Điều 15*). | Regex Pattern Matching | Likert 1–5: Trừ điểm nếu chỉ dẫn chung chung tên Luật. |
| **10%** | **Bảo tồn Định dạng OKF v2.0 (Cleanliness)**<br>Metadata độc lập, sạch thẻ `<think>`, AST node mapping hai chiều đầy đủ. | Linter / JSON Schema | 100% nếu tuân thủ 100% chuẩn OKF. |

---

### C. Miền 3: Viết Học Thuật, Soạn Thảo Văn Bản & Báo Cáo Seminar
*Căn cứ quy chuẩn:* Cấu trúc khoa học IMRAD, Thể thức văn bản NĐ 30/2020/NĐ-CP, Phong cách Viết Tiếng Việt Chuyên Gia CCBA.

| Trọng số | Tiêu chí Đánh giá | Phương pháp Chấm | Quy tắc Điểm Liệt (Hard Floor) |
|---|---|---|---|
| **35%** | **Xác thực Dữ liệu & Chống Bịa Trích Dẫn (No Hallucination)**<br>Mọi số liệu, trích dẫn học thuật bắt buộc phải có thật từ nguồn `input_documents/`. | LLM Judge + Ground Truth check | ❌ **ĐIỂM LIỆT**: Bịa đặt tên tác giả, năm xuất bản, hoặc số liệu thí nghiệm $\rightarrow$ **0 điểm**. |
| **25%** | **Cấu trúc Bố cục Chuyên môn (Structural Compliance)**<br>Tuân thủ chuẩn mực IMRAD (Bài báo) hoặc Thể thức NĐ 30/2020 (Văn bản). | AST Heading & Section Check | Chấm theo thang kiểm tra đầy đủ các đề mục bắt buộc. |
| **25%** | **Văn phong Tiếng Việt Chuyên Gia (Academic Tone)**<br>Ngôn ngữ kỹ thuật súc tích, giữ nguyên thuật ngữ quốc tế (BIM, MEP, API), không dịch ngô nghê. | LLM Rubric (Likert 1–5) | 1=Dịch máy thô; 3=Khá; 5=Chuẩn mực chuyên gia đầu ngành. |
| **15%** | **Độ Sẵn Sàng Xuất Bản (Export Readiness)**<br>Tương thích hoàn hảo bảng Markdown, công thức $\LaTeX$, và định dạng Word/Marp. | Code Parser (Regex & MathML) | Đạt 100% nếu render mượt mà không lỗi cú pháp. |

---

## 3. Rào Chắn Kỹ Thuật & Giới Hạn Vận Hành (Operational Guardrails)

1. **Kỷ luật 2 Tầng Tốc độ (2-Tier Test Speed SLA):**
   - **Tầng 1 — Fast Evals:** Khống chế thời gian thực thi **$< 2.0$ giây** (`pytest -m "fast and not slow"`). Chỉ chạy Code-based assertions in-memory.
   - **Tầng 2 — Deep Evals:** Chạy ngầm qua Background Task (`safe_runner.py`), timeout tối đa **90 giây**, tự động kích hoạt API Circuit Breaker khi có sự cố mạng/gateway.
2. **Ngưỡng Vòng Lặp Tự Sửa Lỗi (Self-Healing Retry Cap):**
   - Giới hạn tối đa **3 vòng lặp tự tối ưu hóa (Max 3 iterations)**.
   - Nếu sau 3 lần sửa mà điểm số vẫn $< 85\%$ hoặc dính Điểm Liệt, hệ thống dừng lại, ghi nhận vào `diagnostics.json` và yêu cầu Kỹ sư can thiệp.
3. **Quản lý Dữ liệu Benchmark (Data Segregation):**
   - Dữ liệu Golden Cases và Rubrics lưu tại `.agents/skills/eval-gate/test_cases/`.
   - Kết quả chạy thực tế và chẩn đoán lưu tại `.md/scratch/eval_runs/`.
   - Không lưu rác kiểm thử vào mã nguồn chính.
