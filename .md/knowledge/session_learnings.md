# 🧠 CCBA Platform — Tổng Hợp Tri Thức & Bài Học Hệ Thống (Session Learnings)

> **Trạng thái:** Active & Consolidated  
> **Cập nhật gần nhất:** 2026-08-16 (Chuẩn hóa 8 Trụ Cột Tri Thức, ADR 0041-0043 & Server Spark)  
> **Phiên bản lưu trữ lịch sử:** [`.md/knowledge/archive/session_learnings_v1_archive.md`](archive/session_learnings_v1_archive.md)  
> **Mục đích:** Tài liệu tri thức cốt lõi cô đọng ~60 nguyên lý thực chiến và các anti-patterns nguy hiểm cần tránh trên toàn bộ hệ sinh thái CCBA Agent Platform.

---

## 📑 Mục Lục Chủ Đề (Thematic Index)

1. [Trụ Cột 1: An Toàn Tiến Trình, Đồng Thời & Khóa Tệp (Process Safety & Locks)](#1-an-toàn-tiến-trình-đồng-thời--khóa-tệp)
2. [Trụ Cột 2: Tương Thích Đa Nền Tảng & Hệ Thống Tệp (Cross-Platform & Filesystems)](#2-tương-thích-đa-nền-tảng--hệ-thống-tệp)
3. [Trụ Cột 3: Kỷ Luật Kiểm Thử, Tốc Độ & Mocking Seams (Testing & Mocking)](#3-kỷ-luật-kiểm-thử-tốc-độ--mocking-seams)
4. [Trụ Cột 4: Quản Trị LLM, Token Budget & AI Gateway (LLM OS & Gateway)](#4-quản-trị-llm-token-budget--ai-gateway)
5. [Trụ Cột 5: Xử Lý Văn Bản, Bảng Biểu & Tài Liệu Pháp Lý (Document Engineering)](#5-xử-lý-văn-bản-bảng-biểu--tài-liệu-pháp-lý)
6. [Trụ Cột 6: Thiết Kế Kiến Trúc Deep Modules & AI-Navigability (Architecture Design)](#6-thiết-kế-kiến-trúc-deep-modules--ai-navigability)
7. [Trụ Cột 7: Hệ Sinh Thái Hub-Spoke, Tiếp Nhận & Đồng Bộ (Spoke-Hub Ecosystem & Sync)](#7-hệ-sinh-thái-hub-spoke-tiếp-nhận--đồng-bộ)
8. [Trụ Cột 8: Quản Trị Doanh Nghiệp IDOP, Server Spark & Viện IBST (ADR 0041-0043)](#8-quản-trị-doanh-nghiệp-idop-server-spark--viện-ibst-adr-0041-0043)

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

#### P1.5. Event-Loop-Bound Primitives Concurrency Invariant
* **Nguyên tắc:** Khi xây dựng wrapper đồng bộ (`convert()` / `run_audit_sync()`) cho các async pipeline sở hữu asyncio primitives (như `asyncio.Semaphore`, `asyncio.Lock`), **tuyệt đối không** dùng `ThreadPoolExecutor` + `asyncio.run()` để lách khi có event loop đang chạy.
* **Hậu quả:** Primitives gắn chặt với event loop gốc sẽ gây lỗi `"bound to a different event loop"` hoặc sinh lỗi concurrency ngầm.
* **Chuẩn thực thi (Fail Fast):**
  ```python
  def convert_sync(...) -> Result:
      try:
          loop = asyncio.get_running_loop()
      except RuntimeError:
          loop = None
      if loop and loop.is_running():
          raise RuntimeError(
              "Sync method cannot be called from within a running event loop. "
              "Please use 'await async_method()' directly."
          )
      return asyncio.run(async_method(...))
  ```

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

#### P2.4. Cross-Platform CP1252 Terminal Encoding Safe Logging (Ghi Nhật Ký An Toàn Trên Windows)
* **Nguyên tắc:** Trên Windows, terminal mặc định (`cp1252` hoặc `cp936`) sẽ phát sinh lỗi `UnicodeEncodeError: 'charmap' codec can't encode character...` khi in trực tiếp các ký tự unicode nâng cao (như emoji 🔍, 🚀, ❌, mũi tên `→`, `│`).
* **Chuẩn thực thi:** Khi định dạng log xuất ra console/terminal:
  - Khuyến nghị sử dụng chuẩn ASCII tương đương (ví dụ: `->` thay vì `→`, `[OK]` thay vì `✅`, `*` thay vì `•`).
  - Hoặc bọc hàm in bằng bộ giải mã an toàn `text.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(...)`.

#### P2.5. Universal Branch Naming Parity Invariant (`feat/...` vs `feature/...`)
* **Nguyên tắc:** Đồng bộ hóa tuyệt đối tiền tố branch sang `feat/short-description` (hoặc `fix/`, `docs/`, `refactor/`, `experiment/`) trên toàn bộ tài liệu hiến pháp, quy ước Git (`git_conventions.md`), tài liệu đóng góp (`CONTRIBUTING.md`), và kịch bản khởi tạo (`ccba-new-feature.md`).
* **Lợi ích:** Tránh sự phân mảnh và cảnh báo phản biện từ các công cụ kiểm tra tĩnh (như GitHub Copilot PR Review Bot) khi hướng dẫn quy trình cho kỹ sư.

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

#### P3.7. Subprocess-Spawning Tests Categorization (SLA Guard)
* **Nguyên tắc:** Mọi file test thực hiện sinh tiến trình con (`subprocess.run`, `pytest` runner, linter CLI) như `test_fast_test_suites.py` **bắt buộc phải gắn nhãn** `pytestmark = [pytest.mark.slow, pytest.mark.integration]`.
* **Lý do:** Tách biệt hoàn toàn các bài test tốn I/O khởi tạo tiến trình khỏi vòng lặp test nhanh mặc định (`pytest -m "not slow and not stress"`), bảo toàn nghiêm ngặt SLA < 2.0s cho AI Feedback Loops.

#### P3.8. Local Multi-Scorer Fast Assertion Framework (`ccba_harness.evals`)
* **Nguyên tắc:** Đo lường chất lượng AI Agent bằng cơ chế Hybrid Scoring kết hợp:
  - *Code-based Scorers (< 1ms):* `ExactMatchScorer`, `RegexScorer`, `LengthBoundsScorer`, `JsonSchemaScorer` cho các ràng buộc kỹ thuật tuyệt đối.
  - *Model-based Rubric Scorer:* `LLMRubricScorer` triển khai cấu trúc Anthropic Chain-of-Thought (`<rubric>`, `<answer>`, `<thinking>`, `<score>1-5</score>`) quy đổi về thang điểm phần trăm chuẩn hóa 0–100%.
  - *Rào chắn Điểm Liệt (Hard Floor Invariant):* Bất kỳ vi phạm nghiêm trọng nào (như trích dẫn luật hết hiệu lực, sai bậc chịu lửa PCCC) sẽ kích hoạt `critical_failed = True` và lập tức kéo điểm tổng thể về 0.0% (Fail-Fast).

#### P3.9. Git-Ratchet Autonomous Experimentation Loop (`karpathy/autoresearch` Pattern)
* **Nguyên tắc:** Biến Git thành bộ lưu trữ state bất biến cho các thí nghiệm tối ưu hóa Prompt và Kỹ năng AI (`SKILL.md`):
  - Khai báo mục tiêu tối giản qua tệp `program.md` (`Target File`, `Target Score`, `Dataset File`, `Guardrails`).
  - *KEEP (Commit):* Khi `Score_mới > Score_cũ` và không có Điểm Liệt $\rightarrow$ AI tự động `git commit`.
  - *REVERT (Rollback):* Khi `Score_mới <= Score_cũ` hoặc có lỗi $\rightarrow$ AI tự động `git checkout -- <target_file>` khôi phục trạng thái cũ an toàn.

#### P3.10. Isolated Fast Test Suites & Strict SLA (< 2s) for AI Fast Feedback Loops (Matt Pocock Pattern)
* **Nguyên tắc:** AI Agent cần vòng lặp phản hồi siêu tốc (< 2s) sau mỗi lần sửa mã nguồn để tránh gián đoạn tư duy và lãng phí token.
* **Giải pháp:**
  1. Đăng ký marker `fast` chính quy trong `pyproject.toml` và gán nhãn `pytestmark = [pytest.mark.fast, pytest.mark.unit]` cho các bài test thuần logic/mock in-memory.
  2. Nâng cấp bộ điều phối test runner `scripts/eval/run_isolated_tests.py --fast` và `scripts/safe_pytest.py --fast` với cấu hình bắt buộc `-c pyproject.toml`.
  3. Cưỡng chế SLA tự động bằng test suite `tests/governance/test_fast_test_suites.py` xác thực 100% các package đều hoàn thành kiểm thử trong thời gian siêu tốc.

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

#### P4.12. Structured XML Prompt Envelopes & Evaluator-Optimizer Loop (`ccba-ai` prompting)
* **Nguyên tắc:** 
  - *Đóng gói Thẻ XML:* Sử dụng `xml_envelope` và `parse_xml_tags` để đóng gói ngữ cảnh dữ liệu (`<context>`, `<input>`, `<instructions>`, `<thinking>`, `<output>`), tạo ranh giới dữ liệu rõ ràng giúp LLM nhận diện đúng cấu trúc và triệt tiêu nguy cơ prompt injection.
  - *Vòng lặp Tự sửa lỗi (Technique 15):* Triển khai `evaluator_optimizer_loop` kết hợp Generator Model và Evaluator Model để tự đánh giá và tinh chỉnh câu trả lời với trần lặp `max_iterations=3`.

#### P4.13. Wayfinding Pattern & Leading Words for Foggy Problems (Latent Space & Matt Pocock Pattern)
* **Vấn đề (Planning Fatigue):** Khi lập kế hoạch cho các bài toán lớn/mờ mịt (greenfield) để chuẩn bị cho AFK Agents chạy ngầm qua đêm, việc nhồi toàn bộ bài toán vào một session duy nhất sẽ làm cạn kiệt context window và suy giảm độ sắc nét của Agent.
* **Giải pháp (Orchestrator Layer & Fog of War):** 
  - *Tư duy Warcraft III:* Không cố quyết định mọi thứ ngay từ đầu. Chỉ tạo các ticket unblocked ở rìa biên giới (`Frontier`), mỗi ticket giải quyết 1 câu hỏi cụ thể trong 1 session ~100K token độc lập.
  - *Ngôn ngữ dẫn đường (Leading Words):* Định hình 3 thực thể chuẩn mực để AI không nhầm lẫn: `Map` (Bản đồ tổng thể lưu quyết định), `Ticket` (Câu hỏi cụ thể giao cho 1 session con), `Session` (Ngữ cảnh giải quyết trọn vẹn 1 ticket).
  - *Fog vs. Ticket Test:* Nếu câu hỏi đã phát biểu sắc nét $\rightarrow$ Tạo Ticket ngay (dù đang bị block); nếu chưa rõ câu hỏi $\rightarrow$ Giữ trong vùng sương mù `Not yet specified`.

#### P4.14. Event-Driven Reactive Wakeup over Background Polling Loops
* **Vấn đề:** Khi chạy các tác vụ nền kéo dài (như `gh pr checks --watch` hoặc `run_harness_evals.py`), Agent vô thức rơi vào vòng lặp gọi `manage_task status` liên tiếp 10-15 lần. Gây lãng phí token, phình to context window và tạo ra hàng chục dòng "Checked Task..." gây nhiễu UI.
* **Giải pháp:** Cưỡng chế nguyên tắc **Zero-Polling Invariant**:
  1. Khi một lệnh chạy dưới dạng background task: Agent chỉ kiểm tra tối đa 2 lần cho task siêu ngắn (< 5s).
  2. Nếu task vẫn `RUNNING`: Agent **bắt buộc dừng gọi công cụ và kết thúc lượt (End Turn)**. Hệ thống sẽ tự động thông báo và đánh thức Agent (*Reactive Wakeup*) ngay khi task kết thúc.

#### P4.15. Copilot Review Requests Gate & Defense-in-Depth Release Invariant
* **Vấn đề (Race Condition Merge Sớm):** GitHub Actions CI thường hoàn thành trước Copilot Review (~30-60s). Nếu Agent kiểm tra comments ngay khi CI xanh, API trả về rỗng do Copilot chưa kịp nộp bài $\rightarrow$ Dẫn đến merge PR sớm và bỏ sót các phản biện quan trọng của Copilot.
* **Giải pháp:** Áp dụng mô hình phòng thủ đa tầng (**Defense-in-Depth**):
  1. *Shift-Left Reminder (`/ccba-create-pr`):* Nhắc nhở người dùng chờ cả CI xanh và Copilot review.
  2. *Hard Gate (`/ccba-release-feature`):* Kiểm tra `gh pr view $PR_NUMBER --json reviewRequests,reviews --jq '{pending: [.reviewRequests[]?.login], reviewed: [.reviews[]?.user.login]}'`. Bắt buộc chỉ thực hiện `gh pr merge` khi danh sách `reviewRequests` không còn `copilot-pull-request-reviewer` và toàn bộ comments đã được xử lý hoặc giải trình trong `walkthrough.md`.

### ⚠️ Anti-Patterns (Cần Tránh)
* **AP4.1. Hardcoded API Keys:** Tuyệt đối không hardcode keys vào code/markdown. Luôn dùng biến môi trường hoặc `.env`.
* **AP4.2. Raw Exception Context Chaining (Ruff B904):** Dùng `raise NewException(...) from None` khi ném ngoại lệ mới trong block except không liên quan.
* **AP4.3. Reasoning Models trong Converter Fallback Chains:** Tuyệt đối không đưa các model có hậu tố `-thinking` vào chuỗi fallback của document converter (`mdconverter`) để tránh rò rỉ khối thẻ `<think>` làm ô nhiễm file Markdown đầu ra.
* **AP4.4. Monolithic Context Overloading (Ball of Mud Prompt):** Nhồi nhét hàng chục trang quy tắc tĩnh và các quy định hiển nhiên (như f-strings, type hints, bare except) vào `AGENTS.md` gốc, làm tiêu tốn ~80% ngân sách chỉ dẫn của LLM và gây phân tâm khi suy luận.
* **AP4.5. Premature Code Generation on Foggy Problems:** Nhảy vào viết code khi chưa xua tan sương mù chiến trận của bài toán. Luôn dùng `/ccba-wayfinder` hoặc `/ccba-grilling` để chốt quyết định thiết kế trước khi lập trình.
* **AP4.6. Background Task Polling Loop:** Lặp lại `manage_task status` liên tục trong cùng một lượt gọi để chờ tác vụ ngầm hoàn thành thay vì kết thúc lượt để chờ cơ chế Reactive Wakeup tự động.
* **AP4.7. Premature Merge on Pending Bot Reviews:** Kích hoạt `gh pr merge` ngay khi CI vừa xanh mà không kiểm tra xem Copilot Review Bot có còn đang phân tích (`reviewRequests`) hay không.

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

#### P5.5. YAML Frontmatter Flow Scalar Bracket Quoting Invariant
* **Nguyên tắc:** Trong YAML frontmatter của các tệp Markdown (`SKILL.md`, `workflows/*.md`), nếu giá trị của một trường vô hướng (như `description:`) bắt đầu bằng ký tự mở ngoặc vuông `[` (ví dụ: `description: [Alias ...] ...`):
  - **Bắt buộc:** Phải bọc toàn bộ chuỗi trong dấu nháy kép `"` (ví dụ: `description: "[Alias ...] ..."`).
* **Lý do:** Parser YAML tiêu chuẩn (PyYAML) sẽ diễn giải `[` ở đầu dòng như một Flow Sequence (danh sách YAML) và ném lỗi cú pháp nghiêm trọng `Failed to parse frontmatter YAML: expected <block end>, but found '<scalar>'` làm vỡ CI validation gates.

### ⚠️ Anti-Patterns (Cần Tránh)
* **AP5.1. Naive Regex Regex Table Replacement:** Dùng regex đơn giản làm mất merge cell hoặc xô lệch dữ liệu bảng số liệu.
* **AP5.2. Stripping YAML Comments on Re-dump:** Dùng `yaml.dump()` thô làm mất toàn bộ comment giải thích do con người viết trước đó.
* **AP5.3. Unquoted Bracket-Leading Scalar in YAML Frontmatter:** Khai báo trường chuỗi bắt đầu bằng `[` mà không bọc nháy kép trong header tệp markdown.

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

#### P6.15. Domain OpenXML Table Extraction & Reconstruction Deep Seam (`TableReconstructor`)
* **Nguyên tắc:** Bảng biểu phức tạp (rowspan/colspan gộp ô, đa cấp, footnotes) xuất hiện ở mọi miền nghiệp vụ (QCVN PCCC, QC Thẩm tra, Hồ sơ hoàn thành, Hợp đồng).
* **Giải pháp:** Gom toàn bộ năng lực bóc tách ma trận bảng 2D, unmerge ô gộp, sinh slug mô tả (`make_descriptive_table_slug`) và thay thế Markdown vào package SSOT `packages/ccba-ooxml` (`from ccba_ooxml import TableReconstructor, StructuredTable`). Các packages khác (`ccba-legal-intel`) và Spokes tái sử dụng trực tiếp mà không viết lại logic.

#### P6.16. Dual-Layer Dependency Contract Enforcement (Import-Linter & Native AST Scanner)
* **Nguyên tắc:** Bảo vệ tuyệt đối ranh giới của các Deep Seams, cấm gọi trực tiếp vào các file private nội bộ `_*` của package khác và ngăn chặn phụ thuộc vòng hoặc đảo ngược tầng (layer inversion).
* **Giải pháp:**
  1. **Cấu hình chuẩn công nghiệp `.importlinter`**: Khai báo các contracts `layers`, `forbidden`, `independence` cho `lint-imports`.
  2. **Native AST Governance Scanner (`scripts/governance/check_dependency_contracts.py`)**: Bộ quét AST zero-dependency quét toàn bộ 200+ file mã nguồn trong `< 0.4s`, bẫy các lỗi `PrivateSubmoduleSeamViolation`, `FoundationLeafPurityViolation`, `LeafIndependenceViolation` mà không cần cài đặt thêm thư viện bên ngoài.
  3. Tích hợp trực tiếp vào CI và `ccba-lint-imports` CLI.

#### P6.17. AST Visitor Private Member Import Guard
* **Nguyên tắc:** Linter kiểm soát ranh giới phụ thuộc (`DependencyASTVisitor`) không được chỉ kiểm tra `node.module`, mà **bắt buộc phải duyệt qua cả `node.names`** trong câu lệnh `from pkg import ...`.
* **Lý do:** Ngăn chặn triệt để hành vi lách luật Seam bằng cách import trực tiếp private symbols/functions (`from ccba_maskara import _private_symbol`), bảo vệ 100% tính toàn vẹn của Thin Seams.

#### P6.18. Resilient Legal AST Node Normalization for VBHN Merging
* **Nguyên tắc:** Trong quy trình đối soát và hợp nhất văn bản pháp luật (VBHN Engine), các node ID sinh ra từ AST (ví dụ `D1`, `D2`) và các patch diff (ví dụ `dieu-1`, `dieu_1`, `1`) phải được chuẩn hóa qua `norm_map` hai chiều.
* **Lý do:** Đảm bảo phép so khớp và chắp vá luôn thành công bất chấp sự khác biệt về case và dấu gạch nối giữa các hệ thống trích xuất.

#### P6.19. 3-Tier Skills Hierarchy & Progressive Disclosure (Kim Tự Tháp Kỹ Năng 3 Tầng & ADR 0040)
* **Nguyên tắc:** Để giải quyết triệt để vấn đề Context Bloat và giảm tải 70-80% token nền:
  1. **Tier 1 (Master Deep Skills - Model Invoked):** Đại diện cho các năng lực đầu cuối hoàn chỉnh, bảo trợ bởi Deep Seams. Khống chế nghiêm ngặt $\le 10$ skills cho mỗi Bundle (`_core: 10`, `_qc: 6`, `_consulting: 4`, `_bim: 5`), với mô tả súc tích $\le 180$ ký tự để AI tự nhận diện trong hội thoại tự nhiên.
  2. **Tier 2 (Progressive References):** Các tài liệu hướng dẫn kỹ thuật chi tiết của sub-skills nông được gom vào thư mục `references/*.md` bên trong Master Skill (Progressive Disclosure — chỉ nạp khi cần xử lý ngoại lệ).
  3. **Tier 3 (User Workflows - User Invoked):** 100% các quy trình mang tính nghi thức, có sự điều khiển của con người (`/ccba-implement`, `/ccba-new-feature`, `/ccba-wait-what`...) bắt buộc gắn `disable-model-invocation: true` để tiêu tốn **0 token** trong System Prompt khởi tạo.

#### P6.20. Infrastructure Glue Code vs Domain Orchestration Distinction (Phân Biệt Rõ Mã Nối Hạ Tầng & Logic Điều Phối)
* **Nguyên tắc:** Khi rà soát mã nguồn để làm sâu module (Deepening via Extraction - P6.6), **bắt buộc phải phân biệt rõ ràng giữa Infrastructure Glue Code với Domain Orchestration Logic**:
  - *Infrastructure Glue Code:* Lệnh gọi `subprocess.run()`, tạo thư mục tạm `tempfile.TemporaryDirectory()`, in banner màu `print()`, đo runtime... $\rightarrow$ Thuộc về CLI scripts hoặc test helpers, **không cấu thành domain depth**. Nghiêm cấm bọc các đoạn glue code này thành Class/Service mới khi không có ít nhất 2 caller thực tế (tránh vi phạm AP6.3 Shallow-Wrapping).
  - *Domain Orchestration Logic:* Xử lý phân loại nghiệp vụ, chuyển đổi định dạng phức tạp, phân giải AST, mutex locks liên quan đến phiên làm việc, cơ chế tự sửa lỗi $\rightarrow$ Bắt buộc bóc tách đưa vào packages lõi trước khi tinh gọn script.

#### P6.21. Cross-Package Unique Symbol Naming Invariant (Bất Biến Định Danh Symbol Độc Nhất Toàn Monorepo)
* **Nguyên tắc:** Mỗi class, protocol hoặc public seam trong Monorepo phải sở hữu một định danh duy nhất phản ánh chính xác 100% năng lực cốt lõi của nó.
* **Quy chuẩn:** Tuyệt đối không đặt tên trùng lặp (ví dụ: `TableReconstructor` ở cả `mdconverter` và `ccba-ooxml`) khi bản chất của một bên chỉ là trích xuất phụ lục (`AppendixExtractor`). Việc này triệt tiêu hoàn toàn nguy cơ ô nhiễm ngữ cảnh (Context Poisoning) và giúp AI Agent luôn định vị đúng Deep Seam chuẩn.

#### P6.22. Hard Caller Count Gate & Ground-Truth Architecture Sweeps (Rào Chắn Số Lượng Caller Thực Tế & Quét Kiến Trúc Thực Chiến)
* **Nguyên tắc:** Khi rà soát mã nguồn để đề xuất các cơ hội làm sâu module (Deepening Opportunities):
  1. **Đếm Caller Thực Tế Bằng `grep_search`:** Tuyệt đối không suy đoán số caller trên lý thuyết. Nếu một đoạn code chỉ có duy nhất 1 caller (`Callers == 1`), đề xuất bóc tách tạo Seam mới bắt buộc phải bị xếp loại `Speculative / Low ROI` (không được gán `Strong Recommendation`). Chỉ đề xuất Deep Seam mới khi có ít nhất $\ge 2$ callers độc lập thực sự cần dùng.
  2. **Ưu Tiên Quét Nợ Kỹ Thuật Thực Tế:** Trong các phiên rà soát kiến trúc, ưu tiên quét triệt tiêu các nợ kỹ thuật gây nguy cơ tiềm ẩn cao: Xung đột tên định danh giữa các packages (P6.21), trôi dạt import cục bộ trong submodules, và các script dùng một lần tồn dư trong thư mục vận hành thay vì chỉ tập trung vào việc bóc tách hàm dài.

#### P6.23. Dynamic Skill Scope & Broad Scan Isolation (Cô Lập Phạm Vi Symbol & Tra Cứu Động)
* **Nguyên tắc:** Khi xây dựng công cụ kiểm tra tĩnh, quét mã nguồn hoặc symbol indexing (như `LinkAuditor`):
  1. **Loại trừ thư mục cục bộ khi quét diện rộng:** Tự động loại trừ `.agents` khi `search_dirs` bao gồm `project_root`, ngăn symbol cục bộ của một skill rò rỉ thành symbol toàn cục (global leak).
  2. **Dynamic Skill Scope:** Tự động phát hiện nếu tệp markdown đang kiểm tra nằm trong `.agents/skills/<skill-name>/` và nạp thêm thư mục `scripts/` nội bộ của chính skill đó vào phạm vi tra cứu, bất kể `search_dirs` được truyền tường minh hay ngầm định.
  3. **Scoped Caching:** Khóa cache kết quả tìm kiếm theo tuple `(symbol, tuple(search_dirs))` để tránh ô nhiễm kết quả giữa các phạm vi kiểm tra khác nhau.

#### P6.24. Direct Re-export over Shallow Subclassing (Ưu Tiên Re-Export Trực Tiếp Hơn Lớp Con Rỗng)
* **Nguyên tắc:** Khi một package cấp cao (consumer như `mdconverter`) kế thừa các kiểu dữ liệu, báo cáo hoặc thực thể từ package nền tảng (foundation như `ccba_pdf_prep`):
  - Nếu không mở rộng hành vi hay bổ sung trường dữ liệu mới, hãy re-export trực tiếp tại `__all__` thay vì tạo các lớp con rỗng (`class Segment(BaseSegment): pass`) hay viết wrapper hàm unpack 15 tham số thủ công.
  - Giúp mã nguồn tinh gọn, bảo đảm tính nhất quán của kiểu dữ liệu (`isinstance` checks luôn khớp) và giảm chi phí bảo trì boilerplate.

### ⚠️ Anti-Patterns (Cần Tránh)

* **AP6.1. Leaky Interface Exporting 30+ Symbols:** Xuất khẩu toàn bộ hàm con ra `__init__.py` làm rối loạn AI navigation.
* **AP6.2. Domain Drift:** Đặt file xử lý PDF vào package OOXML hoặc đặt logic cào web vào module phân tích xung đột.
* **AP6.3. Shallow-Wrapping Deep Seams (Bọc Nông trên Seam Sâu):** Tạo thêm một class/function bọc quanh một Deep Seam đã hoàn chỉnh chỉ để tạo "cảm giác dễ dùng", gây phân mảnh API và vi phạm nguyên lý KISS.
* **AP6.4. Unchecked Transport/SDK Assumptions:** Giả định các SDK/Client hỗ trợ các khả năng đặc thù (như xử lý multimodal bytes, async streams) mà chưa inspect code thực tế của thư viện, dẫn đến kế hoạch sai lệch nghiêm trọng.
* **AP6.5. Deleting Embedded Domain Logic:** Nhầm lẫn giữa mã boilerplate lặp lại với domain orchestration logic (dù đã có docstring) và xóa bỏ khi tinh gọn scripts.
* **AP6.6. Hybrid "Neither Fish Nor Fowl" Model Anti-Pattern (Lớp Mô Hình Lai Tạp):** Cài đặt đè `__getitem__` trên `BaseModel` để vừa hỗ trợ dot notation vừa hỗ trợ dict subscripting, gây mơ hồ khi phân tích kiểu dữ liệu tĩnh và làm sai lệch quá trình serialize JSON/dump.
* **AP6.7. Brittle File Path Instructions (Context Poisoning):** Ghi cứng đường dẫn script phụ trợ cụ thể (`scripts/safe_pytest.py`, `scripts/hooks/test_speed_guard.py`) trong tài liệu quy tắc. Khi refactor module, Agent bị ảo giác và tìm kiếm ở vị trí sai. Thay vào đó, áp dụng **Capability-First Instructions**.
* **AP6.8. Implicit Scope Leaks in Unfiltered Root Scans:** Quét toàn bộ `project_root` bằng `rglob` mà không có bộ lọc ranh giới (`.agents`, `node_modules`, `.md`), dẫn đến việc tài liệu toàn cục tham chiếu nhầm vào các hàm/biến cục bộ của skill (False Positive) hoặc làm chậm CI gấp hàng chục lần.
* **AP6.9. Overlapping Skill Steps (Bước Hướng Dẫn Phủ Lấp):** Thêm bước mới vào SKILL.md mà không hợp nhất với bước cũ có chức năng tương tự, tạo ra các bước đánh số nhảy cóc (1 → 1.4 → 1.5 → 2) và nội dung trùng lặp. Agent phải đọc 2 lần hướng dẫn gần như đồng nghĩa, vi phạm KISS. *Chuẩn:* Khi bổ sung logic mới, tích hợp trực tiếp vào bước cũ hoặc thay thế hoàn toàn, không xếp chồng song song.

---

## 7. Hệ Sinh Thái Hub-Spoke, Tiếp Nhận & Đồng Bộ

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

#### P7.6. Non-Destructive Brownfield Spoke Adoption (`SpokeAdopter` & ADR 0036)
* **Nguyên tắc:** Khi tiếp nhận một codebase/dự án hiện hữu (Brownfield) vào mạng lưới Hub-Spoke:
  1. Áp dụng ma trận khám phá 3 tầng (Stack Detection, Risk Checklist, Constitution Preservation).
  2. Sử dụng thuật toán **Hợp nhất Cộng dồn (Additive Schema Merge)** và tự động tạo bản backup `workspace_context.yaml.bak`.
  3. **Tuyệt đối không ghi đè** tệp `AGENTS.md` tùy biến riêng của Spoke.
  4. Tự động cài đặt Git Pre-commit Security Hook (Maskara) và đồng bộ trọn gói Skills/Workflows theo `project_type`.

#### P7.7. Constitution-Driven Traceability Matrix & Dynamic Knowledge Pointers (ADR 0037)
* **Nguyên tắc:** 
  - Khóa chặt mối liên kết 2 chiều giữa từng dòng Spec/User Story với Điều/Khoản trong văn bản quy chế thể chế và sơ đồ hệ thống qua tệp `cross_references.yaml`.
  - Mọi tri thức nghiệp vụ chuyên biệt thuộc về Spoke (như toàn văn VBPL OKF v2.0 của `ccba-legal-knowledge` hay quy chế nội bộ của `idop-ccba-way`) được Hub tham chiếu qua **Con Trỏ Động (Dynamic Pointer)** `[spoke_path]` trong `catalog.yaml` thay vì copy tệp tin, triệt tiêu 100% rủi ro trùng lặp dữ liệu và duy trì SSOT duy nhất.

#### P7.8. Automated Fuzzy Auto-Patch & Hard Gate for Cross-References (`CrossRefValidator`)
* **Nguyên tắc:** 
  - Ma trận truy vết `cross_references.yaml` được bảo vệ bằng Hard Gate: trả về `Exit Code 1` nếu có bất kỳ liên kết gãy nào (missing file, missing doc, invalid anchor).
  - Tích hợp thuật toán **Fuzzy Matching** (Levenshtein similarity) tự động tìm kiếm heading gần nhất và hỗ trợ cờ `--fix` để tự động vá lỗi cập nhật file YAML khi tài liệu markdown bị sửa đổi tiêu đề mục.
  - Hỗ trợ cờ `--warn-only` cho giai đoạn nháp ban đầu.

#### P7.9. Automated 4-Layer Zero-Duplication Guardrail on Hub (`DuplicationAuditor`)
* **Nguyên tắc:** Thiết lập hệ thống bảo vệ 4 tầng tự động (Git Pre-Commit Hook $\rightarrow$ `DuplicationAuditor` trong `DocAuditor` $\rightarrow$ Khóa cứng `.gitignore` $\rightarrow$ Pointer-First Linting) để ngăn chặn vĩnh viễn việc tái nhiễm các tệp dữ liệu thuộc quyền quản lý độc quyền của Spoke lên Hub.

#### P7.10. OKF v2.0 Clean Markdown & Independent Metadata Bundle SSOT (ADR 0038)
* **Nguyên tắc:** 
  - Tách biệt hoàn toàn metadata ra tệp `metadata.yaml` độc lập cấp bundle, loại bỏ 100% YAML frontmatter khỏi tệp `.md` để giữ định dạng thuần sạch khi hiển thị và xuất bản ra Word/PDF.
  - Danh mục AST `clauses.json` theo mô hình Flat Index có bổ sung `node_type` và `parent_id` (vừa tra cứu $O(1)$, vừa tái dựng cây AST trong 1 vòng lặp cho VBHN Delta Patching).
  - Bộ đối chuẩn `qa_benchmark.json` mở rộng 5 trường (`question`, `answer`, `anchor`, `citation`, `ground_truth_context`) phục vụ đo lường và rào chắn `LegalGroundingGate`.

#### P7.11. Autonomous 4-Step Crawler-to-Spoke Ingestion Protocol (ADR 0039)
* **Nguyên tắc:** 
  - Quy trình 4 bước tự động: Crawl VIP (Hub) $\rightarrow$ Sandbox Temp $\rightarrow$ Ingest & Validate (Spoke) $\rightarrow$ Auto-Purge Temp & Sync Cloud.
  - Tự động hủy bỏ toàn bộ tệp tạm `.docx` ngay khi Spoke xác nhận `Exit Code 0`, bảo vệ 100% nguyên tắc Zero-Duplication SSOT trên Hub.

#### P7.12. Non-Destructive Selective Merge & Dry-Run Preview (`SpokeSynchronizer`)
* **Nguyên tắc:** Khi đồng bộ tài nguyên từ Hub về Spoke:
  1. **Tuyệt đối không xóa đè toàn bộ thư mục** `workflows/` hoặc `skills/`.
  2. Áp dụng cơ chế so sánh nội dung từng tệp (byte-level comparison), phân loại rõ ràng 4 trạng thái: `🟢 NEW`, `🔄 UPDATED`, `⚪ UNCHANGED` và `🛡️ PRESERVED` (bảo toàn 100% các file nội bộ do Spoke tự viết).
  3. Cung cấp cờ `--dry-run` cho phép mô phỏng toàn bộ tiến trình và xuất bảng báo cáo trạng thái chi tiết mà không sửa đổi bất kỳ byte nào trên đĩa.

#### P7.13. Multi-Spoke Batch Sync Engine & Spoke Health/Drift Dashboard
* **Nguyên tắc:** 
  - Điều phối đồng bộ tập trung hàng loạt: Tự động giải mã Hub Registry (RSA 2048-bit), duyệt qua tất cả các Spoke còn tồn tại vật lý và đồng bộ 1 chạm qua `python scripts/sync_spoke.py --all`.
  - Cung cấp Bảng điều khiển Giám sát (`ccba-platform spoke-status`): Tự động phát hiện các Spoke đang hoạt động (`🟢 ACTIVE`), Spoke bị trễ phiên bản (`⚠️ OUTDATED` > 30 ngày kể từ lần sync cuối) hoặc đường dẫn vật lý bị mất (`❌ MISSING`).

#### P7.14. Zero-Latency Static File Inspection for Shared Python Packages (`SharedSdkInspector`)
* **Nguyên tắc:** Khi cần phát hiện xem Spoke Python đã cài đặt các package dùng chung (`ccba-ai`, `ccba-ooxml`) ở chế độ editable (`pip install -e`) hay chưa:
  - **Tuyệt đối không spawn tiến trình subprocess `pip list`** trong vòng lặp sync làm chậm 2–4s cho mỗi Spoke.
  - Thay vào đó, quét trực tiếp cấu trúc file tĩnh trong `.venv/Lib/site-packages/` (hoặc `venv/`) để tìm kiếm sự hiện diện của `.pth`, `__editable__*`, `.egg-link` hoặc `.dist-info` với tốc độ tức thì (< 1ms).
  - Tự động đưa ra khối gợi ý cài đặt 1 dòng lệnh thân thiện (`pip install -e "[hub_path]/packages/..."`) ngay sau bảng báo cáo sync khi phát hiện SDK chưa được liên kết.

#### P7.15. Dual-Mode Spoke Discovery Seam (Registry Lookup with Fallback)
* **Nguyên tắc:** Khi một công cụ dòng lệnh toàn cục (`ccba-platform ingest-legal`) cần định vị đường dẫn vật lý của một Spoke chuyên biệt (như Spoke Pháp điển `ccba-legal-knowledge`):
  - **Ưu tiên 1:** Giải mã và tra cứu danh mục `spoke_registry.yaml` thông qua `get_registered_spokes` theo `spoke_id`, `name`, hoặc hồ sơ `project_type`.
  - **Ưu tiên 2 (Fallback):** Đọc biến môi trường chuyên biệt (`CCBA_LEGAL_SPOKE_PATH`).
  - **Ưu tiên 3 (Standard Defaults):** Quét các đường dẫn repo tiêu chuẩn (`D:/GitHubProjects/...`, `../<spoke-name>`, `./<spoke-name>`).
  - Đảm bảo hệ thống vận hành trơn tru cả trong môi trường phát triển độc lập (isolated standalone) lẫn môi trường mạng lưới đa Spoke đã đăng ký bảo mật.

#### P7.16. End-to-End Archetype Lifecycle Enforcement (ADR 0041 & Spoke Workflows)
* **Nguyên tắc:** Mọi giai đoạn trong vòng đời của một Spoke (tạo mới `/ccba-init-spoke`, tiếp nhận `/ccba-adopt-spoke`, thiết lập cấu hình `/ccba-setup-skills`) đều phải nhận diện và định danh tường minh trường `archetype` (`project_delivery`, `enterprise_governance`, `knowledge_corpus`, `specialized_extension`, `platform_hub`) trong `workspace_context.yaml`. Việc này giúp loại bỏ phỏng vấn thừa và tự động hóa việc cấu hình đúng công cụ nghiệp vụ (ví dụ: `project_delivery` $\rightarrow$ Local Markdown Issues thay vì GitHub Issues).

#### P7.17. Upstream Proposal Archetype Attribution & Local Pre-PR Governance Linter (`ccba-propose-to-hub`)
* **Nguyên tắc:** Khi một Spoke đề xuất sáng kiến ngược lên Hub, mẫu proposal bắt buộc ghi nhận `proposed_by_archetype` để phân loại bối cảnh nghiệp vụ, đồng thời phải vượt qua Governance Gate (`validate_skills.py`, `doc_auditor.py`) tại local trước khi mở Pull Request.

#### P7.18. Symmetric Two-Phase Upstream Contribution Lifecycle (`/ccba-issue-to-hub` & `/ccba-contribute-to-hub`)
* **Nguyên tắc:** Hoàn thiện chu trình đóng góp 2 chiều đối xứng từ Spoke lên Hub bằng cách phân tách độc lập 2 pha:
  1. **Pha 1 (Ý tưởng & RFC - `/ccba-issue-to-hub`):** Tự động bóc tách bối cảnh từ phiên thảo luận Spoke, soạn thảo RFC tiêu chuẩn và tạo GitHub Issue lên Hub trung tâm thông qua `gh issue create`.
  2. **Pha 2 (Mã nguồn & Pull Request - `/ccba-contribute-to-hub`):** Đóng gói mã nguồn, test suite, proposal ADR-0045, chạy rào chắn rò rỉ `check_spoke_leakage.py`, mở GitHub PR và duy trì vòng lặp Self-Healing CI & Copilot Review.
  3. **Tương thích ngược (Backward Compatibility):** Duy trì `/ccba-propose-to-hub` làm Alias chuyển tiếp an toàn để không làm gãy thói quen của kỹ sư.

#### P7.19. Automated Issue Context Bootstrapping in Feature Workflows (`/ccba-new-feature #[ID]`)
* **Nguyên tắc:** Khi kỹ sư kích hoạt workflow khởi tạo branch với mã Issue (ví dụ: `/ccba-new-feature #209`), workflow tự động gọi `gh issue view <id> --json title,body,labels` để bóc tách loại công việc (`feat`, `fix`, `docs`, `refactor`) và mô tả tính năng. Tự động đề xuất branch name chuẩn `feat/...` và bỏ qua hoàn toàn các câu hỏi thủ công, tối ưu hóa tối đa trải nghiệm lập trình.

#### P7.20. Hub-Spoke Taxonomy & Bundle Integrity Guard (ADR 0041, ADR 0044)
* **Nguyên tắc:** Mọi thay đổi hoặc bổ sung về Danh mục Bundle, Archetype, Spoke Type hay Workflows trong Hub-Spoke bắt buộc phải được đồng bộ hóa nhất quán qua **4 điểm chạm**:
  1. `catalog.yaml` (SSOT danh mục bundles và workflows)
  2. CLI Help/Choices (`scripts/adopt_spoke.py`, `scripts/sync_spoke.py`)
  3. Workflows & Skills frontmatter `applies_to`
  4. Engine nhận diện mã nguồn Python (`spoke_bootstrap.py`, `spoke_adopter.py`)
* **Rào chắn tự động:** Bắt buộc duy trì 2 CI Gates `tests/governance/test_taxonomy_integrity.py` và `tests/governance/test_global_skills_integrity.py` để tự động phát hiện và chặn đứng mọi sai lệch khai báo ngay trước khi commit.

#### P7.21. Sandbox Identification Invariant vs Extension Archetypes (ADR 0046)
* **Nguyên tắc:** **TUYỆT ĐỐI KHÔNG ĐÁNH ĐỒNG** Archetype cấp cao `specialized_extension` với cờ trạng thái tạm thời `is_sandbox: True`.
* **Thực tế:** `specialized_extension` bao gồm cả các dự án tiện ích chính thức (`tooling_plugin`, `research_lab`). Việc gán nhầm toàn bộ extension thành sandbox sẽ khiến dự án chính thức bị loại trừ khỏi batch sync và bị xóa dọn sau 60 ngày.
* **Chuẩn thực thi:** Chỉ kích hoạt `is_sandbox = True` khi thỏa mãn: `sub_type == "personal_sandbox"` hoặc `guardrails.get("sandbox_mode") is True`.

### ⚠️ Anti-Patterns (Cần Tránh)
* **AP7.1. Editing YAML without Validation:** Sửa đổi YAML mà không chạy kiểm thử qua `yaml.safe_load()`.
* **AP7.2. Committing Unscanned Code:** Bỏ qua quy trình `/ccba-code-review` hoặc Governance Audit trước khi tạo PR.
* **AP7.3. Context-Blind Link Leakage (`file:///` in Git Repo Docs):** Vô thức đem cú pháp `file:///` từ giao tiếp chat vào nội dung tệp `.md` trong repo. Bộ điều phối `doc_auditor.py` đã tích hợp rào chắn cross-platform để chặn đứng và tự động sửa (`--fix`) lỗi này ngay tại local.
* **AP7.4. Duplicating Domain Corpus onto Central Hub (Anti-SSOT Proliferation):** Sao chép toàn văn các văn bản dữ liệu từ Spoke lên Hub dưới dạng tệp `.txt` cào thô hoặc bản sao `.md`, làm phình to repository trung tâm và gây lệch pha phiên bản khi Spoke cập nhật.
* **AP7.5. Destructive Brownfield Onboarding:** Dùng template tĩnh ghi đè toàn bộ `AGENTS.md` và `workspace_context.yaml` khi kết nối một Spoke hiện hữu, làm mất mát metadata và quy chuẩn riêng của dự án.
* **AP7.6. Destructive Workflow Wipe during Spoke Sync:** Xóa sạch toàn bộ thư mục `.agents/workflows/` của Spoke trước khi copy đè các tệp từ Hub, làm mất vĩnh viễn các workflow tùy biến nội bộ mà đội ngũ Spoke đã tự phát triển.
* **AP7.7. Subprocess Latency Bottleneck in Batch Sync Operations:** Gọi các lệnh shell nặng như `pip list` hoặc `python -m pip` bên trong vòng lặp duyệt qua danh sách hàng loạt Spoke, gây nghẽn và làm chậm tiến trình đồng bộ gấp 10-20 lần.
* **AP7.8. Context Bloat via Equal-Level Flat Skills Proliferation:** Tạo hàng chục tệp `SKILL.md` nhỏ lẻ nằm ngang hàng và đều để ở chế độ `model_invoked`, làm phình to System Prompt khởi tạo. Cần gom các kỹ năng nông thành `references/*.md` của Master Skill và bật `disable-model-invocation: true` cho toàn bộ User Workflows.
* **AP7.9. License Classification Semantic Leakage:** Trả về giá trị enum lạ không nằm trong hợp đồng 4 giá trị (PERMISSIVE, COPYLEFT, PROPRIETARY, UNKNOWN), làm đứt gãy logic phân nhánh downstream.
* **AP7.10. State File Path Mismatch during Registry Migration:** Tự ý đổi tên tệp tin lưu commit SHA trong quá trình chuyển đổi sang YAML registry, khiến hệ thống hiểu nhầm là kho mới và quét lại từ đầu.
* **AP7.11. Unvalidated Free-Text Bundle Declarations:** Tự ý gõ chuỗi tự do trong trường `applies_to` của workflow hoặc `type` trong `workspace_context.yaml` mà không đối soát với enum chuẩn trong `catalog.yaml.bundles`, gây đứt gãy tiến trình đồng bộ Hub-Spoke.

---

## 8. Quản Trị Doanh Nghiệp IDOP, Server Spark & Viện IBST (ADR 0041-0043)

### 🌟 Core Patterns (Mẫu Tốt)

#### P8.1. Hub-Spoke 5-Archetype Taxonomy & Extensibility Framework (ADR 0041)
* **Nguyên tắc:** Phân định rõ 5 loại Spoke trong toàn hệ sinh thái:
  1. `platform_hub` (Công nghệ & AI Engine `ccba-agent-platform`).
  2. `enterprise_governance` (Hệ điều hành doanh nghiệp & Quy chế CCBA `IDOP-CCBA-WAY`).
  3. `knowledge_corpus` (Kho tri thức pháp luật quốc gia SSOT `ccba-legal-knowledge`).
  4. `project_delivery` (Hiện trường dự án thực tế `2026-04 DH Viet Nhat`).
  5. `specialized_extension` (`research_lab`, `tooling_plugin`, `client_portal`).

#### P8.2. Master OneDrive 5TB Offloading vs SharePoint Metadata Pattern
* **Nguyên tắc:** Giữ dung lượng 58 SharePoint lists luôn < 5GB bằng cách chỉ lưu trữ Metadata (Text, Lookups, URLs). Toàn bộ file binary nặng (Revit `.rvt` 500MB, file scan HĐ có dấu đỏ, hồ sơ thầu HSMT) được tự động phân luồng sang **5TB Master OneDrive (`ccba@ibst-bim.vn`)** theo 5 thư mục module chuẩn hóa.

#### P8.3. Autonomous Git-Ratchet Multi-Skill Nightly Daemon (Weighted Priority Queue & Early Stopping)
* **Nguyên tắc:** Vận hành tối ưu hóa tự động qua đêm cho 73+ kỹ năng trên Server Spark (`localhost:8090`):
  - *Hàng đợi ưu tiên thông minh (Weighted Priority Queue):* Kỹ năng có baseline score < 90% được cấp tối đa 30 vòng lặp; kỹ năng 100% chỉ chạy 1 vòng smoke test.
  - *Early Stopping:* Tự ngắt ngay khi đạt 100% hoặc stall 5 vòng liên tiếp.
  - *Git Ratchet:* Tự tạo branch `auto-tune/nightly-YYYYMMDD`, commit đột biến thành công và mở GitHub PR tổng hợp + bắn Telegram Bot alert.

#### P8.4. Dual-Tier Practical Architecture (Project Spoke ↔ IDOP Governance ↔ IBST Handshake Interface)
* **Nguyên tắc:** Tập trung khép kín 2 tầng:
  - *Tầng 1 (Project Spokes):* Kỹ sư thực hiện bản vẽ BIM, thẩm tra PCCC, bóc tách cấu kiện và xuất báo cáo nghiệm thu kỹ thuật.
  - *Tầng 2 (Enterprise Governance Spoke `IDOP-CCBA-WAY`):* Tiếp nhận hồ sơ qua quy trình QA/QC 5 cấp, phân bổ dòng tiền 3 tầng theo QCCTNB 3209, và liên thông với Viện IBST qua `ROLE_HEAD_ADMIN` (Cổng duy nhất gửi KHKT, TCKT, TCHC).

#### P8.5. Tri-Repo Server Sibling Synchronization & Linux Cron Hardening Gate (ADR 0042)
* **Nguyên tắc:** Server Spark duy trì 3 kho lưu trữ cốt lõi ngang hàng (`~/ccba/ccba-agent-platform`, `~/ccba/ccba-legal-knowledge`, `~/ccba/IDOP-CCBA-WAY`).
* **Giải pháp:** Trước khi Auto-Tuner chạy lúc 00:00, kịch bản cron thực thi chuỗi **Tri-Repo Sequential Pull Gate** (`git pull` lần lượt Luật $\rightarrow$ Quy chế $\rightarrow$ Hub) và được bảo vệ bởi **Linux Cron Hardening** (export full `PATH`, `UTF-8` locale `LANG=C.UTF-8`, `PYTHONIOENCODING=utf-8`, và tự động nạp bí mật `.env`).

#### P8.6. Tiered Multi-Severity AI Pre-Submission Gate (ADR 0042)
* **Nguyên tắc:** Phân loại rào chắn tiền kiểm hồ sơ trình Viện IBST thành 3 cấp độ rõ rệt:
  - 🔴 **Tier 1 (Hard-Floor Auto-Block):** Tự động khóa cứng 100% khi viện dẫn luật hết hiệu lực, tạm ứng $> 90\%$ hoặc sai lệch số học dòng tiền 3 tầng.
  - 🟡 **Tier 2 (Governance Override):** Cho phép Giám đốc (`ROLE_DIRECTOR`) phê duyệt vượt rào đối với các ngoại lệ nghiệp vụ cấp bách và bắt buộc ghi nhật ký giải trình bất biến (`Audit Trail`) vào `lessons_learned.json`.
  - 🟢 **Tier 3 (Advisory Warnings):** Cảnh báo mềm về văn phong, thể thức và nhắc nhở mốc tiến độ WBS.

#### P8.7. Decoupled Resilience & Local Staging Queue for Active Spoke Development (ADR 0043)
* **Nguyên tắc:** Khi một Spoke doanh nghiệp (`IDOP-CCBA-WAY`) đang trong giai đoạn tích cực triển khai lên Microsoft 365, hệ thống duy trì tính độc lập (Decoupling) bằng hàng đợi cục bộ [`.md/idop_staged/`](../../.md/) với trạng thái `STAGED_LOCAL`.
* **Giải pháp:** Kỹ sư dự án tiếp tục làm việc bình thường (**Zero-Downtime**), khi kết nối mạng/SharePoint thông suốt trở lại, lệnh `idop_bridge --flush` thực hiện **Idempotent Replay** đồng bộ bù lên đám mây mà không gây trùng lặp bản ghi.

#### P8.8. CI Schema Contract Drift Gate & Zero-Config Dual-Mode Auth (ADR 0043)
* **Nguyên tắc:**
  - *Bảo vệ Schema Khung Xương:* Bài test tự động `test_idop_schema_compatibility.py` cho phép nhóm IDOP tự do thêm cột/bảng mới (Open for Extension) nhưng khóa cứng không cho phép xóa/đổi tên 5 trường cốt lõi (`ProjectCode`, `NationalProjectID`, `ContractId`, `JobAssignments`, `CdeDocuments`).
  - *Trải nghiệm Lập trình 0-Giây (Zero-Config):* Mặc định `IDOP_ENV="DEV"` kích hoạt Local Mock Sandbox, cho phép Kỹ sư mới và CI runners chạy thử toàn bộ logic mà không cần cấp quyền truy cập hay chứng chỉ `.pfx` thật.

#### P8.9. Automated Knowledge Doc-Evolution Daemon & In-Memory AST Grounding (Ticket D-01-D-04)
* **Nguyên tắc:** Hệ thống tài liệu tri thức (LLM-Wiki) phải tự tiến hóa song song với mã nguồn thực tế mà không đòi hỏi con người cập nhật thủ công liên tục.
* **Giải pháp:**
  - *In-Memory AST Code-Grounding:* `CodeGroundingEngine` quét toàn bộ ký hiệu Python và ADRs trong bộ nhớ (< 150ms) để xác thực mọi dẫn chứng mã nguồn trước khi AI được phép đề xuất cập nhật tài liệu.
  - *Zero-Deletion & Parse-Protection Invariants:* `ZeroDeletionGuard` bẫy diff để ngăn chặn AI xóa bỏ bất kỳ tri thức cũ nào (chỉ cho phép gắn thẻ `[DEPRECATED]`) và bảo vệ 100% các khối ghi chú viết tay `<!-- DEVELOPER-NOTES-START -->` ... `<!-- DEVELOPER-NOTES-END -->`.
  - *HitL PR Ratchet & Telegram Alert:* Tiến trình qua đêm lúc 00:00 trên Server Spark tự động tạo branch `docs/auto-refactor-YYYYMMDD`, mở PR trên GitHub kèm lệnh duyệt 1-chạm `gh pr merge --squash` và gửi báo cáo tóm tắt 3 dòng tới Telegram của Kỹ sư.

#### P8.10. Project Delivery Spoke Non-Remote-Git SOP & ccba-spoke CLI Staging Engine (WF-01, WF-03, WF-04)
* **Nguyên tắc:** Các dự án tư vấn sản xuất hồ sơ thực tế (`project_delivery`) vận hành trên **OneDrive của CCBA**, không sử dụng Git remote để triệt tiêu rủi ro rò rỉ hồ sơ mật và tránh xung đột tệp nhị phân đồ họa (Revit `.rvt`, AutoCAD `.dwg`, scan PDF).
* **Giải pháp:** Kỹ sư sử dụng tiện ích dòng lệnh `ccba-spoke` (`ccba-spoke status`, `ccba-spoke sync`, `ccba-spoke stage`, `ccba-spoke flush`):
  - *AI Pre-Submission Gate:* Tự động quét và chặn ngay các vi phạm Hard-Floor (viện dẫn văn bản hết hiệu lực như NĐ 06/2021, sai mã dự án).
  - *Local-First Staging Queue:* Tạo biên nhận PGV JSON (`PGV-<timestamp>-<task_id>.json`) với trạng thái `STAGED_LOCAL` lưu tại `.md/idop_staged/`.
  - *Idempotent Replay:* Khi PM duyệt hoặc khi có kết nối mạng, lệnh `ccba-spoke flush` đẩy bản ghi lên 58 SharePoint Lists IDOP và cập nhật trạng thái `SYNCED_SHAREPOINT`.

#### P8.11. AI Gateway 3-Tier Quota Matrix & Graceful Local-GPU Auto-Fallback on Spark Server (WF-02)
* **Nguyên tắc:** Cân bằng giữa tự do sáng tạo trong Personal Sandbox và kiểm soát ngân sách đám mây bằng Ma trận 3 tầng:
  - *Tier 1 (Personal Sandbox):* Không giới hạn Local GPU (vLLM Qwen 35B FP8 trên Server Spark DGX); Capped $5/tháng Cloud (~50k tokens/ngày).
  - *Tier 2 (Project Delivery & Governance):* Phân bổ theo ngân sách dự án ($50-$200/dự án); cấp quyền Full Multimodal Vision Quad-view PCCC.
  - *Tier 3 (Platform Hub & Nightly Daemon):* Dynamic Budget $10/đêm, ưu tiên chạy 00:00-05:00 kết hợp Circuit Breaker.
  - *Graceful Fallback Invariant:* Khi cạn quota Cloud hoặc API ngoài gặp lỗi 429/503, Gateway tự động giáng cấp ngầm về Qwen 35B Local GPU mà không làm gián đoạn hay crash tiến trình của Kỹ sư.

#### P8.12. Deep Sub-Package Modularization & Forwarding Shim Invariant (ADR 0048, Pattern P6.9 & P6.11)
* **Nguyên tắc:** Khi một tệp mã nguồn đơn lẻ vượt ngưỡng monolith (> 1.000 dòng hoặc gánh trên 5 trách nhiệm miền), tệp đó PHẢI được phân rã thành domain sub-package với các sub-module chuyên biệt và giữ lại Thin Forwarding Facade để duy trì 100% tương thích ngược.
* **Giải pháp:**
  - *Domain Sub-Package Layout:* Chia nhỏ thành các module rõ ràng (`discovery.py`, `catalog.py`, `registry.py`, `sdk_inspector.py`, `backup.py`, `coordinator.py`, `cli.py`, `base.py`).
  - *Resilient Forwarding Shim (P6.11):* Tệp monolith ban đầu được thu gọn thành Thin Facade (&le; 60 dòng) re-export 100% symbols và điều hướng CLI an toàn, cho phép 12+ callers cũ hoạt động bình thường mà không cần sửa code caller.
  - *Dynamic Monkeypatch Support:* Coordinator hỗ trợ phân giải động các class được mock trên Facade trong môi trường kiểm thử unit tests.
  - *Canonical DTO Single Source of Truth (P6.21):* Triệt tiêu duplicate classes (`ASTNode`, `PatchAction`, `GovernanceAuditReport`) về một `models.py` duy nhất, loại bỏ xung đột ký hiệu trên toàn monorepo.

### ⚠️ Anti-Patterns (Cần Tránh)
* **AP8.1. Bypassing Tier 1 Hard-Floor Gate:** Cho phép xuất hồ sơ trình Viện IBST khi vẫn còn lỗi sai số học dòng tiền hoặc viện dẫn luật hết hiệu lực.
* **AP8.2. Direct Heavy Binary Upload to SharePoint:** Upload trực tiếp file mô hình Revit 3D hoặc scan nặng vào SharePoint List làm cạn kiệt dung lượng Tenant 2TB thay vì đưa sang 5TB Master OneDrive.
* **AP8.3. Running Production Daemon without Mock Sandbox Isolation:** Chạy các bài test đánh giá kỹ năng ban đêm mà không cô lập biến môi trường `IDOP_ENV=DEV`, gây nghẽn và fail test khi SharePoint bảo trì.
* **AP8.4. Ungrounded Knowledge Document Refactoring:** Cho phép AI tự do sửa đổi tài liệu kiến trúc hoặc session learnings mà không có AST Code-Grounding và Zero-Deletion guardrails bảo vệ, dẫn đến mất mát bài học lịch sử và sinh ảo giác (hallucinations).
* **AP8.5. Forcing Git Remote onto Production Delivery Spokes:** Ép buộc các Spoke dự án hiện trường phải tạo kho Git remote công khai hoặc mở PR trên GitHub, gây nguy cơ rò rỉ hồ sơ khách hàng và làm phình to kho Git với các tệp CAD/Revit nặng.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Tài liệu này là tài sản tri thức cốt lõi được cập nhật liên tục qua từng phiên làm việc của Platform.*

