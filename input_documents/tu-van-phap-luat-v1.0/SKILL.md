---
name: tu-van-phap-luat
description: TƯ VẤN ĐƯỜNG LỐI XỬ LÝ VẤN ĐỀ PHÁP LÝ VIỆT NAM — TRA CỨU KEYWORD CHÉO QUA CÁC TẦNG VBQPPL, GHÉP NỐI THÀNH SOURCE OF TRUTH TRÍCH DẪN NGUYÊN VĂN, RỒI CHẠY PDCA CASCADE MỞ RỘNG VÀ ĐÀO SÂU. Hỗ trợ định danh vấn đề theo 5 trục (đối tượng, hành vi, tác động, phạm vi, thời điểm), tra chéo VB gốc-sửa đổi-NĐ-TT, xây SOT với trích dẫn nguyên văn có tọa độ, xử lý xung đột lex, so sánh phương án, khuyến nghị đường lối hành động. Kích hoạt khi user đề cập 'pháp luật', 'tư vấn luật', 'tranh chấp', 'bị kiện', 'nghị định'; yêu cầu 'tôi phải làm gì', 'luật quy định thế nào', 'xử lý tình huống này'; nói 'muốn khiếu nại', 'đòi bồi thường', 'thành lập công ty'; trong tình huống gặp vấn đề pháp lý cần đường lối giải quyết. KHÔNG dùng cho nghiên cứu phi pháp lý (→ nghien-cuu-pdca), viết bài (→ viet-chuyen-nghiep). Dùng cho MỌI vấn đề pháp lý — kể cả khi user chỉ nói 'tình huống này xử lý sao' mà không nhắc 'luật'.
---

# Tư Vấn Pháp Luật — PDCA Cascade-Driven

> Khởi tạo Tọa độ & SOT thô → Động cơ PDCA Cascade (Tra cứu - So khớp - Mở rộng) → Tư vấn đường lối.

---

## 1. Triết lý Cốt lõi

1. **Pháp luật VN = bản ghi rời rạc.** Luật, Nghị định, Thông tư là các record riêng lẻ với quan hệ sửa đổi/bổ sung/thay thế/bãi bỏ chồng chéo. Không bao giờ đọc hết — chỉ tra đúng chỗ, ghép đúng thứ tự.
2. **SOT là nền tảng.** Mọi phân tích và tư vấn phải truy ngược được về Source of Truth — tập trích dẫn NGUYÊN VĂN có tọa độ chính xác (VB – Số hiệu – Điều – Khoản – Điểm).
3. **Bắt buộc Hành động & Lưu vết.** Không tự suy luận quá 1 bước mà không gọi tool tra cứu. Mọi hoạt động nghiên cứu pháp lý phải được lưu vết vật lý (Immutable Multi-file Ledger) theo từng giai đoạn (Phase).
4. **Thời điểm quyết định tất cả.** Cùng một vấn đề, cùng một điều luật, nhưng khác thời điểm sẽ khác VB áp dụng (do sửa đổi, thay thế, chuyển tiếp).
5. **Disclaimer.** Skill hỗ trợ nghiên cứu và tư vấn sơ bộ; **không thay thế ý kiến pháp lý chính thức** từ luật sư hoặc cơ quan có thẩm quyền.

---

## 2. Bước 0 — Định danh & Khởi tạo (Phase & Raw SOT)

Trước khi tra cứu bất cứ điều gì, PHẢI khởi tạo không gian và xác định trục tọa độ.

| Trục | Câu hỏi | Ví dụ |
|---|---|---|
| **ĐỐI TƯỢNG** | Ai? Cái gì? (chủ thể, khách thể) | Người lao động; Hợp đồng thuê nhà |
| **HÀNH VI** | Làm gì? (động từ pháp lý) | Sa thải; Đơn phương chấm dứt |
| **TÁC ĐỘNG** | Hệ quả gì? (quyền/nghĩa vụ/trách nhiệm) | Bồi thường; Truy cứu hình sự |
| **PHẠM VI** | Ở đâu? Loại hình? (không gian, bối cảnh) | TP.HCM; Doanh nghiệp FDI |
| **THỜI ĐIỂM** | Khi nào? ★ Trục quan trọng nhất | 15/03/2025 (xác định VB nào áp dụng) |

**Quy trình Khởi tạo:**

1. **Khởi tạo Thư mục & File (Cơ chế N+1 Bắt buộc):**
   - Tạo thư mục `legal_research_[chủ_đề]/`.
   - Kiểm tra xem đã có `legal_phase_X.md` chưa. Đọc file mới nhất để lấy SOT làm Baseline (nếu có). 
   - Tạo file mới `legal_phase_{N+1}.md`.
2. **Định danh 5 trục pháp lý:** Đọc yêu cầu user, điền 5 trục. Thiếu → Hỏi (`ask_question`). Ghi thông tin này vào đầu file phase.
3. **Sinh SOT Thô (Raw SOT):** 
   - Từ 5 trục → sinh bộ keyword (VD: "sa thải"). 
   - Tra bảng "Danh mục Module" (Mục 7) → đọc file trong `resources/domains/` tương ứng.
   - Trích xuất các văn bản xương sống (Luật, Nghị định chính) và tạo bảng SOT thô ban đầu trong file phase.
4. **Xác định Tọa độ đích:** Ghi Target (Câu hỏi cốt lõi) và Exit Condition (Dấu hiệu đủ SOT) vào đầu file phase.

---

## 3. Bước 1 — Động cơ PDCA Cascade (Nuôi lớn SOT)

Đây là **lõi thực thi duy nhất**. Ta sẽ chạy vòng lặp PDCA liên tục trên SOT Thô để bồi đắp nó thành SOT Hoàn chỉnh. Mọi dữ kiện (IPO) của mỗi vòng đều phải ghi nối xuống dưới cùng của file `legal_phase_X.md`.

### [P] Plan — Đặt câu hỏi về SOT hiện tại
Nhìn vào SOT hiện tại (hoặc SOT Thô), đặt câu hỏi để tìm Keyword mới:
- **Chiều xuống**: "Luật này có NĐ/TT nào hướng dẫn chi tiết không?"
- **Chiều ngang**: "Văn bản này đã bị sửa đổi/thay thế/bãi bỏ chưa?"
- **Chiều thời gian**: "Phiên bản nào đang hiệu lực tại mốc THỜI ĐIỂM của user?"
- **Chiều rộng**: "Có vướng pháp luật chuyên ngành nào khác không?" (VD: Tranh chấp lao động có liên đới BHXH?)
→ **Sinh KEYWORD MỚI** và xác định nguồn tìm kiếm (Thư viện pháp luật).

### [D] Do — Hành động Tra cứu
Dùng `search_web` hoặc `read_url_content`. Load `resources/search-sources.md` và `resources/cross-reference-guide.md` để tối ưu.
- **BẮT BUỘC TRÍCH DẪN MÁY MÓC:** Khi tìm thấy dữ liệu, phải trích xuất:
  - Tọa độ: `[Cấp VB] [Số hiệu] – Điều X, Khoản Y, Điểm Z`
  - Nguyên văn: Copy chính xác câu chữ.
  - Trạng thái hiệu lực (tại thời điểm user).

### [C] Check — So khớp & Tìm Mâu thuẫn
Đặt trích dẫn mới lên bàn cân với SOT hiện tại để tìm **Khoảng Trống (GAP) / Mâu thuẫn**:
- **Bổ sung**: Làm rõ SOT thêm.
- **Xung đột ⚠️**: Mâu thuẫn với quy định cũ trong SOT. (Áp dụng Lex Superior/Posterior/Specialis để phân xử).
- **Dư thừa**: Trích dẫn không thêm thông tin mới → Hướng này đã cạn.

### [A] Act — Quyết định & Lưu vết IPO
1. **Quyết định hướng đi:**
   - **Đào sâu (Depth)**: Đã tìm ra Luật, tiếp tục tìm Nghị định.
   - **Mở rộng (Breadth)**: Hướng cũ cạn, chuyển sang lĩnh vực liên quan.
2. **Lưu vết IPO (IMMUTABLE LOGGING):** Ghi (Append) xuống `legal_phase_X.md`:
   - **I (Input):** Giả thuyết vòng này.
   - **P (Process):** Tool & dữ liệu gốc thu được.
   - **O (Output):** Mâu thuẫn tìm thấy, Quyết định cập nhật bảng SOT.
3. **Cập nhật Bảng SOT:** Bổ sung/sửa đổi trực tiếp bảng SOT trong bộ nhớ (để chuẩn bị in ra ở Bước 2).
4. Quay lại [P] nếu chưa thỏa mãn Exit Condition. Mọi hành động dừng lại khi đạt Exit Condition hoặc lặp 2 vòng không ra dữ liệu mới.

---

## 4. Bước 2 — Đóng gói Phase & Xuất Báo cáo Tư vấn (Report)

Chỉ khi SOT đã hoàn chỉnh, thỏa mãn Exit Condition (chốt ở file `legal_phase_X.md`), mới chuyển sang tư vấn. Tư vấn dựa trên SOT chưa đủ sẽ dẫn đến kết luận sai.

### Đóng gói Phase (Chốt file vật lý)
Khi kết thúc phiên nghiên cứu, Agent BẮT BUỘC tổng kết vào cuối file `legal_phase_X.md`:
1. **Sự thật (Truth):** Những phát hiện có SOT đối chứng (kèm nguồn).
2. **Hành động (Actionable):** Giải pháp tư vấn thực tế rút ra.
3. **Khoảng trống (Next Gap):** Những rủi ro/điểm mờ chưa rõ để làm mồi cho đợt nghiên cứu/câu hỏi sau.

### Xuất Báo cáo Tư vấn (Tạo file Report)
Tuyệt đối KHÔNG xuất toàn bộ nội dung tư vấn dài dòng lên khung chat. Agent BẮT BUỘC phải tạo một file báo cáo chính thức mang tên `legal_report_[chủ_đề].md` nằm trong cùng thư mục `legal_research_[chủ_đề]/`. Toàn bộ cấu trúc 5 phần tư vấn sẽ được viết vào file này. Khung chat chỉ dùng để thông báo hoàn thành và tóm tắt ngắn gọn (1 đoạn) kèm link trỏ đến file Report.

**Cấu trúc 5 phần bắt buộc trong file `legal_report_[chủ_đề].md`:**

**(1) Tóm tắt tình huống & Vấn đề pháp lý**
- Xác nhận lại 5 trục (đối tượng, hành vi, tác động, phạm vi, thời điểm)
- Vấn đề pháp lý cốt lõi cần giải quyết
- `[Giả định]` kèm tác động nếu có thông tin chưa xác nhận

**(2) Căn cứ pháp lý — Bảng SOT**
- Bảng SOT đầy đủ (format ở §4)
- Sắp theo thứ bậc, ghi trạng thái, đánh dấu xung đột

**(3) Phân tích phương án**
- Liệt kê ≥2 phương án xử lý (nếu có)
- Mỗi phương án: căn cứ pháp lý (trỏ về # trong SOT) + ưu/nhược + rủi ro
- Nếu ≥2 phương án: so sánh đánh giá:
  - Pháp lý (1–5): Căn cứ chắc chắn đến đâu?
  - Rủi ro (1–5): Khả năng bất lợi?
  - Khả thi (1–5): Thực hiện được không?

**(4) Khuyến nghị đường lối + Lộ trình**
- Phương án được khuyến nghị + lý do
- Lộ trình bước tiếp cụ thể (hồ sơ cần chuẩn bị, cơ quan thụ lý, thời hạn)
- Các mốc quan trọng cần lưu ý

**(5) Cảnh báo & Bước tiếp theo**
- Rủi ro pháp lý cần lưu ý
- Trường hợp cần ý kiến luật sư/chuyên gia
- Nguồn ngoài web đánh dấu `[Web]`
- **Disclaimer**: "Nội dung tư vấn mang tính tham khảo, không thay thế ý kiến pháp lý chính thức."

---

## 5. Quality Gate — 12 điểm

Trước khi xuất đầu ra, kiểm tra:

1. ✅ Đã tạo thư mục `legal_research_...` và file `legal_phase_X.md` chưa?
2. ✅ 5 trục đã xác định đầy đủ (đặc biệt THỜI ĐIỂM)?
3. ✅ File `legal_phase_X.md` đã có Baseline, Target, Exit Condition ở đầu chưa?
4. ✅ SOT có ≥3 trích dẫn nguyên văn?
5. ✅ Mỗi trích dẫn có tọa độ đầy đủ (VB–Số hiệu–Điều–Khoản–Điểm)?
6. ✅ Trạng thái hiệu lực đúng với mốc thời điểm user?
7. ✅ VB sửa đổi đã cross-reference đủ 3 chiều?
8. ✅ File phase đã lưu vết IPO cho mỗi vòng PDCA?
9. ✅ Đã tổng kết Truth/Actionable/Gap ở cuối file Phase chưa?
10. ✅ Đã tạo file `legal_report_[chủ_đề].md` với cấu trúc 5 phần chưa?
11. ✅ Phương án xử lý đã đánh giá so sánh trong Report chưa?
12. ✅ Khung chat chỉ chứa tóm tắt và link trỏ đến file Report?

---

## 6. Khung Pháp luật VN (Tham chiếu nhanh)

Load `resources/legal-system.md` khi cần tra cứu chi tiết. Tóm tắt:

### Thứ bậc VBQPPL (Luật Ban hành VBQPPL 2025)

```
① Hiến pháp
② Bộ luật / Luật / Nghị quyết (Quốc hội)
③ Pháp lệnh / Nghị quyết (UBTVQH); NQ liên tịch UBTVQH-MTTQ
④ Lệnh / Quyết định (Chủ tịch nước)
⑤ Nghị định / Nghị quyết (Chính phủ); NQ liên tịch CP-MTTQ
⑥ Quyết định (Thủ tướng)
⑦ Nghị quyết (Hội đồng Thẩm phán TANDTC)
⑧ Thông tư (Bộ trưởng, Chánh án TANDTC, Viện trưởng VKSNDTC, TKTNN)
⑨ Thông tư liên tịch
⑩–⑮ Văn bản địa phương (HĐND/UBND tỉnh → huyện → xã)
```

### Xung đột

| Quy tắc | Áp dụng khi |
|---|---|
| **Lex superior** | VB cấp cao > VB cấp thấp |
| **Lex posterior** | VB mới > VB cũ (cùng cấp) |
| **Lex specialis** | VB chuyên ngành > VB chung (cùng cấp, cùng thời điểm) |

---

## 7. Danh mục Module Lĩnh vực & Keyword (SOT Baseline 07/2026)

Trước khi tra cứu, Agent phải rà soát xem yêu cầu thuộc nhóm nào dưới đây, sau đó đọc (view_file) trực tiếp vào file module tương ứng trong `resources/domains/` để lấy khung xương sống NĐ/TT.

| Nhóm lĩnh vực | File Module Cần Đọc | Keyword nhận diện |
|---|---|---|
| Dân sự & Gia đình | `resources/domains/01-dan-su.md` | hợp đồng, vay mượn, bồi thường, thừa kế, di chúc, ly hôn, tài sản chung, cấp dưỡng, chia tài sản, án phí. |
| Hình sự & Hành chính | `resources/domains/02-hinh-su-hanh-chinh.md` | tội phạm, khởi tố, án treo, tham nhũng, phạt vi phạm, khiếu nại, tố cáo, giấy phép, phạt giao thông, căn cước. |
| Doanh nghiệp & Lao động | `resources/domains/03-doanh-nghiep-lao-dong.md` | thành lập công ty, cổ đông, vốn, phá sản, đầu tư, sa thải, lương, BHXH, hợp đồng lao động, kỷ luật. |
| Đất đai & Xây dựng | `resources/domains/04-dat-dai-xay-dung.md` | sổ đỏ, đền bù, chuyển nhượng, tiền SDĐ, giá đất, giấy phép xây dựng, chung cư, nhà ở xã hội, dự án BĐS. |
| Thuế & Tài chính | `resources/domains/05-thue-tai-chinh.md` | khai thuế, hoàn thuế, truy thu, TNCN, TNDN, VAT, hóa đơn, đấu thầu, nhà thầu. |
| Chuyên ngành Khác | `resources/domains/06-chuyen-nganh-khac.md` | an ninh mạng, dữ liệu, AI, chữ ký số, nhãn hiệu, bản quyền, ĐTM, ô nhiễm, GPLX, điện lực, năng lượng. |

---

## 8. Bản đồ Resources bổ trợ

| File | Nội dung | Load khi nào |
|---|---|---|
| `resources/legal-system.md` | Thứ bậc, hiệu lực, xung đột, quan hệ VB | §2 (phân loại) + §4 (xung đột SOT) |
| `resources/cross-reference-guide.md` | Tra chéo 3 chiều: xuống-ngang-thời gian | §3 (search & cross-reference) |
| `resources/citation-format.md` | Chuẩn trích dẫn + template SOT | §3 (trích dẫn) + §4 (ghép SOT) |
| `resources/search-sources.md` | Nguồn tin cậy + cú pháp tìm kiếm | §3 (search) |

---

## 9. Nguyên tắc Vận hành

- Mọi kết luận kèm **tọa độ pháp lý** trỏ về SOT
- Thiếu dữ kiện → `[Giả định]` kèm tác động, hoặc hỏi user
- Nguồn tra web → `[Web]` kèm URL
- Ngày tháng: DD/MM/YYYY
- Không tự bịa nội dung VB — phải copy nguyên văn từ nguồn
- Skill hỗ trợ nghiên cứu và tư vấn sơ bộ; **không thay thế ý kiến pháp lý chính thức**
