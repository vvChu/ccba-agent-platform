# ccba-review-proposal — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Quy trình chuẩn SOP thẩm định các đề xuất Pull Request từ Spoke gửi lên Hub
> **Mô tả gốc:** Thẩm định toàn trình các PR đề xuất từ Spoke lên Hub kèm Adaptive Tiered Review (Fast/Boost), Spoke Leakage Guard, Copilot Guard và Đồng bộ Catalog Hậu Merge (ADR 0045, ADR 0047)

---

# Workflow: Review Proposal (Thẩm Định Đề Xuất Spoke Lên Hub — ADR 0045 & ADR 0047)

Quy trình chuẩn hóa toàn trình dành cho Hub Maintainer để thẩm định, làm sạch, tự sửa lỗi có kiểm soát và hợp nhất an toàn các đề xuất (Pull Requests) từ các dự án Spoke vào Hub Monorepo với cơ chế **Phân Cấp Thích Ứng (Adaptive Tiered Review)**.

---

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
3. **Phân Tuyến Thích Ứng (Adaptive Review Tier):**
   - **Tier 1 — Fast Deterministic Review (Mặc định):** Áp dụng cho PR scoped thông thường ($< 400$ LOC, đóng gói trong 1 package). Chạy bộ 3 Deterministic Workers tự động ($< 15$ giây).
   - **Tier 2 — Boost / Multi-Agent Deep Review:** Tự động kích hoạt khi có cờ `--boost` / `--deep` HOẶC PR thay đổi gói core `_core`, sửa đổi $> 400$ LOC. Ủy quyền cho subagents `DeepInvestigator` và `DeepCoder` thực hiện Double-Pass Adversarial Review và kiểm tra Threat Model.
4. **Khảo sát tệp Proposal:**
   - Kiểm tra tệp ghi nhận tại `.agents/proposals/[YYYY-MM-DD]_[name].md`.
   - Đọc YAML frontmatter (`proposal_id`, `type`, `proposed_by_project`, `priority`).
   - Đọc tóm tắt kiến trúc và mục tiêu nghiệp vụ mà Spoke đã giải quyết.

---

**Tiêu chí hoàn thành:** Nhánh main được đồng bộ, PR và tier review được xác định rõ ràng.

---

## 🛡️ Bước 2: Kích Hoạt 3 Worker Thẩm Định Song Song (Parallel Review Gate)

Điều phối 3 luồng kiểm tra song song (tự động chạy script hoặc phân bổ Subagents tương ứng theo Tier):

1. **Worker 1 — Spoke Leakage & Privacy Guard (ADR 0045):**
   - Chạy rào chắn rò rỉ và quét Maskara credentials:
     ```bash
     python scripts/governance/check_spoke_leakage.py
     ```
   - *Chốt chặn (Zero Tolerance):* Không chứa `.md/teach/`, `.tmp/`, cache, đường dẫn tuyệt đối Windows `D:\...`. Tệp proposal bắt buộc có đủ 4 trường metadata (`proposal_id`, `type`, `status`, `name`).

2. **Worker 2 — Deep Seams & Scoped Tests Verification:**
   - Kiểm tra ranh giới Module Sâu: Mã nguồn nghiệp vụ nằm gọn trong `packages/[pkg]/src/`, entry points công khai khai báo trong `__all__` tại `__init__.py`.
   - Chạy kiểm thử tự động và linter:
     ```bash
     uv run pytest packages/[package-name]/tests
     uv run ruff check packages/[package-name]
     ```
   - *Tiêu chí:* $100\%$ Passed, 0 errors, 0 warnings.

3. **Worker 3 — Proposal Lifecycle & Catalog Governance (ADR 0047):**
   - Soát chiếu metadata frontmatter của skill/workflow mới đề xuất.
   - Kiểm tra tính tương thích của `catalog.yaml` và Traceability Matrix.

---

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
3. **Bóc tách nhận xét kỹ thuật từ GitHub Copilot:**
   ```bash
   gh api repos/:owner/:repo/pulls/<PR_NUMBER>/comments --jq ".[] | {path: .path, line: .line, body: .body}"
   ```
4. **Phân loại nhận xét:**
   - *Lỗi kỹ thuật rõ ràng / Đường dẫn vi phạm:* Chuyển sang Bước 4 để tự động khắc phục (Self-Healing).
   - *Góp ý thiết kế / Tài liệu:* Báo cáo Maintainer xem xét.

---

**Tiêu chí hoàn thành:** Nhận xét từ Copilot và trạng thái CI được rà soát đầy đủ.

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

---

**Tiêu chí hoàn thành:** Các lỗi được khắc phục và PR được squash merge thành công.

---

## 🏛️ Bước 5: Quản Trị Vòng Đời Hậu Merge (Post-Merge Governance)

1. **Cập nhật Proposal Header:**
   - Mở tệp `.agents/proposals/[YYYY-MM-DD]_[name].md`, đổi `status: "open"` $\rightarrow$ `status: "merged"`, ghi nhận `merged_commit` hash và `merged_date`.
2. **Đăng ký Hệ Sinh Thái (ADR 0047):**
   - Tự động tái biên dịch Catalog SSoT:
     ```bash
     python scripts/governance/compile_catalog.py
     ```
3. **Gợi ý Spoke Sync (Closed-Loop Sync):**
   - Thông báo cho Spoke đề xuất kích hoạt **Bước 7 của `/ccba-contribute-to-hub`** (hoặc `/ccba-update-spoke`) để nạp tính năng mới và hoàn tất đóng vòng.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


**Tiêu chí hoàn thành:** Proposal cập nhật status merged, compile catalog thành công.
