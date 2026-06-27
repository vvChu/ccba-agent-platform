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
   # =============================================================================
   # WORKSPACE CONTEXT — <Tên thư mục dự án>
   # Machine-readable onboarding file for AI Agents.
   # READ THIS FIRST before touching any code or files.
   # =============================================================================

   project:
     name: "<Tên thư mục dự án vừa lấy được>"
     type: "<Loại dự án được chọn từ danh mục trên>"
     qc_mode: "<internal|third-party|assessment|null>"
     description: >
       <Mô tả ngắn gọn mục tiêu và phạm vi dự án — 1-2 câu>

   # =============================================================================
   # AGENT BOUNDARIES
   # =============================================================================
   agent_boundaries:
     allowed_read_paths:
       - "*"  # Được phép đọc toàn bộ Workspace để thu thập thông tin
     allowed_write_paths:
       - # Khai báo cụ thể thư mục triển khai (Ví dụ: ".md/")
     strict_mode: true  # Khi bật, Agent bị cấm ghi file ngoài allowed_write_paths

   # =============================================================================
   # MUST-READ FILES (theo thứ tự ưu tiên)
   # Chỉ đọc file liên quan đến tác vụ hiện tại. KHÔNG cần đọc tất cả cùng lúc.
   # =============================================================================
   must_read:
     always:
       - path: .md/GLOSSARY.md
         why: "Ubiquitous Language — tên biến, tên bảng, thuật ngữ chuẩn"
     # Bổ sung theo từng loại dự án:
     # when_working_on_<domain>:
     #   - path: .md/docs/<file>.md
     #     why: "<lý do>"

   # =============================================================================
   # OUTPUT DIRECTORIES
   # =============================================================================
   output_dirs:
     reports_and_docs: .md/docs/
     scratch_and_logs:  .md/archive/
     research_scripts:  .md/scripts/

   # =============================================================================
   # DO NOT TOUCH
   # =============================================================================
   do_not_touch:
     - .env  # Secrets — không hardcode, không commit lên Git
     # Bổ sung các file/thư mục cần bảo vệ

   # =============================================================================
   # AGENT ACKNOWLEDGMENT PROTOCOL (theo Global Rule 4 — Override)
   # =============================================================================
   acknowledgment_required: true
   acknowledgment_format: >
     "Tôi đã đọc workspace_context.yaml. Dự án [tên] là [type], đang ở giai đoạn [milestone nếu có].
     Tác vụ hiện tại liên quan đến [lĩnh vực], tôi sẽ tham chiếu thêm [tên file cụ thể]."

   # =============================================================================
   # HUB SERVICES
   # =============================================================================
   related_hub_services:
     - platform-loader
     - mdconverter
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

6. **Khởi tạo Kiến trúc Mã nguồn Chuẩn (Dành riêng cho Dự án Phần mềm)**:  
   Nếu `type` được chọn là **"Phần mềm"**, đề xuất người dùng chọn ngôn ngữ lập trình mục tiêu (ví dụ: Python, Node.js) và thực thi script PowerShell sau để dựng cấu trúc thư mục chuẩn (chỉ khởi tạo nếu chưa tồn tại để đảm bảo an toàn dữ liệu):
   ```powershell
   $projectName = (Get-Item .).Name
   # 1. Tạo các thư mục cơ bản
   $dirs = @("src", "tests", "scripts", "docs")
   foreach ($dir in $dirs) {
       if (-not (Test-Path $dir)) {
           New-Item -ItemType Directory -Path $dir | Out-Null
       }
   }
   
   # 2. Tạo package subfolder cho Python nếu được chọn
   $lang = "<Ngôn ngữ: Python|Node.js>"
   if ($lang -eq "Python") {
       $packageDir = "src\$projectName"
       if (-not (Test-Path $packageDir)) {
           New-Item -ItemType Directory -Path $packageDir | Out-Null
           New-Item -ItemType File -Path "$packageDir\__init__.py" | Out-Null
       }
       # Tạo pyproject.toml mẫu nếu chưa có
       if (-not (Test-Path "pyproject.toml")) {
           @'
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build-meta"

[project]
name = "{0}"
version = "0.1.0"
description = "CCBA Spoke Software Project"
requires-python = ">=3.10"
dependencies = []
'@ -f $projectName | Out-File -FilePath "pyproject.toml" -Encoding utf8
       }
   } elseif ($lang -eq "Node.js") {
       # Tạo package.json mẫu nếu chưa có
       if (-not (Test-Path "package.json")) {
           @'
{
  "name": "{0}",
  "version": "0.1.0",
  "description": "CCBA Spoke Software Project",
  "main": "src/index.js",
  "scripts": {
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "dependencies": {}
}
'@ -f $projectName | Out-File -FilePath "package.json" -Encoding utf8
       }
   }

   # 3. Tạo file README.md cơ bản nếu chưa có
   if (-not (Test-Path "README.md")) {
       @'
# {0}

Dự án phần mềm thuộc hệ sinh thái CCBA Agent Services Platform.

## Kiến trúc thư mục
- `src/`: Mã nguồn dự án
- `tests/`: Kịch bản kiểm thử
- `scripts/`: Công cụ dòng lệnh hỗ trợ
- `.md/`: Tri thức dự án và cấu hình agent

## Khởi động
- Đọc cấu hình tại `.md/workspace_context.yaml` trước khi phát triển.
'@ -f $projectName | Out-File -FilePath "README.md" -Encoding utf8
   }

   # 4. Tạo .gitignore cơ bản nếu chưa có
   if (-not (Test-Path ".gitignore")) {
       @'
# System / IDE
.env
.agents/
.vscode/
.idea/
*.log

# Python
__pycache__/
*.pyc
.venv/
build/
dist/
*.egg-info/

# Node.js
node_modules/
npm-debug.log
'@ | Out-File -FilePath ".gitignore" -Encoding utf8
   }
   Write-Host "Cấu trúc thư mục mã nguồn chuẩn ($lang) đã được khởi tạo thành công!"
   ```

7. **Báo cáo và Hướng dẫn Hub Connect**:
   - In ra thông báo chúc mừng setup thành công không gian Spoke theo cấu chuẩn, nhấn mạnh việc giao diện IDE của dự án từ nay đã tải được danh sách lệnh `/` của nền tảng cốt lõi bằng bản sao cục bộ.
   - Hướng dẫn người dùng: *"Nếu sau này bạn muốn nâng cấp các lệnh này, hãy chạy lệnh /update-ccba-spoke."*
   - Nếu Bước 4 tìm thấy các tập tin chưa xử lý, hãy nhắc nhở người dùng: *"Tôi phát hiện có các tập tin tài liệu thô. Bạn có muốn kích hoạt tiếp `/convert-markdown` để đẩy toàn bộ nội dung của chúng vào `.md\extracted_docs\` nhằm làm giàu Knowledge Base không?"*
   - Xử lý Platform Loader: Agent sẽ tự động tham chiếu đến Hub chung tại `D:\GitHubProjects\ccba-agent-platform\.agent\skills\platform-loader\SKILL.md` để load các Rule toàn cục.
