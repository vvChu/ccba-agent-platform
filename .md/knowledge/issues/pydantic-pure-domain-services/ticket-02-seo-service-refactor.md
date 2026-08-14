# Ticket 02: Refactor `seo.py`, CLI `seo_audit.py`, và `test_seo.py`

> **Part of**: [Wayfinder Map](map.md)  
> **Type**: Task [AFK]  
> **Status**: `BLOCKED` (Blocked by: [Ticket 01](ticket-01-models-definition.md))  
> **Assignee**: Antigravity Agent  

---

## 🎯 Mục Tiêu
1. Cập nhật [`packages/ccba-ai/src/ccba_ai/services/seo.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-ai/src/ccba_ai/services/seo.py):
   - `SEOAuditor.audit_markdown()` $\rightarrow$ trả về `SEOAuditResult`
   - `SEOAuditor.audit_html()` $\rightarrow$ trả về `SEOAuditResult`
   - `SEOAuditor.audit_file()` $\rightarrow$ trả về `SEOAuditResult`
   - `SEOAuditor.audit()` $\rightarrow$ trả về `SEOAuditResult`
   - Các hàm legacy: `audit_markdown()`, `audit_html()`, `audit_file()` $\rightarrow$ trả về `SEOAuditResult`
2. Cập nhật CLI [`scripts/validation/seo_audit.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/validation/seo_audit.py):
   - Đổi từ `result["score"]`, `result["checks"]`, `result["issues"]` sang `result.score`, `result.checks`, `result.issues`.
3. Cập nhật Test Suite [`packages/ccba-ai/tests/test_seo.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-ai/tests/test_seo.py):
   - Kiểm thử truy cập thuộc tính `result.score`, `result.checks`, `result.issues`, `result.file_name`.

## 🧪 Tiêu Chí Nghiệm Thu
- Chạy `pytest packages/ccba-ai/tests/test_seo.py` passed 100%.
- Chạy `python scripts/validation/seo_audit.py README.md` exit code 0.
