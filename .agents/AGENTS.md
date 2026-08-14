# CCBA Workspace Rules — Layer 1 Constitution

> [!IMPORTANT]
> **Đây là Hiến pháp Tối cao và là nguồn quy tắc duy nhất về hành vi của Agent.**
> Mọi quy định dưới đây phải được tuân thủ nghiêm ngặt trong tất cả các phiên làm việc và trên mọi dự án (Spokes) liên kết với Platform.
> Các tài liệu khác (như README.md hoặc SKILL.md) là Layer 2 hoặc Layer 3 và không được phép ghi đè hay thay đổi các quy tắc cốt lõi này.

---

## 1. CCBA Agent Services Platform (Hub) - Reuse-First Gate

Trước khi viết bất kỳ utility/script mới nào tại Spoke (extract, convert, parse...), Agent **PHẢI** thực hiện đánh giá tái sử dụng.
* **Rào cản bắt buộc:** Trong mọi tài liệu kế hoạch triển khai (`implementation_plan.md`) được tạo ra, Agent **bắt buộc phải điền** một mục riêng mang tên `## Đánh giá khả năng tái sử dụng (Reuse Assessment)`.
* **Nội dung bắt buộc trong kế hoạch:**
  * Trạng thái tra cứu Hub catalog (`platform-loader/catalog.yaml`): Chỉ rõ các tool/workflow trùng lặp hoặc liên quan đã tồn tại.
  * Đánh giá cost-benefit: Lý do chi tiết của việc đề xuất viết mới hoặc kế thừa (nêu rõ các yếu tố về dependencies, network, complexity).
* Nếu thiếu mục đánh giá này, kế hoạch triển khai sẽ bị coi là vi phạm nghiêm trọng quy chế làm việc và không được phép tiến hành thực thi.
* **Quy tắc phân biệt Hub và Spoke (Bắt buộc):**
  Agent tự nhận diện môi trường làm việc thông qua việc chạy lệnh `git remote get-url origin`:
  - Nếu kết quả chứa cụm từ `ccba-agent-platform` $\rightarrow$ Xác định dự án hiện tại là **Hub**. Bỏ qua các lệnh đề xuất đóng góp ngược (như `/ccba-propose-to-hub` hay đề xuất export/pull request lên Hub) do mã nguồn đã nằm trực tiếp tại trung tâm.
  - Các trường hợp khác $\rightarrow$ Xác định là **Spoke**. Bắt buộc tuân thủ Reuse-First Gate và đề xuất đóng góp tính năng ngược lên Hub khi hoàn tất.
* **Workspace Mode (`project.mode`):** Trường `project.mode` trong `.md/workspace_context.yaml` quyết định cấu trúc workspace vật lý của Spoke:
  - `software` — `.md/` tối giản (chỉ `workspace_context.yaml` + `scratch/`), output convert → `docs/references/`.
  - `delivery` — `.md/` đầy đủ (10 thư mục con nghiệp vụ), output convert → `.md/extracted_docs/`.
  - `hybrid` — Kết hợp cả hai (dùng cho Hub hoặc R&D Spoke cần cả domain knowledge lẫn software tooling).

---

## 2. CCBA Core Behavior & Quality Standards

* **Giọng điệu giao tiếp:** Trả lời bằng **tiếng Việt** (trừ khi người dùng dùng tiếng Anh). Giữ nguyên các thuật ngữ kỹ thuật tiếng Anh (function, class, endpoint, database...). Giao tiếp chuyên nghiệp, súc tích, khách quan.
* **KISS (Keep It Simple, Stupid):** Luôn ưu tiên giải pháp đơn giản nhất. Trước khi đề xuất thêm module/class/abstraction mới, tự hỏi: "Có thể giải quyết bằng 10-15 dòng code trong file hiện có không?" Nếu có $\rightarrow$ làm vậy.
* **Đăng ký Rules động:** Đối với các quy tắc nghiệp vụ chuyên sâu (đặt tên, debug, release gate, legal...), Agent bắt buộc phải nạp động (**Dynamic Rules**) tương ứng qua `catalog.yaml` thay vì tích hợp tĩnh vào prompt khởi tạo.
* **Nạp Tri thức Tích lũy (Session Learnings Bootstrap):** Khi bắt đầu lập kế hoạch (**Planning Mode**) hoặc triển khai mã nguồn (**SDLC Implementation Loop**), Agent **bắt buộc phải đọc** tệp `.md/knowledge/session_learnings.md` (nếu tệp tồn tại) để nạp các Patterns/Anti-patterns đã được đúc kết qua các phiên trước, tránh lặp lại sai lầm cũ. Tệp này chứa 7 trụ cột tri thức cốt lõi của Platform.
* **Kiểm định mã nguồn, cấu hình & tài liệu:** 
  - Mọi file YAML được Agent chỉnh sửa phải pass qua lệnh parse `yaml.safe_load()`.
  - Luôn sử dụng type hints trong Python (parameters + return types), viết docstring (Google style) cho tất cả public functions.
  - Hàm/phương thức không dài quá 50 dòng; ưu tiên composition over inheritance.
* **Quy trình thực thi mã nguồn (SDLC Implementation Loop):**
  Khi triển khai bất kỳ mã nguồn nào dựa trên đặc tả (specs - Đặc tả Kỹ thuật), Agent bắt buộc phải thực thi theo chu kỳ khép kín:
  1. *TDD (Test-Driven Development)*: Viết unit tests trước tại các điểm khớp nối (seams) đã thỏa thuận nếu áp dụng.
  2. *Continuous Validation*: Chạy kiểm tra kiểu (typecheck), test và chạy toàn bộ test suite trước khi hoàn tất.
  3. *Review before Merge*: Chạy kỹ năng `/ccba-code-review` để quét các code smells trước khi commit/PR.
* **Ruff Scoping & Markdown Isolation:** Khi cấu hình Ruff Linter & Formatter (trong `pyproject.toml` hoặc script test runner `run_harness_evals.py`), Agent **bắt buộc phải loại trừ `*.md`** (`docstring-code-format = false`) và chỉ định rõ các thư mục chứa mã nguồn Python thực sự (`packages`, `scripts`, `src`). Tránh quét format các đoạn mã ví dụ trong tài liệu Markdown làm bẻ gãy CI runner.

---

## 3. Git Conventions

* **Đặt tên Branch:** `type/short-description` *(ví dụ: feature/add-auth, fix/query-timeout)*.
* **Format Commit Message:** `type(scope): description` (bằng tiếng Anh).
  - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`.
  - Commit theo từng logical unit độc lập, không commit tất cả file cùng lúc.

---

## 4. Execution Guardrails & Async Task Policy

* **Scoped Test Execution:** Nghiêm cấm Agent kích hoạt các lệnh kiểm thử toàn diện (unscoped `pytest`) trên cả repository mà không chỉ định rõ file test mục tiêu cụ thể (ví dụ: bắt buộc phải dùng `python scripts/safe_pytest.py -f tests/test_file.py` hoặc `.venv\Scripts\pytest.exe tests/test_file.py`).
* **Bounded Async Task & Anti-Polling Circuit Breaker:** Khi một lệnh chạy dưới dạng tác vụ ngầm (Background Task):
  - Agent có thể dùng `manage_task status` tối đa **2 lần** để kiểm tra tiến độ tác vụ ngắn.
  - Nếu tác vụ vẫn ở trạng thái `RUNNING` sau 2 lần kiểm tra, Agent **NGHIÊM CẤM** lặp polling `manage_task status` dồn dập trong cùng một lượt. Agent phải xuất ra thông báo súc tích cho người dùng rồi **kết thúc lượt (End Turn)**. Hệ thống nền sẽ tự động gửi thông báo Reactive Wakeup khi tác vụ hoàn tất.
* **TDD Retry Cap:** Trong vòng lặp Red→Green→Refactor (TDD) hoặc edit→test (implement), Agent chỉ được lặp lại tối đa **5 vòng** cho cùng một seam hoặc test file. Nếu sau 5 vòng test vẫn fail, Agent phải dừng lại, commit Work-In-Progress (WIP), ghi nhận các blockers chưa giải quyết được, và xin chỉ thị từ người dùng — tuyệt đối không tiếp tục lặp cho đến khi cạn context budget.
* **Anti-Duplicate Background Runner:** Nghiêm cấm Agent kích hoạt nhiều lệnh chạy ngầm (`run_command` async) cho cùng một script test runner (`run_harness_evals.py` hoặc `pytest`). Luôn đảm bảo script test runner đã tự động tích hợp Singleton Process Lock (`ensure_single_instance()`) và chờ tiến trình cũ kết thúc hoặc hủy tiến trình cũ trước khi chạy tiến trình mới.
* **Safe Process Termination Invariant:** Khi viết bất kỳ script nào có chức năng dọn dẹp hoặc duy trì đơn tiến trình (Singleton Process Lock / `ensure_single_instance()`), Agent **bắt buộc phải loại trừ** cả tiến trình hiện tại (`os.getpid()`) và tiến trình cha (`os.getppid()`). Nghiêm cấm kích hoạt `taskkill` hoặc `proc.terminate()` lên `os.getppid()` để tránh làm sập Agent Server Host.
* **Task Log Readiness Check:** Nghiêm cấm Agent gọi `view_file` tới tệp `task-XXX.log` lập tức ngay sau lượt `run_command` async mà không kiểm tra xem tệp tin log đã thực sự được hệ thống tạo và ghi dữ liệu lên ổ đĩa hay chưa. Phải dùng `command_status` hoặc chờ thông báo hoàn tất từ hệ thống trước khi đọc log.
* **Invalid Args Circuit Breaker:** Khi Agent gặp lỗi `model output error: invalid tool call error (invalid_args)` từ **2 lần liên tiếp trở lên**, đây là tín hiệu context budget sắp cạn kiệt. Agent phải **dừng ngay lập tức**, commit WIP nếu có thay đổi chưa lưu, tóm tắt trạng thái công việc hiện tại, và thông báo cho người dùng mở phiên mới để tiếp tục — không được cố gắng chạy thêm bất kỳ tool call nào.
* **2-Tier Test Speed Compliance:** Mọi tệp kiểm thử đơn vị (Unit Test) mới viết bắt buộc phải chạy dưới 2.0 giây (`test_speed_guard.py`). Các tệp test tích hợp mạng/CDP nặng phải được dán decorator `@pytest.mark.slow` hoặc `@pytest.mark.stress` để tự động loại trừ khỏi vòng lặp kiểm thử nhanh hàng ngày (`-m "not slow"`).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
