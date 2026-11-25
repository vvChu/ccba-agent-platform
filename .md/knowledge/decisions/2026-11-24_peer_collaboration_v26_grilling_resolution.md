# Biên Bản Phỏng Vấn Grilling & Kế Hoạch Triển Khai Nâng Cấp Cơ Chế Hợp Tác Peer Collaboration `v2.6`

> **Ngày chốt Grilling:** `2026-11-24` | **Baseline Hub:** `main` @ `2b662343` (`PR #902` merged @ `e07cf8c4`) | **Trạng thái:** `PR-1 MERGED (#902) — PR-2 IN_PROGRESS`  
> **Biên lai Đối soát Seam ([ADR-0061](../../../docs/adr/0061-platform-aware-kiss-v2-and-quarantine-governance.md)):**
> - `.venv/bin/python scripts/governance/compile_catalog.py --in markdown --out json --json` $\rightarrow$ `status: "NO_MATCH"` (`count: 0`, `index_sha256: 29d4ee1aa2efb369ce154585cd65e1c44ec31efed8ec4096a8f603b8944b6c49`)
> - Chỉnh sửa trực tiếp trên các Seam hiện hữu của `ccba_harness` và `scripts/spoke`: [`_peer_watchdog.py`](../../../packages/ccba-harness/src/ccba_harness/_peer_watchdog.py), [`peer.py`](../../../packages/ccba-harness/src/ccba_harness/peer.py), [`telemetry.py`](../../../packages/ccba-harness/src/ccba_harness/telemetry.py), [`_peer_telemetry.py`](../../../packages/ccba-harness/src/ccba_harness/_peer_telemetry.py), [`_parameter_cleanliness.py`](../../../packages/ccba-harness/src/ccba_harness/_parameter_cleanliness.py), [`check_spoke_cleanliness.py`](../../../scripts/spoke/check_spoke_cleanliness.py).
> **Impact-Based Handoff Gate ([ADR-0067](../../../docs/adr/0067-one-way-door-manifest-and-backpressure-circuit-breaker.md)):** `ONE_WAY_DOOR` (cập nhật Public Seam `ccba_harness` `PROFILE_SPECS` / `resolve_model_token_rates` + cập nhật Tier-0 guardrail & ADRs) $\rightarrow$ đã qua **Grok Peer Plan Audit (`2` vòng, `APPROVE_PLAN`, `blocking_conditions: 0`)**; dừng chờ lệnh `proceed` của người dùng trước khi sửa mã sản xuất.

---

## 1. Bước 0 — Mài Sắc Bài Toán & Bằng Chứng Thực Nghiệm (`2026-09-29` → `2026-11-24`)

1. **Mục tiêu thực chất (`in-your-own-words`):** Chuyển hóa các phát hiện định lượng từ 57 ngày vận hành thực tế (`1,072` tệp `.md` trên 7 repository và `1,224` phiên `~/.grok/sessions/`) thành đợt nâng cấp **`v2.6`** cho cơ chế hợp tác **Antigravity ⟷ Grok**. Trọng tâm không phải thay thế một hệ thống đang lỗi (tỷ lệ hoàn tất phiên từ `11/11` đạt `99.5%`, hội tụ sạch đạt `98.5%`, chi phí trung vị `\$0.52`/chuỗi), mà là giải quyết 5 điểm nghẽn cấu trúc: giảm thuế độ trễ (`11.5` phút/chuỗi), chuẩn hóa cơ chế 2 pha `Auto-Synthesis` (`79.4%` ở `audit_plan`, `92.3%` ở `arch_audit`), chống lạm phát `blocking: true` (`65.5%`) & đồng thuận mù quáng (`0.6%` phản biện), sửa sai lệch FinOps trên model Gateway (`5.5×`), và xử lý `203` tệp nháp đang bị Git track trên 5 Spoke.
2. **Dữ kiện gốc kiểm chứng trực tiếp trên codebase & logs (`[đo thực tế]` / `[phân tích log]`):**
   - **Phân bổ luồng & mô hình:** `99.4%` lượt là Gatekeeper (`agentic_code = 0`, `patch_fast = 3`, `qwen-local = 1`); `494/495` lượt theo chiều `Antigravity -> Grok` `[đo thực tế]`.
   - **Giá trị Vòng 2 (`signoff_diff`):** Pass 1 bắt lỗi chặn `64.4%`; Pass 2 vẫn bắt thêm lỗi blocking còn sót ở `33.8%` (`22/65`) chuỗi sau `11/11`; tỷ lệ hội tụ sạch `98.5%` (`64/65`) `[phân tích log]`.
   - **Động học độ trễ sau `11/11`:** `grok-4.7-build` tiêu tốn hằng số `33–36s / model call` bất kể `high`/`xhigh` (`audit_plan` `12`t mất `443s` với `79.4%` `Auto-Synthesis` và bắt lỗi `50/50`; `arch_audit` `8`t mất `306s` với `92.3%` `Auto-Synthesis`; `signoff_diff` `8`t mất `163s` với `13.6%` `Auto-Synthesis`) `[phân tích log]`.
   - **Sai lệch FinOps & `code_review`:** `gemini-3.8-flash-high` (`47` lượt) bị tính `\$7.6935` theo giá phẳng `\$1.25 / \$5.00` của [`telemetry.py`](../../../packages/ccba-harness/src/ccba_harness/telemetry.py#L25-L40) và [`_peer_telemetry.py`](../../../packages/ccba-harness/src/ccba_harness/_peer_telemetry.py#L93-L108) thay vì `~\$1.41` khi tính chiết khấu `cachedReadTokens` (`69.6%` cache); riêng `6` lượt `code_review` dùng Gemini sau `11/11` đều chạm trần và bắt `0/6` lỗi chặn `[đo thực tế]`.
   - **Vệ sinh Spoke:** Hub chỉ track `2` tệp quy chuẩn (`0` nháp), nhưng 5 Spoke (`IDOP-CCBA-WAY`: `102`, `ccba-legal-knowledge`: `40`, `dgx-spark-toolkit`: `34`, `IBST_UNIFIED_ERP`: `19`, `VvC_Notes`: `8`) vẫn track `203` tệp nháp cũ trong Git index `[đo thực tế]`.
3. **Kiểm chứng độc lập bên ngoài (*outside check*):**
   - Kiểm thử tự động `verify-patch --preset code`, unit test hồi quy cho `resolve_model_token_rates_detailed` với `cachedReadTokens` thật (`test_peer_telemetry.py`, `test_telemetry.py`), kiểm tra `check_hardcoded_parameters.py`, và kiểm tra `--enforce-module-budget` trên `check_spoke_cleanliness.py` ($\le 941$ LOC).
   - Kiểm đếm `git ls-files .md/peer_exchange/` trên Hub và 5 Spoke sau triển khai Phase 3.

---

## 2. Bảng Chốt `5/5` Quyết Định Thiết Kế (`Q1`–`Q5`)

| Mã | Chủ đề Frontier | Quyết định đã khóa & Ràng buộc thực thi | Căn cứ |
| :---: | :--- | :--- | :--- |
| **`Q1`** | **Định vị chiến lược & phạm vi `v2.6`** | Chính thức hóa mô hình **"Antigravity Build + Grok Adversarial Gatekeeper"** trong [ADR-0063](../../../docs/adr/0063-level-2-peer-delegation-protocol-and-cost-guardrails.md), hạ `agentic_code` / `patch_fast` / `qwen-local` xuống vai trò tùy chọn/thực nghiệm (gỡ KPI tiết kiệm 85–100% coding cost), dồn phạm vi `v2.6` vào 4 nâng cấp KISS cho luồng Gatekeeper. | `99.4%` lưu lượng là Gatekeeper; chi phí đã tối ưu ở `\$0.52`/chuỗi. |
| **`Q2`** | **Cắt độ trễ & `Auto-Synthesis`** | Hạ `audit_plan` `12 -> 9` turns (đồng bộ `DEFAULT_GROK_SPEC`), giữ `arch_audit = 8`, `signoff_diff = 8`, `deep_spec_audit = 25`, giữ `xhigh`; ép gọi tool song song trong `BOUNDED_TOOL_BUDGET_PROMPT` (`Explore-Then-Synthesize` 2 pha chủ đích); bắt buộc prompt Pass 1 có **Bản đồ `file:line` trọng yếu**. | Tốc độ `33–36s/call` nên không nới turns; ép batching + bản đồ neo giúp giảm lượt mò đường. |
| **`Q3`** | **Chống lạm phát `blocking` & Compliance Bias** | Khóa `blocking: true` trong `AUDIT_BASE_SYSTEM_PROMPT` chỉ cho **4 nhóm lỗi thật** (logic/hợp đồng, bảo mật/PII, gãy CI/OS, giả định sai mã nguồn); bổ sung **KISS & Scope Check** vào §20.3 khuyến khích `[REBUT_WITH_EVIDENCE]`, giữ Pass 2 bắt buộc; đưa `audit_direct` (`120s`, `--no-tools`) lên bảng chọn nhanh. | `65.5%` điều kiện từng bị gắn `blocking`, nhưng chỉ `0.6%` bị phản biện; Pass 2 vẫn bắt `33.8%` lỗi sót. |
| **`Q4`** | **FinOps Telemetry & `code_review`** | Nâng cấp `telemetry.py` & `_peer_telemetry.py` dùng bảng giá khai báo theo họ model có chiết khấu `cachedReadTokens` (giữ nguyên chữ ký 2-tuple của `resolve_model_token_rates`); chuyển `code_review` từ `gemini-38-flash` sang **`grok-4.7`** (`high`, `8` turns, `450.0s`, giữ `fallback_model: "grok-4.7-build-fast"`). | Chấm dứt lệch chi phí `5.5×` trên Flash; bảo toàn độc lập chéo họ mô hình ở `100%` profile audit. |
| **`Q5`** | **Vệ sinh `203` tệp Git trên 5 Spoke** | Thêm `find_tracked_peer_exchange_drafts` trong `_parameter_cleanliness.py` + cảnh báo warn-only (`--strict` exit `1`) trong `check_spoke_cleanliness.py` ($\le 941$ LOC); hậu merge chạy `sync_spoke.py --all --apply` rồi `git rm --cached` an toàn trên 5 Spoke (giữ 100% file cục bộ, worktree riêng cho `IDOP-CCBA-WAY`, không `git push`). | Bảo vệ dữ liệu dự án trên Git index của Spoke mà không đụng lịch sử commit hay file cục bộ. |

---

## 3. Thẩm Định Độc Lập Ngang Hàng (`Grok Peer Plan Audit — ADR-0067`)

| Vòng | Profile | Session ID | Phán quyết | Risk | Blocking | Chi phí / Thời gian | Tóm tắt Kết quả |
| :---: | :--- | :--- | :---: | :-: | :-: | :---: | :--- |
| **Pass 1** | `audit_plan` | `a5b1d735-c8d8-4960-9cb9-9001bbd9e810` | `REVISE_PLAN` | `3` | `5` | `\$0.4169` / `516.06s` | Bắt chính xác 5 điều kiện chặn (`COND-01..05`) + 2 lưu ý (`COND-06..07`) về fallback `code_review`, thứ tự kiểm giá `local`, phạm vi Hub/Spoke của scanner dưới trần `941` LOC, lệch ticks/giá tại `ADR-0064`/`0065`, và nhánh worktree `Phase 3`. |
| **Pass 2** | `signoff_diff` | `3ed0be38-746a-4780-8a27-c51c4382b192` | **`APPROVE_PLAN`** | `2` | **`0`** | `\$0.1222` / `147.26s` | Xác nhận `7/7` điều kiện Pass 1 đã khép khớp 100% mã nguồn; bổ sung `COND-08` (`blocking: false`) giới hạn dòng sửa tại `ADR-0064`/`0065`. |

### Ma trận Phân loại Điều kiện (§20.3 3-Label Triage Matrix)

| ID | Vòng | Phân loại | Đối chứng mã nguồn (`file:line`) & Quyết định Áp dụng |
| :--- | :---: | :--- | :--- |
| `COND-01` | Pass 1 | `[ADOPT_AS_IS]` | [`_peer_watchdog.py`](../../../packages/ccba-harness/src/ccba_harness/_peer_watchdog.py#L200-L212) hiện có `fallback_model: "grok-4.7-build-fast"`. Chuyển `model` sang `"grok-4.7"`, **giữ `fallback_model: "grok-4.7-build-fast"`** (không fallback sang `gemini-38-flash`), `max_turns: 8`, `reasoning_effort: "high"`, `timeout: 450.0`. Khóa đủ 4 trường trong [`test_peer.py`](../../../packages/ccba-harness/tests/test_peer.py#L939-L954). |
| `COND-02` | Pass 1 | `[ADOPT_AS_IS]` | [`telemetry.py`](../../../packages/ccba-harness/src/ccba_harness/telemetry.py#L29-L40): kiểm tra `local` đầu tiên $\to$ `(0.0, 0.0, 0.0)`, rồi `"flash"` $\to$ `(0.30, 0.075, 2.50)`, `"sonnet"` $\to$ `(3.00, 0.30, 15.00)`, mặc định `(1.25, 0.3125, 5.00)`; chỉ dùng token họ (0 literal `gemini-*`/`claude-*`); giữ chữ ký 2-tuple `(r_in, r_out)`. Tại [`_peer_telemetry.py`](../../../packages/ccba-harness/src/ccba_harness/_peer_telemetry.py#L93-L108), giữ nhánh `costUsdTicks` (trừ local `(0,0)`), còn nhánh `estimated` nhận `cached` tại `:183` theo `uncached = inp - min(max(cached, 0), inp)`. |
| `COND-03` | Pass 1 | `[ADOPT_AS_IS]` | `find_tracked_peer_exchange_drafts` trong [`_parameter_cleanliness.py`](../../../packages/ccba-harness/src/ccba_harness/_parameter_cleanliness.py#L442) kiểm `(spoke_root / ".git").exists()`, bỏ qua Hub khi `git remote get-url origin` chứa `"ccba-agent-platform"`, lọc allowlist `{"PEER_HANDSHAKE.md", "README.md", ".gitkeep"}` khớp [`spoke_bootstrap.py`](../../../scripts/spoke/spoke_bootstrap.py#L84-L86). Trong [`check_spoke_cleanliness.py`](../../../scripts/spoke/check_spoke_cleanliness.py#L851-L877) (`930` LOC, trần `941`), thêm $\le 8$ dòng sau `ruff format` và gộp vào `has_warnings` (exit `0` mặc định, exit `1` chỉ với `--strict`). |
| `COND-04` | Pass 1 | `[ADOPT_AS_IS]` | Cập nhật [ADR-0064](../../../docs/adr/0064-peer-exchange-telemetry-and-model-provenance.md#L77-L78) (sửa `/ 10000.0` $\to$ `/ 10_000_000_000.0` và công thức `estimated` có `cachedReadTokens` là tập con của `inputTokens` theo [`test_peer_telemetry.py`](../../../packages/ccba-harness/tests/test_peer_telemetry.py#L124-L130)) và [ADR-0065](../../../docs/adr/0065-peer-runtime-hardening-and-topological-fail-closed.md#L84-L86) (biểu phí phân tầng); kiểm tra `sync_hub_adr_matrix.py --check`. |
| `COND-05` | Pass 1 | `[ADOPT_AS_IS]` | Phase 3 chạy `sync_spoke.py --all --apply` (kích hoạt `ensure_gitignore_rule` tại [`coordinator.py`](../../../scripts/spoke/sync/coordinator.py#L1094)) trước khi dọn index; với `IDOP-CCBA-WAY` dùng `git worktree add -b chore/untrack-peer-exchange <wt_path> main`; chạy `git rm --cached` chỉ trên 5 Spoke, không `git push`, không đụng Hub. |
| `COND-06` | Pass 1 | `[ADOPT_AS_IS]` | Giữ nguyên `analyze_subagent_session()` tại [`telemetry.py`](../../../packages/ccba-harness/src/ccba_harness/telemetry.py#L401-L403) trên `PRICE_PER_M_INPUT` / `PRICE_PER_M_OUTPUT`. |
| `COND-07` | Pass 1 | `[ADOPT_AS_IS]` | Giữ `arch_audit = 8` turns (chỉ nhận batching prompt), hạ `audit_plan` `12 -> 9`, ghi rõ chỉ tiêu vô hiệu định lượng vào `Tradeoff Card`. |
| `COND-08` | Pass 2 | `[ADOPT_AS_IS]` | Khi sửa ADR trong `PR-2`, chỉ sửa đúng dòng `77–78` của `ADR-0064` (giữ dòng `79`) và dòng `84–86` của `ADR-0065` (giữ dòng `87`). |

---

## 4. Kế Hoạch Triển Khai Chi Tiết (`Implementation Plan` — Chờ Lệnh `proceed`)

### 4.1. `PR-1` — `ccba-harness` Core (`Q2 + Q3 + Q4`, `ONE_WAY_DOOR` + Tradeoff Card)
1. **[`_peer_watchdog.py`](../../../packages/ccba-harness/src/ccba_harness/_peer_watchdog.py)** (`685 <= 800` LOC):
   - `:124-130` (`BOUNDED_TOOL_BUDGET_PROMPT`): hướng dẫn gọi song song nhiều `read_file`/`grep` trong cùng 1 lượt và ghi nhận cơ chế 2 pha `Explore-Then-Synthesize`.
   - `:132-139` (`AUDIT_BASE_SYSTEM_PROMPT`): khóa `blocking: true` chỉ cho 4 nhóm lỗi thật (sai logic/hợp đồng, bảo mật/PII, gãy CI/OS, giả định sai mã nguồn); gợi ý ngoài phạm vi/làm đẹp đặt `blocking: false`.
   - `:150-162` (`audit_plan`): giảm `max_turns` từ `12 -> 9` (giữ `grok-4.7`, `xhigh`, `900.0s`).
   - `:200-212` (`code_review`): đổi `model` $\to$ `"grok-4.7"` (`# ccba:allow-raw-model`), giữ `fallback_model: "grok-4.7-build-fast"`, `max_turns: 8`, `reasoning_effort: "high"`, `timeout: 450.0`.
2. **[`peer.py`](../../../packages/ccba-harness/src/ccba_harness/peer.py)** (`755 <= 800` LOC):
   - `:91` (`DEFAULT_GROK_SPEC["max_turns"]`): đồng bộ `12 -> 9`.
3. **[`telemetry.py`](../../../packages/ccba-harness/src/ccba_harness/telemetry.py)** (`744 <= 800` LOC) & **[`_peer_telemetry.py`](../../../packages/ccba-harness/src/ccba_harness/_peer_telemetry.py)** (`729 <= 800` LOC):
   - Trong `telemetry.py`: giữ `PRICE_PER_M_INPUT = 1.25`, `PRICE_PER_M_OUTPUT = 5.00`, dòng `:401-403` và chữ ký 2-tuple `resolve_model_token_rates(model_id) -> tuple[float, float]`. Thêm bảng giá khai báo theo họ & hàm `resolve_model_token_rates_detailed(model_id) -> tuple[float, float, float]` (`local` trước $\to$ `(0.0, 0.0, 0.0)`; `flash` $\to$ `(0.30, 0.075, 2.50)`; `sonnet` $\to$ `(3.00, 0.30, 15.00)`; mặc định `(1.25, 0.3125, 5.00)`), chỉ dùng token họ (`"qwen-local"`, `"local"`, `"flash"`, `"sonnet"`).
   - Trong `_peer_telemetry.py`: mở rộng `_compute_session_cost(..., cached: int = 0)` tại `:93-108` và truyền `cached` tại `:183`; giữ nguyên nhánh `costUsdTicks` (trừ local `(0,0)`), còn nhánh `estimated` khấu trừ `cached` (`uncached = inp - min(max(cached, 0), inp)`).
4. **Tests cập nhật trong `PR-1`:**
   - [`test_peer.py`](../../../packages/ccba-harness/tests/test_peer.py#L939-L954): khóa `code_review` (`model == "grok-4.7"`, `fallback_model == "grok-4.7-build-fast"`, `max_turns == 8`, `timeout == 450.0`) và `audit_plan` (`max_turns == 9`, `reasoning_effort == "xhigh"`).
   - [`test_peer_telemetry.py`](../../../packages/ccba-harness/tests/test_peer_telemetry.py#L209-L248): cập nhật `gemini-38-flash` (`cachedReadTokens: 0` $\to$ `\$2.80`), thêm ca `cachedReadTokens: 700_000` (`\$2.6425`), và ca model fallback vô danh giữ `\$6.25`.
   - [`test_telemetry.py`](../../../packages/ccba-harness/tests/test_telemetry.py#L329-L338): kiểm thử `resolve_model_token_rates` & `resolve_model_token_rates_detailed` qua các họ `qwen-local`, `local`, `flash`, `sonnet`, `""`, `None`.
5. **Tradeoff Card (`PR-1` — `ADR-0067`):**
   - **Core Invariant:** Giữ nguyên chữ ký 2-tuple `resolve_model_token_rates()`, bảo toàn đồng nhất object `AUDIT_BASE_SYSTEM_PROMPT` trên 5 profile đọc đĩa để giữ Prefix KV-Cache, và bảo đảm 100% tính độc lập chéo họ mô hình (`grok-4.7` / `grok-4.7-build-fast`) trên mọi profile audit.
   - **Invalidation Condition:** Đo tỷ lệ chạm `Auto-Synthesis` và tỷ lệ phát hiện lỗi chặn sau khi hạ `audit_plan` (`12 -> 9`) & giữ `arch_audit` (`8`); nếu tỷ lệ bỏ sót lỗi tăng hoặc `code_review` trên `grok-4.7` vượt `450s`, mở rộng lại ngân sách turns hoặc tách profile.
   - **Git Hunk Reference:** Bổ sung `#L<a>-L<b>` ($\le 30$ dòng) từ diff thực tế của `PR-1`.

### 4.2. `PR-2` — Docs, Rules, ADRs & Spoke Git-Tracking Hygiene (`Q1 + Q2 + Q3 + Q4 + Q5`)
1. **[ADR-0063](../../../docs/adr/0063-level-2-peer-delegation-protocol-and-cost-guardrails.md)** (`Q1 + Q2`): Cập nhật định vị chính thức *"Antigravity Build + Grok Adversarial Gatekeeper"*, hạ `AGENTIC_CODE` / `PATCH_FAST` / `qwen-local` thành tùy chọn/thực nghiệm, cập nhật `AUDIT_PLAN` `12 -> 9`.
2. **[ADR-0064](../../../docs/adr/0064-peer-exchange-telemetry-and-model-provenance.md#L77-L78)** & **[ADR-0065](../../../docs/adr/0065-peer-runtime-hardening-and-topological-fail-closed.md#L84-L86)** (`COND-04` + `COND-08`): Chỉ sửa đúng dòng `77–78` ở `ADR-0064` (`/ 10_000_000_000.0` và công thức `estimated` theo `cachedReadTokens` là tập con của `inputTokens`, giữ nguyên dòng `79`) và dòng `84–86` ở `ADR-0065` (biểu phí phân tầng, giữ nguyên dòng `87`).
3. **[execution_coordination_guardrails.md](../../../docs/rules/execution_coordination_guardrails.md#L132-L165)**, `.md/peer_exchange/PEER_HANDSHAKE.md`, `.md/peer_exchange/README.md`:
   - Đồng bộ bảng profile (`audit_plan` `9`t/`900s`, `arch_audit` `8`t/`600s`, `signoff_diff` `8`t/`600s`, `code_review` `grok-4.7` `high` `8`t/`450s`, `audit_direct` `grok-4.7` `high` `3`t/`120s` `--no-tools`).
   - Bắt buộc Bản đồ `file:line` Pass 1, batch tool song song, và thêm KISS & Scope Check ở §20.3 (giữ Pass 2 `signoff_diff`).
4. **[`_parameter_cleanliness.py`](../../../packages/ccba-harness/src/ccba_harness/_parameter_cleanliness.py)** (`442 -> ~465 <= 800` LOC) & **[`check_spoke_cleanliness.py`](../../../scripts/spoke/check_spoke_cleanliness.py)** (`930` LOC, trần `941` LOC):
   - Thêm `find_tracked_peer_exchange_drafts(spoke_root: Path) -> list[str]` (kiểm `.git` qua `exists()`, trả `[]` nếu `origin` chứa `"ccba-agent-platform"` hoặc không có `.git`, lọc `{"PEER_HANDSHAKE.md", "README.md", ".gitkeep"}`).
   - Trong `check_spoke_cleanliness.py`: thêm $\le 8$ dòng sau `ruff format`, nối vào `has_warnings` (không vào `has_errors`). Bổ sung tests vào [`test_spoke_cleanliness.py`](../../../scripts/tests/test_spoke_cleanliness.py).

### 4.3. `Phase 3` — Triển Khai Vận Hành Hậu Merge (`Q5`)
- Chạy `CCBA_SKIP_GIT_PULL=1 .venv/bin/python scripts/sync_spoke.py --all --dry-run` $\to$ `--all --apply` (đã kích hoạt `ensure_gitignore_rule` và cập nhật `PEER_HANDSHAKE.md`, `README.md`, Tier-0 guardrails, `guardrails_manifest.json`).
- Trên đúng 5 Spoke (`ccba-legal-knowledge`, `dgx-spark-toolkit`, `IBST_UNIFIED_ERP`, `VvC_Notes`, và worktree `git worktree add -b chore/untrack-peer-exchange <wt_path> main` của `IDOP-CCBA-WAY`), chạy `git rm --cached` cho `203` tệp nháp `.md/peer_exchange/`, giữ nguyên 100% file cục bộ, commit sạch cục bộ (không `git push`, không đụng Hub).

### 4.4. Lệnh Kiểm Chứng Bắt Buộc Sau Thi Công (`Outside Checks`)
```bash
.venv/bin/python -m pytest packages/ccba-harness/tests/test_peer.py packages/ccba-harness/tests/test_peer_telemetry.py packages/ccba-harness/tests/test_telemetry.py packages/ccba-harness/tests/test_cli_contract_parity.py scripts/tests/test_spoke_cleanliness.py tests/governance/test_parameter_scanner_parity.py -q
.venv/bin/python -m ccba_harness verify-patch --preset code
.venv/bin/python scripts/governance/check_hardcoded_parameters.py --dir packages/ccba-harness/src
.venv/bin/python scripts/spoke/check_spoke_cleanliness.py --path . --enforce-module-budget
.venv/bin/python scripts/sync_hub_adr_matrix.py --check
```
