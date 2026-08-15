# 🗺️ Wayfinding Map: Hub-Spoke Ecosystem Harmonization & Upstream Integration

> **Mã định danh:** `MAP-HUB-SPOKE-HARMONIZATION-01`  
> **Trạng thái:** `Active (Frontier Open)`  
> **Khởi lập:** `2026-08-15`  
> **Áp dụng:** CCBA Agent Platform (Hub) ↔ IDOP-CCBA-WAY (Production Spoke)  

---

## 🎯 1. Điểm Đích (Destination)

Thiết lập cơ chế liên thông kiến trúc 2 chiều hoàn chỉnh giữa **CCBA Agent Platform (Hub)** và **IDOP-CCBA-WAY (Spoke Vận hành)**, đạt được:
1. **0% Trùng lặp dữ liệu (Zero-Duplication SSOT):** Khai báo nhóm tri thức thể chế vận hành CCBA (`ccba_operations_kb`) trong Hub Catalog qua cơ chế **Con trỏ Động (Dynamic Pointer)**, cho phép mọi Agent truy cập `QCTK 2815`, `QCCTNB 3209`, `CCBA Charter 2026` từ Spoke mà không nhân bản tệp tin.
2. **Chuẩn hóa Traceability Matrix:** Ban hành **ADR 0037** đúc kết mô hình `cross_references.yaml` thành quy chuẩn thiết kế hệ thống có truy vết cho toàn bộ hệ sinh thái CCBA.
3. **Đóng gói Kỹ năng `sharepoint-iac`:** Trừu tượng hóa bộ kiểm định schema SharePoint/M365 từ IDOP thành kỹ năng dùng chung trên Hub cho các dự án Intranet/BIM CDE.

---

## 📝 2. Ghi Chú & Nguyên Tắc Vận Hành (Notes)

* **Nguyên tắc SSOT (Single Source of Truth):**
  * Spoke `idop-ccba-way` là nơi lưu trữ **duy nhất** các bản gốc quy chế thể chế và dữ liệu 58 lists.
  * Hub `ccba-agent-platform` chỉ lưu trữ **Meta-Patterns, Validators, Workflows và Con trỏ Catalog (`[idop_path]`)**.
* **Kế thừa các ADR tiền đề:**
  * [`ADR 0035: Polyglot Deep Modules & Subagent Guardrails`](docs/adr/0035-polyglot-deep-modules-and-subagent-guardrails.md).
  * [`ADR 0036: Brownfield Spoke Adoption & Non-Destructive Onboarding`](docs/adr/0036-brownfield-spoke-adoption-and-non-destructive-onboarding.md).

---

## 🏆 3. Quyết Định Đã Chốt (Decisions So Far)

* **[D01: Tiếp nhận Spoke an toàn không phá hủy]**: Đã hoàn thành tiếp nhận Spoke `idop-ccba-way` qua `/ccba-adopt-spoke`, bảo tồn nguyên vẹn 100% cấu trúc custom context và cài đặt Maskara pre-commit hook.
* **[D02: Cơ chế Con trỏ Tri thức (Pointer Pattern)]**: Thống nhất phương án không copy file quy chế sang Hub, mà sử dụng cơ chế con trỏ động `[idop_path]` tương tự `bigbim_method_kb` trong `catalog.yaml`.
* **[D03: Hoàn thành Ticket T01 - Đăng ký ccba_operations_kb]**: Đã khai báo nhóm tri thức thể chế CCBA vào `catalog.yaml` trỏ đến `[idop_path]/.md/INDEX.md` và `cross_references.yaml`.
* **[D04: Hoàn thành Ticket T02 - Ban hành ADR 0037]**: Đã ban hành `docs/adr/0037-constitution-driven-traceability-matrix.md` và cập nhật thuật ngữ vào `CONTEXT.md`.
* **[D05: Hoàn thành Ticket T03 - Đóng gói sharepoint-iac]**: Đã tạo kỹ năng `.agents/skills/sharepoint-iac/SKILL.md` và đăng ký vào `catalog.yaml`.
* **[D06: Giải tỏa Sương mù FOG-01 qua Socratic Grilling]**: Thống nhất xây dựng Deep Module `scripts/governance/cross_ref_validator.py` và CLI `scripts/validate_cross_references.py` trên Hub, hoạt động theo mô hình Hard Gate (`Exit Code 1` on broken links), cờ `--warn-only` cho giai đoạn nháp, và thuật toán Fuzzy Matching gợi ý/tự sửa (`--fix`).
* **[D07: Hoàn thành Ticket T04 - Cross-Reference Validator & CI Gate Engine]**: Đã lập trình Deep Module `cross_ref_validator.py`, CLI `validate_cross_references.py`, bộ test TDD `test_cross_ref_validator.py` (7/7 tests passed 100%), và tích hợp vào `scripts/governance/__init__.py`.

---

## 🚀 4. Danh Sách Ticket Tại Biên Giới (Frontier Tickets)

* **Toàn bộ 4 Ticket (T01, T02, T03, T04) đã hoàn thành 100%!**
* Bản đồ `MAP-HUB-SPOKE-HARMONIZATION-01` đã đạt trạng thái **Hoàn Thành Toàn Diện (Fully Accomplished)**. Lộ trình liên thông và kiểm định kiến trúc Hub ↔ Spoke đạt 100% độ phủ.

---

## 🌫️ 5. Sương Mù Chiến Trận / Chưa Xác Định Rõ (Not Yet Specified)

* **Không còn sương mù (0% Fog):** Toàn bộ bài toán kiểm định và liên thông kiến trúc Hub ↔ Spoke đã được xác định hoàn toàn sáng tỏ.

---

## 🚫 6. Ngoài Phạm Vi (Out of Scope)

* **Sửa đổi văn bản thể chế nội bộ CCBA/IBST:** Các văn bản `QCTK 2815`, `QCCTNB 3209`, `CCBA Charter 2026` là quy chế chính thức do Lãnh đạo Viện/Trung tâm ban hành; Hub và Spoke chỉ tuân thủ và dẫn chiếu, không tự ý chỉnh sửa nội dung điều khoản.
