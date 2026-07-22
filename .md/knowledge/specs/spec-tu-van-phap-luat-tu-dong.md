# Spec: Khung Quy Trình Tư Vấn Pháp Lý Tự Động CCBA (CCBA Automated Legal Advisory Engine)

## Problem Statement

Hiện nay, công tác tư vấn và thẩm tra pháp lý trong các dự án đầu tư xây dựng gặp nhiều khó khăn do hệ thống Văn bản Quy phạm Pháp luật (VBQPPL) Việt Nam gồm nhiều tầng nấc (Luật, Nghị định, Thông tư, Quy chuẩn, Tiêu chuẩn) có mối quan hệ sửa đổi, bổ sung, bãi bỏ và chuyển tiếp phức tạp. 

Khi áp dụng trí tuệ nhân tạo (LLM) để tư vấn pháp lý, các rủi ro lớn nhất bao gồm:
1. **Rủi ro ảo giác (Hallucination)**: AI đưa ra căn cứ pháp lý hoặc số hiệu điều khoản không tồn tại.
2. **Thiếu thông tin ngữ cảnh đầu vào**: Người dùng đưa ra câu hỏi chung chung, thiếu các dữ kiện quan trọng về mốc thời gian, cấp công trình hoặc loại hình dự án.
3. **Mâu thuẫn VBPL (Lex Conflict)**: Không nhận diện được xung đột giữa các văn bản pháp luật hoặc giai đoạn chuyển tiếp, dẫn đến tư vấn áp dụng sai văn bản hết hiệu lực.
4. **Thiếu tính minh bạch và lưu vết**: Kết quả tư vấn không trích dẫn nguyên văn có tọa độ chính xác và không đánh giá được mức độ rủi ro pháp lý (Xanh/Vàng/Đỏ).

## Solution

Xây dựng **Hệ thống Khung Quy trình Tư vấn Pháp lý Tự động CCBA (Automated Legal Advisory Engine)** với kiến trúc 4 khối module chính:

1. **Smart Intake Engine**: Tự động bóc tách câu hỏi đầu vào theo 5 trục dữ kiện (*Đối tượng, Hành vi, Tác động, Phạm vi, Thời điểm*). Tự động kích hoạt luồng phỏng vấn định hướng (Guided Interview) để lấp đầy dữ kiện còn thiếu trước khi tra cứu.
2. **Lex Conflict Engine**: Tự động tra cứu và áp dụng bộ 3 nguyên tắc xung đột pháp lý (*Lex Superior*, *Lex Posterior*, *Lex Specialis*) kết hợp kiểm tra Điều khoản Chuyển tiếp theo mốc thời gian. Định lượng điểm số rủi ro pháp lý và gán nhãn cảnh báo trực quan:
   - 🟢 **Nhãn Xanh (Score 80-100 — An toàn)**
   - 🟡 **Nhãn Vàng (Score 50-79 — Tuân thủ có điều kiện / Cần lập Hồ sơ Giải trình)**
   - 🔴 **Nhãn Đỏ (Score < 50 — Rủi ro cao / Khoảng xám / Cần Công văn Hỏi ý kiến)**
3. **Dual-Layer Reporter**: Xuất báo cáo tư vấn hai tầng gồm:
   - *Tầng 1 (Executive Summary)*: Khuyến nghị phương án tối ưu nhất cho quản lý/Chủ đầu tư.
   - *Tầng 2 (Detailed Risk Matrix)*: Ma trận So sánh rủi ro chi tiết kèm trích dẫn SOT nguyên văn có tọa độ `[Loại VB - Số hiệu - Điều - Khoản - Điểm]`.
4. **On-Demand Dispatch Draft**: Mặc định chỉ phát cảnh báo và hướng đi tiếp theo. Tự động sinh file dự thảo Công văn Xin ý kiến Hướng dẫn Cơ quan Nhà nước (`.docx`) chuẩn Nghị định 30/2020/NĐ-CP khi người dùng chọn kích hoạt.

## User Stories

1. As a legal consultant, I want the system to parse my initial question into a 5-axis taxonomy (Subject, Action, Impact, Scope, Time), so that the search boundary is precise.
2. As a project manager, I want the system to prompt me for missing facts if my input question lacks time or scope coordinates, so that I don't get inaccurate legal advice.
3. As a BIM manager, I want all legal answers to contain exact verbatim Source of Truth (SOT) citations with coordinates `[Doc Type - Number - Article - Clause - Point]`, so that I can verify every legal claim instantly.
4. As a compliance auditor, I want the system to evaluate conflict between general Decrees and specialized Circulars using Lex Specialis and Lex Superior rules, so that the correct legal hierarchy is applied.
5. As a project owner, I want the system to automatically inspect transitional provisions based on the project submission date versus legal enactment date, so that legacy rights are properly protected.
6. As an executive, I want a Dual-Layer report containing an Executive Summary for quick decision making and a Detailed Risk Matrix for thorough review, so that I can balance speed and rigor.
7. As a risk officer, I want legal advice outputs to be color-coded with Green, Yellow, and Red risk scores, so that high-risk gray areas are immediately flagged.
8. As a site engineer, I want the system to automatically log all advisory sessions as immutable Markdown and Word files in the project workspace, so that audit trails are preserved.
9. As a legal coordinator facing a Red-flagged gray area, I want an optional Action Button to auto-generate a formal Consultation Dispatch draft (`.docx`) following Decree 30/2020/NĐ-CP, so that I can send it to government agencies without drafting from scratch.
10. As a system administrator, I want the legal advisory engine to automatically sync document status with `legal_registry.yaml` and NotebookLM, so that expired laws are never recommended.

## Implementation Decisions

- **Architecture Pattern**: Pipeline 4 giai đoạn khép kín (Intake ➔ Conflict Resolution ➔ Dual-Layer Output ➔ On-Demand Dispatching) tích hợp vào package `ccba-legal-intel` và skill `legal-document-tracker`.
- **Data Models & Schemas**:
  - `IntakeTaxonomy`: Schema chứa 5 trường dữ kiện (`subject`, `action`, `impact`, `scope`, `time_timestamp`).
  - `SOTCitation`: Model chứa `doc_type`, `doc_number`, `article`, `clause`, `point`, `verbatim_text`, `effective_date`.
  - `RiskAssessmentScore`: Schema định nghĩa `score` (0-100), `risk_label` (`GREEN`, `YELLOW`, `RED`), `conflict_rule_applied`, `transitional_clause_flag`.
- **Lex Conflict Resolution Rules Engine**:
  - Module mã hóa 3 quy tắc xung đột pháp lý chuẩn Việt Nam:
    1. *Lex Superior*: Hiệu lực pháp lý ưu tiên `Hiến pháp` > `Luật` > `Nghị định` > `Thông tư` > `Quyết định UBND`.
    2. *Lex Posterior*: Cùng cấp thẩm quyền, quy định ban hành sau ưu tiên áp dụng so với quy định ban hành trước.
    3. *Lex Specialis*: Quy định chuyên ngành ưu tiên áp dụng so với quy định chung, trừ khi quy định chung cấp trên có chỉ định khác.
- **Output Formats**:
  - Dual-layer Markdown report render trực tiếp trên UI / Artifact.
  - Generative `.docx` dispatcher kế thừa `ccba-ooxml` / `copywriting` tuân thủ thể thức Nghị định 30/2020/NĐ-CP.

## Testing Decisions

- **Seam**: Kiểm thử tích hợp tại tầng Service API của `packages/ccba-legal-intel/ccba_legal/coordinator.py` và `registry.py` — điểm khớp nối cao nhất quản lý luồng tra cứu và xử lý xung đột pháp lý.
- **External Behavior Testing**:
  - Kiểm thử bóc tách đúng 5 trục từ câu hỏi mẫu.
  - Kiểm thử xử lý xung đột: Đưa ra 2 VBQPPL mâu thuẫn (Nghị định cũ vs Thông tư mới), xác minh hệ thống gắn nhãn `YELLOW` hoặc `RED` và tính đúng Priority Weight.
  - Kiểm thử trích dẫn SOT: Đảm bảo 100% trích dẫn xuất ra đúng định dạng tọa độ và không chứa text tự sinh phi căn cứ.
- **Prior Art**: Kế thừa test pattern từ `packages/ccba-legal-intel/tests/test_parser_registry.py` và `test_granular_amendments.py`.

## Out of Scope

- Tự động ký số hoặc gửi công văn điện tử trực tiếp đến cổng dịch vụ công của cơ quan nhà nước.
- Xử lý các tranh chấp dân sự/hình sự nằm ngoài phạm vi pháp luật quản lý đầu tư xây dựng & PCCC/MEP/BIM.
- Thay thế hoàn toàn tư vấn pháp lý chính thức có đóng dấu chuyên môn của Luật sư thuộc Đoàn Luật sư.

## Further Notes

- Kế thừa trực tiếp kết quả nghiên cứu và cấu hình từ phiên Brainstorming ghi nhận tại [brainstorm_session_tu_van_phap_luat.md](file:///C:/Users/chuvu/.gemini/antigravity/brain/1800601c-9c09-4e0d-9280-19898f0c9c9a/brainstorm_session_tu_van_phap_luat.md).
