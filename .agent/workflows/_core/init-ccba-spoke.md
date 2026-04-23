---
description: Khởi tạo một dự án (Spoke) tuân thủ kiến trúc CCBA Agent Platform
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
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
   Sử dụng công cụ `write_to_file` kết hợp với kết quả từ Bước 2 để tạo và ghi nội dung vào file `.md\workspace_context.yaml`. **Lưu ý quan trọng:** Hãy đề nghị người dùng chọn 1 trong các loại dự án theo danh mục sau cho trường `type`:
   - Dự án phần mềm/build tools
   - Thẩm tra thiết kế/ Third-party Review
   - Thiết kế/ Design
   - Kiểm định/Assessment
   *(Trong tương lai có thể được bổ sung thêm)*

   Dựa vào `type` được chọn, **xác định `qc_mode`** theo bảng sau:
   | type | qc_mode |
   |------|---------|
   | Thiết kế | `internal` |
   | Thẩm tra thiết kế | `third-party` |
   | Kiểm định | `assessment` |
   | Phần mềm | `null` |

   ```yaml
   project_name: "<Tên thư mục dự án vừa lấy được>"
   type: "<Loại dự án được chọn từ danh mục trên>"
   qc_mode: "<internal|third-party|assessment|null>"
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

5. **Đồng bộ hóa Giao diện Lệnh IDE (Copy theo Bundle)**:  
   Copy **chỉ những skills/workflows cần thiết** từ Hub về `.agents` tại dự án (Spoke) dựa trên `type` vừa chọn. Sử dụng công cụ `run_command`:
   ```powershell
   # Bundle mapping — chỉ 2 bundle thực sự
   $bundles = @{
       "Phần mềm"          = @("_core", "_software")
       "Thẩm tra thiết kế" = @("_core", "_qc", "_consulting")
       "Thiết kế"          = @("_core", "_qc", "_consulting")
       "Kiểm định"         = @("_core", "_qc", "_consulting")
   }
   $type = "<type vừa được chọn>"
   $hub  = "D:\GitHubProjects\ccba-agent-platform\.agent"
   New-Item -ItemType Directory -Force -Path ".agents\skills", ".agents\workflows" | Out-Null
   foreach ($bundle in $bundles[$type]) {
       if (Test-Path "$hub\skills\$bundle") {
           Copy-Item -Path "$hub\skills\$bundle\*" -Destination ".agents\skills\" -Recurse -Force
       }
       if (Test-Path "$hub\workflows\$bundle") {
           Copy-Item -Path "$hub\workflows\$bundle\*" -Destination ".agents\workflows\" -Recurse -Force
       }
   }
   Write-Host "Bundle '$type' đã được copy về .agents/"
   ```

6. **Báo cáo và Hướng dẫn Hub Connect**:
   - In ra thông báo chúc mừng setup thành công không gian Spoke theo cấu chuẩn, nhấn mạnh việc giao diện IDE của dự án từ nay đã tải được danh sách lệnh `/` của nền tảng cốt lõi bằng bản sao cục bộ.
   - Hướng dẫn người dùng: *"Nếu sau này bạn muốn nâng cấp các lệnh này, hãy chạy lệnh /update-ccba-spoke."*
   - Nếu Bước 4 tìm thấy các tập tin chưa xử lý, hãy nhắc nhở người dùng: *"Tôi phát hiện có các tập tin tài liệu thô. Bạn có muốn kích hoạt tiếp `/convert-markdown` để đẩy toàn bộ nội dung của chúng vào `.md\extracted_docs\` nhằm làm giàu Knowledge Base không?"*
   - Xử lý Platform Loader: Agent sẽ tự động tham chiếu đến Hub chung tại `D:\GitHubProjects\ccba-agent-platform\.agent\skills\platform-loader\SKILL.md` để load các Rule toàn cục.
