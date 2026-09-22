---
name: ccba-graduate-rd

description: Quy trình cưỡng chế chuyển hóa mã nguồn R&D thành Deep Seam Production, tích hợp /boost, /teamwork và mở PR tự động.
applies_to:
- Phần mềm
- Kiểm định
- Thẩm tra thiết kế
bundle: _core
tier: orchestrator
is-orchestrated: true
user-invocable: true
disable-model-invocation: true
command: /ccba-graduate-rd
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
triggers:
- graduate
- tốt nghiệp
- hợp nhất vào hub
- consolidate
- deep seam
- chuyển scratch vào production
- ccba-graduate-rd
---

# Workflow: Tốt Nghiệp R&D → Deep Seam Production & Auto-PR (/ccba-graduate-rd)

Quy trình tự động hóa toàn trình 7 bước (Full-Cycle Autonomous Pipeline) chuyển hóa mã nguồn thử nghiệm (scratch script, prototype) thành module Production chuẩn mực trong Hub (`packages/ccba-*/src/`), tự động đóng gói Proposal, tạo Pull Request và tự làm xanh CI (Self-Healing Dual-Gate).

> [!CAUTION]
> **3 Bất Biến Tuyệt Đối (Core Invariants):**
> 1. **Không để script vá tồn tại qua phiên:** Mọi scratch script nằm trong `brain/*/scratch/` hoặc `.md/scratch/`, cấm commit vào `scripts/` Spoke.
> 2. **Upstream Promotion bắt buộc:** Khi scratch script chứng minh hiệu quả → Bắt buộc refactor vào Hub `packages/` trong cùng phiên.
> 3. **1-Pass Clean Run & 100% CI Green:** Xóa script vá, chạy lại lệnh gốc và nghiệm thu toàn bộ CI Gates đạt 100% Tích Xanh.

---

## 📋 Bước 1: Kiểm Kê & Phân Loại R&D Artifacts
Quét và phân loại toàn bộ files trong `brain/*/scratch/`, `.md/scratch/` và `scripts/`:
* **Thuật toán cốt lõi** (regex, parser, classifier, KaTeX): → Bước 2 nhúng Deep Seam.
* **Glue code** (CLI wrapper, `print`, `tempfile`): → Loại bỏ, không nhúng vào lõi.
* **Dữ liệu mẫu / fixture**: → Bước 3 chuyển thành test fixture.
* **Báo cáo / ghi chú**: → Lưu vào `.md/archive/` theo chuẩn ADR 0033.
- **Tiêu chí hoàn thành:** Hoàn tất kiểm kê và phân loại chính xác các artifacts thành phần lõi, glue code, test fixture và báo cáo.

---

## 🔧 Bước 2: Bóc Tách & Nhúng Lõi Deep Seam (Giao thức /boost)
Áp dụng cơ chế **Deep Reasoning** (`DeepCoder`) và **5 Cổng Phản Biện** (`improve-codebase-architecture`):
1. **Cổng 1 (Glue vs Domain):** Tỷ lệ $\ge 70\%$ Glue Code $\rightarrow$ KHÔNG nhúng vào lõi Seam.
2. **Cổng 2 (Hard Caller Gate):** Đếm số callers thực tế và xác minh implementation.
3. **Cổng 3 (SDK Signatures):** Kiểm tra signature tương thích kiến trúc hiện có.
4. **Cổng 4 (Unique Naming):** Đảm bảo symbol name không xung đột toàn cục.
5. **Cổng 5 (Measurable Friction):** Bằng chứng lỗi runtime hoặc benchmark thực tế.
*Refactor chuẩn mực:* Loại bỏ hardcoded paths, thêm type hints và Google docstrings đầy đủ.
- **Tiêu chí hoàn thành:** Mã nguồn lõi được đóng gói vào đúng Deep Seam package, vượt qua 5 cổng phản biện và có type hints đầy đủ.

---

## 🧪 Bước 3: Xây Dựng Test Suite (Double-Pass Adversarial Review)
1. Tạo test fixtures trong `packages/ccba-*/tests/` từ dữ liệu thực tế của phiên R&D.
2. Viết unit tests độc lập và chạy kiểm thử tự phản biện (Self-Adversarial):
   ```powershell
   python -m pytest packages/ccba-*/tests/ -v
   ```
   *Tiêu chuẩn:* **100% tests passed, 0 failures**.
- **Tiêu chí hoàn thành:** Test suite cho package chạy qua với 100% tests passed, bao phủ các trường hợp biên.

---

## 🔁 Bước 4: Kiểm Chứng 1-Pass Clean Run & Spoke CI
1. Xóa các scratch scripts cục bộ.
2. Chạy lại lệnh gốc từ đầu vào ban đầu (ví dụ: `python -m ccba_legal convert "ten_doc.docx" "legal_docs/..."`).
3. Chạy Master CI Gate của Spoke:
   ```powershell
   python scripts/validate_legal_spoke.py
   ```
   *Tiêu chuẩn:* `0 Errors, 0 Critical Warnings, 100% Pass`.
- **Tiêu chí hoàn thành:** Quy trình chạy sạch 1-pass không lỗi và Master CI Gate của Spoke đạt 100% Pass.

---

## 📦 Bước 5: Đóng Gói Proposal & Khởi Tạo Branch
Thực thi tại thư mục Hub (`hub_path`):
1. **Khởi tạo branch đề xuất (ADR 0045):**
   ```bash
   BRANCH_NAME="proposal/${ISSUE_ID:+issue-${ISSUE_ID}-}${PROPOSAL_NAME}"
   git checkout main && git pull origin main && git checkout -b "$BRANCH_NAME"
   ```
2. **Định dạng & Cập nhật Thống kê Kiến trúc:**
   ```bash
   python -m ruff check --fix . && python -m ruff format . && python scripts/update_arch_stats.py
   ```
3. **Soạn thảo Proposal File (`.agents/proposals/YYYY-MM-DD_[proposal-name].md`):** Ghi nhận đầy đủ Context, Implementation và Verification.
4. **Leakage Guard & Push:** Chạy `python scripts/governance/check_spoke_leakage.py` và `git push origin "$BRANCH_NAME"`.
- **Tiêu chí hoàn thành:** Nhánh đề xuất được tạo, file proposal được ghi nhận, mã nguồn lint sạch và push thành công.

---

## 🚀 Bước 6: Mở GitHub Pull Request & Vòng Lặp Self-Healing CI Dual-Gate
1. **Mở Pull Request qua GitHub CLI:**
   ```bash
   gh pr create --title "feat([scope]): [tên-đề-xuất]" --body "$PR_BODY" --base main --head "$BRANCH_NAME"
   ```
2. **Vòng lặp Dừng chờ & Tự làm xanh CI (Teamwork Autonomous CI Guard):**
   - Lắng nghe trạng thái qua `gh pr checks <PR_NUMBER>`.
   - Nếu CI Fail: Đọc log qua `gh run view <RUN_ID> --log-failed` $\rightarrow$ Tự động phân tích và sinh bản vá $\rightarrow$ Commit & push bản vá.
   - Lặp lại đến khi **100% CI Checks Tích Xanh** (`validate`, `scan`, `test matrix`, `lint`).
- **Tiêu chí hoàn thành:** Pull Request được mở và toàn bộ các checks CI đều tích xanh.

---

## 🔄 Bước 7: Báo Cáo & Closed-Loop Spoke Sync
1. Báo cáo URL Pull Request, trạng thái CI Tích Xanh và tóm tắt tính năng cho Maintainer.
2. Sẵn sàng cho lệnh `/ccba-contribute-to-hub [PR_NUMBER]` hoặc đồng bộ downstream khi PR được merge.
- **Tiêu chí hoàn thành:** Báo cáo hoàn tất gửi Maintainer kèm link PR và tóm tắt tính năng sẵn sàng review.

## Bộc Lộ Dần & Cấu Trúc Tinh Gọn (Progressive Disclosure)
* **Cấu trúc tài liệu Level 3:** Phân tách rõ ràng giữa quy trình cốt lõi và tài liệu hướng dẫn chuyên sâu qua bảng chỉ mục Level 3.
* **Tham chiếu liên kết:** Mọi tài liệu mở rộng tuân thủ cơ chế bộc lộ dần theo cấp độ (Level 1/2/3 Progressive Disclosure).
* **Chống rác dữ liệu (Anti-Debris Invariant):** Không để lại comment nháp, TODO tạm thời hay các chỉ thị thừa không cần thiết.
