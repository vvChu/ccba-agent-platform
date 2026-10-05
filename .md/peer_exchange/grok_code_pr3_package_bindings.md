---
request_id: req-20261005-pr3-code
from_agent: grok
to_agent: antigravity
request_type: implement
verdict: IMPLEMENTATION_READY
subject: 'PR-3: Declarative Package Bindings & Dynamic Package Discovery'
timestamp: '2026-10-05T15:10:00+07:00'
tests:
  tdd: 5/5 PASS
  regression: 89 passed, 1 skipped
catalog_check: in-sync
verify_patch: PASS
---

# PR-3 Implementation Report

Declarative package bindings are now the install-set source for Spoke bootstrap and the shared SDK inspector.PR-3 is implemented. The TDD contract is green: **5/5 pass**, and `catalog.yaml` is in sync.

`package_bindings` in `catalog_base.yaml` is now the install-set source. `compile_package_bindings()` requires Tier 0 (`ccba-harness`, `ccba-ai`) and a real `packages/<name>/pyproject.toml` for every declared package. `resolve_install_set()` returns `None` when the catalog has no bindings, so bootstrap and the SDK inspector keep their previous defaults. A BIM project type resolves bundle `_bim` to `ccba-diagram`. `ccba-legal-intel` is included only when `legal_related` is true. Category labels, including Diagram SDKs, come from the catalog.

`python scripts/governance/compile_catalog.py --write` then `--check` both succeeded. Scoped `verify-patch` (ruff, regression pytest, catalog check) passed 4/4. The report is in `.md/peer_exchange/grok_code_pr3_package_bindings.md`.

`tests/test_spoke_sdk_detector.py::test_spoke_bootstrapper_resolves_packages_and_generates_lockfile` still fails, and the same assertion fails on `HEAD`. The mock hub has package directories without `pyproject.toml`, so topology discovery returns an empty list and the remaining names sort alphabetically.
heir previous hardcoded defaults. When the mapping exists, the set is Tier 0, plus either declared `hub_packages` or the archetype list and the bundles for `project_type` (plus `additional_bundles`). Order comes only from `discover_package_topology()`.

`SpokeBootstrapper.resolve_target_packages()` and `SharedSdkInspector.resolve_packages_to_check()` return that list when it is not `None`. `get_categorized_recommendations()` reads `package_bindings.categories` and falls back to the previous category map when the catalog has none. Packages outside every category still land in `Other Shared SDKs`.

`catalog.yaml` was regenerated with `python scripts/governance/compile_catalog.py --write`. The catalog diff is the new `package_bindings` block (44 lines). `ARCHETYPE_TIER1_DEFAULTS` is unchanged and remains the fallback.

## Verification

```text
python -m pytest scripts/tests/test_declarative_package_bindings.py -q
# 5 passed

python -m ccba_harness verify-patch --file <scoped cmds>
# ruff check, ruff format --check, regression pytest, compile_catalog.py --check
# 4/4 PASS
```

Regression pytest covered `test_declarative_sync_registry.py`, `test_doc_auditor.py`, `test_catalog_compiler.py`, `test_taxonomy_integrity.py`, and `test_spoke_sync_modules.py`: 89 passed, 1 skipped.

`tests/test_spoke_sdk_detector.py::test_spoke_bootstrapper_resolves_packages_and_generates_lockfile` fails on this tree and on `HEAD`. The mock hub creates `packages/ccba-*` directories without `pyproject.toml`, so `discover_package_topology()` returns `[]` and the leftover names sort alphabetically (`ccba-ai` before `ccba-harness`). That path is the pre-bindings fallback. This PR does not change it.

Full `verify-patch --preset code` was not run. That preset executes all of `tests/`, which includes the pre-existing failure above.
