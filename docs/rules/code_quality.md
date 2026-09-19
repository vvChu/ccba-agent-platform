# CCBA Code Quality & Engineering Standards

> **Tài liệu Tham chiếu Quy chuẩn Lập trình (Layer 2)**  
> Áp dụng cho phát triển mã nguồn Python, TypeScript, và thiết kế Deep Modules trên CCBA Platform.

---

## 1. Automation-First Quality Gate
- Mọi thay đổi mã nguồn Python bắt buộc phải pass qua hai cổng kiểm tra tự động trước khi hoàn tất:
  1. **Linter & Formatter**: `ruff check` (tuân thủ cấu hình trong `pyproject.toml`).
  2. **Static Type Checker**: `mypy` (chế độ strict mode, 100% type hints cho parameters và return types).

---

## 2. Deep Seams & Module Depth (KISS)
- **Deep Modules**: Thiết kế giao diện công khai phẳng, đơn giản (1-3 public functions/classes) ẩn giấu toàn bộ độ phức tạp nghiệp vụ bên trong (high depth, low surface area).
- **Tránh Shallow Modules**: Không tạo các class/wrapper mỏng chỉ ủy quyền 1-1 mà không thêm giá trị xử lý.
- **KISS**: Ưu tiên giải pháp đơn giản nhất. Nếu một vấn đề có thể giải quyết bằng 10-15 dòng code sạch trong file hiện có, hãy làm vậy thay vì tạo abstraction mới.

---

## 3. SDLC Implementation Loop
Khi triển khai mã nguồn dựa trên đặc tả (Spec):
1. **TDD (Test-Driven Development)**: Viết unit tests trước tại các điểm khớp nối công khai (seams).
2. **Continuous Validation**: Chạy kiểm tra kiểu (`mypy`) và chạy test suite liên tục.
3. **Review before Merge**: Chạy `/ccba-code-review` để quét code smells trước khi tạo PR.
4. **Merge Danger Triage**: Mọi PR và Kế hoạch Thực thi (`implementation_plan.md`) bắt buộc tự phân loại mức độ nguy hiểm: Khả năng đảo ngược (**One-way door** vs **Two-way door**) và Bán kính ảnh hưởng (**Localized** vs **Package-wide** vs **Monorepo-wide** vs **Spoke-affecting**) để tối ưu hóa thời gian review của con người.

---

## 4. Cognitive Skills Quality & Invariant Gates (Layer 2)
- Mọi Agent Skill thuộc hệ sinh thái CCBA phải tuân thủ Khung Quyết Định Hai Giai Đoạn (ADR-0057).
- Kỹ năng có nhiều chế độ hoạt động (multi-mode) bắt buộc phải xây dựng Tiêu chí hoàn thành động kiểm chứng đầy đủ từng mode, không để xảy ra tình trạng thiên lệch luồng mặc định gây hoàn thành non.
- Tuân thủ nguyên tắc Single Source of Truth trong các tài liệu tham chiếu vệ tinh (`references/*.md`, `MODES.md`), tuyệt đối không nhân bản các cảnh báo ràng buộc cờ.
- **Recompilation & Asset Synchronization Gate (HUB-ADR-0047, HUB-ADR-0058):**
  Khi tạo mới, chỉnh sửa nội dung hoặc bump version bất kỳ tệp `SKILL.md` nào, Agent **BẮT BUỘC** phải kích hoạt chuỗi 3 lệnh tái biên dịch và đồng bộ hóa tài sản nền tảng:
  1. `python scripts/governance/compile_catalog.py` (Cập nhật catalog SSOT `catalog.yaml`).
  2. `python scripts/governance/compile_skills_docs.py --write` (Đồng bộ Web Docs Portal, Markdown docs, và llms.txt).
  3. `python scripts/sync_hub_adr_matrix.py` (Đồng bộ Living Traceability Matrix nếu kỹ năng có viện dẫn hoặc điều chỉnh phạm vi ADR).

---

## 5. Clean Upstream Porting & Foreign Framework Pruning (KISS)
- **Tẩy uế tàn dư ngoại lai (Clean Dead Wood):** Khi chuyển đổi (port) hoặc nâng cấp bất kỳ kỹ năng nào từ nguồn thượng nguồn (ClaudeKit, external plugins), Agent **BẮT BUỘC** phải loại bỏ hoàn toàn:
  1. Các thẻ XML điều phối ngoại lai (ví dụ: `<tasks>`, `<task>`, `<action>`).
  2. Các hướng dẫn/tệp tin mô tả hệ thống quản lý tác vụ không tương thích (như Claude Native Tasks: `TaskCreate`, `TaskUpdate`, `TaskList`).
  3. Các lệnh giả định hoặc công cụ không tồn tại trong nền tảng CCBA (ví dụ: `/ck:*`, `/ultrathink`, `git-manager`, `AskUserQuestion`).
- **Nguyên tắc Tối Giản (KISS):** Mọi quy trình điều phối đa tác tử (Parallel Review, Codebase Scan) phải tinh gọn tối đa $\le 2$ subagents chuyên biệt (ví dụ: `Standards Worker` & `Spec Worker`), tuân thủ Single-Writer Protocol và chỉ xuất nháp vào sandbox `.system_generated/scratch/`.

---

## 6. Safe Headless External Process Fallback
- Khi viết kịch bản, hướng dẫn hoặc quy trình có thao tác mở tệp/giao diện ngoại vi trên máy trạm lập trình viên (ví dụ: mở tệp HTML báo cáo, tài liệu Word/PDF):
- Agent **BẮT BUỘC** phải bọc lệnh mở tiến trình trong khối xử lý lỗi an toàn đa nền tảng:
  ```powershell
  try {
      Start-Process "<absolute-path-to-file>"
  } catch {
      Write-Warning "Headless environment detected or browser unavailable. Please open manually: file:///<absolute-path-to-file>"
  }
  ```
- Tuyệt đối không để lệnh mở file trần không có xử lý ngoại lệ gây crash hoặc đứt gãy luồng thực thi tự động trong môi trường headless, CI runner, hoặc SSH sessions.

---

## 7. Cross-Platform Filesystem Hardening & Permissions Invariant
- **Bảo toàn quyền thực thi thư mục (`+x` trên POSIX):**
  - Khi gỡ bỏ cờ Read-Only (`_make_writable`), **TUYỆT ĐỐI CẤM** gán mode tĩnh (ví dụ `0o600`, `0o666`, `stat.S_IWRITE | stat.S_IREAD`) vì sẽ tước bỏ bit `stat.S_IXUSR` (`+x`) của thư mục trên Linux/macOS, gây ra `PermissionError: [Errno 13]` khi thao tác tệp con bên trong.
  - **Quy chuẩn bắt buộc:** Luôn bảo toàn các bit mode hiện có:
    ```python
    def _make_writable(p: Path) -> None:
        try:
            st = p.stat()
            p.chmod(st.st_mode | stat.S_IWUSR)
        except OSError:
            pass
    ```
- **Xử lý an toàn Windows NTFS Directory Junctions vs Symlinks (`safe_remove`):**
  - `shutil.rmtree` và `os.walk(..., topdown=False)` trên Windows không coi junction là symlink (`is_symlink() == False`), dẫn đến việc xóa nhầm dữ liệu bên ngoài target.
  - Bắt buộc duyệt `topdown=True`, kiểm tra cờ `FILE_ATTRIBUTE_REPARSE_POINT` (0x400) cho cả Python 3.10-3.11 (nơi `st_reparse_tag` bị khuyết thiếu trên `os.lstat`).
  - Xử lý junction như lá cây: dùng `os.rmdir(p)` trên Windows junction mà không đệ quy; dùng `p.unlink()` trên symlink.
- **Chặn đột biến quyền của Symlink/Junction Target:**
  - Tuyệt đối không gọi `os.chmod` lên symlink hoặc junction vì trên POSIX sẽ làm biến đổi quyền của tệp gốc bên ngoài.
- **Phân giải đích thư mục trong `safe_copy2`:**
  - Khi sao chép tệp ghi đè quyền Read-Only, nếu `dst` là thư mục, bắt buộc chuẩn hóa:
    `target_dst = (dst / src.name) if dst.is_dir() else dst`.



