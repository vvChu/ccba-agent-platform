---
proposal_id: "2026-11-04_enrich-skills-youtube-learn-and-ask"
type: "skill"
name: "enrich-skills-youtube-learn-and-ask"
status: "open"
priority: "Trung bình"
proposed_by_project: "vvc-notes"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-11-04"
applies_to: ["Phần mềm"]
---

# RFC Proposal: Chuẩn Hóa Khối KaTeX & Cầu Nối Liên Ngành trong ccba-youtube-learn và Khung Cược Trước trong ccba-ask

## 1. Bối cảnh & Vấn đề (Context & Problem)
- **Thực trạng**:
  - Khi bóc tách bài giảng/video chuyên sâu bằng kỹ năng `ccba-youtube-learn` (Belief Archaeology), các mô hình toán học và cấu trúc tài chính/định lượng (như Black-Litterman, Sharpe Ratio, Pass-Through Fee...) thường bị LLM diễn giải bằng văn xuôi tản mạn hoặc tự sáng tác công thức giả, gây suy giảm độ chính xác học thuật. Đồng thời, các concept sinh ra từ video có xu hướng bị cô lập trong ốc đảo đơn ngành (*Source Clique Silo*).
  - Khi người dùng hoàn tất phiên động não phát tán ý tưởng bằng `/ccba-ask brainstorm` (theo `brainstorm_templates.md`), kết quả thường dừng lại ở danh sách `Action items` phẳng mà thiếu cơ chế gắn kết sang các công cụ phản biện hoặc cổng thực thi cược xác suất có kiểm chứng.

## 2. Giải pháp Kỹ thuật (Technical Solution)
1. **Nâng cấp `ccba-youtube-learn`**:
   - `SKILL.md`: Cưỡng chế quy tắc trong Phase 4 — khi diễn giả nhắc tới mô hình định lượng/toán học, bắt buộc tường minh hóa thành khối LaTeX độc lập (`$$...$$`) kèm giải thích biến số; nghiêm cấm tự sáng tác công thức cho các khái niệm quản trị định tính.
   - `references/worldview_template.md`: Thêm trường `- **Cầu nối Liên ngành (Cross-Domain Synapses):**` vào khối `## Vault Check` để chủ động liên kết thế giới quan sang 2–3 lĩnh vực ngoài ngành (Kỹ thuật hệ thống, Quản trị rủi ro, Kiến trúc AI).
2. **Nâng cấp `ccba-ask`**:
   - `references/brainstorm_templates.md`: Bổ sung mục **5. Khung Cược Trước & Chuyển tiếp Phản biện (Pre-Flight Conviction Handoff)** ở cuối Bước 5, tự động xuất kèm khối 3 dòng (`🎯 Cược của tôi` / `💣 Điểm gãy` / `🔍 Câu hỏi ép cung AI`) cho phương án ưu tiên số 1 để người dùng có thể dán sang các công cụ phản biện tiếp theo (`Command.md`, `/ccba-grilling`, hoặc `/ccba-to-spec`).

## 3. Tiêu chí Nghiệm thu & Kiểm Định (Acceptance Criteria & Verification)
- [x] Cả 2 kỹ năng tuân thủ trần $\le 200$ dòng vật lý (`ccba-youtube-learn/SKILL.md`: 102 dòng; `ccba-ask/SKILL.md`: 125 dòng).
- [x] Điểm số năng lực quản trị (GPI) được bảo toàn nguyên vẹn: `ccba-youtube-learn` (GPI = 12.0) và `ccba-ask` (GPI = 14.0).
- [x] Vượt qua 100% các cổng kiểm định trên Hub:
  - `python scripts/governance/compile_catalog.py` $\to$ PASS.
  - `python scripts/validate_skills.py` $\to$ PASS (76/76 skills validated).
  - `python scripts/governance/check_spoke_leakage.py` $\to$ PASS.
