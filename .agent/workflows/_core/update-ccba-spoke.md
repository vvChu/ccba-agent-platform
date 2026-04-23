---
description: Cập nhật thủ công các lệnh và kỹ năng mới từ Hub về dự án Spoke hiện tại
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Cập nhật CCBA Spoke Workspace

Workflow này cho phép dự án (Spoke) hiện tại đồng bộ hóa và tải về các bản cập nhật mới nhất (kịch bản lệnh, kỹ năng) từ trung tâm CCBA Agent Platform (Hub). Chỉ sync đúng bundle phù hợp với loại dự án.

## Bước thực hiện:

1. **Đọc bundle type từ workspace_context.yaml**:
   ```powershell
   $ctx = Get-Content ".md\workspace_context.yaml" -Raw
   if ($ctx -match 'type:\s*"?([^"\n]+)"?') { $type = $Matches[1].Trim() }
   Write-Host "Detected project type: $type"
   ```

2. **Sync đúng bundle từ Hub**:
   ```powershell
   $bundles = @{
       "Phần mềm"          = @("_core", "_software")
       "Thẩm tra thiết kế" = @("_core", "_qc", "_consulting")
       "Thiết kế"          = @("_core", "_qc", "_consulting")
       "Kiểm định"         = @("_core", "_qc", "_consulting")
   }
   $hub = "D:\GitHubProjects\ccba-agent-platform\.agent"
   New-Item -ItemType Directory -Force -Path ".agents\skills", ".agents\workflows" | Out-Null
   foreach ($bundle in $bundles[$type]) {
       if (Test-Path "$hub\skills\$bundle") {
           Copy-Item -Path "$hub\skills\$bundle\*" -Destination ".agents\skills\" -Recurse -Force
       }
       if (Test-Path "$hub\workflows\$bundle") {
           Copy-Item -Path "$hub\workflows\$bundle\*" -Destination ".agents\workflows\" -Recurse -Force
       }
   }
   ```

3. **Báo cáo kết quả**:
   - In ra thông báo: *"Đã đồng bộ bundle `$type` từ Hub. Hãy thử gõ phím `/` ở khung chat để kiểm tra các lệnh mới nhất nhé!"*
