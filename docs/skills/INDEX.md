# CCBA Agent Platform — Danh Mục Kỹ Năng (Skills Catalog Index)

> **Tổng hợp**: 71 Kỹ năng Hoạt động được phân loại vào 5 Cổng Điều Hướng theo chuẩn ADR-0047, ADR-0057 và ADR-0058.

Trang tài liệu này phục vụ tra cứu nhanh cho kỹ sư và AI Coding Agents trong Terminal hoặc IDE.
Xem bản web trực quan tại [docs/index.html](../index.html) hoặc tóm tắt chuẩn máy đọc tại [docs/llms.txt](../llms.txt).

---

## Mục Lục Các Cổng Điều Hướng

- [🚀 Khởi tạo, Điều hướng & Đồng bộ](#init_navigation) (8 skills)
- [⚙️ Kỹ nghệ Phần mềm & Đa Tác nhân](#core_engineering) (20 skills)
- [📐 BIGBIM & Thẩm tra AI-QC](#bim_aiqc) (7 skills)
- [⚖️ Pháp lý Xây dựng & Tự động hóa Văn phòng](#legal_compliance) (10 skills)
- [🛡️ Quản trị Nền tảng, AI Gateway & Nghiên cứu](#governance_upkeep) (26 skills)

---

<a id="init_navigation"></a>
## 🚀 Khởi tạo, Điều hướng & Đồng bộ (8 Kỹ Năng)

*Khởi tạo phân vùng Spoke, cập nhật đồng bộ kỹ năng từ Hub, điều hướng bản đồ nhiệm vụ và bàn giao phiên làm việc sạch sẽ.*

| Kỹ Năng | Slash Command | Phân Tầng | Triệu Hồi | Tóm Tắt Nhiệm Vụ |
| :--- | :--- | :--- | :--- | :--- |
| [platform-loader](platform-loader.md) | `/platform-loader` | `kernel` | `Both` | Bootstrap skill cho CCBA Agent Services Platform. Đọc file này để biết toàn b... |
| [ccba-ask](ccba-ask.md) | `/ccba-ask` | `kernel` | `User` | Tư vấn và định hướng lựa chọn kỹ năng hoặc workflow phù hợp với nhu cầu phát ... |
| [ccba-handoff](ccba-handoff.md) | `/ccba-handoff` | `kernel` | `User` | Đóng gói và tổng hợp phiên làm việc hiện tại thành tài liệu Handoff chuẩn mực... |
| [ccba-init-spoke](ccba-init-spoke.md) | `/ccba-init-spoke` | `kernel` | `User` | Khởi tạo một dự án (Spoke) tuân thủ kiến trúc CCBA Agent Platform |
| [ccba-setup-skills](ccba-setup-skills.md) | `/ccba-setup-skills` | `kernel` | `User` | Thiết lập cấu hình dự án (Spoke/Hub) cho các công cụ kỹ thuật — cấu hình issu... |
| [ccba-spoke-adopter](ccba-spoke-adopter.md) | `/ccba-spoke-adopter` | `orchestrator` | `User` | Đánh giá hiện trạng và tiếp nhận an toàn các codebase hiện hữu (Brownfield Sp... |
| [ccba-update-spoke](ccba-update-spoke.md) | `/ccba-update-spoke` | `kernel` | `User` | Đồng bộ hóa các kỹ năng và cập nhật phiên bản giữa Hub và các Spoke (đơn lẻ h... |
| [ccba-wayfinder](ccba-wayfinder.md) | `/ccba-wayfinder` | `kernel` | `User` | Lập bản đồ định hướng để giải quyết các bài toán lớn/mơ hồ thông qua danh sác... |

---

<a id="core_engineering"></a>
## ⚙️ Kỹ nghệ Phần mềm & Đa Tác nhân (20 Kỹ Năng)

*Kỹ nghệ phần mềm chuẩn mực từ mài giũa ý tưởng, đặc tả kỹ thuật, phát triển dẫn dắt bởi kiểm thử (TDD), review mã nguồn, gỡ lỗi đa tác nhân đến xuất xưởng.*

| Kỹ Năng | Slash Command | Phân Tầng | Triệu Hồi | Tóm Tắt Nhiệm Vụ |
| :--- | :--- | :--- | :--- | :--- |
| [ccba-api-circuit-breaker](ccba-api-circuit-breaker.md) | `/ccba-api-circuit-breaker` | `kernel` | `Model` | Rate limiter + Circuit Breaker pattern cho LLM API calls trong batch pipeline... |
| [ccba-append-only-logger](ccba-append-only-logger.md) | `/ccba-append-only-logger` | `kernel` | `Model` | Thread-safe, append-only logging pattern cho Python pipeline multi-daemon. Tr... |
| [ccba-code-review](ccba-code-review.md) | `/ccba-code-review` | `kernel` | `User` | Rà soát chất lượng code song song trên hai trục Standards (Coding style/Smell... |
| [ccba-codebase-design](ccba-codebase-design.md) | `/ccba-codebase-design` | `kernel` | `User` | Shared vocabulary for designing deep modules (locality, depth, leverage, seam... |
| [ccba-create-pr](ccba-create-pr.md) | `/ccba-create-pr` | `kernel` | `User` | Kiểm tra chất lượng code (Shift-Left), Main Branch Guard, đẩy code và mở GitH... |
| [ccba-design](ccba-design.md) | `/ccba-design` | `kernel` | `User` | Design brand identity, logos, banners, and visual assets. Use for brand syste... |
| [ccba-diagnosing-bugs](ccba-diagnosing-bugs.md) | `/ccba-diagnosing-bugs` | `kernel` | `User` | Diagnosis loop for hard bugs and performance regressions. Use when the user s... |
| [ccba-domain-modeling](ccba-domain-modeling.md) | `/ccba-domain-modeling` | `kernel` | `User` | Build, refine, and maintain the project's domain model, ubiquitous language, ... |
| [ccba-excalidraw-diagram](ccba-excalidraw-diagram.md) | `/ccba-excalidraw-diagram` | `kernel` | `User` | Công cụ tạo sơ đồ Excalidraw JSON (.excalidraw) chuyên nghiệp cho Obsidian và... |
| [ccba-git-guardrails](ccba-git-guardrails.md) | `/ccba-git-guardrails` | `kernel` | `User` | Guardrails to block or request explicit user permission before executing dang... |
| [ccba-grilling](ccba-grilling.md) | `/ccba-grilling` | `kernel` | `User` | Phỏng vấn dồn dập người dùng về thiết kế (Stress-Test), đối chiếu quy chuẩn (... |
| [ccba-implement](ccba-implement.md) | `/ccba-implement` | `orchestrator` | `User` | Implement a piece of work based on a spec or set of tickets. |
| [ccba-mermaid-diagram](ccba-mermaid-diagram.md) | `/ccba-mermaid-diagram` | `kernel` | `User` | Tạo sơ đồ Mermaid đạt chuẩn học thuật Academic Grayscale, an toàn cú pháp (su... |
| [ccba-new-feature](ccba-new-feature.md) | `/ccba-new-feature` | `orchestrator` | `User` | Tạo feature branch mới với quy trình lập kế hoạch và phân tách session sạch (... |
| [ccba-release-feature](ccba-release-feature.md) | `/ccba-release-feature` | `orchestrator` | `User` | Merge PR, cleanup branch, auto-close local issues và cập nhật walkthrough |
| [ccba-session-retrospective](ccba-session-retrospective.md) | `/ccba-session-retrospective` | `kernel` | `User` | Tự động tổng hợp tri thức cuối phiên làm việc (Retrospective), tiến hóa kỹ nă... |
| [ccba-tdd](ccba-tdd.md) | `/ccba-tdd` | `kernel` | `User` | Phát triển hướng kiểm thử (Red-Green-Refactor) giúp tạo mã nguồn ổn định, tin... |
| [ccba-teamwork](ccba-teamwork.md) | `/ccba-teamwork` | `orchestrator` | `User` | Điều phối đa tác nhân dài hạn (Teamwork Multi-Agent Framework) theo 4 giai đo... |
| [ccba-to-spec](ccba-to-spec.md) | `/ccba-to-spec` | `kernel` | `User` | Turn the current conversation into a spec and publish it to the project issue... |
| [ccba-web-testing](ccba-web-testing.md) | `/ccba-web-testing` | `kernel` | `User` | Web testing with Playwright, Vitest, k6. E2E, load, visual, and a11y testing.... |

---

<a id="bim_aiqc"></a>
## 📐 BIGBIM & Thẩm tra AI-QC (7 Kỹ Năng)

*Hệ thống quản trị mô hình BIM Sợi Chỉ Vàng, phân loại bảng Uniclass, kiểm soát mâu thuẫn thông tin V2 và thẩm tra tự động thiết kế đa bộ môn (Kiến trúc, Kết cấu, MEP, PCCC).*

| Kỹ Năng | Slash Command | Phân Tầng | Triệu Hồi | Tóm Tắt Nhiệm Vụ |
| :--- | :--- | :--- | :--- | :--- |
| [bigbim-classification](bigbim-classification.md) | `/bigbim-classification` | `kernel` | `Model` | Tự động hóa viết bảng thực thể (En) và phân loại vật tư (PM) theo Uniclass 20... |
| [bigbim-governance](bigbim-governance.md) | `/bigbim-governance` | `kernel` | `Model` | Guardrails quản trị thông tin BIGBIM. Cưỡng chế tuân thủ Hiến pháp Sợi Chỉ Và... |
| [bigbim-rase](bigbim-rase.md) | `/bigbim-rase` | `kernel` | `Model` | Tự động phân tích RASE (Requirement, Applicability, Selection, Exception) cho... |
| [bigbim-risk](bigbim-risk.md) | `/bigbim-risk` | `kernel` | `Model` | Phát hiện "Mâu thuẫn thông tin" (Information Conflict) phi hình học tại bước ... |
| [bigbim-vbpl-digest](bigbim-vbpl-digest.md) | `/bigbim-vbpl-digest` | `kernel` | `Model` | Tra cứu và tóm lược nội dung văn bản pháp lý BIM Việt Nam — NĐ 175/2024, ISO ... |
| [ccba-ai-qc](ccba-ai-qc.md) | `/ccba-ai-qc` | `orchestrator` | `Both` | Master Deep Skill điều phối toàn trình thẩm tra chất lượng thiết kế đa bộ môn... |
| [ccba-ai-qc-pccc-audit](ccba-ai-qc-pccc-audit.md) | `/ccba-ai-qc-pccc-audit` | `kernel` | `Both` | Hệ thống Thẩm tra lỗi thiết kế đa bộ môn (PCCC, MEP, Kiến trúc) thông qua cơ ... |

---

<a id="legal_compliance"></a>
## ⚖️ Pháp lý Xây dựng & Tự động hóa Văn phòng (10 Kỹ Năng)

*Tư vấn & giải đáp pháp lý xây dựng OKF v2.4, theo dõi văn bản quy phạm pháp luật (VBPL, VBHN), bóc tách phụ lục và tự động hóa hồ sơ hoàn thành công trình.*

| Kỹ Năng | Slash Command | Phân Tầng | Triệu Hồi | Tóm Tắt Nhiệm Vụ |
| :--- | :--- | :--- | :--- | :--- |
| [ccba-completion-checklist](ccba-completion-checklist.md) | `/ccba-completion-checklist` | `kernel` | `Model` | Tạo và duy trì Danh Mục Hồ Sơ Hoàn Thành Công Trình theo VBPL hiện hành. Hỗ t... |
| [ccba-copywriting](ccba-copywriting.md) | `/ccba-copywriting` | `kernel` | `User` | Soạn thảo văn bản hành chính, thầu và hợp đồng từ template chuẩn hóa và áp dụ... |
| [ccba-legal-advisor](ccba-legal-advisor.md) | `/ccba-legal-advisor` | `kernel` | `Model` | Tư vấn & giải đáp pháp lý xây dựng: Phỏng vấn thích ứng làm rõ ngữ cảnh và xu... |
| [ccba-legal-document-tracker](ccba-legal-document-tracker.md) | `/ccba-legal-document-tracker` | `kernel` | `Both` | Theo dõi, so sánh và phân tích các VBPL xây dựng Việt Nam với VBHNEngine và R... |
| [ccba-legal-ingest](ccba-legal-ingest.md) | `/ccba-legal-ingest` | `kernel` | `Model` | Autonomous legal document acquisition, OKF v2.4 conversion, VBHN consolidatio... |
| [ccba-legal-intel](ccba-legal-intel.md) | `/ccba-legal-intel` | `kernel` | `Model` | Autonomous legal intelligence agent to crawl, diff, and generate compliance c... |
| [ccba-markdown-document-processing](ccba-markdown-document-processing.md) | `/ccba-markdown-document-processing` | `kernel` | `Both` | Master Skill quản lý và chuẩn hóa tài liệu Markdown từ Word/PDF qua Deep Seam... |
| [ccba-pptx](ccba-pptx.md) | `/ccba-pptx` | `kernel` | `User` | Công cụ tạo và chỉnh sửa file trình chiếu PowerPoint (.pptx) nâng cao bằng HT... |
| [ccba-tvpl-vip-crawler](ccba-tvpl-vip-crawler.md) | `/ccba-tvpl-vip-crawler` | `kernel` | `User` | Kỹ năng tự động cào và đóng gói văn bản pháp luật VIP TVPL qua Deep Seam TVPL... |
| [ccba-xu-ly-van-phong](ccba-xu-ly-van-phong.md) | `/ccba-xu-ly-van-phong` | `kernel` | `User` | Tạo, sửa, chuyển đổi file văn phòng (Word, Excel, Slide, PDF) theo tiêu chuẩn... |

---

<a id="governance_upkeep"></a>
## 🛡️ Quản trị Nền tảng, AI Gateway & Nghiên cứu (26 Kỹ Năng)

*Quản trị vòng đời quyết định kiến trúc ADR, cổng đánh giá chất lượng kỹ năng (GPI), AI Gateway SDK, tìm kiếm kết hợp Hybrid RAG và chu trình tự nghiên cứu học tập.*

| Kỹ Năng | Slash Command | Phân Tầng | Triệu Hồi | Tóm Tắt Nhiệm Vụ |
| :--- | :--- | :--- | :--- | :--- |
| [ccba-academic-writing](ccba-academic-writing.md) | `/ccba-academic-writing` | `kernel` | `User` | Hướng dẫn, cấu trúc, và kiểm duyệt vi mô các bài báo nghiên cứu khoa học theo... |
| [ccba-adr-lifecycle](ccba-adr-lifecycle.md) | `/ccba-adr-lifecycle` | `kernel` | `Both` | Autonomous lifecycle governance for Architecture Decision Records (ADRs) - Sc... |
| [ccba-ai-gateway-sdk](ccba-ai-gateway-sdk.md) | `/ccba-ai-gateway-sdk` | `kernel` | `Model` | Kết nối AI Gateway trên Server Spark — Đa mô hình (local GPU + cloud), 1 endp... |
| [ccba-ai-pdf-preprocessor](ccba-ai-pdf-preprocessor.md) | `/ccba-ai-pdf-preprocessor` | `kernel` | `Model` | Tối ưu hóa PDF cho LLM: Phân đoạn (Segmenting), Chia nhỏ (Chunking) và Tiling... |
| [ccba-autoresearch](ccba-autoresearch.md) | `/ccba-autoresearch` | `orchestrator` | `User` | Khởi chạy vòng lặp tối ưu hóa kỹ năng AI tự động qua đêm (Git-Ratchet Auto-Tu... |
| [ccba-build-skill](ccba-build-skill.md) | `/ccba-build-skill` | `kernel` | `User` | Nghiên cứu tài liệu từ nhiều nguồn qua NotebookLM và tự động đóng gói sinh Sk... |
| [ccba-contribute-to-hub](ccba-contribute-to-hub.md) | `/ccba-contribute-to-hub` | `kernel` | `User` | Đóng gói mã nguồn, tests, proposal từ Spoke và mở PR lên Hub kèm Vòng lặp Dừn... |
| [ccba-docs-manager](ccba-docs-manager.md) | `/ccba-docs-manager` | `kernel` | `User` | Tác nhân Quản lý Tài liệu Kỹ thuật và API của CCBA Platform. |
| [ccba-eval-gate](ccba-eval-gate.md) | `/ccba-eval-gate` | `kernel` | `User` | Thực hiện kiểm chứng mã nguồn thông qua CI Gates tự động và tự động sửa lỗi (... |
| [ccba-file-stability-guard](ccba-file-stability-guard.md) | `/ccba-file-stability-guard` | `kernel` | `Model` | Phát hiện file đã sync hoàn toàn trước khi xử lý. Kiểm tra kích thước thực tế... |
| [ccba-graduate-rd](ccba-graduate-rd.md) | `/ccba-graduate-rd` | `orchestrator` | `User` | Quy trình cưỡng chế chuyển hóa mã nguồn R&D thành Deep Seam Production, tích ... |
| [ccba-hybrid-rag-search](ccba-hybrid-rag-search.md) | `/ccba-hybrid-rag-search` | `kernel` | `Model` | Tìm kiếm ngữ nghĩa kết hợp BM25 (keyword) + Embedding (semantic) + RRF Fusion... |
| [ccba-issue-to-hub](ccba-issue-to-hub.md) | `/ccba-issue-to-hub` | `kernel` | `User` | Soạn thảo và gửi đề xuất ý tưởng/tính năng/báo lỗi (RFC Proposal) từ Spoke lê... |
| [ccba-knowledge-loop](ccba-knowledge-loop.md) | `/ccba-knowledge-loop` | `orchestrator` | `User` | Quy trình Vòng lặp Tri thức & Định hướng toàn trình (Recon → Brainstorm → Way... |
| [ccba-llm-pipeline-patterns](ccba-llm-pipeline-patterns.md) | `/ccba-llm-pipeline-patterns` | `kernel` | `Model` | Anti-patterns và best practices cho việc xây dựng LLM processing pipelines. Đ... |
| [ccba-maskara](ccba-maskara.md) | `/ccba-maskara` | `kernel` | `Model` | Phát hiện, che giấu (redact) thông tin nhạy cảm (API keys, passwords, private... |
| [ccba-notebooklm-connector](ccba-notebooklm-connector.md) | `/ccba-notebooklm-connector` | `kernel` | `Both` | Interact with Google NotebookLM to import YouTube, URLs, PDFs, and Drive docs... |
| [ccba-platform](ccba-platform.md) | `/ccba-platform` | `orchestrator` | `User` | Cổng điều phối toàn cục (Global Router) và kiểm tra môi trường cho CCBA Agent... |
| [ccba-promote-sandbox](ccba-promote-sandbox.md) | `/ccba-promote-sandbox` | `kernel` | `User` | Thăng cấp và bàn giao sản phẩm từ Spoke Cá Nhân sang Spoke Dự Án hoặc Hub (AD... |
| [ccba-research](ccba-research.md) | `/ccba-research` | `kernel` | `User` | Nghiên cứu chuyên sâu một vấn đề kỹ thuật hoặc pháp lý đối chiếu với các nguồ... |
| [ccba-seminar-builder](ccba-seminar-builder.md) | `/ccba-seminar-builder` | `kernel` | `Both` | Chuẩn bị nội dung seminar/training nội bộ CCBA. Tạo recap, agenda, outline, v... |
| [ccba-sharepoint-iac](ccba-sharepoint-iac.md) | `/ccba-sharepoint-iac` | `kernel` | `User` | Quản trị hạ tầng SharePoint Online & M365 dạng mã nguồn (Infrastructure-as-Co... |
| [ccba-skill-repair](ccba-skill-repair.md) | `/ccba-skill-repair` | `kernel` | `User` | Phục hồi và sửa chữa kỹ năng AI theo thể chế ADR-0057 và bộ kiểm định ccba-ha... |
| [ccba-sync-upstream](ccba-sync-upstream.md) | `/ccba-sync-upstream` | `kernel` | `User` | Kiểm tra cập nhật và thẩm tra tính năng thượng nguồn (ADR-0057 Radar) kết hợp... |
| [ccba-xia](ccba-xia.md) | `/ccba-xia` | `kernel` | `User` | Trích xuất, so sánh, port hoặc thích ứng tính năng từ một repository GitHub h... |
| [ccba-youtube-learn](ccba-youtube-learn.md) | `/ccba-youtube-learn` | `kernel` | `User` | Khảo cổ học Niềm tin (Belief Archaeology) thông qua bóc tách phụ đề và hình ả... |

---

## Tài Liệu Bổ Trợ & Quy Chuẩn

- [Hỏi Đáp Thường Gặp (FAQ)](FAQ.md) — Hướng dẫn Hub vs Spoke, xử lý lỗi và đồng bộ.
- [llms.txt](../llms.txt) — Endpoint mô tả nền tảng theo chuẩn mở cho AI Agents.
- [llms-full.txt](../llms-full.txt) — Nội dung hợp nhất chi tiết của toàn bộ kỹ năng.

---
*CCBA Agent Services Platform — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
