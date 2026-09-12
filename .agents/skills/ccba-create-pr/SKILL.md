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
  version: "1.0.0"
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

Quy trình tự động hóa kiểm định chất lượng mã nguồn tại chỗ (Shift-Left Gate), bảo vệ nhánh chính (`main`), đẩy mã nguồn và khởi tạo GitHub Pull Request kèm vòng lặp theo dõi CI tích xanh và đối soát góp ý từ Copilot Review. *(Lệnh: `/ccba-create-pr`)*

---

## 🛡️ Bước 0: Main Branch Guard (Tự động phát hiện & bảo vệ nhánh `main`)

1. **Lấy tên branch hiện hành:**
   ```bash
   git branch --show-current
   ```
2. **Nếu đang ở `main`**: Kiểm tra xem có commit nào chưa được push lên remote không:
   ```bash
   git log origin/main..main --oneline
   ```
3. **Nếu có commit trên `main` chưa push** $\rightarrow$ Tự động tạo feature branch hồi tố (Retroactive Branch Creation):
   - Phân tích các thông điệp commit gần nhất để suy ra loại công việc (`feat`, `fix`, `docs`, `refactor`, `chore`) và mô tả ngắn gọn.
   - Gợi ý tên branch chuẩn (ví dụ: `feat/improve-pr-automation` hoặc `fix/query-timeout`).
   - Sau khi người dùng đồng ý, thực hiện tách nhánh an toàn:
     ```bash
     # Tạo feature branch tại vị trí hiện tại (giữ nguyên commits)
     git branch <tên-branch>
     # Reset main về origin/main sạch sẽ
     git reset --hard origin/main
     # Chuyển sang feature branch vừa tạo
     git checkout <tên-branch>
     ```
4. **Nếu đang ở `main` nhưng KHÔNG có commit mới**:
   - Dừng lại và nhắc nhở: *"Không có thay đổi nào trên `main` để tạo PR. Hãy dùng `/ccba-new-feature` để tạo feature branch trước khi lập trình."*
5. **Nếu đã ở nhánh tính năng (`feat/*`, `fix/*`, `proposal/*`)**: Tiếp tục Bước 1.

- **Tiêu chí hoàn thành:** Đảm bảo toàn bộ commit nằm trên đúng nhánh tính năng, nhánh `main` được bảo vệ tuyệt đối.

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
     ```
   - **Tại Spoke (Pháp điển / Knowledge Corpus / Specialized Spokes):**
     ```bash
     python scripts/validate_legal_spoke.py
     ```
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
   - **Tiêu đề PR (Conventional Commits):** Trích xuất từ tiền tố branch (`feat/`, `fix/`, `refactor/`) và commit đầu tiên.
   - **Liên kết Issue:** Nếu branch có chứa mã Issue (ví dụ `feat/issue-266-...` hoặc có tham số `--issue <id>`), tự động gắn `Closes #<id>` vào phần cuối của PR body.
   - **Mô tả PR (PR Body):** Tự động liệt kê các commit trên branch tính năng:
     ```bash
     git log origin/main..HEAD --pretty=format:"- %s"
     ```
3. **Khởi tạo Pull Request bằng GitHub CLI:**
   ```bash
   gh pr create --title "<Title>" --body "<Body>`n`nCloses #<id>" --base main --head <current_branch>
   ```
4. **Fallback thủ công (nếu `gh` chưa cài hoặc chưa đăng nhập):**
   - Trích xuất URL tạo PR từ `git remote get-url origin`: `https://github.com/<owner>/<repo>/compare/main...<current_branch>`.
   - In đường dẫn kèm mẫu tiêu đề và mô tả để người dùng mở trên trình duyệt.

- **Tiêu chí hoàn thành:** Pull Request được mở thành công trên GitHub kèm link PR và mã số PR.

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
   - **Rào chắn Zero-Polling Policy (RULE-4.8):** Nếu CI đang chạy, Agent có thể chạy `gh pr checks <PR_NUMBER>` hoặc kết thúc lượt (End Turn) để hệ thống tự động đánh thức khi nhận kết quả. Tuyệt đối **CẤM** vòng lặp `manage_task(status)` làm ô nhiễm context.
3. **Theo dõi GitHub Copilot Code Review (Cổng 2):**
   - Kiểm tra bot review:
     ```bash
     python scripts/validation/audit_pr_comments.py --pr <PR_NUMBER>
     ```
   - Chờ Copilot hoàn tất review (không merge khi reviewRequests vẫn còn chứa bot reviewer).
4. **Tự chữa lành (Self-Healing Loop):**
   - Nếu CI thất bại: Đọc log qua `gh run view <RUN_ID> --log-failed` $\rightarrow$ Vá lỗi $\rightarrow$ Commit & push.
   - Nếu Copilot góp ý: Refactor code, giải trình vào báo cáo nghiệm thu (`walkthrough.md`) $\rightarrow$ Commit & push.
   - Lặp lại đến khi 100% checks xanh và `audit_pr_comments.py` trả về exit code 0.

- **Tiêu chí hoàn thành:** 100% CI Checks tích xanh và toàn bộ review của Copilot được giải quyết triệt để.

---

## 🏁 Bước 5: Bàn Giao Kích Hoạt `/ccba-release-feature`

Sau khi PR đã sẵn sàng (CI xanh, Copilot sạch):
1. Cung cấp liên kết PR cho người dùng.
2. Hướng dẫn bước kế tiếp:
   > *"Pull Request đã vượt qua 100% CI Checks và kiểm chuẩn Copilot. Hãy gọi lệnh `/ccba-release-feature` để đối soát, squash merge và tự động đóng issue."*

- **Tiêu chí hoàn thành:** Báo cáo nghiệm thu hoàn tất bàn giao cho quy trình release.
