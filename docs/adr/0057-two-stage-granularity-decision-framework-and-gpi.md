# 0057. Two-Stage Granularity Decision Framework, Granularity Placement Index (GPI), and 3-Tier Skills Architecture

* **Status:** Accepted
* **Date:** 2026-09-07
* **Deciders:** CCBA Platform Core Team
* **Consulted:** ADR 0030 (Instruction Budget), ADR 0035 (Deep Modules), ADR 0040 (Skills Hierarchy), ADR 0053 (Teamwork Multi-Agent), ADR 0056 (Skills Standardization)

---

## Context & Problem Statement

Sau khi hoàn thành di trú 100% legacy workflows sang Agent Skills theo chuẩn hóa namespace ccba-* (ADR 0056), quy mô nền tảng đạt **100 Agent Skills**. Sự phát triển nhanh chóng này đặt ra ba thách thức kiến trúc mới:

1. **Thế Lưỡng Nan Về Độ Phân Rã (The Granularity Dilemma):** Thiếu một tiêu chuẩn định lượng khách quan để xác định: *Khi nào một năng lực nên trở thành một Skill độc lập (.agents/skills/), khi nào nên là một tài liệu tham chiếu nạp tăng tiến (
eferences/*.md), và khi nào bắt buộc phải là một hàm thuần túy trong package (packages/*/src/)*?
2. **Vùng Mù Kiểm Thử & Phình To Mã Nguồn (Script Bloat & Blind Spots):** Khảo sát hạm đội phát hiện 14 kỹ năng đang chứa tới **105 tệp tin với 35.680 dòng mã nguồn trong scripts/** (như parser Word/PDF, regex pháp lý, XML sanitizers) nằm ngoài phạm vi kiểm thử tự động của Monorepo packages và linter.
3. **Bẫy Nhồi Nhét & Lệch Pha (Prompt Bloat & Package-Skill Desync):** Nhồi nhét quá nhiều hướng dẫn vi mô làm loãng ngân sách chú ý (Attention Dilution - Liu et al., TACL 2024), trong khi viết tay schema tham số trong SKILL.md dẫn tới nguy cơ lệch pha với mã nguồn backend (chiếm 35%–45% sự cố runtime trong các hệ thống tác tử công nghiệp).

---

## Decision Outcome

Đội ngũ kiến trúc CCBA quyết định ban hành và thực thi toàn diện:

### 1. Kiến Trúc Monorepo 3 Tầng (3-Tier Agent Architecture)
- **Tầng 1 — Deterministic Engines / Packages (packages/*/src):** Mã nguồn thuần Python/TypeScript, xử lý logic nặng, I/O, thuật toán xác định; kiểm thử 100% bằng Unit Tests trong CI; tuyệt đối không chứa prompt.
- **Tầng 2 — Cognitive Interfaces (.agents/skills/ & 
eferences/*.md):** Các module nhận thức tự đóng gói theo chuẩn *Agent Skills Open Standard* (gentskills.io), kiểm soát chặt chẽ ngân sách chỉ dẫn qua cơ chế **Progressive Disclosure** (Khai mở tăng tiến).
- **Tầng 3 — Composite Orchestrators (.agents/workflows/):** Đồ thị trạng thái (StateGraph) hoặc kiến trúc phân quyền hữu hạn (Single-Writer Protocol theo ADR 0053) điều phối quy trình đa tác tử.

### 2. Khung Quyết Định Phân Rã Hai Giai Đoạn (Two-Stage Framework)

#### Giai đoạn 1: Hai Cổng Bất Biến (Structural Invariant Gates)
- **Cổng 0 (The Determinism Gate):** Nếu tác vụ giải quyết được 100% bằng giải thuật xác định (regex, AST parse, math, file I/O) $\rightarrow$ **Bắt buộc là Tầng 1 (Package Function / Deep Seam)**. Cấm tạo Skill độc lập.
- **Cổng 1 (The Orchestration Gate):** Nếu tác vụ điều phối nhiều tác tử song song, yêu cầu chuyển trạng thái StateGraph có checkpoints hoặc cần con người phê duyệt (HITL) $\rightarrow$ **Bắt buộc là Tầng 3 (Composite Orchestrator)**.

#### Giai đoạn 2: Chỉ Số Phân Rã Kỹ Năng (Granularity & Placement Index - GPI)
Áp dụng cho các năng lực nhận thức tại Tầng 2 để định tuyến:

\mathbf{GPI} = (S \times 2.5) + (K \times 2.0) + (A \times 2.0) - (P \times 1.5)

*Thang điểm 1.0 – 5.0:*
- **$ (Reasoning Steps):** Số bước suy luận nhận thức của LLM.
- **$ (Interface / Schema Complexity):** Độ phức tạp tham số đầu vào/ra.
- **$ (Autonomous Model Invocation):** Mức độ cần Agent tự động triệu hồi.
- **$ (Parent Domain Coupling):** Mức độ gắn kết với Master Skill sở hữu.

*Quy tắc định tuyến:*
- **$\text{GPI} < 12.0$ $\rightarrow$ Tier 2A (Progressive Reference):** Lưu trữ trong 
eferences/<name>.md của Master Skill sở hữu; nạp theo nhu cầu (iew_file), cấm tạo thư mục skill riêng.
- **$\text{GPI} \ge 12.0$ $\rightarrow$ Tier 2B (Standalone Kernel Skill):** Đủ điều kiện tạo thư mục riêng trong .agents/skills/ccba-<name>/.
*(Lưu ý: Các hệ số trọng số hiện là Provisional Heuristic Weights và sẽ được hiệu chuẩn bằng dữ liệu telemetry sau 1–2 quý vận hành).*

### 3. Hiện Thực Hóa Bộ Công Cụ Trong packages/ccba-harness
- Xây dựng module ccba_harness.gpi: Định nghĩa GPIMetrics, ArchitectureTier, DecisionRequest, và hàm đánh giá valuate_two_stage_decision. Chặn triệt để các lỗi toán học IEEE 754 float NaN, boolean coercion và chuẩn hóa namespace ccba-*, igbim-*, platform-loader.
- Nâng cấp SkillValidator: Bổ sung kiểm tra frontmatter gpi:, short-circuit Cổng 0/1 và API valuate_skill_file.
- Cung cấp CLI ccba-harness evaluate-gpi: Hỗ trợ đánh giá trực tiếp file markdown hoặc tham số dòng lệnh, xuất báo cáo ANSI hoặc JSON.
- Đóng gói 38 unit tests chuyên trách với tỷ lệ pass 100%.

### 4. Cưỡng Chế Quy Chuẩn Qua Pull Request Template
- Khởi tạo .github/pull_request_template.md tích hợp checklist bắt buộc chạy ccba-harness evaluate-gpi --file <path> cho mọi đề xuất tạo Skill mới.

### 5. Xuất Bản Bản Thiết Kế Di Trú Hạm Đội (Fleet Skills Migration Blueprint)
- Xuất bản tài liệu BLUEPRINT-2026-SKILLS-001 rà soát 100/100 skills:
  - Phân loại: 6 Tier 1, 34 Tier 2A, 51 Tier 2B, 9 Tier 3.
  - Lập bản đồ di chuyển 105 tệp scripts (35.680 LOC) xuống các packages monorepo.
  - Bảo toàn tuyệt đối cờ disable-model-invocation: true cho 75 User Rituals (0 token nền).

---

## Consequences

### Positive
- **Chuẩn Hóa Định Lượng:** Chấm dứt tranh cãi cảm tính về kích thước kỹ năng bằng công thức GPI đo lường được.
- **Tối Ưu Ngân Sách Ngữ Cảnh:** Giảm thiểu lãng phí token nền nhờ đưa các micro-skills về 
eferences/*.md (chỉ đọc khi cần).
- **Loại Bỏ Vùng Mù Code:** Đưa toàn bộ logic nặng từ scripts/ về packages/ được bảo vệ bởi unit tests và type check.
- **Bảo Toàn Trạm Vệ Tinh:** Quy chế ánh xạ SKILL_DEPRECATION_ALIASES loại trừ 100% nguy cơ Zombie Bloat tại Spoke.

### Neutral / Trade-offs
- Các kỹ sư khi đề xuất Skill mới cần thực hiện thêm một bước kiểm định ccba-harness evaluate-gpi.
- Bộ trọng số thực nghiệm cần được theo dõi và hiệu chuẩn bằng OpenTelemetry trong các đợt phát hành tới.
