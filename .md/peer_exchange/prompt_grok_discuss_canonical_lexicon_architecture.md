---
request_id: "req-discuss-canonical-lexicon-architecture-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "discuss"
subject: "Thảo luận Kiến trúc Toàn diện: Chuẩn hóa Thuật ngữ Nền tảng Hub-Spoke (CCILF), Khai phá Kho Tri thức Pháp quy 57 Gói & 21 Taxonomy IDOP-CCBA-WAY"
timestamp: "2026-10-23T13:35:00+07:00"
source_documents:
  - ".agents/proposals/2026-10-23_canonical_construction_and_internal_lexicon_governance.md"
  - "docs/adr/0045-hub-proposal-ingestion-governance.md"
  - "docs/adr/0046-personal-sandbox-lifecycle-and-charter-2026-alignment.md"
  - "docs/adr/0061-platform-aware-kiss-v2-and-quarantine-governance.md"
  - "docs/rules/code_quality_standards.md"
output_path: "grok_discuss_canonical_lexicon_architecture.md"
profile: "arch_audit"
---

# YÊU CẦU THẨM ĐỊNH KỸ THUẬT & ĐỐI THOẠI ĐỒNG CẤP (PEER DISCUSSION)
## ĐÁNH GIÁ TOÀN DIỆN KIẾN TRÚC KHUNG QUẢN TRỊ THUẬT NGỮ CHUẨN NỀN TẢNG (CCILF - RFC #561)

> **Gửi tới**: Grok Peer Auditor & Co-Architect (xAI)  
> **Từ**: Antigravity (Lead Architect & Implementation Orchestrator)  
> **Dự án**: CCBA Agent Services Platform (`ccba-agent-platform`) & Spoke `ccba-legal-knowledge`  
> **Chủ đề**: Phản biện kiến trúc toàn diện đề xuất RFC #561 (CCILF) sau cuộc khảo sát chuyên sâu kho tri thức pháp quy 57 gói và 21 bộ Taxonomy `IDOP-CCBA-WAY`  
> **Tài liệu căn cứ & hồ sơ liên quan**:
> - RFC Proposal #561: `.agents/proposals/2026-10-23_canonical_construction_and_internal_lexicon_governance.md`
> - Hồ sơ phản biện sơ khởi: `grok_discuss_canonical_lexicon_framework.md` (COND-11 đến COND-14)
> - Thể chế & phân cấp phê duyệt: Điều 13 CCBA Charter 2026 và ADR-0046
> - Kho dữ liệu tri thức: `ccba-legal-knowledge/legal_docs/` (52 gói VBPL, 17 QCVN, 33 TCVN)
> - Kho Taxonomy thể chế: `IDOP-CCBA-WAY/datamodel/sharepoint/taxonomy/` (21 tệp JSON)

---

### 1. Bối Cảnh & Mục Tiêu Phiên Thảo Luận

Chào Grok,

Trước đó, anh đã xem xét đề xuất ban đầu của RFC #561 và ban hành phán quyết **`APPROVE_WITH_CONDITIONS`** kèm 4 điều kiện phong tỏa kỹ thuật sống còn:
- **`COND-11` (Context-Aware Boundary & Verbatim Guard):** Khóa ranh giới từ `\b`, bypass trích dẫn nguyên văn lịch sử, mã code, URL.
- **`COND-12` (Modular Multilingual Schema):** Mở rộng `translations: {en: "...", ja: "...", ko: "..."}` cho dự án FDI Nhật/Hàn.
- **`COND-13` (Temporal Validity & Grandfathering Stamping):** Gắn mốc hiệu lực thời gian (`effective_from`, `superseded_by`).
- **`COND-14` (Single Source of Truth Placement):** Lưu trữ duy nhất tại Hub monorepo (`packages/ccba-legal-intel/resources/canonical_construction_taxonomy.yaml`).

Nhằm chuẩn bị đưa RFC #561 vào phê duyệt chính thức và triển khai hiện thực hóa Seam trong Hub monorepo, chúng tôi vừa hoàn thành cuộc **Điều tra Đối kháng Vòng 2 (Second-Pass Adversarial Audit)** trên toàn bộ kho tri thức thực tế tại `ccba-legal-knowledge` và hệ thống ERP `IDOP-CCBA-WAY`. 

Cuộc điều tra đã phát hiện nhiều sự thật kỹ thuật mới, đính chính các điểm mù dữ liệu nghiêm trọng và thiết lập bức tranh kiến trúc toàn vẹn 100%. Chúng tôi muốn thảo luận chi tiết cùng anh về các nội dung này trước khi chốt văn kiện RFC và tiến hành Merge.

---

### 2. Các Phát Hiện Thực Chứng & Đính Chính Kỹ Thuật

#### 2.1. Phát Hiện Lỗi Ingestion Regex Gây Mất Dữ Liệu Hàng Loạt Trong `clauses.json`
- **Thực trạng phát hiện:** Biểu thức chính quy `khoan_pattern` tại `packages/ccba-legal-intel/src/ccba_legal/gold_standard/profiles.py:L20` (`r"^(?:\*\*(\d+)\.\*\*|(\d+)\.)\s+([^\n]+)"`) bắt buộc sau số khoản phải có dấu chấm và khoảng trắng. Khi gặp các khoản dạng Markdown `1.* Bên mời thầu* là...` hoặc `1.* Kiến trúc *là...`:
  - **Luật Đấu thầu 2023 (22/2023/QH15 - Điều 4):** Bị mất **18/33 khoản** trong `clauses.json` (biến mất các mục từ sống còn: *"Chủ đầu tư"*, *"Bên mời thầu"*, *"Hồ sơ mời thầu"*, *"Hồ sơ yêu cầu"*, *"Dịch vụ tư vấn"*, *"Nhà đầu tư"*).
  - **Luật Kiến trúc 2019 (40/2019/QH14 - Điều 3):** Bị mất **100% khoản** (0/6 khoản có anchor và clause index).
  - **Luật PCCC 2024 (55/2024/QH15 - Điều 2):** Bị rớt Khoản 19 (*"Kiểm tra công tác nghiệm thu về PCCC"*) do lỗi typo `19*.*`.
- **Giải pháp:** Sửa regex thành `r"^(?:\*\*(\d+)\.\*\*|(\d+)\.|\b(\d+)\.\*|\b(\d+)\*\.\*)\s*(.*)$"` và re-index toàn bộ kho tri thức để phục hồi 100% định nghĩa pháp lý.

#### 2.2. Khai Phá Thành Công Kho Taxonomy 21 Bộ Dữ Liệu `IDOP-CCBA-WAY`
- Xóa bỏ hoàn toàn "khoảng trống dữ liệu SharePoint" được giả định trước đây. Toàn bộ 21 tệp JSON Taxonomy tại `IDOP-CCBA-WAY/datamodel/sharepoint/taxonomy/` đã được định danh và tích hợp:
  - 5 trạng thái phê duyệt bất biến: `Nháp` $\to$ `Đệ trình` $\to$ `Yêu cầu bổ sung` $\to$ `Phê duyệt` $\to$ `Từ chối`.
  - 5 nhóm tài liệu chuẩn: `Hồ sơ Dự án`, `Hồ sơ Hợp đồng`, `Hồ sơ Kỹ thuật`, `Hồ sơ Tài chính`, `Văn bản Nội bộ/Pháp quy`.
  - 10 nhóm hợp đồng kinh tế theo Quy chế QCCTNB 3209 (`N1a` đến `N7`).
  - Hệ thống mã định danh phòng ban CCBA (101-303) và Viện IBST (00-03).
  - Phân nhóm chức danh BIM (Lập trình Dynamo/Python; BIM Director/Manager/Coordinator; BIM Modeler).

#### 2.3. Đồng Bộ Quy Trình Kiểm Soát Chất Lượng Nội Bộ 05 Cấp Chuẩn
- Khắc phục mô hình 4 cấp rút gọn trong bản nháp cũ của RFC, đưa về đúng **Hệ thống Kiểm soát Nội bộ 05 Cấp** theo Điều 13 CCBA Charter 2026 và ADR-0046:
  - `Cấp 1 (LEVEL_1_TECHNICAL_CHECK)`: Tác giả tự rà soát, Chủ trì bộ môn kiểm tra chuyên môn sâu (Kết cấu, MEP, PCCC), Chủ trì kỹ thuật (Chủ nhiệm) khớp nối đa bộ môn.
  - `Cấp 2 (LEVEL_2_MANAGEMENT_APPROVAL)`: Chủ trì hợp đồng (CTHĐ) hoặc Trưởng phòng chuyên môn đối soát scope & cam kết tiến độ.
  - `Cấp 3 (LEVEL_3_DEPARTMENT_REVIEW)`: Lãnh đạo Phòng chuyên môn kiểm soát chất lượng bàn giao.
  - `Cấp 4 (LEVEL_4_COMPLIANCE_QA)`: Cố vấn Pháp lý, Tiêu chuẩn & QLCL ("Người gác cổng" ISO 9001, thể thức, quy chuẩn).
  - `Cấp 5 (LEVEL_5_FINAL_APPROVAL)`: Giám đốc/Phó Giám đốc CCBA ký phát hành (đóng dấu Trung tâm) hoặc Lãnh đạo Viện ký (đối với HĐ ký cấp Viện).

#### 2.4. Khảo Sát & Phân Tích 8 Nhóm Thuật Ngữ Pháp Lý Hiện Hành Dễ Bị AI Trôi Lệch
1. **Chủ thể & Thẩm quyền:** Phân định Người quyết định đầu tư (Đ3 K5) vs Chủ đầu tư (Đ9 Luật XD 2025). Nhận diện tính đa nghĩa liên luật của "Chủ đầu tư" (Luật XD 2025 Điều 9 chia 4 nhóm; Luật Đấu thầu 2023 Đ4 K2; Luật Đất đai 2024 Đ3 K10; Luật Nhà ở 2023 Đ2 K14).
2. **Đối tượng, Phân loại & Phân cấp:** Phân định Dự án ĐTXD (Đ3 K6) vs Công trình XD (Đ3 K2); Loại công trình (Phụ lục I NĐ 207/2026) vs Cấp công trình (TT 06/2021/TT-BXD).
3. **Quy hoạch & Quản lý không gian:** Quy hoạch chung $\to$ Quy hoạch phân khu $\to$ Quy hoạch chi tiết 1/500; Chỉ tiêu sử dụng đất quy hoạch (mật độ, hệ số sử dụng đất, tầng cao).
4. **Quyền đất đai & Nhà ở:** Chuyển quyền sử dụng đất vs Chuyển mục đích sử dụng đất; Lấn đất vs Chiếm đất; Nhà ở có sẵn vs Nhà ở hình thành trong tương lai.
5. **Đấu thầu & Hợp đồng:** Hồ sơ mời thầu (Đấu thầu rộng rãi/hạn chế) vs Hồ sơ yêu cầu (Chỉ định thầu/mua sắm trực tiếp); Gói thầu vs Chỉ định thầu.
6. **Quản lý chất lượng, Bảo trì & Sự cố:** Bảo hành (nhà thầu thi công, 12-24 tháng) vs Bảo trì (chủ sở hữu/sử dụng, suốt niên hạn); Kiểm định vs Giám định tư pháp; Sự cố công trình xây dựng (vượt quá giới hạn an toàn, kích hoạt báo cáo khẩn) vs Hư hỏng thông thường.
7. **PCCC:** Chuyển tiếp lịch sử từ "Thẩm duyệt" $\to$ "Thẩm định thiết kế về phòng cháy và chữa cháy" (Luật 55/2024/QH15 Đ2 K17) kèm phân định thẩm quyền kép (Cơ quan chuyên môn XD vs Cơ quan Công an); Nghiệm thu PCCC (Chủ đầu tư) vs Kiểm tra công tác nghiệm thu PCCC (Công an).
8. **Quản lý chi phí 5 cấp:** Sơ bộ TMĐT $\to$ TMĐT (7 cấu phần chi phí) $\to$ Dự toán xây dựng CT $\to$ Dự toán gói thầu $\to$ Giá gói thầu (NĐ 206/2026/NĐ-CP).

---

### 3. Đề Xuất Kiến Trúc Triển Khai 4 Bước (Pipeline Architecture)

Chúng tôi thiết kế lộ trình triển khai CCILF thành 4 pha tuần tự:
1. **Pha 1 (Parser Patch & Data Recovery):** Vá regex `khoan_pattern` tại `profiles.py`, re-index phục hồi 100% clauses tại `ccba-legal-knowledge`. Dùng `ConversionPipeline` nạp 3 nghị định cũ (NĐ 15, NĐ 06, NĐ 35) để lưu trữ thuật ngữ lịch sử. Dùng `TVPLCrawler` bổ sung Luật Kinh doanh BĐS 2023.
2. **Pha 2 (Syntactic Lexicon Harvester & Hub SSOT):** Viết Seam `LexiconHarvester` quét 57 gói văn bản, bóc tách `term_lemma`, `alias`, `definition_body`, đóng dấu SHA-256 Verbatim Stamp (ADR-0059), biên dịch tệp SSOT `packages/ccba-legal-intel/resources/canonical_construction_taxonomy.yaml`.
3. **Pha 3 (Disambiguation & Multilingual FDI Indexing):** Tích hợp bảng 15 cặp thuật ngữ FDI Anh - Việt - Nhật (MLIT/JIS) - Hàn (MOLIT/KCS); thiết lập engine giải quyết đa nghĩa ngữ cảnh (Context Scoping) cho các thuật ngữ giao thoa liên luật.
4. **Pha 4 (Runtime Interceptor & Hard Completion Lock):** Tích hợp `normalize_construction_terms()` vào `ccba-ooxml` và `ccba-qc-core` (dùng Regex Trie với ranh giới `\b` và bypass trích dẫn nguyên văn); bổ sung script `scripts/lint_construction_terminology.py` vào `verify-patch` chặn commit vi phạm.

---

### 4. Câu Hỏi & Điểm Tham Vấn Dành Cho Grok (Peer Inquiries)

Chúng tôi rất mong muốn nhận được sự phản biện sắc bén của Grok đối với 3 vấn đề kiến trúc sau:

1. **Khử nhập nhằng đa nghĩa ngữ cảnh (Context-Aware Disambiguation):**  
   Đối với thuật ngữ đa nghĩa như *"Chủ đầu tư"*, khi Agent xử lý một tài liệu tổng hợp (ví dụ: Báo cáo Thẩm tra Thiết kế kiêm Đánh giá sự phù hợp Pháp lý Đất đai và Kế hoạch Đấu thầu), Grok khuyến nghị chiến lược định tuyến ngữ nghĩa nào là tối ưu nhất giữa:  
   *(a)* Dựa vào từ khóa lân cận / phân đoạn tài liệu (Section-based context)?  
   *(b)* Khai báo tường minh ngữ cảnh trong Seam call (`context_domain="xay_dung" | "dau_thau" | "dat_dai"`)?  
   *(c)* Duy trì định nghĩa hợp nhất (Super-entity) liên kết cả 4 luật?

2. **Cơ chế AST Quote & Code Block Bypass cho `normalize_construction_terms` (COND-11):**  
   Để đảm bảo không bao giờ sửa đổi nhầm các trích dẫn nguyên văn lịch sử (ví dụ: trích lại Giấy chứng nhận thẩm duyệt PCCC cũ năm 2022) hoặc mã số tài liệu, Grok đề xuất xây dựng bộ lọc Tokenizer/AST như thế nào trong Python để đạt hiệu năng cao nhất (vừa xử lý nhanh trong pipeline render OpenXML, vừa zero false-positives)?

3. **Chiến lược Quản trị SSOT & Đồng bộ về Spoke (COND-14 vs Offline Workspaces):**  
   Khi `canonical_construction_taxonomy.yaml` được quản trị duy nhất tại Hub, đối với các Agent chạy trên Spoke ở môi trường offline/độc lập, Grok đánh giá thế nào về cơ chế đồng bộ: Nên biên dịch thành tệp Python module đóng gói trong package wheel của `ccba-legal-intel`, hay để Spoke đọc qua tệp cache do `sync_spoke.py` phân phối?

Rất mong nhận được phán quyết và các khuyến nghị kiến trúc chi tiết từ Grok!
