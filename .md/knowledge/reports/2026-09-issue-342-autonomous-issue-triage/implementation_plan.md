# Kế Hoạch Triển Khai: Nâng Cấp `/ccba-new-feature` — Factory Model v1.3.0 (Issue #342)

> **Mục tiêu:** Nâng cấp kỹ năng `/ccba-new-feature` lên phiên bản `1.3.0` với cơ chế **Autonomous Remote Backlog Discovery & Smart Claiming**, giúp Agent tự động phát hiện backlog mở trên GitHub remote, xếp hạng ưu tiên theo trọng số kỹ thuật, tương tác đề xuất thông minh cho kỹ sư qua `ask_question`, xử lý an toàn race condition theo Multi-Client Peer Claim Lock và tương thích hoàn toàn với các quy chuẩn kiểm định tự động (ADR-0057, ADR-0058).

---

## CCBA Charter Governance & QC Matrix (ADR-0058)

- **Môi trường:** Hub Monorepo (`ccba-agent-platform`)
- **QC Level áp dụng:** Level 2 (Technical & Architecture Parity)
- **Ghế chịu trách nhiệm phê duyệt:** `TRUONG_PHONG_RD_HTQT` (hoặc Lead Technical Architect)
- **Tiêu chuẩn nghiệm thu:** 
  1. 100% các lệnh trong `Verification Plan` trả về Exit Code 0 trên môi trường máy chủ Linux (`.venv/bin/python`).
  2. Báo cáo nghiệm thu `walkthrough.md` nhúng nguyên văn bảng kết quả thực thi từ `verify-patch`.
  3. Snapshot kế hoạch và walkthrough lưu trữ vĩnh viễn vào `.md/knowledge/reports/2026-09-issue-342-autonomous-issue-triage/` trước khi đóng phiên.

---

## User Review Required

> [!IMPORTANT]
> Bản kế hoạch nâng cấp `/ccba-new-feature` lên v1.3.0 đã được thẩm tra phản biện 2 vòng chuyên sâu qua `/boost` (DeepInvestigator), giải quyết triệt để 5 rủi ro kỹ thuật:
> 1. Tránh gãy linter `SkillValidator` do tiêu đề phụ (`STEP_LINE_RE`).
> 2. Tránh lỗi Git Exit 128 tại Bước 5 khi checkout nhánh đã tồn tại (`git show-ref`).
> 3. Sửa lỗi logic Yield Protocol trong Guardrail 13 (agent thua cuộc không gỡ nhãn `in-progress` của agent thắng).
> 4. Rào chắn Prompt Injection & Shell Injection từ dữ liệu Issue tiêu đề/thân bài.
> 5. Hỗ trợ Local Markdown Tracker đệ quy trên Spoke `.md/knowledge/issues/**/issues/*.md`.

---

## 1. Đánh Giá Khả Năng Tái Sử Dụng (Reuse Assessment — ADR 0047 / ADR 0032)

- **Tra cứu Catalog (`catalog.yaml`)**:
  - Kỹ năng `/ccba-new-feature` là một Composite Orchestrator thuộc bundle `_core`, tier `orchestrator`, `disable-model-invocation: true`.
  - Các công cụ CLI tương tác GitHub (`gh issue list`, `gh issue view`, `gh issue edit`, `gh issue comment`) đã được chuẩn hóa trong `docs/rules/execution_guardrails.md` (Mục 12 & 13) và các kỹ năng đối xứng `/ccba-issue-to-hub`, `/ccba-contribute-to-hub`.
  - Công cụ tương tác người dùng `ask_question` là native UI tool của Antigravity IDE, hỗ trợ sẵn định dạng `(Recommended)` và write-in task.
- **Quyết định Tái sử dụng**:
  - **Tái sử dụng 100%**: Sử dụng chuẩn lệnh GitHub CLI `gh issue list --state open --limit 10 --json ...` và quy chuẩn Machine-Parseable Claim Notice của Execution Guardrails.
  - Không tạo thêm package hoặc script cồng kềnh mới ngoài phạm vi orchestrator (tuân thủ nguyên tắc KISS).

---

## 2. Double-Pass Adversarial Audit Findings (`/boost` Deep Investigation)

### Vòng 1 — Code-First Research
- **Hiện trạng Bước 3**: Kỹ năng v1.2.0 chia làm 2 trường hợp:
  - Trường hợp 1: Có mã Issue $\rightarrow$ Dùng `gh issue view` hoặc fallback `.md/knowledge/issues/issue-<id>.md`.
  - Trường hợp 2: Không có mã Issue $\rightarrow$ Ngay lập tức hỏi phỏng vấn thủ công ("Loại công việc là gì?", "Mô tả tính năng là gì?"), bỏ qua toàn bộ Open Issues đang có sẵn trên repo remote.
- **Lệnh GitHub CLI**:
  - `gh issue view` bắt buộc phải kèm cờ `--json` để tránh lỗi GraphQL API sunset classic projects (`repository.issue.projectCards`).
  - Lệnh `gh issue list --state open --limit 10 --json number,title,labels,assignees,updatedAt` hoạt động ổn định và trả về đầy đủ metadata để lọc.
- **Cú pháp Linter `SkillValidator`**:
  - `SkillValidator.analyze_steps_completion_criteria` sử dụng regex `STEP_LINE_RE` bắt các tiêu đề bắt đầu bằng `Bước`, `Step`, hoặc `Pha`. Do đó, các tiêu đề phụ trong Bước 3 BẮT BUỘC dùng định dạng `#### 3.1. ...` (không chứa từ khóa `Pha`) để tránh lỗi CI thiếu Tiêu chí hoàn thành.

### Vòng 2 — Self-Adversarial Review & Edge Cases
- **Edge Case 1: Nhánh tính năng đã tồn tại tại Bước 5 (`git checkout -b` crash)**:
  - Khi kỹ sư tiếp tục làm một Issue của chính mình (`[Đang xử lý bởi bạn]`) hoặc tiếp quản Stale Claim (> 24h), nhánh `feat/issue-XXX-...` thường đã tồn tại cục bộ hoặc remote. Lệnh `git checkout -b` sẽ văng lỗi fatal exit code 128. Cần logic kiểm tra đa nhánh qua `git show-ref`.
- **Edge Case 2: Xung đột nhận việc (Race Condition) và Lỗi Logic Rollback**:
  - Nếu Agent B thua cuộc đua nhận việc với Agent A, Agent B tuyệt đối KHÔNG được gỡ nhãn `in-progress` (vì sẽ làm mất khóa của Agent A). Agent B chỉ gỡ `--remove-assignee "@me"` (nếu đã gán) và nhượng bộ (yield).
- **Edge Case 3: Shell Injection & Prompt Injection từ Issue**:
  - Tiêu đề issue có thể chứa ký tự đặc biệt (`"`, `;`, `$()`). Tên branch bắt buộc phải qua bộ lọc sanitize slug nghiêm ngặt (chỉ giữ `[a-z0-9\-]`, tối đa 40 ký tự).
  - Nội dung Issue trích xuất từ remote phải được gắn cờ `Untrusted Data Block` trong prompt và implementation plan, không coi là chỉ dẫn hệ thống.
- **Edge Case 4: Backlog Offline trên Spoke**:
  - Trên các Spoke dùng Local Markdown Tracker, issues được lưu tại `.md/knowledge/issues/<feature>/issues/<NN>-<slug>.md`. Cơ chế Local Discovery phải quét đệ quy cả `issue-*.md` và `**/issues/*.md`, chỉ lọc các issue có `state: open/needs-triage/ready-for-agent`.

---

## 3. Chi Tiết Các Thay Đổi (Proposed Changes)

### Target 1: `.agents/skills/ccba-new-feature/SKILL.md`
- **Bump metadata version**: Từ `"1.2.0"` lên `"1.3.0"`. Thêm triggers: `triage`, `backlog`, `claim issue`.
- **Cấu trúc lại Bước 3 (Thu thập thông tin & Bóc tách Issue tự động)**:
  - **Trường hợp 1 (Có mã Issue)**: Giữ nguyên luồng bóc tách nhanh qua `gh issue view <id> --json title,body,labels`.
  - **Trường hợp 2 (Không cung cấp mã Issue — Autonomous Remote Backlog Discovery & Smart Claiming)**:
    - **3.1. Quét Backlog từ Remote (`gh issue list`)**:
      ```bash
      gh issue list --state open --limit 10 --json number,title,labels,assignees,updatedAt
      ```
      Tự động phân nhóm issues:
      * Nhóm Khả dụng: Chưa có assignee và không có nhãn `in-progress`.
      * Nhóm Đang xử lý bởi bạn: Gán cho `@me` hoặc tài khoản hiện tại.
      * Nhóm Stale Claim: Có nhãn `in-progress` nhưng `updatedAt` > 24 giờ.
    - **3.2. Động cơ Xếp hạng Ưu tiên Kỹ thuật (Type & Dependency Ranking)**:
      - Xếp hạng theo trọng số kỹ thuật: `bug/hotfix` (P0) > `refactor/architecture` (P1) > `feat/enhancement` (P2) > `perf/docs` (P3) dựa trên Labels hoặc Conventional Commit Prefix trong Title.
      - Phân tích phụ thuộc: Ưu tiên refactor module nền tảng trước khi đắp thêm tính năng mới; phát hiện blocker qua chú thích `Blocked by #X`.
    - **3.3. Cổng Tương tác Người Dùng (Interactive HITL Confirmation Gate)**:
      - Sử dụng công cụ `ask_question` với danh sách lựa chọn có cấu trúc:
        * `[P0] (Recommended) #X: <title>`
        * `[P1] #Y: <title>`
        * `[Đang xử lý bởi bạn] #Z: <title>`
        * `[⚠️ Stale Claim >24h] #W: Tiếp quản xử lý`
        * `Tạo việc mới ngoài backlog (Unlisted custom task)`
    - **3.4. Khóa Nhận Việc An Toàn (Multi-Client Peer Claim Lock)**:
      - Chuẩn bị thư mục: `mkdir -p .md/scratch`
      - Sanitize slug và xác định branch: `${TYPE}/issue-${ID}-${SLUG}`
      - Soạn thảo và đăng claim notice qua file: `gh issue comment <id> -F .md/scratch/claim_notice_<id>.md`
      - Đọc lại comments chống race condition: `gh issue view <id> --json comments`
      - Nếu thua cuộc: Ghi log nhượng bộ, gỡ assignee của mình (`--remove-assignee "@me"`), KHÔNG gỡ nhãn `in-progress`, quay lại menu.
      - Nếu thắng cuộc: Gán nhãn `in-progress`, gỡ `ready-for-agent` (nếu tồn tại), gán assignee `@me`.
    - **3.5. Local Discovery & Graceful Offline Fallback**:
      - Nếu `gh` lỗi hoặc mất mạng: Quét đệ quy `.md/knowledge/issues/issue-*.md` và `.md/knowledge/issues/**/issues/*.md`, lọc `state: open/needs-triage/ready-for-agent`.
      - Nếu không có issue nào hoặc người dùng chọn làm việc ngoài backlog: Chuyển về phỏng vấn ngắn gọn (loại việc + mô tả).
    - **Tiêu chí hoàn thành Bước 3:** Bắt buộc có dòng:
      `- **Tiêu chí hoàn thành:** Thu thập đầy đủ phạm vi yêu cầu từ Issue hoặc phỏng vấn người dùng, hoàn tất Claim Lock hợp lệ nếu chọn từ Backlog.`
- **Cập nhật Bước 5 (Khởi tạo branch an toàn)**:
  - Thay thế lệnh đơn `git checkout -b` bằng kiểm tra đa nhánh:
    ```bash
    if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
      git checkout "${BRANCH_NAME}"
    elif git show-ref --verify --quiet "refs/remotes/origin/${BRANCH_NAME}"; then
      git checkout -b "${BRANCH_NAME}" --track "origin/${BRANCH_NAME}"
    else
      git checkout -b "${BRANCH_NAME}"
    fi
    ```

### Target 2: `tests/test_upstream_workflows.py`
- Mở rộng test suite `test_ccba_new_feature_workflow_structure()`:
  - Kiểm tra `metadata.version` đạt `"1.3.0"`.
  - Kiểm tra `gh issue list` với `--state open` và `--json`.
  - Kiểm tra `gh issue view` với `--json`.
  - Kiểm tra các khái niệm trọng số ưu tiên: `P0`, `P1`, `P2`, `P3`.
  - Kiểm tra quy tắc khóa nhận việc `CCBA_PEER_CLAIM_LOCK` và cơ chế nhượng bộ (Yield Protocol).
  - Kiểm tra cơ chế rẽ nhánh an toàn `git show-ref`.

### Target 3: Compilers & Registry Sync
- Chạy `.venv/bin/python scripts/governance/compile_catalog.py` để đồng bộ `catalog.yaml`.
- Chạy `.venv/bin/python scripts/governance/compile_skills_docs.py --write` để cập nhật `skills_compiled.md` và tài liệu liên quan.

---

## 4. Kế Hoạch Kiểm Thử & Nghiệm Thu (Verification Plan)

Thực thi trên môi trường ảo `.venv/bin/python` của Hub Monorepo:
1. **Unit Test Scoped**:
   ```bash
   .venv/bin/pytest tests/test_upstream_workflows.py -v
   ```
2. **Skill Governance Validation**:
   ```bash
   .venv/bin/python scripts/validate_skills.py --file .agents/skills/ccba-new-feature/SKILL.md --enforce-gpi
   ```
3. **Deterministic Patch Verification**:
   ```bash
   .venv/bin/python -m ccba_harness verify-patch --preset skill --target .agents/skills/ccba-new-feature/SKILL.md
   ```
4. **Catalog & Docs Synchronization Check**:
   ```bash
   .venv/bin/python scripts/governance/compile_catalog.py --check
   .venv/bin/python scripts/governance/compile_skills_docs.py --check
   ```
5. **Spoke Synchronization Dry-Run**:
   ```bash
   .venv/bin/python scripts/sync_spoke.py --dry-run
   ```

---

## 5. Tiến Độ Triển Khai (Milestones)

- [x] **Milestone 1**: Pre-Flight check, Checkout main, Pull latest, Prune merged branches.
- [x] **Milestone 2**: Bóc tách Issue #342, Khóa nhận việc (Peer Claim Lock), Tạo branch `feat/issue-342-autonomous-issue-triage-claiming`.
- [x] **Milestone 2.5 (`/boost`)**: Thẩm tra phản biện chuyên sâu, vá lỗi linter completion criteria, vá lỗi Git branch already exists, và hoàn thiện Yield Protocol.
- [ ] **Milestone 3**: Soạn thảo và hoàn thiện bản nâng cấp `SKILL.md` (v1.3.0) theo thiết kế RFC.
- [ ] **Milestone 4**: Cập nhật và bổ sung tests trong `tests/test_upstream_workflows.py`.
- [ ] **Milestone 5**: Biên dịch lại `catalog.yaml` và tài liệu tự động (`compile_catalog.py`, `compile_skills_docs.py`).
- [ ] **Milestone 6**: Chạy toàn bộ bộ kiểm thử tự động, xác thực Zero-Regression, xuất Walkthrough bàn giao.
