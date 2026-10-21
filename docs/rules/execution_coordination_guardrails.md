# CCBA Execution Coordination Guardrails & Multi-Agent Protocol

> **Tài liệu Tham chiếu Quy chuẩn Điều phối Đa Tác nhân & Remote (Layer 2 — SSOT)**  
> Áp dụng cho các tác vụ phối hợp đa máy, khóa claim, PR pipeline, reasoning escalation và giao thức ủy quyền ngang hàng trên CCBA Platform.  
> Đối với quy chuẩn thực thi cục bộ, kiểm thử và quản trị tiến trình nền, xem [`docs/rules/execution_runtime_guardrails.md`](execution_runtime_guardrails.md).

## 🧭 Bảng Điều Hướng Nhanh (Coordination Navigation Index)

| Nhóm Quy Chuẩn (Category) | Các Mục Quy Chuẩn (Sections) |
| :--- | :--- |
| **I. Tác Nhân & Điều Phối** | [9. Boost Deep Reasoning Protocol](#9-boost-deep-reasoning-protocol--escalation-gate) · [10. Teamwork Orchestration Protocol](#10-teamwork-orchestration-protocol-quy-chuẩn-điều-phối-đa-tác-nhân-dài-hạn) |
| **II. GitHub & Khóa Claim Đa Máy** | [12. Safe GitHub CLI Input & Query](#12-safe-github-cli-input--query-parameterization-guardrails-quy-chuẩn-nhập-liệu--truy-vấn-an-toàn-cho-github-cli) · [13. Multi-Client Issue & PR Coordination](#13-multi-client-issue--pull-request-coordination-protocol-quy-chuẩn-điều-phối-issue-và-pr-đa-máy--khóa-nhận-việc) |
| **III. Hợp Đồng Seam, PR & Giao Thức Peer** | [18. Pre-Flight Seam Inventory (ADR-0061)](#18-pre-flight-seam-inventory--fast-path-policy-chính-sách-tiền-thẩm-định-kế-hoạch--miễn-trừ-nhanh) · [19. Atomic Micro-PR Pipeline & AI Review](#19-atomic-micro-pr-pipeline--read-only-advisory-ai-review-guardrail-quy-chuẩn-pr-nguyên-tử--rào-chắn-ai-review-chỉ-đọc) · [20. Level-2 Peer Agent Delegation](#20-level-2-peer-agent-delegation-protocol-grok--antigravity-cost-turn--liveness-guardrails---adr-00630065) |
| **IV. Thực Thi Cục Bộ & Runtime** | Xem tài liệu bổ trợ: [`execution_runtime_guardrails.md`](execution_runtime_guardrails.md) (Mục 1–8, 11, 14, 15, 16, 17) |

---

## 9. Boost Deep Reasoning Protocol & Escalation Gate
- Kích hoạt **Boost Deep Reasoning** (`/boost`) khi gặp: (1) Concurrency & Race Conditions; (2) Polyglot Monorepo Deep Refactoring đa package; (3) Thẩm định Pháp lý & Xung đột Quy chuẩn đa ngành (Luật Xây dựng `135/2025/QH15`, NĐ `217/2026/NĐ-CP`, Luật PCCC `55/2024/QH15`, NĐ `105/2025/NĐ-CP`, QCVN 06, TCVN 3890); hoặc (4) Chạm ngưỡng TDD Retry Cap (Mục 3 `execution_runtime_guardrails.md`).
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
