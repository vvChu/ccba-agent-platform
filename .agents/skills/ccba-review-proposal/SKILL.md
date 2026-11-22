---
name: ccba-review-proposal
description: Thẩm định toàn trình PR đề xuất từ Spoke lên Hub kèm Adaptive Tiered Review (Fast/Boost), Spoke Leakage Guard, Copilot Guard và Đồng bộ Catalog Hậu Merge (ADR 0045, ADR 0047)
applies_to:
- Phần mềm
- Tác vụ Admin
bundle: _governance
scope: hub
posture: seam-exempt
tier: kernel
disable-model-invocation: true
command: /ccba-review-proposal
user-invocable: true
metadata:
  version: "1.1.0"
  author: "CCBA Hub Lead Maintainer"
gpi:
  s: 4.0
  k: 4.0
  a: 1.0
  p: 1.0
triggers:
- ccba-review-proposal
- review-proposal
- review proposal
- thẩm định proposal
- duyệt proposal
---

# Workflow: Review Proposal (Thẩm Định Đề Xuất Spoke Lên Hub — ADR 0045 & ADR 0047)

Quy trình chuẩn hóa toàn trình dành riêng cho Hub Maintainer (có thẩm quyền QC Level 5 theo Điều 13 CCBA Charter 2026) để thẩm định, làm sạch, tự sửa lỗi có kiểm soát và hợp nhất an toàn các đề xuất (Pull Requests) từ các dự án Spoke vào Hub Monorepo với cơ chế **Phân Cấp Thích Ứng (Adaptive Tiered Review)**.

## 📋 Bước 1: Tiếp Nhận, Phân Tuyến & Khởi Tạo (Pre-flight Sync & Tier Selection)

1. **Đồng bộ Base Branch (Pre-flight Sync Gate):**
   - Đảm bảo nhánh `main` local sạch và được đồng bộ với upstream trước khi thẩm định:
     ```bash
     git checkout main && git pull origin main
     ```
2. **Xác định PR mục tiêu & Tùy chọn Chế độ Review:**
   - Cú pháp chuẩn: `/ccba-review-proposal <PR_NUMBER> [--boost | --deep]`
   - Nếu không chỉ định PR: Tự động quét danh sách các PR đang mở:
     ```bash
     gh pr list --state open
     ```
3. **Phân Tuyến Thích Ứng (Adaptive Review Tier & Progressive Disclosure):**
   - **Nhánh PR Auto-Tune (`auto-tune/*` hoặc tiêu đề PR chứa `auto-tune`):**
     - Đọc tài liệu tham chiếu [references/nightly_tuning_review.md](references/nightly_tuning_review.md) và tuân thủ quy trình đối soát Nightly Evolution Matrix, kiểm tra Goodhart gaming / nhồi từ khóa ảo và kích hoạt quy trình Supervised Halt Protocol nếu phát hiện bất thường.
   - **Spoke PR Thông Thường:** Tiếp tục Bước 1.4 (Khảo sát tệp Proposal và Spoke Leakage Guard).
   - **Tier 1 — Fast Deterministic Review (Mặc định):** Áp dụng cho PR scoped thông thường ($< 400$ LOC, đóng gói trong 1 package). Chạy bộ 3 Deterministic Workers tự động ($< 15$ giây).
   - **Tier 2 — Boost / Multi-Agent Deep Review:** Tự động kích hoạt khi có cờ `--boost` / `--deep` HOẶC PR thay đổi gói core `_core`, sửa đổi $> 400$ LOC. Ủy quyền cho subagents `DeepInvestigator` và `DeepCoder` thực hiện Double-Pass Adversarial Review và kiểm tra Threat Model.
4. **Khảo sát tệp Proposal và Spoke Leakage Guard:**
   - Kiểm tra tệp ghi nhận tại `.agents/proposals/[YYYY-MM-DD]_[name].md`.
   - Đọc YAML frontmatter (`proposal_id`, `type`, `proposed_by_project`, `priority`).
   - Đọc tóm tắt kiến trúc và mục tiêu nghiệp vụ mà Spoke đã giải quyết.

**Tiêu chí hoàn thành:** Nhánh main được đồng bộ, PR và tier review được xác định rõ ràng.

---

## 🛡️ Bước 2: Kích Hoạt 3 Worker Thẩm Định Song Song (Parallel Review Gate)

Điều phối 3 luồng kiểm tra song song (tự động chạy script hoặc phân bổ Subagents tương ứng theo Tier):

1. **Worker 1 — Spoke Leakage & Privacy Guard (ADR 0045):**
   - Chạy rào chắn rò rỉ và quét Maskara credentials trên diff nhánh:
     ```bash
     python scripts/governance/check_spoke_leakage.py
     python scripts/governance/sanitize_review_diff.py --check --base origin/main --head HEAD
     ```
   - *Chốt chặn (Zero Tolerance):* Không chứa `.md/teach/`, `.tmp/`, cache, đường dẫn tuyệt đối Windows `D:\...`. Tệp proposal bắt buộc có đủ 4 trường metadata (`proposal_id`, `type`, `status`, `name`).

2. **Worker 2 — Deep Seams & Scoped Tests Verification:**
   - Kiểm tra ranh giới Module Sâu: Mã nguồn nghiệp vụ nằm gọn trong `packages/[pkg]/src/`, entry points công khai khai báo trong `__all__` tại `__init__.py`.
   - Chạy kiểm thử tự động và linter (với PR gói Python trong `packages/`):
     ```bash
     uv run pytest packages/[package-name]/tests
     uv run ruff check packages/[package-name]
     ```
   - Với PR Tier 2A chỉ sửa skill hoặc template (không sửa mã nguồn `packages/`): chạy `python scripts/validate_skills.py --enforce-gpi`, `pytest tests/governance/ -q`, kiểm tra thuật ngữ, và smoke-test trực tiếp YAML hoặc template mới với Deep Seam Tầng 1 tương ứng.
   - *Tiêu chí:* $100\%$ Passed, 0 errors, 0 warnings.

3. **Worker 3 — Proposal Lifecycle & Catalog Governance (ADR 0047):**
   - Soát chiếu metadata frontmatter của skill hoặc workflow mới đề xuất và kiểm tra liên kết tài liệu bằng `python scripts/validate_docs.py . --src scripts,packages --changed`.
   - Kiểm tra đồng bộ `catalog.yaml`, Web Docs Portal và Traceability Matrix qua bộ 3 cờ `--check`:
     ```bash
     python scripts/governance/compile_catalog.py --check
     python scripts/governance/compile_skills_docs.py --check
     python scripts/sync_hub_adr_matrix.py --check
     ```

**Tiêu chí hoàn thành:** Cả 3 worker hoàn thành kiểm tra với 100% checks đạt chuẩn.

---

## 🤖 Bước 3: Bóc Tách Nhận Xét Copilot & CI Checks Status (Race-Condition Guard)

1. **Kiểm tra trạng thái GitHub Actions CI:**
   ```bash
   gh pr checks <PR_NUMBER>
   ```
2. **Chốt chặn Review Requests của Copilot (Chống Race Condition Merge Sớm):**
   - Đảm bảo Copilot đã hoàn tất nộp bài review trước khi đọc comment:
     ```bash
     gh pr view <PR_NUMBER> --json reviewRequests,reviews --jq '{pending: [.reviewRequests[]?.login], reviewed: [.reviews[]?.user.login]}'
     ```
   - Nếu `pending` còn chứa `copilot-pull-request-reviewer`, Agent tạm dừng chờ Copilot hoàn tất.
3. **Bóc tách và kiểm toán nhận xét kỹ thuật từ GitHub Copilot:**
   ```bash
   python scripts/validation/audit_pr_comments.py --repo <owner>/<repo> <PR_NUMBER>
   gh api repos/:owner/:repo/pulls/<PR_NUMBER>/comments --jq ".[] | {path: .path, line: .line, body: .body}"
   ```
4. **Phân loại nhận xét:**
   - *Lỗi kỹ thuật rõ ràng / Đường dẫn vi phạm:* Chuyển sang Bước 4 để tự động khắc phục (Self-Healing).
   - *Góp ý thiết kế / Tài liệu:* Báo cáo Maintainer xem xét.

**Tiêu chí hoàn thành:** 100% CI checks đạt `SUCCESS`, `reviewRequests` không chứa `copilot-pull-request-reviewer`, và `audit_pr_comments.py` trả về Exit Code `0`.

---

## 🛠️ Bước 4: Tự Sửa Lỗi Có Giám Sát (Supervised Self-Healing) & Hợp Nhất

1. **Khắc phục lỗi tự động trên Branch:**
   - Áp dụng các bản vá sửa regex, docstring conflict, link tuyệt đối hoặc format mã nguồn.
   - Chạy lại `pytest` và `ruff check` để xác minh xanh $100\%$.
   - Push bản vá lên nhánh PR: `git push origin <branch_name>`.
2. **Trình bày Diff cho Maintainer Phê Duyệt:**
   - Tóm tắt các điểm đã sửa và trình bày cho Maintainer bấm xác nhận.
3. **Hợp nhất vào nhánh `main` (Squash Merge):**
   ```bash
   gh pr merge <PR_NUMBER> --squash --delete-branch
   git checkout main && git pull origin main
   ```

**Tiêu chí hoàn thành:** Các lỗi được khắc phục và PR được squash merge thành công.

---

## 🏛️ Bước 5: Quản Trị Vòng Đời Hậu Merge (Post-Merge Governance)

Khi nhánh `main` áp dụng ruleset bắt buộc qua Pull Request và `required_status_checks`, mọi cập nhật hậu merge thực thi trên `git worktree` cô lập và hợp nhất qua follow-up PR:

1. **Khởi tạo Worktree Hậu Merge:**
   - Đồng bộ `main` (`git fetch origin && git pull --ff-only origin main`) và tạo worktree trên nhánh `docs/walkthrough-pr-<PR_NUMBER>`.
2. **Cập nhật Proposal Header & Walkthrough:**
   - Mở `.agents/proposals/[YYYY-MM-DD]_[name].md`, đổi `status: "open"` $\rightarrow$ `status: "merged"`, bổ sung `merged_pr`, `merged_commit` hash và `merged_date`, đồng thời cập nhật `.md/knowledge/reports/walkthrough.md`.
3. **Đăng ký Hệ Sinh Thái & Kiểm Định Triage (ADR 0047 & ADR 0067):**
   - Chạy kiểm định đồng bộ (hoặc tái biên dịch nếu có thay đổi frontmatter):
     ```bash
     python scripts/governance/compile_catalog.py --check
     python scripts/governance/compile_skills_docs.py --check
     python scripts/sync_hub_adr_matrix.py --check
     python scripts/validate_docs.py . --src scripts,packages --changed
     python scripts/governance/sanitize_review_diff.py --check --base origin/main --head HEAD
     python -m ccba_harness door-triage <changed_files> --enforce-tradeoff-card --pr-body-file <pr_body.md>
     ```
   - Nếu `cumulative_streak >= 3` trên `.agents` và `.md` làm `door-triage` leo thang `ONE_WAY_DOOR`, bắt buộc đính kèm `Tradeoff Card` hợp lệ (`Git Hunk Reference <= 30` dòng) trong mô tả follow-up PR.
4. **Hợp Nhất Follow-Up PR & Đồng Bộ Local:**
   - Mở follow-up PR, chờ 100% CI `SUCCESS` và `audit_pr_comments.py` trả Exit Code `0`, gỡ worktree rồi chạy `gh pr merge <followup_pr> --squash --delete-branch` và `git pull --ff-only origin main`.
5. **Gợi ý Spoke Sync (Closed-Loop Sync):**
   - Thông báo cho Spoke đề xuất kích hoạt `/ccba-update-spoke` để nạp tính năng mới và hoàn tất đóng vòng đóng góp thượng nguồn.

**Tiêu chí hoàn thành:** Proposal chuyển `status: "merged"`, `walkthrough.md` & catalog đồng bộ 100%, follow-up PR hợp nhất xanh, worktree dọn sạch.

---

## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu hoặc thẩm định PR đặc thù, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/nightly_tuning_review.md` | Hướng dẫn đối soát Nightly Evolution Matrix, phát hiện Goodhart gaming và quy trình Supervised Halt Protocol cho PR `auto-tune/*` |
