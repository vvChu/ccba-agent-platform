# Walkthrough: PR #301 — Evaluator Architecture Evolution v2 (Generation 2 & 3 Evaluators)

## 1. Tổng Quan PR #301
- **Branch:** `feat/evaluator-architecture-evolution-v2` $\rightarrow$ `main`
- **Tiêu đề:** `feat(evals): implement evaluator architecture evolution v2 (TICKET-004 to TICKET-007)`
- **PR liên quan:** [PR #301](https://github.com/vvChu/ccba-agent-platform/pull/301)
- **Commit hợp nhất:** `858f9387` (Squash and merge)
- **Thể chế & Kiến trúc:** ADR-0058 (Hard Completion Lock), ADR-0059 (Legal Provenance Invariant), ADR-0057 (Two-Stage Governance), Wayfinder Map v2.0.0
- **Bất biến cốt lõi:** *"The Evaluator must be strictly smarter and more rigorous than the Optimizer."*

---

## 2. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot & Maintainer (PR #301)

| ID / Review | Tệp Tin | Vấn Đề Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| Review PR #301 | Toàn bộ PR #301 | Rà soát tự động GitHub Copilot | **HOÀN TOÀN SẠCH**: 0 pending review requests, 0 comments. |
| Audit Script | `audit_pr_comments.py` | Kiểm tra tự động các thay đổi và comments | **[OK]**: All Copilot reviews and comments on PR #301 are clean or resolved. |
| Ruleset Parity | `ci.yml` | Ràng buộc Ruleset #11593010 yêu cầu check `Deterministic Parity & Schema Audit` | **ĐÃ GIẢI QUYẾT**: Bổ sung job CI chuyên dụng `Deterministic Parity & Schema Audit` chạy `python -m ccba_harness verify-patch --preset ci`, đạt 100% Xanh. |
| Maintainer Gate | PR #301 | Phê duyệt hợp nhất và kích hoạt quy trình release | **ĐÃ PHÊ DUYỆT & MERGE**: Squash merge thành công vào `main` tại commit `858f9387`. |

---

## 3. Các Thay Đổi Cốt Lõi (Core Deliverables)

1. **`[TICKET-004]` Thẩm Định Tham Số Kỹ Thuật & PCCC (`PcccParametricScorer`):**
   - **Pluggable Two-Tier Architecture**:
     - *Tier 1 (Deterministic Schema Filter)*: 0 tokens, thực thi <1ms, cưỡng chế Dual Critical Hard Floor (Floor 1: Bẫy đảo ngược kết luận an toàn; Floor 2: Nhầm lẫn khái niệm kỹ thuật red-team).
     - *Tier 2 (Escalation LLM Judge)*: Kích hoạt khi qua Tier 1 để chấm điểm ngữ nghĩa chuyên sâu với graceful fallback.
   - **Mở rộng Dataset**: Bộ test case `eval_pccc_audit.json` được mở rộng lên 12 ca kiểm thử thực tế chuẩn QCVN 06:2022/BXD, QCVN 02:2020/BXD, TCVN 3890:2023.
   - **Routing Tự động**: Tích hợp vào `get_pccc_scorers()` và `TECH_QC_ARCHETYPE_KEYWORDS`.

2. **`[TICKET-006]` Động Cơ Phân Tách Thích Ứng & Nhiễu Động Tham Số (`AdaptiveDataSlicer` & `DynamicPerturbationEngine`):**
   - Module `ccba_harness.evals.slicing`:
     - Phân tầng thích ứng: Tier A ($N < 12$), Tier B ($12 \le N < 30$), Tier C ($N \ge 30$).
     - Động cơ nhiễu động số liệu tất định theo seed (`DynamicPerturbationEngine`) chống overfitting ngữ cảnh.
     - Phân tách holdout mù (Blinded Holdout Separation): Tách tự động 70% Tuning / 30% Holdout nhằm triệt tiêu hoàn toàn Goodhart's Law.
   - Tích hợp sâu vào `GitRatchetOptimizer`, `RatchetReport` và `NightlyTunerDaemon`.

3. **`[TICKET-005]` Xác Thực Phân Loại BIM & Tiêu Chuẩn Quốc Tế (`BimClassificationScorer`):**
   - Chỉ mục phẳng `uniclass_tables_flat.json`: 109 mã Uniclass được xác minh trên 7 bảng (`Co`, `En`, `SL`, `EF`, `Ss`, `Pr`, `PM`) kèm 5 bẫy chống gian lận (Anti-Traps).
   - Engine tra cứu in-memory <1ms (`uniclass_index.py`), xác thực cú pháp định danh ISO 19650 và IFC Alignment.
   - Chấm điểm đa chiều trực giao: Hợp lệ mã (0.4), Tầng đối tượng ISO 12006-2 (0.3), Cấu trúc định danh ISO 19650/IFC (0.3).

4. **`[TICKET-007]` Môi Trường Thực Thi Docker Buồng Kín (`DockerSandboxRunner` & `DockerSandboxScorer`):**
   - Cách ly buồng kín: Chạy kiểm thử mã nguồn trong container Docker tạm thời (`python:3.11-alpine`, `--network none`, RAM 256MB, CPU 1.0, timeout 15s).
   - Tự động fallback sang subprocess cô lập nếu Docker daemon không khả dụng.
   - Đánh giá khách quan theo mã thoát (exit code) và assertion của unit tests.

5. **Hoàn Thiện Kiến Trúc CI & Ruleset Parity:**
   - Bổ sung job `Deterministic Parity & Schema Audit` vào `.github/workflows/ci.yml`.
   - Toàn bộ 7/7 GitHub Actions checks đạt 100% Xanh.

---

## 4. Kết Quả Kiểm Thử Tự Động & Chứng Nhận Hoàn Tất (ADR-0058)

- **Đơn vị kiểm thử (Unit tests)**: 309 passed (6 skipped, 81 deselected) trong `ccba-harness` (0 regressions).
- **Hermetic Pre-release Gate**: 11/11 package suites passed trong `run_isolated_tests.py --all --stress`.
- **Harness CI Presets**: 100% PASS cho cả `code`, `eval`, `skill`, `ci`.
- **GitHub Actions CI (7/7 checks)**:
  - `CI/Deterministic Parity & Schema Audit`: ✅ SUCCESS (46s)
  - `CI/Test - Python 3.10`: ✅ SUCCESS (3m56s)
  - `CI/Test - Python 3.11`: ✅ SUCCESS (3m56s)
  - `CI/Test - Python 3.12`: ✅ SUCCESS (4m05s)
  - `CI/Lint Markdown`: ✅ SUCCESS (12s)
  - `Security & Privacy Scan`: ✅ SUCCESS (13s)
  - `Documentation Check/validate`: ✅ SUCCESS (28s)
