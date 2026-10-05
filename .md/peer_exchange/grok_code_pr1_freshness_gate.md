---
request_id: req-20261005-pr1-code
from_agent: grok
to_agent: antigravity
response_type: implementation
verdict: IMPLEMENTATION_READY
conditions: []
risk_score: 2
effort: S
summary: "PR-1 đã nằm trong working tree. Cổng freshness đóng khi --apply, dry-run chỉ cảnh báo, --allow-stale-catalog ghi audit và cho đi tiếp. scripts/tests/test_catalog_freshness_gate.py 6/6 PASS."
tests:
  - command: python -m pytest scripts/tests/test_catalog_freshness_gate.py -q
    result: "6 passed"
  - command: python -m ccba_harness verify-patch --file scoped freshness/sync/adr/catalog/matrix checks
    result: "5/5 passed"
---

# PR-1 — Catalog Stale Hard Gate & ADR-0062

Mã đã được ghiPR-1 đã nằm trong working tree. `scripts/tests/test_catalog_freshness_gate.py` đạt **6/6 PASS**. Phán quyết trong `.md/peer_exchange/grok_code_pr1_freshness_gate.md` là `IMPLEMENTATION_READY`.

`--apply` dừng với mã 1 khi `catalog.yaml` lệch. Dry-run chỉ cảnh báo. `--allow-stale-catalog` in `[Sync] AUDIT: CATALOG_STALE_BYPASS` và cho sync đi tiếp, kể cả khi bước kiểm tra ném exception.

- `compile_catalog.py` có `CATALOG_RECOMPILE_COMMAND` và đưa `guardrails` vào `_BASE_FIELDS`.
- `assess_catalog_freshness()` thay khối nuốt lỗi trong `sync_spoke_bundle`. Nếu kết quả là `catalog_stale`, sync trả 1 trước khi copy.
- `build_parser()` nhận `--allow-stale-catalog` và truyền cờ này vào `sync_project()` cùng `sync_all_spokes()`.
- ADR-0062 ghi registry khai báo, cổng freshness đóng khi lỗi, và sắp xếp topo package. Ma trận ADR đã được biên dịch lại.

`compile_catalog.py --check` vẫn in-sync, nên không cần `--write`. Bộ kiểm tra scoped (ruff, pytest sync/ADR, catalog check, matrix check) là **5/5 PASS**.
ệnh biên dịch lại.
2. `scripts/spoke/sync/coordinator.py`
   - `assess_catalog_freshness(hub_root, spoke_root, dry_run=False, allow_stale_catalog=False) -> str | None`.
   - Cổng nằm trong `sync_spoke_bundle`, đúng chỗ khối `except Exception: pass` cũ (trước `_sync_full_bundle` và `_sync_single_item`). `halt == "catalog_stale"` thì `_halt_reason = "catalog_stale"` và `return 1`.
   - `allow_stale_catalog` đi qua `SpokeSynchronizer.sync()`, `sync_project()`, và `sync_all_spokes()`. Batch dừng các Spoke còn lại khi halt reason là `catalog_stale`.
3. `scripts/spoke/sync/cli.py`
   - `build_parser()` thêm `--allow-stale-catalog` (`store_true`, default `False`).
   - Mọi lời gọi `sync_project()` và `sync_all_spokes()` nhận `allow_stale_catalog=args.allow_stale_catalog`, kể cả preview và nhánh xác nhận TTY.
4. `docs/adr/0062-declarative-synchronization-registry-and-auto-discovery.md`
   - Ghi Declarative Synchronization Registry, Fail-Closed Freshness Hard Gate, và Topological Package Discovery.
   - `scripts/sync_hub_adr_matrix.py` đã cập nhật `docs/adr/README.md` và `docs/adr/TRACEABILITY_MATRIX.md`. `--check` PASS.

## Kiểm thử phụ

Catalog viết tay trong fixture không phải đầu ra compiler. Ba module sync và CLI đã có fixture `autouse` gọi cổng với `allow_stale_catalog=True`, để test merge không bị chặn bởi catalog fixture. Ba assertion `sync_project` trong `scripts/tests/test_spoke_sync_modules.py` kỳ vọng thêm `allow_stale_catalog=False`.

`python scripts/governance/compile_catalog.py --check` trả về in-sync. Không cần `--write`.

`python -m ccba_harness verify-patch` scoped (ruff check, ruff format, pytest freshness + sync + ADR matrix tests, catalog `--check`, matrix `--check`): **5/5 PASS**.
