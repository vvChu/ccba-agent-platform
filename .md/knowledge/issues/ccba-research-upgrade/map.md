# Bản đồ Wayfinder: Nâng cấp Kỹ năng ccba-research (`ccba-research-upgrade`)

> **Label:** `wayfinder:map`  
> **Trạng thái:** Hoàn tất (Completed)  
> **Ngày hoàn thành:** 2026-07-24  

---

## 🎯 Điểm đích (Destination)

Nâng cấp toàn diện kỹ năng [`ccba-research`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-research/SKILL.md) và workflow [`/ccba-research`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/workflows/ccba-research.md) dựa trên các cải tiến vượt trội từ kho thượng nguồn `claudekit-engineer`:
1. Tích hợp rào chắn ngân sách tìm kiếm **Search Budget Cap (Tối đa 5 tool calls)**.
2. Chuẩn hóa **Mẫu Báo cáo Kỹ thuật 5 phần** (Executive Summary, Key Findings, Implementation Recommendations, References & Citations, Unresolved Questions).
3. Bổ sung quy chuẩn **Kiểm chứng Nguồn tin Chéo (Cross-Reference Validation)** và ưu tiên tài liệu mới trong 12 tháng gần nhất / VBPL hợp nhất hiện hành.
4. Cơ chế lưu trữ **Research Artifact linh hoạt** theo ngữ cảnh (mặc định tại `.md/knowledge/research_and_studies/research-[slug].md` hoặc thư mục issue tương ứng).

---

## 📝 Ghi chú (Notes)

- **Các kỹ năng & công cụ liên quan**: [`wayfinder`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/wayfinder/SKILL.md), [`ccba-research`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-research/SKILL.md), `python scripts/validate_skills.py`.
- **Nguyên tắc**: Tham chiếu ticket theo tên đầy đủ kèm liên kết. Tất cả tickets đã hoàn thành.

---

## 📋 Quyết định đã chốt (Decisions so far)

- [`[Upgrade Skill ccba-research]`](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/ccba-research-upgrade/ticket-1-upgrade-skill-ccba-research.md) — *Đã cập nhật SKILL.md với Search Budget Cap (5 tool calls), Template 5 phần, Cross-Reference Validation & Dynamic Storage.*
- [`[Sync Workflow ccba-research]`](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/ccba-research-upgrade/ticket-2-sync-workflow-ccba-research.md) — *Đã đồng bộ workflow ccba-research.md mô tả các rào chắn mới khớp với SKILL.md.*

---

## 🌫️ Sương mù chiến trận / Chưa xác định rõ (Not yet specified)

- Mở rộng cơ chế tự động nén ngữ cảnh báo cáo khi nhúng vào các workflow lớn như `/ccba-academic-writing` hoặc `/ccba-legal-intel`.

---

## 🚫 Ngoài phạm vi (Out of scope)

- Xây dựng Pipeline đối soát tự động hàng tuần (Weekly Upstream Auto-Sync Audit) trên CI/CD (Đã chủ động loại trừ ở Lựa chọn A để giữ hệ thống tinh gọn).

---

## 🎟️ Danh sách Tickets ở Biên giới (Frontier Tickets)

- [x] [`[Upgrade Skill ccba-research]`](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/ccba-research-upgrade/ticket-1-upgrade-skill-ccba-research.md) *(Đã đóng)*
- [x] [`[Sync Workflow ccba-research]`](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/ccba-research-upgrade/ticket-2-sync-workflow-ccba-research.md) *(Đã đóng)*
