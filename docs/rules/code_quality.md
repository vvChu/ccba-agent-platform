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

---

## 8. Clean Architecture & Decoupled Connection Layer (Inverted Coupling Prevention)
Khi xây dựng các bộ công cụ tích hợp dịch vụ ngoại vi (Google Drive, Cloud Storage, Database, External APIs):
1. **Ngưỡng Kích Hoạt (Trigger Threshold - Tuân thủ KISS):**
   - Chỉ bắt buộc tách riêng tầng kết nối khi tồn tại $\ge 2$ consumers độc lập (ví dụ: vừa Đẩy vừa Kéo dữ liệu) HOẶC dịch vụ yêu cầu xác thực phức tạp (OAuth refresh, credentials migration, session pooling, circuit breaking). Đối với các HTTP call đơn giản 5-10 dòng trong một module duy nhất, ưu tiên giữ gọn tại chỗ (tránh Shallow Modules).
2. **Phân Tách Rõ Rệt 2 Tầng:**
   - **Tầng Hạ Tầng Kết Nối (Connection/Client Factory):** Chuyên trách xác thực (OAuth, API tokens), giải quyết đường dẫn credentials (`~/.ccba/credentials/`), quản lý vòng đời client/session và xử lý lỗi mạng cơ sở (ví dụ: `drive_client.py`).
   - **Tầng Nghiệp Vụ Tiêu Thụ (Domain Consumers):** Các module xử lý luồng dữ liệu chuyên biệt (ví dụ: `drive_uploader.py` cho chiều Đẩy, `drive_ingestor.py` cho chiều Kéo, `notebooklm_sync.py` cho đồng bộ).
3. **CẤM Phụ Thuộc Ngược (No Inverted Coupling) & Quy Tắc Cây Lá (Leaf Dependency):**
   - Tuyệt đối KHÔNG để module Chiều Kéo (Ingestor/Reader) phụ thuộc ngược vào module Chiều Đẩy (Uploader/Writer) chỉ vì module đẩy được viết trước và có sẵn hàm kết nối. Cả hai phải là consumers ngang hàng.
   - Module hạ tầng kết nối (`*_client.py`) phải là **nút lá (leaf dependency)**: tuyệt đối không import ngược bất kỳ logic nghiệp vụ nào từ consumers để loại trừ vĩnh viễn lỗi Circular Import.
4. **Bảo Toàn Tương Thích Ngược & Tuân Thủ Linter (Zero-Breakage Re-export):**
   - Khi chuyển hàm kết nối sang module mới, module cũ BẮT BUỘC phải re-export lại và khai báo tường minh trong `__all__`, đảm bảo callers cũ không bị gãy và không vi phạm quy tắc linter `F401 (imported but unused)`.
5. **Tăng Tính Phát Hiện (Agent Ergonomics & Discoverability):**
   - Đặt tên module hạ tầng nhất quán (`*_client.py`), giúp AI Agents và kỹ sư định vị chức năng ngay tức thì mà không phải duyệt qua hàng trăm dòng mã nghiệp vụ phức tạp.

---

## 9. Pre-Evaluation Working Tree Fast-Fail & CI Parity cho Tác Tử Tự Hóa (Auto-Tuner Guardrails)
Khi thiết kế các pipeline tự động tối ưu hóa mã nguồn hoặc kỹ năng (như Nightly Auto-Tuner, GitRatchetOptimizer):
1. **Chặn Lỗi Trước Khi Đánh Giá (Pre-Evaluation Working Tree Fast-Fail):**
   - Mọi đột biến nội dung (mutation) sau khi áp dụng vào working tree BẮT BUỘC phải vượt qua kiểm tra vệ sinh tĩnh (`LinkAuditor`, syntax parser) **TRƯỚC KHI** kích hoạt hàm đánh giá tốn kém (`evaluate_content` / gọi LLM).
   - Bộ lọc kiểm tra tĩnh phải bao quát toàn diện: liên kết Markdown hỏng (`links`), ký hiệu mã giả định (`code_refs`), và biến môi trường chưa đăng ký (`env_vars`).
   - Nếu phát hiện vi phạm, hệ thống phải ROLLBACK ngay lập tức tệp trên đĩa về `best_content`, hủy bỏ iteration và không tiêu tốn bất kỳ token LLM đánh giá nào.
2. **Chỉ Dẫn Đột Biến An Toàn (Safe Heuristic Directives):**
   - Trong các mutator thao tác đơn tệp (single-file mutators như `tuner.py`), gợi ý cấu trúc tuyệt đối KHÔNG được chèn đường dẫn tương đối tĩnh giả định (ví dụ: `references/guide.md`) nếu tệp chưa hiện diện trên đĩa. Chỉ được dẫn link tới các tệp hiện hữu hoặc hướng dẫn qua mục lục text thuần.
3. **Tuyệt Đối Khớp Nối Công Cụ Kiểm Tra (True CI Parity):**
   - Các cổng Pre-PR Gate của Daemon và lệnh kiểm định cục bộ (`ccba_harness verify-patch --preset skill`) bắt buộc phải đồng bộ 100% với các bước kiểm tra của CI trên GitHub Actions (bao gồm cả `scripts/validate_docs.py . --src scripts,packages --changed`), đảm bảo mã tự động sinh ra luôn xanh 100% khi mở Pull Request.

---

## 10. Test Integrity & Anti-Potemkin Invariant (Kiểm Thử Thực Chất & Chống Test Giả Lập)
Khi viết unit tests cho các cơ chế kiểm định phòng vệ (Guardrails, Linters, Deletion Guards, Diff Auditors):
1. **Bắt buộc kích hoạt vi phạm thực tế (Trigger Before Pardon):**
   - Bài test kiểm tra ngoại lệ tha bổng (ví dụ: cờ `[DEPRECATED]` hoặc whitelist bypass) **BẮT BUỘC PHẢI THỰC SỰ XÓA BỎ** hoặc làm sai lệch đối tượng kiểm chuẩn trong văn bản đề xuất.
   - Nghiêm cấm giữ nguyên cấu trúc gốc trong văn bản đề xuất khiến tập hợp vi phạm rỗng (`missing_patterns == set()`), tạo ra các bài test Potemkin giả lập luôn pass mà mã nguồn kiểm tra ngoại lệ bên dưới chưa từng được thực thi.
2. **Kiểm chứng độc lập nhánh phủ định (Dual Assertion):**
   - Mọi test suite cho guardrail phải đi kèm cặp kiểm thử đối ứng:
     - Trường hợp không có thẻ ngoại lệ $\rightarrow$ Phải bắt lỗi thành công (`assert len(violations) > 0`).
     - Trường hợp có thẻ ngoại lệ hợp lệ $\rightarrow$ Phải tha bổng thành công (`assert len(violations) == 0`).
3. **Bao phủ toàn diện các ký tự phân cách (Separator Coverage):**
   - Bộ test cho parser/regex ranh giới bắt buộc phải kiểm thử độc lập cả 3 họ phân cách: phân cấp số thập phân (`.1`), hậu tố gạch nối (`-bis`, `-sub`), và gạch chéo (`/2`).

---

## 11. Hierarchical Regex Boundary Discipline (Kỷ Luật Ranh Giới Regex Cho Mã Phân Cấp)
Khi xây dựng các biểu thức chính quy (Regex) để trích xuất, đối soát hoặc kiểm tra mã định danh phân cấp (như `RULE-1.1`, `SEC-1`, `P01.01`):
1. **Cấm dùng bare `\b` đơn lẻ cho các mã có chứa số hoặc dấu nối:**
   - Trong Python Regex, ranh giới từ `\b` xác định ranh giới giữa `\w` và `\W`. Ký tự dấu chấm `.`, gạch nối `-`, và gạch chéo `/` đều là `\W`.
   - Do đó, `\b1\b` sẽ khớp với số `1` trong `1.1` hoặc trong `RULE-2.1`. Biểu thức `\bRULE-1.1\b` sẽ khớp với tiền tố của `RULE-1.1-bis`.
2. **Khuôn mẫu chuẩn mực bắt buộc:**
   - Đối với phân vùng/chương: Bắt buộc neo tiền tố cấu trúc rõ ràng kết hợp chặn ký tự phân cách:
     `rf"(?:SEC-|Miền\s+|Trụ\s+Cột\s+){sec_num}(?![.\-\/][\w\d])\b"`
   - Đối với quy tắc có phân cấp: Luôn bọc negative lookahead để loại trừ toàn bộ số phân cấp con hoặc hậu tố chữ/gạch nối/gạch chéo:
     `rf"\b{escaped}(?![.\-\/][\w\d])\b"`
