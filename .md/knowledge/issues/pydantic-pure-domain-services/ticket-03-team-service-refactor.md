# Ticket 03: Refactor `team.py`, File Mutex Lock & JSON Persistence

> **Part of**: [Wayfinder Map](map.md)  
> **Type**: Task [AFK]  
> **Status**: `BLOCKED` (Blocked by: [Ticket 01](ticket-01-models-definition.md))  
> **Assignee**: Antigravity Agent  

---

## 🎯 Mục Tiêu
1. Cập nhật [`packages/ccba-ai/src/ccba_ai/services/team.py`](../../../../packages/ccba-ai/src/ccba_ai/services/team.py):
   - `load_tasks() -> list[TeamTask]`: Tự động parse từng phần tử JSON thành `TeamTask`.
   - `save_tasks(tasks: list[TeamTask | dict], ...)`: Tự động chuyển đổi `[t.model_dump() if isinstance(t, TeamTask) else t for t in tasks]` trước khi ghi JSON.
   - `add_task(name, owner, ...) -> TeamTask`: Trả về `TeamTask`.
   - `claim_task(name, owner, ...) -> TeamTask`: Trả về `TeamTask`.
   - `complete_task(name, ...) -> TeamTask`: Trả về `TeamTask`.
2. Viết/Cập nhật bài test cho `team.py` tại `packages/ccba-ai/tests/test_team.py`.

## 🧪 Tiêu Chí Nghiệm Thu
- Pass 100% test suite thao tác task database (add, claim, complete, serialize).
