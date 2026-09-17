# 📜 CCBA Knowledge Base Mutation Log (Append-Only Log)

> **Mô tả:** Nhật ký dòng thời gian bất biến (Append-Only Journal) ghi nhận toàn bộ các đợt nạp tài liệu (`[ingest]`), tổng hợp tri thức (`[synthesize]`), ban hành quy chuẩn (`[guideline]`), quyết định kiến trúc (`[adr]`), và bảo trì linter (`[linter]`) trong LLM-Wiki.

## [2026-09-17] [synthesize] | Thẩm Định & Hợp Nhất Đề Xuất Spoke PR #283: Dynamic Base Branch Detection cho ccba-create-pr (v1.2.0)
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /ccba-review-proposal & /ccba-session-retrospective)
- **Affected Files**: `.agents/skills/ccba-create-pr/SKILL.md`, `.agents/proposals/2026-09-17_dynamic-base-branch-for-create-pr.md`, `scripts/governance/drift_auditor.py`, `tests/governance/test_global_skills_integrity.py`, `.md/knowledge/reports/walkthrough.md`, `.md/knowledge/session_learnings.md`, `.md/knowledge/archive/session_learnings_history.md`
- **Summary**: Hoàn tất thẩm định, tự chữa lành (Self-Healing) và squash-merge đề xuất PR #283 từ Spoke `dgx-spark-toolkit`: (1) Nâng cấp kỹ năng `ccba-create-pr` (v1.2.0) tích hợp lệnh Git chuẩn tắc `git symbolic-ref --short refs/remotes/origin/HEAD` và fallback native để tự động phân giải default branch (`main`, `master`), xóa bỏ giả định ngầm hardcode `main`, bảo vệ nhánh chính và mở PR chính xác trên đa Spoke; (2) Chuẩn hóa RFC Proposal `2026-09-17_dynamic-base-branch-for-create-pr.md` tuân thủ ADR-0045/ADR-0047, cập nhật trạng thái `merged` với commit `c84fe744`; (3) Tiếp thu và khắc phục triệt để 12/12 ý kiến phản biện từ GitHub Copilot Review (thay thế escape `\n` bằng `$PR_BODY`, loại bỏ absolute file URIs, cô lập phạm vi PR, bình thường hóa bộ lọc drift auditor cho root-level `tests/`); (4) Khắc phục sự cố runner CI bị mất kết nối do thiếu mock bằng cách tái lập bất biến `CCBA_AI_MOCK: "1"` trên GitHub Actions runner; (5) Vượt qua 100% 6/6 CI checks, 3/3 governance tests, 0 leakage violations và biên dịch catalog thành công (73 skills).

---
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /boost, /ccba-grilling, /ccba-create-pr, /ccba-release-feature & /ccba-session-retrospective)
- **Affected Files**: `.agents/skills/ccba-issue-tree/`, `.agents/skills/ccba-diagnosing-bugs/`, `.agents/skills/ccba-ai-qc/`, `.agents/skills/ccba-legal-advisor/`, `.agents/skills/ccba-ask/`, `.agents/skills/ccba-grilling/`, `.agents/skills/bigbim-risk/`, `.agents/skills/ccba-to-spec/`, `docs/skills/`, `.md/knowledge/session_learnings.md`, `.md/knowledge/archive/session_learnings_history.md`, `walkthrough.md`
- **Summary**: Hoàn tất chu trình phát triển, tích hợp và phát hành Pull Request #282: (1) Đóng gói kỹ năng hạt nhân độc lập `ccba-issue-tree` (Tier 2B Standalone Kernel Skill, GPI = 14.50 >= 12.0) tích hợp phương pháp luận cây vấn đề MECE của McKinsey (Diagnostic Why-Tree, Solution How-Tree, Workplan What-Tree) với tầng vận hành Governed Lifecycle (6 trạng thái vòng đời nhánh), ma trận bằng chứng ADR-0059 Verbatim Grounding và ma trận RACI Hiến chương CCBA; (2) Giải quyết bài toán trần cứng ngân sách triệu hồi (ADR-0040) bằng cấu hình `disable-model-invocation: true`, kích hoạt qua `/ccba-issue-tree` hoặc referral mà không tốn system tokens; (3) Tích hợp mạng lưới 7 điểm điều hướng tư duy (Tier 1 Cross-Skill Referral Hooks) vào các kỹ năng chuyên biệt; (4) Khắc phục triệt để 11/11 ý kiến phản biện từ GitHub Copilot Review, chuẩn hóa các định danh khái niệm bền vững chống drift số cứng; (5) Vượt qua 100% 11/11 test suites tiền phát hành, 6/6 GitHub Actions CI checks và squash merge vào `main` tại commit `1fe2f2a7`.

---

## [2026-09-17] [synthesize] | Nâng Cấp ccba-ai v1.2.0 (Drop Params Embedding, Streaming Ceiling, Auto-Timeout Scaling) (#280, PR #281)
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /ccba-new-feature, /boost, /ccba-issue-to-hub & /ccba-session-retrospective)
- **Affected Files**: `packages/ccba-ai/`, `packages/ccba-ai/pyproject.toml`, `.md/knowledge/session_learnings.md`, `.md/knowledge/archive/session_learnings_history.md`, `.md/knowledge/reports/walkthrough.md`
- **Summary**: Hoàn tất xử lý Issue #280 và đề xuất RFC Gateway Issue #51 (`dgx-spark-toolkit`): (1) Khắc phục triệt để lỗi HTTP 400 trong `ai.embed()` và `async_ai.embed()` khi kết nối LiteLLM proxy tới Gemini API bằng cách truyền `extra_body={"drop_params": True}` và đổi model mặc định sang `gemini-embedding-2` (vector 3072 chiều); (2) Bổ sung phương thức native coroutine `AsyncAIClient.embed()`; (3) Khắc phục cắt cụt token khi stream với reasoning models (`gemini-3.7-flash-high`, `-thinking`) bằng cách tự động cấp sàn `max_tokens=16384` qua `resolve_max_tokens`; (4) Bổ sung tham số `timeout` per-request và cơ chế Auto-Timeout Scaling (`max(timeout, max_tokens / 50.0)`) cho `chat()`, `chat_with_metadata()` và `chat_multi()`; (5) Bóc tách chuỗi tư duy độc lập vào `ChatResult.thinking` qua depth-aware scanner trong `LLMOutputParser`, ưu tiên nhận `reasoning_content`; (6) Đồng bộ `version = "1.2.0"` và đăng ký markers `fast`, `unit` trong `pyproject.toml`, triệt tiêu 12 cảnh báo `PytestUnknownMarkWarning`; (7) Tạo RFC Issue #51 trên repo `dgx-spark-toolkit` đề xuất global `drop_params: true` và cân chỉnh timeout server-side; (8) Vượt qua 100% 173/173 tests, 0 warnings, Ruff clean, Mypy clean, live smoke test thành công trên Spark Server (:8090).

---

## [2026-09-13] [synthesize] | Phát Hành Release PR #269 / Issue #268 (Gia Cố Spoke Sync, Decouple Archetype & RSA-OAEP Bounds)
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /ccba-new-feature, /boost, /ccba-create-pr, /ccba-release-feature & /ccba-session-retrospective)
- **Affected Files**: `scripts/spoke/sync/`, `scripts/spoke/spoke_bootstrap.py`, `scripts/spoke/decrypt_spoke_registry.py`, `scripts/ccba_platform_cli.py`, `scripts/tests/test_spoke_sync_modules.py`, `.md/knowledge/reports/walkthrough.md`, `.md/knowledge/session_learnings.md`, `.md/knowledge/archive/session_learnings_history.md`
- **Summary**: Hoàn tất giải quyết triệt để Issue #268 và chu trình phát hành PR #269: (1) Củng cố khuyến nghị SDK packages trong `sdk_inspector.py` tự động nhận diện cả packages monorepo nội bộ và packages đã cài trong môi trường ảo qua `importlib.metadata`, loại bỏ cảnh báo giả; (2) Tách bạch hoàn toàn cơ chế fallback Archetype (`archetype_to_project_type`) khỏi Registry Timestamp, ngăn ngừa ghi đè ngoài ý muốn; (3) Khắc phục giới hạn kích thước bản rõ RSA-2048 OAEP SHA-256 (190 bytes) trong `registry.py` bằng cách bóc tách telemetry heartbeat biến động ra `.md/telemetry/spoke_heartbeats.yaml` (gitignored) và chỉ lưu `static_hash` SHA-256 trong payload mã hóa, loại bỏ hoàn toàn ngoại lệ `ValueError: Plaintext is too long` và bảo vệ Git tree của Hub sạch sẽ; (4) Gia cố seams kiểm thử verification trong `coordinator.py` với tùy chọn `--dry-run` an toàn; (5) Bổ sung 34/34 unit test hồi quy toàn diện trong `scripts/tests/test_spoke_sync_modules.py`; (6) Mở và hoàn tất release PR #269, vượt qua 100% Dual-Gate CI, tiếp thu phản biện Copilot Review và squash merge vào `main` tại commit `43a3d970`; (7) Bổ sung RULE-4.9 và RULE-4.10 vào `session_learnings.md` và lưu trữ đầy đủ trong `session_learnings_history.md`.

---

## [2026-09-12] [synthesize] | Đại Chuẩn Hóa 71 Skills ADR-0057, Thăng Cấp Auditor, Ban Hành /ccba-create-pr & Khóa Cứng Zero-Polling (#266, PR #267)
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /ccba-contribute-to-hub, /ccba-release-feature, /learn & /ccba-session-retrospective)
- **Affected Files**: `.agents/skills/`, `docs/skills/`, `docs/rules/execution_guardrails.md`, `scripts/governance/audit_skills_hygiene.py`, `scripts/governance/compile_skills_docs.py`, `.md/knowledge/session_learnings.md`, `.md/knowledge/reports/walkthrough.md`
- **Summary**: Hoàn tất đại chuẩn hóa toàn diện 71 active skills và chu trình kiểm chuẩn phát hành PR #267 giải quyết Issue #266: (1) Chuẩn hóa 100% cấu trúc thư mục kỹ năng theo ADR-0057, dọn sạch dead wood ClaudeKit, quy hoạch tài nguyên non-.md vào `resources/` và `scripts/`, trang bị router index đa tầng `viet_chuyen_nghiep/INDEX.md` (27 submodules); (2) Chính thức thăng cấp công cụ quản trị `scripts/governance/audit_skills_hygiene.py` và tích hợp vào `scripts/validate_skills.py` kèm 40 unit tests tự động; (3) Mở và hoàn tất release PR #267, vượt qua 6/6 checks GitHub Actions CI và đối soát sạch 4/4 comments Copilot Review; (4) Khắc phục triệt để anti-pattern active polling theo phản ánh người dùng qua lệnh `/learn`, xóa bỏ ngoại lệ 2 lần kiểm tra, thiết lập Zero-Tolerance Polling Policy trong `execution_guardrails.md` và bổ sung RULE-4.8 vào `session_learnings.md`; (5) Thăng cấp quy trình tạo Pull Request thành Standalone Kernel Skill độc lập `/ccba-create-pr` (GPI = 14.0 >= 12.0), hoàn thiện Bộ Ba Bất Biến Git Lifecycle (`new-feature` -> `create-pr` -> `release-feature`) và refactor `ccba-contribute-to-hub` kế thừa trực tiếp; (6) Đồng bộ kỹ năng `ccba-mermaid-diagram` vào PIPELINE_MAP và cập nhật chỉ số nền tảng (71 active skills, 0 yellow, 0 red); (7) Đạt 100% Hard Completion Lock (ADR-0058) và đồng bộ Living ADR Matrix.

---

## [2026-09-10] [synthesize] | Phát Hành Release v2.0-beyond-horizon, Đồng Bộ 5 Spokes & Dogfooding Thẩm Tra Đa Bộ Môn PC13 (15 Tickets)
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /boost, /teamwork-preview & /ccba-session-retrospective)
- **Affected Files**: `.agents/skills/`, `packages/ccba-harness/`, `scripts/governance/`, `scripts/sync_spoke.py`, `scripts/sync_hub_adr_matrix.py`, `docs/adr/`, `.md/dogfood/`, `.md/knowledge/session_learnings.md`, `.md/knowledge/archive/session_learnings_history.md`
- **Summary**: Hoàn tất đại nâng cấp hệ thống qua 15 Tickets từ Phase 0 đến Phase 4 và thực nghiệm kiểm chứng Dogfooding: (1) Chính thức phát hành Release `v2.0-beyond-horizon` (commit `a0ac250e`) và đồng bộ hóa thành công 5 Spokes (`sync_spoke.py --all --apply`) với 100% zero-drift và bảo toàn hiến pháp Non-Destructive Section Merge; (2) Chuẩn hóa Single Source of Truth cho toàn bộ 24 Standalone User Rituals và Master Skills (`user-invocable: true`, `command: /...`), dọn dẹp phantom commands và khử trùng lặp frontmatter; (3) Sửa chữa dứt điểm lỗi Hoàn thành non (Premature Completion) trong `ccba-xia` và chuẩn hóa điểm GPI; (4) Triển khai thực chiến liên hoàn Dogfooding Chủ đề 1: Thẩm tra Đa bộ môn PCCC & Kiến trúc trên hồ sơ mẫu *CCBA Horizon Tower* bám sát Luật Xây dựng 2025, NĐ 207/2026/NĐ-CP, NĐ 217/2026/NĐ-CP và NĐ 105/2025/NĐ-CP; (5) Vận hành 3 Swarm Workers song song qua AI Gateway Spark Server (`gemini-3.7-flash`), hợp nhất nguyên tử qua Single-Writer Engine (`execute_swarm_patches`) trong 3.6ms (0 collision); (6) Kiểm chứng Self-Healing Engine (ADR-0058) tự động phục hồi Exit Code 0 trong 414.4ms; (7) Xuất bản Báo cáo Thẩm tra Kỹ thuật Mẫu PC13 hoàn chỉnh; (8) Vượt qua 100% 7 Cổng CI Eval Gates (`run_harness_evals.py --all`) và bộ kiểm định `verify-patch --preset ci`.

---

## [2026-09-08] [adr] | Ban Hành ADR 0057: Two-Stage Granularity Decision Framework & Chỉ Số GPI (PR #244)
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /boost, /teamwork-preview & /ccba-session-retrospective)
- **Affected Files**: `docs/adr/0057-two-stage-granularity-decision-framework-and-gpi.md`, `docs/adr/README.md`, `docs/adr/TRACEABILITY_MATRIX.md`, `packages/ccba-harness/`, `.github/pull_request_template.md`, `.md/knowledge/session_learnings.md`, `.md/knowledge/blueprints/fleet_skills_3tier_migration_blueprint.md`, `.md/knowledge/research_and_studies/research-agent-architecture-packages-skills-orchestrators.md`
- **Summary**: Hoàn tất nghiên cứu và triển khai toàn diện khuyến nghị kiến trúc từ Báo cáo RES-2026-ARCH-001 v1.2: (1) Ban hành chính thức ADR-0057 về Khung Quyết Định Phân Rã Hai Giai Đoạn (Cổng 0 Determinism Gate, Cổng 1 Orchestration Gate) và công thức tính toán chỉ số Granularity & Placement Index (GPI) phân tầng 4 cấp (Tier 1 Package Function, Tier 2A Progressive Reference, Tier 2B Standalone Kernel Skill, Tier 3 Composite Orchestrator); (2) Tích hợp trọn vẹn module `ccba_harness.gpi`, `SkillValidator` và CLI `ccba-harness evaluate-gpi` với 38 unit tests độc lập (100% pass); (3) Cập nhật PR template bắt buộc kiểm tra Cổng 0/1 và bảng điểm GPI; (4) Khảo sát và phân loại toàn diện 100/100 skills trong hạm đội và ban hành Bản kế hoạch di trú `BLUEPRINT-2026-SKILLS-001`; (5) Cập nhật Living ADR Traceability Matrix và bổ sung Chapter 15 vào `session_learnings.md`.

---

## [2026-09-05] [synthesize] | Chuẩn Hóa Namespace Kỹ Năng ADR-0056, Nâng Cấp Release Gate & Đồng Bộ CLI Toàn Trình (PR #240-#243)
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /boost, /ccba-release-feature & /ccba-session-retrospective)
- **Affected Files**: `.agents/skills/`, `.agents/workflows/`, `.agents/resources/`, `scripts/governance/`, `scripts/spoke/`, `scripts/ccba_platform_cli.py`, `scripts/validation/audit_pr_comments.py`, `.md/knowledge/session_learnings.md`
- **Summary**: Hoàn tất chuỗi PR #240, #241, #242, và #243: (1) Chuẩn hóa 61 kỹ năng sang namespace `ccba-*`, di dời toàn bộ 69 legacy workflows sang kỹ năng độc lập hoặc `.md.bak` theo ADR-0056, giải phóng hoàn toàn thư mục workflows và tái biên dịch `catalog.yaml` (99 skills, 0 workflows); (2) Khắc phục triệt để 8/8 phản biện kỹ thuật từ GitHub Copilot Review; (3) Nâng cấp bộ công cụ Release Gate `audit_pr_comments.py` quét 4 tầng (review requests, review bodies có `author.login` và `### 🟡 Changes recommended`, paginated inline comments, PR conversation comments) kèm 8 bài unit test độc lập; (4) Đồng nhất hóa 100% tham số và cờ CLI (`--apply`, `--bootstrap`, `--force`, `--include-sandboxes`, `--archetype`, `--changed`) giữa Unified Platform CLI `ccba_platform_cli.py`, Spoke Synchronizer `scripts/spoke/sync/cli.py` và 5 tài liệu kỹ năng điều phối; (5) Bổ sung Pattern 12 và Pattern 13 vào `session_learnings.md`, vượt qua 100% CI checks GitHub Actions và toàn bộ các bộ test suite.

---

## [2026-09-03] [adr] | Phát Hành Two-Tier ADR Traceability Matrix & Hardened Type Safety (#231, PR #236)
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /ccba-new-feature, /ccba-create-pr, /ccba-release-feature & /ccba-session-retrospective)
- **Affected Files**: `scripts/sync_hub_adr_matrix.py`, `tests/governance/test_sync_adr_matrix.py`, `docs/adr/TRACEABILITY_MATRIX.md`, `docs/adr/README.md`, `.agents/skills/ccba-adr-lifecycle/SKILL.md`, `packages/ccba-legal-intel/`, `pyproject.toml`, `.md/knowledge/issues/issue-231.md`
- **Summary**: Hoàn tất PR #236 giải quyết Issue #231: (1) Nâng cấp `sync_hub_adr_matrix.py` hiện thực hóa kiến trúc Ma Trận Hai Tầng (Two-Tier Model): Tier 1 (Platform Constitution 55 ADRs Hub kèm Living Skill Radar) và Tier 2 (Domain-Specific ADRs Spoke), bảo toàn 100% quyết định kiến trúc cục bộ tại Spoke mà không gây xung đột số hiệu (ID Collision); (2) Tích hợp cơ chế Non-Destructive Section Preservation cho các bảng đối soát và ghi chú tùy biến; (3) Bổ sung cờ `--check` (CI Gate mode) và `--dry-run`; (4) Tiếp thu 100% khuyến nghị từ GitHub Copilot Review: chuẩn hóa regex trạng thái đa biến thể, lọc bỏ tệp non-ADR, chống lặp số thứ tự chú thích bảng, và gỡ bỏ hoàn toàn suppression mypy bao quát (`ignore_errors = true`) để đạt chuẩn kiểm định kiểu tĩnh nghiêm ngặt; (5) Vượt qua toàn bộ 6/6 checks GitHub Actions CI và 164/164 tests trong Pre-release Gate.

---

## [2026-09-03] [synthesize] | Hoàn Tất Triển Khai Presentation Builder Swiss Minimalist & Storytelling With You (#230, PR #235)
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /ccba-research, /ccba-implement, /ccba-release-feature & /session_retrospective)
- **Affected Files**: `packages/ccba-ooxml/`, `packages/ccba-legal-intel/`, `.agents/skills/seminar-builder/`, `.md/knowledge/ccba_brand_identity_guidelines.md`, `.md/knowledge/research_and_studies/`, `.md/seminars/2026/demo_seminar_nd217_luatxd2025.*`, `.md/knowledge/issues/issue-230.md`
- **Summary**: Hoàn tất PR #235 giải quyết Issue #230: (1) Xây dựng Deep Seam `ccba_ooxml.pptx` gồm `MarkdownDeckParser` và `DeckBuilder` hỗ trợ đầy đủ các Layouts Swiss Minimalist (12-column grid, 60/40 Split, Bento Grid) và Cole Knaflic Storytelling archetypes (Big Idea, Visual Agenda, Process Stepper, Quote); (2) Ban hành Quy chuẩn Nhận diện Thương hiệu CCBA v3.4 (`ccba_brand_identity_guidelines.md`) với Design Tokens tương phản WCAG 2.1 AA; (3) Tích hợp CLI `python -m ccba_ooxml build-deck` và cập nhật skill `seminar-builder`; (4) Đồng bộ hóa toàn diện 100% dữ liệu sang **Luật Xây dựng 2025** và **Nghị định 217/2026/NĐ-CP**; (5) Vượt qua 100% 6/6 checks GitHub Actions CI và 223/223 unit tests.

---

## [2026-08-23] [synthesize] | Thẩm Định & Hợp Nhất Đề Xuất PR #216 (OKF v2.2 Table & Direct Form Extractor) & PR #215/217 (ADR 0045)
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /ccba-review-proposal & /ccba-session-retrospective)
- **Affected Files**: `packages/ccba-legal-intel/`, `scripts/spoke/sync/`, `.agents/proposals/`, `.agents/skills/platform-loader/catalog.yaml`, `.agents/skills/legal-advisor/`, `scripts/tests/`
- **Summary**: Hoàn tất thẩm định và hợp nhất PR #216 (OKF v2.2 Table & Direct Form Template Extractor) và PR #215/217 (Hub-Spoke Standardization, Cleanliness Gate, Enum Aliasing): (1) Khử hoàn toàn hardcode slug bảng, sinh 2D GFM Pipe Tables và bóc tách trực tiếp biểu mẫu `Mẫu số XX/...` vào `templates/`; (2) Bổ sung canonical models `ASTNode` và `PatchAction`; (3) Tái cấu trúc bộ đồng bộ Spoke `spoke_synchronizer.py` thành sub-package module sâu `scripts/spoke/sync/`; (4) Giải quyết xung đột merge với `main` và squash-merge vào `main` tại commit `cd1a2bd6`; (5) Cập nhật trạng thái `merged` cho 3 proposals và biên dịch lại `catalog.yaml` (74 skills, 65 workflows); (6) Vượt qua 100% Spoke Leakage Guard, ruff linter và 261/261 unit tests.

---

## [2026-08-22] [synthesize] | Chuẩn Hóa Bộ Đôi Upstream Contribution /ccba-issue-to-hub & /ccba-contribute-to-hub (#209)
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /ccba-release-feature & /ccba-session-retrospective)
- **Affected Files**: `.agents/workflows/ccba-issue-to-hub.md`, `.agents/workflows/ccba-contribute-to-hub.md`, `.agents/workflows/ccba-propose-to-hub.md`, `.agents/workflows/ccba-new-feature.md`, `.agents/skills/platform-loader/catalog.yaml`, `.agents/skills/architecture-sync/SKILL.md`, `README.md`, `CONTRIBUTING.md`, `tests/test_upstream_workflows.py`, `.md/knowledge/session_learnings.md`
- **Summary**: Hoàn tất PR #213 giải quyết Issue #209: (1) Chuẩn hóa bộ đôi Upstream Contribution đối xứng tách bạch 2 pha: `/ccba-issue-to-hub` (soạn RFC & mở GitHub Issue) và `/ccba-contribute-to-hub` (đóng gói code/tests & mở PR lên Hub); (2) Giữ `/ccba-propose-to-hub` làm Alias tương thích ngược; (3) Tối ưu hóa `/ccba-new-feature` tự động bóc tách Issue metadata qua `gh issue view` và sửa đường dẫn test `scripts/eval/run_harness_evals.py`; (4) Chuẩn hóa tiền tố nhánh sang `feat/...` theo `git_conventions.md`; (5) Vượt qua toàn bộ 6/6 checks GitHub Actions CI và Pre-release Gate (81/81 tests).

---

## [2026-08-17] [synthesize] | Chuẩn Hóa Toàn Trình 4 Workflows Spoke & Archetype-Aware Setup Skills (ADR 0041)
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /ccba-session-retrospective)
- **Affected Files**: `.agents/workflows/ccba-init-spoke.md`, `.agents/workflows/ccba-adopt-spoke.md`, `.agents/workflows/ccba-update-spoke.md`, `.agents/workflows/ccba-propose-to-hub.md`, `.agents/skills/ccba-setup-skills/SKILL.md`, `.agents/skills/ccba-setup-skills/templates/domain.md`, `scripts/spoke/spoke_adopter.py`, `scripts/adopt_spoke.py`, `tests/test_spoke_adopter.py`
- **Summary**: Hoàn tất rà soát và chuẩn hóa toàn trình 4 Workflows quản trị Spoke theo ADR 0041 (5 Archetypes): (1) Bổ sung trường `archetype` vào `workspace_context.yaml`, sửa lỗi biến PowerShell Maskara hook trong `/ccba-init-spoke`; (2) Bổ sung nhận diện Archetype và xử lý an toàn cho Delivery Spoke không dùng Git trong `/ccba-adopt-spoke`; (3) Tích hợp kiểm tra sức khỏe và rà soát kỹ năng mồ côi (Orphaned Skills) trong `/ccba-update-spoke`; (4) Thêm `proposed_by_archetype` và rào chắn linter kiểm thử trước khi mở PR trong `/ccba-propose-to-hub`; (5) Nâng cấp `ccba-setup-skills` tự động gợi ý Issue Tracker thông minh dựa trên Archetype và chuẩn hóa đường dẫn ADRs về `docs/adr/`; (6) Cập nhật engine `SpokeAdopter` và bổ sung unit tests pass 100% (18/18).

---

## [2026-08-17] [synthesize] | Tối Ưu Hóa Hiệu Năng LinkAuditor, Hiện Đại Hóa Async Test & Tinh Gọn Analyzer
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /ccba-release-feature & /ccba-session-retrospective)
- **Affected Files**: `scripts/governance/link_auditor.py`, `scripts/scaffolding/arch_stats.py`, `packages/mdconverter/`, `packages/ccba-pdf-prep/`, `packages/ccba-ai/tests/`, `packages/ccba-notebooklm/tests/`, `pyproject.toml`
- **Summary**: Hoàn tất PR #204 giải quyết 5 ứng viên tối ưu hóa kiến trúc: (1) Tối ưu hóa LinkAuditor đạt gia tốc 17.6x (<1.3s) bằng Directory Exclusions (-95.7% traversal), Scoped Caching, và Dynamic Skill Scope; (2) Hiện đại hóa toàn bộ 30+ async test fixtures sang `@pytest.mark.asyncio` với `asyncio_mode = "strict"`; (3) Khắc phục lỗi charmap encoding CP1252 trên Windows cho arch_stats.py; (4) Đồng bộ hóa model alias `qwen-local-primary` theo ADR-025 và tinh gọn `mdconverter/core/analyzer.py` thành re-export trực tiếp 10 dòng; (5) Tiếp thu và giải quyết 100% review comments từ GitHub Copilot, bổ sung kiểm thử hồi quy và vượt qua toàn bộ 10/10 test suites trong Pre-release Gate.

---

## [2026-08-16] [synthesize] | Dọn Dẹp Kỹ Thuật, Khử Xung Đột Định Danh & Tiến Hóa Kỹ Năng Rà Soát Kiến Trúc
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên /ccba-release-feature & /ccba-session-retrospective)
- **Affected Files**: `.agents/skills/improve-codebase-architecture/SKILL.md`, `.md/knowledge/session_learnings.md`, `packages/mdconverter/`, `packages/ccba-legal-intel/`, `packages/ccba-pdf-prep/`, `scripts/spoke/`, `scripts/update_arch_stats.py`
- **Summary**: Hoàn tất PR #201 giải quyết xung đột định danh `AppendixExtractor` (thay thế `TableReconstructor` trong mdconverter), chuẩn hóa relative imports trong ccba-pdf-prep, thu gọn xuất khẩu `ccba_legal` về 23 Deep Seams/DTOs cốt lõi, lưu trữ script di trú cũ vào `.md/knowledge/archive/`. Tiến hóa kỹ năng `improve-codebase-architecture` (v1.3.0) với 5 Cổng Phản Biện Bắt Buộc (cưỡng chế P6.21 phân biệt Glue Code vs Domain Logic, P6.22 Unique Symbol Naming, và P6.23 Hard Caller Count Gate).

---

## [2026-08-16] [ingest] | Hoàn Tất Triển Khai Động Cơ Tự Tiến Hóa Tài Liệu (Doc-Auto-Evolution)
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Wayfinder Ticket D-01 -> D-04)
- **Affected Files**: `scripts/eval/doc_refactor_daemon.py`, `scripts/tests/test_doc_refactor_daemon.py`, `scripts/cron/run_nightly_tuner.sh`, `scripts/cron/run_nightly_tuner.bat`, `scripts/deploy/bootstrap_spark_server.sh`, `.md/knowledge/issues/doc-auto-evolution/`
- **Summary**: Xây dựng Deep Seam `DocAutoEvolutionEngine` bọc toàn bộ chu trình tự bảo trì tài liệu tri thức LLM-Wiki. Tích hợp động cơ `CodeGroundingEngine` quét AST in-memory (< 150ms), rào chắn `ZeroDeletionGuard`, `Parse-Protection Guard`, và `PillarBalanceAuditor`. Tích hợp quy trình chạy tự động 00:00 hàng đêm trên Server Spark tạo Pull Request và gửi thông báo Telegram.

---

## [2026-08-16] [adr] | Ban Hành ADR 0043: Decoupled Resilience & Active Development Cho IDOP-CCBA-WAY
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên Socrates /ccba-grill-with-docs)
- **Affected Files**: `docs/adr/0043-idop-active-dev-resilience-and-fallback.md`, `scripts/eval/nightly_tuner_daemon.py`, `scripts/tests/test_idop_schema_compatibility.py`, `CONTEXT.md`
- **Summary**: Ban hành cơ chế Hàng Đợi Lưu Trữ Cục Bộ (`.md/idop_staged/`), kiểm soát biến động Schema (`CI Schema Drift Gate`) và xác thực môi trường mềm (`Zero-Config Dual-Mode Auth`), đảm bảo Zero-Downtime cho dự án và cô lập tuyệt đối cho Nightly Auto-Tuner Daemon trên Server Spark.

---

## [2026-08-16] [adr] | Ban Hành ADR 0042: Tiered Pre-Submission Gate & Tri-Repo Server Sync
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên Socrates /ccba-grill-with-docs)
- **Affected Files**: `docs/adr/0042-tiered-ai-pre-submission-gate-and-tri-repo-sync.md`, `scripts/deploy/bootstrap_spark_server.sh`, `scripts/cron/run_nightly_tuner.sh`, `CONTEXT.md`
- **Summary**: Ban hành Rào Chắn Tiền Kiểm Định 3 Cấp Độ (Tier 1: Auto-Block, Tier 2: Director Override, Tier 3: Advisory) trình Viện IBST và cơ chế đồng bộ chuỗi ba kho lưu trữ cốt lõi trên Server Spark lúc 00:00 hàng đêm.

---

## [2026-08-16] [adr] | Ban Hành ADR 0041: Hub-Spoke Ecosystem Taxonomy & 5 Archetypes
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên Socrates /ccba-grill-with-docs)
- **Affected Files**: `docs/adr/0041-hub-spoke-ecosystem-taxonomy-and-archetypes.md`, `CONTEXT.md`
- **Summary**: Chuẩn hóa cấu trúc phân loại 5 Archetypes của hệ sinh thái (`platform_hub`, `enterprise_governance`, `knowledge_corpus`, `project_delivery`, `specialized_extension`) và ban hành Bộ Lọc 4 Tiêu Chí Vàng để xác định Spoke clone về Server.

---

## [2026-08-16] [ingest] | Khai Phá Log Lỗi Thực Tế Từ Sản Xuất & Nâng Cấp Resilient Log Miner

- **Author / Agent**: AI Lead Agent
- **Affected Files**: `scripts/eval/log_eval_miner.py`, `scripts/tests/test_log_eval_miner.py`, `.agents/skills/eval-gate/test_cases/`
- **Summary**: Hoàn tất đợt khai phá 507 file transcript trong `.gemini/antigravity/brain/` (2,205 tương tác), phát hiện và trích xuất 177 test cases thực chiến mới cho các bộ môn (PCCC Audit: 15, Legal Intel: 15, Academic Writing: 3, BigBIM: 3, Copywriting: 1, Agent Orchestration: 34, General Software: 106). Nâng cấp tính năng duyệt cây thư mục an toàn (Safe Directory Walk chống lỗi Windows junction `wt`), tự động làm sạch thẻ XML prompt và phân loại tự động miền nghiệp vụ.

---

## [2026-08-16] [ingest] | Phát Hành Git-Ratchet Autonomous Skill Auto-Tuner (ccba-autoresearch)

- **Author / Agent**: AI Lead Agent
- **Affected Files**: `scripts/eval/git_ratchet_tuner.py`, `scripts/tests/test_git_ratchet_tuner.py`, `.agents/workflows/ccba-autoresearch.md`, `.agents/skills/eval-gate/program_template.md`
- **Summary**: Hiện thực hóa cơ chế tối ưu hóa tự động theo mô hình bánh cóc Git của Karpathy (autoresearch). Tự động commit khi điểm số tăng và rollback sạch qua git checkout khi điểm số giảm hoặc dính Điểm Liệt.

---

## [2026-08-16] [ingest] | Tích Hợp XML Prompt Envelopes & Evaluator-Optimizer Loop Vào ccba-ai (Ticket 4)
- **Author / Agent**: AI Lead Agent
- **Affected Files**: `packages/ccba-ai/src/ccba_ai/prompting.py`, `packages/ccba-ai/tests/test_prompting.py`
- **Summary**: Bổ sung `xml_envelope`, `parse_xml_tags`, và mẫu lặp tự sửa lỗi Generator <-> Evaluator `evaluator_optimizer_loop` (Technique 15) với giới hạn lặp an toàn max_iterations=3.

---

## [2026-08-16] [ingest] | Nâng Cấp Failure-to-Eval Flywheel Trong log_eval_miner.py (Ticket 3)
- **Author / Agent**: AI Lead Agent
- **Affected Files**: `scripts/eval/log_eval_miner.py`, `scripts/tests/test_log_eval_miner.py`
- **Summary**: Nâng cấp công cụ khai phá log lỗi thực chiến từ transcript.jsonl với 3 nhóm lỗi (Router Refusal, Tool Exception, Outdated Citation), sinh chuẩn EvalItem tương thích ccba_harness và cờ --auto-inject chống trùng lặp.

---

## [2026-08-16] [ingest] | Phát Hành Local Multi-Scorer Eval Engine ccba_harness.evals (Ticket 1)
- **Author / Agent**: AI Lead Agent
- **Affected Files**: `packages/ccba-harness/src/ccba_harness/evals/`, `packages/ccba-harness/tests/test_evals_engine.py`
- **Summary**: Xây dựng framework benchmark AI cục bộ chuẩn hóa với EvalRunner, CodeScorers (< 1ms), và LLMRubricScorer (Anthropic CoT Likert 1-5), hỗ trợ rào chắn Điểm Liệt Fail-Fast.

---

## [2026-08-16] [guideline] | Ban Hành Quy Chuẩn Tiêu Chí Thành Công & Rubrics Định Lượng Đa Miền
- **Author / Agent**: Kỹ sư trưởng & AI Lead Agent (Phiên phỏng vấn Socrates /ccba-grilling)
- **Affected Files**: [guidelines/domain_success_criteria_rubrics.md](guidelines/domain_success_criteria_rubrics.md)
- **Summary**: Thiết lập và lượng hóa barem điểm đa chiều (Hybrid Scoring 0–100% kết hợp Likert 1–5), áp dụng rào chắn Điểm Liệt (Hard Floor Fail-Fast) cho 3 miền nghiệp vụ chính: Thẩm tra QC PCCC/MEP (40/30/20/10), Pháp điển VBHN (35/35/20/10), và Viết Học thuật/Seminar (35/25/25/15).

---

## [2026-08-16] [synthesize] | Thiết Lập Cấu Trúc LLM-Wiki & Master Catalog
- **Author / Agent**: AI Lead Agent
- **Affected Files**: [index.md](index.md), [log.md](log.md), [scripts/governance/wiki_health_linter.py](../../scripts/governance/wiki_health_linter.py)
- **Summary**: Hiện thực hóa kiến trúc 3 tầng LLM-Wiki theo mô hình Andrej Karpathy. Phân nhóm toàn bộ kho tài liệu `.md/knowledge/` thành 8 trục tri thức, thiết lập nhật ký đột biến append-only và công cụ kiểm định sức khỏe Wiki Health Linter.

---

## [2026-08-15] [synthesize] | Tổng Kết 30+ Nguyên Lý Thực Chiến Trong Session Learnings
- **Author / Agent**: Core Engineering Team & AI Agents
- **Affected Files**: [session_learnings.md](session_learnings.md)
- **Summary**: Đúc rút và hệ thống hóa 30 bài học kinh nghiệm sâu sắc về kiểm soát process lock, SLA kiểm thử 2 tầng (< 2s), tương thích Windows PowerShell stream, và kiến trúc Deep Modules.

---

## [2026-08-10] [adr] | Quyết Định Tách Biệt Ranh Giới Giữa Hub Và Spoke (ADR-0010 & ADR-0013)
- **Author / Agent**: Lead Architect
- **Affected Files**: [specs_and_roadmaps/Arch_Proposal_Hub_Spoke_Sync_Strategy.md](specs_and_roadmaps/Arch_Proposal_Hub_Spoke_Sync_Strategy.md), [specs_and_roadmaps/adr_0013_knowledge_evolution_loop.md](specs_and_roadmaps/adr_0013_knowledge_evolution_loop.md)
- **Summary**: Ban hành nguyên tắc Hub là nơi lưu trữ tools/skills/packages/rules tập trung; Spoke là nơi chứa ngữ cảnh dự án cụ thể. Cưỡng chế quy tắc Reuse-First Gate.

---

## [2026-08-01] [ingest] | Nạp Kho Tri Thức Pháp Lý Xây Dựng & Thư Viện Pháp Luật
- **Author / Agent**: Automation Pipeline Team
- **Affected Files**: `extracted_docs/`, [research_and_studies/thuvienphapluat_structure_analysis.md](research_and_studies/thuvienphapluat_structure_analysis.md), [specs/spec-deepen-tvpl-crawler.md](specs/spec-deepen-tvpl-crawler.md)
- **Summary**: Nạp dữ liệu toàn văn và trích xuất cấu trúc các bộ quy chuẩn trọng yếu (QCVN 06:2022/BXD, SĐ 1:2023, Luật Xây dựng 2014/2020, NĐ 105/2025/NĐ-CP) vào kho tri thức pháp lý trung tâm.
