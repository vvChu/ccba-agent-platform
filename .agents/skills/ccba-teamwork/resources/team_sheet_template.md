# 📋 Team Sheet: [TÊN DỰ ÁN / TÍNH NĂNG]

> **Trạng thái:** DRAFT | ACTIVE | COMPLETED  
> **Orchestrator:** [Tên Agent / Phiên làm việc]  
> **Ngày khởi tạo:** [YYYY-MM-DD]  
> **Mục tiêu tổng quát:** [Mô tả ngắn gọn kết quả cần đạt của toàn bộ dự án]  
> **Non-Goals (Ranh giới loại trừ):** [Các hạng mục dứt khoát không thực hiện trong đợt này]

---

## 🏛️ Lớp 1: Accountability Mapping (Phân Quyền Phê Duyệt Con Người — ADR 0046)

> Ánh xạ các mốc bàn giao kỹ thuật (Milestones) với các Ghế trách nhiệm giải trình trong *Quy chế Tổ chức & Hoạt động CCBA 2026* (chọn các ghế phù hợp với phạm vi dự án).

| Milestone | Tên Mốc Bàn Giao | Ghế CCBA Chịu Trách Nhiệm Duyệt | Cấp QC Bắt Buộc | Tiêu Chí Ký Duyệt (Sign-off Criteria) |
|:---:|:---|:---|:---:|:---|
| **M1** | [Ví dụ: Bóc tách & Chuẩn hóa OKF] | `TRUONG_PHONG_RD_HTQT` | Cấp 1 (Technical) | 100% tests OKF parser pass, không rò rỉ secret |
| **M2** | [Ví dụ: Thẩm tra Thiết kế PCCC/MEP] | `CHU_TRI_BO_MON` | Cấp 2 (Governance) | Báo cáo đối soát đủ 4 bộ môn, đối chiếu QCVN 06 |
| **M3** | [Ví dụ: Đóng gói Báo cáo Nghiệm thu] | `CHU_TRI_HOP_DONG_PM` | Cấp 3 (Leadership) | Đối soát WBS, hoàn thành bàn giao PGV trên IDOP |
| **M4** | [Ví dụ: Thẩm định Pháp lý Tổng thể] | `CO_VAN_PHAP_LY_QA` | Cấp 4 (Legal/QA) | Không xung đột VBPL, trích dẫn chuẩn OKF v2.4 |

---

## ⚙️ Lớp 2: Worker Assignments (Phân Công AI Subagents Độc Quyền)

> **Nguyên tắc an toàn:**
> - Mỗi Worker chỉ đọc và phân tích files trong **Phạm Vi Seam (File Scope)** được cấp.
> - Workers là **Read-Only** (ADR 0035) — xuất artifact nháp vào `Sandbox Dir`.
> - **Duy nhất Orchestrator** được quyền tổng hợp, ghi file chính thức và commit Git.
> - **Giới hạn đồng thời:** Tối đa 3 workers/batch (Worker Cap).

### Batch 1: [Tên Đợt Thực Thi 1]

#### 🤖 Worker 1: `[worker-slug-1]`
- **Mục tiêu nhiệm vụ:** [Mô tả cụ thể công việc cần phân tích / dự thảo code]
- **Phạm vi Seam (Exclusive File Scope — Read Only):**
  - `[Đường dẫn file 1]`
  - `[Đường dẫn file 2]`
- **Sandbox Output Dir:** `.system_generated/scratch/worker_1/`
- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. [Tiêu chuẩn 1]
  2. [Tiêu chuẩn 2]
- **Chính sách Timeout:** 10 phút (Nếu quá hạn $\rightarrow$ Orchestrator fallback retry / escalate `/boost`)
- **Trạng thái:** `PENDING` | `IN_PROGRESS` | `COMPLETED` | `FAILED`

#### 🤖 Worker 2: `[worker-slug-2]`
- **Mục tiêu nhiệm vụ:** [Mô tả cụ thể]
- **Phạm vi Seam (Exclusive File Scope — Read Only):**
  - `[Đường dẫn file 3]`
  - `[Đường dẫn file 4]`
- **Sandbox Output Dir:** `.system_generated/scratch/worker_2/`
- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. [Tiêu chuẩn 1]
- **Chính sách Timeout:** 10 phút
- **Trạng thái:** `PENDING`

---

## 🔍 Lớp 3: Success Auditor Verification (Cổng Nghiệm Thu Độc Lập)

| Kiểm Tra | Lệnh / Công Cụ | Tiêu Chuẩn Đạt | Kết Quả |
|:---|:---|:---|:---:|
| **Scoped Test Suite** | `pytest [target_test_files]` | 100% Pass, thời gian < 2.0s/test | ⏳ PENDING |
| **Maskara Security Scan** | `python scripts/governance/check_spoke_leakage.py` | Exit code 0, không rò rỉ secrets | ⏳ PENDING |
| **Post-Merge Diff Audit** | `git diff --name-only` | Không sửa đổi file ngoài phạm vi Seam | ⏳ PENDING |
| **Catalog Compilation** | `python scripts/governance/compile_catalog.py` | Catalog SSOT đồng bộ hoàn toàn | ⏳ PENDING |

---

## 📝 Nhật Ký Tiến Độ (Progress Log)

- `[YYYY-MM-DD HH:MM]` Khởi tạo Team Sheet bởi Orchestrator.
