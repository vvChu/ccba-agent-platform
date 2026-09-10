# 🗺️ Bản đồ Định hướng Wayfinder: Lộ Trình Nâng Cấp Toàn Diện Hệ Sinh Thái Kỹ Năng ccba-*

> **Tài liệu tham chiếu & Nền tảng**:
> - [ADR-0030: Instruction Token Budget & Token Budget Governance](../../knowledge/adr/adr-0030.md)
> - [ADR-0035: Deep Modules & Thin Seams Hierarchy](../../knowledge/adr/adr-0035.md)
> - [ADR-0053: Teamwork Multi-Agent Protocol & Single-Writer Coordination](../../knowledge/adr/adr-0053.md)
> - [ADR-0057: Two-Stage Decision Framework for Skill Granularity & Governance](../../knowledge/adr/adr-0057.md)
> - [Skill Authoring Guide: Multi-Mode Standard & Reference Deduplication](../../knowledge/guides/skill_authoring_guide.md)
> - [Latent Space: The /wayfinder Skill: Navigating the “Fog of War” of Planning (Matt Pocock)](https://www.latent.space/p/wayfinder-skill)
> - **Industry Benchmarks**: Claude Code Verification Loops, SWE-bench Evaluator Harness, Letta/MemGPT Memory Compaction, Devin/Cursor Single-Writer Structured Patches.

---

## 1. Điểm đích (Destination)

Toàn bộ **67 kỹ năng và các orchestrators** trong hệ sinh thái **CCBA Agent Services Platform** được nâng cấp toàn diện lên thế hệ kiến trúc tự chủ cấp công nghiệp (Autonomous Agentic Platform v2.0), đạt các tiêu chuẩn bất biến sau:

1. **Exit-Code Deterministic Verification Gate**:
   - Chấm dứt hoàn toàn hiện tượng Agent tự nhận hoàn thành công việc (Premature Completion / Self-Certification). Mọi tiêu chí hoàn thành trong `SKILL.md` được hỗ trợ hoặc bắt buộc đối soát bằng **CLI Exit Codes** (`pytest`, `ruff`, `mypy`, `ccba-harness verify-patch`). Nếu Exit Code $\ne 0$, cấm tuyệt đối Agent kết luận thành công.
2. **Zero Script Bloat Ngoài Packages (Tuân thủ Triệt để Cổng 0 ADR-0057)**:
   - Toàn bộ **105 scripts tự do (35,680 LOC)** hiện đang rải rác bên trong thư mục `scripts/` của 14 skills được di trú hoàn toàn vào các **Deep Seams** của `packages/*/src/` với tỷ lệ kiểm thử unit test $\ge 90\%$. Kỹ năng `SKILL.md` chỉ đóng vai trò hướng dẫn orchestrate và gọi CLI/API, không chứa code logic nghiệp vụ trần.
3. **Bộ Nén Tri Thức Phiên Tự Động (Session Memory Compaction Engine)**:
   - Tài liệu bộ nhớ phiên `.md/knowledge/session_learnings.md` được nén định kỳ và tự động từ **38 KB (~9,500 tokens)** xuống **$\le 10\text{ KB}$**, loại bỏ hiện tượng pha loãng chú ý (Attention Dilution) khi khởi động bất kỳ phiên Agent mới nào mà vẫn bảo toàn 100% các quy tắc cốt lõi đã học được.
4. **Giao Thức Single-Writer & Structured Diff Patch Cho Multi-Agent (ADR-0053)**:
   - Các Worker Agents trong nhóm (`ccba-teamwork`) hoạt động theo nguyên tắc **No Pre-mutation**: tuyệt đối không ghi trực tiếp vào codebase. Toàn bộ đề xuất thay đổi được đóng gói dưới dạng **Unified Diff / Structured Patch** lưu tạm tại `.system_generated/scratch/`. **Lead Orchestrator** là thực thể duy nhất (Single-Writer) thẩm tra xung đột và thực hiện atomic patch.
5. **Cộng Tác Dựa Trên Artifacts & Cổng Phê Duyệt Tương Tác (HITL Gates)**:
   - Mọi trạng thái làm việc phức tạp hoặc kế hoạch đa bước bắt buộc thể hiện qua **Native Antigravity Artifacts** (`RequestFeedback: true`), tích hợp trực tiếp với cơ chế phê duyệt của Hội đồng Thẩm định 11 Ghế CCBA Charter (ADR-0046).
6. **Vận Hành Tự Chủ Doanh Nghiệp & Tối Ưu Hóa Chi Phí Thực Tế (Phase 4: Beyond Horizon)**:
   - Tối ưu hóa chi phí token qua Prompt Density Index (PDI), di trú nốt 28 core scripts còn lại theo Cổng 0 ADR-0057, truyền phát telemetry trực tiếp theo thời gian thực tới Server Spark, và kích hoạt động cơ tự sửa lỗi (Autonomous Self-Healing Loop) khi gặp kiểm định thất bại.

---

## 2. Ghi chú & Tri thức Nền tảng (Notes)

- **Triết lý "Plan, Don't Do" của Wayfinder**:
  - Bản đồ này tập trung vào việc **ra quyết định (decisions)**, xác lập ranh giới kiến trúc và giải mã các vùng sương mù (Fog of War) trước khi viết mã quy mô lớn.
  - Các ticket được chia thành các đơn vị công việc độc lập (~100K token budget/session).
- **Quy tắc Tuân thủ Toàn cục (User Global Rules)**:
  - **Rule 1**: Toàn bộ tài liệu trung gian, bản đồ, spec và artifacts bắt buộc lưu trữ trong thư mục `.\.md\`. Tuyệt đối không lưu rải rác ngoài Project Root.
  - **Rule 4**: Thực hiện theo cơ chế Planning Mode Approval; ưu tiên tái sử dụng (Reuse-First Gate) qua `catalog.yaml`.
  - **Rule 8**: Mọi đề xuất kiến trúc phải trải qua 2 vòng kiểm chứng (Code-First Research & Self-Adversarial Review).
- **Bộ Công Cụ & Thư Viện Nòng Cốt**:
  - `packages/ccba-harness/`: Module cốt lõi chịu trách nhiệm làm Verification Harness và Skill Validator.
  - `packages/ccba-ai/`: Cổng giao tiếp duy nhất với LiteLLM Gateway trên Server Spark.
  - `scripts/governance/`: Các công cụ kiểm soát chất lượng mã nguồn và tính toàn vẹn của nền tảng.

---

## 3. Quyết định Đã Chốt (Decisions so far)

- **[Đã chốt - 2026-09-09] Thẩm tra & Kiểm định Thực chứng 5 Trụ cột Nâng cấp qua `/boost`**:
  - Đã quét thực tế toàn bộ Monorepo: xác nhận 105 loose scripts (35,680 dòng code) trong 14 skills đang vi phạm Cổng 0 ADR-0057; xác nhận `session_learnings.md` đạt 38 KB (9.5K tokens) gây lãng phí ~10% ngữ cảnh mỗi lượt prompt; xác nhận race condition khi nhiều Worker ghi đồng thời vào file mã nguồn.
  - Chi tiết tại Artifact: [learning_proposal.md](file:///C:/Users/chuvu/.gemini/antigravity/brain/ea5a900e-41fd-4ae6-968a-e2e271e67e52/learning_proposal.md).
- **[Đã chốt - 2026-09-09] Đối sánh Chuẩn Công nghiệp & Best Practices qua `/browser`**:
  - Khảo sát Anthropic Claude Code, OpenAI SWE-bench, Devin, Cursor, Aider và Letta/MemGPT.
  - Chốt áp dụng mô hình **Dual-Verification Gate**: Lớp 1 dùng Deterministic CLI Exit Code (nhanh, 0 token, 100% tin cậy); Lớp 2 chỉ spawn Critic/Auditor Agent khi bài toán có độ mơ hồ ngữ nghĩa hoặc thẩm định thiết kế UI/Architecture.
  - Chốt mô hình **Worker Structured Diff Patch** kết hợp **Orchestrator Single-Writer** nhằm loại bỏ xung đột ghi đè tệp.
- **[Đã chốt - 2026-09-09] Tái cấu trúc Chuẩn mực Hình mẫu Kỹ năng `ccba-xia` (Commit `d15a3dfa`)**:
  - Khắc phục lỗi Premature Completion tại Phase 3 và Phase 6, cập nhật tiêu chí hoàn thành có thể kiểm chứng máy tính.
  - Chuẩn hóa GPI $A=1.0$ (tổng điểm $GPI = 16.5 \ge 12.0$), khử hoàn toàn các đoạn văn trùng lặp trong `MODES.md`, dọn dẹp file zombie backup, 100% unit tests và governance tests vượt qua.
- **[Đã chốt - 2026-09-09] Thể chế hóa Tiêu chuẩn Thiết kế Kỹ năng vào Cẩm nang Nền tảng (Commit `8867a540`)**:
  - Bổ sung 2 chương quy phạm vào `skill_authoring_guide.md`: (1) Tiêu chuẩn thiết kế kỹ năng đa chế độ (Multi-Mode Skill Criteria) và (2) Quy tắc tham chiếu không trùng lặp (DRY Reference Rule).
  - Ban hành 6 tiêu chuẩn thiết kế tài liệu `MODES.md` cho toàn bộ các kỹ năng tiếp theo.
- **[Đã chốt - 2026-09-10] Hoàn thành Khảo sát & Ma trận Ánh xạ Di trú Scripts (Ticket 3 - Double-Pass Review)**:
  - Khảo sát thực tế đo lường (`[đo thực tế]`): Chỉ có **11 skills** chứa `scripts/` với **52 files (9,909 LOC)**.
  - Phân loại: **17 files** đã là Thin Adapters; **35 files** chứa Core Logic cần di trú.
  - Thống nhất đề xuất thành lập package mới `packages/ccba-qc-core` cho mảng Thẩm tra Đa bộ môn (`ccba-ai-qc` & `ccba-ai-qc-pccc-audit`), đưa `eval_runner.py` về `packages/ccba-harness`, hợp nhất OOXML vào `packages/ccba-ooxml`, và mở rộng `packages/ccba-pdf-prep`.
  - Chi tiết tại Manifest: [scripts_migration_manifest.md](../../knowledge/scripts_migration_manifest.md).
- **[Đã chốt - 2026-09-10] Triển khai Memory Compaction Engine & Nén session_learnings.md (Ticket 1)**:
  - Xây dựng thành công CLI `scripts/governance/compact_session_learnings.py` hỗ trợ `--stats`, `--check`, `--compact`.
  - Nén tệp `session_learnings.md` từ **38,033 bytes (37.14 KB) về 8,761 bytes (8.56 KB)**, đạt mức giảm **77.0%** (tiết kiệm ~7,300 tokens cho mọi phiên Agent khởi tạo).
  - Bảo toàn 100% bản gốc lịch sử tại [`.md/knowledge/archive/session_learnings_history.md`](../../knowledge/archive/session_learnings_history.md).
  - Bộ kiểm thử `tests/governance/test_compact_session_learnings.py` đạt 7/7 PASS (100% test suite monorepo đạt 81 passed).
- **[Đã chốt - 2026-09-10] Nâng cấp ccba-harness verify-patch với Exit-Code Gate (Ticket 2)**:
  - Đóng gói module `packages/ccba-harness/src/ccba_harness/verifier.py` (`CommandResult`, `PatchVerificationReport`, `verify_patch_execution()`).
  - Bổ sung subcommand CLI `ccba-harness verify-patch` với các flags: `-c / --cmd / --commands`, `--file`, `--timeout`, `--cwd`, `--json`, `--report-file`, `--fail-fast`.
  - Bộ kiểm thử `packages/ccba-harness/tests/test_verify_patch.py` đạt 12/12 PASS (toàn bộ 141 tests trong `ccba-harness` đạt 100% PASS).
  - Thiết lập rào chắn kiểm thử xác định khách quan, chặn đứng hoàn toàn Premature Completion & Self-Certification.
- **[Đã chốt - 2026-09-10] Thiết kế Giao thức Structured Diff Patch & Single-Writer Engine (Ticket 4)**:
  - Ban hành tài liệu đặc tả kỹ thuật: [`.md/knowledge/specs/spec-structured-diff-protocol.md`](../../knowledge/specs/spec-structured-diff-protocol.md) chuẩn hóa format Search-Replace block, JSON manifest, Unified Diff, và quy tắc No Pre-mutation cho Worker Sub-agents.
  - Xây dựng thành công Single-Writer Engine [`scripts/governance/apply_worker_patch.py`](../../../../scripts/governance/apply_worker_patch.py) hỗ trợ phát hiện xung đột (`--check-conflicts`), dry-run ảo hóa (`--dry-run`), áp dụng nguyên tử (`--apply`) kèm snapshot và auto-rollback khôi phục trạng thái gốc nếu verification gate thất bại.
  - Bộ kiểm thử [`tests/governance/test_apply_worker_patch.py`](../../../../tests/governance/test_apply_worker_patch.py) đạt 10/10 PASS (full governance suite đạt 91 passed).
  - Unblock Ticket F3 trong khu vực sương mù.
- **[Đã chốt - 2026-09-10] Phỏng vấn Socratic Grilling & Ban hành ADR-0058 Live Collaboration Artifacts (Ticket 5)**:
  - Hoàn tất 4 vòng phỏng vấn chuyên sâu `/ccba-grilling` cùng Kỹ sư trưởng, lập biên bản tại [`.md/knowledge/grilling_live_artifacts_and_charter.md`](../../knowledge/grilling_live_artifacts_and_charter.md).
  - Thể chế hóa chính thức bằng [**ADR-0058**](../../../docs/adr/0058-live-collaboration-artifacts-workspace-mirroring-and-charter-alignment.md):
    1. Kiến trúc Transient Buffer trong `brain/` kết hợp Final Snapshot Mirroring vào `.\.md\reports/` hoặc `.\.md/knowledge/`.
    2. Chuẩn mực Bộ ba Artifacts (Trio Core Artifacts): `implementation_plan.md`, `walkthrough.md`, `task_dashboard.md` (chỉ khi multi-agent swarm), tích hợp nội khối đề mục `## CCBA Charter Governance & QC Matrix`.
    3. Phân quyền thích ứng 11 Ghế CCBA Charter: Khóa cứng trần QC Level 1 + Watermark `[CCBA SANDBOX DRAFT]` cho Spoke Cá nhân; kích hoạt đúng Ghế chịu trách nhiệm cho Spoke Dự án chính thức.
    4. Bắt buộc nhúng Báo cáo Thẩm tra Khách quan từ `ccba-harness verify-patch` và Khóa hoàn thành cứng (Hard Completion Lock) nếu Exit Code $\ne 0$.
- **[Đã chốt - 2026-09-10] Thành lập packages/ccba-qc-core & Di trú 35 QC Scripts (Ticket F1)**:
  - Khởi tạo package chuyên trách mới `packages/ccba-qc-core` đạt chuẩn Deep Seam (ADR-0035, ADR-0057 Gate 0).
  - Tách bạch và đóng gói toàn bộ logic cốt lõi thành 6 modules chuyên trách:
    1. `discovery.py` (`DiscoveryEngine`, `SheetEntry`, `ProjectBackbone`, `_normalize_vn` chuẩn hóa NFD).
    2. `quadview.py` (`QuadViewAuditEngine`, `_parse_audit_response`).
    3. `semantic.py` (`SemanticAuditEngine`).
    4. `reporter.py` (`ReporterEngine`).
    5. `pccc.py` (`PcccMapReduceEngine`).
    6. `pipeline.py` (`QCBatchOrchestrator`).
    7. `cli.py` (Giao diện dòng lệnh Typer `ccba-qc` với các subcommands: `discover`, `audit`, `batch`, `pccc`).
  - Chuyển đổi 6 loose scripts trong `.agents/skills/ccba-ai-qc/scripts/` và `ccba-ai-qc-pccc-audit/scripts/` thành Thin Adapters ủy nhiệm 100% logic vào `ccba-qc-core`.
  - Bộ unit test `packages/ccba-qc-core/tests/test_qc_core.py` đạt 6/6 PASS, strict mypy 0 issues, ruff format 0 errors.
  - Vượt qua kiểm định phụ thuộc kiến trúc `tests/governance/test_dependency_contracts.py` (6/6 PASS) và toàn bộ 4/4 rào chắn của `ccba-harness verify-patch`.
- **[Đã chốt - 2026-09-10] Tích hợp verify-patch Loop Tự động cho Toàn bộ Kỹ năng (Ticket F2)**:
  - Nâng cấp `ccba-harness verifier.py` và CLI hỗ trợ các **Verification Presets** một chạm: `--preset code`, `--preset doc <target>`, `--preset skill <target>`, `--preset adr`, kèm subcommand mới `ccba-harness verify-doc`.
  - Giải quyết triệt để bài toán kiểm thử cho kỹ năng định tính (Qualitative Skills như `ccba-legal-advisor`, `ccba-completion-checklist`) bằng cách đóng gói các bất biến xác định: kiểm tra sự tồn tại tệp vật lý, dung lượng tối thiểu $\ge \text{min\_bytes}$, kiểm tra cấu trúc headings bắt buộc và zero broken markdown links.
  - Thể chế hóa vào Hiến pháp Nền tảng Layer 1 (`AGENTS.md` và `.agents/AGENTS.md`): Cập nhật điều khoản cốt lõi **Deterministic Hard Completion Lock (ADR-0058)** cấm Agent tự nhận hoàn thành nếu Exit Code $\ne 0$.
  - Cập nhật Cẩm nang Soạn thảo Kỹ năng (`skill_authoring_guide.md`, `skill_review_checklist.md`) và nâng cấp `packages/ccba-harness/tests/test_verify_patch.py` (19/19 tests PASS 100%).
  - Tích hợp mẫu Exit-Code Gate vào các Master Skills và Rituals trọng tâm: `ccba-implement`, `ccba-tdd`, `ccba-code-review`, `ccba-build-skill`, `ccba-legal-advisor`, `ccba-completion-checklist`.
- **[Đã chốt - 2026-09-10] Thử nghiệm Swarm Multi-Agent với Single-Writer Engine (Ticket F3)**:
  - Nâng cấp [`scripts/governance/apply_worker_patch.py`](../../../../scripts/governance/apply_worker_patch.py) với `SwarmExecutionReport`, hỗ trợ cờ linh hoạt `--verify-cmd` (`-c`), `--preset`, `--benchmark`, `--json` và cơ chế phát hiện & báo cáo Semantic Conflict tự động rollback 100% snapshot.
  - Xây dựng bộ kiểm thử E2E mô phỏng Swarm 5 kịch bản [`tests/governance/test_swarm_single_writer_e2e.py`](../../../../tests/governance/test_swarm_single_writer_e2e.py) đạt 5/5 PASS (toàn bộ 99 tests governance đạt 100% PASS):
    1. Concurrent 5-Worker Swarm nộp độc lập 5 patches across 5 seams $\rightarrow$ Single-Writer merge thành công không va chạm dòng.
    2. Syntactic Collision Rejection $\rightarrow$ Chặn đứng 2 workers sửa cùng khối code trước khi ghi đĩa.
    3. Semantic Conflict & Auto-Rollback $\rightarrow$ Phát hiện lỗi logic qua verification gate, tự động phục hồi nguyên trạng đĩa từ snapshot.
    4. Stale / Drift Patch Rejection $\rightarrow$ Từ chối an toàn search blocks không khớp trong dry-run.
    5. High-Throughput Latency Benchmark $\rightarrow$ Đo lường phân tích va chạm 20 khối patch $< 50\text{ms}$.
  - Chuẩn hóa kỹ năng [`.agents/skills/ccba-teamwork/SKILL.md`](../../../../.agents/skills/ccba-teamwork/SKILL.md) cưỡng chế nguyên tắc No Pre-mutation và quy trình nghiệm thu bằng `apply_worker_patch.py` kết hợp ADR-0058 Hard Completion Lock.
- **[Đã chốt - 2026-09-10] Hệ thống Giám sát Token & OpenTelemetry Subagent Runtime (Ticket F4)**:
  - Xây dựng module `packages/ccba-harness/src/ccba_harness/telemetry.py` thu thập, phân tích và chuẩn hóa mức tiêu thụ token/chi phí theo thời gian thực từ Antigravity transcript logs.
  - Tích hợp CLI `ccba-harness telemetry scan / subagents` và script `scripts/governance/subagent_telemetry.py`.
  - Bộ unit tests `tests/governance/test_subagent_telemetry.py` đạt 7/7 PASS.
- **[Đã chốt - 2026-09-10] Tự động hóa Giám sát Chi phí & Token Telemetry vào CI/CD Gates (Ticket F5)**:
  - Thể chế hóa Cổng Kiểm định Thứ 7 (Gate 7: Subagent Swarm Telemetry & Cost Control Gate) trong `scripts/eval/run_harness_evals.py` và `scripts/eval/eval_telemetry_gate.py`.
  - Thiết lập ngân sách token trần và cảnh báo rò rỉ token cho các subagents chạy nền, đạt 100% PASS trên toàn bộ CI Eval Gates.
- **[Đã chốt - 2026-09-10] Tích hợp Giao diện Dashboard Trực Quan Hóa Swarm Telemetry (Ticket F6)**:
  - Xây dựng module `packages/ccba-harness/src/ccba_harness/dashboard.py` sinh Standalone HTML Dashboard với Pure SVG Charts (Token Stacked Bars, Timeline, Tool Frequency).
  - Tích hợp CLI `ccba-harness telemetry dashboard`, xuất bản artifact và mirror `swarm_telemetry_dashboard.html`, đạt 8/8 unit tests PASS.
- **[Đã chốt - 2026-09-10] Mở Rộng Hệ Thống Báo Cáo & Phân Tích Đa Dự Án (Ticket F7)**:
  - Xây dựng module `packages/ccba-harness/src/ccba_harness/fleet.py` quét qua 5 Spokes đã đăng ký trong Hub theo Sanitized Telemetry Protocol (ADR-0046).
  - Sinh báo cáo Fleet Dashboard HTML `cross_spoke_fleet_dashboard.html`, tích hợp CLI `ccba-harness telemetry fleet` và `scripts/governance/cross_spoke_analytics.py`.
  - Hook tự động refresh telemetry trong `scripts/spoke/sync/coordinator.py`, đạt 7/7 unit tests PASS.
- **[Đã chốt - 2026-09-10] Token Economy & Tối Ưu Hóa Chi Phí Prompt (Ticket P4.1)**:
  - Xây dựng module `packages/ccba-harness/src/ccba_harness/economy.py` tính toán Prompt Density Index (PDI), sentence hashing phát hiện trùng lặp siêu tốc (< 300ms) và role-aware token ROI.
  - Tích hợp CLI `ccba-harness telemetry economy` và tiện ích `scripts/governance/token_economy.py`.
  - Xuất bản báo cáo kiểm định 67 kỹ năng `.md/reports/prompt_economy_report.md` và đạt 7/7 unit tests PASS.
- **[Đã chốt - 2026-09-10] Di Trú 28 Core Scripts Về Monorepo Packages (Ticket P4.2)**:
  - Di trú OOXML DOM cleaners (`merge_runs`, `simplify_redlines`, `clone_xml_text`, `infer_author`) vào Deep Seam `packages/ccba-ooxml/src/ccba_ooxml/docx/cleanup.py`.
  - Di trú PDF manipulation (`merge_pdfs`, `split_pdf_pages`, `extract_text_from_pdf`, `parse_pages`) vào Deep Seam `packages/ccba-pdf-prep/src/ccba_pdf_prep/manipulation.py`.
  - Chuyển đổi 100% 4 scripts trong `.agents/skills/ccba-xu-ly-van-phong/scripts/` thành Thin Adapters chuẩn mực tuân thủ Cổng 0 ADR-0057.
  - Xây dựng bộ scoped unit tests (16/16 tests PASS) và vượt qua 100% 7 Cổng CI Eval Gates (ADR-0058).

- **[Đã chốt - 2026-09-10] Real-Time Telemetry Streaming Bridge qua Server Spark (Ticket P4.3)**:
  - Xây dựng module `packages/ccba-harness/src/ccba_harness/streamer.py` với cấu trúc `TelemetryEvent` chuẩn hóa, bộ đệm ngoại tuyến `OfflineBufferManager` và cầu nối `TelemetryStreamingBridge`.
  - Thiết kế an toàn Offline-First & Graceful Degradation: Tự động chuyển sang `OFFLINE_BUFFERING` khi Server Spark (`100.83.192.30:8090`) hoặc VPN gián đoạn, tuyệt đối không làm gián đoạn Agent loop.
  - Tích hợp subcommand `ccba-harness telemetry stream` và tiện ích độc lập `scripts/governance/telemetry_streamer.py` (`ping`, `stream`, `flush`, `status`).
  - Bộ unit tests `tests/governance/test_telemetry_streamer.py` (7/7 PASS) và 100% vượt qua 7 Cổng CI Eval Gates.

---

## 4. Các Ticket ở Biên giới (Frontier Unblocked Tickets)

Toàn bộ **15/15 Tickets (P0, P1, Phase 2, Phase 3 và Phase 4: Beyond Horizon)** trên Bản đồ Wayfinder đã **HOÀN THÀNH 100%**.

```mermaid
flowchart TD
    subgraph Done ["Đã Hoàn thành (Phase 0, 1, 2, 3 & Phase 4: Beyond Horizon - Closed 100%) 🎉"]
        T1["[T1: Task AFK] Memory Compaction Engine cho session_learnings.md ✅"]
        T2["[T2: Task AFK] Exit-Code Deterministic Verification Gate trong ccba-harness ✅"]
        T3["[T3: Research AFK] Ma trận Ánh xạ Di trú 52 Scripts ✅"]
        T4["[T4: Prototype HITL] Giao thức Structured Diff Patch & Single-Writer cho ccba-teamwork ✅"]
        T5["[T5: Grilling HITL] Thiết kế Live State Artifacts & ADR-0058 Charter Alignment ✅"]
        F1["[F1: Task AFK] Di trú 35 Core Scripts & Thành lập packages/ccba-qc-core ✅"]
        F2["[F2: Task AFK] Tích hợp verify-patch Loop Tự động cho 67 SKILL.md ✅"]
        F3["[F3: Task HITL] Thử nghiệm Swarm Multi-Agent với Single-Writer Engine ✅"]
        F4["[F4: Task HITL] Hệ thống Giám sát Token & OpenTelemetry Subagent Runtime ✅"]
        F5["[F5: Task AFK] Tự động hóa Giám sát Chi phí & Token Telemetry vào CI/CD Gates ✅"]
        F6["[F6: Task HITL] Tích hợp Giao diện Dashboard Trực Quan Hóa Swarm Telemetry ✅"]
        F7["[F7: Task HITL] Mở Rộng Hệ Thống Báo Cáo & Phân Tích Đa Dự Án (Cross-Spoke Analytics) ✅"]
        P4_1["[P4.1: Task AFK] Token Economy & Prompt Density Optimization Engine ✅"]
        P4_2["[P4.2: Task AFK] Di Trú 28 Core Scripts Về ccba-ooxml & ccba-pdf-prep ✅"]
        P4_3["[P4.3: Prototype HITL] Real-Time Telemetry Streaming Bridge qua Server Spark ✅"]
        P4_4["[P4.4: Task HITL] Autonomous Self-Healing & Closed-Loop CI Patch Engine ✅"]
    end

    T3 -.->|Đã Giải mã Sương mù| F1
    T2 -.->|Đã Giải mã Sương mù| F2
    T4 -.->|Đã Giải mã Sương mù| F3
    F3 -.->|Đã Giải mã Sương mù| F4
    F4 -.->|Đã Giải mã Sương mù| F5
    F5 -.->|Đã Giải mã Sương mù| F6
    F6 -.->|Đã Giải mã Sương mù| F7
    F7 --> P4_1
    F7 --> P4_2
    F7 --> P4_3
    P4_1 --> P4_4
    P4_2 --> P4_4
    P4_3 --> P4_4
```

---

### Ticket 1: [Task/AFK] `[Xây dựng Cơ chế Nén Tri thức Tự động (Memory Compaction Engine) cho session_learnings.md]` ✅
- **Mục tiêu**: Xây dựng tiện ích CLI `scripts/governance/compact_session_learnings.py` (kèm unit test tại `tests/governance/test_compact_session_learnings.py`) có khả năng phân loại các quy tắc trong `session_learnings.md`, chắt lọc thành bảng tóm tắt $\le 10\text{ KB}$, và tự động lưu các ghi chú lịch sử chi tiết vào `.md/knowledge/archive/session_learnings_archive_<timestamp>.md`.
- **Đầu ra thực tế**:
  - Script [`scripts/governance/compact_session_learnings.py`](../../../../scripts/governance/compact_session_learnings.py) đạt chuẩn strict mypy và ruff.
  - Bộ kiểm thử [`tests/governance/test_compact_session_learnings.py`](../../../../tests/governance/test_compact_session_learnings.py) đạt 100% PASS.
  - File [`.md/knowledge/session_learnings.md`](../../knowledge/session_learnings.md) giảm từ 38 KB về **8.56 KB** (tiết kiệm ~7,300 tokens mỗi phiên).
  - Bản lưu trữ toàn văn 100% tại [`.md/knowledge/archive/session_learnings_history.md`](../../knowledge/archive/session_learnings_history.md).
- **Phân loại**: `Task [AFK]` | **Ưu tiên**: P0.1 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket 2: [Task/AFK] `[Nâng cấp ccba-harness verify-patch với Exit-Code Deterministic Verification Gate]` ✅
- **Mục tiêu**: Bổ sung hàm thực thi kiểm định xác định `verify_patch_execution()` vào `packages/ccba-harness/src/ccba_harness/verifier.py` và command CLI `ccba-harness verify-patch`. Công cụ này cho phép truyền vào danh sách lệnh (`pytest ...`, `ruff check ...`, `mypy ...`), tự động chạy trong subprocess cô lập, bắt exit code và trả về kết quả JSON/Markdown chuẩn hóa kèm thông báo lỗi ngắn gọn nếu exit code $\ne 0$.
- **Đầu ra thực tế**:
  - Module [`packages/ccba-harness/src/ccba_harness/verifier.py`](../../../../packages/ccba-harness/src/ccba_harness/verifier.py) (`CommandResult`, `PatchVerificationReport`, `verify_patch_execution()`).
  - Subcommand `ccba-harness verify-patch` với các flags: `-c / --cmd / --commands`, `--file`, `--timeout`, `--cwd`, `--json`, `--report-file`, `--fail-fast`.
  - Bộ kiểm thử [`packages/ccba-harness/tests/test_verify_patch.py`](../../../../packages/ccba-harness/tests/test_verify_patch.py) đạt 12/12 PASS (100% pass trên toàn suite 141 tests).
- **Phân loại**: `Task [AFK]` | **Ưu tiên**: P0.2 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket 3: [Research/AFK] `[Khảo sát, Lập Danh mục & Ma trận Di trú 52 Scripts Về Monorepo Packages]` ✅
- **Mục tiêu**: Quét toàn bộ mã nguồn Python nằm trong `.agents/skills/*/scripts/`. Phân tích dependency, xác định chức năng và lập ma trận ánh xạ (Mapping Matrix) cụ thể từng script sẽ được chuyển vào Deep Seam của package nào.
- **Đầu ra thực tế**:
  - Tài liệu điều tra và ma trận di trú: [`.md/knowledge/scripts_migration_manifest.md`](../../knowledge/scripts_migration_manifest.md).
  - Xác định chính xác 11 skills chứa scripts (52 files, 9,909 LOC), trong đó 17 files đã là Thin Adapters, 35 files chứa core logic.
  - Đề xuất tạo package mới `packages/ccba-qc-core` và phân bổ các files còn lại về `ccba-harness`, `ccba-ooxml`, `ccba-pdf-prep`.
- **Phân loại**: `Research [AFK]` | **Ưu tiên**: P0.3 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket 4: [Prototype/HITL] `[Thiết kế Mẫu Giao thức Structured Diff Patch & Single-Writer cho ccba-teamwork]` ✅
- **Mục tiêu**: Xây dựng mẫu thử giao thức làm việc cho các Worker Sub-agents: cấm gọi các công cụ sửa file trực tiếp (`replace_file_content`, `write_to_file` trên source code). Thay vào đó, Worker chỉ xuất tệp Patch (`.diff` hoặc JSON Search-Replace) vào thư mục `.system_generated/scratch/`. Thiết kế một helper script `apply_worker_patches.py` để Lead Orchestrator áp dụng lần lượt các patch, kiểm tra xung đột cú pháp và revert nếu gặp lỗi.
- **Đầu ra thực tế**:
  - Tài liệu quy chuẩn giao thức: [`.md/knowledge/specs/spec-structured-diff-protocol.md`](../../knowledge/specs/spec-structured-diff-protocol.md).
  - Script nguyên mẫu: [`scripts/governance/apply_worker_patch.py`](../../../../scripts/governance/apply_worker_patch.py) hỗ trợ `--dry-run`, `--check-conflicts`, `--apply`, `--verify`.
  - Bộ unit tests: [`tests/governance/test_apply_worker_patch.py`](../../../../tests/governance/test_apply_worker_patch.py) đạt 10/10 PASS.
- **Phân loại**: `Prototype [HITL]` | **Ưu tiên**: P1.1 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket 5: [Grilling/HITL] `[Phỏng vấn Thiết kế Tích hợp Live State Artifacts & 11-Seat CCBA Charter Review]` ✅
- **Mục tiêu**: Thực hiện một phiên đối thoại chuyên sâu (Socratic Grilling) cùng Kỹ sư trưởng để thống nhất cấu trúc của các Live State Artifacts (`prompt_draft.md`, `task_dashboard.md`), vị trí lưu trữ hợp chuẩn Rule 1 (`.\.md\scratch\`), và cách thức gắn kết quyết định của 11 Ghế Hội đồng Thẩm định CCBA (ADR-0046) vào giao diện phản hồi của Antigravity (`RequestFeedback: true`).
- **Đầu ra thực tế**:
  - Biên bản phỏng vấn Grilling: [`.md/knowledge/grilling_live_artifacts_and_charter.md`](../../knowledge/grilling_live_artifacts_and_charter.md).
  - Quyết định kiến trúc chính thức: [**ADR-0058**](../../../docs/adr/0058-live-collaboration-artifacts-workspace-mirroring-and-charter-alignment.md).
  - Bộ kiểm thử ADR: `tests/governance/test_adr.py` và `test_sync_adr_matrix.py` đạt 13/13 PASS.
- **Phân loại**: `Grilling [HITL]` | **Ưu tiên**: P1.2 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket F1: [Task/AFK] `[Thành lập packages/ccba-qc-core & Di trú 35 Core Scripts Thẩm định Đa bộ môn]` ✅
- **Mục tiêu**: Khởi tạo package mới `packages/ccba-qc-core`, di trú 35 core scripts (1,788 LOC của `ccba-ai-qc` và `ccba-ai-qc-pccc-audit`) thành Deep Seam chuẩn mực, chuyển đổi các script trong skill thành Thin Adapters, và kiểm định qua `ccba-harness verify-patch`.
- **Đầu ra thực tế**:
  - Scaffolding & source code hoàn chỉnh tại [`packages/ccba-qc-core/`](../../../../packages/ccba-qc-core/):
    - `src/ccba_qc_core/discovery.py` (`DiscoveryEngine`, `SheetEntry`, `ProjectBackbone`, `_normalize_vn`).
    - `src/ccba_qc_core/quadview.py` (`QuadViewAuditEngine`, `_parse_audit_response`).
    - `src/ccba_qc_core/semantic.py` (`SemanticAuditEngine`).
    - `src/ccba_qc_core/reporter.py` (`ReporterEngine`).
    - `src/ccba_qc_core/pccc.py` (`PcccMapReduceEngine`).
    - `src/ccba_qc_core/pipeline.py` (`QCBatchOrchestrator`).
    - `src/ccba_qc_core/cli.py` (CLI `ccba-qc`).
  - Chuyển đổi 6 scripts thành Thin Adapters chuẩn mực (chỉ delegate call và CLI proxy):
    - `.agents/skills/ccba-ai-qc/scripts/` (`discovery_engine.py`, `legacy_quadview_engine.py`, `semantic_audit_engine.py`, `reporter_engine.py`, `orchestrator.py`).
    - `.agents/skills/ccba-ai-qc-pccc-audit/scripts/audit_engine.py`.
  - Bộ unit tests [`packages/ccba-qc-core/tests/test_qc_core.py`](../../../../packages/ccba-qc-core/tests/test_qc_core.py) đạt 6/6 PASS trong 2.27s.
  - Strict mypy đạt 0 issues in 8 source files.
  - Bộ kiểm thử ranh giới phụ thuộc `tests/governance/test_dependency_contracts.py` đạt 6/6 PASS.
  - Toàn bộ 4/4 rào chắn của `ccba-harness verify-patch` đều đạt Exit Code 0.
- **Phân loại**: `Task [AFK]` | **Ưu tiên**: P1.3 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket F2: [Task/AFK] `[Tích hợp verify-patch Loop Tự động cho 67 SKILL.md]` ✅
- **Mục tiêu**: Nâng cấp `packages/ccba-harness` hỗ trợ Verification Presets một chạm (`--preset code`, `--preset doc`, `--preset skill`, `--preset adr`), bổ sung công cụ xác thực tài liệu định tính `ccba-harness verify-doc`, thể chế hóa vào Hiến pháp Layer 1 (`AGENTS.md`) và Cẩm nang Soạn thảo Kỹ năng (`skill_authoring_guide.md`, `skill_review_checklist.md`), đồng thời tích hợp mẫu Exit-Code Gate vào các Master Skills và Rituals trọng tâm.
- **Đầu ra thực tế**:
  - Module [`packages/ccba-harness/src/ccba_harness/verifier.py`](../../../../packages/ccba-harness/src/ccba_harness/verifier.py) (`verify_document_artifact`, `resolve_preset_commands`, `verify_patch_execution` with presets).
  - CLI subcommand `ccba-harness verify-doc` và cờ `--preset` trong `ccba-harness verify-patch`.
  - Bộ kiểm thử unit test [`packages/ccba-harness/tests/test_verify_patch.py`](../../../../packages/ccba-harness/tests/test_verify_patch.py) mở rộng đạt 19/19 PASS (100%).
  - Cập nhật Hiến pháp Nòng cốt [`AGENTS.md`](../../../../AGENTS.md) và [`.agents/AGENTS.md`](../../../../.agents/AGENTS.md): Điều khoản **Deterministic Hard Completion Lock (ADR-0058)** cấm Agent tự nhận hoàn thành nếu Exit Code $\ne 0$.
  - Cập nhật Cẩm nang Soạn thảo Kỹ năng: Bổ sung Chương 3.2 trong `skill_authoring_guide.md` và tiêu chí kiểm định trong `skill_review_checklist.md`.
  - Tích hợp Exit-Code Gate vào các Master Skills: `ccba-implement`, `ccba-tdd`, `ccba-code-review`, `ccba-build-skill`, `ccba-legal-advisor`, `ccba-completion-checklist`.
  - Toàn bộ 67 SKILL.md vượt qua `validate_skills.py --enforce-gpi` và catalog đồng bộ 100%.
- **Phân loại**: `Task [AFK]` | **Ưu tiên**: P1.4 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket F3: [Task/HITL] `[Thử nghiệm Swarm Multi-Agent với Single-Writer Engine]` ✅
- **Mục tiêu**: Nâng cấp `scripts/governance/apply_worker_patch.py` hỗ trợ `--verify-cmd`, `--preset`, và cấu trúc hóa `SwarmExecutionReport` kèm đo lường latency profiler và chẩn đoán Semantic Conflicts. Xây dựng bộ kiểm thử mô phỏng toàn diện `tests/governance/test_swarm_single_writer_e2e.py` bao phủ 5 kịch bản thực chiến (Concurrent 5-worker swarm, line collision rejection, semantic conflict with auto-rollback, stale drift patch rejection, sub-50ms benchmark), đồng thời chuẩn hóa kỹ năng `ccba-teamwork` tích hợp nguyên tắc No Pre-mutation và quy trình hợp nhất Single-Writer Engine theo ADR-0058 Hard Completion Lock.
- **Đầu ra thực tế**:
  - Module [`scripts/governance/apply_worker_patch.py`](../../../../scripts/governance/apply_worker_patch.py) với `SwarmExecutionReport`, hỗ trợ cờ linh hoạt `-c / --verify-cmd`, `--preset`, `--benchmark`, `--json` và cơ chế phát hiện & báo cáo Semantic Conflict tự động rollback 100% snapshot.
  - Bộ kiểm thử E2E mô phỏng Swarm 5 kịch bản [`tests/governance/test_swarm_single_writer_e2e.py`](../../../../tests/governance/test_swarm_single_writer_e2e.py) đạt 5/5 PASS (toàn bộ 99 tests governance đạt 100% PASS).
  - Bộ kiểm thử unit test [`tests/governance/test_apply_worker_patch.py`](../../../../tests/governance/test_apply_worker_patch.py) mở rộng đạt 13/13 PASS.
  - Chuẩn hóa kỹ năng [`.agents/skills/ccba-teamwork/SKILL.md`](../../../../.agents/skills/ccba-teamwork/SKILL.md) cưỡng chế nguyên tắc No Pre-mutation và quy trình nghiệm thu bằng `apply_worker_patch.py` kết hợp ADR-0058 Hard Completion Lock.
- **Phân loại**: `Task [HITL]` | **Ưu tiên**: P2.1 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket F4: [Task/HITL] `[Hệ thống Giám sát Token & OpenTelemetry Subagent Runtime]` ✅
- **Mục tiêu**: Xây dựng engine giám sát runtime chuyên sâu cho Subagents trong Antigravity IDE, hỗ trợ Zero-Overhead streaming parser cho `transcript.jsonl`, bộ ước lượng token song ngữ Việt - Anh (BPE-based), xuất chuẩn OpenTelemetry GenAI Semantic Conventions (v1.28.0+) OTLP Traces JSON (`resourceSpans`), và cơ chế cưỡng chế ngân sách Token/Duration Budget (ADR-0030) với Deterministic Hard Completion Lock (ADR-0058).
- **Đầu ra thực tế**:
  - Module [`packages/ccba-harness/src/ccba_harness/telemetry.py`](../../../../packages/ccba-harness/src/ccba_harness/telemetry.py) (`TokenEstimator`, `stream_transcript_steps`, `analyze_subagent_transcript`, `check_subagent_budget`, `OtelSpanExporter`).
  - Tích hợp CLI `ccba-harness telemetry [inspect|budget-check|export-otel]` trong [`packages/ccba-harness/src/ccba_harness/cli.py`](../../../../packages/ccba-harness/src/ccba_harness/cli.py).
  - Tiện ích CLI độc lập [`scripts/governance/subagent_telemetry.py`](../../../../scripts/governance/subagent_telemetry.py).
  - Bộ unit test [`packages/ccba-harness/tests/test_telemetry.py`](../../../../packages/ccba-harness/tests/test_telemetry.py) đạt 6/6 PASS.
  - Bộ test tích hợp governance [`tests/governance/test_subagent_telemetry.py`](../../../../tests/governance/test_subagent_telemetry.py) đạt 5/5 PASS.
  - Kiểm thử thực tế trên subagent trajectory `bacf8218-9bfb-4f1a-a79d-1e1748fd9caf` (206 steps, 103 turns, 3,101,462 tokens, 206 OTLP spans, runtime 0.1s).
- **Phân loại**: `Task [HITL]` | **Ưu tiên**: P2.2 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket F5: [Task/AFK] `[Tự động hóa Giám sát Chi phí & Token Telemetry vào CI/CD Gates]` ✅
- **Mục tiêu**: Tự động hóa việc giám sát runtime telemetry cho toàn bộ bầy tác tử (Swarm Multi-Agent Session) theo ADR-0030, mở rộng các verification presets `--preset telemetry` và `--preset ci` trong `ccba-harness verify-patch` (ADR-0058), đồng thời tích hợp toàn diện 7 cổng kiểm định (Linter, Formatter, Mypy, Pytest Suites, Docs, Skills Governance, ADR Traceability, Telemetry Budget) vào `scripts/eval/run_harness_evals.py` và `.github/workflows/ci.yml`.
- **Đầu ra thực tế**:
  - Module [`packages/ccba-harness/src/ccba_harness/telemetry.py`](../../../../packages/ccba-harness/src/ccba_harness/telemetry.py) (`SwarmSessionTelemetryReport`, `find_spawned_subagent_ids`, `audit_swarm_session`).
  - Nâng cấp CLI [`packages/ccba-harness/src/ccba_harness/cli.py`](../../../../packages/ccba-harness/src/ccba_harness/cli.py) và [`scripts/governance/subagent_telemetry.py`](../../../../scripts/governance/subagent_telemetry.py) với lệnh `audit-swarm`.
  - Mở rộng [`packages/ccba-harness/src/ccba_harness/verifier.py`](../../../../packages/ccba-harness/src/ccba_harness/verifier.py) với presets `--preset telemetry` và `--preset ci`.
  - Tích hợp 7 CI Gates vào [`scripts/eval/run_harness_evals.py`](../../../../scripts/eval/run_harness_evals.py) và cập nhật workflow [`.github/workflows/ci.yml`](../../../../.github/workflows/ci.yml).
  - Bộ unit test [`packages/ccba-harness/tests/test_verify_patch.py`](../../../../packages/ccba-harness/tests/test_verify_patch.py) và [`packages/ccba-harness/tests/test_telemetry.py`](../../../../packages/ccba-harness/tests/test_telemetry.py) đạt 26/26 PASS.
  - Bộ test tích hợp governance [`tests/governance/test_ci_telemetry_gate.py`](../../../../tests/governance/test_ci_telemetry_gate.py) đạt 4/4 PASS.
  - Toàn bộ 5/5 rào chắn của `ccba-harness verify-patch --preset ci` đều đạt Exit Code 0.
- **Phân loại**: `Task [AFK]` | **Ưu tiên**: P2.3 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket F6: [Task/HITL] `[Tích hợp Giao diện Dashboard Trực Quan Hóa Swarm Telemetry]` ✅
- **Mục tiêu**: Xây dựng module sinh giao diện Swarm Telemetry Dashboard dưới dạng standalone HTML tự thân (Zero-Server, Zero External CDN) tuân thủ CSP của Antigravity IDE (`generative_ui`), trực quan hóa Pure SVG Token Stacked Bars, SVG Gantt-style Timeline, Tool Invocations Latency Matrix, và Turn-by-Turn Trajectory Inspector, tích hợp đồng bộ vào CLI `ccba-harness telemetry dashboard` và `scripts/governance/subagent_telemetry.py dashboard`.
- **Đầu ra thực tế**:
  - Module [`packages/ccba-harness/src/ccba_harness/dashboard.py`](../../../../packages/ccba-harness/src/ccba_harness/dashboard.py) (`generate_swarm_dashboard_html`, `render_swarm_dashboard`, Pure SVG Charts).
  - Tích hợp CLI subcommand `dashboard` trong [`packages/ccba-harness/src/ccba_harness/cli.py`](../../../../packages/ccba-harness/src/ccba_harness/cli.py) và [`scripts/governance/subagent_telemetry.py`](../../../../scripts/governance/subagent_telemetry.py).
  - Xuất bản tệp giao diện thực tế cho phiên Swarm hiện tại (9 subagents, 14.9M tokens):
    - Artifact: [`swarm_telemetry_dashboard.html`](file:///C:/Users/chuvu/.gemini/antigravity/brain/ea5a900e-41fd-4ae6-968a-e2e271e67e52/swarm_telemetry_dashboard.html)
    - Mirror lưu trữ vĩnh viễn: [`.md/reports/swarm_telemetry_dashboard.html`](../../reports/swarm_telemetry_dashboard.html).
  - Bộ kiểm thử độc lập [`tests/governance/test_telemetry_dashboard.py`](../../../../tests/governance/test_telemetry_dashboard.py) đạt 8/8 PASS.
- **Phân loại**: `Task [HITL]` | **Ưu tiên**: P3.1 | **Trạng thái**: **Closed (Done) ✅**

### Ticket F7: [Task/HITL] `[Mở Rộng Hệ Thống Báo Cáo & Phân Tích Đa Dự Án (Cross-Spoke Analytics)]` ✅
- **Mục tiêu**: Xây dựng engine tổng hợp telemetry liên dự án (`CrossSpokeAnalyticsEngine`) quét qua toàn bộ 5 Spokes đã đăng ký trong Hub (`2026-04 DH Viet Nhat`, `IDOP-CCBA-WAY`, `ccba-legal-knowledge`, `Zalo_Bot_Free`, `VvC Second Brain`), tuyệt đối tuân thủ Sanitized Telemetry Protocol (ADR-0046), xây dựng giao diện Standalone HTML Fleet Dashboard (`cross_spoke_fleet_dashboard.html`) với Pure SVG Charts (so sánh Spoke tokens, phân bổ miền dự án, tần suất tools), zero-server, tích hợp CLI `cross_spoke_analytics.py` và `ccba-harness telemetry fleet`, tự động refresh qua `spoke_synchronizer.py sync`.
- **Đầu ra thực tế**:
  - Module [`packages/ccba-harness/src/ccba_harness/fleet.py`](../../../../packages/ccba-harness/src/ccba_harness/fleet.py) (`SpokeTelemetrySummary`, `FleetTelemetryReport`, `scan_spoke_telemetry`, `aggregate_fleet_telemetry`, `generate_fleet_dashboard_html`, `render_fleet_dashboard`).
  - Tích hợp CLI subcommand `fleet` trong [`packages/ccba-harness/src/ccba_harness/cli.py`](../../../../packages/ccba-harness/src/ccba_harness/cli.py) (`ccba-harness telemetry fleet [--json] [--dashboard] [--out] [--title]`).
  - Tiện ích CLI chuyên trách [`scripts/governance/cross_spoke_analytics.py`](../../../../scripts/governance/cross_spoke_analytics.py) (`scan`, `dashboard`, `export-spoke-summary`).
  - Hook tự động refresh telemetry trong [`scripts/spoke/sync/coordinator.py`](../../../../scripts/spoke/sync/coordinator.py) khi chạy sync Spoke.
  - Xuất bản tệp Fleet Dashboard thực tế cho 5 Spokes (15.5M tokens, \$2.41):
    - Artifact: [`cross_spoke_fleet_dashboard.html`](file:///C:/Users/chuvu/.gemini/antigravity/brain/ea5a900e-41fd-4ae6-968a-e2e271e67e52/cross_spoke_fleet_dashboard.html)
    - Mirror lưu trữ vĩnh viễn: [`.md/reports/cross_spoke_fleet_dashboard.html`](../../reports/cross_spoke_fleet_dashboard.html).
  - Bộ kiểm thử độc lập [`tests/governance/test_cross_spoke_analytics.py`](../../../../tests/governance/test_cross_spoke_analytics.py) đạt 7/7 PASS (100%).
- **Phân loại**: `Task [HITL]` | **Ưu tiên**: P3.2 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket P4.1: [Task/AFK] `[Token Economy & Prompt Density Optimization Engine]` ✅
- **Mục tiêu**: Xây dựng module `packages/ccba-harness/src/ccba_harness/economy.py` và subcommand CLI `ccba-harness telemetry economy` nhằm khai thác dữ liệu từ `FleetTelemetryReport` và `SwarmTelemetryReport`.
- **Đầu ra thực tế**:
  - Module [`packages/ccba-harness/src/ccba_harness/economy.py`](../../../../packages/ccba-harness/src/ccba_harness/economy.py) (`SkillPromptMetrics`, `TokenROIMetrics`, `EconomyAuditReport`, `analyze_skill_prompt_density`, `detect_sentence_duplicates`, `calculate_role_aware_roi`, `generate_prompt_pruning_report`).
  - Tiện ích CLI chuyên trách [`scripts/governance/token_economy.py`](../../../../scripts/governance/token_economy.py) (`scan`, `report`, `roi`) và subcommand `ccba-harness telemetry economy`.
  - Báo cáo kiểm định thực tế toàn bộ 67 kỹ năng: [`.md/reports/prompt_economy_report.md`](../../reports/prompt_economy_report.md) (PDI trung bình 73.3/100, phát hiện 4 skills overhead cao, tiềm năng tiết kiệm ~12,134 tokens/lượt).
  - Bộ kiểm thử độc lập [`tests/governance/test_telemetry_economy.py`](../../../../tests/governance/test_telemetry_economy.py) đạt 7/7 PASS (100%).
- **Phân loại**: `Task [AFK]` | **Ưu tiên**: P4.1 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket P4.2: [Task/AFK] `[Di Trú 28 Core Scripts Về Monorepo Packages (Hoàn Tất Giai Đoạn 2)]` ✅
- **Mục tiêu**: Hoàn tất 100% việc dọn dẹp và di chuyển các core logic còn lại từ `.agents/skills/*/scripts/` vào các Deep Seams theo đúng Cổng 0 ADR-0057:
  - Di trú các XML runs helpers, redlines simplifies, clone text từ `ccba-xu-ly-van-phong` vào `packages/ccba-ooxml`.
  - Di trú PDF manipulation tools (`merge_pdfs`, `split_pdf_pages`, `extract_text_from_pdf`, `parse_pages`) vào `packages/ccba-pdf-prep`.
  - Chuyển đổi 100% các script trong các skill tương ứng thành Thin Adapters chuẩn mực (zero core logic bloat ngoài packages).
  - Bộ unit tests trong từng package đạt 100% PASS, vượt qua 7 Cổng CI Eval Gates.
- **Đầu ra thực tế**:
  - Module [`packages/ccba-ooxml/src/ccba_ooxml/docx/cleanup.py`](../../../../packages/ccba-ooxml/src/ccba_ooxml/docx/cleanup.py) (`merge_runs`, `simplify_redlines`, `clone_xml_text`, `get_tracked_change_authors`, `infer_author`).
  - Module [`packages/ccba-pdf-prep/src/ccba_pdf_prep/manipulation.py`](../../../../packages/ccba-pdf-prep/src/ccba_pdf_prep/manipulation.py) (`merge_pdfs`, `split_pdf_pages`, `extract_text_from_pdf`, `parse_pages`).
  - 4 Thin Adapters: `ccba-xu-ly-van-phong/scripts/office/helpers/merge_runs.py`, `simplify_redlines.py`, `clone_text.py`, `process_pdf.py`.
  - Scoped unit tests: [`packages/ccba-ooxml/tests/test_docx_cleanup.py`](../../../../packages/ccba-ooxml/tests/test_docx_cleanup.py) (7/7 PASS) và [`packages/ccba-pdf-prep/tests/test_manipulation.py`](../../../../packages/ccba-pdf-prep/tests/test_manipulation.py) (9/9 PASS).
  - 100% vượt qua 7 Cổng CI Eval Gates (`run_harness_evals.py --all`) và Deterministic Patch Verification (`verify-patch --preset ci`).
- **Phân loại**: `Task [AFK]` | **Ưu tiên**: P4.2 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket P4.3: [Prototype/HITL] `[Real-Time Telemetry Streaming Bridge qua Server Spark]` ✅
- **Mục tiêu**: Xây dựng cầu nối truyền phát dữ liệu đo lường thời gian thực (Real-time Telemetry Bridge) từ Antigravity Worktrees về máy chủ Spark (`100.83.192.30:8090`) qua Tailscale VPN.
- **Đầu ra thực tế**:
  - Module [`packages/ccba-harness/src/ccba_harness/streamer.py`](../../../../packages/ccba-harness/src/ccba_harness/streamer.py) (`TelemetryEvent`, `StreamingConfig`, `StreamingStatus`, `StreamingReport`, `OfflineBufferManager`, `AsyncTranscriptFollower`, `TelemetryStreamingBridge`).
  - Tích hợp CLI subcommand `ccba-harness telemetry stream` trong [`packages/ccba-harness/src/ccba_harness/cli.py`](../../../../packages/ccba-harness/src/ccba_harness/cli.py) hỗ trợ `--endpoint`, `--buffer-file`, `--flush-buffer`, `--ping`, `--dry-run`, `--json`.
  - Tiện ích quản trị chuyên trách [`scripts/governance/telemetry_streamer.py`](../../../../scripts/governance/telemetry_streamer.py) (`ping`, `stream`, `flush`, `status`).
  - Thiết kế an toàn Offline-First & Graceful Degradation: Tự động ghi vào `.md/telemetry/offline_buffer.jsonl` khi endpoint Spark không khả dụng, không bao giờ ngắt quãng luồng agent.
  - Bộ unit tests [`tests/governance/test_telemetry_streamer.py`](../../../../tests/governance/test_telemetry_streamer.py) đạt 7/7 PASS (100% pass trên 137 governance tests).
  - 100% vượt qua 7 Cổng CI Eval Gates (`run_harness_evals.py --all`) và Deterministic Patch Verification (`verify-patch --preset ci`).
- **Phân loại**: `Prototype [HITL]` | **Ưu tiên**: P4.3 | **Trạng thái**: **Closed (Done) ✅**

---

### Ticket P4.4: [Task/HITL] `[Autonomous Self-Healing & Closed-Loop CI Patch Engine]` ✅
- **Mục tiêu**: Xây dựng động cơ tự phục hồi mã nguồn khép kín (`SelfHealingEngine`) tích hợp vào `ccba-harness` và `apply_worker_patch.py` nhằm chẩn đoán và khắc phục tự động các lỗi định dạng, linting, metadata drift và test assertion với trần lặp an toàn và cơ chế rollback nguyên tử.
- **Đầu ra thực tế**:
  - Động cơ cốt lõi [`packages/ccba-harness/src/ccba_harness/healing.py`](../../../../packages/ccba-harness/src/ccba_harness/healing.py) (`ErrorCategory`, `DiagnosticIssue`, `HealingAction`, `HealingReport`, `SelfHealingEngine`).
  - Hỗ trợ chẩn đoán chính xác đa định dạng: Ruff format (`Would reformat`), Ruff check (cả concise format và multiline default format), Catalog drift (`compile_catalog.py`), ADR matrix drift (`sync_hub_adr_matrix.py`), và Pytest assertion failures.
  - Khóa an toàn 2 vòng lặp (`max_iterations = 2`) với In-Memory Snapshot & Full Rollback bảo đảm không gây regression code khi gặp lỗi không thể tự sửa.
  - Tích hợp cờ `--self-heal` và `--max-heal-iterations` vào CLI `ccba-harness verify-patch` ([`cli.py`](../../../../packages/ccba-harness/src/ccba_harness/cli.py)).
  - Tích hợp cơ chế tự phục hồi trước khi rollback vào Single-Writer Engine [`scripts/governance/apply_worker_patch.py`](../../../../scripts/governance/apply_worker_patch.py).
  - Cung cấp script tiện ích độc lập [`scripts/governance/self_healing.py`](../../../../scripts/governance/self_healing.py) hỗ trợ `--dry-run`, `--json`, `--preset`, `--report-file`.
  - Bộ unit tests chuyên trách [`tests/governance/test_self_healing_engine.py`](../../../../tests/governance/test_self_healing_engine.py) đạt 13/13 PASS (100%).
  - Vượt qua 100% 7 Cổng CI Eval Gates (`run_harness_evals.py --all`) và Deterministic Patch Verification (`verify-patch --preset ci`).
- **Phân loại**: `Task [HITL]` | **Ưu tiên**: P4.4 | **Trạng thái**: **Closed (Done) ✅**

---

## 5. Sương mù Chiến trận / Chưa xác định rõ (Not yet specified - Fog of War)

Toàn bộ các bài toán trong Phase 3 và định hướng Phase 4 đã được giải mã và lên kế hoạch rõ ràng!
Các hướng đi xa hơn ở chân trời tương lai (Beyond Phase 4):
1. **[Future/Phase 5] Autonomous Cross-Spoke Orchestration via Service Mesh**:
   - Khả năng để một Agent ở Spoke này triệu hồi hoặc ủy quyền công việc cho một Subagent chuyên trách ở Spoke khác một cách an toàn và bảo mật qua Hub Service Mesh.
2. **[Future/Phase 5] Local Offline Embedding Model Caching & Hardware Acceleration on Server Spark**:
   - Đưa mô hình embedding và reranking chạy 100% cục bộ trên GPU Spark với độ trễ $< 10\text{ms}$.

---

## 6. Ngoài phạm vi (Out of Scope)

1. **Thay đổi nghiệp vụ cốt lõi của các tiêu chuẩn xây dựng**:
   - Không can thiệp hoặc thay đổi các quy tắc tính toán kết cấu, bảng tra QCVN, tiêu chuẩn PCCC hay phân loại Uniclass 200 (chỉ thay đổi kiến trúc thực thi phần mềm).
2. **Can thiệp vào máy chủ AI Gateway LiteLLM**:
   - Không cấu hình lại hạ tầng Server Spark hay endpoint mạng Tailscale (chỉ chuẩn hóa SDK client phía Monorepo).
3. **Viết lại Prompt nghiệp vụ của 67 Skills trong đợt đầu**:
   - Chỉ nâng cấp cấu trúc frontmatter, rào chắn Verification Gate và di chuyển scripts; giữ nguyên tính toàn vẹn của các prompt chuyên môn đã được nghiệm thu.
