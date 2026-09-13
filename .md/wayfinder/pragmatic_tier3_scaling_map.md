# 🗺️ Bản Đồ Định Hướng Wayfinder: Lộ Trình Tái Định Hình Tầng 3 (Pragmatic Strategic Scaling)

> **Mã định danh:** `WAYFINDER-MAP-TIER3-SCALING-2026`  
> **Căn cứ pháp lý & kỹ nghệ:** [ADR-0023](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0023-prompt-optimization-loop-and-regression-governance.md), [ADR-0030](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0030-progressive-disclosure-and-instruction-budget-optimization.md), [ADR-0044](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0044-spoke-hub-package-bootstrap-standard.md), [ADR-0045](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0045-hub-proposal-ingestion-governance.md), [ADR-0046](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0046-personal-sandbox-lifecycle-and-charter-2026-alignment.md), [ADR-0053](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0053-teamwork-multi-agent-orchestration-framework.md), [ADR-0057](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0057-two-stage-granularity-decision-framework-and-gpi.md), [ADR-0058](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0058-live-collaboration-artifacts-workspace-mirroring-and-charter-alignment.md), [RULE-1.7 & RULE-3.1](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/session_learnings.md).  
> **Phương pháp luận:** Wayfinding under "Fog of War" (Matt Pocock / Latent Space), Double-Pass Adversarial Review, KISS & Automation-First Quality.

---

## 1. Điểm Đích (Destination)

Đưa vào vận hành toàn diện hệ thống **Mở Rộng Tự Trị Thực Dụng (Pragmatic Strategic Scaling — Tầng 3)** cho CCBA Agent Platform, đạt được trạng thái hoàn thành tất định:
1. **Bộ Dữ Liệu Benchmark Chuẩn Khiết**: Thanh lọc 100% các prompt rác của lập trình viên / subagents (sửa Mypy, scan git secrets, phục hồi catalog) ra khỏi các tệp benchmark chuyên ngành ([`eval_pccc_audit.json`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-eval-gate/test_cases/eval_pccc_audit.json), [`eval_legal_intel.json`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-eval-gate/test_cases/eval_legal_intel.json)), thiết lập bộ đề thi chuyên môn sâu (QCVN 06:2022, Luật Xây dựng 2025, NĐ 105/2025/NĐ-CP).
2. **Chốt Chặn 30 Canonical Anchors & Deadband Hysteresis (ADR-0057)**: Thiết lập 30 tọa độ mỏ neo kiểm thử bất biến cho 3 phân tầng kiến trúc (Tier 1, Tier 2A, Tier 2B), kết hợp vùng đệm trễ $[11.5, 12.5]$ trong [`gpi.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/gpi.py) để ngăn chặn hiện tượng trôi dạt kiến trúc (Architectural Churn) khi mở rộng lên hàng trăm kỹ năng.
3. **Kiểm Thử Áp Lực Đa Tác Tử Trong CI (ADR-0053)**: Đóng gói kịch bản dogfood 3 Workers song song ([`run_qc_swarm_dogfood.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/governance/run_qc_swarm_dogfood.py)) thành bài kiểm thử định kỳ trong `ccba-harness`, phân định rõ ràng 8/10 Orchestrators là User Rituals tương tác (0 token nền) và bảo vệ Single-Writer Protocol.
4. **Công Cụ Đào Lỗi Cục Bộ Chống Rò Rỉ Dữ Liệu**: Tái cấu trúc cơ chế đọc log của [`log_eval_miner.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/eval/log_eval_miner.py) đúng cấu trúc thực tế, tích hợp 11 quy tắc lọc sâu của [`ccba-maskara`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-maskara/src/ccba_maskara/_rules.py), hoạt động độc lập ở chế độ ngoại tuyến cục bộ và cấm tự ý đẩy lên Hub.
5. **Dashboard Khuyếch Tán Tri Thức Spoke-Hub Bảo Vệ Hiến Pháp 11 Ghế (ADR-0045, ADR-0046)**: Nâng cấp [`cross_spoke_analytics.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/governance/cross_spoke_analytics.py) trực quan hóa công cụ tiềm năng từ các Spoke dự án, duy trì quy trình phê chuẩn có con người ký duyệt (QC Level 5) và cấm tuyệt đối auto-deprecate các kỹ năng nghiệp vụ chu kỳ dài.

---

## 2. Ghi Chú & Tri Thức Nền Tảng (Notes)

- **Nguyên tắc Hoạch định (Plan, don't do):** Bản đồ này dùng để chốt các câu hỏi thiết kế và cấu trúc kỹ nghệ của Tầng 3. Mọi công việc triển khai mã nguồn cụ thể chỉ bắt đầu sau khi ticket tại Biên giới (Frontier) được kích hoạt và gán assignee.
- **Ranh giới Hiến pháp (Constitutional Boundaries):**
  - **ADR-0045 & ADR-0046:** Tiếp nhận mã nguồn từ Spoke về Hub bắt buộc phải qua Cổng Cứng (`check_spoke_leakage.py`) và Cổng Mềm (`/ccba-review-proposal` do QC Level 5 phê chuẩn). Tuyệt đối không tự động hóa việc thăng hạng hoặc xóa kỹ năng.
  - **ADR-0058:** Khóa hoàn thành cứng yêu cầu mọi thay đổi phải đạt Exit Code = 0 từ kiểm chứng tất định máy tính (`pytest`, `mypy`, `ruff`). Không sử dụng các bài test synthetic do LLM tự sinh có tính ngẫu nhiên thống kê làm rào chắn CI.
  - **RULE-1.7 & Bảo mật Hợp đồng:** Tuyệt đối không lưu trữ hay tự động đẩy log hội thoại chứa bí mật dự toán, giải pháp kết cấu hoặc dữ liệu cá nhân của kỹ sư từ máy trạm lên Git Hub.

---

## 3. Quyết Định Đã Chốt (Decisions so far)

- **[Chốt qua Phản biện Đối kháng - 2026-09-13] Bác bỏ cơ chế Daemon tự động đẩy log máy trạm lên Hub (AS-1)**:
  - *Lý do:* Thư mục `~/.gemini/antigravity/brain` không chứa tệp `transcript.jsonl` mà chỉ chứa các bước text rời rạc. Dữ liệu của kỹ sư tư vấn chứa bí mật công trình dạng văn xuôi mà regex của Maskara không thể lọc triệt để. Tự động push lên Hub tạo ra rủi ro pháp lý vi phạm bảo mật nghiêm trọng.
- **[Chốt qua Phản biện Đối kháng - 2026-09-13] Bác bỏ Hồi quy Logistic trên 30 mẫu GPI; Giữ lại 30 Canonical Anchors (AS-2)**:
  - *Lý do:* Phân tầng kỹ năng (Tier 1/2A/2B) là công ước kiến trúc nhằm tối ưu ngân sách ngữ cảnh (ADR-0030). Áp dụng mô hình học máy trên 30 mẫu chủ quan sẽ gây bất ổn định (Architectural Churn). 100% (71/71) kỹ năng hiện tại đã vượt qua `--enforce-gpi`. Giải pháp chuẩn xác là khóa cứng 30 Ca Kiểm Chuẩn Tiêu Biểu (Anchors) trong Unit Test và bổ sung Vùng Đệm Trễ Deadband $[11.5, 12.5]$.
- **[Chốt qua Phản biện Đối kháng - 2026-09-13] Bác bỏ Nhà máy Benchmark Tự động của LLM (AS-3)**:
  - *Lý do:* Bài toán xây dựng/pháp lý đòi hỏi số liệu chính xác tuyệt đối. Dùng LLM tự sinh 320 bài test không có golden answer rồi tự chấm sẽ tạo ra bẫy ảo giác "tự khen nhau", tiêu tốn hơn 130 triệu tokens/tháng và vi phạm nguyên tắc kiểm chứng tất định của ADR-0058.
- **[Chốt qua Phản biện Đối kháng - 2026-09-13] Tái định vị 8/10 Orchestrators là User Rituals (AS-4)**:
  - *Lý do:* 8 Orchestrators có cờ `disable-model-invocation: true` là các hướng dẫn nghi thức tương tác giữa người và máy (0 token nền), không phải AI Swarms. Chỉ có 2 hệ thống Swarm thực thụ (`ccba-teamwork`, `ccba-ai-qc`).
- **[Chốt qua Phản biện Đối kháng - 2026-09-13] Bác bỏ tự động thăng hạng / khai tử kỹ năng Spoke-Hub (AS-5)**:
  - *Lý do:* Vi phạm Hiến pháp 11 Ghế CCBA Charter 2026 (ADR-0046). Các kỹ năng chu kỳ dài (nghiệm thu công trình 6–12 tháng/lần) sẽ bị xóa oan nếu áp dụng quy tắc 0-usage.

---

## 4. Ngoài Phạm Vi (Out of Scope)

1. **AI Synthetic Test Case Generator cho 64 kỹ năng ngoại vi**: Không xây dựng pipeline dùng LLM sinh hàng loạt bài test giả định; thay vào đó chỉ xây dựng bằng tay các bộ test có assertion xác định (Regex/Schema) cho Top 5 kỹ năng nòng cốt.
2. **Hồi quy Logistic / Tối ưu hóa số học tự động cho công thức GPI**: Giữ nguyên các hệ số chuẩn của ADR-0057, không đưa thuật toán ML vào tầng linter kiến trúc.
3. **Daemon tự động đồng bộ log qua Git/Network lên Server Spark**: Giữ nguyên tắc Single-Workstation Privacy: log cá nhân của kỹ sư chỉ được phân tích tại chỗ trên máy trạm khi có yêu cầu tường minh.
4. **Cơ chế tự động merge PR từ Spoke lên Hub và tự động gỡ bỏ kỹ năng (Auto-deprecate)**: Giữ nguyên quy trình kiểm duyệt có chữ ký con người (Human Approval Gate).

---

## 5. Sương Mù Chiến Trận / Chưa Xác Định Rõ (Not yet specified)

- **[Vùng mờ 1: Cơ chế Runtime Event Hook cho Antigravity IDE]**:
  - *Câu hỏi còn nằm trong sương mù:* Thay vì quét hậu kiểm (post-mortem mining) qua các thư mục log tạm sau khi kết thúc phiên, liệu có thể đăng ký một Lifecycle Hook tầng IDE (thông qua `scripts/hooks/` hoặc Antigravity Sidecar) để bắt trực tiếp sự kiện `TOOL_EXCEPTION` ngay tại thời điểm xảy ra và ghi vào file `.md/scratch/live_failures.jsonl`?
- **[Vùng mờ 2: Đo lường mức độ tương tác thực tế của User Rituals]**:
  - *Câu hỏi còn nằm trong sương mù:* Làm thế nào để thu thập dữ liệu định lượng về tần suất kỹ sư sử dụng 8 Lệnh Nghi thức (`/ccba-implement`, `/ccba-new-feature`, v.v.) khi cờ `disable-model-invocation: true` khiến chúng không phát sinh telemetry tool calls thông thường?

---

## 6. Danh Sách Tickets Định Hướng Chi Tiết (The Tickets)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        WAYFINDER DEPENDENCY GRAPH (TIER 3)                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [Ticket 1: Làm Sạch Evals] (DONE) ────► [Ticket 4: Tái Cấu Trúc Miner Cục Bộ]        │
│                                                   (DONE)                               │
│                                                                                        │
│   [Ticket 2: 30 GPI Anchors & Deadband] ──► [Ticket 5: Dashboard Spoke Tri Thức]      │
│                     (DONE)                                (Unblocked)                  │
│                                                                                        │
│   [Ticket 3: Dogfood Swarm vào CI] (DONE)                                              │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 🟣 [ĐÃ HOÀN THÀNH / CLOSED] [Ticket 1: Làm Sạch Ô Nhiễm Bộ Dữ Liệu Benchmark Evals Hiện Hữu](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-eval-gate/test_cases/eval_pccc_audit.json)
* **Loại công việc:** `Task [AFK]`
* **Người nhận việc (Assignee):** `DeepCoder`
* **Trạng thái:** **ĐÃ HOÀN THÀNH / CLOSED (2026-09-13)**
* **Mục tiêu đã giải quyết:**
  - Thanh lọc 100% các prompt rác của lập trình viên / subagents (sửa Mypy, scan git secrets, phục hồi catalog) ra khỏi hai tệp benchmark chuyên ngành [`eval_pccc_audit.json`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-eval-gate/test_cases/eval_pccc_audit.json) và [`eval_legal_intel.json`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-eval-gate/test_cases/eval_legal_intel.json).
  - Bổ sung 6 ca kiểm chuẩn PCCC chuyên sâu: Bậc chịu lửa nhà xưởng F5 Bảng H.3, hút khói hành lang Phụ lục D, khoảng cách thoát nạn hành lang cụt Bảng G.1/G.2, van ngăn cháy REI 150 Điều 4.14, buồng thang không nhiễm khói N1/N2 Điều 3.4.12, và khoảng cách đầu phun Sprinkler TCVN 3890:2023.
  - Bổ sung 6 ca kiểm chuẩn Pháp lý & Pháp điển chuẩn tắc: Thẩm quyền thẩm định dự án nhóm B Luật Xây dựng 2025 (Luật 135/2025/QH15), bãi bỏ cấp mới chứng chỉ QLDA & Định giá Điều 55 NĐ 212/2026/NĐ-CP, miễn chứng chỉ hành nghề, trình tự kiểm tra nghiệm thu NĐ 105/2025/NĐ-CP, quy định chuyển tiếp NĐ 217/2026/NĐ-CP, và giấy phép hoạt động nhà thầu nước ngoài.
  - Tích hợp từ điển ánh xạ bí danh kỹ năng `SKILL_DATASET_ALIASES` trong `ccba_harness.evals.runner` giúp các lệnh CLI (`--skill ccba-ai-qc-pccc-audit`, `--skill ccba-legal-advisor`, `--skill pccc_audit`) tự động định vị đúng tệp benchmark tương ứng mà không làm xáo trộn các bộ test redteam.
* **Kết quả kiểm chứng:**
  - 100% assertions xác định và độ dài hợp lệ.
  - `python -m ccba_harness verify-patch --preset eval` đạt PASSED (53/53 passed).
  - `python -m ccba_harness verify-patch --preset ci` đạt PASSED (5/5 commands, Exit Code 0).

---

### 🟣 [ĐÃ HOÀN THÀNH / CLOSED] [Ticket 2: Đóng Gói 30 Canonical GPI Anchors & Deadband Hysteresis Engine](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/gpi.py)
* **Loại công việc:** `Task [AFK]`
* **Người nhận việc (Assignee):** `DeepCoder`
* **Trạng thái:** **ĐÃ HOÀN THÀNH / CLOSED (2026-09-13)**
* **Mục tiêu đã giải quyết:**
  Tạo chốt chặn hồi quy kiến trúc bất biến cho chỉ số GPI ([ADR-0057](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0057-two-stage-granularity-decision-framework-and-gpi.md)), bảo đảm cấu trúc 71 kỹ năng không bị trôi dạt khi mở rộng.
* **Phạm vi tác động đã hoàn tất:**
  - **[packages/ccba-harness/src/ccba_harness/gpi.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/gpi.py):**
    - Bổ sung hằng số `GPI_DEADBAND_LOWER = 11.5` và `GPI_DEADBAND_UPPER = 12.5`.
    - Cập nhật `DecisionRequest` hỗ trợ `existing_tier` (chuẩn hóa enum/chuỗi) và `force_tier_flip`.
    - Bổ sung cơ chế `Deadband Hysteresis Engine` trong `evaluate_two_stage_decision`: Khi điểm số rơi vào vùng đệm trễ $[11.5, 12.5)$ và có `existing_tier` (Tier 2A hoặc Tier 2B), bảo lưu phân tầng cũ để triệt tiêu Architectural Churn. Chỉ lật tier khi có cờ `--force-tier-flip`.
    - Đóng gói cấu trúc `CANONICAL_ANCHORS` gồm 30 mỏ neo tiêu biểu bất biến (10 Tier 1 Deep Seams, 10 Tier 2A Progressive References, 10 Tier 2B Standalone Kernel Skills).
  - **[packages/ccba-harness/src/ccba_harness/cli.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/cli.py):**
    - Bổ sung cờ `--existing-tier` và `--force-tier-flip` cho `ccba-harness evaluate-gpi`.
    - Hiển thị trạng thái bảo lưu Hysteresis trên terminal và trong JSON output.
  - **[packages/ccba-harness/src/ccba_harness/skill_validator.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/skill_validator.py):**
    - Chuyển tiếp các tham số override cho Hysteresis trong `evaluate_skill_file`.
  - **[packages/ccba-harness/tests/test_gpi_decision_framework.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/tests/test_gpi_decision_framework.py):**
    - `test_30_canonical_anchors_invariants()`: Xác minh 100% 30 mỏ neo phân tầng chính xác.
    - `test_deadband_hysteresis_preserves_existing_tier()`: Kiểm tra điểm 11.5 bảo lưu Tier 2B; điểm 12.0 bảo lưu Tier 2A.
    - `test_deadband_hysteresis_force_tier_flip()`: Kiểm tra cờ lật tầng cưỡng chế hoạt động chính xác trong vùng đệm.
    - `test_deadband_hysteresis_outside_deadband_flips_normally()`: Kiểm tra ngoài vùng đệm phân tầng bình thường.
    - `test_cli_evaluate_gpi_deadband_and_force_flip()` & `test_skill_validator_evaluate_skill_file_with_hysteresis()`.
* **Kết quả kiểm chứng:**
  - 45/45 tests passed trong `test_gpi_decision_framework.py`.
  - 218/218 tests passed trong `packages/ccba-harness/tests/`.
  - `verify-patch --preset code --target packages/ccba-harness` đạt Exit Code 0 (Ruff + Mypy + Pytest).
  - `verify-patch --preset ci` đạt Exit Code 0 (5/5 commands passed).

---

### 🟣 [ĐÃ HOÀN THÀNH / CLOSED] [Ticket 3: Tích Hợp Kịch Bản Kiểm Thử Áp Lực 3 Workers Swarm Vào CI](file:///d:/GitHubProjects/ccba-agent-platform/tests/governance/test_swarm_dogfood_ci.py)
* **Loại công việc:** `Task [AFK]`
* **Người nhận việc (Assignee):** `DeepCoder`
* **Trạng thái:** **ĐÃ HOÀN THÀNH / CLOSED (2026-09-13)**
* **Mục tiêu đã giải quyết:**
  Đưa kịch bản dogfood đa tác tử thực tế vào bộ kiểm thử CI để bảo vệ Single-Writer Protocol ([ADR-0053](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0053-teamwork-multi-agent-orchestration-framework.md)) cho 2 hệ thống Swarm thực thụ (`ccba-teamwork` và `ccba-ai-qc`).
* **Phạm vi tác động đã hoàn tất:**
  - Đóng gói tệp kiểm thử chuyên sâu [`tests/governance/test_swarm_dogfood_ci.py`](file:///d:/GitHubProjects/ccba-agent-platform/tests/governance/test_swarm_dogfood_ci.py):
    - `test_3_worker_swarm_concurrent_clean_merge`: Mô phỏng 3 workers (Legal, MEP, Arch) ghi patch đồng thời vào `.system_generated/scratch/worker_{1,2,3}/`, Single-Writer nạp và gộp nguyên tử vào `report_registry.md`, xác minh zero-collision, dry-run passed, và verification passed trong $< 1.0$s.
    - `test_3_worker_swarm_syntactic_collision_rejection`: Phát hiện và từ chối va chạm dòng khi Worker 1 và Worker 2 cùng sửa đổi một vị trí mã nguồn, bảo vệ nguyên trạng đĩa.
    - `test_3_worker_swarm_semantic_conflict_atomic_rollback`: Bắt lỗi ngữ nghĩa khi kiểm tra verification thất bại và thực hiện phục hồi snapshot 100% trên toàn bộ các tệp đã sửa.
    - `test_load_patches_from_multi_worker_scratch`: Quét đệ quy toàn bộ thư mục scratch đa workers.
  - Cập nhật tài liệu kiến trúc [`docs/adr/0053-teamwork-multi-agent-orchestration-framework.md`](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0053-teamwork-multi-agent-orchestration-framework.md) (Mục 3.H) phân định ranh giới 2 nhóm Orchestrators: Multi-Agent Swarms (`ccba-ai-qc`, `ccba-teamwork`) vs 7 User Rituals tương tác (`disable-model-invocation: true`, 0 background tokens).
* **Kết quả kiểm chứng:**
  - `python -m pytest tests/governance/test_swarm_dogfood_ci.py -v` đạt **4/4 passed trong 0.82s** (đáp ứng tiêu chí $< 5.0$s).
  - `python -m ruff check tests/governance/test_swarm_dogfood_ci.py` đạt **All checks passed!**.
  - `python scripts/sync_hub_adr_matrix.py --check` đạt **PASS** (100% in sync).
  - `python -m ccba_harness verify-patch --preset ci` đạt **Exit Code 0** (5/5 commands passed).
* **Tiêu chí hoàn thành (Definition of Done):**
  - `python -m pytest tests/governance/test_swarm_dogfood_ci.py -v` pass trong $< 5.0$ giây.
  - Khóa hoàn thành cứng: `python -m ccba_harness verify-patch --preset ci` đạt Exit Code 0.

---

### 🟣 [ĐÃ HOÀN THÀNH / CLOSED] [Ticket 4: Tái Cấu Trúc log_eval_miner Đọc Cấu Trúc Log Cục Bộ & Tích Hợp ccba-maskara](file:///d:/GitHubProjects/ccba-agent-platform/scripts/eval/log_eval_miner.py)
* **Loại công việc:** `Task [AFK]`
* **Người nhận việc (Assignee):** `DeepCoder`
* **Trạng thái:** **ĐÃ HOÀN THÀNH / CLOSED (2026-09-13)**
* **Mục tiêu đã giải quyết:**
  Khắc phục ảo giác về file log trong `log_eval_miner.py`, đọc đúng cấu trúc nhật ký cục bộ, quét nông siêu tốc và sử dụng 11 rules của `ccba-maskara` thay cho 4 regex đơn sơ.
* **Phạm vi tác động đã hoàn tất:**
  - **[packages/ccba-maskara/src/ccba_maskara/__init__.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-maskara/src/ccba_maskara/__init__.py):**
    - Xuất khẩu `REGEX_PATTERNS` vào Public Deep Seam của `ccba_maskara`, bảo đảm tuân thủ hợp đồng kiến trúc cấm import private submodule `_rules.py` từ bên ngoài ([ADR-0030](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0030-progressive-disclosure-and-instruction-budget-optimization.md)).
  - **[scripts/eval/log_eval_miner.py](file:///d:/GitHubProjects/ccba-agent-platform/scripts/eval/log_eval_miner.py):**
    - Tích hợp 11 quy tắc bảo mật chuẩn Maskara (Anthropic, OpenAI, GitHub, AWS, Google, Slack, Stripe, JWT, Database URLs, Private Keys, Env Secrets) kết hợp quy tắc PII (Email, Phone, IP nội bộ) trong `redact_sensitive_info`.
    - Thay thế `os.walk` đệ quy toàn bộ thư mục bằng cơ chế tìm kiếm nông 1 cấp (`find_transcript_files` và `resolve_log_dir`): quét trực tiếp `<conv_id>/.system_generated/logs/transcript.jsonl` và `chats/session-*.json`, định vị 619 file logs chỉ trong 0.56 giây (loại bỏ hoàn toàn hiện tượng nghẽn I/O trên Windows NTFS).
    - Hỗ trợ xử lý phòng thủ cho cả định dạng JSON Lines (`.jsonl`) và JSON cấu trúc đối tượng (`session-*.json`).
    - Cập nhật `identify_failures`: Disclaimer từ chối lịch sự trên prompt ngoài phạm vi (`general_domain`) được xác định là **Hành Vi Đúng (Success)**, chỉ ghi nhận lỗi `ROUTER_DISCLAIMER` khi prompt thuộc phạm vi kỹ năng CCBA hợp lệ.
    - Bổ sung cờ an toàn `--dry-run`: xuất toàn bộ test cases vào `.md/scratch/eval_runs/` thay vì ghi đè vào test suite production, bảo vệ 100% tệp gốc.
  - **[scripts/tests/test_log_eval_miner.py](file:///d:/GitHubProjects/ccba-agent-platform/scripts/tests/test_log_eval_miner.py):**
    - Bổ sung 5 bài unit test mới bao phủ: Khử trùng 11 rules Maskara, xử lý Disclaimer out-of-scope, phát hiện Disclaimer in-scope, quét nông siêu tốc, và chế độ export an toàn `--dry-run`.
* **Kết quả kiểm chứng:**
  - `python -m pytest scripts/tests/test_log_eval_miner.py -v` đạt **27/27 passed trong 8.19s**.
  - `python -m ruff check scripts/eval/log_eval_miner.py scripts/tests/test_log_eval_miner.py` đạt **All checks passed!**.
  - Chạy thực nghiệm `python scripts/eval/log_eval_miner.py --dry-run` trực tiếp trên 619 log files máy trạm: bóc tách 2,603 tương tác, phát hiện 309 ca lỗi và xuất an toàn 162 mined cases vào `.md/scratch/eval_runs/` mà không gây biến động nào cho git repo.
  - Khóa hoàn thành cứng: `python -m ccba_harness verify-patch --preset ci` đạt **Exit Code 0** (5/5 commands passed).

---

### 🟢 [BIÊN GIỚI / UNBLOCKED] [Ticket 5: Nâng Cấp Dashboard Khuyếch Tán Tri Thức Spoke-Hub & Mẫu Biểu Đề Bạt](file:///d:/GitHubProjects/ccba-agent-platform/scripts/governance/cross_spoke_analytics.py)
* **Loại công việc:** `Prototype [HITL] / Research`
* **Người nhận việc (Assignee):** *Chưa gán (Unassigned)*
* **Trạng thái:** **MỞ / UNBLOCKED (Sẵn sàng triển khai - Chặn bởi Ticket 2 đã được giải phóng)**
* **Mục tiêu cần giải quyết:**
  Hỗ trợ khuyếch tán tri thức từ Spoke về Hub thông qua Dashboard quan sát trực quan và mẫu biểu đề xuất chuẩn tắc, tuân thủ Hiến pháp 11 Ghế CCBA Charter 2026 ([ADR-0045](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0045-hub-proposal-ingestion-governance.md), [ADR-0046](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0046-personal-sandbox-lifecycle-and-charter-2026-alignment.md)).
* **Phạm vi tác động:**
  - Nâng cấp [`scripts/governance/cross_spoke_analytics.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/governance/cross_spoke_analytics.py): bổ sung phân mục **"Top Spoke Innovations & Candidates for Hub Ingestion"** (gợi ý các module/script tại Spoke có tần suất sử dụng cao để kỹ sư xem xét).
  - Chuẩn hóa tài liệu hướng dẫn và mẫu biểu đề bạt `/ccba-propose-to-hub`, nhấn mạnh yêu cầu: Cổng Cứng (`check_spoke_leakage.py` pass 100%) và Cổng Mềm (Maintainer QC Level 5 phê chuẩn qua `/ccba-review-proposal`).
  - Ghi nhận nguyên tắc bất biến: cấm thuật toán tự ý khai tử các kỹ năng nghiệp vụ chu kỳ dài.
* **Tiêu chí hoàn thành (Definition of Done):**
  - `python scripts/governance/cross_spoke_analytics.py --render-markdown` xuất báo cáo trực quan đầy đủ.
  - Bản thảo hướng dẫn đề bạt tuân thủ 100% ADR-0045 và ADR-0046.
