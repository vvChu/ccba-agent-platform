---
proposal_id: "2026-11-12_add-ccba-book-compiler"
type: "skill"
name: "add-ccba-book-compiler"
status: "merged"
merged_pr: "#731"
merged_commit: "d55f11db"
merged_date: "2026-11-12"
priority: "Cao"
proposed_by_project: "vvc-notes"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-11-12"
applies_to: ["Phần mềm", "Thẩm tra thiết kế", "Thiết kế"]
---

# RFC Proposal: Đóng Góp Kernel Skill `/ccba-book-compiler` (v1.5.0) Lên Platform Hub

## 1. Bối cảnh & Vấn đề (Context & Problem)
- **Thực trạng**: Khi chuyển hóa các đầu sách/ebook chuyên ngành (`.epub` hoặc `.pdf`) sang hệ thống tri thức Zettelkasten cho các dự án Spoke tri thức và tư vấn, quá trình thủ công thường gặp 4 điểm gãy: (1) tranh chấp khóa giữa tác vụ tương tác và daemon chạy nền; (2) ảnh minh họa PNG/JPG không được nén chuẩn WebP in-memory; (3) lệch thuật ngữ song ngữ hoặc lệch thuật ngữ luật định so với SSoT `ccba_legal.lexicon` / `ccba-legal-knowledge`; (4) thiếu công cụ kiểm định tất định cho hộp bao Excalidraw 16:9 và đồ thị liên kết Markdown.

## 2. Giải pháp Kỹ thuật (Technical Solution)
Đóng gói kỹ năng hạt nhân **Tier 2B Standalone Kernel Skill** `ccba-book-compiler` (`GPI = 19.5 >= 12.0`, `disable-model-invocation: true` theo ADR-0040, liên kết trực tiếp với Public Deep Seam `diagram_layout.v1` của `ccba-diagram`):
1. **Quy trình 6 Pha Chuẩn Hóa (`SKILL.md`, 184 dòng)**:
   - Pha 1: Staging chống đua mức cuốn sách, nén WebP in-memory (`quality=80, max_dim=1200`), Metadata SSoT Gate và cổng thừa kế Hệ Từ Điển Liên Hợp 2 Tầng (`core.lexicon` + `ccba_legal.lexicon`).
   - Pha 2–4: Làm giàu `Source Note`, bóc tách 12–16 `Concept Notes` chuẩn Canonical v8.3 qua Stage 4 `verify_and_correct()` + batch vector flush, và vẽ bản đồ kiến trúc Excalidraw 16:9 (`1.000px <= W <= 1.150px`, `fontSize >= 13`).
   - Pha 5–6: Đóng gói Bộ công cụ thực chiến FBA (`Topic Note`), chạy `wiki_maintain.py` và cổng hậu kiểm tất định 100%.
2. **Tài nguyên & Scripts Kiểm Định Đi Kèm**:
   - `scripts/compress_images_to_webp.py`: Hậu kiểm & nén ảnh WebP viết lại tham chiếu Markdown an toàn.
   - `scripts/verify_book_artifacts.py` & `scripts/verify_excalidraw_map.py`: Kiểm định tất định cấu trúc YAML, Clean Wikilink Invariant (`0` code-pills), hộp bao 2D mũi tên Excalidraw 16:9 và chữ ký `fontSize`.
   - `resources/templates/` & `references/visual_and_diagramming_rules.md`: Bộ mẫu chuẩn hóa cho `Source Note`, `Concept Note`, `FBA Toolkit` và quy chuẩn trực quan.

## 3. Tiêu chí Nghiệm thu & Kiểm Định (Acceptance Criteria & Verification)
- [x] `SKILL.md` tuân thủ trần `<= 200` dòng vật lý (`184` dòng) và đạt chuẩn Governance ADR-0057 (`GPI = 19.5 >= 12.0`).
- [x] Vượt qua 100% các cổng kiểm định trên Hub:
  - `python scripts/governance/compile_catalog.py` -> PASS.
  - `python scripts/validate_skills.py --enforce-gpi` -> PASS.
  - `python scripts/governance/check_spoke_leakage.py` -> PASS.
  - `python -m ccba_harness verify-patch --preset skill` -> PASS.
