# 🗺️ Wayfinding Map: Hub Zero-Duplication & Legal Knowledge Pointer Harmonization

> **Mã định danh:** `MAP-LEGAL-ZERO-DUP-01`  
> **Trạng thái:** `Active (Frontier Open)`  
> **Khởi lập:** `2026-08-15`  
> **Áp dụng:** CCBA Agent Platform (Hub) ↔ CCBA-LEGAL-KNOWLEDGE (Spoke)  

---

## 🎯 1. Điểm Đích (Destination)

Đưa Hub **`ccba-agent-platform`** đạt chuẩn **Zero-Duplication SSOT (0% Trùng Lặp Dữ Liệu)**:
1. **Dọn Dẹp Di Sản Trùng Lặp:** Xóa bỏ thư mục `d:\GitHubProjects\ccba-agent-platform\.md\legal_docs\` và các tệp `.txt` cào thô trong `.md\extracted_docs\` vốn là dữ liệu lịch sử tạm thời sinh ra trước khi tách Spoke `ccba-legal-knowledge`.
2. **Thiết Lập Con Trỏ Tri Thức Động (`legal_knowledge_kb`):** Khai báo con trỏ `[legal_knowledge_path]` trong `catalog.yaml` để mọi Agent trên Hub và các Spokes khác tra cứu trực tiếp từ Spoke `ccba-legal-knowledge` mà không nhân bản dữ liệu.
3. **Kiểm Định Khép Kín:** Cập nhật bộ kiểm tra `doc_auditor.py` và đảm bảo toàn bộ 32/32 tests tự động đạt 100% PASSED.

---

## 📝 2. Ghi Chú & Nguyên Tắc Vận Hành (Notes)

* **Nguyên tắc SSOT (Single Source of Truth):**
  * Spoke `D:\GitHubProjects\ccba-legal-knowledge` là nơi lưu trữ **duy nhất** toàn văn Markdown OKF v2.0 của tất cả các bộ luật, nghị định, thông tư, QCVN, TCVN và phụ lục biểu mẫu.
  * Hub chỉ lưu trữ **Logic, Engines, Crawlers, Parsers và Con Trỏ Catalog**.
* **Kế thừa các chuẩn mực kiến trúc:**
  * [`ADR 0036: Brownfield Spoke Adoption & Non-Destructive Onboarding`](docs/adr/0036-brownfield-spoke-adoption-and-non-destructive-onboarding.md).
  * [`ADR 0037: Constitution-Driven Traceability Matrix & Dynamic Knowledge Pointers`](docs/adr/0037-constitution-driven-traceability-matrix.md).

---

## 🏆 3. Quyết Định Đã Chốt (Decisions So Far)

* **[D01: Xác minh trùng lặp thực tế qua Double-Pass Review]**: Đã đối soát đĩa cứng phát hiện `.md/legal_docs` và hơn 40 tệp `.txt` trong `.md/extracted_docs` trên Hub là bản sao lịch sử, cần được dọn dẹp để trả quyền SSOT duy nhất về cho Spoke `ccba-legal-knowledge`.
* **[D02: Áp dụng Pointer Pattern cho Legal Knowledge]**: Đăng ký `legal_knowledge_kb` vào `catalog.yaml` với cú pháp `[legal_knowledge_path]` đồng nhất với `idop_path` và `bigbim_method_path`.
* **[D03: Hoàn thành Khai báo Con trỏ T01 & Dọn dẹp T02]**: Đã khai báo con trỏ động `legal_knowledge_kb` trong `catalog.yaml`, xóa sạch thư mục `.md/legal_docs/` và 22 tệp `.txt` raw text trên Hub.
* **[D04: Hoàn thành Kiểm định T03]**: 32/32 tests passed 100%, Doc Auditor passed 0 errors.

---

## 🚀 4. Danh Sách Ticket Tại Biên Giới (Frontier Tickets)

* **Toàn bộ 3 Ticket (T01, T02, T03) đã hoàn thành 100%!**
* Bản đồ `MAP-LEGAL-ZERO-DUP-01` đã đạt trạng thái **Hoàn Thành Toàn Diện (Fully Accomplished)**. Hub đã sạch hoàn toàn, đạt chuẩn 0% trùng lặp dữ liệu với Spoke `ccba-legal-knowledge`.

---

## 🌫️ 5. Sương Mù Chiến Trận / Chưa Xác Định Rõ (Not Yet Specified)

* **Không có sương mù (0% Fog):** Phạm vi dọn dẹp và cơ chế con trỏ động đã rõ ràng 100%.

---

## 🚫 6. Ngoài Phạm Vi (Out of Scope)

* **Xóa các tài liệu nghiên cứu nội bộ của Hub:** Các báo cáo nghiên cứu kỹ thuật, seminar recap, biên bản khảo sát trong `.md/extracted_docs/` và `.md/knowledge/` được giữ nguyên.
