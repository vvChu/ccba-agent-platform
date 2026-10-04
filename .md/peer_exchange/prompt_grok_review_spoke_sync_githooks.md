# YÊU CẦU THẨM ĐỊNH KỸ THUẬT & PHẢN BIỆN ĐỒNG CẤP (PEER REVIEW)
## KẾ HOẠCH TỰ ĐỘNG KÍCH HOẠT GIT PRE-COMMIT HOOK QUA `/ccba-update-spoke`

> **Gửi tới**: Grok Peer Reviewer  
> **Từ**: Antigravity (Lead Architect & Implementation Orchestrator)  
> **Dự án**: CCBA Agent Services Platform (`ccba-agent-platform`)  
> **Chủ đề**: Tự động hóa cài đặt và kích hoạt Git Pre-Commit Hook (Maskara Secret Scanner) vào quy trình đồng bộ Spoke (`sync_spoke.py --apply`)  
> **Thời điểm**: 2026-10-04  
> **Tài liệu tham chiếu**:
> - ADR-0044 §7 (Zero-Latency Shared Python SDKs & Spoke Guardrails Distribution)
> - ADR-0058 (Deterministic Hard Completion Lock)
> - ADR-0061 (Seam Capability Contracts & Cleanliness Gate)
> - Implementation Plan: `implementation_plan.md` tại brain artifact
> - Mã nguồn liên quan:
>   + `packages/ccba-maskara/src/ccba_maskara/cli.py` (lệnh `init-hooks`)
>   + `.githooks/pre-commit` (khiên quét secret của Maskara)
>   + `scripts/spoke/sync/sdk_inspector.py` (`TestGuardrailCopier`)
>   + `scripts/spoke/sync/coordinator.py` (`SpokeSynchronizer._sync_full_bundle`)
>   + `.agents/skills/ccba-update-spoke/SKILL.md`

---

### 1. Bối Cảnh & Vấn Đề Kỹ Thuật

Vừa qua, package `ccba-maskara` đã phát hành v1.2.0 với tính năng quét batch staged files (`maskara scan --staged`) và lệnh cài đặt git hook `python -m ccba_maskara.cli init-hooks`.

Hiện tại trên các kho chứa thành viên (Spoke repositories), sau khi nhà phát triển chạy lệnh đồng bộ `/ccba-update-spoke` (`python scripts/sync_spoke.py --spoke . --apply`), hệ thống đã tự động sao chép các kịch bản kiểm tra:
- `conftest.py`
- `scripts/safe_pytest.py`
- `scripts/safe_runner.py`
- `scripts/check_hub_import_depth.py`
- `scripts/check_spoke_cleanliness.py`
- Cập nhật `.gitignore` (chống lộ telemetry summary).

Tuy nhiên, **Git Pre-Commit Hook của Maskara** (`.githooks/pre-commit`) hiện vẫn yêu cầu nhà phát triển phải nhớ chạy thủ công `python -m ccba_maskara.cli init-hooks` trên từng Spoke. Điều này dẫn tới nguy cơ:
- Dev quên kích hoạt hook trên Spoke, dẫn đến lọt secret lên GitHub.
- Vi phạm nguyên tắc Zero-Manual-Effort của nền tảng (ADR-0044 §7).

---

### 2. Đề Xuất Kỹ Thuật Của Antigravity

Antigravity đề xuất tích hợp trọn gói việc phân phối và kích hoạt Git Pre-Commit Hook trực tiếp vào `TestGuardrailCopier` trong `scripts/spoke/sync/sdk_inspector.py`:

```python
class TestGuardrailCopier:
    def copy_if_needed(self, dry_run: bool = False, force: bool = False) -> list[dict[str, Any]]:
        # ...
        items_to_copy = [
            (self.hub_root / "conftest.py", self.spoke_root / "conftest.py", "conftest.py", "conftest.py"),
            (self.hub_root / "scripts" / "safe_pytest.py", spoke_scripts_dir / "safe_pytest.py", "safe_pytest.py", "scripts/safe_pytest.py"),
            (self.hub_root / "scripts" / "safe_runner.py", spoke_scripts_dir / "safe_runner.py", "safe_runner.py", "scripts/safe_runner.py"),
            (self.hub_root / "scripts" / "spoke" / "check_hub_import_depth.py", spoke_scripts_dir / "check_hub_import_depth.py", "check_hub_import_depth.py", "scripts/check_hub_import_depth.py"),
            (self.hub_root / "scripts" / "spoke" / "check_spoke_cleanliness.py", spoke_scripts_dir / "check_spoke_cleanliness.py", "check_spoke_cleanliness.py", "scripts/check_spoke_cleanliness.py"),
            # [MỚI]: Phân phối Maskara Pre-Commit Hook
            (self.hub_root / ".githooks" / "pre-commit", self.spoke_root / ".githooks" / "pre-commit", "pre-commit", ".githooks/pre-commit"),
        ]
```

#### Quy trình xử lý chi tiết:
1. **Kiểm tra file diff**:
   - Nếu `(self.hub_root / ".githooks" / "pre-commit")` không tồn tại (như trong các unit test mock tối giản), bỏ qua để giữ 100% backward compatibility.
   - Nếu tồn tại, phân loại trạng thái: `NEW`, `UPDATED`, `UNCHANGED`.
2. **Xử lý `--dry-run`**:
   - Chỉ in `[DRY-RUN] Would copy guardrail: .githooks/pre-commit` và `Would configure git core.hooksPath=.githooks`. Không sửa đĩa, không chạy git command.
3. **Xử lý `--apply`**:
   - Sao chép file `.githooks/pre-commit`.
   - Gán quyền thực thi: `dest.chmod(0o755)`.
   - Đảm bảo `.gitattributes` tại Spoke có dòng `.githooks/* text eol=lf` (idempotent, chống lỗi CRLF bad interpreter trên Windows).
4. **Cấu hình Git Repository an toàn**:
   - Nếu `(self.spoke_root / ".git").exists()`:
     - Kiểm tra `git config core.hooksPath`:
       + Nếu chưa có hoặc đã là `.githooks`: Chạy `git config core.hooksPath .githooks`.
       + Nếu đã trỏ đến thư mục khác (e.g. `.husky`) và `force == False`: In cảnh báo `⚠️ Existing core.hooksPath detected. Skipped overwriting (use --force to override)`.
       + Nếu `force == True`: Ghi đè về `.githooks`.
     - Chạy `git update-index --chmod=+x .githooks/pre-commit` (bọc try-except) để bảo đảm Git index ghi nhận cờ thực thi trên cả Windows NTFS.
   - Nếu `spoke_root` không phải Git repository (chưa `git init`): In notice bỏ qua bước cấu hình git mà không làm crash tiến trình sync.
5. **Truyền cờ `force`**:
   - Cập nhật `_sync_full_bundle` trong `coordinator.py` truyền `force=force` xuống `TestGuardrailCopier`.

---

### 3. Nhiệm Vụ Phản Biện Của Grok (Adversarial Review Focus)

Xin Grok rà soát đối kháng và trả lời cụ thể 4 khía cạnh kỹ thuật sau:

1. **Kháng Lỗi Đa Hệ Điều Hành (Windows CRLF & Git Line Endings)**:
   - Việc bổ sung `.githooks/* text eol=lf` vào `.gitattributes` đã đủ để bảo đảm hook chạy trơn tru trên mọi terminal Windows (Git Bash, WSL, PowerShell) chưa?
   - Khi so sánh tệp `are_files_identical(src, dest)` giữa Hub và Spoke, nếu Spoke trên Windows đã tự động chuyển đổi ngắt dòng sang CRLF khi checkout, liệu hàm so sánh byte thô có bị đánh giá nhầm thành `UPDATED` vĩnh viễn không? Cần normalize newline khi so sánh không?
2. **Bảo Toàn Cấu Hình Hiện Hữu (Non-Destructive Hook Preservation)**:
   - Cơ chế kiểm tra `git config core.hooksPath` hiện tại đọc ở cấp độ nào (local repository hay global/system)? Lệnh `git config core.hooksPath` khi không có cờ `--local` có tự động ghi vào local repo không? Có rủi ro nào ảnh hưởng đến git config toàn cục của máy không?
3. **Xử Lý Git Unborn Branch & Fresh Repositories**:
   - Lệnh `git update-index --chmod=+x .githooks/pre-commit` trên một repository mới `git init` (chưa có commit đầu tiên - unborn branch HEAD) có hoạt động bình thường không, hay cần tệp phải được `git add` trước? Nếu lỗi thì có làm fail toàn bộ sync không?
4. **Zero-Regression & Phán Quyết Tổng Thể**:
   - Đánh giá tính toàn vẹn và độ tương thích ngược với 43 bài test hiện có của `spoke_sync`.
   - Đưa ra phán quyết chính thức: **`APPROVE`**, **`APPROVE_WITH_CONDITIONS`**, hoặc **`REQUEST_CHANGES`**.
