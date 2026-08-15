# 🧠 CCBA Platform — Tổng Hợp Tri Thức & Bài Học Hệ Thống (Session Learnings)

> **Trạng thái:** Active & Consolidated  
> **Cập nhật gần nhất:** 2026-08-15 (Sau Tái cấu trúc Progressive Disclosure & Hierarchical AGENTS.md)  
> **Phiên bản lưu trữ lịch sử:** [`.md/knowledge/archive/session_learnings_v1_archive.md`](archive/session_learnings_v1_archive.md)  
> **Mục đích:** Tài liệu tri thức cốt lõi cô đọng ~30 nguyên lý thực chiến và các anti-patterns nguy hiểm cần tránh trên toàn bộ hệ sinh thái CCBA Agent Platform.

---

## 📑 Mục Lục Chủ Đề (Thematic Index)

1. [Trụ Cột 1: An Toàn Tiến Trình, Đồng Thời & Khóa Tệp (Process Safety & Locks)](#1-an-toàn-tiến-trình-đồng-thời--khóa-tệp)
2. [Trụ Cột 2: Tương Thích Đa Nền Tảng & Hệ Thống Tệp (Cross-Platform & Filesystems)](#2-tương-thích-đa-nền-tảng--hệ-thống-tệp)
3. [Trụ Cột 3: Kỷ Luật Kiểm Thử, Tốc Độ & Mocking Seams (Testing & Mocking)](#3-kỷ-luật-kiểm-thử-tốc-độ--mocking-seams)
4. [Trụ Cột 4: Quản Trị LLM, Token Budget & AI Gateway (LLM OS & Gateway)](#4-quản-trị-llm-token-budget--ai-gateway)
5. [Trụ Cột 5: Xử Lý Văn Bản, Bảng Biểu & Tài Liệu Pháp Lý (Document Engineering)](#5-xử-lý-văn-bản-bảng-biểu--tài-liệu-pháp-lý)
6. [Trụ Cột 6: Thiết Kế Kiến Trúc Deep Modules & AI-Navigability (Architecture Design)](#6-thiết-kế-kiến-trúc-deep-modules--ai-navigability)
7. [Trụ Cột 7: Quy Trình Quản Trị & Đồng Bộ Spoke-Hub (Governance & Synchronization)](#7-quy-trình-quản-trị--đồng-bộ-spoke-hub)

---

## 1. An Toàn Tiến Trình, Đồng Thời & Khóa Tệp

### 🌟 Core Patterns (Mẫu Tốt)

#### P1.1. Cross-Platform Safe Process Liveness Probe (Kiểm tra Tiến trình Sống/Chết An toàn)
* **Nguyên tắc:** **TUYỆT ĐỐI KHÔNG DÙNG `os.kill(pid, 0)` TRÊN WINDOWS**.
* **Thực tế:** Trên Windows, CPython ánh xạ `os.kill(pid, 0)` thành `TerminateProcess(hProcess, 0)`, làm **hạ sát ngay lập tức** tiến trình mục tiêu (bao gồm cả tiến trình của chính mình `os.getpid()` hoặc tiến trình mẹ host).
* **Chuẩn thực thi:**
  ```python
  def is_process_alive(pid: int | None) -> bool:
      if pid is None or pid <= 0:
          return False
      if sys.platform.startswith("win"):
          try:
              import ctypes
              kernel32 = ctypes.windll.kernel32
              handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
              if not handle:
                  return False
              exit_code = ctypes.c_ulong()
              is_active = (kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)) and exit_code.value == 259)  # STILL_ACTIVE = 259
              kernel32.CloseHandle(handle)
              return is_active
          except Exception:
              return False
      else:
          try:
              os.kill(pid, 0)
              return True
          except OSError:
              return False
  ```

#### P1.2. Resilient File Mutex Lock với Override & Expiration (`FileMutexLock`)
* **Ngữ cảnh:** Tránh xung đột phiên đăng nhập VIP (TVPL), ghi đè đồng thời vào file `.plan.lock` hoặc cache.
* **Giải pháp:** 
  - Tạo file lock nguyên tử chế độ độc quyền (`open(path, "x")`).
  - Ghi kèm `{"pid": os.getpid(), "timestamp": time.time()}`.
  - Tự động ghi đè (`Override`) nếu tiến trình sở hữu đã chết (`not is_process_alive(lock_pid)`) hoặc khóa bị quá hạn (`age >= expire_seconds`, mặc định 300s).
  - Kết hợp thread-level lock (`threading.Lock`) và process-level lock để an toàn đa luồng lẫn đa tiến trình.

#### P1.3. Safe Process Termination Invariant & Single-Instance Lock
* **Nguyên tắc:** Khi dọn dẹp hoặc duy trì đơn tiến trình (`ensure_single_instance()`), **bắt buộc phải loại trừ** cả tiến trình hiện tại (`os.getpid()`) và tiến trình cha (`os.getppid()`). Nghiêm cấm kích hoạt `taskkill` hoặc `proc.terminate()` lên `os.getppid()` để không làm sập Agent Server Host.

#### P1.4. Detached Background Execution để Tránh UI Timeout Watchdog
* **Ngữ cảnh:** Các câu lệnh chạy lâu (> 9 giây) như slow integration test hoặc crawler.
* **Giải pháp:** Không chạy đồng bộ kéo dài trên main turn làm kích hoạt bộ giám sát IDE Client UI Timeout Watchdog (`User cancelled agent execution`). Hãy chuyển sang chế độ background qua `safe_runner.py` / `run_command async` với `WaitMsBeforeAsync: 1000` và chờ Reactive Wakeup.

### ⚠️ Anti-Patterns (Cần Tránh)
* **AP1.1. Using `os.kill(pid, 0)` on Windows:** Gây tự sát tiến trình bí ẩn không có traceback.
* **AP1.2. Superficial "User Cancelled" Attribution:** Vội vã kết luận người dùng bấm Cancel khi thấy thông báo giao diện, thay vì dùng `/diagnosing-bugs` kiểm tra xem tiến trình con có bị ngắt socket/terminated hay không.
* **AP1.3. Unbounded Polling Loop:** Lặp `manage_task status` dồn dập trong cùng một turn thay vì nhường luồng (End Turn) để hệ thống tự đánh thức.

---

## 2. Tương Thích Đa Nền Tảng & Hệ Thống Tệp

### 🌟 Core Patterns (Mẫu Tốt)

#### P2.1. Dynamic AppData & Tool Discovery trên Windows
* **Giải pháp:** Định vị các công cụ hệ thống (Chrome, Winget, FFmpeg) tự động qua biến môi trường `%LOCALAPPDATA%`, `os.getenv("PROGRAMFILES")` hoặc fallback sang `Path.home() / "AppData" / "Local"` thay vì hardcode tên user `C:\Users\username`.

#### P2.2. Isolated Standard Stream Reconfiguration & Mypy Type Narrowing
* **Nguyên tắc:** Khi cần cấu hình UTF-8 cho console Windows (`sys.stdout.reconfigure(encoding='utf-8')`):
  1. **Chỉ đặt bên trong khối `if __name__ == '__main__':` hoặc hàm `main()`** để không làm hỏng bộ bắt luồng I/O (stream capture) của Pytest runner khi import.
  2. **Dùng Type Narrowing với `isinstance`** để Mypy tự động nhận diện `sys.stdout` là `io.TextIOWrapper` (tránh lỗi `[union-attr]` trên `TextIO` mà không cần `# type: ignore`):
     ```python
     if sys.platform == "win32":
         import io
         try:
             if isinstance(sys.stdout, io.TextIOWrapper):
                 sys.stdout.reconfigure(encoding="utf-8")
             if isinstance(sys.stderr, io.TextIOWrapper):
                 sys.stderr.reconfigure(encoding="utf-8")
         except Exception:
             pass
     ```


#### P2.3. Safe Workspace Sandbox & Path Traversal Guard
* **Giải pháp:** 
  - Thao tác tệp tạm trong `tempfile.TemporaryDirectory()`, đặt tệp repacked/unpacked trung gian bên trong thư mục sandbox này để tự động dọn dẹp sạch sẽ khi thoát context.
  - Khi nhận đường dẫn từ bên ngoài, luôn kiểm tra an toàn bằng `resolved_path.is_relative_to(sandbox_root.resolve())` để ngăn chặn tấn công vượt cấp (`../../`).

### ⚠️ Anti-Patterns (Cần Tránh)
* **AP2.1. Hardcoded Path Delimiters:** Dùng nối chuỗi chuỗi `/` hoặc `\` thay cho `pathlib.Path`.
* **AP2.2. Leaking Temp Files to Project Root:** Để rải rác tệp tạm `.tmp`, `.lock`, `.log` tại root thay vì gom vào `.md/scratch/` hoặc `.md/data/`.

---

## 3. Kỷ Luật Kiểm Thử, Tốc Độ & Mocking Seams

### 🌟 Core Patterns (Mẫu Tốt)

#### P3.1. Kỷ Luật Kiểm Thử 2 Tầng (2-Tier Test Speed Discipline)
* **Nguyên tắc:** 
  - **Tầng 1 (Fast Daily Loop):** Toàn bộ Unit Tests thông thường **bắt buộc phải chạy dưới 2.0 giây** (`pytest -m "not slow"`).
  - **Tầng 2 (Slow & Stress Tests):** Các test tích hợp mạng, tải Google Drive, hoặc stress test phải được gắn decorator `@pytest.mark.slow` hoặc `@pytest.mark.adversarial` để tự động loại trừ khỏi vòng lặp phát triển nhanh hàng ngày.

#### P3.2. Mocking Seam Alignment khi Di Chuyển Module
* **Nguyên tắc:** Khi refactor di chuyển hàm/biến từ script rời rạc (ví dụ: `scripts/legal/legal_sync.py`) vào thư viện lõi (`ccba_legal.sync`), **bắt buộc phải cập nhật đồng bộ các câu lệnh mock trong test suite** sang đường dẫn chính quy mới (`patch("ccba_legal.sync.GOOGLE_API_AVAILABLE", True)`). Tránh việc mock module cũ khiến code mới đọc biến thật và chạy vào nhánh timeout.

#### P3.3. Non-Portable OS-Specific Mocking Isolation
* **Nguyên tắc:** Không mock trực tiếp `@patch("ctypes.windll...")` ở decorator vì `windll` không tồn tại trên Linux runner làm vỡ CI. Hãy mock ở tầng abstraction độc lập hệ điều hành (`patch("module._is_process_alive", return_value=True)`).

#### P3.4. Scoped Test Execution & TDD Retry Cap (Tối đa 5 Vòng)
* **Nguyên tắc:** Nghiêm cấm chạy unscoped `pytest` toàn repository. Luôn chỉ định file test mục tiêu cụ thể (`pytest path/to/test_file.py`). Giới hạn tối đa 5 vòng lặp Red-Green-Refactor; nếu sau 5 vòng vẫn fail phải dừng lại commit WIP và xin ý kiến người dùng.

#### P3.5. Pytest Class Collection Protection cho Source Classes (`__test__ = False`)
* **Nguyên tắc:** Bất kỳ lớp nghiệp vụ nào trong mã nguồn có tên bắt đầu bằng tiền tố `Test*` (ví dụ: `TestSpeedHook`, `TestRunnerEngine`) sẽ bị Pytest tự động nhận diện nhầm là test class và phát sinh cảnh báo `PytestCollectionWarning` do có hàm khởi tạo `__init__`.
* **Giải pháp:** Bắt buộc khai báo thuộc tính lớp `__test__ = False` để Pytest bỏ qua khi quét test collection.

#### P3.6. Subprocess Binary Mocking trong Unit Tests Tầng 1
* **Nguyên tắc:** Khi kiểm thử các lớp wrapper tương tác với công cụ dòng lệnh bên ngoài (`npx --version`, `git --version`, `ffmpeg`), việc kích hoạt subprocess thực tế có thể tốn từ 2-4 giây trên Windows, làm vi phạm Rule P3.1 (< 2.0s).
* **Giải pháp:** Luôn mock `subprocess.run` trong các bài unit tests nhanh tầng 1 và phân tầng các bài kiểm thử thực tế vào tầng `@pytest.mark.slow`.

### ⚠️ Anti-Patterns (Cần Tránh)
* **AP3.1. Unscoped Full Pytest Run:** Kích hoạt quét test toàn bộ repo làm tràn context và chạm timeout.
* **AP3.2. Blind Retries without Instrumentation:** Thử lại test fail mà không thêm probe log hoặc thu hẹp seam qua `/diagnosing-bugs`.

---

## 4. Quản Trị LLM, Token Budget & AI Gateway

### 🌟 Core Patterns (Mẫu Tốt)

#### P4.1. API Circuit Breaker & Exponential Backoff
* **Ngữ cảnh:** Gọi LLM qua AI Gateway (:8090 LiteLLM Spark) trong batch pipeline.
* **Giải pháp:** Theo dõi tỉ lệ lỗi (429 Quota, 500 Server Error). Khi vượt ngưỡng (ví dụ: 5 lỗi liên tiếp), chuyển mạch sang trạng thái OPEN, tạm ngắt request và backoff lũy thừa (2s $\rightarrow$ 4s $\rightarrow$ 8s) để bảo vệ quota.

#### P4.2. Token Monitoring & Danger Zone (D-Zone) Thresholds (`TokenMonitor`)
* **Giải pháp:** Theo dõi context window token theo thời gian thực (hỗ trợ tiếng Việt và `cl100k_base`). Phát cảnh báo Danger Zone khi đạt 80% max tokens để kích hoạt tóm tắt/cắt tỉa context trước khi gặp lỗi tràn bộ nhớ.

#### P4.3. Append-Only Thread-Safe Audit Logging
* **Giải pháp:** Sử dụng cơ chế ghi nối đuôi (Append-only) với ISO-8601 UTC timestamp (`[2026-08-14T07:00:00Z] [EventType] Message`) vào file audit riêng biệt, mở file chế độ `"a"` với encoding `utf-8` trong khối try-except ngắn gọn, không giữ file handle dài.

#### P4.4. Late-binding Closure Capture trong Vòng Lặp
* **Giải pháp:** Tránh lỗi Ruff B023 khi định nghĩa callback trong vòng lặp bằng cách bind giá trị mặc định:
  ```python
  for filepath in files:
      def process_callback(match, filepath=filepath):
          ...
  ```

#### P4.5. 4 Model Archetypes & Bounded HTTP Timeout (Client Contract)
* **Giải pháp:** Phía client luôn cấu hình `timeout >= 30.0s` (chuẩn `60.0s`) để đảm bảo không ngắt kết nối trong khi AI Gateway failover qua 10 API keys. Phân tách rõ `ocr-primary` (OCR Ingestion thuần túy) với `gemini-3.7-flash` (Vision Multimodal + JSON schema reasoning).

#### P4.6. Reasoning Models Auto-Allocation & CoT Stripping
* **Giải pháp:** Tự động nâng ngân sách `max_tokens=16384` khi gọi các model suy luận sâu (`gemini-3.7-flash-high`, `claude-sonnet-4-6-thinking`) và tự động làm sạch thẻ `<think>` (`strip_thinking=True`) ở cấp độ SDK `ccba-ai` để chống rò rỉ Chain-of-Thought làm ô nhiễm Markdown và JSON downstream.

#### P4.7. Local Fast-Fail Circuit Breaker cho Mạng VPN
* **Giải pháp:** Tích hợp in-memory `CircuitBreaker` với 3 trạng thái (`CLOSED`, `OPEN`, `HALF_OPEN`) tự động ngắt nhanh các tác vụ khi kết nối Tailscale VPN tới Server Spark bị gián đoạn (ngưỡng 3 lỗi liên tiếp, 30s cooldown), tránh làm treo batch pipeline bởi các chu kỳ 60s timeout lặp lại.

#### P4.8. Multimodal Binary Base64 Data URI Filtering trong Privacy Guard
* **Giải pháp:** Khi quét rò rỉ API Keys (`PrivacyGuardHook`), tự động bỏ qua các chuỗi Data URI chứa base64 (`data:...;base64,...`). Việc này ngăn chặn 100% rủi ro false-positive match do chuỗi base64 ngẫu nhiên của file PDF/Image trùng khớp với pattern regex của API keys, đồng thời tiết kiệm đáng kể tài nguyên CPU.

#### P4.9. Per-Request Dynamic Timeout Overrides trong AI Gateway SDK
* **Giải pháp:** Trong các hàm gọi `AsyncAIClient.chat_multi()` / `chat()`, cho phép truyền tham số `timeout: float | None = None` để override timeout per-call khi gửi xuống `AsyncOpenAI(timeout=...)`. Giúp các tác vụ chuyển đổi tài liệu nặng (`mdconverter`) có thể chạy tới 600s mà không bị gò bó bởi timeout mặc định 60s của client.

#### P4.10. Dynamic Model Discovery over Static Hardcoded Counts
* **Nguyên tắc:** Tránh hardcode các con số tĩnh (như *"22 models"*) trong tài liệu kỹ thuật khi hạ tầng backend (LiteLLM/vLLM Gateway) có khả năng thay đổi và mở rộng động.
* **Giải pháp:** Sử dụng giao diện khám phá động `ai.models()` / `async_ai.models()` để truy vấn trực tiếp danh sách mô hình thời gian thực từ Gateway, và ghi tài liệu dưới dạng mở (ví dụ: *"50+ models (khám phá động qua `ai.models()`)"*).

#### P4.11. Progressive Instruction Disclosure Architecture (Kiến Trúc Phân Rã Chỉ Dẫn Lũy Tiến)
* **Nguyên tắc:** Tối ưu hóa Instruction Budget (~150–200 instructions). Tinh giản Root `AGENTS.md` thành mỏ neo định vị (< 25 dòng / ~300 tokens), phân rã các quy tắc chuyên biệt vào `docs/rules/` (`execution_guardrails.md`, `git_conventions.md`, `code_quality.md`) và thiết lập `CLAUDE.md` tại root để đạt cross-agent parity.

### ⚠️ Anti-Patterns (Cần Tránh)
* **AP4.1. Hardcoded API Keys:** Tuyệt đối không hardcode keys vào code/markdown. Luôn dùng biến môi trường hoặc `.env`.
* **AP4.2. Raw Exception Context Chaining (Ruff B904):** Dùng `raise NewException(...) from None` khi ném ngoại lệ mới trong block except không liên quan.
* **AP4.3. Reasoning Models trong Converter Fallback Chains:** Tuyệt đối không đưa các model có hậu tố `-thinking` vào chuỗi fallback của document converter (`mdconverter`) để tránh rò rỉ khối thẻ `<think>` làm ô nhiễm file Markdown đầu ra.
* **AP4.4. Monolithic Context Overloading (Ball of Mud Prompt):** Nhồi nhét hàng chục trang quy tắc tĩnh và các quy định hiển nhiên (như f-strings, type hints, bare except) vào `AGENTS.md` gốc, làm tiêu tốn ~80% ngân sách chỉ dẫn của LLM và gây phân tâm khi suy luận.


---

## 5. Xử Lý Văn Bản, Bảng Biểu & Tài Liệu Pháp Lý

### 🌟 Core Patterns (Mẫu Tốt)

#### P5.1. Dual-Parser & Markdown Table Reconstruction
* **Giải pháp:** Khi chuyển đổi văn bản hành chính sang Markdown, phát hiện các bảng biểu bị vỡ dọc (mất cột, trôi text). Sử dụng parser cấu trúc đối chiếu với file gốc `.docx` để khôi phục chuẩn xác bảng Markdown đa cột có căn lề.

#### P5.2. Open Knowledge Format (OKF) Bundle Structure
* **Quy chuẩn:** Đóng gói tài liệu tri thức thành bundle độc lập:
  - `metadata.yaml`: Chứa ID, tiêu đề, ngày ban hành, nguồn, băm SHA-256.
  - `[slug].md`: Nội dung chính đã được làm sạch thẻ suy nghĩ `<think>`, tiêm Anchor điều khoản `{#dieu-X}` và chuẩn hóa công thức.
  - `index.md`: Mục lục liên kết nội bộ chuẩn SEO và điều hướng.

#### P5.3. AST Parsing & Delta Patching cho Văn bản Pháp luật
* **Giải pháp:** Cắt lớp cấu trúc văn bản pháp luật thành Abstract Syntax Tree (Chương $\rightarrow$ Mục $\rightarrow$ Điều $\rightarrow$ Khoản $\rightarrow$ Điểm). Khi có văn bản sửa đổi bổ sung, sinh `DeltaPatch` định dạng YAML xác định hành vi (`replace`, `insert`, `abrogate`) và tự động hợp nhất thành Văn Bản Hợp Nhất (VBHN).

#### P5.4. Parse-Protection (Bảo Vệ Ghi Chú Thủ Công của Con Người)
* **Giải pháp:** Sử dụng cặp thẻ comment ẩn `<!-- DEVELOPER-NOTES-START -->` và `<!-- DEVELOPER-NOTES-END -->` để AI không bao giờ ghi đè lên các phân tích thủ công của kỹ sư khi cập nhật tài liệu tự động.

### ⚠️ Anti-Patterns (Cần Tránh)
* **AP5.1. Naive Regex Regex Table Replacement:** Dùng regex đơn giản làm mất merge cell hoặc xô lệch dữ liệu bảng số liệu.
* **AP5.2. Stripping YAML Comments on Re-dump:** Dùng `yaml.dump()` thô làm mất toàn bộ comment giải thích do con người viết trước đó.

---

## 6. Thiết Kế Kiến Trúc Deep Modules & AI-Navigability

### 🌟 Core Patterns (Mẫu Tốt)

#### P6.1. Deep Modules — "Giao Diện Nhỏ, Triển Khai Sâu" (High Leverage & Locality)
* **Nguyên tắc:** Một module tốt phải giấu kín sự phức tạp bên trong và chỉ phơi bày giao diện đơn giản nhất có thể ra ngoài.
* **Quy chuẩn Public Interface:**
  - Áp dụng nguyên lý *"Hide by convention, not by force"*: Thu gọn `__all__` tại `__init__.py` chỉ quảng cáo 2-3 Deep Seams chính yếu (`LegalIntelPipeline`, `LegalProcessor`, `LegalSyncEngine`).
  - Giữ nguyên cấu trúc file submodule bên trong để không làm gãy import path của test suite và caller sâu.

#### P6.2. Thin CLI Delegates (Script Facade Adapter Mỏng)
* **Nguyên tắc:** Các tệp script nằm trong `scripts/` (như `tvpl_vip_crawler.py`, `legal_sync.py`) **chỉ đóng vai trò là CLI Facade mỏng**: phân tích đối số dòng lệnh (`argparse`) và ủy thác 100% logic cho Deep Seams trong `packages/`. Tuyệt đối không tự viết lại logic nghiệp vụ tại script.

#### P6.3. Quy Trình Chẩn Đoán Lỗi Khoa Học 6 Bước (`/diagnosing-bugs`)
* **Nguyên tắc:** Khi gặp bug khó hoặc lỗi runtime bất thường:
  1. *Build a tight feedback loop* (Lệnh tái hiện lỗi trong < 2s).
  2. *Reproduce & Minimise* (Thu hẹp tối đa ngữ cảnh gây lỗi).
  3. *Hypothesise* (Lập danh sách 3-5 giả thuyết có thể bác bỏ được).
  4. *Instrument* (Gắn log định danh `[DEBUG-xxxx]` hoặc dùng debugger).
  5. *Fix + Regression Test* (Viết test chống tái phát tại đúng seam trước khi sửa).
  6. *Cleanup & Post-mortem* (Xóa sạch debug log và ghi nhận bài học).

#### P6.4. Two-axis Parallel Review (Đánh Giá Song Song Hai Trục)
* **Giải pháp:** Khi rà soát mã nguồn hoặc thiết kế phức tạp, spawn 2 subagents chạy song song độc lập: Subagent 1 quét trục **Standards & Smells** (Coding style, KISS, Type hints); Subagent 2 quét trục **Spec & Requirements** (Hợp đồng API, Edge cases).

#### P6.5. Caller Justification Gate & Anti-Shallow Seams (Rào Chắn Xác Thực Caller)
* **Nguyên tắc:** Trước khi đề xuất tạo thêm một Seam/Class/Wrapper mới, Agent bắt buộc phải chứng minh được có **ít nhất một caller/consumer thực tế** cần giao diện này. Nếu một Deep Seam đã tồn tại (như `ConversionPipeline`), nghiêm cấm tạo thêm một wrapper nông (như `MarkdownConverter`) chỉ để đổi tên mà không tăng leverage hoặc locality.

#### P6.6. Deepening via Extraction before Script Thinning (Bóc Tách Logic Trước Khi Tinh Gọn Script)
* **Nguyên tắc:** Khi tinh gọn một script dài (> 100 dòng), phải phân tích xem script đó là *Thin CLI đơn thuần* hay là *Domain Orchestration Script* (chứa routing, taxonomy, error recovery). Nếu chứa domain logic, **bắt buộc phải bóc tách logic đó đưa vào package lõi trước**, viết unit test cho seam mới, rồi mới chuyển script thành Thin CLI Delegate. Tuyệt đối không xóa bỏ logic nghiệp vụ chỉ để làm ngắn script.

#### P6.7. Safe Macro Injection (Bảo Tồn Macro Cá Nhân trong LibreOffice Basic)
* **Nguyên tắc:** Khi tự động cấu hình hoặc cập nhật macro LibreOffice (`Module1.xba`), **tuyệt đối không ghi đè toàn bộ tệp**. Phải đọc nội dung hiện tại và chỉ chèn subroutine mới vào ngay trước thẻ đóng `</script:module>`. Việc này bảo vệ 100% macro cá nhân do kỹ sư tự viết trước đó trên máy trạm.

#### P6.8. Pure Pydantic v2 DTOs over Hybrid Dict-Like Wrappers (Không Dùng Hybrid Shims)
* **Nguyên tắc:** Khi chuyển đổi các domain services sang Pydantic v2 `BaseModel`, hãy refactor dứt điểm toàn bộ callers, CLI scripts và tests sang truy cập thuộc tính tường minh (`res.score`, `res.model_dump()`).
* **Lợi ích:** Đảm bảo type safety tuyệt đối, hỗ trợ IDE auto-complete chuẩn xác, JSON serialization an toàn và loại bỏ hoàn toàn nợ kỹ thuật (technical debt).

#### P6.9. Deep Sub-package Modularization of Monolithic Scripts (Tái Cấu Trúc Monolith Thành Sub-Package)
* **Nguyên tắc:** Khi một script nội bộ phình to thành God Class (> 500-1000 dòng) xử lý đa nhiệm, hãy chuyển đổi nó thành một **Domain Sub-Package** chuyên biệt (như `scripts/governance/`, `scripts/scaffolding/`):
  1. *Polymorphic Base & Typed Reports:* Định nghĩa `BaseAuditor` và các DTOs bất biến (`NamedTuple`/`dataclass`) tại `base.py`.
  2. *Domain Sub-Auditors:* Phân chia mỗi nhiệm vụ thành 1 lớp độc lập có context cache riêng.
  3. *Coordinator & Thin Facade:* Giữ tệp script cũ làm Thin Facade re-export 100% public API để bảo toàn tương thích ngược cho mọi caller và test suite cũ.
  4. *Two-Tier Testing Discipline:* Viết unit tests cô lập cho từng sub-auditor mới (< 0.3s) và bảo tồn nguyên vẹn các bài test cũ.

#### P6.10. Coordinator Property Delegation Pattern (Đồng Bộ Thuộc Tính Workspace)
* **Nguyên tắc:** Khi một lớp Điều phối (Coordinator như `DocumentAuditor`) chứa nhiều sub-auditors/sub-services, các thuộc tính trạng thái (như `project_root`) phải được thiết kế dưới dạng `@property` và setter. Khi giá trị này bị thay đổi động từ bên ngoài (e.g., CLI flag `--root`), setter sẽ tự động cập nhật và lan truyền đồng bộ xuống toàn bộ các sub-components.

#### P6.11. Resilient Forwarding Shims with Direct CLI Support (Shims Tương Thích Kép)
* **Nguyên tắc:** Khi di dời/tái cấu trúc scripts thành domain sub-package (như `scripts/hooks/`, `scripts/scaffolding/`, `scripts/legal/`), các scripts facade cũ bắt buộc phải hỗ trợ cả hai phương thức thực thi:
  1. *Package Import:* `from scripts.hooks.test_speed_guard import ...`
  2. *Direct CLI Execution:* `python scripts/hooks/test_speed_guard.py ...`
* **Giải pháp:** Sử dụng mẫu Resilient Import với bootstrap `sys.path`:
  ```python
  try:
      from .base import HookContext
      from .speed import TestSpeedHook
  except (ImportError, ValueError):
      _PROJECT_ROOT = Path(__file__).resolve().parents[2]
      if str(_PROJECT_ROOT) not in sys.path:
          sys.path.insert(0, str(_PROJECT_ROOT))
      from scripts.hooks.base import HookContext
      from scripts.hooks.speed import TestSpeedHook
  ```

#### P6.12. Optional Soft Dependencies for Modular Subsystems (Nhập Khẩu Phụ Thuộc Mềm Tự Phục Hồi)
* **Nguyên tắc:** Sự thiếu vắng của một thư viện phụ trợ (như `PyYAML` trong `BrandHook` hoặc `python-docx` trong `Cleaners`) **tuyệt đối không được làm sập việc import toàn bộ subsystem**.
* **Giải pháp:** Bọc `import` trong khối `try...except ImportError` và cung cấp bộ dữ liệu mặc định (in-code fallback defaults) để hệ thống tiếp tục vận hành an toàn trong môi trường tối giản.

#### P6.13. Standardized DTO Clean Property for Guardrails (`context.clean_path` vs `context.path`)
* **Nguyên tắc:** Khi hệ thống hỗ trợ cơ chế bypass có kiểm soát (như tiền tố `APPROVED:` trên file path), toàn bộ các rào chắn con (Privacy, Naming, Speed Guard) bắt buộc phải truy cập thuộc tính đã làm sạch `context.clean_path` thay vì `context.path` thô, tránh việc đường dẫn bị phân tích sai và fallback ngoài ý muốn.



#### P6.14. Monorepo Hierarchical AGENTS.md for Package Deep Seams
* **Nguyên tắc:** Trong kiến trúc Monorepo, tận dụng cơ chế tự động hòa trộn `AGENTS.md` ở thư mục con vào ngữ cảnh.
* **Giải pháp:** Mỗi package (`packages/{pkg}/AGENTS.md`) sở hữu tệp chỉ dẫn cục bộ ngắn gọn (3-6 dòng) xác định rõ ràng Public Deep Seams (`from {pkg} import ...`), contracts (timeout, caching) và lệnh test độc lập (`pytest packages/{pkg}/tests`).

### ⚠️ Anti-Patterns (Cần Tránh)

* **AP6.1. Leaky Interface Exporting 30+ Symbols:** Xuất khẩu toàn bộ hàm con ra `__init__.py` làm rối loạn AI navigation.
* **AP6.2. Domain Drift:** Đặt file xử lý PDF vào package OOXML hoặc đặt logic cào web vào module phân tích xung đột.
* **AP6.3. Shallow-Wrapping Deep Seams (Bọc Nông trên Seam Sâu):** Tạo thêm một class/function bọc quanh một Deep Seam đã hoàn chỉnh chỉ để tạo "cảm giác dễ dùng", gây phân mảnh API và vi phạm nguyên lý KISS.
* **AP6.4. Unchecked Transport/SDK Assumptions:** Giả định các SDK/Client hỗ trợ các khả năng đặc thù (như xử lý multimodal bytes, async streams) mà chưa inspect code thực tế của thư viện, dẫn đến kế hoạch sai lệch nghiêm trọng.
* **AP6.5. Deleting Embedded Domain Logic:** Nhầm lẫn giữa mã boilerplate lặp lại với domain orchestration logic (dù đã có docstring) và xóa bỏ khi tinh gọn scripts.
* **AP6.6. Hybrid "Neither Fish Nor Fowl" Model Anti-Pattern (Lớp Mô Hình Lai Tạp):** Cài đặt đè `__getitem__` trên `BaseModel` để vừa hỗ trợ dot notation vừa hỗ trợ dict subscripting, gây mơ hồ khi phân tích kiểu dữ liệu tĩnh và làm sai lệch quá trình serialize JSON/dump.
* **AP6.7. Brittle File Path Instructions (Context Poisoning):** Ghi cứng đường dẫn script phụ trợ cụ thể (`scripts/safe_pytest.py`, `scripts/hooks/test_speed_guard.py`) trong tài liệu quy tắc. Khi refactor module, Agent bị ảo giác và tìm kiếm ở vị trí sai. Thay vào đó, áp dụng **Capability-First Instructions**.

---

## 7. Quy Trình Quản Trị & Đồng Bộ Spoke-Hub

### 🌟 Core Patterns (Mẫu Tốt)

#### P7.1. Reuse-First Gate (Cổng Bắt Buộc Kiểm Tra Tái Sử Dụng)
* **Nguyên tắc:** Trước khi viết bất kỳ tool/script mới nào tại Spoke:
  1. Tra cứu Hub Catalog (`platform-loader/catalog.yaml`).
  2. Đánh giá Cost-Benefit chi tiết (dependencies, network, complexity).
  3. Bắt buộc ghi mục `## Đánh giá khả năng tái sử dụng (Reuse Assessment)` trong `implementation_plan.md`.

#### P7.2. Automated Governance Gate (`DocumentAuditor`)
* **Giải pháp:** Sử dụng bộ điều phối `scripts/doc_auditor.py` tự động quét 5 trục chất lượng trước khi commit/release:
  - `LinkSymbolAuditor`: Kiểm tra link markdown và symbol code có tồn tại.
  - `SkillWorkflowAuditor`: Kiểm tra tính toàn vẹn của skills và workflows.
  - `LegalRegistryAuditor`: Xác thực tính hợp lệ của YAML registry.
  - `EnvVarAuditor`: Phát hiện rò rỉ keys hoặc thiếu biến môi trường.
  - `ArchitectureDriftAuditor`: Phát hiện drift kiến trúc so với `AGENTS.md`.

#### P7.3. Context-Aware Markdown Link Separation
* **Nguyên tắc Phân Biệt Ngữ Cảnh:**
  - *Trong Phản Hồi Chat UI:* Sử dụng `[file.py](file:///path/to/file.py)` để hỗ trợ người dùng bấm click mở file ngay trên IDE.
  - *Trong Tệp Lưu Trữ Git Repo (`.md`):* BẮT BUỘC sử dụng đường dẫn tương đối (repo-relative, ví dụ: `[doc.md](../../path/to/doc.md)`) để tương thích 100% trên GitHub Web UI và mọi máy trạm.

#### P7.4. Squash-and-Merge Standard for Feature Releases
* **Nguyên tắc:** Khi release feature branch về `main`, luôn áp dụng chiến lược **Squash and Merge** (`gh pr merge --squash --delete-branch`). Việc này giúp gộp toàn bộ các commits trung gian (sửa linter, test fix, feedback review) thành 1 commit duy nhất mang thông điệp tóm tắt hoàn chỉnh, giữ cho lịch sử nhánh `main` luôn tinh gọn và dễ truy vết.

#### P7.5. Automated Copilot PR Review Comment Audit Gate
* **Nguyên tắc:** Trước khi merge PR, tự động hóa việc đối soát các inline review comments từ Copilot bằng `scripts/validation/audit_pr_comments.py`, đảm bảo mọi phản hồi kỹ thuật đều được tiếp thu hoặc giải trình trong `walkthrough.md`.

### ⚠️ Anti-Patterns (Cần Tránh)
* **AP7.1. Editing YAML without Validation:** Sửa đổi YAML mà không chạy kiểm thử qua `yaml.safe_load()`.
* **AP7.2. Committing Unscanned Code:** Bỏ qua quy trình `/ccba-code-review` hoặc Governance Audit trước khi tạo PR.
* **AP7.3. Context-Blind Link Leakage (`file:///` in Git Repo Docs):** Vô thức đem cú pháp `file:///` từ giao tiếp chat vào nội dung tệp `.md` trong repo. Bộ điều phối `doc_auditor.py` đã tích hợp rào chắn cross-platform để chặn đứng và tự động sửa (`--fix`) lỗi này ngay tại local.


---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Tài liệu này là tài sản tri thức cốt lõi được cập nhật liên tục qua từng phiên làm việc của Platform.*
