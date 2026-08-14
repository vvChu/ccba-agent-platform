# Ticket 01: Định Nghĩa Pydantic v2 DTOs Trong `models.py` & Xuất Bản

> **Part of**: [Wayfinder Map](map.md)  
> **Type**: Task [AFK]  
> **Status**: `READY` (Frontier)  
> **Assignee**: Antigravity Agent  

---

## 🎯 Mục Tiêu
Bổ sung các Pydantic v2 `BaseModel` DTOs vào [`packages/ccba-ai/src/ccba_ai/models.py`](../../../../packages/ccba-ai/src/ccba_ai/models.py) và xuất bản ra `__all__`:
1. `SEOAuditResult(BaseModel)`:
   - `score: int = 100`
   - `checks: list[str] = Field(default_factory=list)`
   - `issues: list[str] = Field(default_factory=list)`
   - `file_name: str = ""`
   - `error: str | None = None`
   - Phương thức helper: `to_dict() -> dict[str, Any]` (gọi `self.model_dump()`)
2. `TeamTask(BaseModel)`:
   - `name: str`
   - `owner: str = "None"`
   - `status: str = "pending"`  # pending, in-progress, completed
   - Phương thức helper: `to_dict() -> dict[str, Any]`
3. `PlanCreationResult(BaseModel)`:
   - `status: str = "success"`
   - `plan_title: str = ""`
   - `plan_folder: str = ""`
   - `plan_file: str = ""`
   - `created_files: list[str] = Field(default_factory=list)`
   - Phương thức helper: `to_dict() -> dict[str, Any]`
4. `PhaseUpdateResult(BaseModel)`:
   - `status: str = "success"`
   - `phase_id: str = ""`
   - `phase_name: str = ""`
   - `old_status: str = ""`
   - `new_status: str = ""`
   - `plan_file: str = ""`
   - `phase_file: str = ""`
   - `phase_file_updated: bool = False`
   - Phương thức helper: `to_dict() -> dict[str, Any]`
5. `PlanPhaseData(BaseModel)`:
   - `id: str`
   - `name: str`
   - `status: str`
   - `file: str`
6. `PlanStatusResult(BaseModel)`:
   - `title: str = ""`
   - `metadata: dict[str, Any] = Field(default_factory=dict)`
   - `phases: list[PlanPhaseData] = Field(default_factory=list)`
   - `plan_file: str = ""`
   - Phương thức helper: `to_dict() -> dict[str, Any]`

## 🧪 Tiêu Chí Nghiệm Thu
- Cả 5 DTOs pass unit test định nghĩa mô hình tại `packages/ccba-ai/tests/test_models.py`.
