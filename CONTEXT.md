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

**Delivery Spoke (Spoke Triển khai)**:
A downstream project-specific workspace created for a service contract or project execution, which syncs workflows/skills from the Hub.

**Functional Spoke / R&D Spoke (Spoke Chức năng)**:
A permanent workspace owned by a specific department (e.g., BIM Design, BIM Project, Legal & QA) to research rules, develop skills/checklists, and propose updates to the Hub.

**Nền tảng số IDOP**:
The Integrated Digital Operations Platform of CCBA, serving as the physical runtime and repository environment of the Hub/Spoke platform.

**Upstream Loop (Vòng đóng góp ngược)**:
The process where Functional Spokes package and propose local skills or workflows back to the central Hub via Pull Requests and validation gates.

**Downstream Sync (Vòng đồng bộ xuôi)**:
The process where Project Spokes synchronize and update their local `.agents/workflows/` and git-ignored `.agents/skills/` from the Hub.

