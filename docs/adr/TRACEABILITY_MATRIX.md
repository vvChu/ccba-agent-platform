# 🗺️ Living Architecture Traceability Matrix & Skill Radar

> **Mục tiêu:** Ma trận tự động theo dõi mối quan hệ giữa các **Quyết định Kiến trúc (ADR)** và các **Kỹ năng (Skills) / Hiến pháp Vận hành**.

*(Tệp này được biên dịch tự động bởi `scripts/sync_hub_adr_matrix.py` — Không chỉnh sửa thủ công)*

---

## 🏛️ CCBA Platform Architectural Decisions

| Mã ADR | Tiêu đề Quyết Định | Trạng thái | Tài Liệu & Skills Đang Tuân Thủ / Viện Dẫn |
| :--- | :--- | :---: | :--- |
| [ADR 0001](0001-standardize-skill-steps-format.md) | **Standardize Skill Steps Format for Linter Validation** | ✅ ACCEPTED | `.agents/workflows/ccba-build-skill.md` |
| [ADR 0002](0002-hierarchical-skill-validation.md) | **Hierarchical Skill Validation Parser with Keyword Exclusion** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0003](0003-object-oriented-plan-management.md) | **Object-Oriented Plan Management with File-based Concurrency Lock** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0004](0004-academic-writing-microstructure-auditing.md) | **Academic Writing Microstructure Auditing and Compliance Checks** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0005](0005-academic-paper-formatting-and-citations.md) | **Academic Paper Title Page Formatting and Citation Auditing** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0006](0006-skills-quality-alignment-for-academic-writing.md) | **Quality and Context Optimization for Academic Writing Skill** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0007](0007-multimodal-youtube-learning-and-transcription.md) | **Multimodal Video Ingestion and Belief Archaeology Analysis** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0008](0008-spoke-classification-and-functional-ownership.md) | **Spoke Classification and Functional Ownership Mapping in CCBA** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0009](0009-hub-spoke-sync-and-partition-strategy.md) | **Hub-Spoke Synchronization and Directory Partitioning Strategy** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0010](0010-skills-integration-and-rag-boundaries.md) | **Phân Định Ranh Giới Tích Hợp Kỹ Năng Nghiên Cứu & Mẫu Thử** | ✅ ACCEPTED | `.agents/skills/ccba-adr-lifecycle/SKILL.md`<br>`.agents/skills/ccba-ai-qc-pccc-audit/SKILL.md`<br>`.agents/skills/excalidraw-diagram/SKILL.md`<br>`.agents/skills/improve-codebase-architecture/SKILL.md` |
| [ADR 0017](0017-dynamic-override-notebook-ids-via-environment-variables.md) | **Dynamic Override of Notebook IDs via Environment Variables** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0018](0018-remove-idop-scaffolder-from-hub.md) | **Loại bỏ skill ccba-idop-scaffolder khỏi Central Hub** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0019](0019-port-matt-pocock-engineering-skills.md) | **Đồng bộ Quy trình Triển khai Kỹ nghệ từ Thượng nguồn & Dọn dẹp Thành phần Lỗi thời** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0020](0020-port-and-adapt-high-priority-upstream-skills.md) | **Quyết định Port và Địa hóa nhóm Skill Upstream Ưu tiên cao** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0021](0021-dual-mode-workspace-and-bigbim-retention.md) | **Dual Mode Workspace And Bigbim Retention** | ✅ ACCEPTED | `.agents/skills/ccba-legal-ingest/SKILL.md`<br>`.agents/skills/ccba-legal-intel/SKILL.md`<br>`.agents/workflows/ccba-legal-ingest.md`<br>`.md/knowledge/session_learnings.md` |
| [ADR 0022](0022-restrict-fast-flag-in-xia-challenge-gate.md) | **Restrict Fast Flag In Xia Challenge Gate** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0023](0023-skill-auto-tuner-integration-via-skillopt.md) | **Tích hợp CCBA Skill Auto-Tuner dựa trên phương pháp Microsoft SkillOpt** | ✅ ACCEPTED | `.agents/skills/notebooklm-connector/SKILL.md` |
| [ADR 0024](0024-deepen-tvpl-crawler-module-interface.md) | **Tái cấu trúc Sâu (Deep Module) cho Phân hệ TVPL VIP Crawler** | ✅ ACCEPTED | `.agents/skills/legal-advisor/SKILL.md` |
| [ADR 0025](0025-ai-gateway-client-configuration-standardization.md) | **Standardizing AI Gateway Client Configuration and Model Aliases** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0026](0026-isolated-test-runner-and-timeout-policy.md) | **Isolated Test Execution and Timeout Policy for Agent Stability** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0027](0027-deepen-notebooklm-service-module.md) | **Deepen NotebookLMService Module & Separate Service Layer** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0028](0028-deepen-detached-execution-engine.md) | **Deepen DetachedExecutionEngine in `scripts/eval/process_safety.py`** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0029](0029-ai-gateway-client-integration-contract.md) | **AI Gateway Client Integration Contract & 4 Model Archetypes Standardization** | ✅ ACCEPTED | `.agents/skills/ccba-legal-ingest/SKILL.md`<br>`.agents/workflows/ccba-legal-ingest.md` |
| [ADR 0030](0030-progressive-disclosure-and-instruction-budget-optimization.md) | **Progressive Disclosure and Instruction Budget Optimization for AGENTS.md** | ✅ ACCEPTED | `.agents/skills/ccba-legal-ingest/SKILL.md`<br>`.agents/workflows/ccba-legal-ingest.md` |
| [ADR 0031](0031-capability-first-instructions-and-stale-path-mitigation.md) | **Capability-First Instructions and Stale Path Mitigation** | ✅ ACCEPTED | `.agents/skills/ccba-legal-ingest/SKILL.md`<br>`.agents/skills/ccba-legal-intel/SKILL.md`<br>`.agents/skills/tvpl-vip-crawler/SKILL.md`<br>`.agents/workflows/ccba-legal-ingest.md`<br>`.md/knowledge/session_learnings.md` |
| [ADR 0032](0032-monorepo-hierarchical-agents-md.md) | **Monorepo Hierarchical AGENTS.md for CCBA Packages** | ✅ ACCEPTED | `.agents/skills/ccba-adr-lifecycle/SKILL.md`<br>`.md/knowledge/session_learnings.md` |
| [ADR 0033](0033-automation-first-quality-enforcement.md) | **Automation-First Code Quality Enforcement and Instruction Pruning** | ✅ ACCEPTED | `.agents/workflows/ccba-graduate-rd.md`<br>`.md/knowledge/session_learnings.md` |
| [ADR 0034](0034-cross-agent-parity-bridge.md) | **Cross-Agent Parity Bridge for AGENTS.md and CLAUDE.md** | ✅ ACCEPTED | `.agents/skills/ccba-legal-ingest/SKILL.md`<br>`.agents/skills/ccba-legal-intel/SKILL.md`<br>`.agents/workflows/ccba-legal-ingest.md` |
| [ADR 0035](0035-polyglot-deep-modules-and-subagent-guardrails.md) | **Polyglot Deep Modules Enforcement and Sub-Agent Review Guardrails** | ✅ ACCEPTED | `.agents/skills/ccba-legal-ingest/SKILL.md`<br>`.agents/skills/ccba-legal-intel/SKILL.md`<br>`.agents/skills/ccba-research/SKILL.md`<br>`.agents/skills/ccba-teamwork/SKILL.md`<br>`.agents/skills/notebooklm-connector/SKILL.md`<br>`.agents/skills/tvpl-vip-crawler/SKILL.md`<br>`.agents/workflows/ccba-legal-ingest.md` |
| [ADR 0036](0036-brownfield-spoke-adoption-and-non-destructive-onboarding.md) | **Brownfield Spoke Adoption and Non-Destructive Onboarding** | ✅ ACCEPTED | `.agents/skills/ccba-legal-ingest/SKILL.md`<br>`.agents/skills/ccba-legal-intel/SKILL.md`<br>`.agents/skills/legal-document-tracker/SKILL.md`<br>`.agents/skills/tvpl-vip-crawler/SKILL.md`<br>`.agents/workflows/ccba-init-spoke.md`<br>`.agents/workflows/ccba-legal-ingest.md` |
| [ADR 0037](0037-constitution-driven-traceability-matrix.md) | **Constitution-Driven Traceability Matrix Pattern & Dynamic Knowledge Pointers** | ✅ ACCEPTED | `.agents/skills/ccba-adr-lifecycle/SKILL.md`<br>`.agents/skills/ccba-legal-ingest/SKILL.md`<br>`.agents/skills/ccba-legal-intel/SKILL.md`<br>`.agents/skills/tvpl-vip-crawler/SKILL.md`<br>`.agents/workflows/ccba-legal-ingest.md` |
| [ADR 0038](0038-unified-okf-v2-bundle-specification.md) | **Chuẩn Hóa Cấu Trúc Gói Tri Thức Hợp Nhất OKF Bundle v2.0 (Unified OKF v2.0 Bundle Specification)** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0039](0039-autonomous-crawler-to-spoke-ingestion-protocol.md) | **Giao Thức Chuyển Giao Tự Động Từ VIP Crawler (Hub) Sang Ingestion Engine (Spoke)** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0040](0040-skills-hierarchy-and-automated-governance.md) | **Phân Tầng Kỹ Năng Kim Tự Tháp 3 Tầng & Rào Chắn Quản Trị Tự Động (Hard CI Gate)** | ✅ ACCEPTED | `.agents/skills/sync-upstream/SKILL.md`<br>`.agents/workflows/ccba-build-skill.md` |
| [ADR 0041](0041-hub-spoke-ecosystem-taxonomy-and-archetypes.md) | **Hub-Spoke Ecosystem Taxonomy, Spoke Archetypes, and Extensibility Framework** | ✅ ACCEPTED | `.agents/skills/ccba-setup-skills/SKILL.md`<br>`.agents/workflows/ccba-adopt-spoke.md`<br>`.agents/workflows/ccba-init-spoke.md`<br>`CONTEXT.md` |
| [ADR 0042](0042-tiered-ai-pre-submission-gate-and-tri-repo-sync.md) | **Tiered Multi-Severity AI Pre-Submission Gate and Tri-Repo Server Synchronization Protocol** | ✅ ACCEPTED | `CONTEXT.md` |
| [ADR 0043](0043-idop-active-dev-resilience-and-fallback.md) | **Decoupled Resilience, Schema Contract Drift Gate, and Dual-Mode Authentication for IDOP-CCBA-WAY Active Development** | ✅ ACCEPTED | `CONTEXT.md` |
| [ADR 0044](0044-spoke-hub-package-bootstrap-standard.md) | **Hub-Spoke Package Bootstrap Standardization & Editable Install Protocol** | ✅ ACCEPTED | `.agents/workflows/ccba-init-spoke.md`<br>`.agents/workflows/ccba-new-feature.md`<br>`.agents/workflows/ccba-update-spoke.md` |
| [ADR 0045](0045-hub-proposal-ingestion-governance.md) | **Hub Proposal Ingestion & Lifecycle Governance Standard (Hybrid Gate & Supervised Self-Healing)** | ✅ ACCEPTED | `.agents/workflows/ccba-contribute-to-hub.md`<br>`.agents/workflows/ccba-graduate-rd.md`<br>`.agents/workflows/ccba-init-spoke.md`<br>`.agents/workflows/ccba-propose-to-hub.md`<br>`.agents/workflows/ccba-review-proposal.md` |
| [ADR 0046](0046-personal-sandbox-lifecycle-and-charter-2026-alignment.md) | **Personal Sandbox Spoke Lifecycle, Registry TTL, and CCBA Charter 2026 Alignment** | ✅ ACCEPTED | `.agents/skills/ccba-setup-skills/SKILL.md`<br>`.agents/workflows/ccba-promote-sandbox.md`<br>`.agents/workflows/ccba-update-spoke.md`<br>`CONTEXT.md` |
| [ADR 0047](0047-catalog-manifest-compiler-and-frontmatter-ssot.md) | **Catalog Manifest Compiler & Frontmatter Single Source of Truth (SSOT)** | ✅ ACCEPTED | `.agents/skills/architecture-sync/SKILL.md`<br>`.agents/skills/ccba-adr-lifecycle/SKILL.md`<br>`.agents/skills/writing-great-skills/SKILL.md`<br>`.agents/workflows/ccba-new-feature.md`<br>`.agents/workflows/ccba-review-proposal.md` |
| [ADR 0048](0048-tvpl-vip-digital-pdf-priority-and-session-engine.md) | **TVPL VIP Digital PDF Priority & Persistent Chrome Profile Session Engine** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0049](0049-okf-v2-4-universal-agent-centric-specification-and-cloud-vault.md) | **OKF v2.4 Universal Agent-Centric Specification & Multi-Asset Cloud Vault** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0050](0050-automated-legal-sync-and-mock-data-isolation.md) | **Automated Legal Sync Pipeline & Mock Data Isolation for Spokes** | ✅ ACCEPTED | `.agents/skills/ccba-legal-intel/SKILL.md`<br>`.agents/workflows/ccba-update-spoke.md`<br>`CONTEXT.md` |
| [ADR 0051](0051-hub-spoke-sync-hardening-constitution-preservation-and-virtual-fallback.md) | **Hub-Spoke Sync Hardening, Constitution Preservation & Virtual Hub Fallback** | ✅ ACCEPTED | `.agents/skills/ccba-adr-lifecycle/SKILL.md` |
| [ADR 0052](0052-boost-deep-reasoning-protocol-and-escalation-gate.md) | **Boost Deep Reasoning Protocol, Early Escalation & Multi-Agent Hierarchy** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0053](0053-teamwork-multi-agent-orchestration-framework.md) | **Teamwork Multi-Agent Orchestration Framework & Exclusive Seam Protocol** | ✅ ACCEPTED | `.agents/skills/ccba-teamwork/SKILL.md` |
| [ADR 0054](0054-antigravity-lifecycle-hooks-and-security-bridge.md) | **Antigravity Lifecycle Hooks & Security Bridge — Adapter Bridge Architecture** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
| [ADR 0055](0055-ccba-ai-multi-tier-failover-and-mock-provider.md) | **CCBA AI Multi-Tier Failover Matrix, Antigravity CLI Bridge, Local Ollama & Offline Mock Provider** | ✅ ACCEPTED | *Chưa có liên kết trực tiếp* |
