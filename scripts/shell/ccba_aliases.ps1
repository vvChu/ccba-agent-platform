# CCBA Developer PowerShell Productivity Suite
# Nạp vào PowerShell Profile: . $PSScriptRoot/ccba_aliases.ps1
# Hoặc thêm vào $PROFILE: . "D:\GitHubProjects\ccba-agent-platform\scripts\shell\ccba_aliases.ps1"

# 1. Tra cứu cú pháp lệnh nhanh từ ngôn ngữ tự nhiên (dùng GitHub Copilot CLI)
function ?? {
    param([Parameter(ValueFromRemainingArguments=$true)][string]$Query)
    if (-not $Query) {
        Write-Host "Cách dùng: ?? <câu hỏi hoặc mô tả lệnh cần tìm>" -ForegroundColor Cyan
        return
    }
    copilot -p "$Query" --silent
}

# 2. Smart Commit Message siêu tốc từ git diff (dùng ccba-ai SDK - độ trễ ~1.2s)
function ai-commit {
    param([string]$ExtraPrompt = "")
    $diff = git diff --cached --stat
    $fullDiff = git diff --cached
    if (-not $fullDiff) {
        Write-Host "[!] Không có thay đổi nào được stage. Hãy chạy 'git add' trước!" -ForegroundColor Yellow
        return
    }
    Write-Host "[*] Đang sinh Conventional Commit message qua ccba-ai..." -ForegroundColor Cyan
    $prompt = "Sinh 1 dòng Conventional Commit message (feat:, fix:, docs:, refactor:, chore:) ngắn gọn (<72 ký tự) dựa trên git diff sau. CHỈ trả về commit message, không thêm markdown hay giải thích:`n" + $diff + "`n" + $ExtraPrompt
    $pyCmd = "from ccba_ai import ai; print(ai.chat('''$prompt''', max_tokens=100).strip())"
    $msg = python -c "$pyCmd"
    if ($msg) {
        Write-Host "[*] Commit message đề xuất: " -NoNewline -ForegroundColor Green
        Write-Host "$msg" -ForegroundColor White
        $confirm = Read-Host "Bạn có muốn commit với message này không? (Y/n)"
        if ($confirm -eq "" -or $confirm -match "^[Yy]") {
            git commit -m "$msg"
        }
    } else {
        Write-Host "[X] Không thể sinh commit message từ ccba-ai." -ForegroundColor Red
    }
}

# 3. Quick Code Review trước khi tạo PR (dùng ccba-ai SDK)
function ai-review {
    $diff = git diff origin/main...HEAD
    if (-not $diff) {
        $diff = git diff HEAD~1
    }
    if (-not $diff) {
        Write-Host "[i] Không có thay đổi nào so với origin/main hoặc HEAD~1 để review." -ForegroundColor Yellow
        return
    }
    Write-Host "[*] Đang review code diff theo chuẩn AGENTS.md và Code Quality..." -ForegroundColor Cyan
    $prompt = "Hãy review git diff sau theo chuẩn AGENTS.md, chỉ chỉ ra các lỗi bảo mật, vi phạm KISS, hoặc lỗi logic nghiêm trọng nếu có. Trả lời ngắn gọn bằng tiếng Việt:`n" + $diff
    $pyCmd = "from ccba_ai import ai; print(ai.chat('''$prompt''', max_tokens=1024).strip())"
    python -c "$pyCmd"
}

# 4. Giải thích nhanh lỗi hoặc câu lệnh phức tạp
function ai-explain {
    param([Parameter(ValueFromRemainingArguments=$true)][string]$Target)
    if (-not $Target) {
        Write-Host "Cách dùng: ai-explain <câu lệnh hoặc đoạn log lỗi>" -ForegroundColor Cyan
        return
    }
    copilot explain "$Target"
}
