# Walkthrough: PR #282 — Kernel Skill ccba-issue-tree & Cross-Skill Referral Hooks

## 1. Tổng Quan PR #282
- **Branch:** `feat/ccba-issue-tree-and-cross-referrals` $\rightarrow$ `main`
- **Tiêu đề:** `feat(skills): add ccba-issue-tree kernel skill and cross-skill referral hooks (#282)`
- **PR liên quan:** [PR #282](https://github.com/vvChu/ccba-agent-platform/pull/282)
- **Thể chế & Kiến trúc:** ADR-0035, ADR-0040, ADR-0047, ADR-0050, ADR-0057, ADR-0058, ADR-0059

---

## 2. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot (PR #282)

| ID / Review | Tệp Tin | Vấn Đề Copilot Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| `4033172362` | `.agents/skills/ccba-issue-tree/SKILL.md` | PR description states GPI = 14.50, but frontmatter shows raw sum S=4, K=2, A=1, P=1 (Total 8.0). Cần đồng bộ giá trị tính theo công thức trọng số ADR-0057. | **ĐÃ KHẮC PHỤC**: Đồng bộ toàn hệ thống. Đã cập nhật generator `compile_skills_docs.py` để tính điểm GPI có trọng số chuẩn xác: $S \times 2.5 + K \times 2.0 + A \times 2.0 - P \times 1.5 = 14.50$. |
| `4033172414` | `.agents/skills/ccba-issue-tree/references/governed_lifecycle_guide.md` | Tiêu đề ghi 5-State lifecycle machine nhưng bảng và sơ đồ định nghĩa 6 trạng thái (`UNVERIFIED`, `IN_INVESTIGATION`, `VERIFIED_FACT`, `FALSIFIED`, `DECISION_READY`, `COMMITTED`). | **ĐÃ KHẮC PHỤC**: Cập nhật tiêu đề và nội dung thành "6-State Lifecycle Machine" (Ma Trận Vòng Đời 6 Trạng Thái) đồng bộ trong cả `governed_lifecycle_guide.md` và `SKILL.md`. |
| `4033239718` | `packages/ccba-legal-intel/src/ccba_legal/federated_rag.py` | `rank-bm25` là dependency bắt buộc trong `pyproject.toml`, việc nuốt `ImportError` che giấu lỗi cấu hình môi trường. | **ĐÃ KHẮC PHỤC**: Bỏ `try...except ImportError`, import trực tiếp `from rank_bm25 import BM25Okapi` để fail-fast rõ ràng. |
| `4033501875` | `packages/ccba-legal-intel/src/ccba_legal/federated_rag.py` | Hardcode `timeout=2.0` có thể gây timeout trong môi trường thực tế khi gọi API embedding. | **ĐÃ KHẮC PHỤC**: Tham số hóa `embed_timeout: float | None = None` với giá trị mặc định an toàn 10.0s, đồng thời hỗ trợ biến môi trường cấu hình `CCBA_EMBED_TIMEOUT`. |
| `4033528975` | `scripts/governance/drift_auditor.py` | Fallback sang `git log -n 20` có thể lấy nhầm commit lịch sử không liên quan, che giấu drift thực tế. | **ĐÃ KHẮC PHỤC**: Loại bỏ fallback `-n 20`, chuyển sang kiểm tra tuần tự các ref so sánh nhánh hợp lệ (`origin/main..HEAD`, `origin/master..HEAD`, `main..HEAD`, `master..HEAD`). |
| `4033575070` | `docs/skills/ccba-issue-tree.md` | Điểm đánh giá GPI hiển thị `Tổng: 8.0` (tổng số học) thay vì điểm trọng số ADR-0057 (GPI = 14.50). | **ĐÃ KHẮC PHỤC**: Nâng cấp `compile_skills_docs.py` để tính điểm trọng số chuẩn ADR-0057, tái biên dịch toàn bộ 73 tài liệu kỹ năng, `INDEX.md`, `llms.txt`, `llms-full.txt`, và `index.html`. |

---

## 3. Các Thay Đổi Cốt Lõi

### 3.1 Đóng Gói Kỹ Năng Hạt Nhân `ccba-issue-tree` (Tier 2B Standalone Kernel Skill)
- **Phương pháp luận:** McKinsey MECE Issue Tree (Diagnostic Why-Tree, Solution How-Tree, Workplan What-Tree) tích hợp tầng vận hành Governed Lifecycle & RACI 11 Ghế CCBA.
- **Rào chắn:** ADR-0059 Verbatim Evidence Grounding, ADR-0058 Hard Completion Lock, ADR-0030 Context Budget Protection.
- **Cấu trúc tài liệu bộc lộ dần:**
  - `.agents/skills/ccba-issue-tree/SKILL.md`: Master skill definition.
  - `references/tree_templates.md`: Mẫu cây và sơ đồ Mermaid chi tiết.
  - `references/governed_lifecycle_guide.md`: Hướng dẫn vận hành 6 trạng thái vòng đời và ma trận bằng chứng.

### 3.2 Mạng Lưới 7 Cross-Skill Referral Hooks
Tích hợp móc nối điều hướng sang `/ccba-issue-tree` tại các điểm nút tư duy trọng yếu:
1. `ccba-diagnosing-bugs`: Pha 3 (Chẩn đoán lỗi phức tạp đa dịch vụ $\rightarrow$ Why-Tree).
2. `ccba-ai-qc`: Pha 3 (Xung đột kỹ thuật liên bộ môn & PCCC $\rightarrow$ Why-Tree + How-Tree).
3. `ccba-legal-advisor`: Bước 1/2 (Tranh chấp hợp đồng Cấp độ 3 $\rightarrow$ Why-Tree chuỗi trách nhiệm + How-Tree giải pháp hòa giải/VIAC).
4. `ccba-ask`: Bước 1 (Đầu mối tiếp nhận bài toán mở đa chiều $\rightarrow$ Issue Tree).
5. `ccba-grilling`: Nhánh A & Biên giới phòng thủ (Xung đột kiến trúc $\ge 2$ lựa chọn $\rightarrow$ How-Tree).
6. `bigbim-risk`: Bước 4 (Xung đột thông tin V2 & drift Unique ID $\rightarrow$ Why-Tree + How-Tree).
7. `ccba-to-spec`: Bước 3 (Bóc tách công việc Epic lớn $\rightarrow$ What-Tree 4 nhãn MECE: ANALYSIS, DECISION, COMMITMENT, SYNTHESIS).

---

## 4. Kết Quả Kiểm Thử & Kiểm Toán Tất Định (ADR-0058)

- **Local Verification:** `python -m ccba_harness verify-patch --preset ci` $\rightarrow$ ✅ 5/5 PASS (Exit Code 0).
- **Harness CI Gates:** `python scripts/eval/run_harness_evals.py --all` $\rightarrow$ ✅ 7/7 GATES PASS (Exit Code 0).
- **GitHub Actions CI (PR #282):**
  - `Lint Markdown`: ✅ PASS
  - `scan` (Security & Privacy): ✅ PASS
  - `validate` (Documentation Check): ✅ PASS
  - `Test - Python 3.10`: ✅ PASS (3m37s)
  - `Test - Python 3.11`: ✅ PASS (3m17s)
  - `Test - Python 3.12`: ✅ PASS (3m33s)
- **Copilot PR Review Audit:** ✅ PASS (100% các ý kiến được giải trình và giải quyết triệt để).

