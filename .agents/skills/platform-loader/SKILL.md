---
name: platform-loader
description: Bootstrap skill cho CCBA Agent Services Platform. Đọc file này để biết
  toàn bộ skills và rules.
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
tier: kernel
command: /platform-loader
user-invocable: true
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
gpi:
  s: 2.0
  k: 3.0
  a: 4.0
  p: 1.0
triggers:
- platform
- bootstrap
- load skills
- danh sách lệnh
---
# CCBA Platform Loader

> **Vai trò**: Đây là điểm khởi đầu duy nhất cho Agent để truy cập toàn bộ dịch vụ của CCBA Platform.
> Đọc file này MỘT LẦN khi bắt đầu phiên để xác định tài nguyên khả dụng và route task chính xác.

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`seam-exempt`** (catalog và định tuyến toàn sàn). Skill đóng vai trò điểm khởi đầu bootstrap và discovery catalog toàn diện cho Platform, phân biệt rạch ròi giữa `catalog.yaml` (routing & triggers) với biên lai hợp đồng kiểm toán `--in/--out` (`seam-contracts.yaml`), không đóng gói pipeline chuyển đổi dữ liệu hay phụ thuộc Seam Contract ứng dụng cụ thể.

---

## Service Catalog & Seam Indexes (Source of Truth)

Để định tuyến chính xác và không bị nhầm lẫn giữa kỹ năng (Skills) và mã nguồn thư viện (Python Deep Seams), Agent cần phân biệt rạch ròi giữa **3 chỉ mục hệ thống**:

| Câu hỏi của Agent | Chỉ mục tra cứu | Công cụ / Lệnh | Bản chất kết quả |
| :--- | :--- | :--- | :--- |
| **"Người dùng muốn thực hiện lệnh/nghiệp vụ nào, cần nạp skill nào?"** | `catalog.yaml` (mục `skills`, `workflows`, `bundles`) | Đọc file hoặc khớp `triggers` | Định tuyến kỹ năng và lọc danh mục đồng bộ Spoke. |
| **"Package nội bộ nào đã công bố symbol gì trong `packages/*/AGENTS.md`?"** | `catalog.yaml` (mục `seams`) | `ccba-platform find-seam <từ-khóa>` (truy vấn vị trí) | Chỉ là **manh mối tìm kiếm (`status: KEYWORD_HINT`)**. CẤM dùng mã băm SHA của KEYWORD_HINT làm biên lai hợp đồng kiểm toán. |
| **"Đã có hợp đồng biến đổi dữ liệu `in → out` chưa, có cấm thư viện thay thế nào?"** | `seam-contracts.yaml` (ADR-0061) | `ccba-platform find-seam --in <types> --out <types> [--json]` | Chỉ kết quả `status: MATCH` kèm `index_sha256` mới là **Biên lai Kiểm toán Hợp đồng (Audit Receipt)**. |

---

## Routing Instructions

Khi nhận yêu cầu từ người dùng, Agent thực hiện định tuyến theo thứ tự ưu tiên:

### 1. Phân định Bản chất Yêu cầu
- **Yêu cầu nghiệp vụ hoặc tác vụ AI** ("đồng bộ spoke", "so sánh kiến trúc", "thẩm tra PCCC", "soạn thảo hồ sơ hoàn thành") $\rightarrow$ Tra cứu `catalog.yaml` theo `triggers` để nạp `SKILL.md` tương ứng.
- **Yêu cầu viết mã nguồn xử lý dữ liệu mới** ("viết script chuyển PDF sang Markdown", "đọc file docx", "gọi LLM") $\rightarrow$ BẮT BUỘC tra cứu Seam Contracts qua CLI: `ccba-platform find-seam --in <types> --out <types>`. Nếu có Seam sẵn $\rightarrow$ Tái sử dụng; cấm viết script chắp vá cục bộ.

### 2. Tự động áp dụng Rules
- Nếu kết quả đầu ra nhân danh CCBA $\rightarrow$ Nạp `.agents/rules/ccba_identity.md`.
- Nếu liên quan đến pháp luật hoặc văn bản pháp lý $\rightarrow$ Nạp `.agents/rules/legal_compliance.md`.
- Nếu tạo tệp tin hoặc thư mục mới $\rightarrow$ Nạp `.agents/rules/naming_conventions.md`.

### 3. Khai thác Kỹ năng tại Spoke: Fallback vs Đồng bộ Vật lý
Khi Agent đang hoạt động tại Spoke và phát hiện kỹ năng cần dùng chưa có sẵn trong thư mục cục bộ `.agents/skills/`:
- **Pha 1 — Virtual Hub Fallback (Đọc tri thức tức thì):**
  Agent đọc trực tiếp nội dung định nghĩa kỹ năng từ kho Hub thông qua biến môi trường `$CCBA_HUB_PATH`:
  `view_file "$CCBA_HUB_PATH/.agents/skills/<tên-kỹ-năng>/SKILL.md"`
  *(Bước này giúp Agent nắm ngay quy trình nghiệp vụ mà không cần làm bẩn git working tree của Spoke).*
- **Pha 2 — Đồng bộ Vật lý Kỹ năng (Lazy Loading Sync qua `--sync-item`):**
  Khi cần sao chép tệp kỹ năng vật lý về Spoke:
  1. Xin phép người dùng: *"Tôi cần tải bổ sung kỹ năng [tên-kỹ-năng] từ Hub về Spoke để xử lý, bạn có đồng ý không?"*
  2. Thực thi lệnh đồng bộ an toàn:
     ```bash
     # POSIX (Linux / macOS / WSL):
     python "$CCBA_HUB_PATH/scripts/sync_spoke.py" --spoke . --sync-item <tên-kỹ-năng> --apply

     # PowerShell (Windows):
     python "$env:CCBA_HUB_PATH\scripts\sync_spoke.py" --spoke . --sync-item <tên-kỹ-năng> --apply
     ```
  3. *Lưu ý quan trọng:* Cờ `--sync-item` **chỉ sao chép duy nhất mục kỹ năng được chỉ định và cập nhật hiến pháp `AGENTS.md`**, hoàn toàn **KHÔNG cài đặt git hooks (Maskara pre-commit) hay guardrails bảo vệ**.
- **Pha 3 — Đồng bộ Toàn diện & Cài đặt Rào chắn Bảo vệ (Full Bundle Sync):**
  Nếu Spoke cần kích hoạt toàn bộ pre-commit hooks bảo mật, linter gates và rào chắn test, bắt buộc phải chạy lệnh đồng bộ đầy đủ:
  ```bash
  # POSIX:
  python "$CCBA_HUB_PATH/scripts/sync_spoke.py" --spoke . --apply
  ```
  ```powershell
  # PowerShell:
  python "$env:CCBA_HUB_PATH\scripts\sync_spoke.py" --spoke . --apply
  ```

### 4. Quy tắc Định tuyến Xử lý Văn bản (Master vs Sub-Skill Routing)
Đối với các yêu cầu xử lý văn bản, tài liệu, hoặc file văn phòng:
- **Ưu tiên nạp Master Skill**:
  - Thao tác tệp Office (Word, Excel, PPT, PDF) $\rightarrow$ Nạp Master Skill `ccba-xu-ly-van-phong`.
  - Chuẩn hóa Markdown / PDF $\rightarrow$ Nạp Master Skill `ccba-markdown-document-processing`.
  - Soạn thảo hành chính / đề xuất thầu $\rightarrow$ Nạp Master Skill `ccba-copywriting`.
  - Viết bài báo khoa học $\rightarrow$ Nạp Master Skill `ccba-academic-writing`.
- **Nạp Sub-Skill / Utility khi cần thiết**: Nạp trực tiếp sub-skills (`ccba-pptx`, `../ccba-xu-ly-van-phong/references/docx_engine_guide.md`) khi cần xử lý thao tác vi mô. Đối với các tác vụ tái cấu trúc bảng, dọn dẹp template biểu mẫu, sửa liên kết tương đối, tham khảo tài liệu kỹ thuật Tier 2 trong `.agents/skills/ccba-markdown-document-processing/references/`.
