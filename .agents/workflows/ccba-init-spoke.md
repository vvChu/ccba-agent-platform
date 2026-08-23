---
description: Khởi tạo một dự án (Spoke) tuân thủ kiến trúc CCBA Agent Platform
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
  - "Tác vụ Admin"
bundle: "_core"
disable-model-invocation: true
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
ai_preferences:
  gateway_endpoint: "http://100.83.192.30:8090/v1"
  default_chat_model: "gemini-3.7-flash"
  reasoning_model: "gemini-3.7-flash-high"
guardrails:
  sandbox_mode: true
  prevent_direct_production_publish: true     # Hồ sơ chính thức phải kiểm soát 5 cấp theo Điều 13
  upstream_proposal_target: "main"
must_read:
  always:
    - path: d:/idop-ccba-way/.md/governance_constitution/03_ccba_charter_2026.md
      why: "Quy chế Tổ chức và Hoạt động CCBA 2026"
do_not_touch: [.env, "*.pfx", "*.key"]
acknowledgment_required: true
acknowledgment_format: "Xin chào [owner_name] ([seat_role] thuộc [department]). Sẵn sàng hỗ trợ các nhiệm vụ PGV!"
```

---

## 🔄 Bước 2: Đồng Bộ Kỹ Năng & Đăng Ký Spoke (Single-Engine Sync)

Agent xác định đường dẫn Hub (`hub_path`) và chạy Deep Seam `SpokeSynchronizer`:
```powershell
python "[hub_path]\scripts\sync_spoke.py" --spoke .
```

*Động cơ sẽ tự động:*
- Tạo cấu trúc thư mục tri thức `.md/` chuẩn theo mode.
- Đọc `workspace_context.yaml` để chọn bundle kỹ năng phù hợp từ `catalog.yaml`.
- Bơm các skills/workflows chuẩn vào `.agents/skills/` và `.agents/workflows/`.
- Đồng bộ hiến pháp `.agents/AGENTS.md` và sao chép bộ rào chắn test (`conftest.py`, `safe_pytest.py`).
- Đăng ký Spoke với khóa mã hóa RSA 2048-bit vào Hub Registry.

---

## 📦 Bước 3: Thiết Lập Python Packages & Spoke Leakage Guard (ADR 0044, ADR 0045)

Đối với các dự án có Python (`is_python_project = True`), khởi tạo môi trường liên kết:
```powershell
python "[hub_path]\scripts\spoke\spoke_bootstrap.py" --spoke .
```

*Động cơ sẽ tự động:*
- Phân tích và sinh `requirements-hub.txt` kết nối editable packages (`ccba-ai`, `ccba-harness`, `ccba-legal-intel`...).
- Tự động cấu hình `.gitignore` cách ly `requirements-hub.txt` và rào chắn rò rỉ `.md/teach/`, `.tmp/`, `.out-of-scope/`.

---

## 🔒 Bước 4: Cài Đặt Bảo Mật Maskara & Hoàn Tất

1. **Cài đặt Git Hook bảo mật:** Tự động tạo pre-commit hook trong `.git/hooks/` gọi Maskara quét chặn lộ API keys.
2. **Xác nhận Onboarding (Global Rule 4):**
   Agent in câu chào mừng:
   > *"Tôi đã khởi tạo thành công Spoke `[tên_dự_án]` (Archetype: `[archetype]`, Type: `[type]`). Toàn bộ kỹ năng, rào chắn an toàn và môi trường đã sẵn sàng!"*

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
