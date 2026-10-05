# 0062. Declarative Synchronization Registry, Fail-Closed Catalog Freshness Gate, and Topological Package Discovery

* **Status:** Accepted
* **Date:** 2026-10-05
* **Deciders:** CCBA Platform Core Team, Lead Architect (Antigravity), Peer Reviewer (Grok)
* **Consulted:** ADR 0044 (Spoke Package Bootstrap), ADR 0047 (Catalog Manifest Compiler), ADR 0051 (Hub-Spoke Sync Hardening), ADR 0058 (Deterministic Hard Completion Lock), ADR 0061 (Platform-Aware KISS v2.0)

---

## Context & Problem Statement

Đồng bộ Hub sang Spoke trước ADR-0062 dựa vào ba danh sách gắn cứng và một cảnh báo có thể bị nuốt:

1. **Guardrail registry gắn cứng.** `TestGuardrailCopier` giữ một danh sách tĩnh các tệp `conftest.py`, `safe_pytest.py`, `safe_runner.py`, linter Spoke và git hooks. Thêm một guardrail mới mà quên sửa Python thì Spoke không nhận tệp đó.
2. **Thứ tự package gắn cứng.** `PACKAGE_TOPOLOGY_ORDER` không đọc `packages/*/pyproject.toml`. Package mới không xuất hiện trong thứ tự cài editable, hoặc xuất hiện sai bậc phụ thuộc.
3. **Catalog có thể lệch mà sync vẫn ghi.** `check_catalog_in_sync()` không so khóa `guardrails`. Khối kiểm tra trong `sync_spoke_bundle` bọc `except Exception: pass` và chỉ in cảnh báo. `--apply` vẫn copy skill, workflow và guardrail từ một `catalog.yaml` đã cũ.

Hệ quả: Spoke nhận bundle không khớp frontmatter và `catalog_base.yaml` trên Hub, trong khi người vận hành tưởng rằng sync đã dùng manifest mới nhất.

---

## Decision Outcome

Ban hành **HUB-ADR-0062** với ba quyết định gắn vào manifest biên dịch (ADR 0047) và luồng `sync_spoke`.

### 1. Declarative Synchronization Registry

- `catalog_base.yaml` là nguồn khai báo của các khóa tĩnh, trong đó có `guardrails`.
- Mỗi guardrail khai báo tối thiểu `name`, `src`, `dest`, `applies_to`. Hook thực thi thêm `chmod` và `git_index`.
- `compile_catalog_dict()` biên dịch khóa `guardrails` vào `catalog.yaml` qua `compile_guardrails()`. Src không tồn tại trên đĩa được cảnh báo, không bị bỏ khỏi manifest.
- `check_catalog_in_sync()` so các khóa nền bằng dữ liệu đã parse, không so chuỗi YAML. Danh sách khóa là `_BASE_FIELDS`, gồm `hub_path`, `hub_repo`, `notebook_ids`, `bundles`, `rules`, `knowledge`, và `guardrails`. Lệch thứ tự phần tử là lệch thật.
- `TestGuardrailCopier` đọc `catalog.yaml`. Khi khóa `guardrails` vắng, copier dùng danh sách Tier-0 fallback tương thích ngược (7 mục: conftest, safe_pytest, safe_runner, hai linter Spoke, pre-commit, pre-push).

### 2. Fail-Closed Catalog Freshness Hard Gate

Cảnh báo không chặn trên `--apply` được thay bằng cổng đóng khi lỗi.

- Hằng số duy nhất: `CATALOG_RECOMPILE_COMMAND = "python scripts/governance/compile_catalog.py --write"`.
- `assess_catalog_freshness(hub_root, spoke_root, dry_run=False, allow_stale_catalog=False) -> str | None` chạy sau khi `catalog.yaml` đã tồn tại và trước `_sync_full_bundle` / `_sync_single_item`.
- Catalog khớp: trả về `None`.
- `dry_run=True` và catalog lệch: in `WARNING: Hub catalog.yaml is out of sync` ra stderr, trả về `None`. Preview không ghi Spoke.
- `dry_run=False` và catalog lệch, không có cờ vượt: in `ERROR: Cannot apply sync because Hub catalog.yaml is out of sync` cùng `CATALOG_RECOMPILE_COMMAND`, trả về `"catalog_stale"`. `sync_spoke_bundle` trả mã 1 ngay. `--force` không mở cổng này.
- `allow_stale_catalog=True`: in `[Sync] AUDIT: CATALOG_STALE_BYPASS` và trả về `None`, kể cả khi `check_catalog_in_sync` ném exception. Sync tiếp tục trên catalog đang có.
- Khối `except Exception` kiểm tra `allow_stale_catalog` trước. Không có cờ và `not dry_run` thì trả về `"catalog_stale"`. Không còn `except Exception: pass`.
- CLI `build_parser()` có `--allow-stale-catalog` (`store_true`, mặc định `False`). Giá trị đi vào `sync_project()`, `SpokeSynchronizer.sync()`, `sync_spoke_bundle()`, và `sync_all_spokes()`. Batch dừng các Spoke còn lại khi halt reason là `catalog_stale`.
- Catalog đã tươi thì sync không cần quyền ghi lên Hub. Pull Hub đứng trước cổng và có thể làm catalog tươi lại trước khi cổng chạy.

### 3. Topological Package Discovery

- `discover_package_topology(hub_root)` đọc `packages/*/pyproject.toml` và sắp thứ tự cài bằng Kahn's algorithm.
- Neo cố định: `ccba-harness` ở vị trí 0, `ccba-ai` ở vị trí 1, khi các package đó có mặt.
- Phụ thuộc nội bộ monorepo được nhận qua tên project và tên thư mục. Vòng lặp hoặc lỗi đọc làm hàm trả về `DEFAULT_PACKAGE_TOPOLOGY_ORDER`.
- Hàm chỉ sắp một tập package đã chọn. Nó không tự quyết định package nào được cài cho từng archetype.

---

## Consequences & Verification

- **Tích cực:** Guardrail mới và lệch `catalog_base.yaml` đi cùng một lần `compile_catalog.py --write`. `--apply` không ghi Spoke từ catalog lệch. Dry-run và cờ vượt khẩn cấp vẫn có đường đi, cờ vượt để lại dòng audit.
- **Chi phí:** Hub maintainer phải biên dịch lại `catalog.yaml` trước khi Spoke chạy `--apply`. Fixture test dùng catalog viết tay phải truyền `allow_stale_catalog=True` hoặc bỏ qua cổng, vì catalog đó không phải đầu ra compiler.
- **Kiểm định:**
  - `python -m pytest scripts/tests/test_catalog_freshness_gate.py`
  - `python -m pytest scripts/tests/test_declarative_sync_registry.py`
  - `python scripts/governance/compile_catalog.py --check`
---
