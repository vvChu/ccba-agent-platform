# 🗺️ Wayfinding Map: Chuẩn Hóa & Tiếp Nhận Spoke CCBA-LEGAL-KNOWLEDGE

> **Mã định danh:** `MAP-LEGAL-SPOKE-ADOPTION-01`  
> **Trạng thái:** `Active (Frontier Open)`  
> **Khởi lập:** `2026-08-15`  
> **Áp dụng:** CCBA Agent Platform (Hub) ↔ CCBA-LEGAL-KNOWLEDGE (Legal Spoke)  

---

## 🎯 1. Điểm Đích (Destination)

Đưa Spoke **`D:\GitHubProjects\ccba-legal-knowledge`** vào trạng thái kết nối chính quy, an toàn và đạt chuẩn 100% của mạng lưới CCBA Platform:
1. **Tiếp nhận An Toàn Không Phá Hủy (ADR 0036):** Hợp nhất tệp `workspace_context.yaml` vào `.md/`, bảo tồn 100% thông tin NotebookLM (`primary_notebook_id: 6dca7e4e-...`) và cấu trúc Shallow Path (`legal_docs/`).
2. **Kích hoạt Bảo mật Toàn Diện:** Cài đặt Maskara Git pre-commit hook tại Spoke để ngăn chặn rò rỉ API Keys/Credentials.
3. **Đồng Bộ Năng Lực AI Mới Nhất:** Nạp đầy đủ 69 Skills và 49 Workflows chuẩn hóa từ Hub.
4. **Dọn Dẹp Workspace Sạch Sẽ:** Dọn dẹp hơn 60 thư mục tạm thời trong `.agents/` từ các subagents phiên trước, tối ưu hóa dung lượng repository.
5. **Kiểm Định Toàn Vẹn:** Chạy kiểm tra Doc Auditor và đăng ký Spoke vào Hub Spoke Registry.

---

## 📝 2. Ghi Chú & Nguyên Tắc Vận Hành (Notes)

* **Bảo tồn Nguồn Sự Thật Duy Nhất (SSOT):**
  * Toàn bộ tài liệu luật, nghị định, thông tư, QCVN, TCVN tại `legal_docs/` và `legal_registry.yaml` được bảo tồn nguyên vẹn 100%.
* **Kế thừa các chuẩn mực kiến trúc:**
  * [`ADR 0036: Brownfield Spoke Adoption & Non-Destructive Onboarding`](docs/adr/0036-brownfield-spoke-adoption-and-non-destructive-onboarding.md).
  * [`ADR 0037: Constitution-Driven Traceability Matrix & Dynamic Knowledge Pointers`](docs/adr/0037-constitution-driven-traceability-matrix.md).

---

## 🏆 3. Quyết Định Đã Chốt (Decisions So Far)

* **[D01: Hoàn tất Ma trận Khám phá 3 Tầng]**: Đã chạy `SpokeAdopter` dry-run trên `D:\GitHubProjects\ccba-legal-knowledge`, xác nhận Spoke thuộc nhóm *Knowledge Base / Tư vấn pháp lý*, `AGENTS.md` được bảo vệ nguyên vẹn và sẵn sàng tiếp nhận.
* **[D02: Hợp nhất Schema 2-thành-1]**: Hợp nhất tệp `workspace_context.yaml` tại Root và `.md/workspace_context.yaml` thành 1 bản duy nhất tại `.md/workspace_context.yaml` chuẩn Hub.
* **[D03: Hoàn thành Tiếp nhận T01 & Dọn dẹp T02]**: Đã tiếp nhận thành công, cài đặt Maskara pre-commit hook, đồng bộ 76 skills & 52 workflows, và xóa sạch hơn 60 thư mục tạm thời trong `.agents/`.
* **[D04: Hoàn thành Kiểm định T03]**: 32/32 unit tests passed (100%), Doc Auditor passed 0 error, Spoke đã được mã hóa đăng ký vào Hub Registry.

---

## 🚀 4. Danh Sách Ticket Tại Biên Giới (Frontier Tickets)

* **Toàn bộ 3 Ticket (T01, T02, T03) đã hoàn thành 100%!**
* Bản đồ `MAP-LEGAL-SPOKE-ADOPTION-01` đã đạt trạng thái **Hoàn Thành Toàn Diện (Fully Accomplished)**. Spoke `ccba-legal-knowledge` chính thức hòa mạng CCBA Platform với độ tin cậy và bảo mật tối đa.

---

## 🌫️ 5. Sương Mù Chiến Trận / Chưa Xác Định Rõ (Not Yet Specified)

* **Không có sương mù (0% Fog):** Toàn bộ quy trình tiếp nhận và dọn dẹp đã được xác định rõ ràng 100%.

---

## 🚫 6. Ngoài Phạm Vi (Out of Scope)

* **Chỉnh sửa nội dung văn bản quy phạm pháp luật:** Không can thiệp vào câu từ hoặc điều khoản trong các tệp Markdown tại `legal_docs/`.
