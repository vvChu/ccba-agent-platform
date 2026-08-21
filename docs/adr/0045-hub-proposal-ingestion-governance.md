# ADR 0045: Hub Proposal Ingestion & Lifecycle Governance Standard (Hybrid Gate & Supervised Self-Healing)

## Trạng thái (Status)
**Đã phê duyệt (Approved)** — 2026-08-21

## Bối cảnh (Context)
Trong kiến trúc Hub-and-Spoke của CCBA Agent Platform, các dự án con (Spoke) chủ động giải quyết bài toán nghiệp vụ thực tế, đóng gói các công cụ/kỹ năng hữu ích và đề xuất ngược lên Hub thông qua workflow `/ccba-propose-to-hub` (ADR 0044).

Tuy nhiên, ở phía Hub Maintainer, quy trình tiếp nhận và thẩm định PR đề xuất trước đây chưa có quy chuẩn thống nhất, dẫn đến các rủi ro:
1. **Rò rỉ dữ liệu / Ô nhiễm Hub (Spoke Leakage):** Các tệp tin tạm thời, tài liệu học tập thử nghiệm cục bộ của Spoke (ví dụ `.md/teach/`), hoặc đường dẫn ổ đĩa tuyệt đối (`D:\...`) vô tình bị commit kèm vào PR lên Hub monorepo.
2. **Thiếu tính nhất quán trong Review:** Việc rà soát thủ công hoặc ra lệnh tự do (ad-hoc prompting) khiến Maintainer dễ bỏ sót các chốt chặn quan trọng (kiểm tra Deep Seams export, phân tích nhận xét của Copilot, cập nhật `catalog.yaml`).
3. **Đứt gãy vòng đời Proposal:** Các tệp `.agents/proposals/*.md` không được cập nhật trạng thái sau khi merge, khiến Hub khó truy vết lịch sử đóng góp.

## Quyết định Kiến trúc (Decision)
Thiết lập tiêu chuẩn **Quản trị Tiếp nhận Đề xuất Hub Toàn diện (Hub Proposal Ingestion & Lifecycle Governance)** dựa trên mô hình **Hybrid 2 Cổng**:

### 1. Cổng Cứng Tự Động (Hard Gate — CI Automation)
- Triển khai script `scripts/governance/check_spoke_leakage.py` chạy trực tiếp trong GitHub Actions CI.
- Tự động chặn đứng (Exit code 1 / Báo đỏ CI) nếu PR vi phạm một trong các điều kiện:
  - Chứa tệp tin thuộc thư mục cấm của Spoke: `.md/teach/`, `.tmp/`, `.out-of-scope/`, `__pycache__/`.
  - Chứa đường dẫn tuyệt đối dạng Windows (`D:\...`, `C:\Users\...`) trong mã nguồn mới.
  - Tệp đề xuất trong `.agents/proposals/` thiếu frontmatter metadata bắt buộc (`proposal_id`, `type`, `status`, `name`).

### 2. Cổng Mềm Tương Tác (Soft Gate — Supervised Self-Healing Workflow)
- Triển khai workflow `/ccba-review-proposal` cho Agent tại Hub.
- Agent đóng vai trò Trợ lý Thẩm định theo quy trình chuẩn hóa 5 bước:
  1. **Tiếp nhận & Khảo sát PR:** Đọc proposal và phân tích diff.
  2. **Kiểm tra Rò rỉ Spoke:** Chạy đối soát Spoke Leakage Guard.
  3. **Thẩm định Kiến trúc Deep Seams:** Xác thực export tại `packages/<pkg>/src/__init__.py` và bộ test độc lập.
  4. **Bóc tách Nhận xét Copilot & CI Status:** Tự động thu thập cảnh báo từ GitHub API.
  5. **Tự sửa lỗi có kiểm soát (Supervised Self-Healing) & Merge:** Tự động vá các lỗi cú pháp/regex rõ ràng, giải quyết conflict cơ bản, chạy `pytest` xác minh xanh 100%, trình Maintainer duyệt diff và thực hiện `gh pr merge --squash --delete-branch`.

### 3. Quản trị Vòng đời Hậu Merge (Post-Merge Lifecycle Governance)
- Tự động cập nhật frontmatter tệp `.agents/proposals/*.md`: `status: "merged"`, `merged_commit: "<hash>"`, `merged_date: "<date>"`.
- Tự động kiểm tra và đăng ký công cụ/kỹ năng mới vào `catalog.yaml` và `PLATFORM.md`.
- Gợi ý danh sách các Spoke downstream nên chạy `/ccba-update-spoke` để nạp tính năng mới.

## Hệ quả & Đánh đổi (Consequences)
- **Tích cực:**
  - Bảo vệ 100% độ thuần khiết của Hub Monorepo, ngăn chặn triệt để rò rỉ dữ liệu và ô nhiễm mã nguồn.
  - Chuẩn hóa quy trình thẩm định cho Maintainer thành 1 lệnh duy nhất, giảm tải nhận thức (cognitive load).
  - Khép kín hoàn toàn vòng lặp Upstream Contribution giữa Hub và các Spoke.
- **Đánh đổi:**
  - Cần bảo trì thêm script `check_spoke_leakage.py` và workflow `ccba-review-proposal.md`.
