# 🧭 CCBA Central Knowledge Base Index (LLM-Wiki Master Catalog)

> **Vai trò:** Bản đồ Danh mục & Cấu trúc Phân loại Tri thức Trung tâm (Master Knowledge Catalog) cho CCBA Agent Platform.  
> **Mô hình:** 3-Tier LLM-Wiki (Raw Sources $\rightarrow$ Curated Wiki Index/Log $\rightarrow$ Health Linter/Query).  
> **Nhật ký Đột biến:** Xem lịch sử cập nhật chi tiết tại [log.md](log.md).

---

## 📌 1. Nền Tảng Cốt Lõi & Từ Điển Thuật Ngữ (Core Invariants & Vocabulary)

- [CONTEXT.md](CONTEXT.md): Từ điển thuật ngữ domain xây dựng, BIM, pháp điển hóa và các nguyên lý kiến trúc nền tảng.
- [session_learnings.md](session_learnings.md): Kho tri thức 30+ nguyên lý thực chiến qua các phiên làm việc (Process Locks, 2-Tier Test SLA, Windows Subprocess, Deep Modules).
- [port_recommendations.md](port_recommendations.md): Tổng hợp khuyến nghị porting tính năng từ các nguồn upstream.
- [upstream_skills_mapping.md](upstream_skills_mapping.md): Bản đồ phân rã và ánh xạ kỹ năng giữa ClaudeKit, MattPocock và CCBA Platform.
- [upstream_sources.yaml](upstream_sources.yaml): Định nghĩa các nguồn upstream chính thức.

---

## 📜 2. Quy Chuẩn & Phương Pháp Luận Nghiệp Vụ (Domain Guidelines & Standards)

- [ccba_brand_identity_guidelines.md](ccba_brand_identity_guidelines.md): **[MỚI]** Quy chuẩn Nhận diện Thương hiệu CCBA (ver 3.4) — Hệ thống màu WCAG AAA, Responsive Logo, Typography 2 tầng và Slogan.
- [guidelines/domain_success_criteria_rubrics.md](guidelines/domain_success_criteria_rubrics.md): **[MỚI]** Quy chuẩn Tiêu chí Thành công & Barem điểm Rubrics Định lượng Đa miền (QC PCCC 40/30/20/10, Pháp điển VBHN 35/35/20/10, Viết Học thuật 35/25/25/15).
- [guidelines/phuong_phap_luan_lap_trinh_agentic.md](guidelines/phuong_phap_luan_lap_trinh_agentic.md): Cẩm nang phương pháp luận lập trình Agentic AI thực chiến.
- [guidelines/CCBA_ADM_QD_006_Rev00_BoNhiemMEP.md](guidelines/CCBA_ADM_QD_006_Rev00_BoNhiemMEP.md): Quyết định bổ nhiệm nhân sự phụ trách bộ môn MEP.
- [guidelines/CCBA_RD_VBPL_004_Rev00-ND_30_2020_CongTacVanThu.md](guidelines/CCBA_RD_VBPL_004_Rev00-ND_30_2020_CongTacVanThu.md): Hướng dẫn công tác văn thư theo Nghị định 30/2020/NĐ-CP.
- [guidelines/CCBA_SOP_001_Rev00-Brainstorming_Workflow.md](guidelines/CCBA_SOP_001_Rev00-Brainstorming_Workflow.md): Quy trình thao tác chuẩn cho phiên Brainstorming.
- [questionnaires/to-questionnaire-sample-pccc.md](questionnaires/to-questionnaire-sample-pccc.md): Bảng câu hỏi mẫu Discovery thẩm tra PCCC đa bộ môn.

---

## 🏗️ 3. Quyết Định Kiến Trúc & Thiết Kế (Architecture & ADRs)

- [grilling_live_artifacts_and_charter.md](grilling_live_artifacts_and_charter.md): **[MỚI]** Biên Bản Phỏng Vấn Socratic Grilling: Thiết Kế Live State Artifacts & Tích Hợp 11 Ghế CCBA Charter (ADR-0058).
- [specs_and_roadmaps/Arch_Proposal_Hub_Spoke_Sync_Strategy.md](specs_and_roadmaps/Arch_Proposal_Hub_Spoke_Sync_Strategy.md): Chiến lược đồng bộ hóa Hub-and-Spoke giữa Platform và các dự án vệ tinh.
- [specs_and_roadmaps/adr_0010_skills_integration.md](specs_and_roadmaps/adr_0010_skills_integration.md): ADR-0010 về tích hợp kỹ năng AI.
- [specs_and_roadmaps/adr_0011_legal_intel_deep_module.md](specs_and_roadmaps/adr_0011_legal_intel_deep_module.md): ADR-0011 về Deep Module hóa gói `ccba-legal-intel`.
- [specs_and_roadmaps/adr_0012_ccba_ai_pure_gateway.md](specs_and_roadmaps/adr_0012_ccba_ai_pure_gateway.md): ADR-0012 về kiến trúc AI Gateway thuần túy.
- [specs_and_roadmaps/adr_0013_knowledge_evolution_loop.md](specs_and_roadmaps/adr_0013_knowledge_evolution_loop.md): ADR-0013 về Vòng lặp Tiến hóa Tri thức Knowledge Loop.
- [adr/adr_20260815_224158_chuan_hoa_deep_seams_cho_4_sub_systems_t.md](adr/adr_20260815_224158_chuan_hoa_deep_seams_cho_4_sub_systems_t.md): Chuẩn hóa Deep Seams cho 4 hệ thống con.

---

## 🔬 4. Nghiên Cứu Chuyên Sâu & Phân Tích Upstream (Research & Studies)

- [research_and_studies/research-agent-architecture-packages-skills-orchestrators.md](research_and_studies/research-agent-architecture-packages-skills-orchestrators.md): **[MỚI]** Báo cáo Nghiên cứu RES-2026-ARCH-001 v1.2: Kiến trúc Agent 3 Tầng, Khung Quyết Định Hai Giai Đoạn và Chỉ số Phân rã Kỹ năng (GPI).
- [research_and_studies/research-rename-skills-vs-alias.md](research_and_studies/research-rename-skills-vs-alias.md): **[MỚI]** Báo cáo Nghiên cứu & Phản biện: Đổi tên trực tiếp Skills sang namespace ccba-* vs Cơ chế Alias.
- [research_and_studies/research-brand-refinements.md](research_and_studies/research-brand-refinements.md): **[MỚI]** Báo cáo Đánh giá & Tinh chỉnh Bộ Nhận diện Thương hiệu CCBA (ver 3.3 $\rightarrow$ ver 3.4).
- [research_and_studies/research-minimalist-slide-design.md](research_and_studies/research-minimalist-slide-design.md): **[MỚI]** Nghiên cứu Kiến trúc Trình chiếu Tối giản Thụy Sĩ (Swiss Minimalist Presentation System).
- [research_and_studies/research-storytelling-with-you-patterns.md](research_and_studies/research-storytelling-with-you-patterns.md): **[MỚI]** Báo cáo Nghiên cứu & Ứng dụng "Storytelling With You" (Cole Nussbaumer Knaflic).
- [research_and_studies/codebase_summary.md](research_and_studies/codebase_summary.md): Báo cáo tóm tắt kiến trúc codebase CCBA.
- [research_and_studies/vibe_coding_sdlc_analysis.md](research_and_studies/vibe_coding_sdlc_analysis.md): Phân tích quy trình phát triển phần mềm theo định hướng AI-first.
- [research_and_studies/thuvienphapluat_structure_analysis.md](research_and_studies/thuvienphapluat_structure_analysis.md): Phân tích cấu trúc dữ liệu và API của Thư Viện Pháp Luật (TVPL).
- [research_and_studies/claudekit_architectural_study.md](research_and_studies/claudekit_architectural_study.md): Nghiên cứu kiến trúc framework ClaudeKit.
- [research_and_studies/claudekit_skills_analysis.md](research_and_studies/claudekit_skills_analysis.md): Khảo sát hệ thống skills của ClaudeKit.
- [research_and_studies/claudekit_mattpocock_skills_reference.md](research_and_studies/claudekit_mattpocock_skills_reference.md): Tài liệu tham chiếu chi tiết skills của Matt Pocock.
- [research_and_studies/claudekit_docs_manager_research.md](research_and_studies/claudekit_docs_manager_research.md): Nghiên cứu quản trị tài liệu kỹ thuật.
- [research_and_studies/claudekit_docs_manager_resolution.md](research_and_studies/claudekit_docs_manager_resolution.md): Biên bản thống nhất giải pháp Docs Manager.
- [research_and_studies/claudekit_marketing_port_analysis.md](research_and_studies/claudekit_marketing_port_analysis.md): Phân tích module Marketing & Copywriting.
- [research_and_studies/claudekit_porting_comparison.md](research_and_studies/claudekit_porting_comparison.md): So sánh chi tiết trước và sau khi porting.
- [research_and_studies/power_platform_skills_comparison.md](research_and_studies/power_platform_skills_comparison.md): Đánh giá tích hợp Microsoft Power Platform.
- [research_and_studies/research-platform-init-setup-sync.md](research_and_studies/research-platform-init-setup-sync.md): Nghiên cứu cơ chế khởi tạo và đồng bộ Hub-Spoke.
- [research_and_studies/port_recommendations.md](research_and_studies/port_recommendations.md): Danh mục chi tiết đề xuất porting.
- [research_and_studies/ai_gateway_quota_matrix_and_routing_architecture.md](research_and_studies/ai_gateway_quota_matrix_and_routing_architecture.md): Ma trận Quota và Kiến trúc Định tuyến AI Gateway Server Spark.
- [research_and_studies/research-issue-232-federated-rag-adversarial.md](research_and_studies/research-issue-232-federated-rag-adversarial.md): Báo cáo Phản biện Kép (Dual-Agent Adversarial) cho Issue #232 — Federated Cross-Spoke Legal RAG Engine.

---

## 📋 5. Đặc Tả Kỹ Thuật & Lộ Trình Phát Triển (Specs & Roadmaps)

- [blueprints/fleet_skills_3tier_migration_blueprint.md](blueprints/fleet_skills_3tier_migration_blueprint.md): **[MỚI]** Kế hoạch & Bản đồ Di trú Toàn diện 100 Agent Skills (BLUEPRINT-2026-SKILLS-001) theo Kiến trúc 3 Tầng và Khung Quyết Định Hai Giai Đoạn.
- [scripts_migration_manifest.md](scripts_migration_manifest.md): **[MỚI]** Báo Cáo Khảo Sát & Ma Trận Ánh Xạ Di Trú 52 Scripts Monorepo (Ticket 3 Manifest).
- [specs/spec-structured-diff-protocol.md](specs/spec-structured-diff-protocol.md): **[MỚI]** Đặc tả Giao thức Structured Diff Protocol & Cơ chế Kiểm soát Single-Writer Engine (Ticket 4).
- [specs_and_roadmaps/agentic_programming_roadmap.md](specs_and_roadmaps/agentic_programming_roadmap.md): Lộ trình phát triển hệ sinh thái lập trình Agentic.
- [specs_and_roadmaps/auto_dev_loop_spec.md](specs_and_roadmaps/auto_dev_loop_spec.md): Đặc tả vòng lặp phát triển phần mềm tự động (Auto-Dev Loop).
- [specs_and_roadmaps/legal_sync_pipeline_spec.md](specs_and_roadmaps/legal_sync_pipeline_spec.md): Đặc tả pipeline đồng bộ văn bản pháp luật tự động.
- [specs_and_roadmaps/marketing_integration_plan.md](specs_and_roadmaps/marketing_integration_plan.md): Kế hoạch tích hợp các công cụ soạn thảo thương mại.
- [specs_and_roadmaps/spec.md](specs_and_roadmaps/spec.md): Tài liệu đặc tả kỹ thuật chung của hệ thống.
- [specs/spec-deep-seams-implementation.md](specs/spec-deep-seams-implementation.md): Đặc tả triển khai kiến trúc Deep Seams Monorepo.
- [specs/spec-safe-execution-sandbox.md](specs/spec-safe-execution-sandbox.md): Đặc tả Safe Execution Sandbox và Process Guards.
- [specs/spec-system-stability-auto-guardrails.md](specs/spec-system-stability-auto-guardrails.md): Đặc tả hệ thống rào chắn tự động ổn định hệ thống.
- [specs/spec-test-isolation-and-stability.md](specs/spec-test-isolation-and-stability.md): Đặc tả cô lập và ổn định hóa kiểm thử Pytest.
- [specs/spec-deepen-tvpl-crawler.md](specs/spec-deepen-tvpl-crawler.md): Đặc tả Deepening module TVPL VIP Crawler.
- [specs/spec-legal-intel-deep-module.md](specs/spec-legal-intel-deep-module.md): Đặc tả Deep Module cho dịch vụ Pháp điển hóa.
- [specs/spec-tu-van-phap-luat-tu-dong.md](specs/spec-tu-van-phap-luat-tu-dong.md): Đặc tả tính năng trợ lý tư vấn pháp luật tự động.
- [specs/spec-wayfinder-cancelled-error.md](specs/spec-wayfinder-cancelled-error.md): Đặc tả khắc phục lỗi timeout/cancel trong Wayfinder.

---

## 📊 6. Báo Cáo Kiểm Định, Chất Lượng & Đánh Giá (Audits & Reports)

- [shallow_modules_audit.md](shallow_modules_audit.md): Báo cáo rà soát và đánh giá các module nông (Shallow Modules) trong toàn bộ codebase.
- [reports/ccba_docs_evaluation_report.md](reports/ccba_docs_evaluation_report.md): Báo cáo đánh giá chất lượng hệ thống tài liệu CCBA.
- [reports/drawing_comprehension_report.md](reports/drawing_comprehension_report.md): Báo cáo năng lực hiểu bản vẽ kỹ thuật của AI Vision.
- [reports/qwen_evaluation_report.md](reports/qwen_evaluation_report.md): Báo cáo benchmark các model dòng Qwen trên hạ tầng Spark.
- [reports/qwen_ntp_eval_report.md](reports/qwen_ntp_eval_report.md): Báo cáo đánh giá hiệu năng tiếp nhận tác vụ nghiệp vụ của Qwen.
- [reports/session_retrospective_2026-04-15.md](reports/session_retrospective_2026-04-15.md): Báo cáo tổng kết phiên làm việc định kỳ.
- [brainstorm_session_software_micro_agent.md](brainstorm_session_software_micro_agent.md): Biên bản thảo luận ý tưởng Micro-Agent phần mềm.
- [brainstorm_session_tvpl_vip_knowledge_pipeline.md](brainstorm_session_tvpl_vip_knowledge_pipeline.md): Biên bản thảo luận pipeline tri thức TVPL VIP.
- [brainstorm_skills_eval_legal_guardrails.md](brainstorm_skills_eval_legal_guardrails.md): Biên bản thảo luận rào chắn an toàn cho Legal Skills.

---

## 🛠️ 7. Vận Hành, Cài Đặt & Kết Nối Hệ Thống (Operations & Setup)

- [client-setup-guide.md](client-setup-guide.md): Hướng dẫn chi tiết thiết lập môi trường trạm làm việc cho Kỹ sư mới.
- [remote-access.md](remote-access.md): Hướng dẫn cấu hình VPN Tailscale và truy cập hạ tầng GPU Server Spark.
- [configs/SETUP_USER_GLOBAL.md](configs/SETUP_USER_GLOBAL.md): Cấu hình môi trường toàn cục và quy chuẩn tích hợp Agent.

---

## 🗄️ 8. Không Gian Vấn Đề Kỹ Thuật (Feature Issues & Trackers)

  - [issues/doc-auto-evolution/map.md](issues/doc-auto-evolution/map.md): **[MỚI]** Hệ thống Tự Tiến Hóa & Bảo Trì Tài Liệu Tự Động (AST Grounding, Zero-Deletion, Nightly PR & Telegram Alert).
  - [issues/idop-bridge/map.md](issues/idop-bridge/map.md): Cầu Nối Dữ Liệu Tầng 1 (Dự Án) ↔ Tầng 2 (IDOP CCBA & Viện IBST).
  - [issues/5-layer-eval-legal-framework/map.md](issues/5-layer-eval-legal-framework/map.md)
  - [issues/safe-execution-sandbox/map.md](issues/safe-execution-sandbox/map.md)
  - [issues/pydantic-pure-domain-services/map.md](issues/pydantic-pure-domain-services/map.md)
  - [issues/prevent-agent-cancellation/map.md](issues/prevent-agent-cancellation/map.md)
  - [issues/ccba-ai-sdk-enhancements/map.md](issues/ccba-ai-sdk-enhancements/map.md)
  - [issues/triage-infrastructure/map.md](issues/triage-infrastructure/map.md)
  - Và các thư mục issue chuyên đề khác.
