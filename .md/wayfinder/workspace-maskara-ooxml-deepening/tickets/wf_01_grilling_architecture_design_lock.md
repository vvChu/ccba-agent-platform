# 🎫 WF-01: Phản biện & Chốt Thiết kế Chi tiết cho 3 Ứng viên Kiến trúc (Workspace/Hub Root Seam, Maskara Redaction Seam, OOXMLValidator Seam)

> **Thuộc bản đồ:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../map.md)  
> **Loại ticket:** `Grilling [HITL]`  
> **Trạng thái:** `CLOSED` (`2026-11-18` — Đã khóa đủ `5/5` câu `Q1`–`Q5`)  
> **Assignee:** `AI Platform Architect & Kỹ sư Trưởng`  
> **Phụ thuộc:** Không có (Mở khóa cho [WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)](wf_02_peer_plan_audit_gate.md))

---

## 1. Bối cảnh & Câu hỏi Cốt lõi

Cả 3 ứng viên hạng `Strong` trong báo cáo kiểm định `.md/scratch/architecture-review/architecture-review-20261118-0605.html` đều tác động tới Public Seam (`ccba_harness`, `ccba_legal`, `ccba_maskara`, `mdconverter`, `ccba_ooxml`) hoặc các tệp `covered_paths` đang được bảo vệ bằng chữ ký SHA-256 (`ADR-0058`, `RULE-2.21`), đồng thời chạm ngưỡng `ONE_WAY_DOOR` theo [ADR-0067](../../../../docs/adr/0067-one-way-door-manifest-and-backpressure-circuit-breaker.md). Cần thực hiện một phiên Socratic Grilling (`/ccba-grilling`, hỏi từng câu một) để khóa toàn bộ thiết kế trước khi sang [WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)](wf_02_peer_plan_audit_gate.md).

## 2. Danh sách Quyết định Cần Chốt (Design Tree Frontiers `Q1`–`Q5`)

1. **`Q1` — Chiến lược cắt lát Micro-PR & `TradeoffCard` (`ADR-0067`):**
   - Chốt số lượng Micro-PR (`<= 200` logic LOC / PR, hoặc gộp theo từng ứng viên kèm `TradeoffCard`) tương ứng với [WF-03: Làm sâu Seam Phân giải Workspace & Hub Root (resolve_workspace_and_hub_roots) cho ccba_legal, ccba_harness và scripts/spoke](wf_03_deepen_workspace_and_hub_root_seam.md), [WF-04: Làm sâu Seam Che giấu Secret & PII Việt Nam (ccba_maskara) và Hợp nhất 3 Bộ Quét Phân kỳ](wf_04_unify_maskara_secret_and_pii_seam.md), và [WF-05: Làm sâu Seam OOXMLValidator (ParsedOOXMLPackage) & Đóng gói ZIP Tất định cho ccba_ooxml](wf_05_deepen_ooxml_validator_and_pack_seam.md) để làm rõ `[FOG-001]`.
2. **`Q2` — Hợp đồng `resolve_workspace_and_hub_roots` & Khả năng chạy Spoke Tier-0 (Ứng viên #1):**
   - Chốt thứ tự ưu tiên phân giải trong `WorkspaceHubContext`: đối số tường minh $\to$ `CCBA_HUB_PATH` / `HUB_PATH` $\to$ duyệt ngược từ `start_dir` tìm `.md/workspace_context.yaml` / `.agents/workspace_context.yaml` / `workspace_context.yaml` / `.git` / `pyproject.toml` $\to$ dịch đường dẫn Windows via `wslpath` trên POSIX.
   - Chốt cơ chế dùng chung thuần stdlib cho [spoke_bootstrap.py](../../../../scripts/spoke/spoke_bootstrap.py#L354-L404) & [check_hub_import_depth.py](../../../../scripts/spoke/check_hub_import_depth.py#L45-L105) khi chạy ở Spoke Tier-0 chưa cài `ccba_harness`, cũng như chính sách bảo vệ [daemon.py](../../../../packages/ccba-harness/src/ccba_harness/evals/daemon.py#L88-L121) không để mất logic fallback tìm Hub `.env` trên repo editable.
3. **`Q3` — Chiến lược 3 Phương Ngữ Placeholder & Guard PII Việt Nam (Ứng viên #2):**
   - Quyết định cách `ccba_maskara` xử lý 3 phương ngữ placeholder đang bị test assert độc lập: `[MASKARA_REDACTED:<rule_id>]` ([test_scanner.py](../../../../packages/ccba-maskara/tests/test_scanner.py#L59)), `[API_KEY_REDACTED]`/`[EMAIL_REDACTED]` ([test_miner.py](../../../../packages/ccba-harness/tests/test_miner.py#L23-L30), [test_log_eval_miner.py](../../../../scripts/tests/test_log_eval_miner.py#L46-L57)), và `[REDACTED_API_KEY]`/`[REDACTED_CCCD]` ([test_phase1_mdconverter_seams.py](../../../../packages/mdconverter/tests/test_phase1_mdconverter_seams.py#L164-L173)) — dùng cờ chọn dialect/mapper tại thin adapter hay chuẩn hóa một bộ token duy nhất kèm cập nhật test?
   - Chốt ngưỡng guard cho regex CMND 9 số / CCCD 12 số (ví dụ: ranh giới từ `\b` + tránh khớp nhầm mã văn bản/tọa độ hoặc giữ đúng hành vi test hiện tại) để thu hẹp `[FOG-002]`.
4. **`Q4` — Ranh giới tách `validation/base.py` `< 800 LOC`, `RedliningValidator` & Tắt Side-effect `stdout` (Ứng viên #3):**
   - Chốt cấu trúc module nội bộ khi tách [base.py](../../../../packages/ccba-ooxml/src/ccba_ooxml/validation/base.py#L44-L265) (`949 LOC`) và cơ chế tích hợp `ParsedOOXMLPackage` với [redlining.py](../../../../packages/ccba-ooxml/src/ccba_ooxml/validation/redlining.py#L11-L106) (đang dùng `xml.etree.ElementTree.parse` thay vì `lxml` an toàn).
   - Xác nhận xử lý [docx.py](../../../../packages/ccba-ooxml/src/ccba_ooxml/validation/docx.py#L68) (`compare_paragraph_counts()` đang in `Paragraphs: ...` ra `stdout` cả khi `verbose=False`) và kiểm tra liệu có test nào đang assert chuỗi `stdout` đó hay không.
5. **`Q5` — Quản trị `module_budget_baseline.json`, Re-anchor SHA-256 & Tài liệu Kiến thức:**
   - Chốt việc xóa entry `validation/base.py` (và dọn entry thừa `ccba_ai/client.py: 1216` vốn đã rút xuống `753 LOC` `[đo thực tế]`) khỏi [module_budget_baseline.json](../../../../packages/ccba-harness/src/ccba_harness/module_budget_baseline.json#L1-L11), đồng bộ `packages/*/AGENTS.md`, [CONTEXT.md](../../../../CONTEXT.md), và làm rõ phương án cập nhật `covered_sha256` cho 5 Profile-B verifiers (`RULE-2.21`).

## 3. Tiêu chí Hoàn thành (Completion Criteria)

- [x] Tự gán `Assignee` trên ticket trước khi bắt đầu phiên chất vấn (`Claiming` theo `/ccba-wayfinder` Bước 2).
- [x] Hoàn tất lần lượt `5/5` câu hỏi `Q1`–`Q5` theo `/ccba-grilling` với xác nhận rõ ràng của Kỹ sư Trưởng.
- [x] Xuất Decision Log tổng hợp & Bản Kế hoạch triển khai chi tiết (bao gồm `TradeoffCard` và Audit Receipt `ADR-0061`) để nạp vào [WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)](wf_02_peer_plan_audit_gate.md).
- [x] Cập nhật kết quả vào mục *Quyết định đã chốt* của [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../map.md), giải quyết `[FOG-001]`, đóng ticket `WF-01` (`CLOSED`) và chuyển `WF-02` lên Active Frontier.

## 4. Kết Quả Phê Duyệt (`2026-11-18`)

Toàn bộ quyết định chi tiết và `5` `TradeoffCard` đã được lưu tại [Biên bản Phỏng vấn Grilling & Kế hoạch Triển khai v1.0](../../../knowledge/decisions/2026-11-18_workspace_maskara_ooxml_grilling_resolution.md):

- **`Q1` (`[FOG-001]` Resolved):** `1` vòng `WF-02` Peer Audit + chuỗi `5` Micro-PR (`PR-1a`, `PR-1b`, `PR-2`, `PR-3a`, `PR-3b`) + `PR-4` Rollup, kèm `5` `TradeoffCard` và `--merge` cho commit neo `covered_sha256`.
- **`Q2`:** Tạo `_workspace_roots.py` thuần stdlib tại `ccba_harness` (`WorkspaceHubContext`, `resolve_workspace_and_hub_roots`), bỏ qua `packages/<pkg>/pyproject.toml` nội bộ, bảo toàn mock surface `resolve_project_root()`, và đồng bộ sang `scripts/_guardrails/_workspace_roots.py` cho Spoke Tier-0.
- **`Q3` (`[FOG-002]` Resolved):** Tách `PII_REGEX_PATTERNS` khỏi pre-commit secret scan, dùng guard `(?<![-\w.])` chống khớp nhầm đuôi UUID (`0/527` dương tính giả `[đo thực tế]`), hỗ trợ `3` `dialect` (`maskara`, `bracket_suffix`, `bracket_prefix`) + PEP 562 lazy `_default_scanner`.
- **`Q4`:** Phân rã `validation/base.py` (`949 LOC`) theo Composition (`base.py` + `_parsed_package.py` + `_relationship_checks.py` + `_xsd_engine.py`, `<= 350 LOC`/tệp, `<= 50 LOC`/hàm), dùng chung `1` `ParsedOOXMLPackage` (kèm `copy.deepcopy` & `_SECURE_OOXML_PARSER`) qua cả `DOCXSchemaValidator` và `RedliningValidator`, tắt rác `stdout` khi `verbose=False`, sắp xếp `7` `rglob()`.
- **`Q5`:** Xóa `2` mục (`validation/base.py` và `ccba_ai/client.py`) khỏi [module_budget_baseline.json](../../../../packages/ccba-harness/src/ccba_harness/module_budget_baseline.json#L1-L11), đồng bộ `AGENTS.md` + `compile_catalog.py` trong từng PR mở seam, giữ `[FOG-003]` (`registry.py`) cho `WF-06`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
