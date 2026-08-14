# ADR 0011: Chuyển Đổi Kiến Trúc Deep Module Cho ccba-legal-intel & Dọn Dẹp Domain ccba-ooxml

* **Trạng thái:** Approved
* **Người đề xuất:** Antigravity AI Agent
* **Ngày quyết định:** 2026-08-14

---

## 1. Ngữ cảnh (Context)
Trong quá trình rà soát kiến trúc định kỳ qua kỹ năng `/improve-codebase-architecture`, chúng tôi phát hiện 2 điểm nghẽn kiến trúc (Architectural Friction):
1. **Rò rỉ Bề mặt Giao diện (Leaky Interface) tại `ccba-legal-intel`**: Tệp `packages/ccba-legal-intel/src/ccba_legal/__init__.py` export hơn 30 symbols nội bộ (ASTNode, Cleaners, OKFBundlePackager, TokenMonitor...). Đồng thời, thư mục `scripts/legal/` chứa các script cào dữ liệu (`tvpl_vip_crawler.py`) tự triển khai `CookieVault` và session checking trùng lặp với core package thay vì dùng chung một Seam duy nhất.
2. **Lạc Domain (Domain Drift) tại `ccba-ooxml`**: Tệp `process_pdf.py` (3.2KB) nằm trong thư viện OOXML (Office Open XML - DOCX, PPTX, XLSX) là dead code / bản sao trùng lặp từ skill văn phòng, gây nhầm lẫn trách nhiệm với package chuyên biệt `ccba-pdf-prep`.

---

## 2. Quyết định (Decisions)

### Quyết định 1: Thu gọn Bề mặt Công khai thành 3 Deep Seams chính theo Convention
* **Nguyên tắc:** Ứng dụng nguyên lý *"Hide by convention, not by force"*.
* **Thực thi:** 
  * Thu hẹp danh sách `__all__` tại `ccba_legal/__init__.py` chỉ còn **3 Deep Seams**:
    1. `LegalIntelPipeline` (kèm `LegalProcessResult`): Điểm nhập duy nhất cho cào Chrome CDP, bảo vệ CookieVault, mutex lock, parse AST và đóng gói OKF Bundle.
    2. `LegalProcessor`: Điểm nhập duy nhất cho phân tích xung đột văn bản pháp lý (`LexConflictEngine`) và tạo báo cáo tư vấn Dual-Layer.
    3. `LegalSyncEngine`: Điểm nhập cho đồng bộ legal registry lên Google NotebookLM / Google Drive.
  * Giữ nguyên cấu trúc file submodules (`ccba_legal.crawler`, `ccba_legal.ast_parser`, `ccba_legal.monitor`...) để đảm bảo 23+ unit test files và cross-package consumers (`ccba-harness`) tiếp tục hoạt động mà không bị phá vỡ import path.

### Quyết định 2: Hợp nhất Hạ tầng `CookieVault` vào Core Package
* **Nguyên tắc:** Đảm bảo tính Locality — logic quản lý phiên VIP của TVPL chỉ nằm tại một nơi duy nhất.
* **Thực thi:** Di chuyển `CookieVault`, `check_vip_session_health`, `get_tvpl_credentials` vào `ccba_legal.crawler`. Tệp `scripts/legal/tvpl_vip_crawler.py` và `auto_tvpl_vip_downloader.py` trở thành Thin CLI Delegates mỏng.

### Quyết định 3: Xóa Bỏ Hoàn Toàn `process_pdf.py` khỏi `ccba-ooxml`
* **Nguyên tắc:** Đảm bảo tính thuần khiết của domain OOXML.
* **Thực thi:** Xóa bỏ tệp `packages/ccba-ooxml/src/ccba_ooxml/process_pdf.py`. Mọi thao tác xử lý PDF trên nền tảng được định tuyến thống nhất về package `ccba-pdf-prep`.

### Quyết định 4: Migrate Test Ngoài Luồng vào Test Suite Chính Thức
* **Thực thi:** Chuyển 5 test cases từ `scripts/legal/verify_legal_intel.py` vào `packages/ccba-legal-intel/tests/test_cleaners_packager.py` và xóa bỏ script kiểm thử ngoài luồng.

---

## 3. Hệ quả (Consequences)
* **Tích cực:**
  * Giảm 75% số lượng symbols công khai tại `ccba_legal`, tăng độ đòn bẩy (Leverage) và tính dễ định hướng cho AI (AI-Navigability).
  * Loại bỏ hoàn toàn nguy cơ phân kỳ logic cào TVPL VIP giữa scripts và package.
  * Codebase sạch, loại bỏ 2 tệp dead code / duplicate code.
* **Tiêu cực / Rủi ro đã phòng ngừa:**
  * Bằng cách không đổi tên các file submodule, chúng tôi ngăn ngừa được nguy cơ làm gãy hơn 40 import paths trong test suite và các package liên kết.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
