## Session Learnings - Kiến thức tích lũy phiên làm việc CCBA Legal Intel

## Cập nhật gần nhất: 2026-07-02

---

## Patterns (Mẫu tốt)

### 1. Đồng bộ và Tự động cập nhật RAG thời gian thực (Real-time Cloud RAG Sync)

- **Ngữ cảnh**: Khi nạp tài liệu từ Google Drive sang Google NotebookLM.
- **Vấn đề giải quyết**: Tránh việc phải tải lên/tải xuống và chạy lại script đồng bộ mỗi khi nội dung văn bản gốc thay đổi.
- **Giải pháp**: 
  1. Upload tệp Word `.docx` lên Drive dưới dạng **Google Docs trực tuyến** bằng cách chỉ định metadata `mimeType="application/vnd.google-apps.document"` khi gọi API Drive.
  2. Kéo file Google Doc này sang NotebookLM. Do NotebookLM liên kết trực tiếp với Drive Doc, mọi chỉnh sửa của người dùng trên Drive sẽ tự động đồng bộ sang ngữ cảnh RAG Cloud theo thời gian thực mà không cần chạy lại script.

### 2. Tháo gỡ lỗi phân quyền NotebookLM Drive API (Auto-Share Link View)

- **Ngữ cảnh**: Khi NotebookLM API trả về lỗi màu hồng `API returned no data for Drive source` đối với tệp tin vừa upload lên Drive.
- **Vấn đề giải quyết**: Giới hạn bảo mật của Google ngăn cản NotebookLM đọc dữ liệu từ tệp Drive cá nhân qua token API.
- **Giải pháp**: Sử dụng API Drive `permissions().create()` để thiết lập quyền đọc công khai có liên kết (`anyone/reader`) cho file Google Doc/PDF trên Drive trước khi kéo sang NotebookLM.

---

## Anti-patterns (Cách tránh)

### 1. Trích xuất Cookie tự động qua CDP cho các dịch vụ bảo mật cao của Google

- **Vấn đề**: Kể từ Google Chrome 127+, cơ chế mã hóa **App-Bound Encryption** trên Windows khóa chặt cookie của Chrome và chặn các tiến trình bên ngoài giải mã, dẫn đến việc lấy cookie qua CDP bị thiếu các mã bảo mật bắt buộc (`SID`, `__Secure-1PSIDTS`) khiến RAG bị từ chối truy cập.
- **Thay thế bằng**: Sử dụng CLI đăng nhập chính thống của thư viện `python -m notebooklm login` để kích hoạt phiên Chromium chuẩn hóa và lưu trữ `storage_state.json`.

---

## Solutions (Giải pháp tham chiếu)

### 1. Lỗi thiếu tham số bắt buộc trong API `add_drive` của `notebooklm-py`

- **Vấn đề**: Gọi `client.sources.add_drive(notebook_id, file_id)` báo lỗi: `missing 1 required positional argument: 'title'`.
- **Giải pháp**: Bổ sung tham số `title` (tên hiển thị nguồn trên Cloud) làm tham số bắt buộc:
  ```python
  source = await client.sources.add_drive(
      notebook_id=notebook_id,
      file_id=drive_file_id,
      title=file_name_stem,
      wait=True
  )
  ```
- **Liên kết**: [.md/scratch/sync_processed_docs.py](file:///d:/GitHubProjects/ccba-agent-platform/.md/scratch/sync_processed_docs.py)

---

## Configurations (Cấu hình tối ưu)

| Setting | Value | Lý do | Áp dụng khi |
| --------- | ------- | ------- | ------------- |
| AI_MODEL | gemini-3.1-flash-lite | Phản hồi đầy đủ không bị đứt đoạn, tốc độ nhanh, tối ưu token | Chạy AI Gateway đối soát pháp lý |

---
---

## Refactor: `ccba_legal/harness` (2026-07-03)

### Kiến trúc `harness/` package sau khi tách

| Sub-module | Dòng | Trách nhiệm |
|---|---|---|
| `_state.py` | ~150 | Shared mutable state (counters, caches, originals) |
| `_sql_monitor.py` | ~280 | SQLite connection/query interception |
| `_file_monitor.py` | ~1150 | File-open hooks, AST scanning, inode tracking |
| `_process_monitor.py` | ~1230 | Subprocess & OS-call monitoring |
| `_guard.py` | ~550 | `HarnessGuard` class + global hook management |
| `__init__.py` | ~138 | Thin re-export wrapper (`# ruff: noqa: F401`) |

### Patterns

**1. Import stdlib phải copy thủ công khi extract code ra file mới**
- **Vấn đề**: Khi cut-paste code từ `__init__.py` sang sub-module, các stdlib imports ở cấp module (`ast`, `base64`, `fnmatch`, `glob`) không được tự động copy theo.
- **Hậu quả**: `NameError: name 'ast' is not defined` bị catch silently bởi `except Exception` → toàn bộ AST security scanning bị bypass mà không có error nào visible.
- **Phát hiện**: Chạy `ruff check` → F821 `Undefined name 'base64'`, `Undefined name 'ast'`.
- **Bài học**: Sau khi extract code ra file mới, luôn chạy `ruff check` ngay lập tức để phát hiện undefined names.

**2. Mock patch path phải theo đúng namespace thực tế**
- `@patch("ccba_legal.harness._original_popen")` → sai (sau khi tách ra `_process_monitor.py`)
- `@patch("ccba_legal.harness._process_monitor._original_popen")` → đúng
- `@patch("ccba_legal.harness.subprocess.run")` vẫn hoạt động vì `subprocess` là module singleton — patching qua alias `__init__.subprocess` affect cùng object trong `_guard.subprocess`.

**3. Backward-compat re-export module: dùng `# ruff: noqa: F401`**
- Khi `__init__.py` là pure re-export module, F401 warnings là false positives.
- Thêm `# ruff: noqa: F401` ở top file thay vì noqa từng dòng.

**4. `TYPE_CHECKING` cho forward references tránh circular import**
- Khi `_file_monitor.py` và `_process_monitor.py` cần type `HarnessGuard` (defined in `_guard.py` which imports them):
  ```python
  from typing import TYPE_CHECKING
  if TYPE_CHECKING:
      from ccba_legal.harness._guard import HarnessGuard
  ```
- Kết hợp với `from __future__ import annotations` → annotations không được evaluate tại runtime → không có circular import.

**5. Security constraint: strict type check**
- `_get_active_guards()` dùng `type(active_guards) is list` (KHÔNG phải `isinstance`) để block `FakeList` bypass attack.

### Anti-patterns

- **Không chạy ruff sau mỗi bước extract** → silent bug (AST bypass) tồn tại nhiều bước.
- **Copy toàn bộ import block từ `__init__.py` vào sub-module** → leftover migration stubs gây F401, F811.

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Pháp lý xây dựng"
bundle: "_core"
---

## PR Checks, Formatting & Portability (2026-07-03 - Evening)

### Patterns

**1. Sử dụng đường dẫn tương đối (repo-relative forward-slash paths) cho data registries**
- **Vấn đề**: Việc sử dụng đường dẫn tuyệt đối (absolute path) như `D:\GitHubProjects\...` trong tệp cấu hình/đối soát (`sources_registry.yaml`) khiến dự án không thể di chuyển sang máy tính khác (non-portable) và gây lỗi CI.
- **Giải pháp**: 
  1. Chuẩn hóa toàn bộ khóa đường dẫn trong registry sang dạng tương đối bắt đầu bằng `.md/` với dấu gạch chéo `/` (OS-independent).
  2. Bổ sung helper function trong `ccba-notebooklm` để tự động chuẩn hóa mọi đường dẫn tuyệt đối sang tương đối trước khi ghi/so khớp registry.
  ```python
  def normalize_to_relative(path_str: str, root_path: Path) -> str:
      try:
          p = Path(path_str).resolve()
          if p.is_relative_to(root_path):
              return p.relative_to(root_path).as_posix()
      except Exception:
          pass
      return path_str.replace("\\", "/")
  ```

**2. Quản lý các file bị `.gitignore` chặn nhưng cần thiết cho CI**
- **Vấn đề**: Thư mục `.agents/` bị bỏ qua trong `.gitignore` toàn cục của dự án. Khi tạo thêm tệp tham chiếu như `.agents/skills/xia/MODES.md`, tệp này không được đẩy lên GitHub, dẫn đến lỗi check link `Broken Link Error: (MODES.md) - File does not exist` khi chạy `validate_docs.py` trên CI.
- **Giải pháp**: Sử dụng `git add -f [file_path]` để cưỡng chế theo dõi (force-track) các tệp tài liệu quan trọng trong thư mục bị ignore, đảm bảo CI checkout đầy đủ.

### Anti-patterns

- **Commit `notebook_id` thực tế lên Git**: Việc commit thông tin xác thực/ID cụ thể lên `workspace_context.yaml` có thể gây xung đột hoặc rò rỉ dữ liệu của nhà phát triển. Cần đưa về cấu hình trống mặc định (`notebook_id: ""`) trước khi đẩy lên PR.

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Pháp lý xây dựng"
bundle: "_core"
---

## Architecture Refactor: Candidate 1 & 4 — QC LLM Integration (2026-07-03 - Evening)

### Bối cảnh phiên

Hoàn thành toàn bộ 6 Candidates từ Architecture Review 2026-07-03. PRs đã merge: #38 (ccba-harness), #39 (idop templates), #40 (ccba-notebooklm), #41 (QC LLM integration + cross-package deps). Test suite: 383 passed.

---

### Patterns

**1. Double-Pass Adversarial Review — Code-First trước khi plan**
- **Ngữ cảnh**: Nhận yêu cầu "lập kế hoạch triển khai Candidate X" từ Architecture Review.
- **Vấn đề**: Báo cáo kiến trúc là snapshot tại thời điểm tạo; code có thể đã partial-migrate. Candidate 1 tưởng cần migration lớn, thực tế 4 engines đã dùng `ccba_ai` rồi.
- **Giải pháp**: Luôn `grep` pattern trước: `grep -r "from ccba_ai" .agents/skills/*/scripts/`. Chỉ plan những gì grep xác nhận là *chưa* done.
- **Impact**: Tiết kiệm ~2h tránh rewrite code đã đúng. Kế hoạch thu hẹn từ 5 tasks lớn xuống 4 gaps nhỏ.

**2. `importlib.util` loader cho peer skill scripts (no sys.path pollution)**
- **Ngữ cảnh**: Scripts trong `.agents/skills/*/scripts/` là standalone, không phải installable packages. Cần import từ sibling skill.
- **Vấn đề**: `sys.path.insert(0, ...)` mutate global interpreter state cho toàn bộ process.
- **Giải pháp**:
  ```python
  def _load_script_module(skill_name: str, script_name: str):
      """Load sibling skill script without sys.path mutation."""
      script_path = _SKILLS_ROOT / skill_name / "scripts" / f"{script_name}.py"
      spec = importlib.util.spec_from_file_location(script_name, script_path)
      module = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(module)
      return module
  ```
- **Trade-off**: Module-level code bị re-execute mỗi lần load. Nếu có side effects nặng, cache result vào biến module-level.
- **Nguồn**: PR #41, `orchestrator.py`

**3. Hard vs Optional dependency cho `pyproject.toml`**
- **Rule**: Nếu `import` là unconditional module-level → `dependencies = [...]` (hard). Nếu `import` nằm trong `try/except ImportError`, lazy trong function, hoặc `if TYPE_CHECKING` → `optional-dependencies.feature = [...]`.
- **Ví dụ phiên này**:
  - `ccba-legal-intel`: `from ccba_ai import ai` ở module level → hard dep
  - `mdconverter`: `from ccba_ai import ai` trong `try` block → `optional-dependencies.ai`

**4. `asyncio_mode = "auto"` cho pytest với async-heavy package**
- Thêm vào `[tool.pytest.ini_options]` trong `pyproject.toml` để toàn bộ `async def test_*` được collect tự động, không cần `@pytest.mark.asyncio` từng function.

---

### Anti-patterns

**1. Chuỗi `replace_file_content` liên tiếp trên cùng file → duplicate imports**
- Hai lần replace độc lập trên `orchestrator.py` đã thêm `import importlib.util` hai lần.
- **Phòng tránh**: Dùng `multi_replace_file_content` cho non-contiguous edits. View file sau mỗi edit quan trọng.

**2. `__all__` không có nhóm comment → khó scan**
- Khi `__all__` >10 items, thêm category comment: `# Singletons`, `# Client classes`, `# Utilities`, `# Models`.

---

### Configurations

| Setting | Value | Lý do | Áp dụng khi |
| --------- | ------- | ------- | ------------- |
| `asyncio_mode` | `"auto"` | Không cần decorator mỗi test | Package có async interface |
| dep type | `optional[ai]` | lazy import trong `try` block | mdconverter `form_cleaner` |
| dep type | `hard` | unconditional module-level import | `ccba-legal-intel` parser |

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

applies_to:
  - "Phần mềm"
bundle: "_core"
---

## Architecture Deepening: Candidate 2, 3, 4, 5, 6 & 7 — Monolith Splitting and Interface Consolidation (2026-07-03 - Night)

### Bối cảnh phiên

Hoàn thành trọn vẹn tất cả 7 ứng cử viên tái cấu trúc kiến trúc (Candidates) từ báo cáo Architecture Review. Đã merge các PR: #42 (Gộp ccba-ooxml dùng chung), #43 (Narrow ccba-notebooklm), #44 (Tách monolith docx document.py), #45 (Tách PDF page-render dùng chung), #46 (QC Protocols seam), #47 (Sửa mdconverter decoy init), #48 (Gom vision.py vào pipeline.py). Bộ kiểm tra xanh 100% (388 passed, 2 skipped).

---

### Patterns

**1. Tách Monolith bằng mô hình Ủy quyền (Delegation Pattern) giữ nguyên tương thích ngược**
- **Ngữ cảnh**: Cần chia nhỏ một file lớn trộn lẫn nhiều domain nghiệp vụ độc lập (như quản lý comment và tracked changes trong `document.py`) nhưng các callers cũ vẫn mong muốn giao diện gọi của class chính không đổi.
- **Giải pháp**:
  1. Trích xuất logic domain A sang `comment_engine.py` (với class `CommentEngine`).
  2. Trích xuất logic domain B sang `change_engine.py` (helpers).
  3. Class chính `Document` đóng vai trò là Orchestrator mỏng, khởi tạo Engine và chuyển tiếp (delegates) các lời gọi hàm tương thích ngược (`add_comment`, `reply_to_comment`) trực tiếp tới `CommentEngine`.
  4. Class editor chính `DocxXMLEditor` delegating các phương thức tracked changes tới helpers trong `change_engine.py`.
- **Lợi ích**: Giảm dung lượng file chính từ 1,277 dòng xuống ~400 dòng mà không làm gãy giao diện công khai hiện có.

**2. Thiết lập Seam bằng Python `typing.Protocol` (Structural Subtyping)**
- **Ngữ cảnh**: Nhiều thành phần độc lập (Discovery, Audit, Reporter) có cấu trúc đầu vào và đầu ra khác biệt nhưng cùng phối hợp trong một pipeline chung (`orchestrator.py`), ta muốn thiết lập giao diện lỏng lẻo (loose coupling) để mock kiểm thử tĩnh.
- **Giải pháp**:
  1. Khai báo các class Protocol trong thư viện dùng chung `ccba-ai` như `QCAuditEngine`, `QCReporterEngine` sử dụng `@runtime_checkable` decorator.
  2. Sử dụng type hints Protocol trong `orchestrator.py` thay vì import trực tiếp lớp cụ thể.
  3. Viết mock classes (ví dụ `MockAuditEngine`) thỏa mãn signature của Protocol trong unit tests. Điều này cho phép chạy mock test suite độc lập cho orchestrator mà không cần đĩa thực hay AI Gateway.

**3. Khắc phục Unicode escape sequence error trên PowerShell CLI**
- **Vấn đề**: Khi gõ lệnh gọi CLI của GitHub (`gh pr create --body "..."`) bằng PowerShell, nếu nội dung body chứa đường dẫn file Windows dạng `\u` (ví dụ: `\utilities.py`), PowerShell sẽ parse nhầm thành ký tự unicode bị lỗi escape sequence (`The Unicode escape sequence is not valid`).
- **Phòng tránh**: Luôn chuyển đổi ký tự dấu gạch chéo ngược Windows `\` thành gạch chéo xuôi `/` (ví dụ: `utilities.py` hoặc `packages/`) trong chuỗi tham số body truyền cho PowerShell để tránh parser crash.

**4. Khai báo Xml Namespaces đầy đủ khi thiết lập Mock XML Templates**
- **Vấn đề**: Khi tạo XML mock thô phục vụ unit test, nếu sử dụng namespace prefix (như `w14:paraId="1111"`) mà không định nghĩa namespace trên nút gốc (`xmlns:w14="..."`), trình parser `defusedxml` sẽ crash lập tức với lỗi `unbound prefix: line X, column Y`.
- **Giải pháp**: Luôn khai báo đầy đủ các namespaces được sử dụng (`xmlns:w`, `xmlns:w14`) trên thẻ root của tài liệu XML mock.

---

### Anti-patterns

- **Decoy Init Pattern (Namespace mờ mịt)**: Tệp tin `__init__.py` chỉ export cấu hình rỗng, ép caller phải import sâu từ module con bên trong (`from mdconverter.core.pipeline import ConversionPipeline`). Gây rò rỉ chi tiết cài đặt và làm cấu hình module bị nông. Cần export trực tiếp các core class sử dụng tại root `__init__.py`.
- **Duplicate PyMuPDF (`fitz`) file openers**: Việc tự viết `fitz.open()` và lưu `get_pixmap()` thô ở nhiều nơi khác nhau không giải phóng file handle đúng cách trong khối `try-finally` gây rò rỉ bộ nhớ. Phải đưa về hàm utility tập trung của thư viện xử lý PDF (`render_page_to_image`).

---

### Configurations

| Setting | Value | Lý do | Áp dụng khi |
| --------- | ------- | ------- | ------------- |
| `runtime_checkable` | `@runtime_checkable` | Cho phép sử dụng `isinstance(mock, Protocol)` | Kiểm tra sự tuân thủ Protocol trong test |

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

applies_to:
  - "Phần mềm"
bundle: "_core"

---

## Architecture Deepening & Knowledge Quality Refactor (2026-07-04 - Morning)

### Bối cảnh phiên
Hoàn thành xuất sắc 100% 5 đợt rà soát chất lượng tri thức (skills & workflows). Thực hiện thành công cải tiến kiến trúc codebase vòng 2: động hóa model LLM (`mock_debugger.py`, `assess_upstream_features.py`) và định vị các đường dẫn cục bộ về Hub trung tâm. Nâng cấp toàn diện các kỹ năng cốt lõi `/ccba-xia` (sát nhập TDD, Socratic Grilling, Domain Alignment), `/ccba-grilling` (sát nhập Grill with Docs), và `/ccba-platform` (sửa broken paths, động hóa Hub, tích hợp tự động kiểm tra VPN và Interactive Setup cấu hình Spoke).

---

### Patterns

**1. Phân giải đường dẫn tương đối động thông qua `Path(__file__)`**
- **Ngữ cảnh:** Định vị thư mục clone, tệp tracking SHA, và file báo cáo của các scripts đồng bộ khi hệ thống được phân phối.
- **Vấn đề:** Sử dụng relative paths từ CWD (`Path(".md/scratch/...")`) sẽ bị lệch hướng và sinh thư mục rác khi chạy từ Spoke con. Cứng hóa đường dẫn (`D:/GitHubProjects/...`) phá vỡ tính di động.
- **Giải pháp:** Phân giải động bằng cách neo vào gốc file script đang chạy:
  ```python
  PLATFORM_ROOT = Path(__file__).resolve().parents[1]
  REPOS_CONFIG = [
      {
          "type": "engineer",
          "local_path": PLATFORM_ROOT / "claudekit-engineer",
          "sha_file": PLATFORM_ROOT / ".md/scratch/claudekit_last_sha.txt"
      }
  ]
  ```

**2. Tích hợp Liveness Check & Interactive Setup vào Bootstrap Skill**
- **Ngữ cảnh:** Khi khởi động global skill điều phối (`ccba-platform`) trên dự án Spoke mới.
- **Vấn đề:** Chương trình crash do mất kết nối VPN đến Spark Server, thiếu cấu hình `.env`, hoặc thiếu file cấu hình dự án `workspace_context.yaml`.
- **Giải pháp:**
  - Tự động chạy lệnh ping/curl nhanh đến Spark LiteLLM URL (`http://100.83.192.30:8090/v1`) trước khi hiển thị menu, hiển thị cảnh báo hướng dẫn bật Tailscale VPN nếu lỗi.
  - Phỏng vấn tương tác người dùng từng câu hỏi một (one-by-one) về các cấu hình thiếu (như chọn GitHub/local task manager, bộ môn QC) rồi tự ghi nhận vào `workspace_context.yaml` để tự động hóa setup.

**3. Khóa hành vi port code bằng Test-Driven Porting (TDD)**
- **Ngữ cảnh:** Chuyển dịch mã nguồn (porting) tính năng từ repository ngoài vào Platform.
- **Vấn đề:** Rủi ro lệch logic nghiệp vụ hoặc cấy ghép code không hoạt động.
- **Giải pháp:** Cưỡng chế quy trình viết/port test case của tính năng nguồn sang trước và chứng kiến nó chạy lỗi (Red), sau đó mới port logic code nghiệp vụ sang để test pass (Green) trước khi refactor.

---

### Anti-patterns

**1. Tham chiếu ảo ảnh (Phantom Script Reference)**
- Tham chiếu và yêu cầu Agent chạy một script không hề tồn tại thực tế trong codebase (`scripts/repomix_pack.py`). Luôn luôn grep xác minh sự tồn tại của script trước khi đưa vào tài liệu quy trình.

**2. Hardcoded LLM Model Selection**
- Ghi cứng tên model `model="gemini-3-flash"` trong code python. Gây crash API khi model bị bãi bỏ hoặc đổi tên trên cloud. Cần loại bỏ hoặc thay thế bằng default model của client để tự động nội suy từ biến môi trường `AI_MODEL`.

**3. Inconsistent CLI vs Slash Command Syntax**
- Khác biệt cú pháp gọi lệnh trong tài liệu hướng dẫn (`/ccba-kit xia` so với `/ccba-xia` thực tế đăng ký). Luôn thống nhất cú pháp public với workflow registration để tránh nhầm lẫn cho Agent và kỹ sư.

---

### Configurations

| Setting | Value | Lý do | Áp dụng khi |
| --------- | ------- | ------- | ------------- |
| `CCBA_HUB_PATH` | Biến env hệ thống | Điểm neo tuyệt đối cho Platform Hub | Mọi dự án Spoke |
| `workspace_context.yaml` | `issue_tracker: "local_json"` | Quản lý task cục bộ qua file JSON | SOLO / Offline Projects |

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

applies_to:
  - "Phần mềm"
bundle: "_core"
---
