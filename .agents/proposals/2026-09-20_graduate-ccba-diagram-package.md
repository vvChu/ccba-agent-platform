---
proposal_id: "2026-09-20_graduate-ccba-diagram-package"
type: "packages"
name: "graduate-ccba-diagram-package"
status: "proposed"
priority: "Cao"
proposed_by_project: "vvc-second-brain-scripts"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-09-20"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Tất cả Spokes"
---

# RFC Proposal: Đóng Gói Flagship Package `packages/ccba-diagram` & Standalone Kernel Skill `ccba-excalidraw-diagram`

- **Tác giả đề xuất:** Kỹ sư / Agent đại diện Spoke (`vvc-second-brain-scripts`)
- **Ngày lập:** 2026-09-20
- **Trạng thái:** Đang đề xuất (Proposed)
- **Căn cứ pháp lý & kỹ thuật:** [ADR-0045](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0045-hub-proposal-ingestion-governance.md), [ADR-0057](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0057-two-stage-granularity-decision-framework-and-standalone-kernel-skills-governance.md), [ADR-0058](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0058-automation-first-quality-and-deterministic-hard-completion-lock.md), Quy chế CCBA 2026.

---

### 1. Bối cảnh & Động lực Thực tế tại Spoke (Context & Real-world Motivation)

1. **Nỗi đau thực tế (Pain point):**
   Trong các báo cáo tư vấn xây dựng, thẩm tra thiết kế và tài liệu kỹ thuật, sơ đồ trực quan (Excalidraw / Mermaid) thường xuyên gặp các lỗi công thái học nghiêm trọng:
   - Các hình khối bị chồng đè, không có thuật toán tối ưu toạ độ tự động.
   - Đầu mũi tên đè lên hình khối hoặc bị đảo ngược khi các khối nằm quá sát nhau.
   - Thiếu bảng đặc tả ma trận đi kèm để giải thích ngữ nghĩa và luồng dữ liệu cho người đọc.
   - Các mô hình LLM thuần túy không thể tự tính toán toạ độ pixel chính xác trong không gian 2D.

2. **Quá trình ươm tạo & hoàn thiện tại Spoke (`vvc-second-brain-scripts`):**
   Spoke đã phát triển và kiểm chứng qua hàng ngàn tài liệu một bộ **8 Layout Engines Tất Định** (`Sugiyama`, `Wheel`, `Matrix`, `Tree`, `Radial`, `Concentric`, `Value Chain`, `Cycle`) cùng bộ điều phối thông minh kết hợp metadata hint và phân tích topology đồ thị NetworkX.

3. **Giá trị khi phổ biến lên Hub:**
   - Đóng gói thành package dùng chung độc lập **`packages/ccba-diagram`** trong Hub monorepo.
   - Phát hành Standalone Kernel Skill **`ccba-excalidraw-diagram`** ($GPI = 14.0 \ge 12.0$).
   - Mọi dự án Spoke (tư vấn, thiết kế, giám sát, pháp lý) đều có thể gọi lệnh 1 chạm để tối ưu sơ đồ và sinh bảng đặc tả ma trận Markdown chuẩn công thái học 16:9.

---

### 2. Đánh Giá Giá Trị × Rủi Ro × KISS (Evaluation Matrix)

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Rất cao | Tự động hóa 100% khâu sắp xếp toạ độ sơ đồ kỹ thuật, nâng cao tính chuyên nghiệp của báo cáo CCBA |
| **Độ Phức tạp (Complexity)** | Vừa phải | Thuần Python + NetworkX + Grandalf, tách rời hoàn toàn khỏi môi trường Obsidian |
| **Tính Tất Định (Determinism)** | Đạt 100% | Đạt Cổng 0 ADR-0057; mọi thuật toán bố cục đều tất định tuyệt đối |
| **Chỉ số Độc lập GPI** | $GPI = 14.0$ | Vượt ngưỡng $12.0$, đủ chuẩn xếp hạng Tier 2B Standalone Kernel Skill |
| **Rủi ro Rò rỉ (Leakage)** | 0 vi phạm | Vượt qua `check_spoke_leakage.py` và `validate_skills.py` |

---

### 3. Thiết Kế Deep Seams & Đặc Tả Kỹ Thuật tại Hub (Technical Specification)

1. **Vị trí tích hợp tại Hub Monorepo:**
   - Package: [`packages/ccba-diagram`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-diagram/)
   - Skill: [`.agents/skills/ccba-excalidraw-diagram/SKILL.md`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-excalidraw-diagram/SKILL.md)
   - Public Seam export:
     ```python
     from ccba_diagram import (
         apply_smart_layout,
         apply_sugiyama_layout,
         apply_wheel_layout,
         apply_matrix_layout,
         apply_tree_layout,
         apply_radial_layout,
         apply_concentric_layout,
         apply_value_chain_layout,
         apply_cycle_layout,
         DiagramTheme,
         generate_markdown_spec_table,
     )
     ```

2. **CLI Commands:**
   - `ccba-diagram layout input.json -o output.json [--engine auto]`
   - `ccba-diagram spec-table input.json`

---

### 4. Quy Trình Thẩm Định 5 Cổng (5-Gate Verification Log)

1. **Cổng 1 (Package Unit Tests):**
   - Lệnh: `pytest packages/ccba-diagram/tests/ -v`
   - Kết quả: **27/27 passed in 0.85s** (toàn bộ 8 layout engines, geometry clipping, router topology, spec table, CLI).
2. **Cổng 2 (CLI Execution):**
   - Kiểm tra `ccba-diagram --help`, `ccba-diagram layout`, `ccba-diagram spec-table`: **Exit code 0**.
3. **Cổng 3 (Code Quality & Formatting):**
   - Lệnh: `python -m ruff check packages/ccba-diagram/` & `python -m ruff format --check packages/ccba-diagram/`
   - Kết quả: **All checks passed! 22 files already formatted.**
4. **Cổng 4 (Skill Validation & GPI):**
   - Lệnh: `python -m ccba_harness validate-skill --file .agents/skills/ccba-excalidraw-diagram/SKILL.md --enforce-gpi`
   - Kết quả: **Successfully validated 1 SKILL.md file(s) across all CI Gates.**
5. **Cổng 5 (Governance & Catalog Compilation):**
   - Lệnh: `python scripts/governance/check_spoke_leakage.py` & `compile_catalog.py`
   - Kết quả: **0 violations, catalog compiled successfully (74 skills).**
