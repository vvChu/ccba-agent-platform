# 🎫 WF-01: Phản biện & Chốt Thiết kế Chi tiết cho 3 Ứng viên Kiến trúc (PEP 562, Frontmatter Seam, Stdlib Parameter Scanner)

> **Thuộc bản đồ:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Lõi & Hợp nhất Quản trị](../map.md)  
> **Loại ticket:** `Grilling [HITL]`  
> **Trạng thái:** `CLOSED` (`2026-11-15`)  
> **Assignee:** `AI Platform Architect & Kỹ sư Trưởng`  
> **Phụ thuộc:** Không có (Mở khóa cho [WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)](wf_02_peer_plan_audit_gate.md))

---

## 1. Bối cảnh & Câu hỏi Cốt lõi

Ba ứng viên hạng `Strong` trong báo cáo kiến trúc `.md/scratch/architecture-review/architecture-review-20261115-0825.html` đều chạm các điểm `ONE_WAY_DOOR` (`__init__.py` Public Seam, hợp đồng kiểm định `ccba_harness`, và kịch bản guardrail đồng bộ tới Spoke Tier-0). Cần chạy vòng lặp Socratic Grilling từng câu một theo `/ccba-grilling` (Nhánh A + B) để khóa toàn bộ lựa chọn thiết kế trước khi xuất bản kế hoạch kiểm định ngang hàng.

## 2. Danh sách Quyết định Cần Chốt (Design Tree Frontiers)

1. **Chiến lược cắt lát Micro-PR & Peer Audit Plan:** Chạy `1` vòng `audit_plan` tổng thể ([WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)](wf_02_peer_plan_audit_gate.md)) rồi tách `3` Micro-PR tuần tự ([WF-03: Triển khai PEP 562 Lazy Package Seams, Deferred AIClient & Cô lập PyMuPDF cho 4 Package Lõi](wf_03_pep562_lazy_package_seams.md) → [WF-04: Hợp nhất 9 Bộ Phân tích Frontmatter qua parse_markdown_frontmatter & Phân rã SkillValidator dưới 800 LOC](wf_04_unify_frontmatter_and_deepen_skill_validator.md) → [WF-05: Chuẩn hóa Seam Quét Tham số, IP & Machine-Path Thuần Stdlib và Thu gọn check_spoke_cleanliness dưới 800 LOC](wf_05_unify_stdlib_parameter_cleanliness_scanners.md)) hay gộp/chia khác.
2. **Mẫu PEP 562 & cơ chế deferred `ai` / `async_ai` + `fitz`/`pymupdf`:** Cách đáp ứng `isinstance(ccba_ai.async_ai, AsyncAIClient)` ([test_async_client.py](../../../../packages/ccba-ai/tests/test_async_client.py#L22)), `patch("ccba_ai.async_ai.chat_multi")` ([test_qc_core.py](../../../../packages/ccba-qc-core/tests/test_qc_core.py#L177)), `check_init_lazy_exports_parity` ([check_dependency_contracts.py](../../../../scripts/governance/check_dependency_contracts.py#L473-L524)), và cô lập `pymupdf`.
3. **Seam `parse_markdown_frontmatter` / `SkillFrontmatterSpec` & phân rã `SkillValidator`:** Vị trí đặt seam, cách giữ fallback stdlib tất định cho [find_skills.py](../../../../scripts/spoke/find_skills.py#L30-L53), và ranh giới tách `skill_validator.py` (`1,481 LOC` → `<=800 LOC`).
4. **Đóng gói bộ quét tham số/IP/path thuần stdlib (`FOG-001`):** Hình thái triển khai cho [check_hardcoded_parameters.py](../../../../scripts/governance/check_hardcoded_parameters.py), [check_spoke_cleanliness.py](../../../../scripts/spoke/check_spoke_cleanliness.py), [peer_gate.py](../../../../packages/ccba-harness/src/ccba_harness/peer_gate.py) và đồng bộ Spoke qua [sdk_inspector.py](../../../../scripts/spoke/sync/sdk_inspector.py#L70-L74).
5. **Phạm vi cập nhật tài liệu tri thức (`FOG-003`):** Chọn ngưỡng cập nhật `CONTEXT.md`, `packages/*/AGENTS.md`, `.md/knowledge/index.md`, hay tạo thêm ADR mới.

## 3. Tiêu chí Hoàn thành (Completion Criteria)

- [x] Hoàn tất mọi câu hỏi trên Frontier với xác nhận rõ ràng từ Kỹ sư Trưởng (`5/5` câu `Q1`–`Q5`: `"Đồng ý"`).
- [x] Xuất Decision Log tổng hợp (relative links chuẩn `RULE-3.5`) & Kế hoạch triển khai chi tiết.
- [x] Cập nhật kết quả vào mục *Quyết định đã chốt* của [Bản đồ Định hướng](../map.md) và mở khóa [WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)](wf_02_peer_plan_audit_gate.md).

## 4. Kết Quả Phê Duyệt (`2026-11-15`)

- **`Q1`:** Chạy `1` vòng `audit_plan` ([WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)](wf_02_peer_plan_audit_gate.md)) rồi triển khai tuần tự theo Micro-PR `<= 200` logic LOC (`ADR-0067`).
- **`Q2`:** Chuẩn hóa PEP 562 `_LAZY_EXPORTS` + `if TYPE_CHECKING:` + `__getattr__` + `__dir__` (khởi tạo thực thể `AIClient`/`AsyncAIClient` thật + bind `9` shorthands tại `ccba_ai`, chuyển `14` dòng `import fitz` sang lazy `import pymupdf as fitz`).
- **`Q3`:** Xuất `parse_markdown_frontmatter` / `SkillFrontmatterSpec` trên `ccba_harness`, giữ fallback stdlib + `sorted(iterdir())` tại `find_skills.py`, và tách `SkillValidator` bằng Composition sang `_skill_frontmatter.py`, `_skill_content_checks.py`, `_skill_gpi_gates.py` kèm re-anchor `RULE-2.21`.
- **`Q4` (`FOG-001`):** Đặt `_ParameterCleanlinessScanner` / `scan_parameter_cleanliness` thuần stdlib tại `ccba_harness` và khai báo đồng bộ sang `scripts/_guardrails/_parameter_cleanliness.py` trong `catalog_base.yaml` + `sdk_inspector.py`.
- **`Q5` (`FOG-003`):** Không lập ADR mới; cập nhật `packages/ccba-harness/AGENTS.md` + `CONTEXT.md` trong PR triển khai, lưu [Biên bản Quyết định Grilling & Kế hoạch Triển khai 2026-11-15](../../../knowledge/decisions/2026-11-15_core_seams_and_governance_grilling_resolution.md) và đăng ký vào LLM-Wiki.
