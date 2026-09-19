# Ticket 08: Sửa Lỗi CI `Deploy Skills Docs to GitHub Pages` Đang Thất Bại Trên `main`

- **Type:** Task (AFK / CI & Infra Fix)
- **Status:** open
- **Assignee:** Antigravity AI Agent
- **Target Seam:** `.github/workflows/deploy-pages.yml`, `tests/governance/test_skills_docs_integrity.py`
- **Reference:** GitHub Actions Run ID #35412113932

---

## 🎯 Mục Tiêu
Khắc phục lỗi workflow GitHub Actions `Deploy Skills Docs to GitHub Pages` thất bại liên tục trên nhánh `main`:
```text
ImportError while importing test module 'tests/governance/test_skills_docs_integrity.py'.
tests/governance/test_skills_docs_integrity.py:12: in <module>
    from scripts.governance.compile_skills_docs import (...)
E   ModuleNotFoundError: No module named 'scripts'
```

---

## 📋 Phương Án Khắc Phục
1. Thêm `PYTHONPATH: .` vào env của step `Run Skills Docs Integrity Test Suite` trong file `.github/workflows/deploy-pages.yml`:
   ```yaml
         - name: Run Skills Docs Integrity Test Suite
           env:
             PYTHONPATH: .
           run: |
             pytest tests/governance/test_skills_docs_integrity.py
   ```
2. Trong `tests/governance/test_skills_docs_integrity.py`, bổ sung fallback thêm project root vào `sys.path` (như các test khác trong `scripts/tests/`):
   ```python
   project_root = Path(__file__).resolve().parent.parent.parent
   if str(project_root) not in sys.path:
       sys.path.insert(0, str(project_root))
   ```

---

## ✅ Tiêu Chí Nghiệm Thu (Acceptance Criteria)
- [ ] 1. Chạy test độc lập bằng lệnh `python3 -m pytest tests/governance/test_skills_docs_integrity.py` trong môi trường không cài đặt editable package vẫn PASS 100%.
- [ ] 2. `python -m ccba_harness verify-patch --preset doc` và `verify-patch --preset code` đạt PASS.
- [ ] 3. Đưa vào PR để merge vào `main` làm xanh lại GitHub Pages deployment workflow.
