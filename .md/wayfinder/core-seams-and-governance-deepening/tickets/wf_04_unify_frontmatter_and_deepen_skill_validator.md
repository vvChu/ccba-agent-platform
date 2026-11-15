# 🎫 WF-04: Hợp nhất 9 Bộ Phân tích Frontmatter qua parse_markdown_frontmatter & Phân rã SkillValidator dưới 800 LOC

> **Thuộc bản đồ:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Lõi & Hợp nhất Quản trị](../map.md)  
> **Loại ticket:** `Task [AFK]`  
> **Trạng thái:** `CLOSED` (`PR-2a` & `PR-2b` đã hoàn tất trên nhánh tích hợp; tiếp nối sang [WF-05](wf_05_unify_stdlib_parameter_cleanliness_scanners.md))  
> **Assignee:** `AI Platform Architect`

---

## 1. Phạm vi Kỹ thuật (Ứng viên #2)

1. **Deep Seam `parse_markdown_frontmatter` / `SkillFrontmatterSpec` (tên duy nhất toàn repo, `0` xung đột):**
   - Khớp chính xác mở/đóng YAML frontmatter từ đầu file (`^---\s*\r?\n...\r?\n---(?:\s*$|\r?\n)`), không bị vỡ khi giá trị scalar chứa `"---"` (sửa lỗi `compile_catalog.extract_frontmatter` nuốt `ScannerError` trả `{}` trên `"Stage A --- Stage B"`).
   - Hợp nhất `9` callers hiện hành: [compile_catalog.py](../../../../scripts/governance/compile_catalog.py#L64-L77), [compile_skills_docs.py](../../../../scripts/governance/compile_skills_docs.py#L80-L93), [audit_skills_hygiene.py](../../../../scripts/governance/audit_skills_hygiene.py#L241-L252), [link_auditor.py](../../../../scripts/governance/link_auditor.py#L35-L48), [eval_runner.py](../../../../.agents/skills/ccba-eval-gate/scripts/eval_runner.py#L92-L109), [skill_validator.py](../../../../packages/ccba-harness/src/ccba_harness/skill_validator.py#L40), [skill_governance.py](../../../../packages/ccba-harness/src/ccba_harness/evals/skill_governance.py#L104-L113), [_tuner_mutator.py](../../../../packages/ccba-harness/src/ccba_harness/evals/_tuner_mutator.py#L47-L63), và [find_skills.py](../../../../scripts/spoke/find_skills.py#L30-L53) (giữ nhánh fallback stdlib nhẹ + sửa `sorted(skills_dir.iterdir())` tại L53 theo chuẩn bất biến inode).
2. **Làm sâu `SkillValidator` (`1,481 LOC` → `<= 800 LOC` / module, hàm `<= 50 LOC`):**
   - Phân rã [skill_validator.py](../../../../packages/ccba-harness/src/ccba_harness/skill_validator.py) (`8` methods > `50 LOC`, đỉnh điểm `_audit_granularity_and_gpi` `244 LOC` ở L712-955) thành các sub-module nội bộ mạch lạc (`SkillFrontmatterSpec`, GPI scorer, cross-link checker).
   - Truyền nội dung đã đọc vào thay cho lệnh đọc lặp lại đĩa tại L778, giữ nguyên public seam tại `ccba_harness` (`__all__` & `_LAZY_EXPORTS`) và backward re-export nếu test có import.

## 2. Tiêu chí Hoàn thành (Completion Criteria)

- [x] Toàn bộ `13` caller mục tiêu dùng `parse_markdown_frontmatter` / `SkillFrontmatterSpec` (kèm fallback stdlib 3 tầng tại `find_skills.py`, bảo toàn byte `raw_block` tại `_tuner_mutator.py`, giữ nguyên `7` domain splitters & `_peer_models.extract_frontmatter`); test hồi quy chứng minh YAML chứa `"---"` không ném hoặc nuốt `ScannerError` trả rỗng `{}`.
- [x] `check_ast_function_length` & `check_module_size_budget` (`RULE-2.20`) đạt `0` vi phạm trên tất cả module chỉnh sửa (`<= 450 LOC` / `<= 50 LOC`), không còn re-read và `iterdir()` chưa sort.
- [x] `verify-patch --preset code --target packages/ccba-harness` và `pytest scripts/tests/` pass `100%`.
