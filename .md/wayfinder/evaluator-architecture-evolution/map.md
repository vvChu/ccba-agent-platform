# 🗺️ BẢN ĐỒ ĐỊNH HƯỚNG: TIẾN HÓA BỘ ĐÁNH GIÁ ĐA BỘ MÔN (WAYFINDER MAP)
> **Mã định danh:** `WAYFINDER-EVALUATOR-EVOLUTION`  
> **Trạng thái:** ĐANG HOẠCH ĐỊNH & THỰC THI (ACTIVE)  
> **Khởi tạo:** `2026-09-20` | **Phiên bản:** `1.1.0` (Cập nhật sau Double-Pass Adversarial Audit)  
> **Phạm vi áp dụng:** Toàn bộ 73 Agent Skills & Nightly Auto-Tuner Daemon

---

## 🎯 1. Điểm Đích (Destination)

Xây dựng và hoàn thiện **Hệ thống Đánh giá Thế hệ 2 & 3 (Structured Semantic & Executable Evals)** cho toàn bộ 73 kỹ năng trên CCBA Platform, đảm bảo nguyên tắc bất biến:
> **"Bộ Đánh Giá (Evaluator) phải tuyệt đối thông minh và khắt khe hơn Bộ Tối Ưu (Optimizer)"**

**Tiêu chí hoàn thành định lượng:**
1. **Xóa sổ 100%** các bộ Scorer Fallback quan liêu đơn biến (dòng 632 trong `tuner.py`).
2. **100% kỹ năng cốt lõi (Core Archetypes)** có bộ chấm chuyên biệt đa trục trực giao (Dual/Multi-Pillar) kèm rào chắn Điểm Liệt (Critical Hard Floor).
3. Triển khai thành công **Legal Verbatim Provenance Scorer (ADR-0059)** đối soát trực tiếp với kho `legal_clauses_flat.json` (~261 KB, 267,526 bytes) đóng gói nội bộ package.
4. Triển khai cơ chế **Blinded Adaptive Holdout Split** có ngưỡng sàn kích thước mẫu và cơ chế Dynamic Parameter Perturbation ngăn chặn học vẹt đề thi.
5. Bảo đảm Zero-Regression: Toàn bộ 275 passed (6 skipped, 81 deselected) tests của `ccba-harness` và CI Gates của 73 kỹ năng đạt PASS 100%.
6. Bảo đảm Độ Phủ Chuyên Môn Tuyệt Đối: Duy trì 100% Archetype Taxonomy Routing trên toàn bộ 73 kỹ năng (0 fallback).

---

## 📝 2. Ghi Chú (Notes)
- **Kỹ năng liên quan:** `/ccba-grilling`, `/ccba-implement`, `/ccba-tdd`, `/ccba-review-proposal`.
- **Hiến pháp đối chiếu:** [ADR-0030](../../docs/adr/0030-progressive-disclosure-and-instruction-budget-optimization.md), [ADR-0045](../../docs/adr/0045-hub-proposal-ingestion-governance.md), [ADR-0052](../../docs/adr/0052-boost-deep-reasoning-plateau-escalation.md), [ADR-0057](../../docs/adr/0057-two-stage-granularity-decision-framework-and-gpi.md), [ADR-0058](../../docs/adr/0058-live-collaboration-artifacts-workspace-mirroring-and-charter-alignment.md), [ADR-0059](../../docs/adr/0059-legal-verbatim-grounding-and-mandatory-acquisition-invariant.md).
- **Nguyên tắc hành động:** *"Plan, don't do"* — mỗi ticket chỉ tập trung vào một quyết định kiến trúc hoặc một khối nghiệm thu khép kín. Không mở rộng phạm vi ra ngoài điểm đích.

---

## ✅ 3. Quyết Định Đã Chốt (Decisions So Far)

*   `[TICKET-000] [Dập tắt Goodhart's Law cho Coding Archetype]`: Đã triển khai `HardCompletionLockScorer` + Dual-Pillar `EngineeringDisciplineScorer`, cấm comment HTML rác và tạo dataset `eval_codebase_engineering.json` (Commit [`496a8d98`](https://github.com/vvChu/ccba-agent-platform/commit/496a8d98)).
*   `[TICKET-001] [Hệ thống Phòng thủ 4 Tầng cho Nightly Runner & Review Proposal]`: Đã triển khai Pre-PR Gate (`git diff -w`), rào cấm `RE_DEAD_WOOD` trong `audit_skills_hygiene.py` và Progressive Disclosure Level 3 Reference cho `ccba-review-proposal` (Commit [`6fbbdc9a`](https://github.com/vvChu/ccba-agent-platform/commit/6fbbdc9a)).
*   `[TICKET-002B] [Thay Thế Dòng 632 Bằng LeanStructuralScorer An Toàn]`: Đã xóa bỏ 4 regex quan liêu `(xử lý|hướng dẫn|thực hiện|quy định)`, thay thế bằng bộ chấm `get_lean_structural_scorers` (`ProgressiveDisclosureScorer` [0.4] + `LengthBoundsScorer` [0.3] + `AntiDebrisScorer` [0.3]), KHÔNG áp đặt điểm liệt critical hard floor, bảo vệ 46 non-coding skills. 261 passed, 6 skipped tests (Commit [`39e8a83f`](https://github.com/vvChu/ccba-agent-platform/commit/39e8a83f)).
*   `[TICKET-003A] [Biên Soạn Chỉ Mục Phẳng Legal Clauses Flat Index (~259 KB)]`: Đã biên dịch toàn diện 55 văn bản pháp luật, 19,724 statutory keys, và 24 replaces mappings vào `packages/ccba-harness/src/ccba_harness/evals/datasets/legal_clauses_flat.json`, tích hợp engine `load_legal_flat_index()` và CLI `compile_legal_flat_index.py`, bảo đảm 100% CI Parity. 265 passed, 6 skipped tests.
*   `[TICKET-003B] [Legal Verbatim Provenance Scorer Chuẩn ADR-0059]`: Đã triển khai `LegalVerbatimProvenanceScorer` và `get_legal_scorers()` (`legal_verbatim_provenance` [0.5, critical] + `progressive_disclosure_links` [0.2] + `anti_debris` [0.15] + `depth` [0.15]), cưỡng chế rào chắn Điểm Liệt (Anti-Trap Hard Floor & Zero-Hallucination Hard Floor: trích dẫn văn bản hết hiệu lực không có cảnh báo/thay thế, hoặc bịa đặt văn bản/điều luật $\rightarrow$ điểm 0.0 critical fail), kiểm chứng SHA-256 provenance đối soát trực tiếp từ `legal_clauses_flat.json` (Commit [`1cab6743`](https://github.com/vvChu/ccba-agent-platform/commit/1cab6743)). 272 passed, 6 skipped tests.
*   `[TICKET-002A] [Mở Rộng Archetype Routing Cho 73 Skills]`: Đã triển khai Taxonomy phân loại hoàn chỉnh cho 8 domain archetypes (Coding, Legal, Tech QC, BIM, Academic, Office, Visual, Orchestration) trong `tuner.py` và `daemon.py`. Xây dựng các scorers chuyên biệt `OfficeStandardScorer` (NĐ 30/2020) và `DiagramSyntaxScorer` (Mermaid/Excalidraw). Số lượng kỹ năng rơi vào bộ chấm fallback giảm từ 46 xuống 0/73 skills (đạt 100% độ phủ chuyên môn). Vượt qua 100% CI Gates (`verify-patch --preset code/eval/skill`) (Commit [`3a3d4025`](https://github.com/vvChu/ccba-agent-platform/commit/3a3d4025)).

---

## ⚡ 4. Rìa Biên Giới & Các Ticket Hành Động (The Frontier Tickets)

Các ticket mở, không bị phụ thuộc, sẵn sàng giải quyết ngay theo thứ tự ưu tiên:

---

### 🟡 GIAI ĐOẠN 2 (P1: Nâng Cấp Kỹ Thuật Xây Dựng, PCCC & BIM)

*   **`[TICKET-004]` [PCCC & Technical QC Parametric Condition Scorer] [Task - Co-Design Blueprint]**
    - **Mục tiêu:** 
      1. Triển khai `PcccParametricScorer` theo Kiến Trúc Phân Tầng Tách Rời (Decoupled Pluggable Two-Tier):
         - **Gate 1 (Deterministic Schema Filter - Primary Default):** Phân tích cú pháp tham số kỹ thuật, đối soát trực tiếp `parametric_rules` trong metadata (Expected Verdict, Required Parameters, Forbidden Anti-Trap Parameters, Legal Basis QCVN 06:2022/BXD) với cơ chế Điểm Liệt Kép (Critical Hard Floor), chạy < 1ms, 0 token LLM, 100% CI Parity (ADR-0058).
         - **Gate 2 (Escalation LLM Judge - Advisory Plugin):** Mặc định `escalation_judge=None`. Được cung cấp dưới dạng plugin phúc thẩm độc lập phục vụ kiểm toán ngoại tuyến hoặc chẩn đoán suy luận sâu khi kỹ năng bị kẹt bế tắc ([ADR-0052](../../docs/adr/0052-boost-deep-reasoning-plateau-escalation.md)), không chạy trong vòng lặp Nightly Ratchet tự động nhằm tránh nghẽn token.
      2. Mở rộng `eval_pccc_audit.json` từ 6 lên 12 test cases tham số kỹ thuật thực tế theo QCVN 06:2022/BXD (Bậc chịu lửa, Hút khói hành lang, Khoảng cách thoát nạn, Bơm PCCC, Khoang ngăn cháy). Bảo toàn nguyên vẹn tính đối kháng của `eval_pccc_audit_redteam.json`.
    - **Trạng thái:** 🟢 READY (Đã chốt thiết kế qua Grilling & Adversarial Audit)
    - **Assignee:** Unassigned

*   **`[TICKET-005]` [Uniclass 200 & ISO 12006-2 Taxonomy Validator Cho BIM] [Research - AFK]**
    - **Mục tiêu:** Khảo sát, thu thập nguồn dữ liệu chính thức và biên soạn bảng mã phân loại Uniclass 200 (Co, En, SL, EF, Ss, Pr, PM) vào `uniclass_tables_flat.json`, tích hợp vào `BimClassificationScorer` kiểm tra tính khớp nối thực thể và mã gán.
    - **Trạng thái:** 🟢 READY (Unblocked - Domain routing độc lập tại `tuner.py:650`)
    - **Assignee:** Unassigned

*   **`[TICKET-006]` [Thiết Kế Cơ Chế Three-Tier Adaptive Slicing & Dynamic Perturbation] [Research & Task - AFK]**
    - **Mục tiêu:** Thiết kế cấu trúc phân tách dữ liệu kiểm thử trong `daemon.py` và `tuner.py` theo mô hình Phân Tầng Ba Cấp (Three-Tier Adaptive Slicing):
      - **Tier A ($N < 12$ cases):** Giữ 100% bộ đề kiểm định, kích hoạt **Dynamic Parameter Perturbation (FOG-001)** hoán đổi ngẫu nhiên các số liệu hình học để chống học vẹt context.
      - **Tier B ($12 \le N < 30$ cases):** Phân tách phân tầng **Stratified 70% Tuning / 30% Holdout** (bảo đảm tập Tuning luôn có từ 8 đến 21 câu hỏi định hướng đột biến).
      - **Tier C ($N \ge 30$ cases):** Kích hoạt **Blinded Multi-Seed Split** (50/50 hoặc 70/30).
    - **Trạng thái:** 🟢 READY (Đã hoàn thiện thiết kế toán học)
    - **Assignee:** Unassigned

---

### 🔵 GIAI ĐOẠN 3 (P2: Executable Evals & Sandbox Cô Lập)

*   **`[TICKET-007]` [Executable Docker Sandbox Evaluation Cho Coding Archetype] [Prototype - HITL]**
    - **Mục tiêu:** Xây dựng mẫu thử chạy `pytest` thật trong ephemeral container cô lập để chấm điểm trực tiếp code sinh ra bởi Agent.
    - **Trạng thái:** 🟡 BLOCKED bởi `[TICKET-006]`
    - **Assignee:** Unassigned

---

## 🌫️ 5. Sương Mù Chiến Trận (Not Yet Specified)
*Nơi ghi nhận các ý tưởng dự kiến nhưng chưa đủ sắc nét để tạo ticket:*

*   **[FOG-001] [Dynamic Parameter Perturbation]:** Cơ chế xáo trộn tự động các thông số hình học/số liệu trong đề thi mỗi đêm để chống học vẹt context. (Cần giải quyết xong `[TICKET-006]` mới rõ dạng).
*   **[FOG-002] [Adversarial LLM Judge Panel]:** Mô hình 2 thẩm phán LLM (Prosecutor vs Advocate) chấm điểm bài thi phi cấu trúc bằng Frontier Thinking Model. (Chờ đo lường chi phí token thực tế).
*   **[FOG-003] [Self-Escalating Red-Team Difficulty]:** Cơ chế tự động tăng độ khó của bộ đề khi điểm trung bình toàn hệ thống vượt 95%.

---

## 🚫 6. Ngoài Phạm Vi (Out of Scope)
*   Không huấn luyện lại (re-training / fine-tuning) các mô hình nền tảng trên Server Spark.
*   Không can thiệp vào định dạng lưu trữ văn bản gốc của Thư viện pháp luật (TVPL).
*   Không thay đổi kiến trúc Hub-Spoke Core Invariants đã quy định trong `AGENTS.md`.
