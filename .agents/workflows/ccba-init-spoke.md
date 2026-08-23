---
description: Khởi tạo một dự án (Spoke) tuân thủ kiến trúc CCBA Agent Platform
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
- BIM
- Tác vụ Admin
- Pháp điển
bundle: _core
disable-model-invocation: true
command: /ccba-init-spoke
triggers:
- init spoke
- setup project
- khởi tạo dự án
---
# Workflow: Khởi Tạo CCBA Spoke Workspace (/ccba-init-spoke)

Workflow này tự động hóa việc thiết lập một không gian làm việc (workspace) dự án mới để tuân thủ kiến trúc **CCBA Hub-and-Spoke** (ADR 0041, ADR 0044) và **Global Rules**.

---

## 🛡️ Bước 0: Rào Chắn An Toàn Dự Án Hiện Hữu (Brownfield Safety Guard)

> [!CAUTION]
> Nếu thư mục hiện tại **đã có sẵn mã nguồn hoặc cấu hình cũ** (có `workspace_context.yaml`, thư mục `.md/`, `.agents/`, hoặc `AGENTS.md`):
> - **TUYỆT ĐỐI KHÔNG** chạy tiếp `/ccba-init-spoke` để tránh ghi đè dữ liệu!
> - Hãy chuyển sang lệnh: **`/ccba-adopt-spoke`** để tự động tiếp nhận an toàn và bảo tồn 100% dữ liệu cũ.

---

## 📋 Bước 1: Khảo Sát & Tạo Cấu Hình `workspace_context.yaml`

1. **Lấy tên dự án:** Lấy tên thư mục hiện tại làm `project.name`.
2. **Xác định Archetype ([ADR 0041](../../docs/adr/0041-hub-spoke-ecosystem-taxonomy-and-archetypes.md)):**
   - `project_delivery` (Dự án tư vấn, thiết kế, thẩm tra công trình thực tế)
   - `enterprise_governance` (Hệ điều hành quản trị nội bộ / IDOP-CCBA-WAY)
   - `knowledge_corpus` (Kho tri thức pháp điển quốc gia OKF v2.0 / ccba-legal-knowledge)
   - `specialized_extension` (Khung mở rộng chuyên biệt):
     * `sub_type: personal_sandbox` (Không gian nghiên cứu, thử nghiệm & làm việc cá nhân theo Quy chế CCBA 2026)
     * `sub_type: research_lab` (Viện R&D, bài báo khoa học)
     * `sub_type: tooling_plugin` (Phát triển Add-in CAD/BIM)
     * `sub_type: client_portal` (Cổng Khách hàng Extranet)
3. **Xác định Loại dự án (`type` & `mode`):**
   - `Phần mềm` $\rightarrow$ mode: `software`, qc_mode: `null`
   - `Thẩm tra thiết kế` $\rightarrow$ mode: `delivery`, qc_mode: `third-party`
   - `Thiết kế` $\rightarrow$ mode: `delivery`, qc_mode: `internal`
   - `Kiểm định` $\rightarrow$ mode: `delivery`, qc_mode: `assessment`
   - `BIM` $\rightarrow$ mode: `delivery`, qc_mode: `internal`
   - `Tác vụ Admin` $\rightarrow$ mode: `admin`, qc_mode: `null`
   - `Pháp điển` $\rightarrow$ mode: `software`, qc_mode: `legal`
4. **Khởi tạo tệp `.md/workspace_context.yaml`:**

#### Mẫu A: Spoke Dự Án Kỹ Thuật (`project_delivery`)
```yaml
project:
  name: "2026-04-dh-viet-nhat"
  archetype: "project_delivery"
  type: "Thẩm tra thiết kế"
  mode: "delivery"
  qc_mode: "third-party"
  hub_path: "D:/GitHubProjects/ccba-agent-platform"
  description: "Dự án Thẩm tra Thiết kế PCCC & MEP Công trình ĐH Việt Nhật"
must_read:
  always:
    - path: .md/GLOSSARY.md
      why: "Thuật ngữ chuẩn hóa dự án"
do_not_touch: [.env]
acknowledgment_required: true
acknowledgment_format: "Tôi đã đọc workspace_context.yaml. Đây là Spoke Dự Án '[project_name]'. Sẵn sàng làm việc!"
```

#### Mẫu B: Spoke Cá Nhân (`specialized_extension` / `personal_sandbox` — Chuẩn Quy chế 2026)
```yaml
project:
  name: "chuvu-sandbox"
  archetype: "specialized_extension"
  sub_type: "personal_sandbox"
  hub_path: "D:/GitHubProjects/ccba-agent-platform"
  description: "Không gian nghiên cứu, thử nghiệm AI prompts & ươm tạo sáng kiến cá nhân"
organizational_identity:
  owner_name: "Chu Vũ"
  owner_email: "chuvu@ibst-bim.vn"
  department: "PHONG_RD_HTQT"                  # PHONG_TONG_HOP | PHONG_RD_HTQT | PHONG_BIM_THIET_KE | PHONG_BIM_DU_AN | PHONG_TV_KD_HCM | BAN_GIAM_DOC
  seat_role: "IDOP_LEAD"                       # 1 trong 11 Ghế giải trình theo Phụ lục 01 Quy chế 2026
qc_governance:
  authorized_qc_level: "LEVEL_1_TECHNICAL_CHECK" # LEVEL_1 đến LEVEL_5 theo Điều 13 Quy chế 2026
  can_sign_off_technical: true
idop_tasks:
  active_pgv_list:
    - pgv_code: "PGV-2026-08-014"
      task_name: "Nghiên cứu tối ưu hóa RAG pháp điển PCCC"
      max_advance_rate: 0.70                   # Hạn mức tạm ứng tối đa 70% theo Điều 17
guardrails:
  sandbox_mode: true
  prevent_direct_production_publish: true     # Hồ sơ chính thức phải kiểm soát 5 cấp theo Điều 13
  upstream_proposal_target: "main"
must_read:
  always:
    - path: d:/idop-ccba-way/.md/governance_constitution/03_ccba_charter_2026.md
      why: "Quy chế Tổ chức và Hoạt động CCBA 2026"
do_not_touch: [.env, "*.pfx", "*.key"]
```

> [!NOTE]
> **Vòng đời Spoke Cá Nhân (ADR 0046):**
> 1. **TTL 60 ngày:** Sandbox không hoạt động > 60 ngày sẽ dọn dẹp bởi `sweep_inactive_sandboxes()`.
> 2. **Thủy ấn & QC:** Mọi file tự động mang watermark `[CCBA SANDBOX DRAFT]`, giới hạn QC Cấp 1.
> 3. **Bàn giao PGV:** Dùng [`/ccba-promote-sandbox`](ccba-promote-sandbox.md) để chuyển giao sang dự án chính thức.

---

## 🔄 Bước 2: Đồng Bộ Kỹ Năng & Đăng Ký Spoke (Single-Engine Sync)

Agent chạy Deep Seam `SpokeSynchronizer`:
```powershell
python "[hub_path]\scripts\sync_spoke.py" --spoke .
```
*Tự động: tạo `.md/`, chọn bundle từ `catalog.yaml`, bơm skills/workflows, đồng bộ `AGENTS.md`, đăng ký RSA 2048-bit vào Hub Registry.*

---

## 📦 Bước 3: Thiết Lập Python Packages & Spoke Leakage Guard (ADR 0044, ADR 0045)

Đối với dự án có Python (`is_python_project = True`), khởi tạo môi trường liên kết:
```powershell
python "[hub_path]\scripts\spoke\spoke_bootstrap.py" --spoke .
```
*Tự động: sinh `requirements-hub.txt` kết nối editable packages (`ccba-ai`, `ccba-harness`...), cấu hình `.gitignore` cách ly.*

---

## 🔒 Bước 4: Cài Đặt Bảo Mật Maskara & Hoàn Tất

1. **Cài đặt Git Hook:** Tự động tạo pre-commit hook trong `.git/hooks/` gọi Maskara quét chặn lộ API keys.
2. **Xác nhận Onboarding (Global Rule 4):**
   > *"Tôi đã khởi tạo thành công Spoke `[tên_dự_án]` (Archetype: `[archetype]`, Type: `[type]`). Sẵn sàng làm việc!"*

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
