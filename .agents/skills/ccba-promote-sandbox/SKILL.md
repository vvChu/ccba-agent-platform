---
name: ccba-promote-sandbox

description: Thăng cấp và bàn giao sản phẩm từ Spoke Cá Nhân sang Spoke Dự Án hoặc
  Hub (ADR 0046)
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
- Tác vụ Admin
bundle: _core
tier: kernel
disable-model-invocation: true
command: /ccba-promote-sandbox
user-invocable: true
gpi:
  s: 3.0
  k: 3.0
  a: 1.0
  p: 1.0
triggers:
- promote sandbox
- bàn giao sandbox
- thăng cấp sản phẩm
- nghiệm thu pgv
- pgv handover
---
# Workflow: Thăng Cấp & Bàn Giao Sản Phẩm Từ Sandbox (/ccba-promote-sandbox)

Workflow này hướng dẫn kỹ sư thực hiện quy trình thăng cấp bàn giao 3 bước để chuyển giao sản phẩm nghiên cứu, bản tính hoặc báo cáo từ **Spoke Cá Nhân (`personal_sandbox`)** sang **Spoke Dự Án chính thức (`project_delivery`)** hoặc đề xuất lên Hub theo **ADR 0046** và **Quy chế CCBA 2026**.

---

## 🛡️ Bước 1: Khảo Sát & Xác Thực Môi Trường Nguồn

1. Agent đọc tệp `.md/workspace_context.yaml` tại thư mục hiện tại.
2. **Kiểm tra điều kiện tiên quyết:**
   - Workspace phải được cấu hình là Spoke Cá Nhân (`sub_type: personal_sandbox` hoặc `guardrails.sandbox_mode: true`).
   - Nếu không phải sandbox, Agent thông báo:
     > *"Thư mục hiện tại không phải là Spoke Cá Nhân. Quy trình này chỉ áp dụng cho môi trường sandbox."*

**Tiêu chí hoàn thành:** Xác thực môi trường hiện tại là Spoke Cá Nhân hợp lệ.

---

## 📋 Bước 2: Xác Định Sản Phẩm & Dự Án Đích

Agent hỗ trợ kỹ sư xác định các tham số bàn giao:

1. **Danh sách tệp bàn giao (`--files`):**
   - Quét các tệp hoàn thiện trong `output/`, `specs/`, `scripts/` (ví dụ: `output/pccc_audit_report.md`).
2. **Đường dẫn Spoke Dự Án đích (`--target`):**
   - Đường dẫn thư mục của Spoke Dự Án thụ hưởng (ví dụ: `D:/GitHubProjects/2026-04-dh-viet-nhat`).
   - *Nếu là công cụ/script dùng chung:* Hướng dẫn kỹ sư sử dụng lệnh `/ccba-contribute-to-hub` thay thế.
3. **Mã Phiếu Giao Việc (`--pgv`):**
   - Mã PGV được phân công trên IDOP (ví dụ: `PGV-2026-08-014`).

**Tiêu chí hoàn thành:** Xác định đầy đủ danh sách tệp bàn giao, Spoke đích và mã PGV.

---

## ⚙️ Bước 3: Thực Thi Thăng Cấp 3 Bước (Single-Command Promotion)

Agent xác định đường dẫn Hub (`hub_path`) và thực thi lệnh thăng cấp:

```powershell
python "[hub_path]\scripts\promote_sandbox.py" --target "[duong_dan_spoke_dich]" --files [danh_sach_tep] --pgv "[ma_pgv]"
```

*Động cơ `SandboxPromoter` sẽ tự động thực hiện tuần tự:*
1. **Pha 1 (Cleanse & Validate):** Rà soát và gỡ bỏ hoàn toàn thủy ấn `[CCBA SANDBOX DRAFT]` để chuẩn hóa thành phẩm.
2. **Pha 2 (Target Ingestion):** Sao chép tệp sạch sang Spoke Dự Án đích, tự động tạo thư mục cha và tính mã băm SHA-256 bất biến.
3. **Pha 3 (PGV Sign-off Staging):** Tạo biên nhận `.md/idop_staged/pgv_handover_[pgv]_[timestamp].json` lưu trữ thông tin kỹ sư (`owner_name`, `seat_role`) và commit SHA để phục vụ nghiệm thu trên SharePoint IDOP.

**Tiêu chí hoàn thành:** Lệnh promote_sandbox.py hoàn tất cả 3 pha và tạo biên nhận IDOP thành công.

---

## 🎯 Bước 4: Hướng Dẫn Nghiệm Thu & Giải Ngân Tầng 3 (Điều 17 Quy Chế 2026)

Agent in báo cáo xác nhận thành công:
> ✅ **Đã bàn giao thành công `[so_tep]` tệp sang Spoke `[ten_du_an_dich]`.**
> 📋 **Biên nhận nghiệm thu IDOP:** `[duong_dan_receipt]`
> 
> 💡 **Bước tiếp theo:** Vui lòng thông báo cho Chủ nhiệm Hợp đồng (`CHU_TRI_HOP_DONG_PM`) hoặc Trưởng phòng chuyên môn để thực hiện kiểm tra Cấp 2 và phê duyệt nghiệm thu Phiếu Giao Việc `[ma_pgv]` trên hệ thống IDOP.

**Tiêu chí hoàn thành:** In báo cáo xác nhận bàn giao và hướng dẫn nghiệm thu PGV.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*\n