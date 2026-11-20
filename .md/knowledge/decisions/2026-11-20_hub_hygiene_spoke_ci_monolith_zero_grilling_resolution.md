# Biên Bản Phỏng Vấn Grilling & Kế Hoạch Triển Khai: Hub Hygiene, Spoke Sync/CI Bước B & Monolith Zero (`0/7`)

> **Ngày chốt Grilling:** `2026-11-20` | **Baseline:** Hub `main` @ `9f8df1b7` (`.venv/bin/python` = `Python 3.12.3`)  
> **Nguồn bối cảnh:** `.md/scratch/handoffs/handoff-2026-11-18-160900.md`, `.md/scratch/handoffs/handoff-2026-11-18-200100.md`, [session_learnings.md](../session_learnings.md)  
> **Biên lai Đối soát Seam ([ADR-0061](../../../docs/adr/0061-platform-aware-kiss-v2-and-quarantine-governance.md)):** `find-seam --in docx --out docx --json` $\rightarrow$ `MATCH` (`ooxml_processor.v1`, `ccba_ooxml:DocxDocument`) | `index_sha256`: `84408980fb63f7f7f2d4a5f493411abf42c8e35217a36c491de454ee4ea4bc9b`  
> **Impact-Based Handoff Gate ([ADR-0067](../../../docs/adr/0067-one-way-door-manifest-and-backpressure-circuit-breaker.md)):**  
> - **Đợt 1 (Waves 1–3):** `Fast-Path` hạ tầng & CI (không chạm mã nguồn `packages/*` hay Public Seam) $\rightarrow$ thực thi trực tiếp sau lệnh `proceed`.  
> - **Đợt 2 (Wave 4 — `7` Monoliths):** `ONE_WAY_DOOR` (`AUTHZ_SECURITY`, `CROSS_SPOKE_CONTRACT`, `exceeded_loc_budget=True`) $\rightarrow$ mở đầu bằng Grok Peer Plan Audit (`audit_plan` $\to$ `signoff_diff` đến `blocking_conditions == 0`) + `TradeoffCard` tại Checkpoint sau Đợt 1.

---

## 1. Bảng Chốt `5/5` Quyết Định Thiết Kế (`Q1`–`Q5`)

| Mã | Chủ đề | Quyết định đã khóa | Căn cứ thực đo & Ràng buộc |
| :--- | :--- | :--- | :--- |
| **`Q1`** | **Nhịp triển khai & Checkpoint** | Chia **2 Đợt có Checkpoint bắt buộc**: Đợt 1 chạy trọn **Wave 1 $\to$ Wave 2 $\to$ Wave 3** rồi dừng nghiệm thu; Đợt 2 chạy **Wave 4** tuần tự **4A (`ccba-ooxml/pptx`) $\to$ 4B (`ccba-harness`) $\to$ 4C (`ccba-legal-intel`)**. | Cô lập rủi ro hạ tầng khỏi `8,652 LOC` refactor cấu trúc (`~15` đơn vị PR/commit nguyên tử). |
| **`Q2`** | **`vvc-second-brain` & PR `#145`** | **Mở rộng Đợt 1:** Cài mới self-hosted ARM64 runner dạng `systemd --user` không cần `sudo` (`~/.actions-runner-vvc-second-brain`, unit `actions-runner-vvc-second-brain.service`, nhãn `[self-hosted, Linux, ARM64, dgx-spark]`), cập nhật `ci.yml` + sync delta Hub ngay trên nhánh PR `#145`, chạy xanh CI rồi merge. | `2` runner hiện có (`dgx-spark`, `idop`) đang chạy ổn định qua `systemd --user`; tháo gỡ triệt để lỗi GitHub Actions spending limit (fail `4s`) trên private repo. |
| **`Q3`** | **2 Spoke local-only** | **`IBST_UNIFIED_ERP`:** Tách **2 commits** trên `master` local — (1) `chore(sync)` cho Hub-sync thuần; (2) `chore(hygiene)` dùng `git rm --cached` cho `5` tệp `grok_phase5_*.md` (giữ nguyên `100%` file trên đĩa) + prune backup cũ đã xóa.<br>**`ctymmt_ai_native_organization`:** Quét `ccba-maskara` toàn repo rồi tạo `initial commit` sạch trên `master` local. | Giữ nguyên telemetry thực (`turn_count: 1 -> 2`) trên đĩa, đưa working tree về sạch theo chuẩn ADR-0045 / `RULE-4.20`. |
| **`Q4`** | **Wave 3 — `pytest-xdist` & Spoke CI** | Ghim trần **`-n 4 --dist=loadfile`** cho `IDOP-CCBA-WAY`, `dgx-spark-toolkit` và `vvc-second-brain` trên DGX Spark (`20` nhân chia sẻ `3` runners + dịch vụ local). **Rollback Gate định lượng:** chỉ giữ xdist cho từng suite khi chạy cục bộ pass **2 lần liên tiếp với `0` flake** (bảo toàn `--cov`) VÀ rút ngắn thời gian thực đo **$\ge 25\%$**. `ccba-legal-knowledge` (public, `ubuntu-latest`): giữ `ubuntu-latest`, thay `pip install --upgrade pip` $\times 5$ jobs bằng `uv` + `actions/cache@v4`, giữ nguyên tên `5` jobs & aggregator `Deterministic Parity & Schema Audit`. | Tránh tranh chấp CPU/RAM khi chạy `20` workers/PR; giữ KISS cho các suite vốn chạy `< 5s`. |
| **`Q5`** | **Wave 4 — Monolith Zero (`0/7`) & Grok Audit** | **Pure Structural Refactor (`0` đổi hành vi)** theo mô hình **Thin Facade + Private Submodules (`_*.py`)**, không sửa top-level `__init__.py` (`0` drift `covered_sha256` trên `verify-ccba-ooxml`, `verify-ccba-harness`, `verify-ccba-legal-intel`), bảo toàn `3` điểm mock (`_Originals.popen`, `ccba_legal.cli.*`, `ccba_legal.registry.resolve_project_root`), mọi hàm `<= 50 LOC` (`main` post-parse `<= 40 LOC`), `0` `# ccba:quarantine`, gỡ từng mục trong [module_budget_baseline.json](../../../packages/ccba-harness/src/ccba_harness/module_budget_baseline.json) về `{}` (`0/7`). Chạy Grok Peer Plan Audit ngay đầu Đợt 2 trước khi sửa mã `packages/*`. | Tuân thủ [peer_gate.py](../../../packages/ccba-harness/src/ccba_harness/peer_gate.py#L241-L271), `RULE-2.20`, `RULE-2.21` và ADR-0067. |

---

## 2. Đối Chiếu Thực Đo So Với Handoff Cũ (`9f8df1b7` vs `1325f390`)

1. **Remote branches Hub:** Còn **`6`** nhánh `origin/*` đã merge (`#779`, `#788`, `#794`, `#796`, `#798`, `#800`) thay vì `14`; xóa sạch để chỉ còn `refs/heads/main`.
2. **Nightly CI Hub:** Trong run `44500275566` (`2m48s`), bước `Install packages and dev tools` chỉ tốn `6s`, còn `2m32s` (`90%`) là `run_isolated_tests.py --all --stress`; tối ưu [nightly-slow-tests.yml](../../../.github/workflows/nightly-slow-tests.yml) thêm `fetch-depth: 0`, `cache: "pip"`, `actions/cache@v4` cho `~/.cache/uv`, gộp `1`-shot `uv pip install --system` khớp [ci.yml](../../../.github/workflows/ci.yml), và đặt `CCBA_AI_MOCK: "1"`.
3. **Verifiers & `PPTXSchemaValidator`:** `PR #813` (`6dca1547`) đã migrate xong `PPTXSchemaValidator`; `0/7` monoliths còn lại nằm trong `covered_paths` của bất kỳ `verify-ccba-*` skill nào.

---

## 3. Lộ Trình Hai Đợt Thực Thi

- **Đợt 1 (Waves 1–3):**
  1. **Wave 1:** Xóa `6` nhánh `origin/*` đã merge + Micro-PR tối ưu [nightly-slow-tests.yml](../../../.github/workflows/nightly-slow-tests.yml) và lưu biên bản Grilling này.
  2. **Wave 2:** Cài `actions-runner-vvc-second-brain.service` (`systemd --user`), chạy `sync_spoke.py --all --apply --force` đồng bộ bản `9f8df1b7`+, đóng gói sạch PR/commit trên `6/6` Spokes (`dgx-spark-toolkit`, `ccba-legal-knowledge`, `IDOP-CCBA-WAY`, `vvc-second-brain` PR `#145`, `IBST_UNIFIED_ERP`, `ctymmt_ai_native_organization`).
  3. **Wave 3:** Thực thi Bước B tối ưu CI cục bộ cho `IDOP-CCBA-WAY`, `dgx-spark-toolkit` (`-n 4 --dist=loadfile` qua Rollback Gate `>= 25%` / `0` flake) và `ccba-legal-knowledge` (`uv` + cache `5` jobs).
- **Checkpoint Đợt 1 $\to$ Đợt 2:** Báo cáo thực đo trạng thái sạch `6/6` Spokes và đối chiếu thời gian CI trước/sau.
- **Đợt 2 (Wave 4 — `0/7` Monoliths):** Khởi chạy Grok Peer Audit (`audit_plan` $\to$ `signoff_diff`), sau đó triển khai `7` Micro-PRs + `1` Rollup PR qua 3 chặng `4A` (`inventory.py`, `deck_builder.py`) $\to$ `4B` (`fleet.py`, `_file_monitor.py`, `_process_monitor.py`) $\to$ `4C` (`cli.py`, `registry.py` `[FOG-003]`).

---

## 4. Nghiệm Thu Thực Thi (Đợt 1 & Đợt 2 — `COMPLETED`, Monolith Zero `0/7`)

- **Trạng thái tổng thể:** `COMPLETED` — cả `Đợt 1` (Waves 1–3) và `Đợt 2` (Wave 4 Monolith Zero `0/7`, đóng `[FOG-003]`) đã hoàn tất và merge về `main` với `8/8` GitHub CI checks xanh.
- **Đợt 1 (Waves 1–3):**
  - `PR #822` (`e8f10c84`): Hub Hygiene ([nightly-slow-tests.yml](../../../.github/workflows/nightly-slow-tests.yml) + xóa `6` nhánh `origin/*` đã merge).
  - Spoke Sync & Wave 3 CI: cài runner `actions-runner-vvc-second-brain.service` (`systemd --user`), đồng bộ `6/6` Spokes (`PR #253`, `#60`, `#145` + local commits trên `IBST_UNIFIED_ERP` & `ctymmt_ai_native_organization`) và tối ưu CI Spoke (`PR #254`, `#61`).
- **Đợt 2 — Grok Peer Plan Audit:** `APPROVE_PLAN`, `blocking_conditions: 0` (sessions `abed9168`, `8b01bb0c`, `7fe2756a-8482-4d51-82b1-044cc4308b2f`; hồ sơ đối soát tại `.md/peer_exchange/grok_monolith_zero_wave4_signoff_p3.md`).
- **Chuỗi Micro-PR Wave 4 (`PR-M0` .. `PR-M7`) đã merge vào `main`:**
  - `PR #823` (`e89526a7`, `PR-M0`): sửa `mypy` upstream trong [_workspace_roots.py](../../../packages/ccba-harness/src/ccba_harness/_workspace_roots.py) (`yaml_mod: Any = None`).
  - `PR #824` (`5df33743`, `PR-M1`): phân rã [inventory.py](../../../packages/ccba-ooxml/src/ccba_ooxml/pptx/inventory.py) (`1,033 LOC`) thành facade + `_inventory_models.py`, `_inventory_metrics.py`, `_inventory_geometry.py` (`7 -> 6`).
  - `PR #825` (`3b26d6d8`, `PR-M2`): phân rã [deck_builder.py](../../../packages/ccba-ooxml/src/ccba_ooxml/pptx/deck_builder.py) (`1,586 LOC`) thành facade + `_deck_models.py`, `_deck_parser.py`, `_deck_render_basic.py`, `_deck_render_complex.py` (`6 -> 5`).
  - `PR #826` (`bad936c8`, `PR-M3`): phân rã [fleet.py](../../../packages/ccba-harness/src/ccba_harness/fleet.py) (`1,024 LOC`) thành facade + `_fleet_scanner.py`, `_fleet_charts.py`, `_fleet_html.py` (`5 -> 4`).
  - `PR #827` (`d9d81b17`, `PR-M4`): phân rã [_file_monitor.py](../../../packages/ccba-harness/src/ccba_harness/_file_monitor.py) (`1,127 LOC`, `AUTHZ_SECURITY`) thành facade + `_file_path_utils.py`, `_file_sensitive_eval.py`, `_file_ast_scanner.py` (`4 -> 3`).
  - `PR #828` (`80a1303b`, `PR-M5`): phân rã [_process_monitor.py](../../../packages/ccba-harness/src/ccba_harness/_process_monitor.py) (`1,185 LOC`, `AUTHZ_SECURITY`) thành facade + `_proc_shell_parser.py`, `_proc_guard_checks.py`, `_proc_wrappers.py` (`3 -> 2`).
  - `PR #829` (`4e91f75c`, `PR-M6`): phân rã [cli.py](../../../packages/ccba-legal-intel/src/ccba_legal/cli.py) (`1,455 LOC`, `CROSS_SPOKE_CONTRACT`) thành facade + `_cli_parser.py`, `_cli_crawl_handlers.py`, `_cli_pipeline_handlers.py`, `_cli_query_handlers.py` (`2 -> 1`).
  - `PR #830` (`75683856`, `PR-M7`): phân rã [registry.py](../../../packages/ccba-legal-intel/src/ccba_legal/registry.py) (`1,242 LOC`, `CROSS_SPOKE_CONTRACT`) thành facade (`258 LOC`) + `_registry_discovery.py` (`181 LOC`), `_registry_lifecycle.py` (`461 LOC`), `_registry_query.py` (`350 LOC`) và đưa [module_budget_baseline.json](../../../packages/ccba-harness/src/ccba_harness/module_budget_baseline.json) về `{}` (`0/7`, `8,670 -> 0 LOC` ratchet, đóng `[FOG-003]`).
- **Kết quả Kiểm định Toàn Monorepo sau `PR #830` (`75683856`):**
  - Không chỉnh sửa bất kỳ top-level `__init__.py` nào (`0` `# ccba:quarantine`, `check_ast_function_length` & `check_module_size_budget` xanh).
  - `verify-patch --preset ci`: **7/7 PASS** (`18,593.0 ms`: ruff check, ruff format, `mypy packages/*/src`, pytest, `validate_skills.py --enforce-gpi`, `compile_catalog.py --check`, `sync_hub_adr_matrix.py --check`).
  - Profile-B Verifiers: `run_verify_ooxml.py` (**6 passed**, `0.07s`), `run_verify_harness.py` (**8 passed**, `0.30s`), `run_verify_legal_intel.py` (**6 passed**, `0.10s`).
  - `scripts/eval/run_harness_evals.py --all --ci-matrix`: **4/4 gates PASS** (`Ruff Lint`, `Ruff Format`, `Mypy Typecheck`, `Pytest Unit Tests`).
