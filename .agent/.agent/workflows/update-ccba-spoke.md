---
description: Cập nhật thủ công các lệnh và kỹ năng mới từ Hub về dự án Spoke hiện tại
---

# Cập nhật CCBA Spoke Workspace

Workflow này cho phép dự án (Spoke) hiện tại đồng bộ hóa và tải về các bản cập nhật mới nhất (kịch bản lệnh, kỹ năng) từ trung tâm CCBA Agent Platform (Hub) thông qua hành động copy cục bộ.

## Bước thực hiện:

1. **Khởi chạy đồng bộ hóa từ Hub về Spoke**:
   Sử dụng công cụ `run_command` để chạy PowerShell sao chép và ghi đè toàn bộ nội dung thư mục `.agent` từ Hub về thư mục `.agents` của dự án hiện tại:
   ```powershell
   Copy-Item -Path "D:\GitHubProjects\ccba-agent-platform\.agent\*" -Destination ".agents" -Recurse -Force | Out-Null
   ```

2. **Báo cáo kết quả**:
   - In ra thông báo: *"Đã cập nhật thành công toàn bộ kịch bản và luật từ Hub về dự án cục bộ con. Hãy thử gõ phím `/` ở khung chat để kiểm tra các lệnh mới nhất nhé!"*
