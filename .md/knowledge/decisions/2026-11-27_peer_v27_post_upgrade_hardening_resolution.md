# Biên Bản Phỏng Vấn Grilling & Kế Hoạch Triển Khai `v2.7.1`: Hardening Cơ Chế Phối Hợp Peer Hậu Kiểm Toán `75` Lượt Thực Tế

> **Ngày chốt Grilling:** `2026-11-27` | **Baseline Hub:** `main` @ `c3c3e3fb` | **Trạng thái:** `PR-1 MERGED (#931 @ bd8f4c50) — PR-2 IN_PROGRESS`  
> **Biên lai Đối soát Seam ([ADR-0061](../../../docs/adr/0061-platform-aware-kiss-v2-and-quarantine-governance.md)):**
> - `.venv/bin/python scripts/ccba_platform_cli.py find-seam --in markdown,yaml --out json,report --json` $\rightarrow$ `status: "NO_MATCH"` (`count: 0`, `index_sha256: 29d4ee1aa2efb369ce154585cd65e1c44ec31efed8ec4096a8f603b8944b6c49`)
> - Sửa trực tiếp trên các Seam và script hiện hữu: [`_peer_models.py`](../../../packages/ccba-harness/src/ccba_harness/_peer_models.py), [`_peer_watchdog.py`](../../../packages/ccba-harness/src/ccba_harness/_peer_watchdog.py), [`audit_pr_comments.py`](../../../scripts/validation/audit_pr_comments.py), [`audit_peer_effectiveness.py`](../../../scripts/governance/audit_peer_effectiveness.py) (tách helper nội bộ `_peer_yaml.py`, `0` Public Seam mới).
> **Impact-Based Handoff Gate ([ADR-0067](../../../docs/adr/0067-one-way-door-manifest-and-backpressure-circuit-breaker.md)):** `ONE_WAY_DOOR` (`PR-1`: Public Seam `ccba_harness.peer`; `PR-2`: `HUB_CONSTITUTION` + governance scripts) $\rightarrow$ đã vượt qua **Grok Peer Plan Audit (`2` vòng, `APPROVE_PLAN`, `risk_score: 2`, `blocking_conditions: 0`)**; dừng chờ lệnh `proceed` của người dùng trước khi sửa mã sản xuất.

---

## 1. Bước 0 — Mài Sắc Bài Toán & Bằng Chứng Thực Nghiệm (`2026-11-25 07:08` → `2026-11-27 21:00`)

1. **Mục tiêu thực chất (`in-your-own-words`):** Đóng dứt điểm **4 lỗ hổng vận hành thật** lộ ra sau `75` lượt thực thi hậu-`v2.6`/`v2.7` trên Hub & 6 Spokes (`196/196` tests PASS, chi phí/chuỗi giảm `33.9%`, `blocking: true` giảm `-19.8pp`, `0` tệp nháp `.md/peer_exchange/` bị Git track trên 7/7 repos): (1) khử *False Green* khi CodeRabbit bỏ qua review PR trên repo `< 10★`, (2) chống rớt phán quyết `grok-4.7` đã hoàn tất do `yaml.safe_load` gặp `ScannerError`, (3) nâng trần `code_review` vượt `450s` theo đúng *Invalidation Condition* `PR #902` và khóa ngưỡng `audit_direct`, (4) chuẩn hóa baseline `v2.5` & nối chuỗi Pass 2+ trong `audit_peer_effectiveness.py`.
2. **Dữ kiện gốc kiểm chứng trực tiếp (`[đo thực tế]` / `[phân tích log]` / `[GitHub API]`):**
   - **False Green CodeRabbit (`Q1`):** `9/9` PR Hub gần nhất (`#914`, `#915`, `#919`, `#920`, `#921`, `#922`, `#924`, `#926`, `#929`) đều chỉ có 1 comment skip-review (`reviews=0`, `inline=0`, `walkthrough=0`) mang đồng thời `auto-generated comment: summarize by coderabbit.ai` và `auto-generated comment: skip review by coderabbit.ai`. [`audit_pr_comments.py`](../../../scripts/validation/audit_pr_comments.py#L243-L247) & [`:325-329`](../../../scripts/validation/audit_pr_comments.py#L325-L329) đếm `prc_cnt = 1` nên trả `CLEAN (exit 0)` thay vì `NO_AI_REVIEW`.
   - **YAML `ScannerError` trên phán quyết hoàn tất (`Q2`):** Quét toàn bộ `~/.grok/sessions/*/chat_history.jsonl` bắt `3` phiên hoàn tất bị rớt parse: `12f4dfd4-bcf5` (`IBST_UNIFIED_ERP`, `511s` `APPROVE`, unquoted `ws: wss:` trong `description:`), `deac9dd6-1c1` (`- COND-06: ...: ...`), và `c6d7e142-4cb` (`- "Condition ... r'\[\[' ... \le ..."`). [`_peer_models.py`](../../../packages/ccba-harness/src/ccba_harness/_peer_models.py) hiện **`788 / 800` LOC** (`12` dòng headroom trước trần cứng `RULE-2.20`); [`_peer_models.py:471-486`](../../../packages/ccba-harness/src/ccba_harness/_peer_models.py#L471-L486) đã có `_normalize_conditions` (`mode="before"`) chuẩn hóa cả `str` và `dict` 1 khóa.
   - **`code_review` vượt trần `450s` (`Q3`):** `11/11` lượt hậu-`v2.6` chạm `max_turns_reached` (`8`t), `6/11` vượt `450s` (`med = 515.1s`, `max = 853.89s`), `1/11` (`ef03da75`) chạm timeout thật tại `495.2s` (`450s + 45s` grace) gây fallback `grok-4.7-build-fast` (`+515s`, `\$0.4694`); tỷ lệ bắt lỗi chặn tăng `0/6 -> 2/11`. `audit_direct` (`120s`, `--no-tools`) hiện `0/75` lượt.
   - **Đo lường `audit_peer_effectiveness.py` (`Q4`):** `pre_v26` trộn `226` lượt trước `2026-11-11` (`98.1s`) với `151` lượt `v2.5` (`506.1s`); `6/34` (`17.6%`) lượt Pass 2+ nối phiên qua CLI `--resume` thiếu `env.resume_session_id` bị tách chuỗi.
3. **Kiểm chứng độc lập bên ngoài (*outside checks*):**
   - `audit_pr_comments.py --repo vvChu/ccba-agent-platform --pr 929` $\to$ `[WARN] NO_AI_REVIEW` (`exit 0`), `--require-review` $\to$ `exit 3`.
   - Replay end-to-end `parse_verdict_from_md()` lên đúng `3` payload `ScannerError` thực tế + block scalar `|`/`>` + `bad_yaml` fail-closed.
   - Chạy `audit_peer_effectiveness.py` trên `6` repos với baseline `2026-11-11`, `wc -c docs/rules/execution_coordination_guardrails.md <= 24,576`, và `verify-patch --preset code`.

---

## 2. Bảng Chốt `5/5` Quyết Định Thiết Kế (`Q1`–`Q5`)

| Mã | Chủ đề Frontier | Quyết định đã khóa & Ràng buộc thực thi | Căn cứ |
| :---: | :--- | :--- | :--- |
| **`Q1`** | **False Green CodeRabbit `< 10★`** | Giữ [`audit_pr_comments.py`](../../../scripts/validation/audit_pr_comments.py) **100% Read-Only**; không cộng comment `skip review by coderabbit.ai` (không có `walkthrough_start` & không có `Actionable>=1`) vào `effective_prc_cnt` để trả đúng `NO_AI_REVIEW` (`exit 0` mặc định, `exit 3` với `--require-review`) kèm gợi ý `@coderabbitai review` khi thấy skip-review marker; chỉ gọi `@coderabbitai review` có chọn lọc trên PR lõi. | Triệt tiêu False Green trên `9/9` PR Hub mà không vi phạm hạn mức `1 review/giờ` hay biến tool kiểm toán thành tool ghi. |
| **`Q2`** | **YAML Recovery & trần `800` LOC** | Tách helper nội bộ `_peer_yaml.py` (`<= 120` LOC, hàm `<= 50` LOC, `0` Public Seam mới) để `_peer_models.py` giữ `789 <= 800` LOC; áp dụng **strict-first & fail-closed** xử lý cả 2 lớp lỗi đã chứng minh (`: ` trong scalar 1 dòng không bọc nháy với bộ theo dõi block scalar `|`/`>`, và escape `\` lạ trong chuỗi `"..."` giữ nguyên bảng escape PyYAML + hex chạy đầy đủ), cộng thêm 1 câu nhắc quote YAML trong `AUDIT_BASE_SYSTEM_PROMPT` & `SYNTHESIS_FALLBACK_PROMPT`. | Cứu `3/3` ca `ScannerError` thực tế (`511s` audit `grok-4.7`) trong khi giữ nguyên `bad_yaml -> None` và KV-Cache prefix. |
| **`Q3`** | **`code_review` `600s` & `audit_direct`** | Nâng `PROFILE_SPECS["code_review"]["timeout"]`: `450.0 -> 600.0` (giữ `grok-4.7`, `high`, `max_turns=8`, fallback `grok-4.7-build-fast`); bổ sung ngưỡng ưu tiên `audit_direct` (`120s`, `--no-tools`) cho diff khép kín `<= 100 LOC` & `<= 3` tệp trong `PEER_HANDSHAKE.md`, `README.md`, `execution_coordination_guardrails.md`. | Đáp ứng *Invalidation Condition* `PR #902`, chặn timeout cắt ngang Pha 1 (`495s`) và tận dụng `audit_direct` cho diff nhỏ. |
| **`Q4`** | **Baseline `v2.5` & Ghép chuỗi Pass 2+** | Thêm `--baseline-since` (CLI mặc định `"2026-11-11T00:00:00+07:00"`, nhận `"all"`, Python API mặc định `None`, ném `ValueError` khi sai định dạng) xuất `pre_baseline_excluded: int` & `baseline_since_utc: str \| None`; mirror chuẩn predicate ghép chuỗi của `_peer_telemetry.py` nội bộ trong `audit_peer_effectiveness.py` (cùng `exchange_dir`, `0 < delta <= 43_200`, chặn `Plan -> Code`, `None`-safe opt-out `new\|none\|false\|0`), xuất `inferred_chain_links: int`. | Chấm dứt Simpson's Paradox (`98.1s` vs `506.1s`) và khôi phục `6/34` chuỗi Pass 2+ nối phiên qua CLI. |
| **`Q5`** | **Đóng gói `2` Atomic Micro-PRs & Phase 3** | Tách `PR-1` (`ccba-harness` Core: `Q2 + Q3`) và `PR-2` (`scripts/` + Guardrails Docs: `Q1 + Q4 + Q3 docs`), mỗi PR `<= 80 LOC` logic & 1 danh mục cửa `ONE_WAY_DOOR`; hậu merge `PR-2` chạy `CCBA_SKIP_GIT_PULL=1 .venv/bin/python scripts/sync_spoke.py --all --dry-run` $\to$ `--all --apply` xuống 6 Spokes (không `git push` Spokes, giữ nguyên nhánh local `ccba-legal-knowledge`). | Tuân thủ `ADR-0067` (`<= 200` LOC diff, `<= 1` Public Seam/PR), dễ kiểm soát và rollback độc lập. |

---

## 3. Thẩm Định Độc Lập Ngang Hàng (`Grok Peer Plan Audit — ADR-0067`)

| Vòng | Profile | Session ID | Phán quyết | Risk | Blocking | Chi phí / Thời gian / KV-Cache | Tóm tắt Kết quả |
| :---: | :--- | :--- | :---: | :-: | :-: | :---: | :--- |
| **Pass 1** | `audit_plan` | `1d5b5afb-e210-4c36-829e-a6ec12d4677c` | `REVISE_PLAN` | `4` | `2` | `\$0.2286` / `724.16s` / `84.7%` | Xác nhận `Q1` & `Q3` khớp mã nguồn; bắt chính xác `2` lỗi chặn ở kế hoạch ban đầu: nguy cơ sửa nhầm dòng trong block scalar `|`/`>` (`COND-YAML-01`) và lỗi `None`-crash + lệch predicate ghép pha ở `audit_peer_effectiveness.py` (`COND-CHAIN-02`). |
| **Pass 2** | `signoff_diff` | `a986055b-9822-4732-8ac9-afd524e29e8c` | **`APPROVE_PLAN`** | `2` | **`0`** | `\$0.1505` / `252.44s` / `94.2%` | Khép sạch `COND-YAML-01` & `COND-CHAIN-02` đối chứng trực tiếp codebase; thêm `1` lưu ý triển khai `COND-PORT-05` (`blocking: false`). |

### Ma trận Phân loại Điều kiện (§20.3 3-Label Triage Matrix)

| ID | Vòng | Phân loại | Đối chứng mã nguồn (`file:line`) & Quyết định Áp dụng |
| :--- | :---: | :--- | :--- |
| `COND-YAML-01` | Pass 1 *(blocking)* | `[ADOPT_ADAPTED]` | Bổ sung bộ theo dõi block scalar `|`/`>` (`block_parent_indent`) trong `_peer_yaml.py` (`<= 120` LOC, hàm `<= 50` LOC) để không bao giờ sửa nội dung khối; giữ bảng escape PyYAML `frozenset('0abtnvfre "/\\N_LPxuU')` (giữ `\x41`/`\u0041` hợp lệ, fail-closed `\xZZ`/`\u00Z`); đối chứng [`_peer_models.py:471-486`](../../../packages/ccba-harness/src/ccba_harness/_peer_models.py#L471-L486) (`_normalize_conditions` đã xử lý `str` và `dict` 1 khóa) và bắt buộc test end-to-end qua `parse_verdict_from_md()` cho cả 3 fixture `ScannerError`. |
| `COND-CHAIN-02` | Pass 1 *(blocking)* | `[ADOPT_AS_IS]` | Copy nguyên predicate runtime từ [`_peer_telemetry.py`](../../../packages/ccba-harness/src/ccba_harness/_peer_telemetry.py#L35-L43), [`:390-402`](../../../packages/ccba-harness/src/ccba_harness/_peer_telemetry.py#L390-L402), [`:495-529`](../../../packages/ccba-harness/src/ccba_harness/_peer_telemetry.py#L495-L529), [`:547-555`](../../../packages/ccba-harness/src/ccba_harness/_peer_telemetry.py#L547-L555) vào `audit_peer_effectiveness.py` (`<= 620` LOC, `0` import `ccba_harness._*`); `None`-safe opt-out `{new, none, false, 0}`; join thêm `profile` & `request_type` tại [`:170-178`](../../../scripts/governance/audit_peer_effectiveness.py#L170-L178); cửa sổ `0 < delta <= 43_200`, cùng `exchange_dir`, khác `request_id`/`session_id`, bỏ bản ghi `ts is None`; chủ động `raise ValueError` khi `--baseline-since` sai định dạng; xuất `pre_baseline_excluded: int`, `inferred_chain_links: int`, `baseline_since_utc: str \| None` giữ `json.dumps` an toàn. |
| `COND-CR-03` | Pass 1 | `[ADOPT_AS_IS]` | Loại trừ comment thỏa `_is_coderabbit_skip_review_comment()` khỏi `effective_prc_cnt` tại [`audit_pr_comments.py:313-329`](../../../scripts/validation/audit_pr_comments.py#L313-L329); khóa gợi ý `@coderabbitai review` (`< 10 stars`) theo cờ boolean `has_skipped_review` đọc từ mảng `comments` (không gọi API stars); giữ `parse_cli_args()` 2-tuple (`:102-105`), `walkthrough_start -> CLEAN`, command-ack `-> CLEAN`, `Actionable >= 1 -> CHANGES_RECOMMENDED`. |
| `COND-Q3-04` | Pass 1 | `[ADOPT_AS_IS]` | Đổi `450.0 -> 600.0` tại [`_peer_watchdog.py:219`](../../../packages/ccba-harness/src/ccba_harness/_peer_watchdog.py#L219), [`test_peer.py:956`](../../../packages/ccba-harness/tests/test_peer.py#L956), [`execution_coordination_guardrails.md:139`](../../../docs/rules/execution_coordination_guardrails.md#L139), `PEER_HANDSHAKE.md:58`, `README.md:44`; giữ 1 object `AUDIT_BASE_SYSTEM_PROMPT`; ghi nhận cả tỷ lệ timeout Pha 1 lẫn tỷ lệ chạm `max_turns_reached` ở 8 turns vào *Invalidation Condition* `PR-1`; giữ `wc -c execution_coordination_guardrails.md <= 24,576`. |
| `COND-PORT-05` | Pass 2 | `[ADOPT_AS_IS]` | Khi port predicate ghép chuỗi vào `audit_peer_effectiveness.py`, đọc đúng dict keys (`rec["profile"]`, `rec["request_type"]`, `rec["verdict"]`, `rec["request_id"]`, `rec["file_name"]`, `rec["session_id"]`) thay vì `getattr`; giữ tách biệt file-stem equality (`:547`) và request-stem containment `min_len >= 8` (`:549-555`); `is_pass2_plus` loại cả `{new, none, false, 0}`; chỉ copy `session_id` cha không rỗng. |

---

## 4. Kế Hoạch Triển Khai Chi Tiết (`Implementation Plan` — Chờ Lệnh `proceed`)

### 4.1. `PR-1` — `ccba-harness` Core (`Q2 + Q3`, `ONE_WAY_DOOR`: Public Seam `ccba_harness.peer`, Tradeoff Card)
1. **Tạo `packages/ccba-harness/src/ccba_harness/_peer_yaml.py` (`<= 120` LOC, hàm `<= 50` LOC):**
   - `safe_load_frontmatter_yaml(raw_yaml: str) -> Any`: strict `yaml.safe_load` trước; khi `yaml.YAMLError`, chạy `_repair_frontmatter_yaml_lines()` (theo dõi block scalar `|`/`>`, Lớp A bọc `json.dumps` cho plain scalar 1 dòng có `: `, Lớp B escape `\` ngoài `0abtnvfre "/\N_LPxuU` trong `"..."` 1 dòng), nếu `repaired == raw_yaml` hoặc parse lần 2 vẫn lỗi $\to$ trả `None` (fail-closed).
2. **Sửa [`packages/ccba-harness/src/ccba_harness/_peer_models.py`](../../../packages/ccba-harness/src/ccba_harness/_peer_models.py) (`788 -> 789 <= 800` LOC):**
   - Import `safe_load_frontmatter_yaml` từ `._peer_yaml`; thay `yaml.safe_load(match.group(1))` tại `L548`, `L558`, `L568` (giữ `import yaml` cho `yaml.dump` ở `L752`, `L766`).
3. **Sửa [`packages/ccba-harness/src/ccba_harness/_peer_watchdog.py`](../../../packages/ccba-harness/src/ccba_harness/_peer_watchdog.py) (`693 -> ~697 <= 800` LOC):**
   - `L219`: `PROFILE_SPECS["code_review"]["timeout"] = 600.0`.
   - `L136-155`: thêm 1 mệnh đề nhắc quote YAML chứa `: ` hoặc `\` vào `AUDIT_BASE_SYSTEM_PROMPT` (1 object duy nhất) và `SYNTHESIS_FALLBACK_PROMPT`.
4. **Tests ([`packages/ccba-harness/tests/test_peer.py`](../../../packages/ccba-harness/tests/test_peer.py)):**
   - `L956`: cập nhật `assert cr["timeout"] == 600.0`.
   - Thêm test end-to-end `parse_verdict_from_md()` cho 3 ca `ScannerError` lịch sử (`12f4dfd4`, `deac9dd6`, `c6d7e142`), bảo toàn block scalar `|`/`>` có `note: keep: this`, bảo toàn escape hợp lệ + fail-closed `\xZZ` & `bad_yaml`.
5. **Tradeoff Card (`PR-1` — `ADR-0067`):**
   - **Core Invariant:** Strict-first `yaml.safe_load`, fail-closed YAML hỏng & block scalar bất biến, `_peer_models.py <= 800` LOC, 1 object `AUDIT_BASE_SYSTEM_PROMPT` cho KV-Cache, giữ `grok-4.7` cross-family cho `code_review`.
   - **Invalidation Condition:** Đo đồng thời (a) tỷ lệ timeout Pha 1 `code_review` (`>= 2/10` lượt vượt `600s`) và (b) tỷ lệ chạm `max_turns_reached` ở `8` turns (hiện `11/11 = 100%`), hoặc bất kỳ ca `_peer_yaml` nào parse nhầm YAML hỏng thành dict hợp lệ.

### 4.2. `PR-2` — `Governance Scripts + Guardrails Docs` (`Q1 + Q4 + Q3 docs`, `ONE_WAY_DOOR`: `HUB_CONSTITUTION`, Tradeoff Card)
1. **Sửa [`scripts/validation/audit_pr_comments.py`](../../../scripts/validation/audit_pr_comments.py) (`474 -> ~500 <= 800` LOC):**
   - Thêm `_is_coderabbit_skip_review_comment(body)` (`skip review by coderabbit.ai` + không có `<!-- walkthrough_start -->` + không actionable).
   - Trong `_collect_unaddressed_pr_comments()` (`L313-329`): loại trừ skip-review khỏi `effective_prc_cnt`; truyền `has_skipped_review: bool` vào `_build_zero_issue_result()` (`L353-371`) để chỉ gắn gợi ý `@coderabbitai review` (`< 10 stars`) khi có marker skip-review. Giữ `parse_cli_args()` 2-tuple (`L102-105`) và `COND-07`.
2. **Sửa [`scripts/governance/audit_peer_effectiveness.py`](../../../scripts/governance/audit_peer_effectiveness.py) (`435 -> <= 620 <= 800` LOC, hàm `<= 50` LOC):**
   - Thêm `_DEFAULT_BASELINE_SINCE = "2026-11-11T00:00:00+07:00"`, tham số `baseline_since: str | None = None` ở `evaluate_peer_effectiveness()` (API giữ mặc định không lọc; CLI `--baseline-since` mặc định `_DEFAULT_BASELINE_SINCE`, hỗ trợ `"all"`; ném `ValueError` khi chuỗi ngày sai định dạng).
   - Port chuẩn predicate `_peer_telemetry.py` đọc trực tiếp dict keys (`COND-PORT-05`), `None`-safe opt-out `{new, none, false, 0}`, ghép chuỗi cùng `exchange_dir` trong `0 < delta <= 43_200`, chặn `Plan -> Code`, tách file-stem equality và request-stem containment (`>= 8`), xuất `baseline_since_utc`, `pre_baseline_excluded: int`, `inferred_chain_links: int` tương thích `json.dumps`.
3. **Đồng bộ Docs & Rules:**
   - [`docs/rules/execution_coordination_guardrails.md`](../../../docs/rules/execution_coordination_guardrails.md) (`<= 24,576 B`), [`.agents/rules/release_gate.md`](../../../.agents/rules/release_gate.md), `.md/peer_exchange/PEER_HANDSHAKE.md`, `.md/peer_exchange/README.md`: đồng bộ `code_review` `600s`, ngưỡng `audit_direct` (`<= 100 LOC`, `<= 3` tệp), và hành vi `NO_AI_REVIEW` khi CodeRabbit skip `< 10★`.
4. **Tests ([`test_audit_pr_comments.py`](../../../scripts/tests/test_audit_pr_comments.py) & [`test_audit_peer_effectiveness.py`](../../../scripts/tests/test_audit_peer_effectiveness.py)):**
   - Full regression tests cho skip-review `< 10★` thuần (`NO_AI_REVIEW` `0`/`3`), skip + walkthrough (`CLEAN`), skip + actionable (`CHANGES_RECOMMENDED`); `baseline_since` / `"all"` / invalid `ValueError`, CLI-resumed Pass 2 link, `resume_session_id: "new"` opt-out, cross-repo isolation, `Plan -> Code` block với prompt `profile: code_review`, và `json.dumps`.
5. **Tradeoff Card (`PR-2` — `ADR-0067`):**
   - **Core Invariant:** Giữ `audit_pr_comments.py` chỉ đọc & `parse_cli_args()` 2-tuple, giữ `COND-07`, giữ `execution_coordination_guardrails.md <= 24,576 B`, giữ `evaluate_peer_effectiveness()` mặc định không lọc, tôn trọng `resume_session_id: "new"`.
   - **Invalidation Condition:** Nếu CodeRabbit thay đổi HTML marker skip-review hoặc mẫu kiểm toán thủ công phát hiện tỷ lệ ghép chuỗi sai `> 5%`.

### 4.3. `Phase 3` — Rollout Hậu Merge `PR-2`
- Chạy `CCBA_SKIP_GIT_PULL=1 .venv/bin/python scripts/sync_spoke.py --all --dry-run` $\to$ `--all --apply` đồng bộ rules & `PEER_HANDSHAKE.md` xuống `6` Spokes (không `git push` trên Spokes; giữ nguyên nhánh local `ccba-legal-knowledge`).

### 4.4. Lệnh Kiểm Chứng Bắt Buộc (`Outside Checks`)
```bash
.venv/bin/python -m pytest packages/ccba-harness/tests/test_peer*.py packages/ccba-harness/tests/test_cli_contract_parity.py scripts/tests/test_audit_pr_comments.py scripts/tests/test_audit_peer_effectiveness.py -q
.venv/bin/python -m ccba_harness verify-patch --preset code
.venv/bin/python scripts/validation/audit_pr_comments.py --repo vvChu/ccba-agent-platform --pr 929
.venv/bin/python scripts/validation/audit_pr_comments.py --repo vvChu/ccba-agent-platform --pr 929 --require-review
.venv/bin/python scripts/governance/audit_peer_effectiveness.py --roots /home/vvc/ccba/ccba-agent-platform /home/vvc/ccba/IDOP-CCBA-WAY /home/vvc/ccba/IBST_UNIFIED_ERP /home/vvc/ccba/ccba-legal-knowledge /home/vvc/ccba/ctymmt_ai_native_organization /home/vvc/Codebase/dgx-spark-toolkit --format markdown
wc -c docs/rules/execution_coordination_guardrails.md
```
