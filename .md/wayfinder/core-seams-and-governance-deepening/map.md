# 🗺️ Bản đồ Định hướng: Làm sâu Seam Lõi & Hợp nhất Quản trị (Wayfinder Map)

> **Mã định danh:** `WAYFINDER-CORE-SEAMS-GOVERNANCE-20261115`  
> **Trạng thái:** `IN_PROGRESS` (Frontier hiện tại: [WF-05: Chuẩn hóa Seam Quét Tham số, IP & Machine-Path Thuần Stdlib và Thu gọn check_spoke_cleanliness dưới 800 LOC](tickets/wf_05_unify_stdlib_parameter_cleanliness_scanners.md))  
> **Khởi tạo:** `2026-11-15` | **Chế độ dự án:** `hybrid` (`ccba-agent-platform` Hub Monorepo)  
> **Phạm vi áp dụng:** 4 Package lõi (`ccba-ai`, `ccba-harness`, `ccba-legal-intel`, `ccba-qc-core`) + 13 Frontmatter Callers + 3 Parameter/IP/Machine-Path Scanners (8 Micro-PRs)  
> **ADR-0061 Audit Receipt:** `model_routing.v1` → `ccba_ai:choose_model` (`MATCH`), `maskara_scanner.v1` → `ccba_maskara:MaskaraScanner` (`MATCH`) | `index_sha256`: `fe4c3c11ca879eba54a8790ade072dbd98022f26bb1393585dee90149dddacfc`

---

## 🎯 1. Điểm Đích (Destination)

Triển khai toàn diện **3 Ứng viên Kiến trúc hạng `Strong`** từ báo cáo kiến trúc `.md/scratch/architecture-review/architecture-review-20261115-0825.html` theo quy trình kiểm soát rủi ro một chiều (`ADR-0067`) và khóa cứng nghiệm thu (`ADR-0058`), đảm bảo:

1. **Ứng viên #1 — PEP 562 Lazy Package Seams, Deferred `AIClient` & Cô lập `pymupdf`:**
   - Độ trễ nạp leaf/routing module trong subprocess sạch giảm xuống `< 15 ms` (so với mức nền `283.72–644.24 ms` / `+1,214..+2,390` modules); `openai`, `httpx`, `fitz`, `pymupdf` không xuất hiện trong `sys.modules` khi import leaf/routing (`ccba_ai.routing`, `ccba_legal.models`, `ccba_harness.gpi`, `ccba_qc_core.jurisdiction`).
   - Bảo toàn `100%` `576` import sites, đạt `0` `OrphanLazyExportViolation` / `DuplicateAllExportViolation` trong [check_dependency_contracts.py](../../../scripts/governance/check_dependency_contracts.py#L473-L565).
   - Giữ nguyên hợp đồng runtime `isinstance(ccba_ai.async_ai, AsyncAIClient)` tại [test_async_client.py](../../../packages/ccba-ai/tests/test_async_client.py#L22) và `patch("ccba_ai.async_ai.chat_multi")` tại [test_qc_core.py](../../../packages/ccba-qc-core/tests/test_qc_core.py#L177); dọn sạch `14` dòng eager `import fitz` (gồm [pipeline.py](../../../packages/ccba-qc-core/src/ccba_qc_core/pipeline.py#L8-L9)) để đạt `0` cảnh báo `fitz` deprecation trên stderr khi import package.

2. **Ứng viên #2 — Hợp nhất 13 Bộ trích xuất Frontmatter & Làm sâu `SkillValidator`:**
   - Hợp nhất tập đóng `13` caller production quản trị Skill/Markdown/Eval/Spoke (trên nền `5` bản `content.split("---", 2)` và regex/parser lệch pha, loại trừ rõ `7` domain splitters chuyên biệt) về `1` seam chuẩn `parse_markdown_frontmatter` / `SkillFrontmatterSpec(raw_block, ...)` với `re.DOTALL` (bảo toàn byte CRLF/comments và không nuốt `ScannerError` trả `{}`), kết hợp fallback stdlib nhẹ có thứ tự `sorted()` tất định cho [find_skills.py](../../../scripts/spoke/find_skills.py#L53).
   - Phân rã [skill_validator.py](../../../packages/ccba-harness/src/ccba_harness/skill_validator.py#L40) từ `1,481 LOC` xuống `<= 450 LOC` mỗi module (`<= 800 LOC` trần cứng) và `<= 50 LOC` mỗi function (`RULE-2.20`), đồng thời loại bỏ thao tác đọc lặp lại đĩa tại dòng `778`.

3. **Ứng viên #3 — Hợp nhất 3 Bộ quét Parameter, IP & Machine-Path Thuần Stdlib:**
   - Hợp nhất `3` scanner ([check_hardcoded_parameters.py](../../../scripts/governance/check_hardcoded_parameters.py#L27-L160), [check_spoke_cleanliness.py](../../../scripts/spoke/check_spoke_cleanliness.py#L25-L175), [peer_gate.py](../../../packages/ccba-harness/src/ccba_harness/peer_gate.py#L544-L590)) về cùng luật chuẩn thuần stdlib (`scan_parameter_cleanliness` / `_ParameterCleanlinessScanner`), không kéo thêm phụ thuộc ngoài cho kịch bản Spoke đồng bộ qua [sdk_inspector.py](../../../scripts/spoke/sync/sdk_inspector.py#L70-L74).
   - Lệnh mặc định `check_hardcoded_parameters.py --dir .` chạy dưới `1.0s` (giảm từ `8,676.16 ms` / `2,199` false positives trong `.venv`), triệt tiêu các lỗi giả `'qwen-local*'` và `'3.2.1.1'`, bắt được đường dẫn Windows chứa dấu cách, và thu gọn [check_spoke_cleanliness.py](../../../scripts/spoke/check_spoke_cleanliness.py) từ `979 LOC` xuống `< 800 LOC`.

4. **Khóa cứng Kiểm định Toàn sàn (`ADR-0058`):**
   - `python -m ccba_harness verify-patch --preset ci`, `compile_catalog.py --check`, `compile_skills_docs.py --write` và `sync_hub_adr_matrix.py` đều thoát mã `0`.

---

## 📝 2. Ghi Chú (Notes)

- **Nguyên tắc vận hành (`Plan, don't do`):** Trong suốt giai đoạn [WF-01: Phản biện & Chốt Thiết kế Chi tiết cho 3 Ứng viên Kiến trúc (PEP 562, Frontmatter Seam, Stdlib Parameter Scanner)](tickets/wf_01_grilling_architecture_design_lock.md) và [WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)](tickets/wf_02_peer_plan_audit_gate.md), tuyệt đối không sửa mã production (`packages/*`, `scripts/*`, `.agents/*`, `docs/*`).
- **Kỹ năng tham chiếu:** `/ccba-codebase-design`, `/ccba-wayfinder`, `/ccba-grilling`, `/ccba-implement`, `/ccba-tdd`.
- **Hiến pháp & ADR đối chiếu:**
  - [ADR-0057: Two-Stage Granularity Decision Framework & GPI](../../../docs/adr/0057-two-stage-granularity-decision-framework-and-gpi.md)
  - [ADR-0058: Verification Lock & Alignment](../../../docs/adr/0058-live-collaboration-artifacts-workspace-mirroring-and-charter-alignment.md)
  - [ADR-0061: Platform-Aware KISS v2.0 & Quarantine Governance](../../../docs/adr/0061-platform-aware-kiss-v2-and-quarantine-governance.md)
  - [ADR-0067: One-Way Door Manifest & Backpressure Circuit-Breaker](../../../docs/adr/0067-one-way-door-manifest-and-backpressure-circuit-breaker.md)
  - [session_learnings.md](../../knowledge/session_learnings.md)

---

## ✅ 3. Quyết Định Đã Chốt (Decisions So Far)

- `[DECISION-001]` **Khảo sát & Phản biện Kép 5 Cổng (`architecture-review-20261115-0825.html`)**: Hoàn tất quét toàn repo (`539` tệp non-test Python, `512` tệp hợp đồng phụ thuộc `0` vi phạm), chọn đúng `3` ứng viên hạng `Strong` (`in-process`) và loại/hoãn `6` mục không đạt cổng hoặc ROI thấp hơn (`cli.py` glue code, false-positive `skill_auditor.py`/`doc_auditor.py`, PR `#610` đã xong, backlog ROI `#4–#6`).
- `[DECISION-002]` **Ràng buộc Kỹ thuật Bất biến Trước Khi Phỏng Vấn Grilling**:
  - `check_init_lazy_exports_parity` ([check_dependency_contracts.py](../../../scripts/governance/check_dependency_contracts.py#L473-L524)) kiểm tra parity AST 1:1 giữa `__all__` và mọi symbol không chứa dấu chấm trong `_*_EXPORTS`, yêu cầu mô hình `_LAZY_EXPORTS` + `if TYPE_CHECKING:` + `__getattr__` (tham khảo mẫu chuẩn tại [ccba_harness/cli/__init__.py](../../../packages/ccba-harness/src/ccba_harness/cli/__init__.py#L14-L64)).
  - [test_async_client.py](../../../packages/ccba-ai/tests/test_async_client.py#L22) kiểm tra `isinstance(ccba_ai.async_ai, AsyncAIClient)` và [test_qc_core.py](../../../packages/ccba-qc-core/tests/test_qc_core.py#L177) dùng `patch("ccba_ai.async_ai.chat_multi")`, nên `ai` / `async_ai` phải trả về thực thể `AIClient` / `AsyncAIClient` thật thông qua PEP 562 `__getattr__` + cache vào `globals()`, không bọc bằng proxy giả.
  - [sdk_inspector.py](../../../scripts/spoke/sync/sdk_inspector.py#L70-L74) đồng bộ `check_spoke_cleanliness.py` độc lập sang các Spoke Tier-0, nên phần lõi quét tham số/IP/path chia sẻ phải thuần Python stdlib (không phụ thuộc `ccba_harness` hoặc `pyyaml`).
- `[DECISION-003]` **Kết Quả Khóa Thiết Kế Sau Phỏng Vấn Grilling (`Q1`–`Q5`) & Thẩm định Peer Audit (`Pass 1 -> Pass 3 APPROVE_PLAN`, [Biên bản Quyết định Grilling & Kế hoạch Triển khai v2.1](../../knowledge/decisions/2026-11-15_core_seams_and_governance_grilling_resolution.md))**:
  - `Q1` (DAG `8` Micro-PR + `8` `TradeoffCard`): Thực thi chuỗi thẩm định Peer Plan Audit (`Pass 1` `9e8c03f7-d66d-4bca-9dfe-3e7a5a588b73` `REVISE_PLAN` $\to$ `Pass 2` `94f5c6c2-08af-44e4-9a81-23783877e138` `REVISE_PLAN` $\to$ `Pass 3` `951a1441-976f-49cb-bd84-057689eefb81` **`APPROVE_PLAN`**, `risk_score: 2`, `blocking_conditions: 0`), tiếp nối tuần tự sau lệnh `proceed` bằng `8` Micro-PR (`PR-1a..PR-1d` cho PEP 562 & lazy PyMuPDF, `PR-2a` di dời cơ học `SkillValidator` + khóa SHA-256 `RULE-2.21` bằng `--merge`, `PR-2b` hợp nhất `13` callers frontmatter, `PR-3a..PR-3b` cho Stdlib Parameter Scanner & Spoke Tier-0 Sync).
  - `Q2`: Toàn bộ `4` package gốc dùng `_LAZY_EXPORTS = {...}` không annotation (`ast.Assign`, đúng hợp đồng `check_dependency_contracts.py:490`) + `if TYPE_CHECKING:` + `__getattr__` (gồm nhánh module `services` cho `ccba_ai`) + `__dir__`; `ccba_ai` khởi tạo real `AIClient()`/`AsyncAIClient()` và bind `9` shorthands vào `globals()`; `ccba_harness` giữ eager `import subprocess`; chuyển `14` dòng `import fitz` cùng lời gọi top-level `fitz.TOOLS.mupdf_display_errors(False)` (`provenance.py:30`) sang helper lazy `_get_fitz()` / `import pymupdf as fitz` với `PYMUPDF_MESSAGE=fd:2`.
  - `Q3`: Expose `SkillFrontmatterSpec(raw_block, ...)` & `parse_markdown_frontmatter(text: str)` dùng `re.DOTALL` trên `ccba_harness` (bảo toàn byte CRLF/comments cho `_tuner_mutator.py`, giữ nguyên `extract_frontmatter`); `find_skills.py` giữ fallback stdlib `3` tầng + `sorted(iterdir())`; phân rã `SkillValidator` theo Composition sang `_skill_frontmatter.py`, `_skill_content_checks.py`, `_skill_gpi_gates.py` (`<= 450 LOC`/module trong `<= 800 LOC` trần cứng, `<= 50 LOC`/hàm, bỏ re-read `L778`, re-anchor `verify-ccba-harness/SKILL.md`).
  - `Q4` (`FOG-001`): Đặt `_ParameterCleanlinessScanner` & `scan_parameter_cleanliness` thuần stdlib tại `ccba_harness._parameter_cleanliness` và khai báo đồng bộ sang `scripts/_guardrails/_parameter_cleanliness.py` qua `catalog_base.yaml` & `sdk_inspector.py`.
  - `Q5` (`FOG-003`): Không lập ADR mới; cập nhật `packages/ccba-harness/AGENTS.md` + `CONTEXT.md` trong PR triển khai, lưu Decision Log vào `.md/knowledge/decisions/` và đăng ký LLM-Wiki.

---

## ⚡ 4. Biên Giới & Danh Mục Ticket (The Frontier & Ticket DAG)

### Biên giới Hiện tại (Active Frontier — Unblocked)

| Ticket | Loại | Trạng thái | Assignee | Đầu ra cốt lõi |
| :--- | :--- | :--- | :--- | :--- |
| [WF-05: Chuẩn hóa Seam Quét Tham số, IP & Machine-Path Thuần Stdlib và Thu gọn check_spoke_cleanliness dưới 800 LOC](tickets/wf_05_unify_stdlib_parameter_cleanliness_scanners.md) | `Task [AFK]` | `IN_PROGRESS` | `AI Platform Architect` | Micro-PR `3a`/`3b`: `scan_parameter_cleanliness` / `_ParameterCleanlinessScanner` thuần stdlib (`PR-3a`) + sửa `.venv`, `qwen-local*`, `3.2.1.1`, Win path, Spoke Tier-0 sync & thu gọn `check_spoke_cleanliness.py` dưới `800 LOC` (`PR-3b`) |

### Đã Hoàn Thành (Closed)

| Ticket | Loại | Trạng thái | Assignee | Kết quả |
| :--- | :--- | :--- | :--- | :--- |
| [WF-01: Phản biện & Chốt Thiết kế Chi tiết cho 3 Ứng viên Kiến trúc (PEP 562, Frontmatter Seam, Stdlib Parameter Scanner)](tickets/wf_01_grilling_architecture_design_lock.md) | `Grilling [HITL]` | `CLOSED` | `AI Platform Architect & Kỹ sư Trưởng` | Khóa `5/5` câu `Q1`–`Q5`, xuất [Biên bản Quyết định Grilling & Kế hoạch Triển khai 2026-11-15](../../knowledge/decisions/2026-11-15_core_seams_and_governance_grilling_resolution.md) |
| [WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)](tickets/wf_02_peer_plan_audit_gate.md) | `Task [HITL]` | `CLOSED` | `AI Platform Architect & Grok 4.7 Auditor` | Pass 3 `951a1441-976f-49cb-bd84-057689eefb81` **`APPROVE_PLAN`** (`risk_score: 2`, `blocking_conditions: 0`, `.md/peer_exchange/grok_core_seams_governance_plan_signoff_p3.md`) & Kỹ sư xác nhận `Proceed` |
| [WF-03: Triển khai PEP 562 Lazy Package Seams, Deferred AIClient & Cô lập PyMuPDF cho 4 Package Lõi](tickets/wf_03_pep562_lazy_package_seams.md) | `Task [AFK]` | `CLOSED` | `AI Platform Architect` | PR `#751`..`#754`: PEP 562 cho `ccba_ai`, `ccba_legal`, `ccba_qc_core`, `ccba_harness` + lazy `pymupdf` (`0` cảnh báo `fitz` deprecation, `ccba_harness.gpi` `11.06 ms`) |
| [WF-04: Hợp nhất 9 Bộ Phân tích Frontmatter qua parse_markdown_frontmatter & Phân rã SkillValidator dưới 800 LOC](tickets/wf_04_unify_frontmatter_and_deepen_skill_validator.md) | `Task [AFK]` | `CLOSED` | `AI Platform Architect` | PR `#755` (`PR-2a` phân rã `skill_validator.py` -> `<= 450 LOC`/module + neo SHA-256) & `PR-2b` (`FRONTMATTER_PATTERN`, `SkillFrontmatterSpec`, `parse_markdown_frontmatter` nối `13` callers + fallback `find_skills.py` + neo SHA-256) |

### Đường ống Hạ nguồn (Downstream Tickets — Blocked chờ Frontier)

| Ticket | Loại | Chặn bởi | Phạm vi tóm tắt |
| :--- | :--- | :--- | :--- |
| [WF-06: Kiểm định Liên thông 4 Cổng ADR-0058, Đồng bộ Catalog/Docs SSOT & Đóng Bản đồ Wayfinder](tickets/wf_06_ci_verification_and_catalog_rollup.md) | `Task [AFK]` | [WF-05: Chuẩn hóa Seam Quét Tham số, IP & Machine-Path Thuần Stdlib và Thu gọn check_spoke_cleanliness dưới 800 LOC](tickets/wf_05_unify_stdlib_parameter_cleanliness_scanners.md) | `verify-patch --preset ci`, `compile_catalog.py`, `compile_skills_docs.py --write`, `sync_hub_adr_matrix.py`, đo benchmark hậu cải tiến & đóng bản đồ |

---

## 🌫️ 5. Sương Mù Chiến Trận (Not Yet Specified)

- `[FOG-001]` `[RESOLVED in WF-01 — Q4]` Hình thái đóng gói đồng bộ sang Spoke Tier-0 qua [sdk_inspector.py](../../../scripts/spoke/sync/sdk_inspector.py#L70-L74): đặt `_ParameterCleanlinessScanner` thuần stdlib tại `ccba_harness._parameter_cleanliness` và khai báo đồng bộ sang `scripts/_guardrails/_parameter_cleanliness.py` trong `catalog_base.yaml` + `sdk_inspector.py`, giữ cơ chế fallback `try/except ImportError` trong `check_spoke_cleanliness.py`.
- `[FOG-002]` Sau khi [WF-03: Triển khai PEP 562 Lazy Package Seams, Deferred AIClient & Cô lập PyMuPDF cho 4 Package Lõi](tickets/wf_03_pep562_lazy_package_seams.md) hoàn tất, các package phụ (`ccba-pdf-prep`, `mdconverter`, `ccba-ooxml`) có còn độ trễ nạp bắc cầu đáng kể để mở rộng PEP 562 ở đợt kế tiếp không?
- `[FOG-003]` `[RESOLVED in WF-01 — Q5]` Không tạo ADR mới; cập nhật `packages/ccba-harness/AGENTS.md`, `CONTEXT.md` trong PR triển khai, và lưu [Biên bản Quyết định Grilling & Kế hoạch Triển khai 2026-11-15](../../knowledge/decisions/2026-11-15_core_seams_and_governance_grilling_resolution.md) vào LLM-Wiki.

---

## 🚫 6. Ngoài Phạm Vi (Out of Scope)

- **Các ứng viên bị loại ở 5 Cổng Bằng chứng:** `packages/ccba-legal-intel/src/ccba_legal/cli.py` (`1,455 LOC`, Gate 1 Glue Code >= 70%), `scripts/governance/skill_auditor.py` & `scripts/doc_auditor.py` (Gate 2 False Positive vì đã ủy quyền 100%), và các mục cũ từ `2026-11-05`/`11-06` đã xử lý xong trong PR `#610` (`301fc8fd`).
- **Backlog ROI `#4–#6` (để sau đợt này):** `HarnessGuard` analyzers (`_process_monitor.py` `1,185 LOC` & `_file_monitor.py` `1,127 LOC`), Telemetry HTML/SVG renderers (`fleet.py` `1,024 LOC` & `dashboard.py` `645 LOC`), và `ccba-ooxml` monoliths (`pptx/deck_builder.py` `1,586 LOC` & `validation/base.py` `949 LOC`).
