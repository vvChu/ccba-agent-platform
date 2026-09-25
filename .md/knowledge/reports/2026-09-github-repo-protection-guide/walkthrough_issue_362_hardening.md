# Walkthrough: Next Sprint Governance Hardening — POSIX Hook Sanitization & 99% Coverage

## 1. CCBA Charter Governance & QC Matrix (ADR-0058 Alignment)

| Thuộc tính | Giá trị quy định |
| :--- | :--- |
| **Môi trường tác vụ** | CCBA Central Hub Monorepo (`ccba-agent-platform`) |
| **Ghế phê duyệt (Charter Seat)** | `TRUONG_PHONG_RD_HTQT` (Core Infrastructure) / `CHU_TRI_BO_MON` |
| **Cấp độ thẩm duyệt (QC Level)** | **Level 2 (Technical & Architecture Review)** |
| **Cơ chế kiểm soát** | ADR-0058 Hard Completion Lock via `python -m ccba_harness verify-patch` |
| **Issue / Pull Request** | [Issue #362](https://github.com/vvChu/ccba-agent-platform/issues/362) / [PR #363](https://github.com/vvChu/ccba-agent-platform/pull/363) (Merged at [`914dc655`](https://github.com/vvChu/ccba-agent-platform/commit/914dc655)) |
| **Trạng thái hoàn tất** | 100% Exit Code 0, Coverage đạt 99%, Zero Regression |

---

## 2. Executive Summary

Trong phiên làm việc này, toàn bộ các mục tiêu nâng cấp và tăng cường độ vững chắc (hardening) được đề xuất sau đợt review của Issue #360 và PR #361 đã được hoàn thành 100%:
1. **Khắc phục triệt để lỗ hổng Word-Splitting & Git Octal-Escape trong hook `pre-commit`**:
   - Chuyển đổi toàn diện sang kiến trúc POSIX `/bin/sh` streaming subshell pipeline: `git -c core.quotepath=false diff --cached --name-only --diff-filter=d | ( while IFS= read -r file; do ... done; exit $has_leak )`.
   - Bảo đảm tương thích 100% với Dash (Debian/Ubuntu), Bash, Zsh và Git Bash trên Windows mà không phụ thuộc vào các Bash-isms như `read -d ''` hay `< <(...)`.
   - Thay thế `echo "$file" | grep` bằng `case "$file" in` nguyên sinh của shell POSIX, triệt tiêu việc fork sub-process per-file.
   - Loại bỏ lệnh gọi `git diff` dư thừa ban đầu, tăng tốc độ quét pre-commit.
2. **Hoàn thiện cơ chế Git Worktree / Submodule Legacy Fallback**:
   - Bổ sung việc cài đặt song song cả `legacy_pre_commit` và `legacy_pre_push` trong `legacy_hook_dir` với quyền thực thi `chmod 0o755`.
3. **Nâng độ phủ kiểm thử đơn vị (`protect_repo.py`) từ 66% lên 99%**:
   - Bổ sung kiểm thử mock toàn diện cho các nhánh: `get_default_branch` (API, rỗng, lỗi, ngoại lệ), `enable_vulnerability_alerts` (thành công, thất bại), `enable_secret_scanning` (thành công, cảnh báo GHAS), `apply_branch_ruleset` (PUT update, POST create, API error), `protect_repository` (full flow, `--no-dependabot`, auto default branch), và `main()`.
   - Độ bao phủ đạt **99%** (167/168 statements).
4. **Đồng bộ hóa tài liệu SOP**:
   - Cập nhật mẫu template `.githooks/pre-commit` trong [`docs/sop/github_repo_protection_guide.md`](docs/sop/github_repo_protection_guide.md).

---

## 3. Tóm Tắt Thay Đổi Mã Nguồn

### 3.1. Client-Side Hook Engine
- [`.githooks/pre-commit`](.githooks/pre-commit):
  - Bổ sung cờ `-c core.quotepath=false` khi lấy danh sách tệp staged để bảo toàn tên tệp UTF-8 tiếng Việt nguyên vẹn.
  - Streaming subshell pipeline đọc từng dòng an toàn qua `while IFS= read -r file; do ... done; exit $has_leak`.
- [`scripts/spoke/spoke_adopter.py`](scripts/spoke/spoke_adopter.py):
  - Cập nhật template `pre_commit_content` với cấu trúc POSIX streaming subshell.
  - Hoàn thiện legacy fallback: cài đặt cả `legacy_pre_commit` và `legacy_pre_push` với `chmod(st_mode | 0o755)`.
- [`docs/sop/github_repo_protection_guide.md`](docs/sop/github_repo_protection_guide.md):
  - Cập nhật section 9.3 với nội dung POSIX streaming subshell script chuẩn hóa.

### 3.2. Mở Rộng Bộ Kiểm Thử
- [`tests/test_spoke_repo_protection.py`](tests/test_spoke_repo_protection.py):
  - Thêm `test_maskara_hook_handles_filenames_with_spaces_and_unicode`: Khởi tạo git repo thật, staged file có khoảng trắng và dấu tiếng Việt (`tài liệu dự án.txt`, `mật khẩu bảo mật.txt`), chạy hook qua `sh` và kiểm tra chặn leak chính xác.
  - Thêm `test_install_guardrails_worktree_and_submodule_fallback`: Giả lập cấu trúc worktree pointer (`.git` chứa `gitdir:` trỏ tới `worktrees/wt1` với `commondir`), kiểm tra cài đặt đủ cả `pre-commit` và `pre-push` với quyền thực thi.
- [`tests/test_protect_repo_cli.py`](tests/test_protect_repo_cli.py):
  - Thêm 10 test case mới bao phủ toàn bộ các luồng `PUT`/`POST`, GHAS fallback, Dependabot bypass, fallback nhánh mặc định, và CLI `main()`.

---

## 4. Kết Quả Xác Minh & Đo Lường

### 4.1. Độ Phủ Kiểm Thử (`Coverage Report`)
```text
Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
scripts/governance/protect_repo.py     168      1    99%   456
------------------------------------------------------------------
TOTAL                                  168      1    99%
```
*(Dòng 456 là `if __name__ == "__main__": sys.exit(main())` khi chạy trực tiếp qua CLI).*

### 4.2. Bộ Test Suites Liên Quan
```text
tests/test_spoke_repo_protection.py .........                            [ 15%]
tests/test_protect_repo_cli.py ......................                    [ 54%]
tests/test_spoke_adopter.py .........                                    [ 70%]
tests/test_spoke_initializer.py .................                        [100%]

============================== 57 passed in 0.55s ==============================
```

### 4.3. Chốt Khóa ADR-0058 (`ccba_harness verify-patch`)
```text
# 🛡️ Deterministic Patch Verification Report: ✅ ALL PASSED

- Overall Status: PASS
- Commands Executed: 3/3 passed
- Total Duration: 802.0 ms

| Status | Exit Code | Command |
| :---: | :---: | :--- |
| PASS | 0 | .venv/bin/ruff check scripts/spoke/ scripts/governance/protect_repo.py tests/test_spoke_repo_protection.py tests/test_protect_repo_cli.py |
| PASS | 0 | .venv/bin/ruff format --check scripts/spoke/ scripts/governance/protect_repo.py tests/test_spoke_repo_protection.py tests/test_protect_repo_cli.py |
| PASS | 0 | .venv/bin/python -m pytest tests/test_spoke_repo_protection.py tests/test_protect_repo_cli.py tests/test_spoke_adopter.py tests/test_spoke_initializer.py -q |
```

---

## 5. Hướng Dẫn Kích Hoạt Trực Tiếp Trên Remote (Maintainer 1-Click)

Để kích hoạt bộ quy tắc bảo vệ nhánh `main` và kích hoạt toàn diện bảo mật trên GitHub remote cho repository `vvChu/ccba-agent-platform`:

```bash
python scripts/ccba_platform_cli.py protect-repo \
  --repo vvChu/ccba-agent-platform \
  --branch main \
  --checks "CI/Test - Python 3.12 (push)" "CI/Deterministic Parity Verification (push)" "CI/Lint Markdown (push)" "Security & Privacy Scan/Maskara Secret & Privacy Leak Gate (push)"
```
*(Lưu ý: Chạy lệnh với tài khoản có quyền Admin của repository).*
