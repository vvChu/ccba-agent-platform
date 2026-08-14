# Ticket 05: Kiểm Định Toàn Trình, Governance Gate & Ghi Nhận ADR-014

> **Part of**: [Wayfinder Map](map.md)  
> **Type**: Task [AFK]  
> **Status**: `BLOCKED` (Blocked by: [Ticket 02](ticket-02-seo-service-refactor.md), [Ticket 03](ticket-03-team-service-refactor.md), [Ticket 04](ticket-04-plan-service-refactor.md))  
> **Assignee**: Antigravity Agent  

---

## 🎯 Mục Tiêu
1. Chạy toàn bộ Fast Test Suite (`pytest -m "not slow"`) để bảo đảm toàn bộ 602+ tests passed 100%.
2. Chạy Governance Gate:
   - `python scripts/validate_skills.py`
   - `python scripts/validate_docs.py`
   - `ruff check packages/ scripts/`
3. Ghi nhận quyết định kiến trúc **ADR-014: Chuẩn Hóa Toàn Bộ Domain Services Sang Pydantic v2 DTOs Thuần Túy** vào [`.md/knowledge/CONTEXT.md`](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/CONTEXT.md).
4. Cập nhật trạng thái các tickets và đóng bản đồ Wayfinder [Map](map.md).

## 🧪 Tiêu Chí Nghiệm Thu
- 0 test failures, 0 lint warnings, 0 doc drift errors.
