# 🗺️ BẢN ĐỒ ĐỊNH HƯỚNG: TIẾN HÓA BỘ ĐÁNH GIÁ ĐA BỘ MÔN (WAYFINDER MAP)
> **Mã định danh:** `WAYFINDER-EVALUATOR-EVOLUTION`  
> **Trạng thái:** HOÀN TẤT TOÀN BỘ GIAI ĐOẠN 1, 2, 3 (ALL TICKETS COMPLETED)  
> **Khởi tạo:** `2026-09-20` | **Phiên bản:** `2.0.0` (Hoàn thành TICKET-007 & Bộ Đánh Giá Thế Hệ 2/3)  
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
5. Bảo đảm Zero-Regression: Toàn bộ 309 passed (6 skipped, 81 deselected) tests của `ccba-harness` và CI Gates của 73 kỹ năng đạt PASS 100%.
6. Bảo đảm Độ Phủ Chuyên Môn Tuyệt Đối: Duy trì 100% Archetype Taxonomy Routing trên toàn bộ 73 kỹ năng (0 fallback).

---

## 📝 2. Ghi Chú (Notes)
- **Kỹ năng liên quan:** `/ccba-grilling`, `/ccba-implement`, `/ccba-tdd`, `/ccba-review-proposal`.
- **Hiến pháp đối chiếu:** [ADR-0030](../../../docs/adr/0030-progressive-disclosure-and-instruction-budget-optimization.md), [ADR-0045](../../../docs/adr/0045-hub-proposal-ingestion-governance.md), [ADR-0052](../../../docs/adr/0052-boost-deep-reasoning-protocol-and-escalation-gate.md), [ADR-0057](../../../docs/adr/0057-two-stage-granularity-decision-framework-and-gpi.md), [ADR-0058](../../../docs/adr/0058-live-collaboration-artifacts-workspace-mirroring-and-charter-alignment.md), [ADR-0059](../../../docs/adr/0059-legal-verbatim-grounding-and-mandatory-acquisition-invariant.md).
- **Nguyên tắc hành động:** *"Plan, don't do"* — mỗi ticket chỉ tập trung vào một quyết định kiến trúc hoặc một khối nghiệm thu khép kín. Không mở rộng phạm vi ra ngoài điểm đích.

---

## ✅ 3. Quyết Định Đã Chốt (Decisions So Far)

*   `[TICKET-000] [Dập tắt Goodhart's Law cho Coding Archetype]`: Đã triển khai `HardCompletionLockScorer` + Dual-Pillar `EngineeringDisciplineScorer`, cấm comment HTML rác và tạo dataset `eval_codebase_engineering.json` (Commit [`496a8d98`](https://github.com/vvChu/ccba-agent-platform/commit/496a8d98)).
*   `[TICKET-001] [Hệ thống Phòng thủ 4 Tầng cho Nightly Runner & Review Proposal]`: Đã triển khai Pre-PR Gate (`git diff -w`), rào cấm `RE_DEAD_WOOD` trong `audit_skills_hygiene.py` và Progressive Disclosure Level 3 Reference cho `ccba-review-proposal` (Commit [`6fbbdc9a`](https://github.com/vvChu/ccba-agent-platform/commit/6fbbdc9a)).
*   `[TICKET-002B] [Thay Thế Dòng 632 Bằng LeanStructuralScorer An Toàn]`: Đã xóa bỏ 4 regex quan liêu `(xử lý|hướng dẫn|thực hiện|quy định)`, thay thế bằng bộ chấm `get_lean_structural_scorers` (`ProgressiveDisclosureScorer` [0.4] + `LengthBoundsScorer` [0.3] + `AntiDebrisScorer` [0.3]), KHÔNG áp đặt điểm liệt critical hard floor, bảo vệ 46 non-coding skills. 261 passed, 6 skipped tests (Commit [`39e8a83f`](https://github.com/vvChu/ccba-agent-platform/commit/39e8a83f)).
*   `[TICKET-003A] [Biên Soạn Chỉ Mục Phẳng Legal Clauses Flat Index (~259 KB)]`: Đã biên dịch toàn diện 55 văn bản pháp luật, 19,724 statutory keys, và 24 replaces mappings vào `packages/ccba-harness/src/ccba_harness/evals/datasets/legal_clauses_flat.json`, tích hợp engine `load_legal_flat_index()` và CLI `compile_legal_flat_index.py`, bảo đảm 100% CI Parity. 265 passed, 6 skipped tests.
*   `[TICKET-003B] [Legal Verbatim Provenance Scorer Chuẩn ADR-0059]`: Đã triển khai `LegalVerbatimProvenanceScorer` và `get_legal_scorers()` (`legal_verbatim_provenance` [0.5, critical] + `progressive_disclosure_links` [0.2] + `anti_debris` [0.15] + `depth` [0.15]), cưỡng chế rào chắn Điểm Liệt (Anti-Trap Hard Floor & Zero-Hallucination Hard Floor: trích dẫn văn bản hết hiệu lực không có cảnh báo/thay thế, hoặc bịa đặt văn bản/điều luật $\rightarrow$ điểm 0.0 critical fail), kiểm chứng SHA-256 provenance đối soát trực tiếp từ `legal_clauses_flat.json` (Commit [`1cab6743`](https://github.com/vvChu/ccba-agent-platform/commit/1cab6743)). 272 passed, 6 skipped tests.
*   `[TICKET-002A] [Mở Rộng Archetype Routing Cho 73 Skills]`: Đã triển khai Taxonomy phân loại hoàn chỉnh cho 8 domain archetypes (Coding, Legal, Tech QC, BIM, Academic, Office, Visual, Orchestration) trong `tuner.py` và `daemon.py`. Xây dựng các scorers chuyên biệt `OfficeStandardScorer` (NĐ 30/2020) và `DiagramSyntaxScorer` (Mermaid/Excalidraw). Số lượng kỹ năng rơi vào bộ chấm fallback giảm từ 46 xuống 0/73 skills (đạt 100% độ phủ chuyên môn). Vượt qua 100% CI Gates (`verify-patch --preset code/eval/skill`) (Commit [`3a3d4025`](https://github.com/vvChu/ccba-agent-platform/commit/3a3d4025)).
*   `[TICKET-004] [PCCC & Technical QC Parametric Condition Scorer]`: Đã mở rộng `eval_pccc_audit.json` lên 12 test cases thực tế theo QCVN 06:2022/BXD, QCVN 02:2020/BXD và TCVN 3890:2023 với schema `parametric_rules`. Triển khai `PcccParametricScorer` với kiến trúc 2 tầng (Gate 1 Deterministic Schema Filter < 1ms, 0 token, Dual Critical Hard Floor cho kết luận đảo ngược an toàn & bẫy quan niệm kỹ thuật sai lệch; Gate 2 Advisory Escalation LLM Judge với cơ chế graceful fallback). Tích hợp vào `get_pccc_scorers()` và `tuner.py` cho `TECH_QC_ARCHETYPE_KEYWORDS`. Đạt 282 passed tests và 100% PASS trên tất cả presets (`code/eval/skill`).
*   `[TICKET-006] [Thiết Kế Cơ Chế Three-Tier Adaptive Slicing & Dynamic Perturbation]`: Đã triển khai module `slicing.py` hoàn chỉnh với `AdaptiveDataSlicer` và `DynamicPerturbationEngine` (FOG-001). Phân loại chính xác 3 cấp độ: Tier A ($N < 12$, 100% evaluation + dynamic perturbation chống học vẹt), Tier B ($12 \le N < 30$, phân tầng Stratified 70% Tuning / 30% Holdout), Tier C ($N \ge 30$, Blinded Multi-Seed Split). Tích hợp vào `GitRatchetOptimizer`, `RatchetReport` (bổ sung `slicing_tier`, `tuning_size`, `holdout_size`, `holdout_score`, `holdout_initial_score`) và `NightlyTunerDaemon`. 290 passed tests, 0 regressions trên 658 tests toàn sàn (Commit [`de4f4ad3`](https://github.com/vvChu/ccba-agent-platform/commit/de4f4ad3)).
*   `[TICKET-005] [Uniclass 200 & ISO 12006-2 Taxonomy Validator Cho BIM]`: Đã biên soạn chỉ mục phẳng `uniclass_tables_flat.json` (109 mã Uniclass chuẩn quốc tế qua 7 bảng Co, En, SL, EF, Ss, Pr, PM, 38 KB) và engine `uniclass_index.py` (<1ms in-memory lookup). Triển khai `BimClassificationScorer` và `get_bim_classification_scorers()` đánh giá đa chiều (Mã Uniclass & Bảng [0.4], Lớp ISO 12006-2 [0.3], Cú pháp ISO 19650 Container & IFC Alignment Linear [0.3]), tích hợp Anti-Trap Hard Floor (0.0 critical fail cho 5 bẫy kỹ thuật kinh điển). Định tuyến chính thức toàn bộ BIM/Classification/IFC/RASE/Governance skills. 299 passed tests, 100% PASS tất cả presets (Commit [`3b25e0e7`](https://github.com/vvChu/ccba-agent-platform/commit/3b25e0e7)).
*   `[TICKET-007] [Executable Docker Sandbox Evaluation Cho Coding Archetype]`: Đã triển khai module `sandbox.py` với `DockerSandboxRunner` và `DockerSandboxScorer`. Hỗ trợ chạy unit test thực tế trong ephemeral container cô lập (`python:3.11-alpine`, `--network none`, giới hạn RAM 256MB, CPU 1.0) kèm cơ chế tự động fallback sang localized subprocess sandbox nếu Docker daemon ngoại tuyến. Đạt 10/10 test cases sandbox mới và 309 passed tests toàn package `ccba-harness`, 100% PASS trên tất cả presets (`code/eval/skill`).

---

## ⚡ 4. Rìa Biên Giới & Các Ticket Hành Động (The Frontier Tickets)

*(Tất cả 8 Ticket thuộc Giai đoạn 1, Giai đoạn 2 và Giai đoạn 3 đã hoàn tất 100%.)*

---

## 🌫️ 5. Sương Mù Chiến Trận (Not Yet Specified)
*Nơi ghi nhận các ý tưởng nghiên cứu dài hạn tiếp theo:*

*   **[FOG-001] [Dynamic Parameter Perturbation]:** Đã giải quyết và tích hợp trong `[TICKET-006]` (`DynamicPerturbationEngine`).
*   **[FOG-002] [Adversarial LLM Judge Panel]:** Mô hình 2 thẩm phán LLM (Prosecutor vs Advocate) chấm điểm bài thi phi cấu trúc bằng Frontier Thinking Model. (Chờ đo lường chi phí token thực tế).
*   **[FOG-003] [Self-Escalating Red-Team Difficulty]:** Cơ chế tự động tăng độ khó của bộ đề khi điểm trung bình toàn hệ thống vượt 95%.

---

## 🚫 6. Ngoài Phạm Vi (Out of Scope)
*   Không huấn luyện lại (re-training / fine-tuning) các mô hình nền tảng trên Server Spark.
*   Không can thiệp vào định dạng lưu trữ văn bản gốc của Thư viện pháp luật (TVPL).
*   Không thay đổi kiến trúc Hub-Spoke Core Invariants đã quy định trong `AGENTS.md`.
