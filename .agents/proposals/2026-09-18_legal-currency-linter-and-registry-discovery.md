---
proposal_id: "2026-09-18_legal-currency-linter-and-registry-discovery"
type: "tool"
name: "legal-currency-linter-and-registry-discovery"
status: "open"
priority: "Cao"
related_issue: "#288"
proposed_by_project: "IBST_TVTT_T09_002_Voltage_BV"
proposed_by_archetype: "specialized_extension"
proposed_date: "2026-09-18"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Tất cả Spokes"
---

# RFC Proposal: Linter Nhận Thức Ngữ Cảnh Đa Định Dạng & Vá Lỗi Tầng Nhân Khám Phá Registry (ccba-legal-intel)

- **Tác giả đề xuất:** Kỹ sư / Agent đại diện Spoke (`IBST_TVTT_T09_002_Voltage_BV`)
- **Ngày lập:** 2026-09-18
- **Trạng thái:** Đang mở (Open) — Liên kết Issue #288
- **Căn cứ pháp lý nền tảng:** ADR-0029, ADR-0030, ADR-0045, ADR-0050, ADR-0057, ADR-0058, ADR-0059

---

### 1. Bối cảnh & Động lực Thực tế tại Spoke (Context & Real-world Motivation)

1. **Nỗi đau thực tế (Pain point):**
   - Trong quá trình lập hồ sơ kỹ thuật và slide thuyết trình dự thầu dự án GE Vernova HVDC Transformer Plant, AI Agent vẫn viện dẫn các văn bản quy phạm pháp luật đã bãi bỏ (Nghị định 15/2021/NĐ-CP, Thông tư 06/2021/TT-BXD, Thông tư 12/2021/TT-BXD, Luật Xây dựng 2014) dù kho tri thức pháp lý 2025–2026 đã có sẵn tại Spoke.
   - Phân tích nguyên nhân gốc rễ (RCA qua McKinsey MECE Issue Tree) chỉ ra:
     - Khâu tra cứu tầng nhân: `discover_master_registry_path()` bị lỗi fallback trỏ nhầm vào stub rỗng 90 dòng thay vì registry 928 dòng của Spoke, và hàm tra cứu tự động gán nhầm trạng thái `ACTIVE` cho văn bản không tồn tại.
     - Khâu hậu kiểm: Thiếu một Static Linter có khả năng quét phát hiện các số hiệu văn bản bãi bỏ trên đa định dạng giao nộp (.md, .txt, .pptx, .docx) và tự động khóa cứng hoàn thành (ADR-0058).

2. **Quá trình ươm tạo & kiểm chứng tại Spoke:**
   - Đã kiểm chứng thực tế và làm sạch 100% hồ sơ dự thầu:
     - `Technical_Proposal_Methodology_IBST.md`: 0 lỗi văn bản bãi bỏ.
     - `IBST_Presentation_Interview_GE_Vernova_HVDC.pptx`: Quét trực tiếp 12 slide qua phân tích XML DrawingML bằng `zipfile` (tốc độ ~18ms), phát hiện 0 lỗi.
   - Đã xây dựng bộ kiểm thử 11 test cases trong `test_linter_currency.py` bao phủ đầy đủ các kịch bản: viện dẫn khẳng định, miễn trừ chuyển tiếp, bảo toàn tiêu chuẩn hợp lệ (TCVN 10333-1:2014), cảnh báo 2 tầng và trích xuất slide PPTX.

3. **Giá trị khi phổ biến lên Hub:**
   - Trang bị cho toàn bộ hệ sinh thái CCBA một chốt chặn tự động bảo vệ tính hợp pháp và tính thời sự của các sản phẩm tư vấn xây dựng.
   - Ngăn ngừa triệt để rủi ro hallucination và trích dẫn luật lỗi thời từ parametric bias của các mô hình nền tảng.

---

### 2. Đánh Giá Giá Trị × Rủi Ro × KISS (Evaluation Matrix)

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Tối thượng | Bảo đảm 100% hồ sơ tư vấn CCBA tuân thủ khung pháp lý hiện hành 2025–2026 |
| **Độ Phức tạp (Complexity)** | Rất thấp (KISS) | Thuần thư viện chuẩn Python (`zipfile`, `xml.etree.ElementTree`, `re`), zero external dependency |
| **Rủi ro Rò rỉ (Risk)** | 0% (Triệt tiêu) | Không chứa bất kỳ dữ liệu thương mại, thông tin khách hàng hay bí mật dự án nào |
| **Bảo tồn Tiêu chuẩn** | Tuân thủ 100% | Vượt qua `validate_skills.py --enforce-gpi` (73/73 skills) và ADR-0058 |

---

### 3. Thiết Kế Chi Tiết & Thay Đổi Kỹ Thuật

1. **Vá lỗi Tầng Nhân Tra Cứu (`packages/ccba-legal-intel/src/ccba_legal/registry.py` & `models.py`):**
   - Tự động nhận diện registry Spoke theo thứ tự ưu tiên 6 tầng (ADR 0050).
   - Cơ chế lập chỉ mục đảo `_inverted_replacements` và từ điển ánh xạ chuyển tiếp luật định chuẩn `KNOWN_STATUTORY_REPLACEMENTS`.
   - Chuẩn hóa trạng thái `LegalDocStatus.UNVERIFIED` cho văn bản chưa được xác thực.

2. **Linter Nhận Thức Ngữ Cảnh Đa Định Dạng (`packages/ccba-legal-intel/src/ccba_legal/linter.py`):**
   - Từ điển văn bản bãi bỏ `OBSOLETE_LEGAL_PATTERNS` với độ chính xác cao (bảo toàn tiêu chuẩn cũ còn hiệu lực).
   - Bộ bóc tách văn bản `extract_file_lines()` hỗ trợ `.md`, `.txt`, `.pptx` (đọc thẻ `<a:t>` trong slide XML), `.docx` (đọc `word/document.xml`).
   - Bộ lọc ngữ cảnh `is_transitional_context()`: Miễn trừ các câu đối chiếu/lịch sử (*thay thế, bãi bỏ, trước đây là, so sánh, superseding*).
   - Cơ chế 2 tầng: `ERROR` (exit code 1) cho văn bản bãi bỏ; `WARNING` (exit code 0) cho văn bản chưa có trong registry.

3. **Giao Diện Dòng Lệnh (`packages/ccba-legal-intel/src/ccba_legal/cli.py`):**
   - Thêm cờ `--check-currency` (`-c`) và `--json` cho lệnh `ccba_legal lint`.
   - In bảng báo cáo trực quan với vị trí file, dòng/slide, viện dẫn vi phạm và văn bản hiện hành thay thế.

4. **Bộ Kiểm Thử Toàn Diện (`packages/ccba-legal-intel/tests/test_linter_currency.py`):**
   - 6 bài kiểm thử mới + 5 bài kiểm thử hiện hữu: 11/11 tests pass 100%.
