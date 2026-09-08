---
proposal_id: "2026-09-07_enhance-legal-advisor-grounding-gate"
type: "skill"
name: "enhance-legal-advisor-grounding-gate"
status: "merged"
merged_commit: "d286d8ae3d2b12502766a35f262c99600ee3d8bb"
merged_date: "2026-09-08"
priority: "Cao"
related_issue: ""
proposed_by_project: "vvc_working_space"
proposed_by_archetype: "specialized_extension"
proposed_date: "2026-09-07"
applies_to:
  - Phần mềm
  - Thẩm tra thiết kế
  - Pháp điển
---

# Đề Xuất Nâng Cấp Kỹ Năng `ccba-legal-advisor`: Bổ Sung Rào Chắn Kiểm Chứng Bắt Buộc (Mandatory Grounding Gate)

## 1. Tóm Tắt & Vấn Đề Thực Tế Cần Giải Quyết
Trong quá trình triển khai tư vấn pháp lý xây dựng tại các Spoke (như `vvc_working_space`), phát hiện lỗ hổng nghiêm trọng:
- Khi người dùng đưa ra câu hỏi kỹ thuật có thông số chi tiết (ví dụ: công trình văn phòng 25 tầng, 4 tầng hầm), AI Agent có xu hướng bỏ qua bước truy xuất cơ sở dữ liệu tri thức trên ổ đĩa và chuyển sang suy luận dựa trên bộ nhớ mô hình (LLM parametric memory).
- Hệ quả thực tế: Agent đã trích dẫn quy chuẩn cũ hết hiệu lực (`QCVN 10:2014/BXD`) thay vì quy chuẩn mới nhất **`QCVN 10:2024/BXD`** (hiệu lực từ 01/02/2025) vốn đã được bóc tách và kiểm định chuẩn mực trong kho `ccba-legal-knowledge`.

## 2. Giải Pháp Kỹ Thuật Đã Triển Khai
1. **Thiết lập `MANDATORY GROUNDING INVARIANT`:**
   - Đưa vào rào chắn mệnh lệnh (imperative guardrail) cấm xuất Legal Opinion nếu Agent chưa gọi công cụ kiểm chứng dữ liệu thực tế (`grep_search`, `find_by_name`, `view_file`).
2. **Định tuyến tri thức 3 tầng (Three-Tier Knowledge Routing):**
   - Tầng 1: Cục bộ Spoke (`.\.md\legal_docs\`).
   - Tầng 2: Spoke Tri Thức Gốc (`<ccba-legal-knowledge>/legal_docs/`) theo cơ chế Virtual Hub Fallback.
   - Tầng 3: Danh mục SSOT (`legal_registry.yaml` & `metadata.yaml`) kiểm tra trường `relations.replaces` để loại bỏ văn bản hết hiệu lực.
3. **Bắt buộc dẫn chứng file thực tế (Evidence Citation Obligation):**
   - Mọi điều khoản và quy chuẩn trong Bảng Ma trận bắt buộc phải kèm liên kết `file:///...` trỏ thẳng tới tệp `metadata.yaml` hoặc `clauses.json` nguồn.

## 3. Các Tệp Tin Thay Đổi
- [MODIFY] `.agents/skills/ccba-legal-advisor/SKILL.md` (nâng lên v1.1.0).
- [NEW] `.agents/proposals/2026-09-07_enhance-legal-advisor-grounding-gate.md`.

## 4. Kết Quả Kiểm Thử Cục Bộ
- Đã kiểm tra đối soát 100% chính xác với các gói quy chuẩn `qcvn_03_2022_bxd`, `qcvn_06_2022_bxd`, `qcvn_10_2024_bxd`, `tcvn_2737_2023`, `tcvn_7336_2021` tại Spoke `vvc_working_space`.
