# Walkthrough: Overhauled C-A-B Roadmap — Legal Ingestion Flywheel & Knowledge Migration

## 1. Executive Summary

This walkthrough documents the end-to-end execution of the overhauled **C-A-B roadmap** spanning across the Hub (`ccba-agent-platform`) and Spoke (`ccba-legal-knowledge`):

- **Phase C (Live Pilot Ingestion)**: Executed autonomous 1-command legal ingestion on Hub for **Nghị định 339/2026/NĐ-CP** (replacing 16/2022/NĐ-CP), generating verified sources (`.docx`, `.pdf`), 135 multi-line AST clause spans (`line_start < line_end`), 135 QA benchmark pairs, and updated registry graph.
- **Phase A (Sub-Gate 5.3 Upgrade & Batch Migration)**:
  - Upgraded Sub-Gate 5.3 (`_validate_legal_validity_and_in_force`) in `validate_legal_spoke.py` to the **Two-Tier In-Memory Transitive Engine** (multi-key canonical tokenization preserving document types, Tier 1 replacement DAG BFS detecting superseded active documents transitively, and Tier 2 statutory baseline safety floor).
  - Fixed substring matching precedence in `tvpl_parser.py` (`"hết hiệu lực một phần"` evaluated before `"hết hiệu lực"`).
  - Auto-loaded `title` and `cong_bao_number` from `metadata.yaml` in `ast_qa_generator.py` when omitted.
  - Rectified `TCVN-3890-2023` to `status: expired` with `relations.replaced_by: QCVN-10-2025-BCA`, enriched `replaces` relations for active decrees (`217/2026/NĐ-CP`, `207/2026/NĐ-CP`, `105/2025/NĐ-CP`, `QCVN 06:2022/BXD`).
  - Created `scripts/maintenance/migrate_legacy_spans.py` and batch-migrated all 24 legacy bundles plus `vn_hn_qd_38_2026_qd_ubnd`, achieving 100% multi-line spans across 4,926 clauses in 27 bundles.
- **Phase B (Remote Push & Pull Request)**:
  - Ran monorepo harness preset `ccba_harness verify-patch --preset code` (2/2 passed).
  - Validated Spoke 15-Gate CI (`CI=true python scripts/validate_legal_spoke.py` passed 15/15 with 0 errors).
  - Verified remote branches and PRs on Hub (PR #323) and Spoke (PR #10).

---

## 2. Phase-by-Phase Implementation Details

### Phase C: Autonomous Legal Ingestion of Nghị định 339/2026/NĐ-CP
- **CLI Command**:
  ```bash
  /home/vvc/ccba/ccba-agent-platform/.venv/bin/python scripts/ccba_platform_cli.py ingest-legal \
    "https://thuvienphapluat.vn/van-ban/Xay-dung/Nghi-dinh-339-2026-ND-CP-xu-phat-vi-pham-hanh-chinh-trong-linh-vuc-xay-dung-658189.aspx" \
    --slug "nghi_dinh_339_2026_nd_cp" \
    --category "01_vbpl" \
    --type "vbpl"
  ```
- **Generated Bundle Artifacts** (`legal_docs/01_vbpl/nghi_dinh_339_2026_nd_cp/`):
  - `sources/nghi_dinh_339_2026_nd_cp.docx` (41.0 KB)
  - `sources/nghi_dinh_339_2026_nd_cp.pdf` (968 B)
  - `nghi_dinh_339_2026_nd_cp.md` (30.5 KB, pure normative body stripped of administrative noise)
  - `clauses.json` (135 multi-line AST nodes, 0 single-line spans)
  - `qa_benchmark.json` (135 ground-truth pairs)
  - `metadata.yaml` & `index.md`
- **Registry Update** (`legal_registry.yaml`):
  - Registered entry `nghi_dinh_339_2026_nd_cp` with `relations.replaces: "16/2022/NĐ-CP"`.

---

### Phase A: Sub-Gate 5.3 Upgrade & Knowledge Migration

#### 1. Two-Tier Transitive Engine (`validate_legal_spoke.py`)
- **Multi-key Canonical Tokenization** (`_canonical_keys`):
  - Normalizes IDs and document numbers while preserving document types (`nd_cp`, `tt_bxd`, `qd_ubnd`, `tcvn`, `qcvn`).
  - Supports `:` for standards (`TCVN 3890:2023` $\rightarrow$ `tcvn_3890_2023`, `QCVN 06:2022/BXD` $\rightarrow$ `qcvn_06_2022_bxd`, `06_2022_bxd`).
- **Tier 1 (Replacement DAG BFS)**:
  - Traverses forward (`replaces`) and backward (`replaced_by`) edges starting from active documents.
  - If any document reachable in the replaced subgraph has `status: active`, it is flagged with a hard floor violation.
- **Tier 2 (Statutory Baseline Safety Floor)**:
  - Fallback lookup table `STATUTORY_BASELINE_REPEALED` prevents known repealed regulations (`10/2021/NĐ-CP`, `15/2021/NĐ-CP`, `175/2024/NĐ-CP`, `06/2021/NĐ-CP`, `136/2020/NĐ-CP`, `16/2022/NĐ-CP`, `QCVN 06:2020/BXD`) from remaining active.

#### 2. Gold Standard AST & QA Generator Upgrade
- In `ast_qa_generator.py`: Auto-loads `title` and `cong_bao_number` from `metadata.yaml` if omitted in the caller signature.
- In `tvpl_parser.py`: Fixed substring precedence so `"hết hiệu lực một phần"` is matched before `"hết hiệu lực"`.

#### 3. Registry & Bundle Rectifications
- `TCVN-3890-2023`: set to `status: expired`, `relations.replaced_by: QCVN-10-2025-BCA`, and updated `index.md` with explicit warning banner.
- Added missing `replaces` to active decrees:
  - `nghi_dinh_217_2026_nd_cp`: `replaces: ["15/2021/NĐ-CP", "175/2024/NĐ-CP"]`
  - `nghi_dinh_207_2026_nd_cp`: `replaces: "06/2021/NĐ-CP"`
  - `nghi_dinh_105_2025_nd_cp`: `replaces: "136/2020/NĐ-CP"`
  - `QCVN-06-2022-BXD`: `replaces: "QCVN 06:2020/BXD"`

#### 4. Batch Migration Tool (`scripts/maintenance/migrate_legacy_spans.py`)
- Created reusable batch migration script in Spoke.
- Migrated 24 legacy bundles + `vn_hn_qd_38_2026_qd_ubnd`. Added missing `index.md` to `vn_hn_qd_38_2026_qd_ubnd`.
- Result: **27 bundles** in `legal_docs/01_vbpl/` with **4,926 clauses** having 100% multi-line spans (`line_start < line_end`, 0 bad spans).

---

## 3. Verification & Compliance Record

| Gate / Test Suite | Scope | Result | Details |
|---|---|---|---|
| `ccba_harness verify-patch --preset code` | Hub Monorepo | ✅ PASS | 2/2 commands passed (Ruff check + Pytest tests/ -q) |
| `pytest tests/integration/test_validate_legal_spoke.py` | Spoke Integration | ✅ PASS | 8/8 tests passed in 0.42s (including DAG BFS integration test) |
| `CI=true python scripts/validate_legal_spoke.py` | Spoke 15-Gate CI | ✅ PASS | 15/15 Gates passed, 0 errors, 2 expected non-normative warnings |
| `python scripts/maintenance/migrate_legacy_spans.py --check-only` | Spoke Knowledge Spans | ✅ PASS | 27/27 bundles, 4,926 clauses, 0 bad spans |
| Scoped Ingestion 15-Gate Check | Hub CLI $\rightarrow$ Spoke Bundle | ✅ PASS | Pilot bundle `nghi_dinh_339_2026_nd_cp` passed scoped validation with 0 errors |

---

## 4. Remote Synchronization & Pull Requests

- **Hub Repository (`ccba-agent-platform`)**:
  - Branch: `feat/zero-touch-legal-ingestion-flywheel`
  - PR: [#323](https://github.com/vvChu/ccba-agent-platform/pull/323)
- **Spoke Repository (`ccba-legal-knowledge`)**:
  - Branch: `feat/ingest-10-2021-nd-cp`
  - PR: [#10](https://github.com/vvChu/ccba-legal-knowledge/pull/10)
