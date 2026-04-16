---
description: Khởi tạo một dự án (Spoke) tuân thủ kiến trúc CCBA Agent Platform
---

# Khởi tạo CCBA Spoke Workspace

Workflow này tự động hóa việc thiết lập một không gian làm việc (workspace) dự án mới để tuân thủ kiến trúc **CCBA Hub-and-Spoke** và **Global Rules**. Bạn nên chạy command `/init-ccba-spoke` ngay khi mở một thư mục dự án trên IDE (đặc biệt là các dự án tư vấn, quản lý cấu hình, QC).

Vui lòng thực hiện tuần tự các bước sau:

## Các bước thực hiện:

1. **Khởi tạo cấu trúc Knowledge Base (Global Rule 1)**:  
   Sử dụng công cụ `run_command` để tạo luôn kiến trúc thư mục `.md` bằng PowerShell:
   ```powershell
   New-Item -ItemType Directory -Force -Path ".md\extracted_docs" | Out-Null
   ```

2. **Ghi nhận tên dự án**:  
   Để file cấu hình được cá nhân hóa cho từng thư mục, sử dụng `run_command` lệnh sau để lấy tên thư mục Root:
   ```powershell
   (Get-Item .).Name
   ```

3. **Tạo file Workspace Context**:  
   Sử dụng công cụ `write_to_file` kết hợp với kết quả từ Bước 2 để tạo và ghi nội dung vào file `.md\workspace_context.yaml` (Lưu ý: Hãy hỏi người dùng loại dự án là gì, hoặc mặc định ghi là "Verification & Design Management"):
   ```yaml
   project_name: "<Tên thư mục dự án vừa lấy được>"
   type: "<Xác định loại dự án hoặc mặc định: Verification & Design Management>"
   related_hub_services:
     - platform-loader
     - mdconverter
   agent_boundaries:
     allowed_read_paths:
       - "*" # Được phép đọc toàn bộ Workspace để thu thập thông tin
     allowed_write_paths:
       - # Khai báo Cụ Thể thư mục triển khai (Ví dụ: "2024-04 Ban DD HCM - BV NTP")
     strict_mode: true # Khi bật, Agent bị cấm dùng lệnh tạo file, ghi file hoặc chạy script làm thay đổi dữ liệu nằm ngoài allowed_write_paths
   context: "Agent có đặc quyền truy cập mọi tài liệu (Hợp đồng, Đấu thầu, Thiết kế), nhưng MỌI thao tác ghi/tạo sửa file đều phải nằm gọn trong thư mục triển khai dự án được chỉ định."
   ```

4. **Trích xuất tài liệu (Extraction) - Quét**:  
   Kiểm tra xem dự án hiện tại có file raw (Word/PDF) nào chưa xử lý không. Sử dụng lệnh PowerShell (tìm với độ sâu tới 3 cấp):
   ```powershell
   Get-ChildItem -Path . -Recurse -Depth 3 | Where-Object { $_.Extension -match "\.(pdf|docx)$" } | Select-Object Name
   ```

5. **Đồng bộ hóa Giao diện Lệnh IDE (Copy toàn bộ từ Hub)**:
   Copy toàn bộ thư mục `.agent` từ Hub về thư mục `.agents` tại dự án (Spoke) hiện tại để IDE nhận diện lệnh. Việc này tạo bản sao cục bộ, để cập nhật trong tương lai bạn cần gọi riêng workflow cập nhật. Sử dụng công cụ `run_command` để chạy PowerShell:
   ```powershell
   Copy-Item -Path "D:\GitHubProjects\ccba-agent-platform\.agent" -Destination ".agents" -Recurse -Force | Out-Null
   ```

6. **Báo cáo và Hướng dẫn Hub Connect**:
   - In ra thông báo chúc mừng setup thành công không gian Spoke theo cấu chuẩn, nhấn mạnh việc giao diện IDE của dự án từ nay đã tải được danh sách lệnh `/` của nền tảng cốt lõi bằng bản sao cục bộ.
   - Hướng dẫn người dùng: *"Nếu sau này bạn muốn nâng cấp các lệnh này, hãy chạy lệnh /update-ccba-spoke."*
   - Nếu Bước 4 tìm thấy các tập tin chưa xử lý, hãy nhắc nhở người dùng: *"Tôi phát hiện có các tập tin tài liệu thô. Bạn có muốn kích hoạt tiếp `/convert-markdown` để đẩy toàn bộ nội dung của chúng vào `.md\extracted_docs\` nhằm làm giàu Knowledge Base không?"*
   - Xử lý Platform Loader: Agent sẽ tự động tham chiếu đến Hub chung tại `D:\GitHubProjects\ccba-agent-platform\.agent\skills\platform-loader\SKILL.md` để load các Rule toàn cục.
