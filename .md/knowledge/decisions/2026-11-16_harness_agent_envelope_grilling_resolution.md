# Biên Bản Phỏng Vấn Grilling & Kế Hoạch Triển Khai v1.1: Agent-First JSON Envelope & Semantic Exit Codes Cho `ccba-harness`

> **Ngày chốt Grilling:** `2026-11-16` | **Phiên bản Kế hoạch:** `v1.2` (`APPROVE_PLAN` — Giải trình đầy đủ `COND-HEAL-SSOT`, `COND-NEXT-ACTIONS`, `COND-ARGPARSE-EXIT`, `COND-DOOR-MATRIX`, `COND-THIN-CLI`, `COND-CATALOG-CLI-LINE` + bổ sung 2 mục non-blocking `COND-DOC-FAIL-SPEC`, `COND-TIMEOUT-TEST`)  
> **Nguồn cảm hứng Clean-Room:** [Báo cáo Nghiên cứu `tose.sh`](../research_and_studies/research-tose-sh-public-architecture.md)  
> **Grok Audit Trail (`ADR-0067`):** Pass 1 `7e0dd009-3c73-4773-9ff9-b5c311dbb7e3` (`REVISE_PLAN`, `risk_score: 4`, `5` blocking) $\to$ Pass 2 `9c6bcf35-3738-497d-b827-fd8cff1bbeda` (**`APPROVE_PLAN`**, `risk_score: 2`, `0` blocking, biên bản `.md/peer_exchange/grok_harness_agent_envelope_plan_signoff_p2.md`)  
> **Trạng thái:** `IMPLEMENTED_VERIFIED` (Đã thi công xong & vượt qua toàn bộ cổng kiểm định tất định `ADR-0058` / `ADR-0061` / `ADR-0067`)  
> **Biên lai Đối soát Seam (`ADR-0061`):** `compile_catalog.py --in markdown --out markdown --json` $\to$ `status: NO_MATCH`, `index_sha256: fe4c3c11ca879eba54a8790ade072dbd98022f26bb1393585dee90149dddacfc` — tái sử dụng trực tiếp `SelfHealingEngine.diagnose_failures()` & `generate_remediation_actions()` ([healing.py](../../../packages/ccba-harness/src/ccba_harness/healing.py#L174-L364)) và `validate_tradeoff_card()` ([backpressure.py](../../../packages/ccba-harness/src/ccba_harness/backpressure.py#L124-L155)).

---

## 1. Giải Trình Điều Kiện Thẩm Định Pass 1 (`7e0dd009-3c73-4773-9ff9-b5c311dbb7e3`)

| Mã Điều kiện | Phân loại | Dẫn chứng Mã nguồn (`file:line`) | Cơ chế Khắc phục trong Kế hoạch `v1.1` |
| :--- | :---: | :--- | :--- |
| **`COND-HEAL-SSOT`** | `[ADOPT_AS_IS]` | [verifier.py](../../../packages/ccba-harness/src/ccba_harness/cli/commands/verifier.py#L121-L142), [verifier.py](../../../packages/ccba-harness/src/ccba_harness/cli/commands/verifier.py#L266-L277), [healing.py](../../../packages/ccba-harness/src/ccba_harness/healing.py#L87-L99) | Thân JSON & `--report-file *.json` serialize `active.to_dict()` (`HealingReport` khi `--self-heal` chạy, giữ nguyên `final_verification_report` lồng nhau không chèn phong bì); 4 khóa phong bì chỉ gắn ở **cấp 1**. `status`, `error`, `timed_out`, `next_actions` và exit code đọc từ **`report` sau dòng `275–276`**. Nếu `report.all_passed` là `True`, luôn trả `status="ok"`, `error=None`, `next_actions=[]` kể cả khi `diagnosed_issues` khác rỗng. `to_markdown()` giữ nguyên 100%. |
| **`COND-NEXT-ACTIONS`** | `[ADOPT_AS_IS]` | [healing.py](../../../packages/ccba-harness/src/ccba_harness/healing.py#L174-L233), [healing.py](../../../packages/ccba-harness/src/ccba_harness/healing.py#L308-L364), [healing.py](../../../packages/ccba-harness/src/ccba_harness/healing.py#L439), [verifier.py (domain)](../../../packages/ccba-harness/src/ccba_harness/verifier.py#L192-L200) | Bỏ hoàn toàn bảng lệnh song song `.venv/bin/ruff`. Khi `not report.all_passed`: (1) kiểm tra `any(r.timed_out for r in report.results)` trước $\to$ `COMMAND_TIMEOUT`, `retryable=True`, semantic exit `124`; (2) gọi `SelfHealingEngine.diagnose_failures(report)` rồi `generate_remediation_actions(issues)` để phát lệnh chuẩn (`python -m ruff format/check --fix`, `python scripts/...`); (3) nếu danh sách action rỗng (vd: `TEST_ASSERTION`, `UNKNOWN`, hoặc regex trượt/`continue`) mà `not report.all_passed`, sinh `next_action` fallback chạy lại chính `command` đầu tiên thất bại. |
| **`COND-ARGPARSE-EXIT`** | `[ADOPT_AS_IS]` | [verifier.py](../../../packages/ccba-harness/src/ccba_harness/cli/commands/verifier.py#L52-L57), [verifier.py](../../../packages/ccba-harness/src/ccba_harness/cli/commands/verifier.py#L94-L97), [verifier.py](../../../packages/ccba-harness/src/ccba_harness/cli/commands/verifier.py#L116-L117), [verifier.py](../../../packages/ccba-harness/src/ccba_harness/cli/commands/verifier.py#L262-L264), [test_cli_contract_parity.py](../../../packages/ccba-harness/tests/test_cli_contract_parity.py#L53-L61) | Tách rạch ròi 3 đường lỗi: (1) `verify-patch` không lệnh/preset và `ValueError` giữ `return 1` + `stderr` nguyên văn khi **không** có `--json` (`--report-file` không tạo file); (2) `verify-doc --target` giữ `required=True` và cờ lạ giữ `SystemExit(2)` của `argparse` khi **không** có `--json`; (3) `--help` (kể cả `--json --help`) luôn in help và giữ `SystemExit(0)`. Chỉ khi flag `--json` được parse thật bằng pre-parser `parse_known_args` (hỗ trợ `--`, không dùng substring `"--json" in args_list`), tắt `stderr`/`print(result.stdout)` thừa và in **duy nhất 1 JSON** (`INVALID_INPUT` $\to$ exit `2` khi `--semantic-exit-codes` hoặc `argparse` code `2`, `1` trên `verify-patch` mặc định). |
| **`COND-DOOR-MATRIX`** | `[ADOPT_AS_IS]` | [architecture.py](../../../packages/ccba-harness/src/ccba_harness/cli/commands/architecture.py#L83-L117), [backpressure.py](../../../packages/ccba-harness/src/ccba_harness/backpressure.py#L124-L155), [door_policy.py](../../../packages/ccba-harness/src/ccba_harness/door_policy.py#L364-L382) | Vá lỗ hổng fail-open tại `architecture.py:97-117` và khóa cứng ma trận 5 trường hợp (Mục 2.3) ở cả kế hoạch lẫn `test_agent_envelope.py`. Xử lý cả thiếu `--pr-body-file`, tệp không tồn tại, hoặc `OSError` khi đọc; `sampled_for_audit` không bao giờ ánh xạ sang exit `4`; `TRADEOFF_CARD_INVALID` chỉ kích hoạt khi bật `--enforce-tradeoff-card`. |
| **`COND-THIN-CLI`** | `[ADOPT_AS_IS]` | [peer_gate.py](../../../packages/ccba-harness/src/ccba_harness/peer_gate.py#L254-L280), [verifier.py](../../../packages/ccba-harness/src/ccba_harness/cli/commands/verifier.py#L239-L277), [verify-ccba-harness/SKILL.md](../../../packages/ccba-harness/.agents/skills/verify-ccba-harness/SKILL.md#L21-L42) | `run_verify_patch_cli` hiện dài **39/40 dòng** sau `parse_args`. Vì vậy rút toàn bộ logic hậu parse của `run_verify_patch_cli` và `run_verify_doc_cli` sang helper private (`<= 45` LOC/hàm) + module `cli/_envelope.py` ($\le 120$ LOC, mỗi hàm $\le 50$ LOC), giữ thân sau `parse_args` chỉ `<= 15` dòng. Không thêm symbol vào `ccba_harness.__all__`, không chạm `cli/core.py`, `verifier.py`, `door_policy.py`. |
| **`COND-CATALOG-CLI-LINE`** | `[ADOPT_AS_IS]` | [packages/ccba-harness/AGENTS.md](../../../packages/ccba-harness/AGENTS.md#L6), [compile_catalog.py](../../../scripts/governance/compile_catalog.py#L175-L235) | Chỉ sửa dòng `- **CLI Commands**:` trong `packages/ccba-harness/AGENTS.md` (không sửa `Public Deep Seams`). Nếu `compile_catalog.py --check` báo lệch chỉ vì synopsis, cập nhật `.agents/skills/platform-loader/catalog.yaml` trong cùng PR và ghi rõ không có `__all__` churn. |

---

## 2. Đặc Tả Hợp Đồng Giao Diện Chuẩn Hóa (`v1.1`)

### 2.1. Additive Flat JSON Envelope (`verify-patch`, `verify-doc`, `door-triage` & `--report-file *.json`)

- Giữ nguyên 100% các khóa gốc ở cấp 1 của từng lệnh (`active.to_dict()` với `verify-patch`, `result.to_dict()` với `verify-doc`, payload gốc với `door-triage`).
- Không gắn khóa phong bì vào `final_verification_report` lồng bên trong `HealingReport.to_dict()`.
- Luôn gắn đúng **4 khóa chuẩn ở cấp 1**:
  - `"schema_version"`: `"1"`
  - `"status"`: `"ok" | "error" | "approval_required"`
  - `"error"`: `{"code": str, "message": str, "retryable": bool} | None`
  - `"next_actions"`: `list[{"command": str, "description": str}]`
- Khi `verify-doc --json` thành công, không gọi `print(result.stdout)` thô trước khi in JSON — chỉ phát **duy nhất 1 tài liệu JSON** ra `stdout`.

### 2.2. Luồng Phân Loại Lỗi, `next_actions` & 3 Đường `INVALID_INPUT`

1. **`verify-patch` (`report` lấy từ sau `verifier.py:275-276`, không dùng `active` để đánh giá trạng thái):**
   - `report.all_passed == True` $\to$ `status="ok"`, `error=None`, `next_actions=[]`, exit `0`.
   - `any(r.timed_out for r in report.results)` $\to$ `error.code="COMMAND_TIMEOUT"`, `retryable=True`, semantic exit `124` (mặc định `1`); `next_actions` gợi ý chạy lại lệnh timeout với `--timeout` lớn hơn, cộng thêm remediation actions từ `SelfHealingEngine` nếu có lỗi non-timeout khác.
   - Ngược lại (`not report.all_passed`) $\to$ `error.code="CHECKS_FAILED"`, `retryable=False`, exit `1`. Gọi `SelfHealingEngine(base_dir).diagnose_failures(report)` $\to$ `generate_remediation_actions(issues)` để tạo `next_actions` (dùng đúng lệnh `python -m ruff ...` / `python scripts/...` của engine). Nếu `actions` rỗng (do `TEST_ASSERTION`, `UNKNOWN`, hoặc regex trượt/`continue`), tự sinh `next_action` chạy lại đúng lệnh thất bại đầu tiên.
2. **`verify-doc` (`enrich_doc_result_dict` — `COND-DOC-FAIL-SPEC`):**
   - `result.passed == True` $\to$ `status="ok"`, `error=None`, `next_actions=[]`, exit `0`; khi `--json`, không gọi `print(result.stdout)` thô trước khi in JSON.
   - `result.passed == False` (lỗi kiểm định file/size/headings, không phải lỗi `argparse`) $\to$ `status="error"`, `error={"code": "CHECKS_FAILED", "message": ..., "retryable": False}`, exit `1` ở cả hai chế độ mã thoát, `next_actions` gợi ý một lệnh `verify-doc` chạy lại kèm `--min-bytes` / `--required-headings` sau khi sửa tệp mục tiêu.
3. **3 đường `INVALID_INPUT` (tách biệt theo `COND-ARGPARSE-EXIT`):**
   - **Đường A (`verify-patch` không commands/preset hoặc `ValueError`):** Không có `--json` $\to$ `return 1` + `stderr` nguyên văn (`--report-file` không ghi file). Có `--json` $\to$ tắt `stderr`, in JSON `INVALID_INPUT` ra `stdout`, trả `2` nếu `--semantic-exit-codes` else `1`.
   - **Đường B (`verify-doc` thiếu `--target` hoặc cờ lạ trên 3 lệnh):** Không có `--json` $\to$ giữ `SystemExit(2)` nguyên thủy của `argparse`. Có `--json` (nhận diện qua pre-parser `parse_known_args` với `add_help=False` tôn trọng `--` và token giá trị của `--cmd`/`--commands`) $\to$ tắt `stderr`, in JSON `INVALID_INPUT` ra `stdout` và thoát mã `2`.
   - **Đường C (`--help` / `-h`, kể cả `--json --help`):** Luôn in help và giữ nguyên `SystemExit(0)`.

### 2.3. Ma Trận Đầy Đủ Cho `door-triage` (`COND-DOOR-MATRIX`)

| `door_type` | `--enforce-tradeoff-card` | Trạng thái `--pr-body-file` | `tradeoff_card_valid` | `status` | `error.code` | Exit mặc định | Exit `--semantic-exit-codes` |
| :--- | :---: | :--- | :---: | :--- | :--- | :---: | :---: |
| `TWO_WAY_DOOR` / `PAVED_ROAD` | Tắt / Bật | Bất kỳ (thiếu hoặc có) | `true` | `"ok"` | `null` | `0` | `0` |
| `ONE_WAY_DOOR` | **Tắt** | Thiếu / Không tồn tại / `OSError` | `true` *(giữ cũ)* | `"approval_required"` | `"HUMAN_APPROVAL_REQUIRED"` | `0` | `4` |
| `ONE_WAY_DOOR` | **Tắt** | Tồn tại, Card **invalid** | `false` *(giữ cũ)* | `"approval_required"` | `"HUMAN_APPROVAL_REQUIRED"` | `0` | `4` |
| `ONE_WAY_DOOR` | **Bật** | Thiếu / Không tồn tại / `OSError` / Card **invalid** | `false` *(fail-closed)* | `"error"` | `"TRADEOFF_CARD_INVALID"` | `1` | `1` |
| `ONE_WAY_DOOR` | **Bật** | Tồn tại, Card **hợp lệ** | `true` | `"approval_required"` | `"HUMAN_APPROVAL_REQUIRED"` | `0` | `4` |

*(Ghi chú: `sampled_for_audit` không bao giờ ánh xạ sang exit `4`; `TRADEOFF_CARD_INVALID` chỉ phát sinh khi `--enforce-tradeoff-card` được bật.)*

---

## 3. Kế Hoạch Thay Đổi Tệp & Kiểm Thử TDD

| Hành động | Tệp đích | Thiết kế Tuân thủ Trần AST (`peer_gate.py`) |
| :---: | :--- | :--- |
| `[NEW]` | `packages/ccba-harness/src/ccba_harness/cli/_envelope.py` | $\le 120$ LOC, mỗi hàm $\le 50$ LOC, strict `mypy`: `parse_with_json_envelope`, `enrich_patch_report_dict`, `enrich_doc_result_dict`, `enrich_door_triage_dict`, `build_invalid_input_envelope`, `resolve_exit_code`. Không đưa vào `ccba_harness.__all__`. |
| `[MODIFY]` | [cli/commands/verifier.py](../../../packages/ccba-harness/src/ccba_harness/cli/commands/verifier.py) | Thân sau `parse_args` của `run_verify_doc_cli` và `run_verify_patch_cli` $\le 15$ dòng (trần `40`); tách helper private $\le 45$ dòng cho mỗi luồng xử lý, đồng bộ `--report-file *.json` với `--json` trên `stdout`. |
| `[MODIFY]` | [cli/commands/architecture.py](../../../packages/ccba-harness/src/ccba_harness/cli/commands/architecture.py) | `_execute_door_triage` ($\le 45$ dòng, trần `50`) dùng helper đọc `pr_body_file` fail-closed khi `enforce_tradeoff_card` bật trên `ONE_WAY_DOOR`, gắn `enrich_door_triage_dict`, thêm `--semantic-exit-codes`. |
| `[MODIFY]` | [packages/ccba-harness/AGENTS.md](../../../packages/ccba-harness/AGENTS.md) | Cập nhật dòng `- **CLI Commands**:` (đồng bộ `catalog.yaml` nếu `compile_catalog.py --check` báo drift synopsis). |
| `[NEW]` | `packages/ccba-harness/tests/test_agent_envelope.py` | Unit tests `pytest.mark.fast`: kiểm đủ `HealingReport` sau `--self-heal` (`status=ok` dù `diagnosed_issues != []`, `final_verification_report` không bị chèn phong bì), ca `any(r.timed_out)` trên `report.results` (`COMMAND_TIMEOUT`, `retryable=True`, semantic exit `124`, mặc định `1`, kể cả khi `diagnose_failures` trả `[]` — `COND-TIMEOUT-TEST`), `next_actions` từ `SelfHealingEngine` & fallback, `verify-doc --json` pass & `CHECKS_FAILED`, 3 đường `INVALID_INPUT` & `--json --help`, trọn bộ ma trận 5 trạng thái `door-triage` (kể cả `OSError`, đọc `--pr-body-file` chỉ khi `ONE_WAY_DOOR`), và `--report-file *.json` parity. |

---

## 4. Tradeoff Card (`ADR-0067 — PUBLIC_API_SEAM`)

### Tradeoff Card (ADR-0067 — PUBLIC_API_SEAM)
- **Core Invariant**: Bảo toàn 100% khóa JSON gốc (`active.to_dict()` cho `verify-patch`, `result.to_dict()` cho `verify-doc`, payload gốc cho `door-triage`) và mã thoát mặc định (`0`/`1`/`SystemExit(2)`), tách bạch kiểm tra `report.all_passed` sau `--self-heal`, khóa fail-closed khi `--enforce-tradeoff-card` thiếu hoặc lỗi đọc `--pr-body-file`, và không chạm bất kỳ `covered_paths` nào của `verify-ccba-harness/SKILL.md`.
- **Invalidation Condition**: Kế hoạch bị vô hiệu nếu việc gắn 4 khóa phong bì cấp 1 làm gãy bất kỳ caller nào đọc JSON, nếu thân sau `parse_args` vượt `40` dòng (`peer_gate.py:257`), hoặc nếu tổng logic diff vượt trần `200 LOC`.
- **Git Hunk Reference**: `packages/ccba-harness/src/ccba_harness/cli/commands/verifier.py#L121-L143`

---

## 5. Kết Quả Triển Khai & Kiểm Định Thực Tế (`ADR-0058`)

- **Tệp đã tạo / cập nhật `[đo thực tế]`:**
  - [\_envelope.py](../../../packages/ccba-harness/src/ccba_harness/cli/_envelope.py): `120` dòng (đạt trần $\le 120$ LOC sau `ruff format`).
  - [cli/commands/verifier.py](../../../packages/ccba-harness/src/ccba_harness/cli/commands/verifier.py): `333` dòng.
  - [cli/commands/architecture.py](../../../packages/ccba-harness/src/ccba_harness/cli/commands/architecture.py): `172` dòng.
  - [packages/ccba-harness/AGENTS.md](../../../packages/ccba-harness/AGENTS.md): cập nhật dòng `- **CLI Commands**:`, giữ nguyên `Public Deep Seams` và `ccba_harness.__all__`.
  - [test_agent_envelope.py](../../../packages/ccba-harness/tests/test_agent_envelope.py): `373` dòng, `15` test cases TDD (`pytest.mark.fast`).
- **Biên lai kiểm định sau lần chỉnh sửa mã nguồn cuối `[đo thực tế]`:**
  - `.venv/bin/ruff format --check` & `.venv/bin/ruff check packages/ccba-harness/`: exit `0` (`All checks passed!`).
  - `.venv/bin/python -m mypy --strict --follow-imports=silent packages/ccba-harness/src`: exit `0` (`no issues found in 94 source files`).
  - `.venv/bin/python -m pytest packages/ccba-harness/tests/test_agent_envelope.py packages/ccba-harness/tests/test_verify_patch.py packages/ccba-harness/tests/test_cli_contract_parity.py packages/ccba-harness/tests/test_door_policy.py tests/governance/test_self_healing_engine.py -q`: exit `0` (`96 passed in 4.00s`).
  - `.venv/bin/python -m ccba_harness verify-patch --preset code --target packages/ccba-harness`: exit `0` (**`4/4 passed`** trong `10840.9 ms`, gồm toàn bộ `pytest packages/ccba-harness/tests -q`).
  - `check_ast_function_length` trên `_envelope.py`, `verifier.py`, `architecture.py`: exit `0` (`passed=True`, `<= 50` LOC / post-parse `<= 40` LOC).
  - `.venv/bin/python scripts/governance/compile_catalog.py --check`: exit `0` (`catalog.yaml` in-sync `100%`).
  - `.venv/bin/python scripts/governance/check_dependency_contracts.py`: exit `0` (`518 Python source files` sạch 100%).
  - Đối soát `covered_sha256` trong [verify-ccba-harness/SKILL.md](../../../packages/ccba-harness/.agents/skills/verify-ccba-harness/SKILL.md): tất cả `8/8` tệp khớp SHA-256 nguyên vẹn.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
