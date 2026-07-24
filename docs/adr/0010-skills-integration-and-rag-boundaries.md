# ADR 0010: Phân Định Ranh Giới Tích Hợp Kỹ Năng Nghiên Cứu & Mẫu Thử

* **Trạng thái:** Approved
* **Người đề xuất:** Antigravity AI Agent
* **Ngày quyết định:** 2026-07-09

---

## 1. Ngữ cảnh (Context)
Việc porting và nâng cấp thành công hai kỹ năng mới là `/ccba-research` (Nghiên cứu chạy ngầm qua subagent) và `/ccba-prototype` (Xây dựng mẫu thử thô) mở ra cơ hội liên kết rất lớn với các kỹ năng nghiệp vụ hiện có trên CCBA Platform (như PCCC Audit, lập hồ sơ hoàn công, cải tiến kiến trúc). 

Tuy nhiên, việc tích hợp tự động hoàn toàn (100% auto-trigger) đi kèm hai rủi ro lớn:
1.  **Phình to chi phí API Gateway**: Mỗi lượt spawn subagent nghiên cứu đệ quy văn bản lớn hoặc dựng prototype sẽ tiêu tốn lượng token khổng lồ từ LiteLLM Spark.
2.  **Kéo dài thời gian phản hồi**: Việc Agent chính bị block để đợi subagent hoàn thành legwork sẽ làm giảm trải nghiệm tương tác trực tiếp.

## 2. Quyết định (Decisions)
Chúng tôi thống nhất thiết lập các ranh giới và quy tắc tích hợp như sau:

### Quyết định 1: Chế độ bán tự động (HITL) cho RAG đối chiếu Quy chuẩn trong PCCC Audit
*   **Nguyên tắc:** Khi chạy audit thiết kế (`ccba-ai-qc-pccc-audit`) và phát hiện lỗi nghi vấn, Agent **không tự ý** spawn subagent nghiên cứu.
*   **Thực thi:** Agent ghi nhận lỗi nghi vấn vào báo cáo sơ bộ và đưa ra đề xuất tương tác: *"Phát hiện nghi vấn vi phạm TCVN 3890 tại hành lang thoát nạn. Anh có muốn kích hoạt `/ccba-research tcvn-3890` để đối soát sâu dưới nền không?"*. Lệnh nghiên cứu chỉ chạy khi có sự xác nhận tường minh của người dùng.

### Quyết định 2: Tích hợp RAG có điều kiện trong hồ sơ hoàn công (`completion-checklist`)
*   **Nguyên tắc:** Ưu tiên sử dụng dữ liệu cấu trúc tĩnh (static templates) mặc định có sẵn cho Nghị định 06/2021/NĐ-CP (đã được thay thế bởi NĐ 105/2025/NĐ-CP) để tiết kiệm 100% chi phí token RAG.
*   **Thực thi:** Chỉ kích hoạt RAG nghiên cứu qua `ccba-research` khi Registry văn bản cục bộ (`legal_registry.yaml`) báo cáo Nghị định hoặc Thông tư về nghiệm thu hoàn công hiện hành đã chuyển trạng thái sang `superseded` (hết hiệu lực) và có văn bản thay thế mới (`current`).

### Quyết định 3: Giới hạn đề xuất dựng mẫu thử trong cải tiến kiến trúc (`improve-codebase-architecture`)
*   **Nguyên tắc:** Không bắt buộc dựng prototype cho mọi đề xuất refactor codebase.
*   **Thực thi:** Chỉ đề xuất dựng `/ccba-prototype` (nhánh Logic/UI) khi việc refactor ảnh hưởng trực tiếp đến **Core Platform (Hub)** (như sửa đổi core services, metadata registry, database schema chung). Đối với các Spoke apps hoặc các hàm độc lập, thực hiện viết code trực tiếp và chạy kiểm thử an toàn.

## 3. Hệ quả (Consequences)
*   **Tích cực:** Kiểm soát tối ưu chi phí API của Platform, duy trì tốc độ phản hồi nhanh cho các phiên làm việc thông thường.
*   **Tiêu cực:** Người dùng cần thực hiện thêm 1 bước xác nhận (HITL) khi muốn Agent đối soát sâu quy chuẩn gốc.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
