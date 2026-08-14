# Ticket 04: Refactor `plan.py` DTOs & `test_plan_manager.py`

> **Part of**: [Wayfinder Map](map.md)  
> **Type**: Task [AFK]  
> **Status**: `BLOCKED` (Blocked by: [Ticket 01](ticket-01-models-definition.md))  
> **Assignee**: Antigravity Agent  

---

## 🎯 Mục Tiêu
1. Cập nhật [`packages/ccba-ai/src/ccba_ai/services/plan.py`](../../../../packages/ccba-ai/src/ccba_ai/services/plan.py):
   - `create_plan() -> PlanCreationResult`
   - `update_phase_status() -> PhaseUpdateResult`
   - `get_plan_status() -> PlanStatusResult`
2. Cập nhật [`packages/ccba-ai/tests/test_plan_manager.py`](../../../../packages/ccba-ai/tests/test_plan_manager.py):
   - Cập nhật các assertions truy cập trực tiếp bằng thuộc tính (`res.status`, `res.plan_file`, `res.phases`).

## 🧪 Tiêu Chí Nghiệm Thu
- `pytest packages/ccba-ai/tests/test_plan_manager.py` passed 100%.
