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
# Khởi tạo CCBA Spoke Workspace

Workflow này tự động hóa việc thiết lập một không gian làm việc (workspace) dự án mới để tuân thủ kiến trúc **CCBA Hub-and-Spoke** và **Global Rules**. Bạn nên chạy command `/ccba-init-spoke` ngay khi mở một thư mục dự án trên IDE.

## Các bước thực hiện:

### 0. Rào Chắn An Toàn Dự Án Hiện Hữu (Brownfield Safety Guard)
> [!CAUTION]
> **KIỂM TRA BẮT BUỘC TRƯỚC KHI KHỞI TẠO:**  
> Nếu thư mục hiện tại **đã có sẵn mã nguồn** (ví dụ: có file `workspace_context.yaml`, thư mục `.md/`, `.agents/`, `AGENTS.md`, hoặc code nghiệp vụ):
> - **TUYỆT ĐỐI KHÔNG** chạy tiếp `/ccba-init-spoke` vì sẽ ghi đè và làm mất dữ liệu hiện hữu!
> - Hãy chuyển ngay sang lệnh: **`/ccba-adopt-spoke`** để tự động quét hiện trạng, bảo tồn 100% dữ liệu cũ và kết nạp an toàn vào Hub.

Kiểm tra an toàn bằng PowerShell:
```powershell
if ((Test-Path ".md\workspace_context.yaml") -or (Test-Path "AGENTS.md") -or (Test-Path ".agents\workspace_context.yaml")) {
    Write-Warning "PHÁT HIỆN CODEBASE HIỆN HỮU (BROWNFIELD SPOKE)!"
    Write-Host "Để tránh mất dữ liệu cấu hình, vui lòng chạy lệnh: /ccba-adopt-spoke" -ForegroundColor Yellow
    return
}
```

### 1. Khởi tạo cấu trúc Knowledge Base (Global Rule 1)
Tạo kiến trúc thư mục `.md` chứa dữ liệu tri thức bằng PowerShell tùy theo Mode được chọn (`software`, `delivery`, hoặc `hybrid`):
```powershell
$mode = "[mode tương ứng]" # (Phần mềm -> software, Xây dựng/Tư vấn -> delivery, Platform/R&D -> hybrid)
if ($mode -eq "software") {
    $kbDirs = @(".md\scratch")
} else {
    $kbDirs = @(
        ".md\seminars", 
        ".md\legal_docs", 
        ".md\extracted_docs", 
        ".md\scratch", 
        ".md\data", 
        ".md\knowledge\configs", 
        ".md\knowledge\guidelines", 
        ".md\knowledge\related_papers", 
        ".md\knowledge\reports", 
        ".md\knowledge\specs_and_roadmaps"
    )
}
foreach ($dir in $kbDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
```


### 2. Ghi nhận tên dự án
Lấy tên thư mục Root hiện hành để cấu hình:
```powershell
(Get-Item .).Name
```

### 3. Tạo file Workspace Context
Tạo file `.md\workspace_context.yaml` và ghi nội dung cấu hình. Đề nghị người dùng chọn 1 trong các loại dự án sau để điền vào trường `type`:
- Dự án phần mềm/build tools (type: `Phần mềm`)
- Thẩm tra thiết kế/ Third-party Review (type: `Thẩm tra thiết kế`)
- Thiết kế/ Design (type: `Thiết kế`)
- Kiểm định/Assessment (type: `Kiểm định`)
- Tác vụ Admin/ Hành chính & Quản trị (type: `Tác vụ Admin`)

Dựa vào `type` được chọn, xác định `mode` mặc định (`software` cho Phần mềm, `delivery` cho các loại còn lại. Nếu là Hub hoặc Spoke hỗn hợp thì chọn `hybrid`).
Xác định `qc_mode` tự động:
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
  mode: "[mode tương ứng: software | delivery | hybrid]"
  qc_mode: "[qc_mode tương ứng]"
  description: >
    [Mô tả ngắn gọn mục tiêu và phạm vi dự án]

# =============================================================================
# MUST-READ FILES
# =============================================================================
must_read:
  always:
    - path: .md/GLOSSARY.md
      why: "Ubiquitous Language — thuật ngữ chuẩn"

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
  "Tôi đã đọc workspace_context.yaml. Dự án [tên] là [type] (mode: [mode]). Tác vụ hiện tại liên quan đến [lĩnh vực]."
```

### 4. Quét tìm tài liệu chưa xử lý
Kiểm tra xem dự án có file tài liệu thô (Word/PDF) nào chưa được xử lý hay không:
```powershell
Get-ChildItem -Path . -Recurse -Depth 3 | Where-Object { $_.Extension -match "\.(pdf|docx)$" } | Select-Object Name
```

### 5. Đồng bộ hóa Kỹ năng & Đăng ký Spoke với Hub (Single-Engine Sync)
Xác định đường dẫn Hub (`hub_path`) của Platform (mặc định lấy từ biến môi trường `CCBA_HUB_PATH`, cấu hình `workspace_context.yaml` hoặc thư mục anh em). Tiến hành đồng bộ kỹ năng và workflows bằng Deep Seam `SpokeSynchronizer`:

```powershell
# Chạy đồng bộ tự động theo bundle nghiệp vụ và đăng ký RSA Spoke Registry
python "$hub\scripts\sync_spoke.py" --spoke .
```

*Lưu ý:* Lệnh `sync_spoke.py` sẽ tự động:
- Đọc `project_type` trong `workspace_context.yaml` để chọn đúng bundle từ `catalog.yaml`.
- Đồng bộ các skills và workflows chuẩn vào `.agents/skills/` và `.agents/workflows/`.
- Đồng bộ hiến pháp `.agents/AGENTS.md`.
- Tự động sao chép bộ rào chắn test (`conftest.py`, `scripts/safe_pytest.py`) nếu là dự án Phần mềm.
- Mã hóa RSA 2048-bit thông tin Spoke và tự động đăng ký vào Hub Registry (`.md/data/spoke_registry.yaml`).

### 6. Khởi tạo cấu trúc .gitignore và Mã nguồn Chuẩn
*Lưu ý:* Bước này và bước 6.1 chỉ áp dụng nếu dự án được khởi tạo dưới dạng Spoke Chức năng (Functional/R&D Spoke) có sẵn Git cục bộ. Đối với các Spoke Dự án/Triển khai (Delivery Spoke) đồng bộ thuần túy qua OneDrive/SharePoint và không có repo GitHub riêng, hãy bỏ qua các bước cấu hình Git này.

Tạo tệp `.gitignore` mẫu **bảo mật 2 lớp** cho dự án (loại bỏ whitelist cho `skills` để Kỹ năng không bị commit vào Spoke, đồng thời loại trừ đệ quy các tệp nhị phân lớn để đồng bộ SharePoint):
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

# CCBA Agent Platform - Whitelist selected configs (skills is local only and git-ignored)
.agents/*
!.agents/workflows/
!.agents/proposals/
!.agents/AGENTS.md
.agents/**/*.log
.agents/**/*.json
.agents/**/*.env
.agents/**/__pycache__/
.agents/**/*.pyc

# Processing Workspace (.md/)
# Temp files during processing are ignored, but structure is tracked
.md/**/*.pdf
.md/**/*.docx
.md/**/*.xlsx
.md/**/*.pptx
.md/**/*.txt
# Except keep markdown and raw transcripts in general folders
!.md/**/raw_transcript.txt
.md/extracted_docs/*
!.md/extracted_docs/.gitkeep
# Ignore images of youtube-learn
.md/**/images/*.webp
.md/**/images/*.jpg
.md/**/images/*.png

# Ignore all specific project outputs (OneDrive/SharePoint synced)
.md/projects/*
!.md/projects/.gitkeep
```

### 6.1. Thiết lập Git Pre-commit Hook Bảo mật (Maskara)
Tự động cấu hình pre-commit hook cục bộ tại Spoke để gọi Maskara bảo vệ khóa API và thông tin nhạy cảm:
```powershell
if (Test-Path ".git") {
    $hookDir = ".git\hooks"
    if (-not (Test-Path $hookDir)) {
        New-Item -ItemType Directory -Path $hookDir -Force | Out-Null
    }
    $hookPath = Join-Path $hookDir "pre-commit"
    $hookContent = @"
#!/bin/sh
# CCBA Maskara Pre-commit Security Hook
echo 'Running Maskara staged files scan...'

# Get list of staged files (excluding deleted ones)
staged_files=`$(git diff --cached --name-only --diff-filter=d)

if [ -z "`$staged_files" ]; then
    echo "No files staged for commit. Skipping scan."
    exit 0
fi

has_leak=0
for file in `$staged_files; do
    # Skip binary and static asset files
    if echo "`$file" | grep -qE '\.(png|jpg|jpeg|gif|ico|pdf|zip|tar|gz|exe|dll|so|dylib|woff|woff2|eot|ttf|mp3|mp4|wav|avi)$'; then
        continue
    fi
    
    # Skip ignored dirs
    if echo "`$file" | grep -qE '^(\.md/scratch/|\.venv/|node_modules/)'; then
        continue
    fi
    
    if [ -f "`$file" ]; then
        python "$hub/scripts/maskara.py" scan --root "`$file" > /dev/null 2>&1
        status_code=`$?
        if [ `$status_code -ne 0 ]; then
            echo "❌ Leak detected in staged file: `$file"
            python "$hub/scripts/maskara.py" scan --root "`$file"
            has_leak=1
        fi
    fi
done

if [ `$has_leak -ne 0 ]; then
    echo 'Error: Raw API keys or credentials detected. Commit blocked!'
    exit 1
fi

echo "✅ Security check passed."
exit 0
"@
    [System.IO.File]::WriteAllText($hookPath, $hookContent)
}
```

Nếu `mode` là **"software"** hoặc **"hybrid"**, đề xuất người dùng chọn ngôn ngữ lập trình mục tiêu (Python/Node.js) và dựng cấu trúc thư mục chuẩn:
- Tạo các thư mục `src`, `tests`, `scripts`, `docs`, `docs/references`, `docs/adr`
- Khởi tạo `pyproject.toml` (cho Python) hoặc `package.json` (cho Node.js)
- *(Lưu ý: Bộ rào chắn test `conftest.py` và wrapper script `scripts/safe_pytest.py` đã được `sync_spoke.py` tự động đồng bộ ở Bước 5)*.

### 7. Khởi tạo cấu trúc Tri thức Mẫu (Dành cho các dự án nghiệp vụ)
Nếu `mode` là **"delivery"** hoặc **"hybrid"**, sao chép các tệp tin templates từ Hub về Spoke để kỹ sư bắt đầu ghi nhận tri thức:
```powershell
$hubTemplates = "[hub_path]\.agents\workflows\resources\templates"
if (Test-Path $hubTemplates) {
    Copy-Item -Path "$hubTemplates\ccba_rd_seminar_template.md" -Destination ".md\seminars\CCBA_RD_SEMINAR_001_Rev00-Template.md" -Force
    Copy-Item -Path "$hubTemplates\contract_template.md" -Destination ".md\data\contracts\contract_template.md" -Force
    Copy-Item -Path "$hubTemplates\weekly_report_template.md" -Destination ".md\knowledge\reports\weekly_report_template.md" -Force
}
```

### 8. Báo cáo hoàn tất
- In thông báo thiết lập Spoke Workspace thành công.
- Hướng dẫn người dùng các bước kế tiếp:
  - Chạy `/ccba-setup-skills` để thiết lập cấu hình công cụ phát triển (Issue Tracker, Domain Docs).
  - Sử dụng `/ccba-update-spoke` để nâng cấp các skills/workflows mới từ Hub.
  - Sử dụng `/ccba-convert-markdown` nếu cần chuyển đổi tài liệu Word/PDF sang Markdown.
