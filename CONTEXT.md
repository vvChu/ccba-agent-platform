# CCBA Agent Platform Context & Domain Vocabulary

The CCBA Agent Services Platform is a framework to develop and coordinate AI agent skills, workflows, and compliance checks across construction consulting projects.

---

## 📑 Mục Lục Phân Loại Tri Thức (Domain Taxonomy)

1. [🏛️ 1. Hệ Sinh Thái Hub-Spoke & Phép Ẩn Dụ Hệ Thống (ADR 0041)](#1-hệ-sinh-thái-hub-spoke--phép-ẩn-dụ-hệ-thống-adr-0041)
2. [🧩 2. Kiến Trúc Cốt Lõi, Deep Seams & Ngân Sách Chỉ Dẫn](#2-kiến-trúc-cốt-lõi-deep-seams--ngân-sách-chỉ-dẫn)
3. [🤖 3. Hạ Tầng AI Gateway, LLM Prompting & Auto-Tuner](#3-hạ-tầng-ai-gateway-llm-prompting--auto-tuner)
4. [🛡️ 4. Chính Sách Kiểm Thử, CI Gates & An Toàn Tiến Trình](#4-chính-sách-kiểm-thử-ci-gates--an-toàn-tiến-trình)
5. [📚 5. Pháp Điển Xây Dựng, VBHN & Xử Lý Tài Liệu](#5-pháp-điển-xây-dựng-vbhn--xử-lý-tài-liệu)
6. [🏢 6. Quản Trị Doanh Nghiệp IDOP & Cổng Giao Tiếp Viện IBST (ADR 0042, 0043)](#6-quản-trị-doanh-nghiệp-idop--cổng-giao-tiếp-viện-ibst-adr-0042-0043)

---

## 1. Hệ Sinh Thái Hub-Spoke & Phép Ẩn Dụ Hệ Thống (ADR 0041)

### Phép Ẩn Dụ Hệ Thống (System Metaphor)
> **Hệ thống CCBA hoạt động như một Mạng lưới Nhượng quyền Tri thức (Knowledge Franchise Network).**

- **Hub** = Tổng hành dinh nhượng quyền — nắm giữ Hiến pháp (`AGENTS.md`), bộ sổ tay vận hành chuẩn (Skills/Workflows), và khuôn mẫu kiểm soát chất lượng.
- **Spoke** = Chi nhánh nhượng quyền — vận hành độc lập tại từng dự án, kế thừa quy trình từ Hub, nhưng tùy chỉnh theo ngữ cảnh địa phương (`workspace_context.yaml`).
- **Downstream Sync** = Cập nhật Sổ tay Nhượng quyền — khi Hub cập nhật kỹ năng/workflow mới, các Spoke đồng bộ xuôi để nhận bản mới nhất.
- **Upstream Loop** = Đóng góp Sáng kiến từ Chi nhánh — khi một Spoke phát triển quy trình mới hiệu quả, đóng gói và đề xuất ngược lên Hub qua Pull Request.
- **AI Gateway** = Đường dây nóng trung tâm — mọi chi nhánh đều liên lạc qua một cổng duy nhất (`100.83.192.30:8090/v1`) để truy cập hệ thống đa mô hình AI (local GPU & cloud).
- **Deep Seams** = Chuyên gia nội bộ — mỗi package/module đóng vai trò một chuyên gia đầu ngành, ẩn giấu toàn bộ sự phức tạp nghiệp vụ đằng sau một giao diện đơn giản duy nhất.
- **Skill Factory (`/ccba-build-skill`)** = Dây chuyền R&D nhượng quyền — tự động đóng gói các công thức nấu ăn / quy trình nghiệp vụ mới thành sổ tay chuẩn (Skill) phân phối cho toàn mạng lưới.

### Phân Loại 5 Spoke Archetypes (ADR 0041)
1. **Platform Hub (`platform_hub`)**:
   Tổng hành dinh công nghệ, lưu trữ 73+ Skills/Workflows, Deep Seam Packages Python, hệ thống Auto-Tuner và Quality Gates (`ccba-agent-platform`).
2. **Enterprise Governance Spoke (`enterprise_governance`)**:
   Hệ điều hành doanh nghiệp & Quản trị nội bộ ("The CCBA Way"): Quy chế QCTK 2815, Phân bổ dòng tiền 3 tầng, Phiếu giao việc PGV, 15 Vai trò chuẩn hóa, 58 SharePoint lists (`IDOP-CCBA-WAY`).
3. **Knowledge Corpus Spoke (`knowledge_corpus`)**:
   Kho lưu trữ chuẩn quốc gia về Văn bản quy phạm pháp luật, Quy chuẩn PCCC, Tiêu chuẩn Xây dựng theo định dạng OKF v2.0 Bundle (`ccba-legal-knowledge`).
4. **Project Delivery Spoke (`project_delivery`)**:
   Hiện trường triển khai công trình thực tế: Hồ sơ thiết kế, Bản vẽ BIM, Báo cáo Thẩm tra PCCC, Danh mục hồ sơ hoàn công (`2026-04 DH Viet Nhat`).
5. **Specialized Extension Spokes (Khung Mở Rộng Tương Lai)**:
   - `research_lab`: Không gian R&D thuật toán chuyên sâu, mô phỏng kết cấu và bài báo khoa học.
   - `tooling_plugin`: Kho phát triển Add-in/Plugin cho Revit, AutoCAD, Rhino/Grasshopper.
   - `client_portal`: Cổng giao tiếp Extranet phục vụ Chủ đầu tư tra cứu báo cáo thẩm tra trực tiếp.

### Thuật Ngữ Mạng Lưới Hub-Spoke
**Hub**:
The central repository containing the master constitution, catalogs, reusable skills, and templates.
_Avoid_: Central, upstream

**Spoke**:
A downstream project-specific workspace that inherits and syncs bundles of skills/workflows from the Hub.
_Avoid_: Sub-project, spoke repo

**Delivery Spoke (Spoke Triển khai / Spoke Dự án)**:
A downstream project-specific workspace created for a service contract or project execution, which syncs workflows/skills from the local Hub. It operates without a local or remote Git/GitHub repository, and synchronizes its raw and output assets exclusively via OneDrive/SharePoint.

**Functional Spoke / R&D Spoke (Spoke Chức năng)**:
A permanent workspace owned by a specific department (e.g., BIM Design, BIM Project, Legal & QA) to research rules, develop skills/checklists, and propose updates to the Hub. It uses local Git and remote GitHub repositories to submit Pull Requests back to the Hub (Upstream Loop).

**Nền tảng số IDOP**:
The Integrated Digital Operations Platform of CCBA, serving as the physical runtime and repository environment of the Hub/Spoke platform.

**Upstream Loop (Vòng đóng góp ngược)**:
The process where Functional Spokes package and propose local skills or workflows back to the central Hub via Pull Requests and validation gates.

**Downstream Sync (Vòng đồng bộ xuôi)**:
The process where Project Spokes synchronize and update their local `.agents/workflows/` and git-ignored `.agents/skills/` from the Hub.

**Dynamic Knowledge Pointer (Con Trỏ Tri Thức Động)**:
Mẫu hình chia sẻ tri thức giữa Hub và Spoke thông qua khai báo đường dẫn phân giải động trong `catalog.yaml` thay vì sao chép nội dung tệp tin, duy trì nguyên tắc Một Nguồn Sự Thật Duy Nhất (Single Source of Truth) và loại bỏ hoàn toàn nguy cơ trùng lặp dữ liệu.

**Brownfield Spoke Adoption (Tiếp Nhận Spoke Hiện Hữu)**:
Quy trình kỹ thuật và công cụ (`/ccba-adopt-spoke`) cho phép kết nạp an toàn một repository/codebase đã có sẵn vào mạng lưới CCBA Platform mà không phá hủy cấu trúc dữ liệu, Hiến pháp riêng hoặc mã nguồn hiện hữu.

**Non-Destructive Schema Merging (Hợp Nhất Cấu Hình Bảo Toàn)**:
Giao thức hợp nhất tệp `workspace_context.yaml` theo nguyên tắc Additive (chỉ thêm các trường bắt buộc của Hub, bảo tồn 100% các nhóm tài liệu và milestone tùy biến cũ của Spoke) kèm sao lưu tự động.

**Brownfield Safety Guard (Rào Chắn An Toàn Dự Án Hiện Hữu)**:
Cơ chế kiểm tra tự động trong `/ccba-init-spoke` nhằm phát hiện mã nguồn hoặc cấu trúc tri thức có sẵn, chủ động chặn đứng hành vi ghi đè nguy hiểm và điều hướng sang quy trình tiếp nhận thích ứng.

**Git Core - Cloud Artifacts (Nhân Git - Vệ tinh Cloud)**:
The hybrid synchronization strategy where lightweight, diffable text/code files are synced via Git, while large binaries and raw media files are synchronized via OneDrive/SharePoint.

**Maskara Pre-commit Hook**:
A local Git security hook written dynamically to `.git/hooks/pre-commit` in Spoke workspaces during initialization, which runs the Maskara privacy tool to scan and block commits containing hardcoded API keys or raw credentials.

**Spoke Leakage Guard (Rào Chắn Rò Rỉ Spoke)**:
Cơ chế kiểm soát tự động tại CI và Agent Workflow nhằm phát hiện, ngăn chặn và bóc tách các tệp tin rác hoặc tài sản cục bộ của Spoke (thư mục `.md/teach/`, `.tmp/`, `.out-of-scope/`, cache hoặc đường dẫn tuyệt đối dạng Windows `D:\...`) trước khi chúng bị hợp nhất vào Hub Monorepo.

**Supervised Self-Healing (Tự Khắc Phục Lỗi Có Giám Sát)**:
Mô thức vận hành của Agent khi thẩm định PR đề xuất: Agent chủ động checkout nhánh, áp dụng các bản vá lỗi kỹ thuật rõ ràng (fix regex, resolve conflict cơ bản, format code), chạy bộ kiểm thử để xác minh xanh 100%, và trình bày tóm tắt diff cho Maintainer phê duyệt trước khi commit/merge.

**Proposal Lifecycle Governance (Quản Trị Vòng Đời Đề Xuất)**:
Quy chuẩn quản trị trạng thái tệp đề xuất `.agents/proposals/[YYYY-MM-DD]_[name].md` xuyên suốt chu trình: từ khi mở (`status: "open"`), qua thẩm định, đến khi hoàn tất merge (`status: "merged"` kèm `merged_commit` hash và ngày merge) đồng thời tự động cập nhật catalog hệ sinh thái (`catalog.yaml`, `PLATFORM.md`).

---

## 2. Kiến Trúc Cốt Lõi, Deep Seams & Ngân Sách Chỉ Dẫn

**Deep Seam (Mối nối sâu)**:
Mô thức thiết kế cốt lõi của CCBA Platform: một module công khai duy nhất ẩn giấu toàn bộ logic phức tạp bên trong (high depth, low surface area), cung cấp 1-3 entry points cho callers bên ngoài. Ngược lại với "Shallow Module" (nhiều public methods, logic rải rác).
_Avoid_: Facade (quá chung), Wrapper, Service layer

**Polyglot Deep Module Enforcement (Cơ chế Cưỡng chế Module Sâu Đa Ngôn Ngữ)**:
Chuẩn quản trị ranh giới module trong Monorepo: Đối với Python packages (`packages/*/`), bắt buộc chỉ xuất khẩu 2–3 Deep Seams qua `__all__` tại `__init__.py`, bảo vệ các submodule bằng tiền tố gạch dưới và linter (`Ruff SLF001`); đối với TypeScript packages, sử dụng `dependency-cruiser` cấm import sâu qua thư mục con `lib/`.

**Progressive Instruction Disclosure (Phân rã Chỉ dẫn Lũy tiến)**:
Mô thức phân rã tập chỉ dẫn của Agent thành nhiều lớp độc lập: chỉ giữ mỏ neo định vị và bất biến cốt lõi tại `AGENTS.md` gốc, phân phối chi tiết nghiệp vụ và rào chắn kỹ thuật vào các tài liệu chuyên biệt (`docs/rules/*.md`) hoặc kỹ năng động để tối ưu hóa ngân sách chỉ dẫn.

**Instruction Budget (Ngân sách Chỉ dẫn)**:
Giới hạn số lượng chỉ dẫn (~150-200 chỉ dẫn nhất quán) mà mô hình ngôn ngữ lớn (Frontier LLM) có thể ghi nhớ và tuân thủ chặt chẽ trên mỗi lượt gọi prompt mà không bị suy giảm độ chính xác hoặc phân tâm.

**Ball of Mud Prevention (Chống Cục Bùn Chỉ dẫn)**:
Nguyên tắc kiểm soát và tái cấu trúc định kỳ bộ quy chuẩn Agent nhằm phát hiện và loại bỏ các chỉ dẫn thừa thãi, hiển nhiên hoặc xung đột, ngăn ngừa `AGENTS.md` trở thành khối văn bản không thể bảo trì.

**Capability-First Instruction (Chỉ dẫn Hướng Năng lực)**:
Phương pháp biên soạn tài liệu và quy chuẩn cho AI Agent tập trung vào mô tả mục tiêu hành vi và giao diện chuẩn hóa thay vì ghi cứng đường dẫn file nội bộ, giúp ngăn chặn hiện tượng nhiễm độc ngữ cảnh khi codebase tái cấu trúc.

**Context Poisoning (Nhiễm độc Ngữ cảnh)**:
Hiện tượng thông tin lỗi thời, đường dẫn tệp tin không còn tồn tại hoặc chỉ dẫn sai lệch trong tệp cấu hình khiến AI Agent liên tục suy đoán sai và mắc kẹt trong vòng lặp tìm kiếm vô ích.

**Hierarchical Monorepo AGENTS.md (Hệ thống AGENTS.md Phân tầng Monorepo)**:
Mô hình phân cấp tệp chỉ dẫn trong kiến trúc Monorepo; Root `AGENTS.md` chỉ quản lý bức tranh tổng thể và công cụ dùng chung, trong khi mỗi package (`packages/{pkg}/AGENTS.md`) sở hữu tệp chỉ dẫn cục bộ ngắn gọn (3-6 dòng) định nghĩa mục đích, Public Deep Seams và lệnh kiểm thử riêng biệt.

**Smart Zone & D-Zone (Phân vùng Ngữ cảnh)**:
Mô hình phân loại nội dung trong cửa sổ ngữ cảnh (context window) của AI Agent: Smart Zone chứa tri thức cô đọng, cấu trúc hóa cao phục vụ suy luận; D-Zone (Danger Zone) chứa nội dung rác, verbose, stale làm phình context và suy giảm chất lượng. Mục tiêu: tối đa Smart Zone, loại bỏ D-Zone.
_Avoid_: Context budget, token limit (quá chung)

**Master Skill (Kỹ Năng Toàn Trình)**:
Kỹ năng cấp cao đóng vai trò nhạc trưởng điều phối một hoặc nhiều Deep Seams (ví dụ: `markdown-document-processing`, `ccba-legal-intel`, `ccba-ai-qc-audit`), cung cấp khả năng tự động nhận diện tác vụ đầu cuối (Model-Invoked) và dẫn xuất chi tiết sang các Progressive References.

**Progressive Reference (Tài Liệu Tham Chiếu Bộc Lộ Dần)**:
Tài liệu hướng dẫn kỹ thuật chi tiết hoặc SOP chuyên biệt được lưu trữ trong thư mục `references/*.md` của một Master Skill, chỉ được AI Agent nạp khi cần xử lý các ca biên đặc thù, giúp giữ cho tệp `SKILL.md` chính luôn gọn gàng và không làm ô nhiễm context.

**Reference Skill vs Driver Skill (Phân định Kỹ năng Tham chiếu & Kỹ năng Hành động)**:
Mô hình phân loại kỹ năng của Platform: Reference Skill (`codebase-design`, `domain-modeling`) chỉ đóng vai trò từ vựng và tiêu chuẩn gốc, áp dụng quy tắc dừng cứng khi gọi độc lập; trong khi Driver Skill (`implement`, `improve-codebase-architecture`, `grill-with-docs`) sở hữu quy trình lặp và điểm kết thúc rõ ràng.

**Skill**:
A structured set of agent guidelines, scripts, and completion criteria defined in a `SKILL.md` file.
_Avoid_: Tool, plugin

**Workflow**:
A markdown script registered as a Slash Command that directs agent actions sequentially.
_Avoid_: Scenario, command line script

**Bundle**:
A grouping of related skills and workflows organized by domain area (e.g., `_core`, `_software`, `_qc`, `_consulting`).
_Avoid_: Package bundle, module

**Spec (Đặc tả Kỹ thuật)**:
Tài liệu mô tả yêu cầu thiết kế, hành vi và seam kỹ thuật chi tiết cho một tính năng hoặc quy trình công việc, được sinh ra từ quy trình `/ccba-to-spec` và lưu trữ tại `.md/knowledge/specs/spec-{slug}.md`. Thuật ngữ này thay thế hoàn toàn cho khái niệm PRD (Product Requirement Document) đã lỗi thời.
_Avoid_: PRD, Product Requirement Document, Bản yêu cầu sản phẩm

**User Loops (Chu trình Người dùng)**:
Các mô thức hoặc hoạt động lặp đi lặp lại hàng ngày/hàng tuần của người dùng, được định nghĩa qua `loop-me` và tài liệu hóa trong `.md/knowledge/user_loops.md` trước khi tự động hóa thành workflow chính thức.

**Cohesive Topic Folder (Thư mục Đề tài Chuyên biệt)**:
A directory structure under `.md/projects/[Ten_De_Tai]/` that contains all raw assets, transcripts, notes, drafts, and compiled Word documents belonging to a single R&D or writing project, preventing file fragmentation.

**Reuse-First Gate (Rào cản Tái sử dụng)**:
Quy trình bắt buộc trong `AGENTS.md` (Layer 1) yêu cầu Agent tra cứu Hub catalog trước khi viết bất kỳ utility/script mới nào, ghi nhận quyết định reuse/viết mới kèm lý do.

**Session Learnings Bootstrap (Nạp Tri thức Tích lũy)**:
Quy trình bắt buộc trong `AGENTS.md` (Layer 1) yêu cầu Agent đọc tệp `.md/knowledge/session_learnings.md` khi bắt đầu Planning Mode hoặc SDLC Implementation Loop để nạp các Patterns/Anti-patterns đã được đúc kết.

**Self-Evolution Loop (Vòng lặp Tiến hóa Tri thức)**:
Chu trình phản hồi 3 cấp độ (Micro: Rules, Meso: Skill Refactor, Macro: New Skill) diễn ra tại `/ccba-session-retrospective` giúp nền tảng tự động nâng cấp năng lực sau mỗi phiên làm việc mà không làm phình ngữ cảnh (Decoupled Recommendation Pattern).

**Skill Factory (Nhà máy Sản xuất Kỹ năng)**:
Kiến trúc Meta-Skill (`/ccba-build-skill`) tự động hóa toàn trình việc quét an toàn (Maskara), chưng cất tri thức (NotebookLM RAG từ Canonical Artifacts & Code Seams), sinh cấu trúc Skill đạt chuẩn CCBA và phân định đăng ký Hub/Spoke.

**Context Budget Ceiling (Trần Ngân Sách Ngữ Cảnh Kỹ Năng)**:
Rào chắn cứng trong kiểm định CI (`skill_auditor.py`) giới hạn tổng số kỹ năng tự động kích hoạt (`model_invoked`) trong một Bundle tối đa là 10 skills, bảo vệ vùng nhớ thông minh (*Smart Zone* < 120k tokens) của AI Agent.

**Zero-Duplicate Skill Gate (Rào Chắn Không Trùng Lặp Kỹ Năng)**:
Quy tắc linter tự động cấm tạo các file `SKILL.md` trùng tên hoặc trùng lặp cấu trúc thư mục giữa cấp root `.agents/skills/` và các thư mục con.

**Plan Lock**:
A file-based locking mechanism (`.plan.lock`) to prevent lost updates when multiple agents concurrently modify phase status.

**Target Line Override**:
A formatting preservation technique where only specific key-value pairs (like status) in frontmatter are overwritten instead of full file re-serialization.

---

## 3. Hạ Tầng AI Gateway, LLM Prompting & Auto-Tuner

**AI Gateway Master Endpoint**:
Cổng giao tiếp duy nhất `http://100.83.192.30:8090/v1` kết nối qua Tailscale VPN tới hệ thống LiteLLM AI Gateway trên Server Spark, điều hướng tự động đa mô hình AI (local GPU & cloud).

**RAG Virtual Aliases (Bí danh ảo RAG)**:
Chuỗi định danh mô hình ảo (`ocr-primary`, `ocr-fallback`, `rag-core`, `text-gemma`, `reasoning-gemma`) được AI Gateway tự động định tuyến nhằm tối ưu hóa chi phí (Free Tier Farm) và hiệu năng xử lý văn bản lớn.

**Primary Local GPU Model Alias**:
Định danh chuẩn `qwen-local-primary` đại diện cho model Qwen 3.5 35B FP8 chạy trực tiếp trên GPU local của Server Spark, thay thế hoàn toàn cho chuỗi `qwen3.5-35b` đã bị khai tử.

**Skill Auto-Tuner**:
Quy trình tự động tinh chỉnh văn bản kỹ năng (`SKILL.md`) của AI Agent thông qua chu trình lặp 4 bước (Rollout - Reflect - Edit - Validate) dựa trên phương pháp SkillOpt mà không cần can thiệp trọng số mô hình (frozen LLM).

**Validation Gate (Cổng kiểm chứng SKILL)**:
Cơ chế đánh giá bản sửa đổi prompt trên tập bài kiểm tra held-out tasks để chống hiện tượng suy giảm chất lượng ở các tác vụ khác (Prompt Drift).

**Prompt Drift**:
Hiện tượng tệp hướng dẫn/prompt được sửa để đạt kết quả tốt hơn ở một tác vụ cụ thể nhưng lại làm suy giảm hiệu suất ở các tác vụ hoặc ngữ cảnh khác.

**Flat NotebookLM Client (Deep Seam)**:
Lớp bọc seam sâu của NotebookLMClient nhằm cung cấp một giao diện phẳng duy nhất, tự động điều phối các loại tác vụ sinh/tải Structured Artifacts và ẩn đi cấu trúc RPC dịch vụ con phức tạp của thư viện Google thô. Giúp tăng tính leverage và đơn giản hóa việc viết unit tests.

**Dynamic ID Override**:
A routing mechanism that allows developers to dynamically override Google Notebook IDs using environment variables (e.g., `NOTEBOOKLM_CORE_ID`) to prevent hardcoded configuration values across different staging environments.

**NotebookLMService (Dịch vụ Điều phối Nguồn & Artifact NotebookLM)**:
Module dịch vụ sâu hợp nhất tại `ccba_notebooklm._service` chịu trách nhiệm bọc `CCBANotebookLMClient`, tự động điều phối SHA-256 registry caching, Lazy Maskara security gating, và cung cấp API đơn giản hóa cho các quy trình RAG và Artifact flow.

---

## 4. Chính Sách Kiểm Thử, CI Gates & An Toàn Tiến Trình

**Kiểm thử cô lập (Isolated Test Execution)**:
Chiến lược chạy từng file kiểm thử độc lập trong một sub-process Python cô lập kèm giới hạn thời gian (timeout 5s) và khóa đơn tiến trình (`ensure_single_instance()`). Mô thức này ngăn chặn triệt để hiện tượng rò rỉ tiến trình, treo CPU hoặc đứt gãy phiên làm việc của AI Agent.
_Avoid_: Test chung, pytest unscoped, full test run

**Chính sách 2 Tầng Kiểm thử (2-Tier Testing Policy)**:
Mô hình phân tầng kiểm thử bắt buộc: Fast Unit Tests (Layer 1, runtime < 2.0s, chạy hàng ngày qua cờ `-m "not slow"`) và Slow Integration Tests (Layer 2, bắt buộc gắn decorator `@pytest.mark.slow` hoặc `@pytest.mark.stress`).

**Test Speed Guard**:
Công cụ Linter & Pre-commit hook tại `scripts/hooks/test_speed_guard.py` tự động đo thời gian thực thi của tệp test và phát cảnh báo/chặn commit nếu một tệp test chạy > 2.0s mà không được dán nhãn `@pytest.mark.slow`.

**Automation-First Quality Gate (Cổng Chất lượng Hướng Tự động hóa)**:
Nguyên tắc chuyển giao toàn bộ việc kiểm soát cú pháp, kiểu dữ liệu và định dạng mã nguồn cho các công cụ phân tích tĩnh tự động (Ruff, Mypy, Pre-commit hooks) thay vì tiêu hao ngân sách chỉ dẫn của LLM bằng các quy định văn bản hiển nhiên.

**Two-Layer Sub-Agent Guardrail (Rào chắn Kép Sub-Agent)**:
Cơ chế bảo vệ trong quy trình Code Review kết hợp chặn prompt tường minh (chống đệ quy, cấm gọi lệnh review con) và giới hạn công cụ (read-only tools / `disable-model-invocation`), ngăn chặn triệt để hiện tượng bùng nổ đệ quy sub-agents lồng nhau.

**Cross-Agent Parity Bridge (Cầu nối Tương thích Đa Tác nhân)**:
Cơ chế duy trì tính tương thích giữa các định dạng tệp cấu hình tác nhân khác nhau (`AGENTS.md` theo chuẩn mở và `CLAUDE.md` của Claude Code) tại thư mục gốc repository, đảm bảo mọi công cụ AI đều tự động nạp cùng một bộ chỉ dẫn Layer 1 nhất quán.

**DetachedExecutionEngine (Động cơ Thực thi Detached An toàn Tiến trình)**:
Module sâu hợp nhất tại `scripts/eval/process_safety.py` chịu trách nhiệm quản lý an toàn tiến trình (Single-instance Process Lock, Tree Kill), thực thi tiến trình chạy ngầm detached không bị gián đoạn daemon, dọn dẹp log atomic, và tự động phát hiện danh sách file test bị thay đổi từ `git status`.

**SpokeSynchronizer (Bộ Đồng bộ Spoke)**:
Module sâu hợp nhất tại `scripts/spoke/spoke_synchronizer.py` chịu trách nhiệm định vị Hub thông minh (Smart Hub Discovery), đồng bộ nguyên tử tệp tin skills/workflows, hòa trộn danh mục `catalog.yaml` an toàn và đăng ký Spoke bảo mật với Hub.

**UpstreamEvaluator (Trình Đánh giá Thượng nguồn)**:
Module sâu hợp nhất tại `scripts/spoke/upstream_evaluator.py` thay thế cho tiến trình IPC rời rạc cũ để thực hiện trinh sát, đối soát catalog và đánh giá tự động các tính năng port từ thượng nguồn.

**DocumentAuditor (Trình Kiểm định Tài liệu & Governance)**:
Module sâu hợp nhất tại `scripts/doc_auditor.py` đóng vai trò Coordinator điều phối 5 Sub-Auditors nội bộ để kiểm soát chất lượng tài liệu, skills và quy định quản trị đằng sau giao diện báo cáo chuẩn hóa `AuditReport`.

**Hierarchical Section Parser**:
The parsing algorithm in `validate_skills.py` that tracks Markdown heading levels using a stack to determine which lines belong to a workflow section.

**Exclusion Headers**:
A set of common static headings (such as "Lưu ý", "Tham chiếu") that temporarily disable step-validation checking to prevent false positives.

**Boost Escalation Gate (Cổng Leo Thang Boost)**:
Quy chuẩn chuyển giao và leo thang bài toán kỹ thuật từ vòng lặp TDD bế tắc ($\ge 3$ vòng fail liên tiếp) hoặc các ca bẫy đa tiến trình/đa package sang chu trình suy luận đa tác nhân (`/boost`), ngăn chặn triệt để hành vi đoán mò và tiêu hao ngữ cảnh vô ích.

**Deep Problem Brief (Hồ Sơ Vấn Đề Chuyên Sâu)**:
Bản đóng gói thông tin kỹ thuật tiêu chuẩn hóa (Failure Manifest, Tested Hypotheses, Code Seams, Error Logs, Actionable Recommendations) do Agent tự động biên soạn khi kích hoạt Boost Escalation Gate để cung cấp ngữ cảnh cô đọng cho quy trình suy luận sâu.

**Three-Phase Reasoning Hierarchy (Hệ Phân Cấp Suy Luận 3 Pha)**:
Mô hình kiến trúc đa tác nhân phỏng theo Antigravity Boost: Pha 1 (Goal & Strategy Formulation - Orchestrator phân rã bài toán), Pha 2 (Parallel Execution & Verification - Các Subagents chuyên biệt kiểm chứng đa giả thuyết độc lập kèm rào chắn Two-Layer Guardrail), và Pha 3 (Synthesis & Solution Delivery - Hợp nhất giải pháp và phản biện chéo).

**Team Sheet (Bản Phân Bổ Đội Ngũ)**:
Tệp tin tài liệu hóa `.agents/teams/[project]_team_sheet.md` trong Teamwork Framework gồm 2 lớp cấu trúc phân tách rõ ràng: Lớp 1 - Accountability Mapping (ánh xạ 11 Ghế trách nhiệm giải trình của CCBA Charter 2026 với các milestones nghiệm thu của con người) và Lớp 2 - Worker Assignments (danh sách động các AI Subagents, phạm vi file/seam độc quyền, tiêu chí nghiệm thu và chính sách timeout).

**Exclusive Seam Ownership (Phân Quyền Seam Độc Quyền)**:
Nguyên tắc phân định ranh giới trong Teamwork: Mỗi Worker Subagent chỉ được cấp quyền đọc và phân tích các tệp tin trong phạm vi seam được Orchestrator chỉ định tường minh trong prompt dispatch. Mọi sản phẩm trung gian được xuất ra thư mục sandbox cô lập (`.system_generated/scratch/worker_{N}/`) và duy nhất Orchestrator có quyền tổng hợp, ghi file chính thức lên codebase nhằm ngăn chặn race condition và conflict ghi đè.

**Post-Merge Diff Audit (Kiểm Toán Phân Vùng Hậu Hợp Nhất)**:
Cơ chế kiểm định độc lập do Success Auditor hoặc Orchestrator thực thi sau mỗi milestone bằng cách so khớp danh sách tệp thay đổi thực tế (`git diff --name-only`) với danh sách file scope đã phân quyền trong `team_sheet.md`, chủ động chặn đứng nguy cơ rò rỉ ranh giới module (Seam Boundary Leakage).

**Teamwork Session (Phiên Điều Phối Đa Tác Nhân)**:
Quy trình điều phối đa tác nhân dài hạn (/ccba-teamwork) chia làm 4 giai đoạn (Interview $\rightarrow$ Team Sheet $\rightarrow$ Parallel Milestone Execution $\rightarrow$ Success Audit) phục vụ xử lý các dự án quy mô lớn phân rã đa luồng công việc song song, phân biệt với quy trình /boost (suy luận sâu ngắn hạn tập trung giải quyết bế tắc kỹ thuật).

**Antigravity Lifecycle Hooks (Móc Vòng Đời Antigravity)**:
Cơ chế `hooks.json` của Antigravity Platform cho phép chạy các lệnh shell tại các sự kiện vòng đời (PreToolUse, PostToolUse, PreInvocation, Stop) để kiểm soát, chặn hoặc tiêm ngữ cảnh vào Agent. Giao tiếp qua stdin/stdout JSON camelCase.

**Hook Bridge Adapter (Bộ Chuyển Đổi Móc)**:
Adapter Layer mỏng tại `scripts/hooks/antigravity_hook_bridge.py` dịch giữa Antigravity stdin/stdout I/O (camelCase, decision string) và CCBA HookCoordinator (snake_case, exit_code int). Không chứa business logic — chỉ là lớp dịch schema.

**Fail-Safe Hook Protocol (Giao Thức Móc Dự Phòng An Toàn)**:
Nguyên tắc thiết kế: Mọi ngoại lệ trong hook bridge đều fallback về `{"decision": "allow"}`, không bao giờ làm gián đoạn trải nghiệm IDE. Đảm bảo hooks không trở thành single point of failure.

---

## 5. Pháp Điển Xây Dựng, VBHN & Xử Lý Tài Liệu

**LegalIntelPipeline (Unified Legal Intelligence Deep Module)**:
Deep module hợp nhất của package `ccba-legal-intel` cung cấp seam công khai duy nhất `pipeline.process_document(url_or_id)` điều phối toàn bộ chu trình cào Chrome CDP, bảo vệ session CookieVault, mutex lock, giải mã bảng TVPL, phân tích AST và đóng gói OKF Bundle.

**LegalProcessor (Legal Advisory Deep Seam)**:
Seam điều phối phân tích xung đột văn bản pháp lý (`LexConflictEngine`), trích xuất điều khoản sửa đổi và tạo báo cáo tư vấn pháp lý Dual-Layer.

**LegalSyncEngine (Cloud Sync Deep Seam)**:
Deep module của `ccba-legal-intel` chịu trách nhiệm đồng bộ legal registry lên Google NotebookLM và Google Drive chung, quản lý tính toán băm SHA-256 deduplication và nguồn tài liệu.

**Open Knowledge Format (OKF) Bundle Structure**:
Cấu trúc đóng gói tài liệu tri thức chuẩn mực: `metadata.yaml` (ID, SHA-256), `[slug].md` (nội dung làm sạch, anchor {#dieu-X}), và `index.md` (mục lục SEO).

**AST Parsing & Delta Patching cho Văn bản Pháp luật**:
Cắt lớp cấu trúc văn bản pháp luật thành Abstract Syntax Tree (Chương $\rightarrow$ Mục $\rightarrow$ Điều $\rightarrow$ Khoản $\rightarrow$ Điểm) và áp dụng các file `DeltaPatch` YAML để tự động sinh Văn Bản Hợp Nhất (VBHN).

**Three-Tier Fallback (Quy trình tải tệp ba tầng)**:
Quy trình tải tài liệu pháp lý 3 tầng (Tier 1: Local & Cache, Tier 2: Cloud Drives/S3, Tier 3: Chrome CDP crawl) được triển khai trong crawler để tối ưu hóa hiệu suất, tránh cào web lặp lại và giảm thiểu nguy cơ bị khóa tài khoản VIP.

**TVPLSessionMutex (Khóa loại trừ tương hỗ phiên TVPL)**:
Cơ chế khóa loại trừ tương hỗ (Mutex lock) dựa trên tệp tin lock để đảm bảo chỉ có tối đa một phiên cào web (Chrome CDP) VIP diễn ra tại một thời điểm, ngăn ngừa lỗi đăng nhập đồng thời trên hệ thống Thư viện Pháp luật (TVPL).

**PDFProcessingPipeline (Unified PDF Preprocessor Deep Module)**:
Deep module của package `ccba-pdf-prep` cung cấp seam công khai duy nhất `pipeline.process(pdf_path, output_dir)` điều phối toàn bộ pipeline phân tích PDF, tiling ảnh, trích xuất khung tên và tổng hợp composite.
_Avoid_: PDFPrepEngine, pdf_pipeline, pdf_processor

**Source Manifest (Biên bản nguồn)**:
Bản ghi siêu dữ liệu bắt buộc được tạo ra trong Pha 1 (Recon) của quy trình port tính năng (`ccba-xia`), bao gồm đường dẫn repo, nhánh, commit SHA, loại giấy phép (`license_type`) và danh sách dependencies cốt lõi.
_Avoid_: Source info, repo metadata

**Copy-Raw (Sao chép thô)**:
Chế độ port tính năng (`--copy-raw`) trong `ccba-xia` cấy ghép mã nguồn với số lượng thay đổi tối thiểu, đánh dấu tường minh các file chưa tuân thủ tiêu chuẩn Platform và bắt buộc tạo follow-up issue refactor.
_Avoid_: Copy, raw copy, as-is copy

**Section-Based Thresholds**:
Dynamic constraints in microstructure auditing where different passive voice and stylistic rules are applied based on the parsed section header (e.g., Methods vs. Discussion).

**Signal Phrases Matcher**:
Pattern matching algorithms used to verify structural components of academic texts, such as identifying the 3-moves of the CARS model in an Introduction.

**Bối cảnh Nghiên cứu (Research Territory)**:
Thuật ngữ chuẩn hóa thay thế cho "Lãnh thổ nghiên cứu" (Move 1 trong mô hình CARS), biểu thị khu vực kiến thức, tầm quan trọng và bối cảnh tổng quan của đề tài nghiên cứu.
_Avoid_: Lãnh thổ nghiên cứu, Vùng nghiên cứu.

**Academic Title Page**:
The automatically formatted cover section of a research paper containing title, author names, affiliations, and corresponding email, generated from Markdown YAML frontmatter.

**Citation Consistency Audit**:
The verification algorithm in `microstructure_audit.py` that cross-references in-text citations with the references section.

**Belief Archaeology (Khảo cổ học Niềm tin)**:
The analytical process of extracting a speaker's hidden assumptions and worldviews from video transcript and visual frames.

**Storyboard Coarse Sampling**:
The first-stage frame extraction method that downloads storyboard image grids from CDN and slices them at chapter/heatmap timestamps, avoiding raw video downloading.

**Talking Head Filter**:
The image filtering logic that rejects frames consisting only of the speaker's face without educational slides, drawings, or code.

**Constitution-Driven Traceability Matrix (Ma Trận Truy Vết Dẫn Dắt Bởi Thể Chế)**:
Mô hình cấu trúc dữ liệu (`cross_references.yaml`) ánh xạ 2 chiều chính xác 100% giữa từng Đặc tả Kỹ thuật (Spec/User Story/AC) với từng Điều/Khoản/Phụ lục trong các văn bản quy chế pháp lý và tài liệu thiết kế hệ thống, đảm bảo tính giải trình và khả năng kiểm toán toàn diện.

**Hybrid Two-Tier Legal Sync (Cơ Chế Phân Phối Dữ Liệu Pháp Lý 2 Tầng — ADR 0050)**:
Cơ chế 1-lệnh (`python -m ccba_legal sync --pull-latest`) cho phép Spoke Dự án tự động kéo các gói tri thức OKF v2.4 chuẩn: Ưu tiên quét thư mục `ccba-legal-knowledge/legal_docs` cục bộ lân cận trên máy (Tier 1 - Offline tốc độ cao) và fallback tự động sang Cloud Legal Vault (Tier 2).

**LegalDocStatus Lifecycle Enum (Hệ Thống Enum Vòng Đời Văn Bản Pháp Lý — ADR 0050)**:
Chuẩn phân loại trạng thái hiệu lực động (`LegalDocStatus.ACTIVE`, `LegalDocStatus.SUPERSEDED`, `LegalDocStatus.PARTIALLY_AMENDED`, `LegalDocStatus.PENDING_EFFECTIVE`, `LegalDocStatus.DRAFT`) trong `ccba_legal.models` tích hợp cơ chế tự động gắn banner cảnh báo pháp lý và gợi ý văn bản thay thế khi Agent tra cứu văn bản cũ.

**Mock Data Isolation Guard (Rào Chắn Cách Ly Dữ Liệu Thử Nghiệm — ADR 0050)**:
Quy chuẩn và bài kiểm thử CI cưỡng chế chuyển toàn bộ output của các script demo/test vào `tests/fixtures/mock_*/`, tuyệt đối ngăn chặn file dữ liệu giả định làm ô nhiễm thư mục `.md/` hoặc không gian tri thức thật của Spoke.

**Non-Destructive Additive Registry Merge (Hòa Trộn Danh Mục Pháp Lý Bảo Toàn — ADR 0050)**:
Chiến lược hòa trộn `legal_registry.yaml` khi đồng bộ: tự động sao lưu bản `.bak`, cập nhật trạng thái vòng đời SSOT cho các văn bản chuẩn và bảo tồn 100% các ghi chú, phân loại riêng của Spoke Dự án.

---

## 6. Quản Trị Doanh Nghiệp IDOP & Cổng Giao Tiếp Viện IBST (ADR 0042, 0043)

**Tri-Repo Server Synchronization Gate (ADR 0042)**:
Cơ chế đồng bộ hóa tuần tự kéo mã mới nhất của cả 3 kho lưu trữ cốt lõi (`ccba-legal-knowledge` $\rightarrow$ `IDOP-CCBA-WAY` $\rightarrow$ `ccba-agent-platform`) trước khi kích hoạt Auto-Tuner lúc 00:00 hàng đêm trên Server Spark.

**Master OneDrive 5TB Offloading Pattern (ADR 0041 / P7.23)**:
Nguyên tắc lưu trữ: 58 SharePoint lists chỉ lưu trữ Metadata (Text, Lookups, URLs). Toàn bộ file binary nặng (Revit `.rvt` 500MB, file scan HĐ có dấu đỏ, hồ sơ thầu HSMT) được tự động phân luồng sang 5TB Master OneDrive (`ccba@ibst-bim.vn`) theo 5 thư mục module chuẩn hóa.

**Headless IDOPBridge SDK (ADR 0042)**:
Module Python kết nối trực tiếp đa nền tảng (Windows Kỹ sư & Linux Server) qua Microsoft Graph REST API và App-Only Certificate (`c055c7a4-9150-4bd5-bf01-445c65467feb`) để tự động cập nhật tiến độ WBS, PGV và đăng ký tài liệu ISO 19650 vào `CdeDocuments`.

**Tiered AI Pre-Submission Gate (Rào Chắn Tiền Kiểm 3 Tầng — ADR 0042)**:
Hệ thống kiểm soát đa cấp trước khi nộp hồ sơ trình Viện IBST:
- **Tier 1 (Hard-Floor Auto-Block):** Tự động khóa cứng 100% đối với văn bản luật hết hiệu lực, tạm ứng $> 90\%$ hoặc sai lệch toán học dòng tiền 3 tầng.
- **Tier 2 (Governance Override):** Cho phép Giám đốc (`ROLE_DIRECTOR`) phê duyệt vượt rào đối với các trường hợp ngoại lệ nghiệp vụ và bắt buộc ghi nhật ký giải trình bất biến (`Audit Trail`) vào `lessons_learned.json`.
- **Tier 3 (Advisory Warnings):** Cảnh báo mềm về văn phong, định dạng và nhắc nhở mốc tiến độ WBS.

**Local Staging Queue (Hàng Đợi Lưu Trữ Cục Bộ — ADR 0043)**:
Cơ chế đệm dữ liệu tại [`.md/idop_staged/`](.md/) khi SharePoint IDOP đang bảo trì, mất mạng hoặc ở chế độ DEV, giúp Kỹ sư tiếp tục làm việc liên tục (Zero-Downtime).

**Idempotent Replay (Đồng Bộ Bù Bất Biến — ADR 0043)**:
Quy trình quét hàng đợi [`.md/idop_staged/`](.md/) và đẩy bù lên Microsoft Graph API khi có mạng trở lại mà không tạo bản ghi trùng lặp trên SharePoint.

**CI Schema Contract Drift Gate (ADR 0043)**:
Bài kiểm thử tự động trên Hub (`test_idop_schema_compatibility.py`) bảo vệ các trường dữ liệu cốt lõi (`ProjectCode`, `NationalProjectID`, `ContractId`, `JobAssignments`, `CdeDocuments`) không bị đổi tên hay xóa bỏ trong lúc nhóm IDOP phát triển tính năng mới.

**Zero-Config Dual-Mode Auth (ADR 0043)**:
Cơ chế tự động chuyển đổi giữa chế độ Mock Sandbox (`IDOP_ENV=DEV` - không cần mật khẩu/chứng chỉ) và chế độ Production (`IDOP_ENV=PROD` - xác thực qua `.pfx`), giúp kỹ sư mới và CI runner chạy thử nghiệm tức thì mà không cần xin cấp quyền.

**Personal Sandbox Spoke (Spoke Cá Nhân — ADR 0046)**:
Không gian làm việc, nghiên cứu và thử nghiệm cá nhân của từng kỹ sư, chuyên gia thuộc phân hệ `specialized_extension` (`sub_type: personal_sandbox`), được cách ly bằng chế độ sandbox và tự động kế thừa toàn bộ AI Gateway, Skills và Security Hooks từ Hub.

**CCBA Charter 2026 Accountability Seats (11 Ghế Giải Trình — ADR 0046)**:
Mô hình quản trị nhân sự theo Sơ đồ Trách nhiệm Giải trình (Phụ lục 01 Quy chế CCBA 2026) gồm 11 Ghế chức năng (`GIAM_DOC`, `PHO_GIAM_DOC`, `CO_VAN_PHAP_LY_QA`, `TRUONG_PHONG_TONG_HOP`, `PHU_TRACH_KE_TOAN`, `TRUONG_PHONG_RD_HTQT`, `IDOP_LEAD`, `TRUONG_PHONG_BIM_THIET_KE`, `TRUONG_PHONG_BIM_DU_AN`, `CHU_TRI_HOP_DONG_PM`, `CHU_TRI_BO_MON`, `KY_SU_THUC_THI`) gắn liền với 5 Phòng Ban chức năng.

**5-Level QC Gate (Quy Trình Kiểm Soát Chất Lượng 05 Cấp — ADR 0046)**:
Quy trình rà soát và phê duyệt hồ sơ dịch vụ kỹ thuật 5 cấp theo Điều 13 Quy chế CCBA 2026 (Cấp 1: Kiểm soát Kỹ thuật nội bộ $\rightarrow$ Cấp 2: Phê duyệt Quản trị DA $\rightarrow$ Cấp 3: Kiểm soát Lãnh đạo Phòng $\rightarrow$ Cấp 4: Thẩm định Pháp lý & QA $\rightarrow$ Cấp 5: Phê duyệt Lãnh đạo và Phát hành).

**Sandbox Draft Watermark & Promotion Protocol (ADR 0046)**:
Cơ chế tự động chèn thủy ấn `[CCBA SANDBOX DRAFT]` cho mọi báo cáo tạo ra từ Spoke cá nhân, khóa cứng trần phê duyệt ở Cấp 1, và quy trình chuyển giao 3 bước (Cleanse $\rightarrow$ Target Ingestion $\rightarrow$ PGV Staging) khi hoàn thành bàn giao sang Spoke Dự Án chính thức.

