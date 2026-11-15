# 🎫 WF-03: Triển khai PEP 562 Lazy Package Seams, Deferred AIClient & Cô lập PyMuPDF cho 4 Package Lõi

> **Thuộc bản đồ:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Lõi & Hợp nhất Quản trị](../map.md)  
> **Loại ticket:** `Task [AFK]`  
> **Trạng thái:** `IN_PROGRESS` (Frontier Active — Claimed; đã mở khóa sau [WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)](wf_02_peer_plan_audit_gate.md))  
> **Assignee:** `AI Platform Architect`

---

## 1. Phạm vi Kỹ thuật (Ứng viên #1)

Loại bỏ eager import và side-effect khởi tạo tại root `__init__.py` trên `4` package lõi, bảo toàn `100%` hợp đồng `__all__` (`ADR-0061`) và `isinstance` / `unittest.mock.patch` trong test suite:

- [packages/ccba-ai/src/ccba_ai/__init__.py](../../../../packages/ccba-ai/src/ccba_ai/__init__.py#L24-L91): Chuyển toàn bộ export (bao gồm `ai`, `async_ai`) sang PEP 562 `_LAZY_EXPORTS` + `if TYPE_CHECKING:` + `__getattr__` cache vào `globals()`. Bảo đảm `import ccba_ai.routing` chỉ nạp leaf (~`10` modules) và `isinstance(ccba_ai.async_ai, AsyncAIClient)` vẫn đúng.
- [packages/ccba-harness/src/ccba_harness/__init__.py](../../../../packages/ccba-harness/src/ccba_harness/__init__.py#L20-L280): Chuyển `237` symbols (`524 LOC`) sang PEP 562 lazy seam chuẩn (tương tự [ccba_harness/cli/__init__.py](../../../../packages/ccba-harness/src/ccba_harness/cli/__init__.py#L14-L64)) để [WF-04: Hợp nhất 9 Bộ Phân tích Frontmatter qua parse_markdown_frontmatter & Phân rã SkillValidator dưới 800 LOC](wf_04_unify_frontmatter_and_deepen_skill_validator.md) và [WF-05: Chuẩn hóa Seam Quét Tham số, IP & Machine-Path Thuần Stdlib và Thu gọn check_spoke_cleanliness dưới 800 LOC](wf_05_unify_stdlib_parameter_cleanliness_scanners.md) gắn public symbol kế tiếp sạch sẽ.
- [packages/ccba-legal-intel/src/ccba_legal/__init__.py](../../../../packages/ccba-legal-intel/src/ccba_legal/__init__.py#L16-L203): Chuyển `30` eager imports / `148` `__all__` sang PEP 562 để cắt luôn lan truyền `1,860` modules tới [jurisdiction.py](../../../../packages/ccba-qc-core/src/ccba_qc_core/jurisdiction.py#L23).
- [packages/ccba-qc-core/src/ccba_qc_core/__init__.py](../../../../packages/ccba-qc-core/src/ccba_qc_core/__init__.py#L5-L22): Chuyển `14` `__all__` sang PEP 562 và cô lập `pymupdf` (`import pymupdf as fitz`) khỏi import top-level tại `14` dòng `import fitz` (gồm [pipeline.py](../../../../packages/ccba-qc-core/src/ccba_qc_core/pipeline.py#L8-L9), [discovery.py](../../../../packages/ccba-qc-core/src/ccba_qc_core/discovery.py#L82), [core.py](../../../../packages/ccba-pdf-prep/src/ccba_pdf_prep/core.py#L13), [detector.py](../../../../packages/ccba-pdf-prep/src/ccba_pdf_prep/detector.py#L12), [vision.py](../../../../packages/ccba-pdf-prep/src/ccba_pdf_prep/vision.py#L12), [cli.py](../../../../packages/ccba-pdf-prep/src/ccba_pdf_prep/cli.py#L127), [provenance.py](../../../../packages/ccba-legal-intel/src/ccba_legal/provenance.py#L21), [formula_harvester.py](../../../../packages/ccba-legal-intel/src/ccba_legal/formula_harvester.py#L709), [gemini.py](../../../../packages/mdconverter/src/mdconverter/core/gemini.py#L293), [analyze_pdfs.py](../../../../packages/mdconverter/scripts/analyze_pdfs.py#L17)) — giữ `PYMUPDF_MESSAGE` theo `RULE-5.13`.

## 2. Tiêu chí Hoàn thành (Completion Criteria)

- [ ] `check_dependency_contracts.py` (`check_package_all_exports` + `check_init_lazy_exports_parity`) đạt `0` vi phạm.
- [ ] Subprocess isolation kiểm chứng `ccba_ai.routing`, `ccba_legal.models`, `ccba_harness.gpi`, `ccba_qc_core.jurisdiction` không nạp `openai`, `httpx`, `fitz`, `pymupdf`, không còn `fitz` stderr deprecation warning, thời gian `< 15 ms` `[đo thực tế]`.
- [ ] `verify-patch --preset code` pass trên cả `4` packages + `mdconverter` + `ccba-pdf-prep`, không phá vỡ [test_async_client.py](../../../../packages/ccba-ai/tests/test_async_client.py#L22) và [test_qc_core.py](../../../../packages/ccba-qc-core/tests/test_qc_core.py#L177).
