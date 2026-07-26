# 🗺️ Wayfinder Map: Xây Dựng Trợ Lý AI Tư Vấn Pháp Luật Xây Dựng CCBA

- **Mã dự án:** `legal_advisory_agent`
- **Khởi tạo:** 25/07/2026
- **Cập nhật gần nhất:** 25/07/2026 (Hoàn thành 100% Giai đoạn MVP - Ticket 01, 02, 03)
- **Trạng thái:** MVP Completed (Hoàn thành Giai đoạn MVP)

---

## 🎯 Điểm Đích (Destination)

Xây dựng thành công **Trợ lý AI Tư vấn Pháp luật Xây dựng CCBA** vận hành chính thức trên CCBA Agent Platform với các năng lực cốt lõi:
1. Tra cứu RAG siêu tốc & chuẩn xác 100% kèm trích dẫn Điều/Khoản VBPL gốc, rào chắn chống hallucination.
2. Tự động theo dõi & duy trì trạng thái Sổ bộ Pháp lý `legal_registry.yaml` (Luật, Nghị định, Thông tư, QCVN/TCVN).
3. Bộ dịch song phương **Legal-Technical Translator** (dịch lỗi kỹ thuật thành mức phạt/rủi ro pháp lý & tài chính).
4. Tích hợp Google NotebookLM Connector cho phép hỏi đáp & xuất Audio Podcast trên các bộ VBPL cực lớn.
5. Nhúng trực tiếp bước **Legal Compliance Audit** vào chuỗi kiểm soát chất lượng tự động `run-qc-pipeline`.

---

## 📝 Ghi Chú & Kỹ Năng Bổ Trợ (Notes)

- **Nguyên tắc:** Lập kế hoạch trước (Plan, don't do). Mỗi ticket nhằm làm rõ một quyết định chiến lược.
- **Kỹ năng nạp:** `legal-document-tracker`, `hybrid-rag-search`, `notebooklm-connector`, `xu-ly-van-phong`, `ccba-ai-qc-reporter`, `ccba-research`.
- **Rào chắn bảo mật:** Không hardcode API Keys; lưu trữ tri thức tại `.md/knowledge/` của dự án.

---

## ✅ Quyết Định Đã Chốt (Decisions So Far)

- `[Thống nhất Mục tiêu & Kiến trúc Brainstorming](file:///C:/Users/chuvu/.gemini/antigravity/brain/bb6b76dd-7a8d-44e9-85be-6ea70ffabf5f/brainstorm_session_legal_advisory_agent.md)`: Đã hoàn tất phiên brainstorm xác định 4 khối tính năng, mô hình người dùng song song (Internal PM vs External Client) và lộ trình ưu tiên P0 → P1 → P2.
- `[Chuẩn hóa Sổ bộ legal_registry.yaml & Triển khai Hybrid RAG Index](file:///d:/GitHubProjects/ccba-agent-platform/scripts/legal_rag_indexer.py)`: Đã cài đặt module `scripts/legal_rag_indexer.py` và bộ test seam `tests/test_legal_registry_rag.py` (3/3 tests PASSED).
- `[Prototype Workflow /ccba-legal-intel & Grounding Gate](file:///d:/GitHubProjects/ccba-agent-platform/.agents/workflows/ccba-legal-intel.md)`: Đã cài đặt module verifier `scripts/legal_grounding_gate.py`, workflow guide `.agents/workflows/ccba-legal-intel.md` và test suite `tests/test_legal_grounding_gate.py` (3/3 tests PASSED).
- `[Thiết kế Biểu mẫu Báo cáo Tư vấn Pháp lý & Công văn theo NĐ 30/2020](file:///d:/GitHubProjects/ccba-agent-platform/scripts/legal_template_generator.py)`: Đã cài đặt module document generator `scripts/legal_template_generator.py` và test suite `tests/test_legal_template_generator.py` (3/3 tests PASSED).

---

## 🚀 Biên Giới / Ticket Mở Unblocked (Frontier Tickets)

- *Toàn bộ các ticket MVP đã hoàn tất.*

---

## 🌫️ Chưa Xác Định Rõ / Sương Mù Chiến Trận (Not Yet Specified)

1. **Auto Legal Crawler Engine:** Cơ chế tự động cào và phát hiện thay đổi trên cổng moc.gov.vn (Chờ làm rõ cấu trúc web và tần suất cập nhật).
2. **Legal Diff Engine (NĐ 06 vs Dự thảo NĐ QLCL 2026):** Thuật toán so sánh ngữ nghĩa câu từ giữa bản cũ và mới (Chờ có dự thảo chính thức hoàn chỉnh).
3. **QC Pipeline Integration:** Cách thức nhúng điểm phạt pháp lý vào file Coordination Matrix của `run-qc-pipeline` (Chờ nâng cấp pipeline QC tiếp theo).

---

## 🚫 Ngoài Phạm Vi (Out of Scope)

- Thay thế hoàn toàn tư vấn pháp lý chính thức của Luật sư/Chuyên gia pháp luật có chứng chỉ hành nghề.
- Xây dựng phần mềm quản lý dự án độc lập không nằm trên hệ sinh thái CCBA Agent Platform.
