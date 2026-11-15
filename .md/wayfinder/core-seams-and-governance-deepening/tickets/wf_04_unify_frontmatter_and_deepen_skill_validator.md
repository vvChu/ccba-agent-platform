# 🎫 WF-04: Hợp nhất 9 Bộ Phân tích Frontmatter qua parse_markdown_frontmatter & Phân rã SkillValidator dưới 800 LOC

> **Thuộc bản đồ:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Lõi & Hợp nhất Quản trị](../map.md)  
> **Loại ticket:** `Task [AFK]`  
> **Trạng thái:** `IN_PROGRESS` (Frontier Active — Unlocked sau [WF-03: Triển khai PEP 562 Lazy Package Seams, Deferred AIClient & Cô lập PyMuPDF cho 4 Package Lõi](wf_03_pep562_lazy_package_seams.md))  
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

- [ ] Toàn bộ `9` caller dùng cùng quy tắc trích xuất; test hồi quy chứng minh YAML chứa `"---"` không ném hoặc nuốt `ScannerError` trả rỗng `{}`.
- [ ] `check_ast_function_length` & `check_module_size_budget` (`RULE-2.20`) đạt `0` vi phạm trên tất cả module chỉnh sửa (`<= 800 LOC` / `<= 50 LOC`), không còn re-read L778 và `iterdir()` chưa sort.
- [ ] `verify-patch --preset code --target packages/ccba-harness` và `pytest scripts/tests/` pass `100%`.
