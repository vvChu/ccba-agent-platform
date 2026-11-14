---
name: ccba-create-pr
description: Kiểm tra chất lượng code (Shift-Left), Main Branch Guard, đẩy code và mở GitHub Pull Request kèm rào chắn Dual-Gate CI & Copilot Review
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
tier: kernel
disable-model-invocation: true
command: /ccba-create-pr
user-invocable: true
metadata:
  version: "1.3.3"
  author: "CCBA Hub"
gpi:
  s: 3.0
  k: 3.0
  a: 1.0
  p: 1.0
triggers:
- create pr
- create-pr
- tạo pr
- mở pr
- ccba-create-pr
- pull request
---

# Kỹ năng: Tạo Pull Request Chuẩn CCBA Platform (CCBA Pull Request Flow)

Quy trình tự động hóa kiểm định chất lượng mã nguồn tại chỗ (Shift-Left Gate), bảo vệ nhánh chính (`<default_branch>`), đẩy mã nguồn và khởi tạo GitHub Pull Request kèm vòng lặp theo dõi CI tích xanh và đối soát góp ý từ Copilot Review. *(Lệnh: `/ccba-create-pr`)*

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`seam-exempt`** (SOP kernel mở Pull Request trong repo hiện tại). GPI đạt (3.0, 3.0, 1.0, 1.0) = 14.0; kỹ năng `ccba-contribute-to-hub` đã kế thừa quy chuẩn này cho chiều đóng góp từ Spoke sang Hub. Không đóng gói pipeline xử lý dữ liệu hay phụ thuộc Seam Contract ứng dụng cụ thể. Giữ nguyên `tier: kernel`.

---

## 🛡️ Bước 0: Main Branch Guard (Tự động phát hiện & bảo vệ nhánh chính)

1. **Lấy tên branch hiện hành & xác định nhánh chính (Default Branch):**
   ```bash
   git branch --show-current
   git symbolic-ref --short refs/remotes/origin/HEAD
   ```
   *Agent xác định nhánh hiện tại (`<current_branch>`) và nhánh chính mặc định của repository (`<default_branch>`, ví dụ: `main` hoặc `master`, trích xuất từ `origin/HEAD` hoặc fallback kiểm tra `origin/main` / `origin/master`).*
2. **Nếu đang ở nhánh chính (`<default_branch>`)**: Kiểm tra xem có commit nào chưa được push lên remote không:
   ```bash
   git log origin/<default_branch>..<default_branch> --oneline
   ```
3. **Nếu có commit trên nhánh chính chưa push** $\rightarrow$ Tự động tạo feature branch hồi tố (Retroactive Branch Creation):
   - Phân tích các thông điệp commit gần nhất để suy ra loại công việc (`feat`, `fix`, `docs`, `refactor`, `chore`) và mô tả ngắn gọn.
   - Gợi ý tên branch chuẩn (ví dụ: `feat/improve-pr-automation` hoặc `fix/query-timeout`).
   - Sau khi người dùng đồng ý, thực hiện tách nhánh an toàn:
     ```bash
     # Tạo feature branch tại vị trí hiện tại (giữ nguyên commits)
     git branch <tên-branch>
     # Reset nhánh chính về origin sạch sẽ
     git reset --hard origin/<default_branch>
     # Chuyển sang feature branch vừa tạo
     git checkout <tên-branch>
     ```
4. **Nếu đang ở nhánh chính nhưng KHÔNG có commit mới**:
   - Dừng lại và nhắc nhở: *"Không có thay đổi nào trên `<default_branch>` để tạo PR. Hãy dùng `/ccba-new-feature` để tạo feature branch trước khi lập trình."*
5. **Nếu đã ở nhánh tính năng (`feat/*`, `fix/*`, `proposal/*`)**: Tiếp tục Bước 1.

- **Tiêu chí hoàn thành:** Đảm bảo toàn bộ commit nằm trên đúng nhánh tính năng, nhánh chính (`<default_branch>`) được bảo vệ tuyệt đối.

---

## 🧪 Bước 1: Kiểm định Chất lượng Local Shift-Left Gate (ADR-0058 Hard Completion Lock)

Trước khi đẩy mã nguồn lên remote, Agent **BẮT BUỘC** thực hiện kiểm tra tại chỗ để đảm bảo không đưa code lỗi lên GitHub Actions CI:

1. **Kiểm tra trạng thái Working Tree:**
   ```bash
   git status --short
   ```
   *Nếu còn thay đổi dở dang, hoàn tất commit hoặc stash trước khi tiếp tục.*

2. **Chạy bộ kiểm chuẩn cục bộ (Scoped Shift-Left Gate):**
   - **Tại Hub Platform (`ccba-agent-platform`):**
     ```bash
     # Nếu thay đổi liên quan đến kỹ năng/governance:
     python -m ccba_harness verify-patch --preset skill
     # Nếu thay đổi liên quan đến monorepo packages/code:
     python -m ccba_harness verify-patch --preset code
     # Nếu có sửa đổi dưới scripts/ (kiểm tra lại trần AST <= 50 dòng SAU khi chạy ruff format):
     python -m pytest scripts/tests/ -q
     ```
   - **Tại Spoke (Pháp điển / Knowledge Corpus / Specialized Spokes):**
     ```bash
     python scripts/validate_legal_spoke.py
     ```
   - **Nếu nhánh chính cục bộ đang có commit hoặc file dở dang của phiên đồng đẳng (`RULE-4.21`):** Thực thi kiểm định, tách nhánh và mở PR trên một `git worktree` cô lập tách trực tiếp từ `origin/<default_branch>`.
3. **Quy tắc chặn lỗi tại nguồn:**
   - Nếu kiểm chuẩn trả về mã thoát `0`: Mã nguồn đạt chuẩn, chuyển sang Bước 2.
   - Nếu có lỗi kiểm thử hoặc vi phạm linting: **DỪNG LẠI NGAY LẬP TỨC**, sửa lỗi tại chỗ và commit lại trước khi đẩy lên remote.

- **Tiêu chí hoàn thành:** Toàn bộ rào chắn kiểm chuẩn cục bộ đạt 100% PASS (Exit Code 0).

---

## 📤 Bước 2: Đẩy Mã Nguồn Lên Remote (Push & Set Upstream)

1. **Lấy tên branch hiện tại:**
   ```bash
   git branch --show-current
   ```
2. **Đẩy branch lên remote và thiết lập tracking:**
   ```bash
   git push -u origin <current_branch>
   ```

- **Tiêu chí hoàn thành:** Branch đã được cập nhật đầy đủ trên remote repository (`origin`).

---

## 🚀 Bước 3: Tự Động Khởi Tạo Pull Request (GitHub CLI `gh`)

1. **Kiểm tra xác thực GitHub CLI:**
   ```bash
   gh auth status
   ```
2. **Phân tích thông tin để tạo Title & Body chuẩn CCBA:**
   - **Xác định Base Branch:** Lấy tên nhánh chính (`<default_branch>`) từ Bước 0 (`main` hoặc `master`).
   - **Tiêu đề PR (Conventional Commits):** Trích xuất từ tiền tố branch (`feat/`, `fix/`, `refactor/`) và commit đầu tiên.
   - **Liên kết Issue:** Nếu branch có chứa mã Issue (ví dụ `feat/issue-266-...` hoặc có tham số `--issue <id>`), tự động gắn `Closes #<id>` vào phần cuối của PR body.
   - **Mô tả PR (`PR Body` — Khuôn mẫu Show-Me Visual & Merge Danger `v1.3.0 #1120`):** Đọc khuôn mẫu chuẩn tại [`.github/pull_request_template.md`](../../../.github/pull_request_template.md) (tên tệp chữ thường trên Linux; không truy cập `PULL_REQUEST_TEMPLATE.md` viết hoa), sử dụng ngôn ngữ nghiệp vụ từ `CONTEXT.md` và trình bày theo cấu trúc 3 phần chuẩn mực:
     ```markdown
     ## Summary

     <chọn góc nhìn trực quan nhỏ nhất làm rõ điểm cốt lõi: pseudocode cho thuật toán, call tree cho luồng gọi runtime, file tree cho tái cấu trúc thư mục, sơ đồ Mermaid cho tương tác thành phần, hoặc khối diff tập trung>

     ## Evidence

     - **Before:** <kết quả test lỗi / output CLI cũ / ảnh chụp màn hình trước khi sửa>
     - **After:** <kết quả test xanh / output CLI mới / ảnh chụp màn hình sau khi sửa>

     ## Merge Danger

     **Door:** <One-way hoặc Two-way>
     **Blast Radius:** <Localized | Package-wide | Monorepo-wide | Spoke-affecting>
     ```
     Kèm danh sách các commit trên branch tính năng so với nhánh chính:
     ```bash
     git log origin/<default_branch>..HEAD --pretty=format:"- %s"
     ```
   - **Tiền kiểm `One-Way Door` & `TradeoffCard` (`ADR-0067`):** Ghi mô tả PR ra tệp tạm `<body_file>` (tuyệt đối không truyền chuỗi Markdown dài trực tiếp qua `--body`), sau đó chạy kiểm định phân loại cửa rủi ro và thẻ đánh đổi (`#L<a>-L<b>` tối đa 30 dòng):
     ```bash
     python -m ccba_harness door-triage <changed_files> --pr-body-file <body_file> --enforce-tradeoff-card
     ```
3. **Kiểm tra chống trùng lặp & Khởi tạo Pull Request bằng GitHub CLI (`RULE-4.21`, `RULE-5.11`):**
   ```bash
   # Kiểm tra trạng thái remote trước khi tạo để chống sinh PR trùng lặp:
   gh pr list --head <current_branch> --json number,url
   # Tạo PR qua tệp mô tả (-F) và gán người phụ trách:
   gh pr create --title "<Title>" -F <body_file> --base <default_branch> --head <current_branch> --assignee "@me"
   # Khi cần cập nhật mô tả PR hiện có (tránh lỗi GraphQL Classic Projects của gh pr edit):
   gh api repos/<owner>/<repo>/pulls/<PR_NUMBER> -X PATCH -F body=@<body_file>
   ```
4. **Fallback thủ công (nếu `gh` chưa cài hoặc chưa đăng nhập):**
   - Trích xuất URL tạo PR từ `git remote get-url origin`: `https://github.com/<owner>/<repo>/compare/<default_branch>...<current_branch>`.
   - In đường dẫn kèm mẫu tiêu đề và mô tả để người dùng mở trên trình duyệt.

- **Tiêu chí hoàn thành:** Lệnh `door-triage --enforce-tradeoff-card` trả về Exit Code `0`, không phát sinh PR trùng lặp, và Pull Request được mở thành công trên GitHub trỏ đúng base branch (`<default_branch>`) kèm link PR và mã số PR.

---

## 🔄 Bước 4: Đồng Hành Dual-Gate CI & Copilot Review (Reactive Wakeup Invariant)

> [!IMPORTANT]
> **Tuyệt đối không kết thúc quy trình ngay sau khi mở PR.** Agent phải đồng hành cho đến khi toàn bộ CI tích xanh và mọi góp ý của Copilot Review được xử lý.

1. **Lấy mã số PR vừa tạo:**
   ```bash
   gh pr view --json number,url -q ".number"
   ```
2. **Theo dõi GitHub Actions CI (Cổng 1):**
   - Chạy kiểm tra: `gh pr checks <PR_NUMBER>`.
   - **Rào chắn Zero-Polling Policy (RULE-4.8):** Nếu CI đang chạy, ưu tiên khởi chạy nền `gh pr checks <PR_NUMBER> --watch` (`WaitMsBeforeAsync: 500`) rồi **lập tức kết thúc lượt (End Turn)** để hệ thống đánh thức qua *Reactive Wakeup* đúng 1 lần khi hoàn tất. Nếu dùng `schedule` cho ma trận CI Hub (`~6–7` phút), bắt buộc áp dụng backoff phân tầng (`DurationSeconds: 240` lần đầu $\to$ `60` pha đuôi) thay vì đặt `60s` liên tiếp; **tuyệt đối không** gọi thêm tool nào khác trong cùng lượt với `schedule` và **tuyệt đối CẤM** vòng lặp `manage_task(status)` làm ô nhiễm context.
3. **Theo dõi AI Code Reviewers (Copilot & Cursor Bugbot — Cổng 2):**
   - Kiểm tra bot review (tại Hub gọi trực tiếp `scripts/validation/audit_pr_comments.py`, tại Spoke gọi qua `CCBA_HUB_PATH`):
     ```bash
     # Tại Hub:
     python scripts/validation/audit_pr_comments.py --pr <PR_NUMBER>
     # Tại Spoke:
     python "${CCBA_HUB_PATH:-../ccba-agent-platform}/scripts/validation/audit_pr_comments.py" --pr <PR_NUMBER>
     ```
   - Chờ Copilot hoặc Bugbot hoàn tất review (không merge khi `reviewRequests` vẫn còn chứa bot reviewer).
   - **Đối soát Invariants:** Rà soát các góp ý của bot đối chiếu với tập luật 10 Invariants tại [`.github/bugbot-rules.md`](../../../.github/bugbot-rules.md).
4. **Tự chữa lành (Self-Healing Loop):**
    - Nếu CI thất bại: Đọc log qua `gh run view <RUN_ID> --log-failed` $\rightarrow$ Vá lỗi $\rightarrow$ Commit & push.
    - Nếu AI Reviewer (Copilot hoặc Bugbot) góp ý: Refactor code, giải trình vào báo cáo nghiệm thu tại `.md/knowledge/reports/walkthrough.md` (kèm review_id `PRR_...` hoặc inline comment `id` theo RULE-4.10; tuyệt đối không lưu tại `.md/walkthrough.md` trần) $\rightarrow$ Commit & push.
    - Lặp lại đến khi 100% checks xanh và `audit_pr_comments.py` trả về exit code 0.

- **Tiêu chí hoàn thành:** 100% CI Checks tích xanh và toàn bộ review của Copilot/Bugbot được giải quyết triệt để tuân thủ 10 Invariants (`python scripts/validation/audit_pr_comments.py --pr <PR_NUMBER>` trả về Exit Code `0`, `0` vòng lặp `manage_task` polling).

---

## 🏁 Bước 5: Bàn Giao Kích Hoạt `/ccba-release-feature`

Sau khi PR đã sẵn sàng (CI xanh, Copilot sạch):
1. Cung cấp liên kết PR cho người dùng.
2. Hướng dẫn bước kế tiếp:
   > *"Pull Request đã vượt qua 100% CI Checks và kiểm chuẩn Copilot. Hãy gọi lệnh `/ccba-release-feature` để đối soát, squash merge và tự động đóng issue."*

- **Tiêu chí hoàn thành:** Báo cáo nghiệm thu hoàn tất bàn giao cho quy trình release.
