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
   - `specialized_extension` (R&D Lab, Add-in CAD-BIM, Client Extranet Portal)
3. **Xác định Loại dự án (`type` & `mode`):**
   - `Phần mềm` $\rightarrow$ mode: `software`, qc_mode: `null`
   - `Thẩm tra thiết kế` $\rightarrow$ mode: `delivery`, qc_mode: `third-party`
   - `Thiết kế` $\rightarrow$ mode: `delivery`, qc_mode: `internal`
   - `Kiểm định` $\rightarrow$ mode: `delivery`, qc_mode: `assessment`
4. **Khởi tạo tệp `.md/workspace_context.yaml`:**
   Ghi nhận cấu hình `project`, `must_read` (`.md/GLOSSARY.md`), `do_not_touch` (`.env`), và `acknowledgment_required: true`.

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
