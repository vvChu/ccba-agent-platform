---
proposal_id: "2026-09-17_dynamic-base-branch-for-create-pr"
type: "skills"
name: "dynamic-base-branch-for-create-pr"
status: "proposed"
priority: "Cao"
proposed_by_project: "dgx-spark-toolkit"
proposed_by_archetype: "specialized_extension"
proposed_date: "2026-09-17"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Tất cả Spokes"
---

# RFC Proposal: Nâng Cấp Kỹ Năng ccba-create-pr Tự Động Nhận Diện Base Branch (v1.2.0)

- **Tác giả đề xuất:** Kỹ sư / Agent đại diện Spoke (`dgx-spark-toolkit`)
- **Ngày lập:** 2026-09-17
- **Trạng thái:** Đang đề xuất (Proposed)
- **Căn cứ pháp lý nền tảng:** ADR-0045, ADR-0046, ADR-0056, ADR-0058

---

### 1. Bối cảnh & Động lực Thực tế tại Spoke (Context & Real-world Motivation)

1. **Nỗi đau thực tế (Pain point):**
   - Kỹ năng [`ccba-create-pr`](../skills/ccba-create-pr/SKILL.md) (v1.1.0) hiện tại trên Hub giả định ngầm toàn bộ repository đều sử dụng nhánh chính là `main` (`gh pr create --base main`, `git log origin/main..HEAD`).
   - Khi chạy quy trình tại các Spoke sử dụng nhánh `master` (như dự án `dgx-spark-toolkit`) hoặc bất kỳ nhánh chính nào khác, lệnh kiểm tra Main Branch Guard (Bước 0) và lệnh mở PR (Bước 3) gặp lỗi không tìm thấy `origin/main` hoặc mở PR trỏ sai base branch.
2. **Quá trình ươm tạo & kiểm chứng tại Spoke:**
   - Đã triển khai và kiểm chứng thực tế tại Spoke `dgx-spark-toolkit` trong phiên làm việc giải phóng Issue #51 (PR #52).
   - Tích hợp cơ chế phát hiện tự động nhánh chính remote qua `git symbolic-ref --short refs/remotes/origin/HEAD` hoặc fallback kiểm tra `origin/main` / `origin/master`.
3. **Giá trị khi phổ biến lên Hub:**
   - Nâng cao tính tổng quát và độ bền bỉ của Kernel Skill `ccba-create-pr`.
   - Giúp toàn bộ Spokes trong hệ sinh thái CCBA (bất kể dùng `main` hay `master`) vận hành trơn tru mà không cần can thiệp thủ công.

---

### 2. Đánh Giá Giá Trị × Rủi Ro × KISS (Evaluation Matrix)

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Rất cao | Ngăn chặn đứt gãy quy trình tạo PR và bảo vệ nhánh chính trên đa Spoke |
| **Độ Phức tạp (Complexity)** | Rất thấp (KISS) | Chỉ thay đổi logic phân giải tên nhánh bằng lệnh git nội tại, không thêm dependency |
| **Rủi ro Rò rỉ (Risk)** | 0% (Triệt tiêu) | Không chứa logic đặc thù dự án con, hoàn toàn platform-agnostic |
| **Bảo tồn Tiêu chuẩn** | Tuân thủ 100% | Vượt qua `validate-skill --enforce-gpi` |

---

### 3. Thiết Kế Chi Tiết & Thay Đổi Kỹ Thuật

- **Tệp sửa đổi trọng tâm:** `.agents/skills/ccba-create-pr/SKILL.md` (bump version `1.1.0` $\rightarrow$ `1.2.0`).
  - **Bước 0:** Xác định nhánh chính `<default_branch>` (qua `git symbolic-ref --short refs/remotes/origin/HEAD`) và dùng `<default_branch>` cho các lệnh kiểm tra commit chưa push và reset nhánh chính.
  - **Bước 3:** Sử dụng `--base <default_branch>` cho lệnh `gh pr create --body "$PR_BODY"`, tự động sinh URL so sánh chính xác theo nhánh chính remote.
- **Các thay đổi phụ trợ & đồng bộ hệ thống (Supporting Changes):**
  - Cập nhật rào chắn liên kết trong `tests/governance/test_global_skills_integrity.py` bỏ qua placeholder `<...>`.
  - Đồng bộ trừ thư mục `tests/` và `scripts/tests/` khỏi kiến trúc structural drift trong `scripts/governance/drift_auditor.py`.
  - Tăng cường khả năng chịu lỗi import trong `packages/ccba-legal-intel/src/ccba_legal/federated_rag.py` (`rank_bm25`) và cách ly mock tại `packages/ccba-harness/tests/test_tuner.py`.
