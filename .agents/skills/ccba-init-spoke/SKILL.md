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
tier: kernel
disable-model-invocation: true
command: /ccba-init-spoke
user-invocable: true
metadata:
  version: "1.2.0"
  author: "CCBA Hub"
gpi:
  s: 4.0
  k: 2.0
  a: 1.0
  p: 1.0
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
Kỹ năng này tự động hóa việc thiết lập không gian làm việc dự án mới theo chuẩn **CCBA Hub-and-Spoke** (ADR 0041, ADR 0044) và **Global Rules** qua cơ chế điều phối mỏng (Thin Orchestrator) tất định 100%.

---

## 🛡️ Bước 0: Chốt Chặn Từ Chối Cứng (Hard Refusal Gate & Multi-Device Protection)
> [!CAUTION]
> **Hiến pháp Single-User Multi-Device & Machine-State Decoupling:**
> 1. Nếu phát hiện tệp tin `workspace_context.yaml` **ĐÃ TỒN TẠI** (trong `.md/` hoặc `.agents/`):
>    - Agent **BẮT BUỘC DỪNG LẠI NGAY LẬP TỨC**, tuyệt đối không chạy tiếp các bước sau.
>    - **CẤM TUYỆT ĐỐI** gợi ý chuyển sang `/ccba-spoke-adopter` (vì Spoke này đã được cấu hình từ máy khác).
>    - Hướng dẫn người dùng chuyển sang lệnh bootstrap môi trường làm việc:
>      - Trên Linux / macOS / WSL:
>        ```bash
>        python3 "$CCBA_HUB_PATH/scripts/ccba_platform_cli.py" bootstrap-spoke --create-venv
>        ```
>      - Trên Windows PowerShell:
>        ```powershell
>        python "$env:CCBA_HUB_PATH/scripts/ccba_platform_cli.py" bootstrap-spoke --create-venv
>        ```
> 2. Nếu thư mục **CHƯA CÓ** `workspace_context.yaml` nhưng **ĐÃ CÓ** mã nguồn hoặc cấu trúc dự án (Brownfield):
>    - Chuyển hướng sang kỹ năng: **`/ccba-spoke-adopter`** để phân tích hiện trạng và tiếp nhận không phá hủy.
> 3. Chỉ tiếp tục Bước 1 của `/ccba-init-spoke` khi thư mục hoàn toàn mới tinh (Greenfield).

**Tiêu chí hoàn thành:** Dừng lại an toàn và hiển thị lệnh bootstrap nếu đã có context; chuyển hướng sang adopter nếu là brownfield chưa cấu hình; hoặc tiếp tục bước 1 nếu là greenfield mới tinh.

---

## 📋 Bước 1: Khởi Tạo Dự Án Tất Định (Deterministic Spoke Initialization CLI)

Agent **BẮT BUỘC** gọi Deep Seam / CLI tất định thay vì tự sinh chuỗi YAML trong prompt (ADR-0058):

### Lệnh thực thi chuẩn:
```bash
python scripts/ccba_platform_cli.py init-spoke \
  --name "<project_name>" \
  --archetype "<project_delivery|enterprise_governance|knowledge_corpus|specialized_extension>" \
  --type "<project_type>" \
  --mode "<software|delivery|admin|consulting|hybrid>"
```
*(hoặc sử dụng wrapper `python scripts/init_spoke.py ...`)*

### Các tùy chọn khởi tạo theo Archetype:
1. **`project_delivery`** (Dự án tư vấn, thiết kế, thẩm tra công trình thực tế):
   ```bash
   python scripts/ccba_platform_cli.py init-spoke --archetype project_delivery --type "Thẩm tra thiết kế" --mode delivery
   ```
2. **`specialized_extension` / `personal_sandbox`** (Không gian nghiên cứu, thử nghiệm cá nhân theo Quy chế CCBA 2026):
   ```bash
   python scripts/ccba_platform_cli.py init-spoke --archetype specialized_extension --sub-type personal_sandbox --type "Phần mềm" --mode software
   ```
3. **`knowledge_corpus`** (Kho tri thức pháp điển quốc gia OKF v2.4 Universal):
   ```bash
   python scripts/ccba_platform_cli.py init-spoke --archetype knowledge_corpus --type "Pháp điển" --mode software
   ```
4. **`enterprise_governance`** (Hệ điều hành quản trị nội bộ IDOP):
   ```bash
   python scripts/ccba_platform_cli.py init-spoke --archetype enterprise_governance --type "Tác vụ Admin" --mode admin
   ```

*Lệnh CLI trên tự động thực thi tất định 100%: tạo khung thư mục `.md/`, sinh `.md/INDEX.md`, tạo `workspace_context.yaml` chuẩn hóa, thiết lập `.gitignore` chống rò rỉ (ADR-0045), cấu hình Virtual Hub Fallback trong `.agents/AGENTS.md`, và cài Git Hook Maskara nếu có Git.*

> [!TIP]
> Bạn có thể kết hợp khởi tạo, đồng bộ kỹ năng và tạo môi trường ảo Python trong một lệnh duy nhất:
> ```bash
> python scripts/ccba_platform_cli.py init-spoke --archetype project_delivery --sync --bootstrap
> ```

**Tiêu chí hoàn thành:** Chạy thành công lệnh `init-spoke` qua `ccba_platform_cli.py` (hoặc `init_spoke.py`), tệp `.md/workspace_context.yaml` và cấu trúc thư mục được khởi tạo tất định.

---

## 🔄 Bước 2: Đồng Bộ Kỹ Năng & Đăng Ký Spoke (Single-Engine Sync)

Nếu chưa chỉ định cờ `--sync` tại Bước 1, Agent chạy Deep Seam `SpokeSynchronizer`:
```powershell
python "[hub_path]\scripts\sync_spoke.py" --spoke .
```
*Tự động: tạo `.md/`, chọn bundle từ `catalog.yaml`, bơm kỹ năng, đồng bộ `AGENTS.md`, đăng ký RSA 2048-bit vào Hub Registry.*

**Tiêu chí hoàn thành:** Chạy thành công `sync_spoke.py` để đồng bộ kỹ năng và đăng ký Spoke.

---

## 📦 Bước 3: Thiết Lập Python Packages & Spoke Leakage Guard (ADR 0044, ADR 0045)

Nếu chưa chỉ định cờ `--bootstrap` tại Bước 1, đối với dự án có Python (`is_python_project = True`), khởi tạo môi trường liên kết:
```powershell
python "[hub_path]\scripts\spoke\spoke_bootstrap.py" --spoke .
```
*Tự động: sinh `requirements-hub.txt` kết nối editable packages (`ccba-ai`, `ccba-harness`...), cấu hình `.gitignore` cách ly.*

**Tiêu chí hoàn thành:** Hoàn thành thiết lập môi trường Python liên kết và rào chắn cô lập Spoke.

---

## 🔒 Bước 4: Kiểm Tra Bảo Mật Maskara & Hoàn Tất Onboarding

1. **Xác nhận Git Hook:** Lệnh `init-spoke` đã tự động cài pre-commit hook trong `.git/hooks/` (nếu repo có Git).
2. **Xác nhận Onboarding (Global Rule 4):**
   > *"Tôi đã khởi tạo thành công Spoke `[tên_dự_án]` (Archetype: `[archetype]`, Type: `[type]`). Sẵn sàng làm việc!"*

**Tiêu chí hoàn thành:** Xác nhận Git Hook Maskara hoạt động an toàn và xuất thông báo xác nhận onboarding.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/interactive_wizard.md` | Kịch bản hướng dẫn tương tác từng bước khi khởi tạo dự án Spoke mới |
| `references/server_deployment.md` | Hướng dẫn triển khai cấu hình server và hạ tầng phục vụ Agent |
