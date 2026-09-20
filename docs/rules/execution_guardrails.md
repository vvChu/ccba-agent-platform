# CCBA Execution Guardrails & Async Task Policy

> **Tài liệu Tham chiếu Quy chuẩn Thực thi (Layer 2)**  
> Áp dụng cho toàn bộ các tác vụ lập trình, chạy kiểm thử, và điều phối quy trình ngầm trên CCBA Platform.

---

## 1. Scoped Test Execution (Kiểm thử Cô lập)
- Nghiêm cấm kích hoạt các lệnh kiểm thử toàn diện (unscoped `pytest`) trên toàn bộ repository mà không chỉ định rõ phạm vi.
- Luôn chỉ định rõ file test hoặc module mục tiêu: ví dụ `pytest packages/{pkg}/tests/test_file.py` hoặc cờ loại trừ `-m "not slow and not stress"`.

---

## 2. Bounded Async Task, Zero-Polling & Reactive Wakeup Invariant
- Khi một lệnh chạy dưới dạng tác vụ ngầm (Background Task) như `run_harness_evals.py`, `pytest`, hoặc `gh pr checks`:
  - **Nguyên lý Reactive Wakeup (Thức dậy theo sự kiện - Bắt buộc):** Hệ thống Antigravity tự động đánh thức và gửi thông điệp `<SYSTEM_MESSAGE>` cho Agent ngay khi tác vụ nền hoàn thành.
  - **Chính sách Không Polling Tuyệt Đối (Zero-Tolerance Polling Policy):**
    - Nghiêm cấm Agent tự tạo vòng lặp kín để thăm dò trạng thái (`manage_task status`) nhiều lần liên tiếp trong lúc chờ tiến trình nền.
    - **Hành động bắt buộc ngay sau khi lệnh chuyển sang Background Task:**
      1. **Dừng gọi công cụ (Stop Calling Tools / End Turn):** Thông báo ngắn gọn cho người dùng (nếu cần) và kết thúc lượt ngay lập tức để runtime tự động đánh thức khi tác vụ hoàn thành.
      2. **Hoặc Triển khai công việc song song có ích (Parallel Work):** Soạn thảo tài liệu, cập nhật artifact, phân tích mã nguồn độc lập khác trong lúc chờ — tuyệt đối không chèn các lệnh kiểm tra trạng thái vô nghĩa.
  - **Nguyên tắc Scoped Execution First:**
    - Với các lệnh kiểm tra cục bộ, **luôn chỉ định phạm vi hẹp (Scoped Target)** kết hợp cấu hình `WaitMsBeforeAsync=10000` (10s) để lệnh hoàn tất đồng bộ ngay trong lượt gọi đầu tiên, tránh đẩy vô cớ xuống Background Task.
    - Nghiêm cấm chạy full test suite unscoped chỉ để kiểm tra 1 thay đổi cục bộ.
  - **Rào chắn lệnh theo dõi CI (`gh pr checks`):** Nghiêm cấm chạy `gh pr checks --watch` kết hợp lặp `manage_task status`. Thay vào đó, chạy `gh pr checks` đơn lẻ hoặc khởi chạy `--watch` rồi lập tức dừng lượt để hệ thống tự động trả về kết quả khi CI hoàn tất.
  - **Rào chắn Review Requests của Copilot (Chống Race Condition):** Nghiêm cấm kích hoạt `gh pr merge` khi `gh pr view --json reviewRequests` vẫn còn chứa bot reviewer (`copilot-pull-request-reviewer`). Phải đợi bot hoàn thành nộp bài review và đối soát toàn bộ comments trước khi merge.

---

## 3. TDD Retry Cap & Early Escalation (Giới Hạn Vòng Lặp & Điểm Cắt Lỗi)
- Trong vòng lặp Red→Green→Refactor (TDD) hoặc edit→test, Agent chỉ được lặp lại tối đa **5 vòng** cho cùng một seam hoặc test file.
- **Quy tắc Cắt Lỗi Sớm (Early Escalation tại vòng 3):**
  - Nếu sau **3 vòng test liên tiếp** vẫn không pass do lỗi logic sâu, race condition, hoặc xung đột đa file: Agent **bắt buộc dừng thử mù**, không được tiếp tục đoán mò cách sửa.
  - Agent phải lập tức đóng gói **Deep Problem Brief** (gồm: Triệu chứng lỗi, Giả thuyết đã thử nhưng sai, Các code seams liên quan, Log lỗi then chốt).
- **Hành động tại vòng 5 (Hard Stop):**
  - Nếu chạm mốc 5 vòng, Agent dừng ngay lập tức, commit Work-In-Progress (WIP), xuất Deep Problem Brief và kích hoạt **Boost Escalation Gate** (Mục 9) — tuyệt đối không lặp tiếp làm cạn kiệt ngân sách ngữ cảnh.

---

## 4. Anti-Duplicate Background Runner
- Nghiêm cấm Agent kích hoạt nhiều lệnh chạy ngầm (`run_command` async) cho cùng một script test runner hoặc harness evaluation.
- Mọi script test runner ngầm bắt buộc phải tích hợp Singleton Process Lock (`ensure_single_instance()`) và kiểm tra tiến trình cũ trước khi khởi động.

---

## 5. Safe Process Termination Invariant
- Khi viết hoặc thực thi bất kỳ logic nào có chức năng dọn dẹp hoặc duy trì đơn tiến trình (`ensure_single_instance()`), Agent **bắt buộc phải loại trừ** cả tiến trình hiện tại (`os.getpid()`) và tiến trình cha (`os.getppid()`).
- Nghiêm cấm kích hoạt `taskkill` hoặc `proc.terminate()` lên `os.getppid()` để tránh làm sập Agent Server Host.

---

## 6. Task Log Readiness Check
- Nghiêm cấm gọi `view_file` tới tệp `task-XXX.log` lập tức ngay sau lượt `run_command` async mà không kiểm tra xem tệp tin log đã thực sự được hệ thống tạo và ghi dữ liệu lên ổ đĩa hay chưa.
- Phải dùng `manage_task status` hoặc chờ thông báo hoàn tất từ hệ thống trước khi đọc log.

---

## 7. Invalid Args Circuit Breaker
- Khi gặp lỗi `model output error: invalid tool call error (invalid_args)` từ **2 lần liên tiếp trở lên**, đây là tín hiệu context budget sắp cạn kiệt.
- Agent phải **dừng ngay lập tức**, commit WIP nếu có thay đổi chưa lưu, tóm tắt trạng thái công việc hiện tại, và thông báo cho người dùng mở phiên mới để tiếp tục — không được cố gắng chạy thêm bất kỳ tool call nào.

---

## 8. 2-Tier Test Speed Compliance
- Mọi tệp kiểm thử đơn vị (Unit Test) mới viết bắt buộc phải chạy dưới 2.0 giây.
- Các tệp test tích hợp mạng, Chromium CDP, hoặc LLM latency nặng bắt buộc phải được dán decorator `@pytest.mark.slow` hoặc `@pytest.mark.stress` để tự động loại trừ khỏi vòng lặp kiểm thử nhanh hàng ngày (`-m "not slow"`).

---

## 9. Boost Deep Reasoning Protocol & Escalation Gate
- Khi xử lý các bài toán kỹ thuật có độ phức tạp cao vượt quá khả năng xử lý của vòng lặp đơn lẻ (Single-turn ReAct), Agent và Kỹ sư CCBA áp dụng quy chuẩn **Boost Deep Reasoning**:
  - **Trường hợp kích hoạt:**
    1. **Concurrency & Race Conditions:** Xung đột tiến trình nền, mutex lock (`TVPLSessionMutex`), pipeline đa tiến trình (VvC Second Brain daemons, IDOP staging sync).
    2. **Polyglot Monorepo Deep Refactoring:** Tái cấu trúc hoặc trích xuất Deep Seams qua nhiều package Python/TypeScript đồng thời.
    3. **Thẩm định Pháp lý & Xung đột Quy chuẩn Đa ngành:** Xử lý các điều khoản chồng chéo, xung đột ranh giới thẩm quyền (Luật 55/2024, NĐ 105/2025, QCVN 06, TCVN 3890).
    4. **Bế tắc TDD (Chạm ngưỡng 3–5 vòng test fail):** Khi TDD Retry Cap bị kích hoạt.
  - **Quy chuẩn Đóng Gói Deep Problem Brief:**
    Khi kích hoạt Escalation Gate, Agent phải tổng hợp tệp hoặc thông điệp chuẩn mực:
    ```markdown
    ### 🔬 Deep Problem Brief
    - **Vấn đề cốt lõi (Failure Manifest):** [Mô tả ngắn gọn lỗi kỹ thuật/test fail]
    - **Các giả thuyết đã kiểm chứng & Thất bại (Tested Hypotheses):** [Liệt kê 2-3 cách sửa đã thử và lý do fail]
    - **Vùng ảnh hưởng (Seams Involved):** [Danh sách files / classes / functions liên quan]
    - **Logs / Error Trace:** [Trích đoạn log lỗi then chốt]
    - **Khuyến nghị hành động:** [Đề xuất người dùng kích hoạt `/boost` kèm brief này để chạy chu trình suy luận đa tác nhân]
    ```
  - **Rào chắn An Toàn Đa Tác Nhân (Two-Layer Sub-Agent Guardrail — ADR 0035):**
    Khi quy trình CCBA tự động mô phỏng hoặc khởi tạo các subagents chạy ngầm theo mô hình 3 pha của Boost (Strategy $\rightarrow$ Parallel Workers $\rightarrow$ Synthesis):
    1. **Giới hạn Độ sâu (Depth Limit = 1):** Nghiêm cấm subagent spawn thêm subagent con để chống bùng nổ đệ quy.
    2. **Giới hạn Công cụ (Tool Scoping):** Subagents chỉ được cấp quyền công cụ đọc (`view_file`, `grep_search`, `read_resource`) và chạy kiểm thử cô lập (`run_command` scoped test), tuyệt đối không cấp quyền chỉnh sửa file hoặc lệnh Git nguy hiểm.
    3. **Giới hạn Số Lượng (Max Workers):** Tối đa 3 subagents chạy song song trong một phiên điều tra/nghiên cứu.

---

## 10. Teamwork Orchestration Protocol (Quy Chuẩn Điều Phối Đa Tác Nhân Dài Hạn)
- Khi triển khai các dự án quy mô lớn đòi hỏi phân rã đa seams (Monorepo refactoring, thẩm tra thiết kế 4 bộ môn, nạp kho pháp điển hàng loạt), Platform áp dụng khung **Teamwork Framework** (lấy cảm hứng từ Antigravity `/teamwork-preview` và ADR 0053):
  - **Mô hình 3 Vai Trò Tối Giản (KISS Hierarchy):**
    1. **Orchestrator (Nhạc Trưởng):** Chịu trách nhiệm toàn trình (phỏng vấn, lập `team_sheet.md`, dispatch workers, điều phối, tổng hợp kết quả, ghi file chính thức và commit Git). Duy nhất Orchestrator có quyền ghi đè codebase.
    2. **Workers (Tác Nhân Thực Thi):** Chạy song song độc lập. Tuân thủ nghiêm ngặt **Two-Layer Guardrail (ADR 0035)**: Chỉ có quyền đọc và chạy test scoped; xuất kết quả phân tích/code draft dưới dạng artifact text vào thư mục sandbox cô lập (`.system_generated/scratch/worker_{N}/`).
    3. **Success Auditor (Kiểm Định Nghiệm Thu):** Độc lập chạy kiểm thử scoped, quét an toàn Maskara, và thực hiện kiểm toán phân vùng file.
  - **Giới Hạn Tác Nhân & Chiến Lược Phân Đợt (Worker Cap & Batching Strategy):**
    - Tối đa **3 workers** chạy đồng thời trong cùng một thời điểm.
    - Nếu dự án có nhiều hơn 3 seams/milestones độc lập, Orchestrator **bắt buộc phân đợt** (Batching): chạy tối đa 3 workers/batch, chờ batch hoàn tất rồi mới dispatch batch tiếp theo.
  - **Kiểm Toán Phân Vùng Hậu Hợp Nhất (Post-Merge Diff Audit):**
    - Sau mỗi milestone, trước khi hợp nhất, Auditor hoặc Orchestrator phải đối chiếu `git diff --name-only` với danh sách file scope đã khai báo trong `team_sheet.md`.
    - Mọi tệp tin bị sửa đổi nằm ngoài phạm vi seam được phân quyền phải bị gắn cờ cảnh báo rò rỉ seam (Seam Boundary Leakage) để Orchestrator xử lý trước khi commit.
  - **Rào Chắn Quá Giờ & Cơ Chế Khôi Phục (Worker Timeout & Fallback Protocol):**
    - Mỗi worker có thời hạn tối đa là **10 phút** cho một tác vụ subagent.
    - Nếu worker không phản hồi hoặc gặp lỗi suy thoái ngữ cảnh (`invalid_args` / Context Exhaustion): Orchestrator đánh dấu milestone là `INCOMPLETE`, trích xuất log trung gian và chọn 1 trong 2 nhánh:
      - *Nhánh A:* Khởi động lại với Worker mới kèm prompt thu hẹp phạm vi.
      - *Nhánh B:* Nếu lỗi do bế tắc logic sâu, đóng gói Deep Problem Brief và kích hoạt `/boost` (Escalation UP).
  - **Phân Định Ranh Giới `/boost` vs `/ccba-teamwork`:**
    - **`/boost` (Escalation UP):** Xử lý sự cố kỹ thuật bế tắc, phân tích sâu lỗi logic/concurrency đơn lẻ trong phạm vi 1 session.
    - **`/ccba-teamwork` (Coordination OUT):** Điều phối phân rã dự án quy mô lớn thành nhiều workstreams độc lập chạy song song qua nhiều milestones.
    - **Kết hợp:** Trong phiên Teamwork, nếu một Worker gặp sự cố logic bế tắc tại seam của mình, Orchestrator có thể kích hoạt Boost Escalation Gate để xử lý triệt để seam đó trước khi tiếp tục chu trình Teamwork.

---

## 11. Antigravity Lifecycle Hooks Policy (Chính Sách Móc Vòng Đời Antigravity) — ADR 0054
- Platform tích hợp **Antigravity Lifecycle Hooks** (`hooks.json`) theo kiến trúc Adapter Bridge (ADR 0054):
  - **Bridge = Adapter Layer Mỏng:** File `scripts/hooks/antigravity_hook_bridge.py` chỉ dịch schema giữa Antigravity stdin/stdout (camelCase) và CCBA `HookCoordinator` (snake_case). Không chứa business logic chặn/quét.
  - **Schema Translation:** `toolCall.name` → `tool`, `toolCall.args` (object) → `args` (JSON string), `exit_code` (0/1/2) → `decision` (allow/ask/deny).
  - **Phase 1:** Chỉ bật `PreToolUse` trên matcher `run_command|write_to_file|replace_file_content|multi_replace_file_content`.
  - **Hiệu năng:** Tổng subprocess overhead ~200-500ms trên Windows (Python startup), logic-only < 15ms. Hooks chạy đồng bộ, chặn agent loop.
  - **Fail-Safe Default:** Mọi ngoại lệ không mong muốn trong bridge đều fallback về `{"decision": "allow"}` — không bao giờ làm gián đoạn IDE.
  - **Hai Entry Point:** CLI `hook_runner.py` (offline/CI) và Antigravity `hooks.json` (IDE) cùng dẫn về `HookCoordinator` với cùng 7 hooks.

---

## 12. Safe GitHub CLI File-Based Input Invariant (Quy Chuẩn Nhập Dữ Liệu Qua File cho GitHub CLI)
- Khi gọi các lệnh GitHub CLI (`gh issue comment`, `gh issue create`, `gh pr create`, `gh pr comment`) có nội dung nhiều dòng, Markdown phức tạp, mã nguồn hoặc ký tự đặc biệt:
  - **Nghiêm cấm:** Truyền trực tiếp chuỗi nội dung qua tham số dòng lệnh `--body "..."` (dễ gây lỗi escape ký tự, vượt quá độ dài dòng lệnh hệ điều hành và bị pre-tool security hook chặn).
  - **Bắt buộc (File-First Pattern):**
    1. Ghi nội dung cần đăng vào tệp tạm thời trong thư mục `.md/scratch/` (ví dụ: `.md/scratch/comment_<id>.md` hoặc `.md/scratch/pr_body.md`).
    2. Sử dụng cờ `-F` hoặc `--body-file` để truyền đường dẫn tệp tin:
       ```bash
       gh issue comment <issue_id> -F .md/scratch/comment_<issue_id>.md
       gh pr create --title "..." -F .md/scratch/pr_body.md
       ```
    3. Mẫu này đảm bảo bảo toàn 100% mã hóa UTF-8, định dạng Markdown, bảng biểu và không bao giờ bị bộ lọc an toàn command-line từ chối.

---

## 13. Multi-Client Issue & Pull Request Coordination Protocol (Quy Chuẩn Điều Phối Issue và PR Đa Máy & Khóa Nhận Việc)

### A. Quy Trình Khóa Nhận Việc Cho GitHub Issues (Issue Claim Locking - TTL 24h)
1. **Chuyển trạng thái tức thì:**
   - Kiểm tra nhãn hiện tại qua `gh issue view <id> --json labels`. Chỉ gỡ `ready-for-agent` hoặc `backlog` nếu nhãn đó thực sự tồn tại (tránh lỗi API 404).
   - Gán nhãn `in-progress` và gán assignee động theo tài khoản đang đăng nhập:
     ```bash
     gh issue edit <id> --add-label "in-progress" --add-assignee "@me"
     ```
2. **Đăng thông báo nhận việc máy-đọc-được (Machine-Parseable Claim Notice):**
   - Tạo tệp nội dung tạm thời trong `.md/scratch/` và đăng qua cờ `-F` (tuân thủ Guardrail 12):
     ```markdown
     <!-- CCBA_PEER_CLAIM_LOCK
     host: [linux-workstation / windows-pc / wsl]
     branch: feat/issue-[id]-[short-desc]
     claimed_at: [ISO-8601-UTC-Timestamp]
     ttl_hours: 24
     -->
     🤖 **Agent Claim & Coordination Notice**: Issue này đang được xử lý trong phiên làm việc hiện tại trên môi trường [OS]. Vui lòng bỏ qua, không claim nhận việc trùng lặp.
     ```
3. **Khóa an toàn chống đua đồng thời (Post-Claim Verification & Concurrency Safe-Guard):**
   - Sau khi đăng claim, Agent bắt buộc đọc lại danh sách comments: `gh issue view <id> --json comments`.
   - Nếu phát hiện có một Claim Notice của peer agent khác được đăng trước comment của mình dù chỉ vài giây: Agent nhận việc sau **bắt buộc phải nhượng bộ (yield)**, tự động rollback (`--remove-label "in-progress"`) và chuyển sang tìm issue khác.
4. **Xử lý Stale Claims (Cơ Chế Takeover Sau 24h):**
   - Nếu một issue mang nhãn `in-progress` nhưng không có commit mới nào trên nhánh remote liên kết trong vòng **24 giờ** $\rightarrow$ issue được coi là *Stale Claim*.
   - **Chế độ tương tác (Interactive):** Agent hỏi ý kiến người dùng: *"⚠️ Issue #X đang in-progress bởi client cũ nhưng đã ngừng hoạt động > 24h. Bạn có muốn tiếp quản (re-claim) issue này không?"*. Khi người dùng đồng ý, Agent đăng comment takeover và đổi assignee sang `@me`.
   - **Chế độ tự động/ngầm (Headless/CI/Daemon):** Agent tự động bỏ qua (skip) để tránh treo tiến trình.
5. **Nghiệm thu & Đóng Issue sạch sẽ (Clean Handoff & Closure):**
   - Khi hoàn tất và PR được squash merge vào `main`, để lại bình luận tổng kết nghiệm thu kèm PR link/Commit SHA và đóng issue ngay lập tức (`gh issue close <id> --reason "completed"`).

### B. Quy Trình Khóa Tranh Chấp Cho Pull Requests (PR Claim Locking & Lease Push - TTL 4h)
1. **Khóa Nhận Xử Lý PR (PR Assignee & Status Locking):**
   - Khi Agent tiếp nhận một PR để review, sửa lỗi CI, hoặc đối soát nhận xét Copilot:
     ```bash
     gh pr edit <id> --add-assignee "@me" --add-label "in-progress"
     ```
2. **Đăng PR Lock Notice (TTL = 4 giờ):**
   - Đăng comment khóa PR qua tệp tin trong `.md/scratch/`:
     ```markdown
     <!-- CCBA_PR_CLAIM_LOCK
     host: [linux-workstation / windows-pc / wsl]
     agent_role: [pr-review / ci-repair / merge-release]
     branch: [head-branch-name]
     claimed_at: [ISO-8601-UTC-Timestamp]
     ttl_hours: 4
     -->
     🤖 **Agent PR Claim Notice**: PR này đang được tiếp nhận xử lý bởi Agent trên môi trường [OS]. Vui lòng không can thiệp hoặc push đè lên nhánh `[branch]`.
     ```
3. **Rào Chắn Đẩy Mã Nguồn An Toàn (Pre-Push Lease Invariant):**
   - Tuyệt đối **NGHIÊM CẤM** sử dụng lệnh bare `git push --force` (`-f`) trên các nhánh PR.
   - Khi cần cập nhật nhánh sau rebase, **BẮT BUỘC** sử dụng:
     ```bash
     git fetch origin
     git push --force-with-lease origin <branch-name>
     ```
   - Lệnh này đảm bảo nếu có Agent khác vừa đẩy commit lên remote trong lúc bạn đang làm việc, lệnh push sẽ bị từ chối an toàn thay vì ghi đè làm mất mã nguồn của đồng đội.
4. **Giải Quyết Xung Đột Đồng Thời Trên PR (Post-Claim Verification for PRs):**
   - Sau khi claim PR, Agent đọc lại comments: `gh pr view <id> --json comments`.
   - Nếu có peer claim đăng trước, Agent lập tức hủy claim (`gh pr edit <id> --remove-assignee "@me"`).
5. **Cơ Chế Giải Phóng Khóa (Release / Takeover Protocol for PRs):**
   - **Tự động đóng khóa khi merge:** Khi PR được squash merge vào `main`, trạng thái khóa tự động kết thúc.
   - **Chủ động giải phóng khi dừng phiên:** Nếu Agent dừng phiên trước khi PR hoàn tất, bắt buộc đăng comment `<!-- CCBA_PR_CLAIM_RELEASE -->` và gỡ assignee: `gh pr edit <id> --remove-assignee "@me"`.
   - **Stale PR Claim Takeover (Ngưỡng 4 giờ):** Nếu một PR bị khóa nhưng nhánh không có commit mới sau **4 giờ**, Agent ở máy khác được phép kích hoạt Interactive Takeover để tiếp quản việc sửa PR.

---

## 14. Cross-Platform Machine-State Isolation & Environment Parity Invariant (Quy Chuẩn Cách Ly Trạng Thái Máy & Đồng Bộ Đa Nền Tảng)
- Nhằm đảm bảo mã nguồn và tài liệu vận hành trơn tru giữa máy Windows và Linux/WSL:
  1. **Ưu tiên biến môi trường `$CCBA_HUB_PATH`:** Mọi script phân giải vị trí Hub/Spoke bắt buộc phải kiểm tra biến môi trường `$CCBA_HUB_PATH` lên hàng đầu trước khi duyệt file system.
  2. **Bảo vệ đường dẫn ổ đĩa Windows trên POSIX:** Trên môi trường Linux/WSL/POSIX, tuyệt đối không truyền chuỗi đường dẫn mang ký tự ổ đĩa (`D:\...`, `C:\...`) trực tiếp vào `Path()`, phải sử dụng hàm phân giải đường dẫn an toàn (`resolve_cross_platform_path()`).
  3. **Chống rò rỉ trạng thái máy (Zero Machine-State Leakage):** Nghiêm cấm commit các đường dẫn máy cục bộ (`/home/...`, `D:/...`, `C:/...`). Kiểm định bắt buộc bằng lệnh `check_spoke_cleanliness.py`.
  4. **Chuẩn hóa Line Endings (LF Invariant):** Mọi repository thuộc hệ sinh thái CCBA bắt buộc có cấu hình `.gitattributes` chuẩn hóa (`* text=auto eol=lf`) để triệt tiêu xung đột CRLF/LF khi làm việc đa nền tảng.
  5. **Cổng Cưỡng Chế Sharded Registry (Hard Completion Gate):** Tại các Spoke tri thức quản lý văn bản pháp lý (có thư mục `legal_docs/`), lệnh kiểm tra tính toàn vẹn `ccba-legal compile-registry --check` (hoặc `validate_registry_sync()`) là điều kiện tiên quyết bắt buộc phải trả về `exit code 0`. Nếu có drift, Agent phải chạy compile trước khi commit.
  6. **Skills Hygiene Linting Rule:** Trong các tài liệu `SKILL.md`, các đoạn mã bash có chứa lệnh gán biến môi trường (`export VAR=...`) bắt buộc phải gắn nhãn ngôn ngữ chứa `linux` hoặc `ubuntu` (ví dụ ````bash (linux)````) để vượt qua bộ lọc chống Windows Bashism của `audit_skills_hygiene.py`.
