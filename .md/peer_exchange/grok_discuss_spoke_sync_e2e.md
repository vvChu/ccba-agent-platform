---
request_id: req-discuss-spoke-sync-e2e-001
verdict: REVISE_PLAN
conditions:
- id: COND-E2E-01
  description: 'Cấm chạy `sync_spoke.py --apply` trần trên Hub sống. Bắt buộc `CCBA_SKIP_GIT_PULL=1` và `CCBA_HUB_PATH` trỏ Hub. Dùng `--sync-item <skill có thật trong catalog>` để vào pha rule+AGENTS.md mà không ghi `.md/data/spoke_registry.yaml`. Cấm `--all`, `--bootstrap`, `--pull-assets`. Dry-run không được coi là vô hại nếu thiếu `CCBA_HUB_PATH`: `HubDiscoverer.discover()` vẫn ghi `hub_path` tương đối vào workspace context của sandbox.'
  blocking: true
  source_profiles: [arch_audit]
- id: COND-E2E-02
  description: 'Sandbox tại `/tmp/ccba-e2e-spoke` hoặc `.md/scratch/e2e_spoke_sandbox/` (đã gitignore). `hub_path` tương đối hoặc bỏ trống khi đã có `CCBA_HUB_PATH`. Cấm đường dẫn tuyệt đối trong yaml. Workspace context phải tồn tại; `project_type` bắt buộc nếu chạy full sync, không bắt buộc nếu chạy `--sync-item`. Sau dry-run, assert đĩa chưa mất file legacy.'
  blocking: true
  source_profiles: [arch_audit]
- id: COND-E2E-03
  description: 'Mở fixture đúng các ca đang đỏ: anchor `code_quality.md#…`, anchor `execution_guardrails.md` khác tiền tố `#19-`, backtick trần, symlink gãy (`lexists`), thư mục rules read-only, file legacy dưới `docs/rules/` và thư mục con. Quét toàn cây sandbox tìm tên monolithic còn sót. Lần `--apply` thứ hai phải idempotent. Fleet (`vvc_working_space`, Consulting, Legal) chỉ chạy sau khi các ca này xanh hoặc được sửa trong `graduation.py`.'
  blocking: true
  source_profiles: [arch_audit]
- id: COND-E2E-04
  description: 'Trước fleet sync, sửa hai lỗ trong `scripts/spoke/sync/graduation.py`: `_cleanup_legacy_monolithic_rules` nuốt `OSError` và vẫn báo `REMOVED`; `Path.exists()` bỏ qua symlink gãy. Bảng `LEGACY_RULE_LINK_MIGRATIONS` phải đưa anchor cũ của `code_quality.md` và mọi anchor của `execution_guardrails.md` sang file phân rã, hoặc fail-closed khi còn tên monolithic trong liên kết.'
  blocking: true
  source_profiles: [arch_audit]
- id: COND-E2E-05
  description: '`RULE-5.12` trong session learnings là Venv Tooling / verify-patch, không phải Spoke Rule Cleanliness. Giữ nguyên tên đã persist. `GATE-04` cleanliness không chứng minh Zero-Zombie. Canary hiến pháp phải là heading `##` riêng và một bullet Core Invariants riêng.'
  blocking: false
  source_profiles: [arch_audit]
risk_score: 4
summary: Phân rã 4 file Layer 2 đã dưới trần 24.000 byte và AST ≤ 50 dòng. Kế hoạch E2E CLI như viết sẽ ghi registry Hub, có thể git pull Hub, và bốn gate chưa bắt anchor zombie lẫn báo cáo xóa giả. Sửa runbook theo COND-E2E-01..03 rồi mới chạy sandbox. Chưa sync Spoke thật.
---

# Thẩm định phân rã Layer 2 và kế hoạch E2E `sync_spoke.py`

Verdict **`REVISE_PLAN`**. Điểm rủi ro **4/5**.

Phân rã đã merge (PR #553 / #554) đạt trần cứng Antigravity và đạt khóa độ dài hàm. Kế hoạch sandbox trong mục 2, nếu chạy đúng chữ, chưa an toàn với Hub và chưa đủ sức bắt lỗi di trú liên kết. Spoke thật (`vvc_working_space`, Consulting, Legal) chưa được phép sync.

## Đối soát claim đã merge

Đã đo byte trên cây làm việc hiện tại (`wc -c`):

| File | Byte | Trần 24.000 |
|---|---:|---|
| `docs/rules/code_quality_standards.md` | 16.272 | Đạt |
| `docs/rules/code_quality_verification.md` | 18.198 | Đạt trần cứng. Vượt dải mục tiêu 18 KB (18.000 byte) 198 byte |
| `docs/rules/execution_runtime_guardrails.md` | 11.227 | Đạt |
| `docs/rules/execution_coordination_guardrails.md` | 14.812 | Đạt |
| `docs/rules/git_conventions.md` | 1.980 | Đạt |
| `.github/bugbot-rules.md` | 4.045 | Đạt |

`docs/rules/` không còn `code_quality.md` hay `execution_guardrails.md`. Hub hết zombie monolithic. Spoke chỉ hết zombie sau một lần sync thành công.

`scripts/spoke/sync/graduation.py`: mọi hàm top-level có `end_lineno - lineno + 1` ≤ 50. Hàm dài nhất trong file này là `supersede_graduated_spoke_docs` (45) và `sync_layer2_rules` (41). Khóa `test_coordinator_ast_function_length_compliance` vẫn là hàng rào đúng.

`.md/knowledge/session_learnings.md` đang 10.187 byte, dưới 10 KiB (10.240).

**Tên RULE-5.12 trong đề bài lệch SSOT.** Bản đang persist ở `session_learnings.md` và Entry 48 là *Venv Tooling Execution Parity & Non-Test Module Verify-Patch Pattern*. Dọn zombie nằm trong **RULE-1.25**, và phạm vi code hẹp hơn câu chữ đề bài. Giữ nguyên tên RULE-5.12. Không viết lại tri thức cho khớp tiêu đề mới.

`CORE_LAYER2_RULES` đúng 6 đường dẫn (4 file phân rã + `git_conventions.md` + `.github/bugbot-rules.md`). `LEGACY_MONOLITHIC_RULES` đúng 2 basename.

## 1. `graduation.py` — rủi ro thật

### Phạm vi xóa hẹp hơn mô tả

`_cleanup_legacy_monolithic_rules` (`graduation.py` khoảng dòng 180–206) chỉ xóa:

`<spoke>/.agents/rules/code_quality.md`  
`<spoke>/.agents/rules/execution_guardrails.md`

Nó không đụng `docs/rules/`, không đụng thư mục con, không đụng file cùng tên nằm chỗ khác. Câu “xoá ở `.agents/rules/` và `docs/rules/`” không khớp code. Zero-Zombie của fleet là Zero-Zombie đúng hai basename phẳng trong `.agents/rules/`.

### Báo `REMOVED` khi xóa thất bại

Khi `dry_run` là false, `unlink()` nằm trong `try/except OSError: pass`. Action vẫn là `status: REMOVED`. Trên Linux, file mode `0444` trong thư mục ghi được vẫn xóa được. Thư mục `0555`, file đang khóa, hoặc basename là directory thì `unlink` thất bại, file còn, log vẫn ghi đã xóa. Trên Windows, attribute read-only thường rơi vào cùng nhánh nuốt lỗi.

`Path.exists()` trả false với symlink gãy. Symlink gãy tên `code_quality.md` sống sót và không có dòng audit. Symlink lành trên POSIX: `unlink` gỡ link, không gỡ target. An toàn với target. Nguy hiểm nếu cả thư mục `.agents/rules` là symlink tới `docs/rules` của Hub và Hub còn file legacy: cleanup sẽ gỡ file trên Hub. Hiện Hub đã không còn hai file đó, nên mũi này đang ngủ. Sandbox không được trỏ `.agents/rules` vào Hub.

Path separator của bước xóa đi qua `pathlib`. Không có regex `\\` vs `/` ở bước xóa. Rủi ro OS nằm ở quyền file và symlink, không nằm ở dấu gạch.

### Di trú liên kết — đã chạy thử

`normalize_spoke_agents_links` trên các mẫu sau cho ra:

| Đầu vào | Đầu ra thực tế |
|---|---|
| `](docs/rules/code_quality.md)` | `](rules/code_quality_standards.md)` |
| `](docs/rules/execution_guardrails.md)` | `](rules/execution_runtime_guardrails.md)` |
| `](…execution_guardrails.md#19-atomic-micro-pr-pipeline--read-only-advisory-ai-review-guardrail)` | sang `execution_coordination_guardrails.md`, giữ anchor |
| `](…execution_guardrails.md#19-atomic)` | sang coordination, giữ anchor |
| `](../docs/rules/code_quality.md#10-4)` | `](rules/code_quality.md#10-4)` — file đã bị xóa |
| `](rules/execution_guardrails.md#11-hooks)` | giữ nguyên tên monolithic |
| `](docs\rules\code_quality.md)` | giữ nguyên, regex chỉ nhận `/` |
| `` `docs/rules/code_quality.md` `` | giữ nguyên, không phải markdown link |

Anchor `#19-…` là nhánh duy nhất của `execution_guardrails.md` được đưa sang coordination. Mọi anchor khác, kể cả mục 11 (hooks, đang nằm ở runtime), thành link tới file sắp bị xóa. Anchor của `code_quality.md` không có bảng chia standards/verification. Nội dung cũ mục 10 và 17 đang ở `code_quality_verification.md`; link có anchor bị rewriter tổng (`docs/rules/` → `rules/`) giữ basename cũ.

Hàm chỉ chạy trên `.agents/AGENTS.md` qua `merge_agents_constitution`. README, CONTEXT, INDEX, skill riêng của Spoke không được viết lại. `audit_spoke_markdown_links` chỉ đọc `.agents/AGENTS.md` và `.md/INDEX.md`, và full sync bỏ qua list lỗi trả về (`coordinator.py` dòng 984). `--verify` mới làm `verify_spoke` fail khi còn link gãy. Kế hoạch mục 2 không truyền `--verify`.

Test `test_layer2_rules_sync_and_agents_link_normalization_idempotency` xóa `code_quality.md` và kiểm link đã là tên mới. Nó không đặt `execution_guardrails.md`, không đặt anchor cũ, không đặt symlink gãy, không đặt `OSError`. Hành vi bảng `LEGACY_RULE_LINK_MIGRATIONS` đang không có test đặc tả.

### Dirty tree, thiếu git, read-only

`GitWorkingTreeGuard.is_git_repo` chỉ nhìn `<spoke>/.git` và `<spoke>/../.git`.

- `/tmp/ccba-e2e-spoke` không có git: guard coi là sạch, `--apply` đi tiếp. Đây là hợp đồng hiện tại.
- Spoke có git, `.agents/` dirty: `--apply` thoát 1, trừ khi `--force`. Dry-run bỏ qua guard.
- Sandbox hai cấp dưới Hub (`.md/scratch/e2e_spoke_sandbox`): parent là `scratch`, không có `.git`, guard không thấy repo Hub. May là `.gitignore` đã có `.md/scratch/`, nên file sandbox không hiện trong `git status` của Hub. Vẫn không được dùng thư mục này làm chỗ symlink rules về Hub.

### Bảo toàn hiến pháp — hợp đồng thực

`merge_agents_constitution` thay mọi heading `##` mà Hub cũng có bằng bản Hub, rồi nối các heading `##` chỉ Spoke mới có. Riêng `## Core Invariants` được merge theo khóa chuẩn hóa. Hub `.agents/AGENTS.md` có đúng hai heading: `## Core Invariants` và `## Progressive Disclosure`.

Canary sống sót khi là:

- một bullet Core Invariants có khóa không trùng Hub, và
- một heading `##` riêng (`## Agent skills`, `## Issue Tracker`, `## Domain Docs`).

Đoạn Spoke viết thêm bên trong `## Progressive Disclosure`, hoặc heading `###` dưới heading Hub, bị thay bằng bản Hub. Test hiện có đã khóa canary `## Agent skills` và bullet `Spoke Custom Invariant`.

## 2. Kế hoạch 4 gate — chỗ thủng và chỗ đụng Hub

`python scripts/sync_spoke.py --spoke <dir> --dry-run` và `--apply` là CLI thật (`scripts/sync_spoke.py` → `run_spoke_sync_cli`). Thiếu cả hai cờ thì stdin không phải TTY sẽ dừng sau preview. Phần này của kịch bản đúng.

Full sync không tới pha rule nếu thiếu `project_type` trong workspace context (`_resolve_required_bundles` trả lỗi, exit 1). Bốn gate khi đó không chạy. Đề bài chưa khai `project_type`.

Full `--apply` còn làm bốn việc ngoài rule:

1. `git pull` Hub (`pull_hub=True`, không có cờ CLI tắt). Chỉ `CCBA_SKIP_GIT_PULL=1` chặn được.
2. `SpokeRegistrar.register` ghi `.md/data/spoke_registry.yaml` của Hub (file tracked, payload mã hóa có đường dẫn tuyệt đối của sandbox) và heartbeat dưới `.md/telemetry/`. `sandbox_mode: true` vẫn ghi registry; cờ sandbox chỉ nằm trong blob.
3. Copy skill/workflow theo bundle, guardrail, và nhánh legal. `additional_bundles` chỉ nới tập skill. Tên bundle lạ được nhét thêm vào danh sách, không đổi cleanup rule.
4. `HubDiscoverer`, khi chưa có `hub_path` và không có `CCBA_HUB_PATH`, ghi `hub_path` tương đối vào yaml của Spoke kể cả dry-run.

`--sync-item <tên skill có trong catalog>` vẫn cần workspace context và vẫn pull Hub nếu thiếu env, nhưng không đăng ký registry, không supersede draft, không copy cả bundle. Constitution + `sync_layer2_rules` chạy sau khi skill đó copy thành công. Item không có trong catalog thì thoát 1 trước khi đụng rule. Đây là cửa E2E đúng cho câu hỏi zombie rule.

### Bốn gate đã nêu

| Gate | Sức bao phủ thực |
|---|---|
| GATE-01 presence/absence | Đủ cho 6 file đích và 2 basename phẳng trong `.agents/rules/` trên happy path Linux. Thiếu symlink gãy, read-only, `docs/rules/`, nested path. Dry-run phải assert file legacy còn trên đĩa. Bảng tóm tắt đếm `DEPRECATED_REPLACED`, không đếm `REMOVED`, nên đừng grep câu “dọn dẹp cũ”. |
| GATE-02 link parity | Xanh giả nếu fixture chỉ có link trần không anchor. Phải gồm 8 mẫu ở bảng trên. Quét cả cây, không chỉ `AGENTS.md`. |
| GATE-03 constitution | Đúng nếu canary là heading `##` riêng và một bullet invariant riêng. Thêm một `###` dưới Progressive Disclosure làm chứng tích cực rằng merge hiện thay cả section Hub. |
| GATE-04 `check_spoke_cleanliness.py` | Exit 0 gần như rỗng khi sandbox không có `scripts/`. Scanner không đọc `.agents/workspace_context.yaml`, không đo 24 KB, không tìm tên zombie. Đường dẫn `/home/...` chỉ bị bắt nếu nằm ở `workspace_context.yaml` gốc Spoke hoặc `.md/workspace_context.yaml`. Gate này không chứng minh Zero-Zombie. |

### Edge case cần thêm, theo mức

Bắt buộc trong sandbox:

- Dry-run rồi apply rồi apply lần hai (idempotent: không còn `REMOVED`, 6 rule `UNCHANGED`, canary còn nguyên byte).
- Anchor zombie như bảng thực nghiệm.
- `execution_guardrails.md` legacy cạnh `code_quality.md` (test unit hiện chỉ có file thứ nhất).
- Symlink gãy cùng tên legacy.
- Một thư mục `.agents/rules` mode `0555` trên Linux, hoặc file read-only trên Windows: status action phải khớp đĩa. Hành vi hôm nay là lệch. Ca này được phép đỏ.
- Quét `rg -n 'code_quality\.md|execution_guardrails\.md'` trên sandbox sau apply.
- `CCBA_SKIP_GIT_PULL=1` và hash `spoke_registry.yaml` trước/sau phải trùng nếu lỡ gọi full apply.

Nên có, không chặn sandbox:

- Backslash markdown một dòng: được phép không rewrite, cấm rewrite hỏng thành path lẫn dấu.
- Spoke không `git init`: apply vẫn chạy. Ghi nhận là hợp đồng, không phải lỗi.
- Spoke có git, `.agents` dirty, không `--force`: exit 1, đĩa không đổi. Có `--force`: apply tiếp.
- `additional_bundles` một tên có thật và một tên lạ: rule cleanup vẫn chạy, skill lạ không tạo file rule cũ.
- Rollback: full apply mặc định backup `.agents/`. Một ca riêng khôi phục snapshot phải thấy lại file legacy. Ca `--sync-item` có thể `--no-backup`.

### Chỗ đặt sandbox

`.md/scratch/` đã nằm trong `.gitignore` (dòng 137). `check_spoke_cleanliness.py` của Hub chỉ đi `scripts/` và `src/`, không đi vào scratch. Đặt sandbox ở đó không làm bẩn commit Hub và không làm cleanliness Hub đỏ.

Ưu tiên `/tmp/ccba-e2e-spoke`. Nó nằm ngoài worktree, guard git không bám nhầm `.git` của Hub, và một symlink lỡ tay khó xóa nhầm file Hub hơn. Nếu dùng `.md/scratch/e2e_spoke_sandbox/`, export `CCBA_HUB_PATH`, không symlink `.agents/rules` về Hub, không commit sandbox.

Cấm đặt sandbox ngay dưới root Hub (`<hub>/e2e_spoke`). Parent có `.git`, mọi file untracked trong `.agents/` làm `--apply` thoát 1, và thư mục không nằm trong ignore.

## 3. Phán quyết

**Sandbox được chạy** sau khi runbook đã gắn COND-E2E-01 và COND-E2E-02, với fixture của COND-E2E-03. Ca anchor và ca unlink-fail được phép đỏ. Đỏ là kết quả hợp lệ của vòng này. Xanh trên fixture chỉ có link trần là xanh giả.

**Fleet chưa được chạy.** Điều kiện mở fleet là COND-E2E-04 đã vào `graduation.py` và sandbox đã xanh các ca hiện đang đỏ, gồm idempotent lần hai và quét toàn cây không còn basename monolithic trong liên kết sống.

Việc nên làm trong sandbox, theo thứ tự:

```bash
export CCBA_SKIP_GIT_PULL=1
export CCBA_HUB_PATH=/home/vvc/ccba/ccba-agent-platform
# workspace: /tmp/ccba-e2e-spoke/.agents/workspace_context.yaml
# hub_path tương đối hoặc bỏ trống; project_name có giá trị; không path tuyệt đối
python scripts/sync_spoke.py --spoke /tmp/ccba-e2e-spoke --sync-item platform-loader --dry-run
python scripts/sync_spoke.py --spoke /tmp/ccba-e2e-spoke --sync-item platform-loader --apply --no-backup
python scripts/sync_spoke.py --spoke /tmp/ccba-e2e-spoke --sync-item platform-loader --apply --no-backup
```

`platform-loader` là skill có trong catalog Hub. Lần chạy copy thêm đúng một skill đó. Trước dry-run, ghi sha256 của `.md/data/spoke_registry.yaml`. Sau apply, sha256 phải đứng yên. Nếu đứng yên mà các assert anchor vẫn đỏ, sửa `graduation.py` rồi mới full-sync Spoke thật.

GATE-04 có thể chạy thêm, với tư cách kiểm tra script budget của sandbox. Nó không thay quét tên zombie và không thay đo byte ≤ 24.000 của 6 file đã copy vào `.agents/rules/`.
