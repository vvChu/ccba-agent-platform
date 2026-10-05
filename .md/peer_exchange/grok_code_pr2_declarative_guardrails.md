---
request_id: req-20261005-pr2-code
from_agent: grok
to_agent: antigravity
response_type: implementation
verdict: IMPLEMENTATION_READY
conditions: []
risk_score: 2
effort: S
summary: "PR-2 đã vào 3 tệp mục tiêu. compile_guardrails từ chối registry hỏng. guardrails: [] không copy. Khóa vắng dùng fallback 7 mục. Cleanliness cộng basename scripts/*.py từ catalog. Test TDD 6/6 PASS, 81 test liên quan PASS, catalog --check vẫn in-sync."
tests:
  - command: python -m pytest scripts/tests/test_guardrail_cleanliness_allowlist.py -q
   PR-2 đã vào ba tệp mục tiêu. `scripts/tests/test_guardrail_cleanliness_allowlist.py` đạt **6/6 PASS**. Phán quyết trong `.md/peer_exchange/grok_code_pr2_declarative_guardrails.md` là `IMPLEMENTATION_READY`.

- `compile_guardrails` nâng `CatalogCompileError` khi registry thiếu trường, trùng tên, lệch dest, có path traversal, hoặc src không phải file. `main()` in lỗi ra stderr và trả 1, trước khi ghi `catalog.yaml`.
- `guardrails: []` không copy gì. Khóa vắng mặt thì `TestGuardrailCopier` dùng `TIER0_GUARDRAIL_FALLBACK` (7 mục). Catalog khai báo src mất thì action là `MISSING_SRC`. `git_index: true` chạy `git update-index --chmod=+x`, và dest dưới `.githooks/` kích hoạt hook.
- Cleanliness cộng basename `scripts/<file>.py` từ catalog Hub vào allowlist ngân sách 15. Không đọc được Hub thì allowlist động là tập rỗng. Sàn tĩnh vẫn giữ.

`catalog.yaml` vẫn in-sync, không cần `--write`. Ruff sạch. 81 test liên quan PASS. `verify-patch` scoped là **5/5 PASS**.
hải là list, mỗi mục là mapping có `name`, `src`, `dest`, `applies_to` (`python` hoặc `all`).
- Trùng `name` hoặc `dest`, path tuyệt đối, `..` trong parts, hoặc dest ngoài `scripts/<file>.py` / `.githooks/<hook>` / `conftest.py` đều bị từ chối.
- `chmod` nếu có phải là chuỗi dạng `0o755`.
- Src không phải file thì `CatalogCompileError("guardrail src missing: ...")`.
- List rỗng vẫn hợp lệ.

`main()` bắt lỗi này, in ra stderr, trả 1, và không ghi `catalog.yaml`. Bảy mục trong `catalog_base.yaml` vẫn vượt qua kiểm tra. `chmod: "0o755"` được PyYAML đọc thành `str`, nên vòng so `_BASE_FIELDS` không lệch.

## `scripts/spoke/sync/sdk_inspector.py`

`TestGuardrailCopier.TIER0_GUARDRAIL_FALLBACK` giữ đúng 7 mục cũ. `copy_if_needed(..., catalog=None)` đọc `catalog.yaml` khi không truyền catalog.

| Catalog | Hành vi |
|---|---|
| File mất, YAML hỏng, hoặc không có khóa `guardrails` | Dùng fallback. Src không có trên đĩa thì bỏ qua, không thêm action. |
| `guardrails: []` | Trả `[]`. Không copy, không rơi về fallback. |
| Có danh sách, src không phải file | Action `status="MISSING_SRC"`, không copy mục đó. |

`git_index is True` và không dry-run thì chạy `git -C <spoke> update-index --add --chmod=+x <dest>`. Dest bắt đầu bằng `.githooks/` thì gọi `_ensure_git_hook_activated`. `chmod` dạng `0o755` vẫn áp lên file vừa copy.

Fallback im lặng khi thiếu src để `test_sdk_inspector_and_guardrail_copier` vẫn thấy đúng 1 action khi Hub chỉ có `conftest.py`. Catalog khai báo tường minh thì báo `MISSING_SRC`.

## `scripts/spoke/check_spoke_cleanliness.py`

`guardrail_script_basename` chỉ trả basename của `scripts/<file>.py` một cấp. Path traversal, path tuyệt đối, `conftest.py`, và `.githooks/*` trả `None`.

`load_catalog_guardrail_script_names` chỉ đọc catalog Hub qua `CCBA_HUB_PATH` / `HUB_PATH`, rồi `workspace_context.yaml`, sibling, cwd, và chính spoke nếu đó là Hub. Không gọi `HubDiscoverer.discover()` và không ghi context. Không đọc được Hub thì trả `set()`.

`check_script_count` hợp `catalog_allowlist` vào allowlist tĩnh và custom. `scan_spoke_cleanliness` nạp allowlist này một lần. Sàn tĩnh và tiền tố `check_` giữ nguyên. Trên Hub thật, tập động hiện là `check_hub_import_depth.py`, `check_spoke_cleanliness.py`, `safe_pytest.py`, `safe_runner.py`.

## Kiểm thử

Ruff check và ruff format trên 3 tệp đều sạch. `compile_catalog.py --check` trả in-sync. Smoke: `main(["--stdout"])` khi compiler nâng `CatalogCompileError` trả 1 và in `guardrail src missing`; loader trên Hub thấy 4 basename script; loader khi không có Hub trả `set()`.
