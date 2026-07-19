# CCBA Agent Platform Context

The CCBA Agent Services Platform is a framework to develop and coordinate AI agent skills, workflows, and compliance checks across construction consulting projects.

## Language

**Hub**:
The central repository containing the master constitution, catalogs, reusable skills, and templates.
_Avoid_: Central, upstream

**Spoke**:
A downstream project-specific workspace that inherits and syncs bundles of skills/workflows from the Hub.
_Avoid_: Sub-project, spoke repo

**Skill**:
A structured set of agent guidelines, scripts, and completion criteria defined in a `SKILL.md` file.
_Avoid_: Tool, plugin

**Workflow**:
A markdown script registered as a Slash Command that directs agent actions sequentially.
_Avoid_: Scenario, command line script

**Spec (Đặc tả Kỹ thuật)**:
Tài liệu mô tả yêu cầu thiết kế, hành vi và seam kỹ thuật chi tiết cho một tính năng hoặc quy trình công việc, được sinh ra từ quy trình `/ccba-to-spec` và lưu trữ tại `.md/knowledge/specs/spec-{slug}.md`. Thuật ngữ này thay thế hoàn toàn cho khái niệm PRD (Product Requirement Document) đã lỗi thời.
_Avoid_: PRD, Product Requirement Document, Bản yêu cầu sản phẩm

**Bundle**:
A grouping of related skills and workflows organized by domain area (e.g., `_core`, `_software`, `_qc`, `_consulting`).
_Avoid_: Package bundle, module

**Hierarchical Section Parser**:
The parsing algorithm in `validate_skills.py` that tracks Markdown heading levels using a stack to determine which lines belong to a workflow section.

**Exclusion Headers**:
A set of common static headings (such as "Lưu ý", "Tham chiếu") that temporarily disable step-validation checking to prevent false positives.

**Plan Lock**:
A file-based locking mechanism (`.plan.lock`) to prevent lost updates when multiple agents concurrently modify phase status.

**Target Line Override**:
A formatting preservation technique where only specific key-value pairs (like status) in frontmatter are overwritten instead of full file re-serialization.

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

**Cohesive Topic Folder (Thư mục Đề tài Chuyên biệt)**:
A directory structure under `.md/projects/[Ten_De_Tai]/` that contains all raw assets, transcripts, notes, drafts, and compiled Word documents belonging to a single R&D or writing project, preventing file fragmentation.

**Git Core - Cloud Artifacts (Nhân Git - Vệ tinh Cloud)**:
The hybrid synchronization strategy where lightweight, diffable text/code files are synced via Git, while large binaries and raw media files are synchronized via OneDrive/SharePoint.

**Maskara Pre-commit Hook**:
A local Git security hook written dynamically to `.git/hooks/pre-commit` in Spoke workspaces during initialization, which runs the Maskara privacy tool to scan and block commits containing hardcoded API keys or raw credentials.

**Flat NotebookLM Client (Deep Seam)**:
Lớp bọc seam sâu của NotebookLMClient nhằm cung cấp một giao diện phẳng duy nhất, tự động điều phối các loại tác vụ sinh/tải Structured Artifacts và ẩn đi cấu trúc RPC dịch vụ con phức tạp của thư viện Google thô. Giúp tăng tính leverage và đơn giản hóa việc viết unit tests.

**Dynamic ID Override**:
A routing mechanism that allows developers to dynamically override Google Notebook IDs using environment variables (e.g., `NOTEBOOKLM_CORE_ID`) to prevent hardcoded configuration values across different staging environments.

**User Loops (Chu trình Người dùng)**:
Các mô thức hoặc hoạt động lặp đi lặp lại hàng ngày/hàng tuần của người dùng, được định nghĩa qua `loop-me` và tài liệu hóa trong `.md/knowledge/user_loops.md` trước khi tự động hóa thành workflow chính thức.


**Three-Tier Fallback (Quy trình tải tệp ba tầng)**:
Quy trình tải tài liệu pháp lý 3 tầng (Tier 1: Local & Cache, Tier 2: Cloud Drives/S3, Tier 3: Chrome CDP crawl) được triển khai trong crawler để tối ưu hóa hiệu suất, tránh cào web lặp lại và giảm thiểu nguy cơ bị khóa tài khoản VIP.

**TVPLSessionMutex (Khóa loại trừ tương hỗ phiên TVPL)**:
Cơ chế khóa loại trừ tương hỗ (Mutex lock) dựa trên tệp tin lock để đảm bảo chỉ có tối đa một phiên cào web (Chrome CDP) VIP diễn ra tại một thời điểm, ngăn ngừa lỗi đăng nhập đồng thời trên hệ thống Thư viện Pháp luật (TVPL).

**Source Manifest (Biên bản nguồn)**:
Bản ghi siêu dữ liệu bắt buộc được tạo ra trong Pha 1 (Recon) của quy trình port tính năng (`ccba-xia`), bao gồm đường dẫn repo, nhánh, commit SHA, loại giấy phép (`license_type`) và danh sách dependencies cốt lõi.
_Avoid_: Source info, repo metadata

**Copy-Raw (Sao chép thô)**:
Chế độ port tính năng (`--copy-raw`) trong `ccba-xia` cấy ghép mã nguồn với số lượng thay đổi tối thiểu, đánh dấu tường minh các file chưa tuân thủ tiêu chuẩn Platform và bắt buộc tạo follow-up issue refactor.
_Avoid_: Copy, raw copy, as-is copy
