# CCBA Execution Guardrails & Async Task Policy

> **Tài liệu Tham chiếu Quy chuẩn Thực thi (Layer 2 — SSOT)**  
> Áp dụng cho toàn bộ các tác vụ lập trình, chạy kiểm thử, điều phối đa tác nhân và đồng bộ liên bang trên CCBA Platform.

## 🧭 Bảng Điều Hướng Nhanh Theo Miền (Quick Navigation Index)

| Miền Quản Trị (Domain) | Các Mục Quy Chuẩn (Sections) |
| :--- | :--- |
| **I. Thực Thi Kiểm Thử & Tiến Trình Ngầm (Runtime & Async)** | [1. Scoped Test](#1-scoped-test-execution-kiểm-thử-cô-lập) · [2. Bounded Async & Reactive Wakeup](#2-bounded-async-task-zero-polling--reactive-wakeup-invariant) · [3. TDD Retry Cap](#3-tdd-retry-cap--early-escalation-giới-hạn-vòng-lặp--điểm-cắt-lỗi) · [4. Anti-Duplicate Runner](#4-anti-duplicate-background-runner) · [5. Safe Process Termination](#5-safe-process-termination-invariant) · [6. Task Log Readiness](#6-task-log-readiness-check) · [7. Invalid Args Breaker](#7-invalid-args-circuit-breaker) · [8. 2-Tier Test Speed](#8-2-tier-test-speed-compliance) |
| **II. Điều Phối Đa Tác Nhân & Hooks (Multi-Agent & Hooks)** | [9. Boost Deep Reasoning](#9-boost-deep-reasoning-protocol--escalation-gate) · [10. Teamwork Orchestration](#10-teamwork-orchestration-protocol-quy-chuẩn-điều-phối-đa-tác-nhân-dài-hạn) · [11. Antigravity Lifecycle Hooks](#11-antigravity-lifecycle-hooks-policy-chính-sách-móc-vòng-đời-antigravity--adr-0054) |
| **III. GitHub CLI & Khóa Nhận Việc Đa Máy (GitHub & Claim Locking)** | [12. Safe GitHub CLI Input & Query](#12-safe-github-cli-input--query-parameterization-guardrails-quy-chuẩn-nhập-liệu--truy-vấn-an-toàn-cho-github-cli) · [13. Multi-Client Issue & PR Locking](#13-multi-client-issue--pull-request-coordination-protocol-quy-chuẩn-điều-phối-issue-và-pr-đa-máy--khóa-nhận-việc) |
| **IV. Đa Nền Tảng, CDP & Worktree (Cross-Platform, CDP & Worktree)** | [14. Cross-Platform Machine-State Isolation](#14-cross-platform-machine-state-isolation--environment-parity-invariant-quy-chuẩn-cách-ly-trạng-thái-máy--đồng-bộ-đa-nền-tảng) · [15. Chrome CDP Automation](#15-chrome-devtools-protocol-cdp--browser-agent-automation-invariant-quy-chuẩn-tự-động-hóa-trình-duyệt--bảo-mật-cdp) · [16. Ephemeral Worktree & Nightly Cron](#16-ephemeral-worktree--automated-nightly-cron-invariant-quy-chuẩn-vận-hành-worktree-tạm-thời) · [17. Spoke CLI Parameter Symmetry](#17-spoke-cli-parameter-symmetry--safe-invocation-invariant-quy-chuẩn-chữ-ký-tham-số--an-toàn-thực-thi-spoke-cli) |
| **V. Hợp Đồng Seam, Micro-PR & Ủy Quyền Ngang Hàng (Seams, PR & Peer)** | [18. Pre-Flight Seam Inventory (ADR-0061)](#18-pre-flight-seam-inventory--fast-path-policy-chính-sách-tiền-thẩm-định-kế-hoạch--miễn-trừ-nhanh) · [19. Atomic Micro-PR & Advisory AI Review](#19-atomic-micro-pr-pipeline--read-only-advisory-ai-review-guardrail-quy-chuẩn-pr-nguyên-tử--rào-chắn-ai-review-chỉ-đọc) · [20. Level-2 Peer Delegation (Grok ↔ Antigravity)](#20-level-2-peer-agent-delegation-protocol-grok--antigravity-cost-turn--liveness-guardrails---adr-00630065) |

---

## 1. Scoped Test Execution (Kiểm thử Cô lập)
- Nghiêm cấm kích hoạt kiểm thử toàn diện không khoanh vùng (unscoped `pytest`) trên toàn bộ repository.
- Luôn chỉ định rõ file test hoặc module mục tiêu (`pytest packages/{pkg}/tests/test_file.py`) kèm `WaitMsBeforeAsync=10000` (10s) để lệnh hoàn tất đồng bộ ngay trong lượt gọi đầu tiên, hoặc dùng cờ loại trừ `-m "not slow and not stress"`.

---

## 2. Bounded Async Task, Zero-Polling & Reactive Wakeup Invariant
- Khi một lệnh chuyển sang chạy ngầm (Background Task) như `pytest`, `peer-dispatch`, hoặc `gh pr checks --watch`:
  - **Nguyên lý Reactive Wakeup (Bắt buộc):** Runtime tự động đánh thức và gửi `<SYSTEM_MESSAGE>` ngay khi tác vụ nền hoàn thành.
  - **Chính sách Không Polling Tuyệt Đối (Zero-Tolerance Polling Policy):**
    - Nghiêm cấm lặp `manage_task status` để thăm dò trạng thái tiến trình nền.
    - **Hành động bắt buộc ngay sau khi lệnh chuyển sang Background Task:**
      1. **Dừng gọi công cụ (End Turn):** Thông báo ngắn gọn cho người dùng và kết thúc lượt ngay để hệ thống tự động đánh thức khi hoàn tất; **hoặc**
      2. **Làm việc song song có ích (Parallel Work):** Soạn thảo tài liệu hoặc phân tích mã nguồn độc lập khác trong lúc chờ.
  - **Rào chắn theo dõi CI & Copilot Review (`gh pr checks`):** Khởi chạy `gh pr checks <id> --watch` rồi dừng lượt chờ Reactive Wakeup. Nghiêm cấm chạy `gh pr merge` khi `gh pr view <id> --json reviewRequests` vẫn còn `copilot-pull-request-reviewer`.

---

## 3. TDD Retry Cap & Early Escalation (Giới Hạn Vòng Lặp & Điểm Cắt Lỗi)
- Trong vòng lặp Red $\rightarrow$ Green $\rightarrow$ Refactor, chỉ được thử tối đa **5 vòng** cho cùng một seam hoặc test file:
  - **Cắt lỗi sớm tại vòng 3 (Early Escalation):** Nếu sau 3 vòng liên tiếp vẫn lỗi do logic sâu hoặc race condition, dừng đoán mò và đóng gói **Deep Problem Brief** (Mục 9).
  - **Dừng cứng tại vòng 5 (Hard Stop):** Commit WIP, xuất Deep Problem Brief và kích hoạt **Boost Escalation Gate** (Mục 9) — tuyệt đối không lặp tiếp làm cạn ngân sách ngữ cảnh.

---

## 4. Anti-Duplicate Background Runner
- Nghiêm cấm kích hoạt nhiều lệnh chạy ngầm (`run_command` async) cho cùng một script test runner hoặc harness evaluation.
- Mọi script runner ngầm bắt buộc tích hợp khóa đơn tiến trình (`ensure_single_instance`) và kiểm tra tiến trình cũ trước khi khởi động.

---

## 5. Safe Process Termination Invariant
- Khi viết hoặc thực thi logic dọn dẹp tiến trình (`ensure_single_instance`), **bắt buộc loại trừ** cả tiến trình hiện tại (`os.getpid`) và tiến trình cha (`os.getppid`).
- Nghiêm cấm gọi `taskkill` hoặc `proc.terminate` lên `os.getppid` để tránh làm sập Agent Server Host.

---

## 6. Task Log Readiness Check
- Nghiêm cấm gọi `view_file` tới `task-XXX.log` ngay sau lượt `run_command` async khi chưa nhận được thông báo hoàn tất từ hệ thống hoặc kiểm tra trạng thái qua `manage_task status`.

---

## 7. Invalid Args Circuit Breaker
- Khi gặp lỗi `model output error: invalid tool call error (invalid_args)` từ **2 lần liên tiếp trở lên** (dấu hiệu cạn kiệt context budget), Agent phải **dừng ngay lập tức**, commit WIP, tóm tắt trạng thái và đề nghị người dùng mở phiên mới (hoặc dùng `/compact`).

---

## 8. 2-Tier Test Speed Compliance
- Mọi Unit Test mới bắt buộc chạy dưới **2.0 giây**.
- Các bài test tích hợp mạng, Chromium CDP, hoặc LLM thực tế bắt buộc gắn decorator `@pytest.mark.slow` hoặc `@pytest.mark.stress` để loại trừ khỏi vòng kiểm thử nhanh (`-m "not slow"`).

---

## 9. Boost Deep Reasoning Protocol & Escalation Gate
- Kích hoạt **Boost Deep Reasoning** (`/boost`) khi gặp: (1) Concurrency & Race Conditions; (2) Polyglot Monorepo Deep Refactoring đa package; (3) Thẩm định Pháp lý & Xung đột Quy chuẩn đa ngành (Luật Xây dựng `135/2025/QH15`, NĐ `217/2026/NĐ-CP`, Luật PCCC `55/2024/QH15`, NĐ `105/2025/NĐ-CP`, QCVN 06, TCVN 3890); hoặc (4) Chạm ngưỡng TDD Retry Cap (Mục 3).
- **Mẫu Deep Problem Brief:**
  ```markdown
  ### 🔬 Deep Problem Brief
  - **Vấn đề cốt lõi (Failure Manifest):** [Mô tả ngắn gọn lỗi kỹ thuật/test fail]
  - **Các giả thuyết đã kiểm chứng & Thất bại (Tested Hypotheses):** [2-3 cách sửa đã thử và lý do fail]
  - **Vùng ảnh hưởng (Seams Involved):** [Danh sách files / classes / functions liên quan]
  - **Logs / Error Trace:** [Trích đoạn log lỗi then chốt]
  - **Khuyến nghị hành động:** [Đề xuất kích hoạt `/boost` kèm brief này]
  ```
- **Rào chắn An Toàn Đa Tác Nhân (Two-Layer Sub-Agent Guardrail — ADR-0035):**
  1. **Depth Limit = 1:** Cấm subagent tự khởi tạo thêm subagent con.
  2. **Tool Scoping:** Subagents chỉ có quyền đọc (`view_file`, `grep_search`) và chạy test cô lập; cấm sửa file hoặc chạy lệnh Git đột biến.
  3. **Max Workers = 3:** Tối đa 3 subagents chạy song song trong một phiên điều tra.

---

## 10. Teamwork Orchestration Protocol (Quy Chuẩn Điều Phối Đa Tác Nhân Dài Hạn)
- Khi triển khai dự án lớn đa seams (ADR-0053), áp dụng mô hình **3 Vai Trò Tối Giản**:
  1. **Orchestrator (Nhạc Trưởng):** Lập `team_sheet.md`, điều phối workers, tổng hợp kết quả, và là **tác nhân duy nhất có quyền ghi codebase / commit Git** (Single-Writer Invariant).
  2. **Workers (Tác Nhân Thực Thi):** Tối đa **3 workers/batch** chạy song song (tuân thủ ADR-0035, thời hạn tối đa **10 phút/worker**), xuất kết quả nháp vào `.system_generated/scratch/worker_{N}/`.
  3. **Success Auditor (Kiểm Định Nghiệm Thu):** Chạy kiểm thử cô lập, quét Maskara, và đối chiếu `git diff --name-only` với phạm vi khai báo trong `team_sheet.md` (chống Seam Boundary Leakage).
- **Cơ chế Khôi phục & Phân định Ranh giới:**
  - Nếu worker quá hạn hoặc suy thoái ngữ cảnh, Orchestrator đánh dấu milestone là `"INCOMPLETE"` và khởi động lại với phạm vi thu hẹp hoặc kích hoạt `/boost` (Escalation UP cho bế tắc sâu đơn lẻ) trước khi tiếp tục `/ccba-teamwork` (Coordination OUT cho đa luồng công việc).

---

## 11. Antigravity Lifecycle Hooks Policy (Chính Sách Móc Vòng Đời Antigravity) — ADR 0054
- File `scripts/hooks/antigravity_hook_bridge.py` đóng vai trò **Adapter Layer mỏng** dịch schema giữa Antigravity IDE (`toolCall.name` / `toolCall.args` camelCase) và `HookCoordinator` (snake_case, cùng chia sẻ 7 hooks với CLI `hook_runner.py`).
- Chỉ kích hoạt ở bước `"PreToolUse"` trên matcher `run_command|write_to_file|replace_file_content|multi_replace_file_content`.
- **Fail-Safe Default:** Mọi ngoại lệ không mong muốn trong bridge đều trả về `{"decision": "allow"}` để không làm gián đoạn IDE.

---

## 12. Safe GitHub CLI Input & Query Parameterization Guardrails (Quy Chuẩn Nhập Liệu & Truy Vấn An Toàn cho GitHub CLI)

### 12.1. Safe File-Based Input Invariant for Mutations (`-F` / `--body-file`)
- Khi gọi `gh issue comment`, `gh issue create`, `gh pr create`, `gh pr comment` có nội dung nhiều dòng hoặc Markdown:
  - **Nghiêm cấm:** Truyền chuỗi trực tiếp qua `--body "..."` (dễ lỗi shell expansion/backticks).
  - **Bắt buộc:** Ghi vào tệp tạm (hoặc truyền qua `--body-file - << 'EOF'` với single-quoted heredoc) rồi gọi `-F` / `--body-file`:
    ```bash
    gh issue comment <issue_id> -F .md/scratch/comment_<issue_id>.md
    gh pr create --title "..." -F .md/scratch/pr_body.md
    ```

### 12.2. Safe JSON Parameterization for Queries (`gh issue/pr view --json`)
- **GraphQL Deprecation Invariant (`RULE-5.11`):** Tuyệt đối không gọi `gh issue view <id>` hoặc `gh pr view <id>` thiếu cờ `--json` (do GitHub đã gỡ `projectCards` của Projects Classic gây lỗi GraphQL Exit Code 1):
  ```bash
  gh issue view <id> --json number,title,state,assignees,labels,body,comments
  gh pr view <id> --json number,title,state,headRefName,baseRefName,mergeable,reviewRequests
  ```

---

## 13. Multi-Client Issue & Pull Request Coordination Protocol (Quy Chuẩn Điều Phối Issue và PR Đa Máy & Khóa Nhận Việc)

### A. Khóa Nhận Việc Cho GitHub Issues (Issue Claim Locking — TTL 24h)
1. **Chuyển trạng thái & Gán nhãn:** Kiểm tra nhãn qua `gh issue view <id> --json labels`, sau đó gán `in-progress` và `@me`:
   ```bash
   gh issue edit <id> --add-label "in-progress" --add-assignee "@me"
   ```
2. **Đăng Claim Notice máy-đọc-được (qua `-F`):**
   ```markdown
   <!-- CCBA_PEER_CLAIM_LOCK
   host: [linux-workstation / windows-pc / wsl]
   branch: feat/issue-[id]-[short-desc]
   claimed_at: [ISO-8601-UTC-Timestamp]
   ttl_hours: 24
   -->
   🤖 **Agent Claim & Coordination Notice**: Issue này đang được xử lý trên môi trường [OS]. Vui lòng không claim trùng lặp.
   ```
3. **Chống đua đồng thời (Post-Claim Verification):** Đọc lại `gh issue view <id> --json comments`; nếu có Claim Notice của peer khác đăng trước, bắt buộc nhượng bộ (`--remove-label "in-progress"`).
4. **Takeover Stale Claims (> 24h không có commit mới):** Hỏi xác nhận người dùng khi chạy tương tác, hoặc tự động bỏ qua khi chạy ngầm (headless/daemon).
5. **Đóng Issue khi hoàn tất:** Sau khi squash-merge PR vào `main`, đăng comment nghiệm thu kèm PR/Commit SHA và đóng issue (`gh issue close <id> --reason "completed"`).

### B. Khóa Tranh Chấp Cho Pull Requests (PR Claim Locking & Lease Push — TTL 4h)
1. **Khóa PR & Đăng Notice (TTL = 4h):** Chạy `gh pr edit <id> --add-assignee "@me" --add-label "in-progress"` và đăng block `<!-- CCBA_PR_CLAIM_LOCK ... ttl_hours: 4 -->` qua `-F`. Khi dừng phiên sớm, đăng `<!-- CCBA_PR_CLAIM_RELEASE -->` và gỡ `@me`.
2. **Pre-Push Lease Invariant:** Nghiêm cấm dùng bare `git push --force` (`-f`). Bắt buộc dùng:
   ```bash
   git fetch origin
   git push --force-with-lease origin <branch-name>
   ```
3. **Zero-Red-Merge Invariant:** Nghiêm cấm dùng `--admin` hoặc `--auto`. Chỉ chạy `gh pr merge <id> --squash --delete-branch` sau khi 100% checks báo xanh và `reviewRequests` rỗng.

---

## 14. Cross-Platform Machine-State Isolation & Environment Parity Invariant (Quy Chuẩn Cách Ly Trạng Thái Máy & Đồng Bộ Đa Nền Tảng)
1. **Ưu tiên `$CCBA_HUB_PATH`:** Mọi script phân giải vị trí Hub/Spoke phải ưu tiên đọc biến môi trường `$CCBA_HUB_PATH`.
2. **An toàn đường dẫn đa hệ điều hành:** Trên Linux/WSL/POSIX, không truyền trực tiếp chuỗi ổ đĩa Windows (`D:\...`, `C:\...`) vào `pathlib.Path`; bắt buộc dùng `resolve_cross_platform_path`.
3. **Chống rò rỉ trạng thái máy (ADR-0061):** Cấm commit đường dẫn tuyệt đối cục bộ (`/home/...`, `C:/...`) hoặc IP cứng; kiểm định qua `check_spoke_cleanliness.py`.
4. **Chuẩn hóa LF & Ngân sách In-Memory:** Mọi repo phải có `.gitattributes` (`* text=auto eol=lf`). Ngưỡng dung lượng tài liệu (như 10.0 KB của `session_learnings.md`) phải tính sau khi chuẩn hóa `content.replace("\r\n", "\n").encode("utf-8")`.
5. **Sharded Legal Registry Gate:** Tại các Spoke có `legal_docs/`, lệnh `ccba-legal compile-registry --check` bắt buộc trả về exit code 0 trước khi commit.
6. **Skills Hygiene Bash Labeling:** Các khối bash trong `SKILL.md` có lệnh `export` phải ghi nhãn ````bash (linux)````.

---

## 15. Chrome DevTools Protocol (CDP) & Browser Agent Automation Invariant (Quy Chuẩn Tự Động Hóa Trình Duyệt & Bảo Mật CDP)
- **Bắt buộc `--remote-allow-origins=*` & Khóa Loopback `127.0.0.1`:** Mọi lệnh mở Chrome Debug trên cổng `9222` (SSOT duy nhất) phải kèm `--remote-allow-origins=*` và chỉ lắng nghe trên `127.0.0.1` (cấm `0.0.0.0`).
- **Attach-First & Profile Dùng Chung:** Dùng chung profile bền vững `~/.gemini/antigravity-browser-profile`; tự động dọn `~/.gemini/antigravity-browser-profile/LOCK` bị treo nếu cổng `9222` trống.
- **Dừng An Toàn Chọn Lọc:** Chỉ tắt tiến trình gắn với cổng `9222` hoặc `antigravity-browser-profile`; nghiêm cấm `taskkill /IM chrome.exe /F` hàng loạt.

---

## 16. Ephemeral Worktree & Automated Nightly Cron Invariant (Quy Chuẩn Vận Hành Worktree Tạm Thời)
- **Cách ly Worktree & Chống rò rỉ đường dẫn import:** Mọi tác vụ auto-tuner/telemetry tự động phải chạy trong detached worktree (`.worktrees/` đã khai báo trong `.gitignore`) và đặt lại đường dẫn tìm kiếm gói Python ưu tiên trỏ vào worktree trước khi chạy test:
  ```bash (linux)
  export PYTHONPATH="$worktree_dir/packages/ccba-harness/src:$worktree_dir/packages/ccba-ai/src:$worktree_dir"
  ```
- **Fast-Forward Guard & Dynamic Branching:** Dùng hậu tố nhánh động `docs/auto-refactor-YYYYMMDD_HHMMSS`. Không chép ngược untracked files vào workspace chính; chỉ `git merge --ff-only origin/main` khi working tree chính hoàn toàn sạch.
- **Kiểm tra tiến trình trước khi xóa Worktree (`Active Lock Protection`):** Trước khi `git worktree remove` hoặc xóa lock file, bắt buộc kiểm tra bằng `fuser -v "$worktree_dir"` và `flock -n "$lock_file" -c "true"`; cấm xóa khi tiến trình đang hoạt động.

---

## 17. Spoke CLI Parameter Symmetry & Safe Invocation Invariant (Quy Chuẩn Chữ Ký Tham Số & An Toàn Thực Thi Spoke CLI)
1. **Bộ Script Độc Lập (`scripts/`):**
   - `python scripts/sync_spoke.py --spoke <path> [--apply]`: Mặc định chạy xem trước (Preview); bắt buộc truyền `--apply` để ghi đĩa.
   - `python scripts/adopt_spoke.py --spoke <path> [--dry-run]`: Mặc định áp dụng trực tiếp; truyền `--dry-run` để xem trước (cấm truyền `--apply`).
   - `python scripts/init_spoke.py <spoke_path>` (hoặc `-p <spoke_path>`): Nhận tham số vị trí (cấm truyền `--spoke`).
2. **CLI Hợp Nhất (`scripts/ccba_platform_cli.py`):** Cả 3 lệnh `init-spoke`, `adopt-spoke`, `sync-spoke` đều nhận `<spoke_path>` là **tham số vị trí** (cấm truyền `--spoke`).

---

## 18. Pre-Flight Seam Inventory & Fast-Path Policy (Chính Sách Tiền Thẩm Định Kế Hoạch & Miễn Trừ Nhanh)

### 18.1. Tra Cứu Hợp Đồng Năng Lực Seam & Biên Lai Kiểm Toán (`ADR-0061`)
Trước khi đề xuất giải pháp kỹ thuật hoặc viết script/utility mới trong `implementation_plan.md`, Agent **BẮT BUỘC** tra cứu Seam Capability Contracts theo kiểu đầu vào/đầu ra:
```bash
ccba-platform find-seam --in <input_types> --out <output_types> [--hardware <hw>] --json
# Hoặc:
python scripts/governance/compile_catalog.py --in <input_types> --out <output_types> --json
```
- **Audit Receipt Invariant (`index_sha256`):** Bắt buộc dán biên lai JSON (có trường `index_sha256`) vào `implementation_plan.md`.
- **Cấm ngụy biện bằng Keyword Search:** Tra cứu theo từ khóa vị trí (`--query "<kw>"`) chỉ trả về `"KEYWORD_HINT"` và **không được coi là biên lai hợp đồng**. Nếu nền tảng đã có Seam khớp $\rightarrow$ bắt buộc tái sử dụng (`from ccba_<pkg> import <Seam>`). Mọi ngoại lệ thư viện thứ ba phải qua `# ccba:quarantine seam_id=... reason=... until=YYYY-MM-DD issue=...`.

### 18.2. Ngưỡng Kích Hoạt Bắt Buộc & Fast-Path Miễn Trừ
- **Bắt buộc có Audit Receipt** đối với: (1) File I/O & chuyển đổi tài liệu; (2) Security & Secrets (`ccba-maskara`); (3) Networking, Crawl & Cloud Sync; (4) Tạo tệp `.py` mới trong `scripts/` hoặc `packages/`; (5) Thẩm định pháp lý & QC thiết kế.
- **Miễn trừ Fast-Path** (không cần dán biên lai CLI) đối với: (1) Bugfix cục bộ trong 1 hàm/1 file hiện hữu không thêm dependency; (2) Cập nhật test fixtures/eval cases; (3) Sửa tài liệu Markdown thuần túy.

---

## 19. Atomic Micro-PR Pipeline & Read-Only Advisory AI Review Guardrail (Quy Chuẩn PR Nguyên Tử & Rào Chắn AI Review Chỉ Đọc)

### 19.1. Giới Hạn Kích Thước PR Nguyên Tử & Phân Loại Cửa Một Chiều (`ADR-0067`)
- Mọi Pull Request mã nguồn logic nghiệp vụ phải khống chế trong ngân sách **$\le 200$ LOC diff** (không tính tests và `.md`) và tác động tối đa **1 Public Deep Seam** mỗi PR.
- Các PR chạm vào 7 danh mục Cửa Một Chiều (`door_policy.py`) hoặc vượt chuỗi tích lũy $K \ge 3$ PRs `"PAVED_ROAD"` trong 72h trên cùng `packages/<pkg>` bắt buộc đính kèm **Tradeoff Card** (`Core Invariant`, `Invalidation Condition`, `Git Hunk Reference` $\le 30$ dòng) được kiểm định tự động qua `ccba-harness door-triage` (`backpressure.py`).

### 19.2. Rào Chắn AI Review Chỉ Đọc & 10 Invariants Kiểm Tra Tự Động (`.github/bugbot-rules.md`)
- Các AI Reviewers tự động (Bugbot, Copilot Reviewer) chỉ vận hành ở chế độ **Chỉ Đọc & Tư Vấn (Read-Only Advisory)** — nghiêm cấm tự động gửi trạng thái `"APPROVE"` hoặc auto-merge mã nguồn.
- Toàn bộ 10 quy tắc kiểm tra tự động (từ Invariant #1 Seam Reuse đến Invariant #10 Atomic Micro-PR) được định nghĩa đầy đủ tại SSOT [`.github/bugbot-rules.md`](../../.github/bugbot-rules.md).
- **Chống bão Quota:** AI Review trên PR chỉ kích hoạt opt-in qua nhãn `ai-review-requested` hoặc lệnh `/ccba-ai-review` (bỏ qua PR của bots) sau khi đã lọc qua `redact_secrets_in_text`.

---

## 20. Level-2 Peer Agent Delegation Protocol (Grok ↔ Antigravity Cost, Turn & Liveness Guardrails - ADR-0063..0065)

### 20.1. Ma Trận 8 Execution Profiles & Trần Vòng Lặp Bắt Buộc (`peer.PROFILE_SPECS`)
Mọi lệnh gọi Grok CLI bắt buộc đi qua Seam `invoke_grok_cli` hoặc CLI `ccba-harness peer-dispatch` với `--verbatim --disable-web-search` theo 8 profiles chuẩn hóa:
1. **`deep_spec_audit` (Stage 1 Pre-Code Deep Audit):** $\le 25$ turns, `reasoning_effort: xhigh`, `output_format: json`, `timeout: 900s`, chỉ đọc (`read_file`, `grep`, `list_dir`).
2. **`audit_plan`:** $\le 12$ turns, `reasoning_effort: xhigh`, `timeout: 900s`, chỉ đọc.
3. **`signoff_diff` (Stage 3 Post-Code Sign-off):** $\le 15$ turns, `reasoning_effort: high`, `output_format: json`, `fork_session: True`, `timeout: 600s`; hỗ trợ `--resume <session_id> --fork-session` kế thừa KV-Cache từ Stage 1 (hoặc kèm `--no-tools` khi đã nhúng đủ diff).
4. **`arch_audit`:** $\le 8$ turns, `reasoning_effort: xhigh`, `timeout: 600s`, chỉ đọc.
5. **`code_review`:** $\le 10$ turns, `reasoning_effort: high`, `timeout: 300s`, chỉ đọc.
6. **`audit_direct`:** $\le 3$ turns, `reasoning_effort: high`, `timeout: 120s`, khóa toàn bộ 15 built-in tools (`--deny "*"`).
7. **`agentic_code`:** $\le 8$ turns, `reasoning_effort: high`, `timeout: 600s`, cho phép `read_file`, `search_replace`, `list_dir`.
8. **`patch_fast`:** Đúng **1 turn** (`--max-turns 1`), `timeout: 120s`, khóa toàn bộ 15 built-in tools (`--deny "*"`), sinh bản ghi neo để `apply_anchor_patch` áp dụng (xác thực SHA-256 trước khi ghi).

### 20.2. Liveness-Aware Watchdog, Telemetry Đa Lượt & Rào Chắn Suy Thoái Suy Luận (`RULE-4.19`)
- **Liveness-Aware Watchdog (`inspect_session_liveness`):** Giám sát `~/.grok/sessions/**/<session_id>/events.jsonl`:
  - *Fail-Fast:* Ngắt ngay khi gặp `turn_ended:error`, `turn_ended:cancelled`, hoặc kẹt tại `mcp_init_completed:` quá `90.0s` (cấm ngắt ở `phase_changed:waiting_for_model`).
  - *Turn-Ended Drain & Grace Window:* Đọc `temp_out` trước khi thu hồi process group (`_terminate_proc_tree`) khi treo sau `turn_ended:*` quá `5.0s`; cấp 1 lần gia hạn `+45.0s` khi đang streaming (`age_s < 5.0s`); cứu hộ phán quyết từ `chat_history.jsonl` qua `_recover_verdict_from_chat_history` khi chạm `max_turns`.
- **Multi-Turn Telemetry & Degraded-Reasoning Gate:** Khi dùng `--resume`, `extract_grok_session_telemetry` ưu tiên lấy số liệu lượt cuối (`turns[-1]`). Nếu profile `high`/`xhigh` trả về `reasoning_tokens == 0`, `synthesize_verdicts` tự động chèn điều kiện chặn `COND-DEGRADED-REASONING` (`blocking=True`), hạ đồng thuận từ `"APPROVE"` xuống `"APPROVE_WITH_CONDITIONS"`.
- **Định tuyến 3 Tầng (Multi-Tier Routing):** Tier 1 `local` (`qwen-local` — `$0.00` cho `patch_fast`), Tier 2 `gateway` (`gemini-38-flash` / `claude-sonnet-4-6`), Tier 3 `cloud` (`grok-4.7` cho thẩm định kiến trúc & nghiệm thu).
