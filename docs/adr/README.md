# 🏛️ CCBA Agent Services Platform — Architectural Decision Records (ADRs)

Tài liệu này lưu trữ toàn bộ các Quyết định Kiến trúc (ADRs) định hình nền tảng **CCBA Agent Services Platform (Hub)**, bao gồm Skills Framework, AI Gateway, Monorepo Packages, Governance, và Hub-Spoke Ecosystem.

*(Tệp này được biên dịch tự động bởi `scripts/sync_hub_adr_matrix.py` — Không chỉnh sửa thủ công)*

---

## 📑 Danh Mục Quyết Định Kiến Trúc (0001 — 0058)

| Mã ADR | Tiêu đề | Trạng thái |
| :--- | :--- | :---: |
| [ADR 0001](0001-standardize-skill-steps-format.md) | Standardize Skill Steps Format for Linter Validation | ✅ ACCEPTED |
| [ADR 0002](0002-hierarchical-skill-validation.md) | Hierarchical Skill Validation Parser with Keyword Exclusion | ✅ ACCEPTED |
| [ADR 0003](0003-object-oriented-plan-management.md) | Object-Oriented Plan Management with File-based Concurrency Lock | ✅ ACCEPTED |
| [ADR 0004](0004-academic-writing-microstructure-auditing.md) | Academic Writing Microstructure Auditing and Compliance Checks | ✅ ACCEPTED |
| [ADR 0005](0005-academic-paper-formatting-and-citations.md) | Academic Paper Title Page Formatting and Citation Auditing | ✅ ACCEPTED |
| [ADR 0006](0006-skills-quality-alignment-for-academic-writing.md) | Quality and Context Optimization for Academic Writing Skill | ✅ ACCEPTED |
| [ADR 0007](0007-multimodal-youtube-learning-and-transcription.md) | Multimodal Video Ingestion and Belief Archaeology Analysis | ✅ ACCEPTED |
| [ADR 0008](0008-spoke-classification-and-functional-ownership.md) | Spoke Classification and Functional Ownership Mapping in CCBA | ✅ ACCEPTED |
| [ADR 0009](0009-hub-spoke-sync-and-partition-strategy.md) | Hub-Spoke Synchronization and Directory Partitioning Strategy | ✅ ACCEPTED |
| [ADR 0010](0010-skills-integration-and-rag-boundaries.md) | Phân Định Ranh Giới Tích Hợp Kỹ Năng Nghiên Cứu & Mẫu Thử | ✅ ACCEPTED |
| [ADR 0017](0017-dynamic-override-notebook-ids-via-environment-variables.md) | Dynamic Override of Notebook IDs via Environment Variables | ✅ ACCEPTED |
| [ADR 0018](0018-remove-idop-scaffolder-from-hub.md) | Loại bỏ skill ccba-idop-scaffolder khỏi Central Hub | ✅ ACCEPTED |
| [ADR 0019](0019-port-matt-pocock-engineering-skills.md) | Đồng bộ Quy trình Triển khai Kỹ nghệ từ Thượng nguồn & Dọn dẹp Thành phần Lỗi thời | ✅ ACCEPTED |
| [ADR 0020](0020-port-and-adapt-high-priority-upstream-skills.md) | Quyết định Port và Địa hóa nhóm Skill Upstream Ưu tiên cao | ✅ ACCEPTED |
| [ADR 0021](0021-dual-mode-workspace-and-bigbim-retention.md) | Dual Mode Workspace And Bigbim Retention | ✅ ACCEPTED |
| [ADR 0022](0022-restrict-fast-flag-in-xia-challenge-gate.md) | Restrict Fast Flag In Xia Challenge Gate | ✅ ACCEPTED |
| [ADR 0023](0023-skill-auto-tuner-integration-via-skillopt.md) | Tích hợp CCBA Skill Auto-Tuner dựa trên phương pháp Microsoft SkillOpt | ✅ ACCEPTED |
| [ADR 0024](0024-deepen-tvpl-crawler-module-interface.md) | Tái cấu trúc Sâu (Deep Module) cho Phân hệ TVPL VIP Crawler | ✅ ACCEPTED |
| [ADR 0025](0025-ai-gateway-client-configuration-standardization.md) | Standardizing AI Gateway Client Configuration and Model Aliases | ✅ ACCEPTED |
| [ADR 0026](0026-isolated-test-runner-and-timeout-policy.md) | Isolated Test Execution and Timeout Policy for Agent Stability | ✅ ACCEPTED |
| [ADR 0027](0027-deepen-notebooklm-service-module.md) | Deepen NotebookLMService Module & Separate Service Layer | ✅ ACCEPTED |
| [ADR 0028](0028-deepen-detached-execution-engine.md) | Deepen DetachedExecutionEngine in `scripts/eval/process_safety.py` | ✅ ACCEPTED |
| [ADR 0029](0029-ai-gateway-client-integration-contract.md) | AI Gateway Client Integration Contract & 4 Model Archetypes Standardization | ✅ ACCEPTED |
| [ADR 0030](0030-progressive-disclosure-and-instruction-budget-optimization.md) | Progressive Disclosure and Instruction Budget Optimization for AGENTS.md | ✅ ACCEPTED |
| [ADR 0031](0031-capability-first-instructions-and-stale-path-mitigation.md) | Capability-First Instructions and Stale Path Mitigation | ✅ ACCEPTED |
| [ADR 0032](0032-monorepo-hierarchical-agents-md.md) | Monorepo Hierarchical AGENTS.md for CCBA Packages | ✅ ACCEPTED |
| [ADR 0033](0033-automation-first-quality-enforcement.md) | Automation-First Code Quality Enforcement and Instruction Pruning | ✅ ACCEPTED |
| [ADR 0034](0034-cross-agent-parity-bridge.md) | Cross-Agent Parity Bridge for AGENTS.md and CLAUDE.md | ✅ ACCEPTED |
| [ADR 0035](0035-polyglot-deep-modules-and-subagent-guardrails.md) | Polyglot Deep Modules Enforcement and Sub-Agent Review Guardrails | ✅ ACCEPTED |
| [ADR 0036](0036-brownfield-spoke-adoption-and-non-destructive-onboarding.md) | Brownfield Spoke Adoption and Non-Destructive Onboarding | ✅ ACCEPTED |
| [ADR 0037](0037-constitution-driven-traceability-matrix.md) | Constitution-Driven Traceability Matrix Pattern & Dynamic Knowledge Pointers | ✅ ACCEPTED |
| [ADR 0038](0038-unified-okf-v2-bundle-specification.md) | Chuẩn Hóa Cấu Trúc Gói Tri Thức Hợp Nhất OKF Bundle v2.0 (Unified OKF v2.0 Bundle Specification) | ✅ ACCEPTED |
| [ADR 0039](0039-autonomous-crawler-to-spoke-ingestion-protocol.md) | Giao Thức Chuyển Giao Tự Động Từ VIP Crawler (Hub) Sang Ingestion Engine (Spoke) | ✅ ACCEPTED |
| [ADR 0040](0040-skills-hierarchy-and-automated-governance.md) | Phân Tầng Kỹ Năng Kim Tự Tháp 3 Tầng & Rào Chắn Quản Trị Tự Động (Hard CI Gate) | ✅ ACCEPTED |
| [ADR 0041](0041-hub-spoke-ecosystem-taxonomy-and-archetypes.md) | Hub-Spoke Ecosystem Taxonomy, Spoke Archetypes, and Extensibility Framework | ✅ ACCEPTED |
| [ADR 0042](0042-tiered-ai-pre-submission-gate-and-tri-repo-sync.md) | Tiered Multi-Severity AI Pre-Submission Gate and Tri-Repo Server Synchronization Protocol | ✅ ACCEPTED |
| [ADR 0043](0043-idop-active-dev-resilience-and-fallback.md) | Decoupled Resilience, Schema Contract Drift Gate, and Dual-Mode Authentication for IDOP-CCBA-WAY Active Development | ✅ ACCEPTED |
| [ADR 0044](0044-spoke-hub-package-bootstrap-standard.md) | Hub-Spoke Package Bootstrap Standardization & Editable Install Protocol | ✅ ACCEPTED |
| [ADR 0045](0045-hub-proposal-ingestion-governance.md) | Hub Proposal Ingestion & Lifecycle Governance Standard (Hybrid Gate & Supervised Self-Healing) | ✅ ACCEPTED |
| [ADR 0046](0046-personal-sandbox-lifecycle-and-charter-2026-alignment.md) | Personal Sandbox Spoke Lifecycle, Registry TTL, and CCBA Charter 2026 Alignment | ✅ ACCEPTED |
| [ADR 0047](0047-catalog-manifest-compiler-and-frontmatter-ssot.md) | Catalog Manifest Compiler & Frontmatter Single Source of Truth (SSOT) | ✅ ACCEPTED |
| [ADR 0048](0048-tvpl-vip-digital-pdf-priority-and-session-engine.md) | TVPL VIP Digital PDF Priority & Persistent Chrome Profile Session Engine | ✅ ACCEPTED |
| [ADR 0049](0049-okf-v2-4-universal-agent-centric-specification-and-cloud-vault.md) | OKF v2.4 Universal Agent-Centric Specification & Multi-Asset Cloud Vault | ✅ ACCEPTED |
| [ADR 0050](0050-automated-legal-sync-and-mock-data-isolation.md) | Automated Legal Sync Pipeline & Mock Data Isolation for Spokes | ✅ ACCEPTED |
| [ADR 0051](0051-hub-spoke-sync-hardening-constitution-preservation-and-virtual-fallback.md) | Hub-Spoke Sync Hardening, Constitution Preservation & Virtual Hub Fallback | ✅ ACCEPTED |
| [ADR 0052](0052-boost-deep-reasoning-protocol-and-escalation-gate.md) | Boost Deep Reasoning Protocol, Early Escalation & Multi-Agent Hierarchy | ✅ ACCEPTED |
| [ADR 0053](0053-teamwork-multi-agent-orchestration-framework.md) | Teamwork Multi-Agent Orchestration Framework & Exclusive Seam Protocol | ✅ ACCEPTED |
| [ADR 0054](0054-antigravity-lifecycle-hooks-and-security-bridge.md) | Antigravity Lifecycle Hooks & Security Bridge — Adapter Bridge Architecture | ✅ ACCEPTED |
| [ADR 0055](0055-ccba-ai-multi-tier-failover-and-mock-provider.md) | CCBA AI Multi-Tier Failover Matrix, Antigravity CLI Bridge, Local Ollama & Offline Mock Provider | ✅ ACCEPTED |
| [ADR 0056](0056-migrate-legacy-workflows-to-skills-and-standardize-ccba-namespace.md) | Migration of Legacy Workflows to Modern Skills and Direct CCBA Namespace Standardization | ✅ ACCEPTED |
| [ADR 0057](0057-two-stage-granularity-decision-framework-and-gpi.md) | Two-Stage Granularity Decision Framework, Granularity Placement Index (GPI), and 3-Tier Skills Architecture | ✅ ACCEPTED |
| [ADR 0058](0058-live-collaboration-artifacts-workspace-mirroring-and-charter-alignment.md) | Live Collaboration Artifacts, Workspace Mirroring, and CCBA Charter 11-Seat Review Alignment | ✅ ACCEPTED |
