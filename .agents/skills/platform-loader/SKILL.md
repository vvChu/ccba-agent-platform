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

## Service Catalog (Source of Truth)

Toàn bộ thông tin về trigger keywords, đường dẫn (paths) và phân loại nghiệp vụ của Skills được định nghĩa duy nhất tại:
```text
.agents/skills/platform-loader/catalog.yaml
```
Agent bắt buộc phải đọc trực tiếp tệp `catalog.yaml` để lấy cấu hình mới nhất, không tự suy đoán hoặc sử dụng danh sách cũ.

---

## Routing Instructions

Khi nhận yêu cầu từ người dùng, Agent thực hiện theo logic sau:

### 1. Phân tích Trigger Keywords
Đọc `catalog.yaml`. Đối chiếu request của người dùng với các `triggers` trong catalog:
- Khớp skill $\rightarrow$ Đọc `skill_path` (`SKILL.md`) tương ứng để nạp kỹ năng.
- Nếu skill chưa có ở Spoke $\rightarrow$ Xem mục 3 (Lazy Loading Sync) hoặc áp dụng Virtual Hub Fallback.

### 2. Tự động áp dụng Rules
- Nếu kết quả đầu ra nhân danh CCBA $\rightarrow$ Nạp `.agents/rules/ccba_identity.md`.
- Nếu liên quan đến pháp luật hoặc văn bản pháp lý $\rightarrow$ Nạp `.agents/rules/legal_compliance.md`.
- Nếu tạo tệp tin hoặc thư mục mới $\rightarrow$ Nạp `.agents/rules/naming_conventions.md`.

### 3. Đồng bộ bổ sung kỹ năng (Lazy Loading Sync)
Khi Agent đang hoạt động tại Spoke và phát hiện yêu cầu cần sử dụng một skill có sẵn trên Hub nhưng chưa được đồng bộ cục bộ về Spoke:
1. Tra cứu `catalog.yaml` để tìm tên skill cần thiết.
2. Xin phép người dùng cài đặt bổ sung: *"Tôi cần tải bổ sung kỹ năng [tên-skill] từ Hub về Spoke để xử lý, bạn có đồng ý không?"*
3. Sau khi được đồng ý, xác định đường dẫn Hub (`hub_path`) từ `workspace_context.yaml` hoặc biến môi trường `CCBA_HUB_PATH` (mặc định sử dụng repository chung) và thực thi lệnh đồng bộ:
    ```bash
    python [hub_path]/scripts/sync_spoke.py --spoke . --sync-item <tên-skill> --apply
    ```
4. Sau khi đồng bộ thành công, Agent tự động nạp kỹ năng mới qua cơ chế Auto-Discovery và tiếp tục thực hiện công việc.

### 4. Quy tắc Định tuyến Xử lý Văn bản (Master vs Sub-Skill Routing)
Đối với các yêu cầu xử lý văn bản, tài liệu, hoặc file văn phòng:
- **Ưu tiên nạp Master Skill**:
  - Thao tác tệp Office (Word, Excel, PPT, PDF) $\rightarrow$ Nạp Master Skill `ccba-xu-ly-van-phong`.
  - Chuẩn hóa Markdown / PDF $\rightarrow$ Nạp Master Skill `ccba-markdown-document-processing`.
  - Soạn thảo hành chính / đề xuất thầu $\rightarrow$ Nạp Master Skill `ccba-copywriting`.
  - Viết bài báo khoa học $\rightarrow$ Nạp Master Skill `ccba-academic-writing`.
- **Nạp Sub-Skill / Utility khi cần thiết**: Nạp trực tiếp sub-skills (`ccba-pptx`, `../ccba-xu-ly-van-phong/references/docx_engine_guide.md`) khi cần xử lý thao tác vi mô. Đối với các tác vụ tái cấu trúc bảng, dọn dẹp template biểu mẫu, sửa liên kết tương đối, tham khảo tài liệu kỹ thuật Tier 2 trong `.agents/skills/ccba-markdown-document-processing/references/`.
