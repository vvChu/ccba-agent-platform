---
description: Khởi tạo một dự án (Spoke) tuân thủ kiến trúc CCBA Agent Platform
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
  - "Tác vụ Admin"
bundle: "_core"
---

# Khởi tạo CCBA Spoke Workspace

Workflow này tự động hóa việc thiết lập một không gian làm việc (workspace) dự án mới để tuân thủ kiến trúc **CCBA Hub-and-Spoke** và **Global Rules**. Bạn nên chạy command `/ccba-init-spoke` ngay khi mở một thư mục dự án trên IDE.

## Các bước thực hiện:

### 1. Khởi tạo cấu trúc Knowledge Base (Global Rule 1)
Tạo kiến trúc thư mục `.md` chứa dữ liệu tri thức bằng PowerShell:
```powershell
New-Item -ItemType Directory -Force -Path ".md\extracted_docs" | Out-Null
```

### 2. Ghi nhận tên dự án
Lấy tên thư mục Root hiện hành để cấu hình:
```powershell
(Get-Item .).Name
```

### 3. Tạo file Workspace Context
Tạo file `.md\workspace_context.yaml` và ghi nội dung cấu hình. Đề nghị người dùng chọn 1 trong các loại dự án sau để điền vào trường `type`:
- Dự án phần mềm/build tools
- Thẩm tra thiết kế/ Third-party Review
- Thiết kế/ Design
- Kiểm định/Assessment
- Tác vụ Admin/ Hành chính & Quản trị

Dựa vào `type` được chọn, xác định `qc_mode` tự động:
- Thiết kế $\rightarrow$ `internal`
- Thẩm tra thiết kế $\rightarrow$ `third-party`
- Kiểm định $\rightarrow$ `assessment`
- Phần mềm hoặc Tác vụ Admin $\rightarrow$ `null`

```yaml
# =============================================================================
# WORKSPACE CONTEXT — [Tên thư mục dự án]
# Machine-readable onboarding file for AI Agents.
# =============================================================================

project:
  name: "[Tên thư mục dự án]"
  type: "[Loại dự án được chọn]"
  qc_mode: "[qc_mode tương ứng]"
  description: >
    [Mô tả ngắn gọn mục tiêu và phạm vi dự án]

# =============================================================================
# AGENT BOUNDARIES
# =============================================================================
agent_boundaries:
  allowed_read_paths:
    - "*"
  allowed_write_paths:
    - ".md/"
  strict_mode: true

# =============================================================================
# MUST-READ FILES
# =============================================================================
must_read:
  always:
    - path: .md/GLOSSARY.md
      why: "Ubiquitous Language — thuật ngữ chuẩn"

# =============================================================================
# OUTPUT DIRECTORIES
# =============================================================================
output_dirs:
  reports_and_docs: .md/docs/
  scratch_and_logs: .md/archive/
  research_scripts: .md/scripts/

# =============================================================================
# DO NOT TOUCH
# =============================================================================
do_not_touch:
  - .env

# =============================================================================
# AGENT ACKNOWLEDGMENT PROTOCOL (Global Rule 4 — Override)
# =============================================================================
acknowledgment_required: true
acknowledgment_format: >
  "Tôi đã đọc workspace_context.yaml. Dự án [tên] là [type]. Tác vụ hiện tại liên quan đến [lĩnh vực]."
```

### 4. Quét tìm tài liệu chưa xử lý
Kiểm tra xem dự án có file tài liệu thô (Word/PDF) nào chưa được xử lý hay không:
```powershell
Get-ChildItem -Path . -Recurse -Depth 3 | Where-Object { $_.Extension -match "\.(pdf|docx)$" } | Select-Object Name
```

### 5. Đồng bộ hóa Giao diện Lệnh (Copy theo Bundle)
Xác định đường dẫn Hub (`hub_path`) của Platform (mặc định lấy từ biến môi trường `CCBA_HUB_PATH` hoặc repository chung). Tiến hành sao chép các kỹ năng/workflows tương ứng về Spoke:
```powershell
$bundles = @{
    "Phần mềm"          = @("_core", "_software")
    "Thẩm tra thiết kế" = @("_core", "_qc", "_consulting")
    "Thiết kế"          = @("_core", "_qc", "_consulting")
    "Kiểm định"         = @("_core", "_qc", "_consulting")
    "Tác vụ Admin"      = @("_core", "_consulting")
}
$type = "[type vừa được chọn]"
$hub  = "[hub_path]"
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

### 6. Khởi tạo cấu trúc Mã nguồn Chuẩn (Dành cho Dự án Phần mềm)
Nếu `type` là **"Phần mềm"**, đề xuất người dùng chọn ngôn ngữ lập trình mục tiêu (Python/Node.js) và dựng cấu trúc thư mục chuẩn:
- Tạo các thư mục `src`, `tests`, `scripts`, `docs`
- Khởi tạo `pyproject.toml` (cho Python) hoặc `package.json` (cho Node.js)
- Tạo `.gitignore` mẫu **bảo mật 2 lớp** (whitelisting workflows/skills cục bộ):
  ```text
  # System / IDE
  .env
  .vscode/
  .idea/
  *.log

  # Python / Node.js build
  __pycache__/
  *.pyc
  node_modules/
  .venv/
  build/
  dist/
  *.egg-info/

  # CCBA Agent Platform - Whitelist selected configs
  .agents/*
  !.agents/workflows/
  !.agents/skills/
  !.agents/proposals/
  !.agents/AGENTS.md
  .agents/**/*.log
  .agents/**/*.json
  .agents/**/*.env
  .agents/**/__pycache__/
  .agents/**/*.pyc
  ```

### 7. Khởi tạo cấu trúc Tri thức Mẫu (Dành cho Tác vụ Admin)
Nếu `type` là **"Tác vụ Admin"**, sao chép các tệp tin templates từ Hub về Spoke:
```powershell
$adminDirs = @(
    ".md\seminars", 
    ".md\legal_docs", 
    ".md\extracted_docs", 
    ".md\scratch", 
    ".md\data\contracts", 
    ".md\knowledge\configs", 
    ".md\knowledge\guidelines", 
    ".md\knowledge\related_papers", 
    ".md\knowledge\reports", 
    ".md\knowledge\specs_and_roadmaps"
)
foreach ($dir in $adminDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}
$hubTemplates = "[hub_path]\.agents\workflows\resources\templates"
if (Test-Path $hubTemplates) {
    Copy-Item -Path "$hubTemplates\CCBA_RD_SEMINAR_001_Rev00-Template.md" -Destination ".md\seminars\" -Force
    Copy-Item -Path "$hubTemplates\CONTRACT_TEMPLATE.md" -Destination ".md\data\contracts\" -Force
    Copy-Item -Path "$hubTemplates\weekly_report_template.md" -Destination ".md\knowledge\reports\" -Force
}
```

### 8. Báo cáo hoàn tất
- In thông báo thiết lập Spoke Workspace thành công.
- Hướng dẫn người dùng các lệnh liên quan: `/ccba-update-spoke` và `/ccba-convert-markdown`.
