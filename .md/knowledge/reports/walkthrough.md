# Báo Cáo Nghiệm Thu Hoàn Thành (Walkthrough) — Phát Hành `PR #846`
## Chore: Đăng Ký Spoke `SDS for Data Center` & Nâng Cấp 4 Windows Spokes Lên Chuẩn `ADR-0062`

> **Pull Request Đã Hợp Nhất (`--squash`):** [#846](https://github.com/vvChu/ccba-agent-platform/pull/846) (`ad4dc12c7b76d698ef728b5c0b641b1359dec37a`) | **Branch:** `chore/sync-windows-spoke-registry-adr0062` (`bb5f7d50` -> `9cc07fca`, rebased trên `4083d561`) | **Base:** `4083d561` | **Issue:** N/A  
> **Trạng thái chung:** ✅ **PR #846 MERGED, 12/12 ISOLATED TEST TARGETS PASS (TRIHT x2), 8/8 CI CHECKS PASS, 0 UNRESOLVED PR COMMENTS, 14/14 SPOKES CHUẨN ADR-0062**

---

## 1. Tổng Kết Thay Đổi Kỹ Thuật — PR `#846`

| Thành Phần | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Đăng ký Spoke mới `SDS for Data Center`** | [`spoke_registry.yaml`](../../../.md/data/spoke_registry.yaml) | Nâng tổng số spoke đăng ký từ `13` -> `14`; bổ sung bản ghi mã hóa RSA-2048 (`spoke_id`: `b35979ec03bf...`, `project_type`: `Thiết kế`, `archetype`: `project_delivery`) kèm `static_hash` theo chuẩn `ADR-0062` (không lộ đường dẫn cục bộ plain-text). | Verified |
| **2. Nâng cấp 4 Windows Spokes lên `ADR-0062`** | [`spoke_registry.yaml`](../../../.md/data/spoke_registry.yaml) | Cập nhật schema (`static_hash` + `archetype`, tách `last_sync` sang telemetry cục bộ) cho `2026-04 DH Viet Nhat` (`d4267226284a`), `IDOP-CCBA-WAY` (`4b6b5545f00e`), `vvc-second-brain` (`99ac46032a12`) và `Zalo_Bot_Free` (`a933f55f1eb8`), bảo toàn toàn bộ `13/13` `spoke_id` cũ và đạt `14/14` (`100%`) chuẩn `ADR-0062`. | Verified |

---

## 2. Bằng Chứng Kiểm Chứng Thực Nghiệm & Hậu Hợp Nhất (`ADR-0058` / `ADR-0062` / `ADR-0067`)

- **Kiểm định mật mã học & Rò rỉ Spoke (`ADR-0045` / `ADR-0062`):**
  - Toàn bộ `14/14` mục trong [`spoke_registry.yaml`](../../../.md/data/spoke_registry.yaml) có `spoke_id` và `static_hash` chuẩn SHA-256 `64` ký tự hex cùng ciphertext RSA-OAEP `256 bytes` khớp khóa công khai `2048-bit` tại [`registry_public_key.pem`](../../../.agents/resources/registry_public_key.pem) (`0` xóa, `0` trùng lặp).
  - `sanitize_review_diff.py --base origin/main --head bb5f7d50 --check`: `[PASS]` (`0` secrets), `check_spoke_leakage.py`: `0` violations, `door-triage .md/data/spoke_registry.yaml`: `PAVED_ROAD` (`0 LOC` logic diff).
  - *Phạm vi kiểm chứng trên Linux:* Khóa bí mật `~/.gemini/antigravity/keys/registry_private_key.pem` ([`decrypt_spoke_registry.py`](../../../scripts/spoke/decrypt_spoke_registry.py)) không tồn tại trên máy trạm Linux nên không giải mã plaintext; nội dung bên trong 5 payload cập nhật/mới dựa trên đối soát đồng bộ thực tế trên Windows (`sync_spoke.py --all --dry-run` và `spoke-status` báo `🟢 ACTIVE`).
- **Local TRIHT Cổng 0.1–0.3 trên PR `#846` (đã chạy trên `bb5f7d50` và chạy lại đầy đủ trên commit rebased `9cc07fca` trong `/home/vvc/ccba/wt-hub-846`):**
  - Cổng 0.1 & 0.3 (`check_release_cleanliness.py --phase pre/post`): `PASS` (`100%` Hermetic).
  - Cổng 0.2 (`run_isolated_tests.py --all --stress` trên `9cc07fca`): **12/12 targets PASS** (`ccba-ai` `5.38s`, `ccba-diagram` `0.30s`, `ccba-harness` `13.06s`, `ccba-legal-intel` `48.89s`, `ccba-maskara` `0.35s`, `ccba-notebooklm` `0.40s`, `ccba-ooxml` `2.56s`, `ccba-pdf-prep` `9.63s`, `ccba-qc-core` `1.11s`, `mdconverter` `2.36s`, `scripts` `15.57s`, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.61s` / total `30.26s`).
- **CI & Hậu hợp nhất trên `main` (`ad4dc12c`, `--squash`):**
  - `8/8` CI `SUCCESS` trên `9cc07fca`, `audit_pr_comments.py --pr 846` exit `0`, `reviewRequests` rỗng, đã gỡ nhãn `in-progress`, nhánh remote `chore/sync-windows-spoke-registry-adr0062` & worktree đã dọn sạch.
  - `compile_catalog.py --check`: `[OK]` (`100% in-sync`).

---

## 3. Lưu Trữ Phát Hành Trước Đó — Phân Tách Operations OS & Financial Ledger Trong `HUB-ADR-0060` (`PR #854` / `#849`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#854](https://github.com/vvChu/ccba-agent-platform/pull/854) (`6d1d3f5e7e6dc671b7da2531f7c522f8fc64df56`) | **Branch:** `docs/issue-849-adr-0060-erp-sor-separation` (`1b85482c`) | **Base:** `609afbc1` | **Issue:** [#849](https://github.com/vvChu/ccba-agent-platform/issues/849) (`CLOSED`)

- **Thành phần chính:** Cập nhật [`0060-4hub-federated-spokes-architecture.md`](../../../docs/adr/0060-4hub-federated-spokes-architecture.md) (Mục 1 & Mục 7 Amendment `2026-11-22`): phân tách cứng SOR điều hành (`IDOP-CCBA-WAY`) khỏi SOR sổ cái `31v` (`IBST_UNIFIED_ERP` trên `[Spoke PG16 loopback]`), ủy thác chi tiết vận hành Spoke về Spoke ADR-0011 (`Accepted`), đặt cầu Closed-Loop `IDOP → ERP` loopback-only (`127.0.0.1`), xác thực kép + taxonomy fail-closed SHA-256 (`IBST_IDOP_TAXONOMY_DIR`), và chuẩn hóa 5 trục tương tác IBST.
- **Nghiệm thu:** Grok Peer Audit Pass 2 `APPROVE_PLAN` (`risk_score: 2`, `0` blocking), `validate_docs.py` / `sync_hub_adr_matrix.py --check` (`61` ADRs) / `verify-patch --preset adr,doc` / `door-triage` (`ONE_WAY_DOOR`, `tradeoff_card_valid: true`) PASS, TRIHT Cổng 0.1–0.3 (`12/12` targets PASS, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.47s` / total `30.00s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 854` exit `0`, Issue `#849` `CLOSED` (`#issuecomment-7074500733`).

---

## 4. Lưu Trữ Phát Hành Trước Đó — Phát Hành Đợt Kép `PR #845` (`#844`) & `PR #848` (`#842`)

> **PR `#845` Đã Hợp Nhất (`--squash`):** [#845](https://github.com/vvChu/ccba-agent-platform/pull/845) (`76f48be83790a24ec28817b7f8d3f5e8f44086e8`) | **Issue:** [#844](https://github.com/vvChu/ccba-agent-platform/issues/844) (`CLOSED`) | **Branch:** `fix/issue-844-md-spoke-retrospective-gates` (`e2a42753`)  
> **PR `#848` Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#848](https://github.com/vvChu/ccba-agent-platform/pull/848) (`deeae22d7564f629f54298403cae9d24f0c71dd1`) | **Issue:** [#842](https://github.com/vvChu/ccba-agent-platform/issues/842) (`CLOSED`) | **Branch:** `feat/issue-842-ooxml-xlsx-seam` (`07c6549e`, rebased trên `76f48be8`)

- **Thành phần chính PR `#845`:** Bổ sung `resolve_target_adr_dir()`, `--adr-dir`, `--create-adr-dir` tại [`sync_hub_adr_matrix.py`](../../../scripts/sync_hub_adr_matrix.py); thêm `--profile generic-spoke` tại [`compact_session_learnings.py`](../../../scripts/governance/compact_session_learnings.py); nâng `/ccba-session-retrospective` `v1.7.2`; bổ sung 5 ca test tại [`test_sync_adr_matrix.py`](../../../tests/governance/test_sync_adr_matrix.py) và [`test_compact_session_learnings.py`](../../../tests/governance/test_compact_session_learnings.py).
- **Thành phần chính PR `#848`:** Triển khai deep subpackage `ccba_ooxml.xlsx` ([`xlsx/__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/__init__.py), PEP 562 lazy exports tại [`__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), [`calc.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py), [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`verify-ccba-ooxml/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md), [`test_xlsx.py`](../../../packages/ccba-ooxml/tests/test_xlsx.py), [`2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md`](../decisions/2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md)).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS` x2), `8/8` CI `SUCCESS` x2, `audit_pr_comments.py` exit `0`, `git cat-file -e 7259350d8020834c52ab88e4c5681e165612cc8b^{commit}` exit `0`, `compile_catalog.py --check` PASS, `test_verification_harness_dogfood.py` `5 passed`, `run_verify_ooxml.py` `6 passed`.

---

## 5. Lưu Trữ Phát Hành Trước Đó — Siết Chặt Startup `.env` ASGI & Neo `.ruff.toml` `conftest.py` (`PR #841`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#841](https://github.com/vvChu/ccba-agent-platform/pull/841) (`3d582834d0e652f7932318daa3cc83456dabe778`) | **Issue Đã Đóng:** [#840](https://github.com/vvChu/ccba-agent-platform/issues/840) (`CLOSED`) | **Branch:** `docs/issue-840-harden-asgi-env-conftest-ruff` (`f9e3e71f` -> `c3ce5041`) | **Base:** `a0282a9e`

- **Thành phần chính:** Bổ sung checklist startup `.env` & session active (`api.md`), bump `/ccba-code-review` `v1.8.1`, bump `/ccba-implement` `v1.2.2` neo `./conftest.py` và `urlunparse()`, re-anchor `verify-ccba-code-review` & `verify-ccba-implement` tại `a0282a9e`.
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 841` exit `0`, `test_verification_harness_dogfood.py` `5 passed`.

---

## 6. Lưu Trữ Phát Hành Trước Đó — Nâng Cấp `/ccba-book-compiler` v1.5.4 (`PR #817`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#817](https://github.com/vvChu/ccba-agent-platform/pull/817) (`1de529cb5a47274d6d570f310b87bff193274140`) | **Nhánh:** `feat/book-compiler-v154` (`ba079377` -> `1de529cb`) | **Base:** `170c04f3`

| Thành Phần | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Đồng bộ Kernel Skill `v1.5.4`** | [`.agents/skills/ccba-book-compiler/SKILL.md`](../../../.agents/skills/ccba-book-compiler/SKILL.md) | Nâng phiên bản `1.5.3` -> `1.5.4` (`6-Phase SOP v1.5.4`); đăng ký hai Spoke pipeline seams mới (`scripts/pipeline/book_staging_recovery.py`, `scripts/pipeline/book_link_verifier.py`) và cập nhật Bất biến #1 cho phép staging lũy đẳng từ thư mục `<Book_Stem>_MD` sạch hoặc khi `.epub`/`.pdf` gốc đã lưu trữ (đối ứng Spoke PR `vvChu/vvc-second-brain-scripts#144`). | Verified |
| **2. Đăng ký Parity Seams của Spoke** | [`tests/governance/test_workflow_script_parity.py`](../../../tests/governance/test_workflow_script_parity.py) | Bổ sung `scripts/pipeline/book_link_verifier.py` và `scripts/pipeline/book_staging_recovery.py` vào `SPOKE_SPECIFIC_SCRIPTS` để bảo đảm 100% kiểm định liên kết nội tuyến trong skill. | Verified |
| **3. Tái biên dịch Cổng Tài liệu Tĩnh** | [`docs/index.html`](../../../docs/index.html) | Cập nhật cổng web tĩnh qua `python3 scripts/governance/compile_skills_docs.py --write` và đối soát qua `--check`. | Verified |

- **TRIHT & Dual-Gate (`PR #817`):** Cổng 0.1 `PASS`, Cổng 0.2 **12/12 PASS** (`root-tests` `602 passed, 1 skipped, 10 deselected` in `27.93s`), Cổng 0.3 `PASS`; `8/8` CI `SUCCESS`, `audit_pr_comments.py` Exit Code `0` (`IC_kwDOQzfV088AAAABoRr_IA`), Grok Pass 3 `APPROVE_PLAN` (`3b5fd6e0-d35f-4560-973a-244bf9aa7245`, `risk_score: 2`, `0` blocking).
