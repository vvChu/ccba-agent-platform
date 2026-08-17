# 📜 CCBA Knowledge Base Mutation Log (Append-Only Log)

> **Mô tả:** Nhật ký dòng thời gian bất biến (Append-Only Journal) ghi nhận toàn bộ các đợt nạp tài liệu (`[ingest]`), tổng hợp tri thức (`[synthesize]`), ban hành quy chuẩn (`[guideline]`), quyết định kiến trúc (`[adr]`), và bảo trì linter (`[linter]`) trong LLM-Wiki.

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
