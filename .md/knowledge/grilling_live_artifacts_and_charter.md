# Biên Bản Phỏng Vấn Socratic Grilling: Thiết Kế Live State Artifacts & Tích Hợp 11 Ghế CCBA Charter

> **Thời gian thực hiện:** 2026-09-10  
> **Kỹ năng chủ trì:** `/ccba-grilling`  
> **Thành phần tham gia:** Antigravity Platform Agent & Kỹ sư trưởng CCBA  
> **Quy chuẩn đối chiếu:** ADR-0030 (Instruction Budget), ADR-0035 (Deep Modules), ADR-0046 (Personal Sandbox & CCBA Charter 2026), ADR-0053 (Teamwork Multi-Agent), ADR-0057 (Two-Stage Decision Framework).  
> **Tài liệu sinh sau:** ADR-0058 (Live Collaboration Artifacts & Charter Review).

---

## 1. Bối Cảnh & Mục Tiêu Phiên Phỏng Vấn

Nhằm nâng cấp toàn diện hệ sinh thái kỹ năng `ccba-*` theo lộ trình Wayfinder (**Ticket 5**), phiên đối thoại Socratic Grilling được kích hoạt để giải quyết triệt để 4 điểm nghẽn kiến trúc xoay quanh việc tương tác giữa AI Agent và Lập trình viên:
1. Xung đột giữa cơ chế hiển thị Tab Native của Antigravity IDE (`<appDataDir>\brain\<conversation-id>/`) và Quy tắc Toàn cục số 1 (`.\.md\` là Knowledge Base duy nhất).
2. Tình trạng sinh quá nhiều Artifacts gây pha loãng chú ý (Attention Dilution).
3. Cách thức áp dụng và cưỡng chế thẩm quyền của **11 Ghế Hội đồng Thẩm định CCBA Charter 2026** và **5 Cấp độ QC** (ADR-0046) trên giao diện phản hồi của Agent (`RequestFeedback: true`).
4. Khóa cứng kết quả kiểm thử máy tính của **Exit-Code Deterministic Verification Gate** (`ccba-harness verify-patch`) vào vòng nghiệm thu.

---

## 2. Diễn Biến 4 Vòng Phỏng Vấn Dồn Dập (Grilling Log & Resolution Summary)

### Vòng 1 — Cơ Chế Lưu Trữ & SSOT: Hóa Giải Xung Đột `brain/` vs `.\.md\`
- **Câu hỏi đặt ra**: Antigravity bắt buộc ghi vào thư mục nội bộ `brain/` để render Tab giao diện và nút `Proceed`, trong khi Rule 1 bắt buộc mọi tài sản AI phải nằm trong `.\.md\`. Cấu trúc đường ống lưu trữ như thế nào?
- **Phân tích trade-offs**:
  - *Phương án A*: Transient Buffer in `brain/` + Final Snapshot in `.\.md\reports/` hoặc `.\.md/knowledge/`.
  - *Phương án B*: Dual-Write Synchronous Mirroring (ghi đè đồng thời mỗi bước).
  - *Phương án C*: NTFS Symlink / Directory Junction.
- **Phán quyết của Kỹ sư trưởng**: **Chọn Phương án A**.
- **Quy tắc chốt**: Trong suốt phiên làm việc, Agent dùng `brain/` làm vùng đệm tương tác động. Khi người dùng nhấn duyệt hoặc khi hoàn thành task / commit git, Agent tự động sao lưu bản snapshot cuối cùng vào `.\.md\reports/` (hoặc `.\.md/knowledge/`) để lưu trữ vĩnh viễn trong Git repository. Tránh rác Git working tree, tương thích 100% Windows.

---

### Vòng 2 — Danh Mục Artifacts Chuẩn Hóa: Dashboard Mới Hay Tối Ưu Nội Khối (In-Situ)?
- **Câu hỏi đặt ra**: Có nên sinh hàng loạt artifacts mới (`task_dashboard.md`, `qc_matrix.md`, `risk_register.md`) cho mọi task không?
- **Phân tích trade-offs**:
  - *Phương án A (KISS)*: Bộ Ba Chuẩn Mực Bất Biến (Trio Core Artifacts) gồm `implementation_plan.md`, `walkthrough.md`, `task_dashboard.md` (chỉ khi multi-agent). Nhúng nội khối đề mục `## CCBA Charter Governance & QC Matrix` trong Kế hoạch.
  - *Phương án B*: Phân tách tối đa thành 4–5 file chuyên biệt (Hyper-Modular).
  - *Phương án C*: Gộp chung làm 1 file duy nhất (Single Consolidated Living Document).
- **Phán quyết của Kỹ sư trưởng**: **Chọn Phương án A**.
- **Quy tắc chốt**: Tối đa hóa sự tập trung nhận thức của người dùng. `implementation_plan.md` là màn hình duy nhất để duyệt kế hoạch; `walkthrough.md` là màn hình duy nhất để nghiệm thu kết quả; `task_dashboard.md` chỉ sinh ra khi có điều phối Swarm Multi-Agent.

---

### Vòng 3 — Cơ Chế Phân Quyền 11 Ghế CCBA Charter & 5 Cấp Độ QC (ADR-0046)
- **Câu hỏi đặt ra**: Ràng buộc thẩm quyền 11 Ghế và trần QC giữa Personal Sandbox Spoke và Spoke Dự án chính thức như thế nào?
- **Phân tích trade-offs**:
  - *Phương án A*: Tự động thích ứng theo ngữ cảnh Workspace (Context-Aware Adaptive Gate & Sandbox Watermark Cap).
  - *Phương án B*: Tự do khai báo text (Free-form Role Tagging).
  - *Phương án C*: Khóa cứng đa chữ ký (Rigid Multi-Signature).
- **Phán quyết của Kỹ sư trưởng**: **Chọn Phương án A**.
- **Quy tắc chốt**:
  1. **Personal Sandbox Spoke**: Tự động khóa trần phê duyệt ở **QC Level 1 (Technical Check)** với ghế `KY_SU_THUC_THI`. Mọi Artifact tự động gắn Watermark: `⚠️ [CCBA SANDBOX DRAFT — BẢN THẢO NGHIÊN CỨU NỘI BỘ — CHƯA PHÁT HÀNH CHÍNH THỨC]`. Cấm tuyệt đối Agent tự nâng trần QC.
  2. **Spoke Dự Án Chính Thức (`delivery_project`)**: Kích hoạt đúng thẩm quyền 11 Ghế:
     - Code/Kỹ thuật: `CHU_TRI_BO_MON` (QC Level 2).
     - Nghiệm thu sản phẩm / IDOP: `CHU_TRI_HOP_DONG_PM` (QC Level 3) + `IDOP_LEAD`.
     - Pháp lý / Tiêu chuẩn: `CO_VAN_PHAP_LY_QA` (QC Level 4).
     - Phát hành chính thức: `GIAM_DOC` / `PHO_GIAM_DOC` (QC Level 5).
  3. **Hub Platform**: Thay đổi hệ thống, kiến trúc do `TRUONG_PHONG_RD_HTQT` hoặc `GIAM_DOC` chuẩn y.

---

### Vòng 4 — Khóa Chặt Cổng Kiểm Định Khách Quan (Exit-Code Gate) Vào Vòng Nghiệm Thu
- **Câu hỏi đặt ra**: Làm sao triệt tiêu hoàn toàn Premature Completion khi người dùng xem `walkthrough.md`?
- **Phân tích trade-offs**:
  - *Phương án A*: Bắt buộc nhúng Bằng chứng Máy tính (Deterministic Machine Evidence) từ `ccba-harness verify-patch` và Khóa hoàn thành cứng (Hard Completion Lock).
  - *Phương án B*: Tự đánh giá định tính (Qualitative Self-Report).
  - *Phương án C*: Chỉ dựa vào Silent Git Hook ngầm.
- **Phán quyết của Kỹ sư trưởng**: **Chọn Phương án A**.
- **Quy tắc chốt**:
  1. `walkthrough.md` bắt buộc phải nhúng Báo cáo Thẩm tra Khách quan từ `ccba-harness verify-patch`.
  2. **Hard Lock**: Nếu Exit Code $\ne 0$, cấm tuyệt đối Agent tuyên bố hoàn thành hoặc đề xuất nghiệm thu. Bắt buộc kích hoạt Fix Loop hoặc dừng khẩn cấp kèm log chi tiết.

---

## 3. Bản Mẫu Khung Chuẩn Hóa (Standard Template Specification)

### Khung đề mục bắt buộc trong `implementation_plan.md`:
```markdown
## CCBA Charter Governance & QC Matrix

- **Workspace Archetype:** [personal_sandbox | delivery_project | central_hub]
- **QC Authorization Level:** [LEVEL_1_TECHNICAL_CHECK .. LEVEL_5_FINAL_APPROVAL]
- **Accountability Seat:** [KY_SU_THUC_THI | CHU_TRI_BO_MON | CHU_TRI_HOP_DONG_PM | CO_VAN_PHAP_LY_QA | GIAM_DOC | TRUONG_PHONG_RD_HTQT]
- **Watermark Status:** [APPLIED: [CCBA SANDBOX DRAFT] | OFFICIAL_PROJECT_RECORD]
- **IDOP Task Code:** [PGV_XXXX / None]
- **Pre-execution Verification Commands:**
  * `pytest ...`
  * `ruff check ...`
  * `mypy ...`
```

### Khung đề mục bắt buộc trong `walkthrough.md`:
```markdown
## Objective Verification Evidence

```bash
# Deterministic Patch Verification Report: ✅ ALL PASSED
- Overall Status: PASS
- Commands Executed: 3/3 passed
- Total Duration: 1250.0 ms
  * [PASS] python -m ruff check ... (Exit Code: 0)
  * [PASS] python -m mypy ... (Exit Code: 0)
  * [PASS] python -m pytest ... (Exit Code: 0)
```
```

---

## 4. Kết Luận & Các Bước Tiếp Theo
Toàn bộ kết quả đối thoại đã được sự nhất trí 100% của Kỹ sư trưởng và được thể chế hóa thành **ADR-0058**.
Ticket 5 đã hoàn thành toàn bộ mục tiêu phản biện kiến trúc và chuyển sang trạng thái **Closed (Done) ✅**.
