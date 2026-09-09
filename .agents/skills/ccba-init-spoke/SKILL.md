---
name: ccba-init-spoke
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
- ccba-wizard
- wizard
- ccba-server-deploy
- server-deploy
---

# Kỹ Năng: Khởi Tạo CCBA Spoke Workspace (/ccba-init-spoke)
Kỹ năng này tự động hóa việc thiết lập không gian làm việc dự án mới theo chuẩn **CCBA Hub-and-Spoke** (ADR 0041, ADR 0044) và **Global Rules**.

---

## 🛡️ Bước 0: Rào Chắn An Toàn Dự Án Hiện Hữu (Brownfield Safety Guard)
> [!CAUTION]
> Nếu thư mục hiện tại **đã có sẵn mã nguồn hoặc cấu hình cũ** (có `workspace_context.yaml`, `.md/`, `.agents/`):
> - **TUYỆT ĐỐI KHÔNG** chạy tiếp `/ccba-init-spoke` để tránh ghi đè dữ liệu!
> - Hãy chuyển sang lệnh: **`/ccba-spoke-adopter`** để tự động tiếp nhận an toàn và bảo tồn 100% dữ liệu cũ.

**Tiêu chí hoàn thành:** Kiểm tra thư mục hiện tại không có dữ liệu cũ cần bảo vệ hoặc chuyển hướng sang ccba-spoke-adopter.

---

## 📋 Bước 1: Khảo Sát & Tạo Cấu Hình `workspace_context.yaml`

1. **Lấy tên dự án:** Lấy tên thư mục hiện tại làm `project.name`.
2. **Xác định Archetype ([ADR 0041](../../../docs/adr/0041-hub-spoke-ecosystem-taxonomy-and-archetypes.md)):**
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
  always: [{path: .md/GLOSSARY.md, why: "Thuật ngữ chuẩn hóa dự án"}]
do_not_touch: [.env]
acknowledgment_required: true
acknowledgment_format: "Tôi đã đọc workspace_context.yaml. Đây là Spoke Dự Án '[project_name]'. Sẵn sàng làm việc!"
```

#### Mẫu B: Spoke Cá Nhân (`specialized_extension` / `personal_sandbox` — Quy chế 2026)
```yaml
project:
  name: "chuvu-sandbox"
  archetype: "specialized_extension"
  sub_type: "personal_sandbox"
  hub_path: "D:/GitHubProjects/ccba-agent-platform"
  description: "Không gian nghiên cứu & làm việc cá nhân theo Quy chế CCBA 2026"
organizational_identity:
  owner_name: "Chu Vũ"
  owner_email: "chuvu@ibst-bim.vn"
  department: "PHONG_RD_HTQT"
  seat_role: "IDOP_LEAD"
qc_governance:
  authorized_qc_level: "LEVEL_1_TECHNICAL_CHECK"
  can_sign_off_technical: true
guardrails:
  sandbox_mode: true
  prevent_direct_production_publish: true
  upstream_proposal_target: "main"
must_read:
  always: [{path: d:/idop-ccba-way/.md/governance_constitution/03_ccba_charter_2026.md, why: "Quy chế 2026"}]
do_not_touch: [.env, "*.pfx", "*.key"]
```

#### Mẫu C: Spoke Kho Tri Thức Pháp Điển (`knowledge_corpus` / `Pháp điển`)
```yaml
project:
  name: "ccba-legal-knowledge"
  archetype: "knowledge_corpus"
  type: "Pháp điển"
  mode: "software"
  qc_mode: "legal"
  hub_path: "D:/GitHubProjects/ccba-agent-platform"
  description: "Kho Tri thức Pháp điển & Quy chuẩn Xây dựng Quốc gia (OKF v2.4 Universal Agent-Centric)"
hub_packages: [ccba-legal-intel, ccba-notebooklm]
must_read:
  always: [{path: .md/GLOSSARY.md, why: "Thuật ngữ pháp lý chuẩn hóa"}]
do_not_touch: [.env]
acknowledgment_required: true
acknowledgment_format: "Tôi đã đọc workspace_context.yaml. Đây là Spoke Kho Tri Thức '[project_name]'. Sẵn sàng làm việc!"
```

> [!NOTE]
> **Quy chuẩn Spoke Tri thức (ADR 0036, ADR 0044 & Issue #215):**
> 1. **Cấu trúc OKF v2.4 Universal (ADR 0036):** Bắt buộc có ngăn kéo `sources/` (chứa PDF/DOCX gốc) và 4 ngăn chuyên biệt (`tables/`, `figures/`, `annexes/`, `templates/`). Tuyệt đối cấm để thư mục `templates/` rỗng.
> 2. **Gate 0 Ingestion Provenance (ADR 0016):** Tự động đối soát cấu trúc và Text Parity giữa DOCX và PDF Công báo qua `ccba_legal.provenance`.
> 3. **Script Budget & Cleanliness (ADR 0044):** Duy trì $\le 15$ core scripts trong `scripts/`. Tái sử dụng `ccba_legal` và `ccba_ai` từ Hub qua `spoke_bootstrap.py`. Chặn wrapper thừa qua `check_spoke_cleanliness.py`.

**Tiêu chí hoàn thành:** Tệp `.md/workspace_context.yaml` được khởi tạo đúng archetype và cấu hình dự án.

---

## 🔄 Bước 2: Đồng Bộ Kỹ Năng & Đăng Ký Spoke (Single-Engine Sync)

Agent chạy Deep Seam `SpokeSynchronizer`:
```powershell
python "[hub_path]\scripts\sync_spoke.py" --spoke .
```
*Tự động: tạo `.md/`, chọn bundle từ `catalog.yaml`, bơm kỹ năng, đồng bộ `AGENTS.md`, đăng ký RSA 2048-bit vào Hub Registry.*

> [!TIP]
> Bạn có thể gộp Bước 2 & Bước 3 với cờ `--bootstrap` (`-b`):
> ```powershell
> python "[hub_path]\scripts\sync_spoke.py" --spoke . --apply --bootstrap
> ```

**Tiêu chí hoàn thành:** Chạy thành công `sync_spoke.py` để đồng bộ kỹ năng và đăng ký Spoke.

---

## 📦 Bước 3: Thiết Lập Python Packages & Spoke Leakage Guard (ADR 0044, ADR 0045)

Đối với dự án có Python (`is_python_project = True`), khởi tạo môi trường liên kết:
```powershell
python "[hub_path]\scripts\spoke\spoke_bootstrap.py" --spoke .
```
*Tự động: sinh `requirements-hub.txt` kết nối editable packages (`ccba-ai`, `ccba-harness`...), cấu hình `.gitignore` cách ly.*

**Tiêu chí hoàn thành:** Hoàn thành thiết lập môi trường Python liên kết và rào chắn cô lập Spoke.

---

## 🔒 Bước 4: Cài Đặt Bảo Mật Maskara & Hoàn Tất

1. **Cài đặt Git Hook:** Tự động tạo pre-commit hook trong `.git/hooks/` gọi Maskara quét chặn lộ API keys.
2. **Xác nhận Onboarding (Global Rule 4):**
   > *"Tôi đã khởi tạo thành công Spoke `[tên_dự_án]` (Archetype: `[archetype]`, Type: `[type]`). Sẵn sàng làm việc!"*

**Tiêu chí hoàn thành:** Cài đặt git hook quét Maskara và xuất thông báo xác nhận onboarding.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/interactive_wizard.md` | Kịch bản hướng dẫn tương tác từng bước khi khởi tạo dự án Spoke mới |
| `references/server_deployment.md` | Hướng dẫn triển khai cấu hình server và hạ tầng phục vụ Agent |

