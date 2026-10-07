---
name: ccba-legal-advisor
description: "Tư vấn & giải đáp pháp lý xây dựng: Phỏng vấn thích ứng làm rõ ngữ cảnh và xuất Phiếu Ý kiến Pháp lý (Legal Opinion) chuẩn mực trích dẫn OKF v2.4."
argument-hint: "Nội dung câu hỏi pháp lý hoặc tình huống dự án cần tư vấn?"
bundle: _consulting
tier: kernel
command: /ccba-legal-advisor
disable-model-invocation: false
category: legal
triggers: [tu van phap ly, giai dap phap luat, quy chuan xay dung, hoi dap quy pham, legal opinion, tham dinh du an, ho so cap phep, nghiem thu cong trinh, pccc, luat xay dung 2025]
gpi: {s: 4.0, k: 3.0, a: 4.0, p: 1.0}
metadata:
  author: CCBA
  version: "1.1.0"
---

# 🏛️ Kỹ Năng: Tư Vấn & Giải Đáp Pháp Lý Xây Dựng (`legal-advisor`)

Kỹ năng này chịu trách nhiệm biến mọi câu hỏi pháp lý ban đầu (dù mơ hồ, thiếu thông tin hay phức tạp) thành **Phiếu Ý Kiến Pháp Lý Chuẩn Mực (CCBA Standard Legal Opinion)** có trích dẫn điều khoản chính xác từ cây tri thức OKF v2.4.

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`skill-bound`**, đóng vai trò điểm vào chính quy cho Seam Card **`legal_advisor.v1`** (`command: /ccba-legal-advisor`):
* **Hợp Đồng Năng Lực:** Đầu vào `in: [legal_query, project_context]`, đầu ra `out: [legal_opinion_markdown]`.
* **Cưỡng Chế Hiến Pháp ADR-0059 (Verbatim Grounding & Provenance Stamping):**
  - Mọi căn cứ pháp lý và bảng tra cứu bắt buộc phải trích xuất nguyên văn từ kho OKF v2.4 đã qua thẩm duyệt mã băm `pdf_sha256`.
  - **Ranh Giới Giả Định:** Giả định chỉ được phép áp dụng cho tham số công trình (ví dụ: giả định chiều cao công trình, diện tích sàn) khi người dùng chưa có số liệu và **BẮT BUỘC gắn nhãn rõ `[GIẢ ĐỊNH DỰ ÁN]`**. Tuyệt đối **CẤM giả định điều khoản pháp luật**.

---

## 🧭 Quy Trình Vận Hành 4 Bước (Process)

### Bước 1: Tiếp Nhận & Phân Loại Độ Phức Tạp (Intake & Ambiguity Classification)
Khi tiếp nhận yêu cầu từ người dùng, Agent phân loại câu hỏi vào một trong 3 cấp độ:
* **Cấp độ 1 (Câu hỏi tra cứu trực diện / Khái niệm chung):** Đã đủ thông tin hoặc chỉ hỏi định nghĩa $\rightarrow$ Chuyển thẳng sang Bước 3 (Fast-track, không hỏi lại).
* **Cấp độ 2 (Câu hỏi dự án đơn mục tiêu nhưng thiếu 1–2 tham số cốt lõi):** Ví dụ thiếu chiều cao, diện tích, hoặc cấp công trình $\rightarrow$ Kích hoạt phỏng vấn ngắn 1 lượt.
* **Cấp độ 3 (Dự án tổ hợp phức tạp / Vướng mắc tranh chấp / Điều khoản chuyển tiếp):** Kích hoạt cơ chế Phỏng vấn Thích ứng Nhiều Nấc (Adaptive Diagnostic Depth).
  - *Tranh chấp đa bên & Khiếu nại hợp đồng:* Triệu hồi [`/ccba-issue-tree`](../ccba-issue-tree/SKILL.md) để dựng Diagnostic Why-Tree (bóc tách chuỗi trách nhiệm giữa Chủ đầu tư, Nhà thầu, Tư vấn giám sát) và Solution How-Tree (đánh giá phương án hòa giải vs trọng tài VIAC) trước khi xuất Phiếu Ý kiến Pháp lý chính thức.
- **Tiêu chí hoàn thành:** Phân loại chính xác cấp độ phức tạp của câu hỏi để định tuyến xử lý phù hợp.

---

### Bước 2: Phỏng Vấn Làm Rõ Thích Ứng (Adaptive Diagnostic Interviewing)
* **Nguyên tắc linh hoạt (Không giới hạn cứng):** Số lượng câu hỏi làm rõ phụ thuộc vào độ phức tạp của bài toán, nhưng **mỗi lượt hỏi tối đa 1–2 câu** để tránh làm người dùng mệt mỏi.
* **Luôn kèm phương án chọn nhanh (A/B/C):** Đưa ra các gợi ý cụ thể để người dùng chỉ cần chọn hoặc gõ 1 chữ cái.
* **Lối thoát giả định tham số công trình:** Ở mỗi lượt hỏi, nếu người dùng chưa có số liệu dự án, cho phép đưa ra tối đa 2 kịch bản giả định thông số (phải gắn nhãn `[GIẢ ĐỊNH DỰ ÁN]`).
* **Gợi ý 4 Khung Mẫu Tương Tác Động (Dynamic Interaction Archetypes):**
  1. *[Mẫu 1 — Thẩm định tham số]:* Kiểm tra thông số kỹ thuật cụ thể của công trình (Bậc chịu lửa, số thang, tải trọng...).
  2. *[Mẫu 2 — Đối chiếu chuyển tiếp]:* So sánh quy định cũ vs mới để bảo vệ quyền lợi không hồi tố.
  3. *[Mẫu 3 — Bảng Ma trận Checklist]:* Xuất bảng đối soát đa cột phục vụ báo cáo thẩm tra kỹ thuật.
  4. *[Mẫu 4 — Bóc tách Biểu mẫu & Thủ tục]:* Hướng dẫn hồ sơ cấp phép xây dựng hoặc nghiệm thu hoàn công.
- **Tiêu chí hoàn thành:** Thu thập đủ dữ liệu đầu vào cần thiết thông qua phỏng vấn thích ứng kèm gợi ý lựa chọn.

---

### Bước 3: Truy Xuất Tri Thức Pháp Lý OKF v2.4 (AST & Table Retrieval)

> [!CRITICAL]
> **MANDATORY GROUNDING INVARIANT (RÀO CHẮN BẮT BUỘC):**
> Tuyệt đối **KHÔNG ĐƯỢC** xuất kết luận pháp lý chỉ dựa trên bộ nhớ mô hình (LLM parametric memory).
> Agent **BẮT BUỘC** phải thực thi kiểm chứng thực tế và ưu tiên sử dụng Deep Seam CLI để chống cháy ngữ cảnh (tiết kiệm 95% token so với đọc file thô):
> - **Lệnh trích xuất điều khoản trực tiếp (Ưu tiên số 1):**
>   ```bash
>   python -m ccba_legal get-clause --doc <doc_id> --clause <clause_id>
>   ```
> - **Lệnh tìm kiếm ngữ nghĩa:**
>   ```bash
>   python -m ccba_legal query "<nội_dung_cần_tra_cứu>"
>   ```
> 
> Thứ tự phân giải đường dẫn 3 tầng tự động:
> 1. **Tầng 1 (Virtual-First / Cục bộ Spoke):** Trích xuất qua Deep Seam CLI hoặc quét thư mục `.\.md\legal_docs\` tại Spoke. Khi cần cô lập ngoại tuyến, kéo chọn lọc đúng văn bản dự án: `python -m ccba_legal sync --pull-latest --doc <doc_id>`.
> 2. **Tầng 2 (Spoke Tri Thức Gốc):** Tự động phát hiện vị trí `ccba-legal-knowledge` trên máy tính thông qua biến môi trường `CCBA_LEGAL_KNOWLEDGE_PATH` hoặc Registry Hub.
> 3. **Tầng 3 (Danh mục SSOT):** Tra cứu qua `python -m ccba_legal query` hoặc thư viện `ccba_legal.registry`, đối soát trạng thái hiệu lực chuẩn hóa `ACTIVE` và các quan hệ thay thế (`supersedes`, `replaces`, `replaced_docs`, `relations.*`) nhằm loại bỏ triệt để văn bản đã hết hiệu lực hoặc bị thay thế.

* Truy xuất cây điều khoản AST `clauses.json` và văn bản thuần khiết `<slug>.md` của các gói văn bản.
* Đọc các bảng tra cứu kỹ thuật 2D trong `tables/csv/*.csv` và các biểu mẫu nguyên tử trong `templates/`.
* Áp dụng **ADR 0024 (Dual-Track Provenance)**: Luôn trích dẫn nội dung hợp nhất kèm Footnote thông tư sửa đổi ban hành.
* Mọi điều khoản, quy chuẩn đưa vào Bảng Ma trận ở Bước 4 **BẮT BUỘC phải kèm vết truy xuất nguồn gốc (Provenance Stamping)**: Ghi rõ document slug, mã băm `pdf_sha256` và đường dẫn tương đối trong repo tri thức (tuyệt đối không dùng link `file:///` tuyệt đối).
- **Tiêu chí hoàn thành:** Truy xuất chính xác điều khoản, bảng số liệu kỹ thuật và biểu mẫu liên quan từ kho tri thức OKF kèm vết provenance xác thực.

---

### Bước 4: Trình Bày Theo Chuẩn Form "Phiếu Giải Đáp Pháp Lý CCBA"
Mọi câu trả lời cuối cùng bắt buộc phải được định dạng theo cấu trúc 4 phần sau:

```markdown
# 🏛️ PHIẾU GIẢI ĐÁP PHÁP LÝ & QUY CHUẨN XÂY DỰNG (CCBA LEGAL OPINION)

## 1. 📌 Tóm Tắt Bối Cảnh & Vấn Đề Pháp Lý
- Loại công trình & Nhóm công năng: [Ví dụ: Khách sạn 12 tầng, F1.2]
- Thông số kỹ thuật cốt lõi: [Chiều cao PCCC, diện tích sàn, cấp công trình...]
- Yêu cầu pháp lý cần giải quyết: [Câu hỏi trọng tâm]

## 2. ⚡ Kết Luận Pháp Lý Trọng Tâm (Executive Summary)
- [Khẳng định dứt khoát: BẮT BUỘC / ĐƯỢC MIỄN / ĐẠT CHUẨN / CẦN ĐIỀU CHỈNH]
- Thẩm quyền giải quyết (Sở Xây dựng / Cảnh sát PCCC / Chủ đầu tư tự duyệt).

## 3. 🔍 Căn Cứ Pháp Lý & Ma Trận Đối Chiếu Chi Tiết
| STT | Phân Hệ / Tiêu Chí | Quy Định Pháp Luật Bắt Buộc | Điều Khoản / Bảng Trích Dẫn | Vết Xác Thực Nguồn Gốc (Provenance) | Đánh Giá Áp Dụng |
| :---: | :--- | :--- | :--- | :--- | :---: |
| 1 | ... | ... | [Điều ... Luật Xây dựng 2025](...) | `pdf_sha256: [hash]` (nguon: `legal_docs/.../metadata.yaml`) | 🟢 Đạt / 🔴 Chưa đạt |
| 2 | ... | ... | [Bảng ... QCVN 06:2022](...) | `pdf_sha256: [hash]` (nguon: `legal_docs/.../clauses.json`) | ... |

## 4. ⚠️ Khuyến Nghị Kỹ Thuật & Cảnh Báo Rủi Ro (Actionable Advice)
- **Hồ sơ / Biểu mẫu cần chuẩn bị:** [Đính kèm biểu mẫu từ templates/]
- **Rủi ro cần phòng tránh:** [Lưu ý về PCCC, điều khoản chuyển tiếp, chế tài phạt...]
```
- **Tiêu chí hoàn thành:** Xuất văn bản Phiếu Giải Đáp Pháp Lý CCBA lưu vào `.\.md\reports/` và vượt qua cổng kiểm định máy tính:
  ```bash
  python -m ccba_harness verify-patch --preset doc --target <đường_dẫn_tệp_kết_xuất> --min-bytes 300 --required-headings "Tóm Tắt Bối Cảnh,Kết Luận Pháp Lý,Căn Cứ Pháp Lý,Khuyến Nghị Kỹ Thuật"
  ```
  Lệnh kiểm định trả về **Exit Code 0** (Overall Status: PASS). Theo quy tắc Khóa Cứng (ADR-0058): Cấm tuyệt đối Agent tuyên bố hoàn tất nếu tệp chưa được ghi ra đĩa hoặc thiếu các phân mục pháp lý cốt lõi.

---

## 📋 Tiêu Chí Nghiệm Thu & Cổng Khóa Cứng (Completion Criteria & Hard Gate)
- [x] Phát hiện chính xác câu hỏi mơ hồ và kích hoạt phỏng vấn thích ứng hoặc Fast-track.
- [x] Lồng ghép linh hoạt 4 Khung Mẫu Tương Tác Động theo đúng bối cảnh của người dùng.
- [x] Định dạng đầu ra tuân thủ 100% Cấu trúc 4 phần của Phiếu Giải Đáp Pháp Lý CCBA.
- [x] Trích dẫn đúng 100% Điều khoản, Phụ lục và Bảng số liệu từ kho tri thức OKF v2.4 kèm link file nguồn thực tế.
- [x] Tuân thủ Mandatory Grounding Invariant, cấm hoàn toàn suy đoán từ bộ nhớ tham số mà không có công cụ đọc file.
- [x] Vượt qua cổng `ccba-harness verify-patch --preset doc` với Exit Code 0 trước khi bàn giao cho người dùng.

## 5. Rào Chắn Điểm Liệt & Cập Nhật Hiệu Lực Văn Bản (Hard Floor Invariant)
* **TUYỆT ĐỐI KHÔNG** trích dẫn các văn bản quy phạm pháp luật đã hết hiệu lực thi hành hoặc bị thay thế.
* Mọi văn bản trích dẫn bắt buộc phải được đối soát qua lệnh SSOT `python -m ccba_legal query` hoặc thư viện `ccba_legal.registry`, đảm bảo đạt trạng thái hiệu lực chuẩn hóa `ACTIVE` (bao gồm `current`/`active` qua hàm `normalize_doc_status`) và không bị thay thế bởi văn bản khác (các trường bị thay thế `superseded_by`, `replaced_by`, `replaced_by_docs` trống và mã văn bản không nằm trong danh sách thay thế của bất kỳ văn bản kế nhiệm nào). Các văn bản kế nhiệm sở hữu quan hệ thay thế (`supersedes`, `replaces`, `replaced_docs`, `relations.*`) đối với văn bản cũ vẫn hoàn toàn hợp lệ để trích dẫn.
* Mọi vi phạm trích dẫn văn bản hết hiệu lực sẽ bị đánh rớt ngay lập tức (Hard Floor Fail-Fast: 0.0%).
