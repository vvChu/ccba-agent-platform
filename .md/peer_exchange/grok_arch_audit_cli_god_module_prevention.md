---
request_id: req-arch-audit-cli-god-module-001
verdict: REVISE_PLAN
conditions:
- id: COND-ARCH-01
  description: Command registry là tuple tĩnh COMMANDS. importlib.import_module chỉ
    chạy sau khi argv[0] khớp tên lệnh. cli/__init__.py re-export bằng PEP 562 __getattr__.
    Import domain giữ lazy bên trong handler. Cấm pkgutil.iter_modules và cấm import
    domain ở đầu command module.
  blocking: true
  source_profiles: []
- id: COND-ARCH-02
  description: 'Mở rộng seam ccba_harness.peer_gate.check_ast_function_length rồi
    gắn vào verify-patch preset ci và preset code. Thêm file-size ratchet có baseline.
    Marker miễn trừ dùng token mới, until theo UTC, issue là URL GitHub đầy đủ. Cấm
    tái sử dụng # ccba:quarantine khi không có seam_id. Parse AST lỗi thì fail-closed.
    Gỡ bypass cả file # ccba:allow-long-functions.'
  blocking: true
  source_profiles: []
- id: COND-ARCH-03
  description: Tách làm ba pha PR. Pha 0 là test đặc tả cho alias và ba entry point.
    Pha 1 chỉ di chuyển cơ học và xóa shadow parser trong main(). Pha 2 rút policy
    Level-3 khỏi handler vào seam peer. Hard cap bật sau khi handler mới đã dưới trần.
    Cấm quarantine nguyên hàm vừa được di chuyển. Hồi quy bằng pytest packages/ccba-harness/tests
    và tests/governance.
  blocking: true
  source_profiles: []
- id: COND-ARCH-04
  description: 'Khóa đủ tên lệnh đang sống trong fast-path: gate, watch-peer, dispatch-peer,
    explain-why, cùng alias argparse co-review, peer-apply, apply-patch. Giữ ba entry
    point ccba_harness.cli:main, python -m ccba_harness, và python -m ccba_harness.cli.'
  blocking: true
  source_profiles: []
- id: COND-ARCH-05
  description: 'Ngưỡng chuẩn: file soft 500 / hard 800 kèm ratchet cho tệp hiện hữu;
    hàm domain giữ hard 50 như peer-gate; phần thân sau parse_args của handler CLI
    hard 40 dòng và cấm write_text, mkdir, subprocess trong package cli. Hard 80 là
    nới lỏng so với cổng hiện có, không được thành chuẩn mới.'
  blocking: false
  source_profiles: []
risk_score: 4
summary: Chẩn đoán God Module là đúng và hướng tách CLI được chấp nhận. Kế hoạch 4
  trụ cột, nếu code đúng như viết, mâu thuẫn với ngân sách dòng, làm yếu cổng 50 dòng
  đang có, và đánh mất lazy import. Sửa registry, marker, và trình tự PR trước khi
  đụng cli.py.
telemetry:
  session_id: 6905c48d-4791-477c-bb66-1c6e4f4885d3
  primary_model: grok-4.7-build
  input_tokens: 743405
  output_tokens: 27987
  reasoning_tokens: 20448
  cached_read_tokens: 664320
  total_tokens: 771392
  model_calls: 14
  turn_count: 1
  cost_usd: 223805.68
  cost_mode: exact
  duration_seconds: 415.1
---
# Thẩm định kiến trúc: tách `cli.py` và chặn God Module

Điểm rủi ro **4/5** theo `PeerVerdictBlock` (ADR-0065, `ge=1, le=5`). Thang 1–10 trong template yêu cầu không parse được bằng harness hiện tại. Verdict `REVISE_PLAN` vì hướng đi đúng và kế hoạch triển khai chưa đúng.

Nguồn ADR trong yêu cầu ghi `docs/adr/0065-level-2-hardening-and-fail-closed-preimage-rollback.md`. File đó không tồn tại. Bản đang có hiệu lực là `docs/adr/0065-peer-runtime-hardening-and-topological-fail-closed.md`. Policy Level-3 mà CLI đang nắm (`patch_fast` + verdict `HANDOFF` + ghi gate file) nằm ở handler, seam rollback nằm ở `peer.py`.

## Hiện trạng đã đối soát

`packages/ccba-harness/src/ccba_harness/cli.py` có **2705 dòng**, 18 hàm top-level. `main()` chiếm dòng 2089–2700 (**612 dòng**). Khoảng 543 dòng đầu của `main()` dựng `ArgumentParser` đầy đủ, rồi fast-path bỏ qua object đó và gọi `run_*_cli(argv[1:])`, nơi parser được dựng lần thứ hai. Nhánh fallback (2670–2697) lặp lại cùng chuỗi `if` và cũng bỏ namespace đã parse.

Độ dài AST (`end_lineno - lineno + 1`):

| Hàm | Dòng |
|---|---:|
| `main` | 612 |
| `run_telemetry_cli` | 376 |
| `run_peer_dispatch_cli` | 258 |
| `run_peer_co_review_cli` | 253 |
| `run_skill_validation_cli` | 214 |
| `run_eval_cli` | 211 |
| `run_verify_patch_cli` | 185 |
| `run_evaluate_gpi_cli` | 133 |
| `run_apply_anchor_patch_cli` | 109 |
| `run_verify_doc_cli` | 69 |
| `run_peer_watch_cli` | 56 |
| Các hàm còn lại | ≤ 41 |

Import domain ở top-level chỉ có `SkillValidator`. Mọi seam nặng (`peer`, `verifier`, `gpi`, `telemetry`, `healing`, `evals`) đều import **bên trong hàm**. Đó là tài sản cần giữ.

Ba entry point đang sống đồng thời:

- Console script `ccba-harness = ccba_harness.cli:main` trong `packages/ccba-harness/pyproject.toml`.
- `python -m ccba_harness` qua `src/ccba_harness/__main__.py`.
- `python -m ccba_harness.cli` qua khối `if __name__ == "__main__"` cuối `cli.py`.

Không có `--version`. Lệnh “nhanh” thực tế là root `--help` và `why` / `blast-radius`. Cả hai vẫn trả tiền xây toàn bộ subparser trong `main()` trước khi dispatch. `why` còn trả tiền import `skill_validator` dù không dùng.

`ccba_harness/__init__.py` chỉ re-export ba symbol CLI: `run_apply_anchor_patch_cli`, `run_peer_co_review_cli`, `run_peer_dispatch_cli`. `AGENTS.md` của package khai báo đúng ba seam đó. Hai hàm `_print_gpi_result` và `_parse_commands_from_file` là private. Đóng băng “100% 18 symbol” thành API công khai sẽ biến tai nạn đặt tên thành hợp đồng.

Consumer Python thực (import trực tiếp), không phải 35 call site:

- Production: `scripts/peer_dispatch.py`, `scripts/peer_bridge_watcher.py`.
- Package tests: `test_cli.py`, `test_peer_watch_cli.py`, `test_peer_dispatch_cli.py`, `test_peer_auto_apply.py`, `test_peer_co_review.py`, `test_peer.py`, `test_verify_patch.py`, `test_telemetry.py`, `test_skill_validator.py`, `test_gpi_decision_framework.py`, `test_tier3_orchestrator.py`, `test_tuner.py`, `test_pstack_disciplines.py`.
- Governance: `tests/governance/test_telemetry_streamer.py`, `tests/governance/test_self_healing_engine.py`.

Chuỗi `python -m ccba_harness.cli ...` trong skill và docs là entry point module. Chúng ổn nếu `cli/__main__.py` tồn tại. Chúng không phải import path.

Alias chỉ tồn tại trong fast-path, **không** có `aliases=` trên parser: `gate`, `watch-peer`, `dispatch-peer`, `explain-why`. `co-review`, `peer-apply`, `apply-patch` có cả hai. Không có test nào gọi bốn alias fast-path. Một registry dựng từ `add_parser(..., aliases=)` sẽ làm rơi chúng.

## 1. Registry và startup

Cơ chế đúng là **explicit static registry**:

```python
COMMANDS = (
    CommandSpec(
        names=("why", "explain-why"),
        module="ccba_harness.cli.commands.architecture",
        attr="run_explain_why_cli",
        help="Query architectural rationale from ADRs.",
    ),
    # ...
)
```

`main()` khớp `argv[0]` với `names`, rồi `importlib.import_module` đúng một module. Root `--help` in `names` + `help` từ tuple, không import command module, không dựng parser của lệnh khác. Lệnh đã chọn tự dựng parser của nó, đúng như `run_*_cli` đang làm. Shadow parser trong `main()` bị xóa, không được copy sang `core.py`.

`core.py` dưới 60 dòng đạt được với dispatcher này. Nó không đạt được nếu `core.py` import mọi command module để “tự đăng ký”.

`pkgutil.iter_modules` bị loại vì bốn lý do gắn với KISS và tính tất định của ADR-0061:

- Thứ tự lệnh phụ thuộc filesystem.
- Discovery bắt buộc import mọi module để chạy side effect `register()`, nên `why` kéo theo `peer` và `telemetry`.
- Một file test hoặc helper lọt vào package `commands/` thành subcommand ẩn.
- Review diff không thấy danh sách lệnh ở một chỗ.

Tương thích import dùng PEP 562 trên `cli/__init__.py`: `__getattr__` trả về symbol khi có `from ccba_harness.cli import run_peer_dispatch_cli`. Entry point Hatch `ccba_harness.cli:main` đi qua `getattr`, nên `main` có thể nằm ở `core.py` mà console script vẫn phân giải được.

Ba cạm bẫy nếu làm “cho sạch”:

1. **Relative import.** `cli.py` hôm nay là module của `ccba_harness`, nên `from .peer import ...` ra `ccba_harness.peer`. Sau khi file nằm ở `cli/commands/peer.py`, cùng câu import trỏ vào chính package `commands`. Handler phải dùng `from ccba_harness.peer import ...` hoặc `from ...peer import ...`.
2. **Import eager trong `__init__.py`.** `ccba_harness/__init__.py` import ba hàm CLI **trước** khi import `peer`. Nếu command module import `peer` ở top-level, khởi tạo package sẽ kéo `peer.py` giữa chừng. Giữ lazy import bên trong hàm.
3. **`unittest.mock.patch`.** Chỉ một chỗ patch `ccba_harness.cli.run_peer_watch_cli` (`test_peer_watch_cli.py:115`). Patch đó ăn vào global của module chứa `main`. Dispatcher qua `importlib` làm patch này vô hiệu. Các patch `ccba_harness.peer.*` và `ccba_harness.evals.runner.*` vẫn đúng vì import nằm trong hàm, sau khi patch đã gắn.

Startup của `why` sau thiết kế này: một command module + `architecture.py`. Hết. Không `SkillValidator`, không parser của `peer-dispatch`, không `telemetry`.

## 2. Ngưỡng và phân mảnh

Hard cap **80** dòng/hàm là nới lỏng so với seam đang có. `check_ast_function_length(..., max_lines=50)` đã là hard gate trong `run_full_gate`. Một hàm mới 70 dòng **fail** peer-gate hôm nay và **pass** cổng đề xuất. Nếu cổng mới thay cổng cũ, governance đi lùi. Giữ hard **50** cho hàm domain mới hoặc vừa sửa. Hard 80 không trở thành chuẩn.

File cap đề xuất cũng không chặn đúng bệnh:

- Câu chữ “file `.py` mới” có hai nghĩa. Nghĩa “chỉ file tạo trong PR” cho phép mọi file cũ, kể cả `cli.py` sau khi đã tách một phần, phình thêm mãi mãi.
- Áp hard 800 cho toàn bộ `packages/` ngay lập tức làm đỏ những God Module đã có: `cli.py` 2705, `evals/tuner.py` 2396, `peer.py` 2176, `evals/scorers/domain.py` 1919, `ccba_legal/cli.py` 1456.
- `run_peer_dispatch_cli` (258) và `run_peer_co_review_cli` (253) chuyển nguyên khối sang `cli/commands/peer.py` thì file có thể vẫn dưới 800, còn từng hàm vẫn vỡ trần 50 và trần 80. Bật gate trong cùng PR với pha di chuyển buộc phải dán miễn trừ lên chính hàm vừa chuyển. Đó là `# ccba:allow-long-functions` đổi tên.

Sweet spot cho monorepo này:

- **File** trong `packages/*/src/**/*.py`: warn 500, hard 800. File đã vượt trần ghi vào baseline đã commit (số dòng). CI fail khi số dòng tăng. Gỡ khỏi baseline khi file xuống dưới 800.
- **Hàm domain**: warn và hard đều bám 50, đo bằng span AST như seam hiện có.
- **Handler CLI**: đo đoạn **sau** `parse_args`. Hard 40 dòng. Package `cli` không được gọi `Path.write_text`, `mkdir`, `subprocess` hay tự viết giao dịch rollback. Argparse 12 flag đã ngốn ~90 dòng (`run_verify_patch_cli` dựng parser từ 724 đến 813). Đếm cả parser vào trần 50 sẽ đẻ hàng loạt `_add_*_args()` 30 dòng. Đó là phân mảnh vi mô, không phải độ sâu.
- **Granularity đích**: năm module theo bounded context, sau khi handler đã mỏng. `telemetry` (376 dòng, 8 sub-action: inspect, budget-check, export-otel, swarm, dashboard, fleet, economy, stream) được tách theo sub-action vì mỗi action đã có seam riêng (`telemetry.py`, `dashboard.py`, `fleet.py`, `economy.py`, `streamer.py`). Không tách một file cho mỗi `add_argument`.

`code_quality.md` mục 2.1 cấm shallow module 1-1. Adapter CLI mỏng là ngoại lệ có chủ đích: độ sâu nằm ở `peer.py` / `verifier.py` / `architecture.py`. Ghi ngoại lệ này trong kế hoạch để pha thin-shell không bị chặn bởi chính quy chuẩn shallow-module.

Rule “hàm ≤ 50 dòng” mà yêu cầu gọi là Rule 5 không nằm trong `docs/rules/code_quality.md`. Nơi đang cưỡng chế là `peer_gate.check_ast_function_length`. Nơi đang bị bypass là dòng 3 của `cli.py`: `# ccba:allow-long-functions`. Checker thấy marker này thì **skip cả file**.

## 3. Di chuyển và độ phủ test

`cli.py` và package `cli/` không thể cùng tồn tại. Strangler nhiều PR theo kiểu “để cả hai sống” là không khả thi với cùng một import name. Strangler đúng là facade một file trong vài PR, hoặc một PR đổi tên cơ học.

Trình tự an toàn, khớp micro-PR ≤ 200 LOC ở `docs/rules/execution_guardrails.md` cho pha có sửa hành vi:

1. **Pha 0, chỉ test.** Ma trận `--help` cho 13 subcommand. Bốn alias fast-path. Ba entry point cùng trỏ một `main`. Một test import từng symbol mà consumer đang dùng. Chưa sửa production.
2. **Pha 1, di chuyển cơ học.** Đổi `cli.py` thành package, registry lazy, xóa shadow parser và chuỗi `if` trùng. Không đổi điều kiện `patch_fast` / `HANDOFF`, không đổi exit code 4 khi rollback proven, không “dọn” import. Diff lớn nhưng là rename. Hồi quy full `pytest packages/ccba-harness/tests tests/governance`.
3. **Pha 2, thin shell.** Rút khối auto-apply trong `run_peer_dispatch_cli` (1634–1721) và khối tương ứng của co-review vào seam `peer` đã có (`auto_apply_and_verify_patch`, `orchestrate_peer_co_review`). Mỗi PR một policy, ≤ 200 LOC hành vi.
4. **Pha 3, bật ratchet.** Lúc này handler mới đã dưới trần, baseline giữ các God Module còn lại. Không có miễn trừ cho code vừa move.

`verify-patch --preset ci` **không** chạy `test_cli.py` hay `test_peer_*.py`. Preset `ci` trong `verifier.py` chỉ pytest `test_telemetry.py`, `test_verify_patch.py`, và `tests/governance/`, cộng ruff, validate_skills, compile_catalog, sync ADR matrix. Một PR tách CLI có thể xanh preset `ci` trong khi gãy `peer-dispatch`. Preset `ci` là chỗ gắn checker tĩnh (rẻ, mili-giây). Nó không phải lưới hồi quy của pha 1.

Độ phủ hiện tại khóa được hành vi Level-3 trong `test_peer_auto_apply.py` và vài đường help (`eval`, `peer-watch`). Nó không khóa alias fast-path, không khóa parity ba entry point, và không khóa sự lệch giữa parser ngoài và parser trong vì parser ngoài gần như là code chết trên fast-path. Coi bộ test này là “100% ranh giới” sẽ tạo cảm giác an toàn giả.

`patch("ccba_harness.cli.run_peer_watch_cli")` phải được viết lại để patch đúng seam dispatcher, trong pha 0, trước khi `main()` đổi chỗ.

## 4. Ma trận ADR-0061

| Trục | Đánh giá |
|---|---|
| Giá trị | Cao. File 2705 dòng, parser dựng hai lần, policy Level-3 nằm trong handler, completion lock không nhìn thấy độ dài hàm. |
| Độ phức tạp | Kế hoạch đánh giá thấp. Phần việc thật là tương thích entry point, alias, relative import, và rút policy. Đổi tên file chỉ là pha 1. |
| Rủi ro | Cao nếu pha 1+2+3 gộp một PR và bật hard cap kèm quarantine. Thấp nếu đi đúng bốn pha trên. |
| KISS | Registry tuple + mở rộng `check_ast_function_length` là KISS bậc 1 (seam đã có). `pkgutil`, checker song song, và dialect quarantine mới là KISS giả. |

### Pitfall bắt buộc xử lý trong kế hoạch

**Cổng “không tồn tại” thì không đúng.** `peer_gate.py` đã có AST function length 50, redundant comments, secret/IP, import depth. `run_full_gate` gọi nó trên file đổi theo git. Hai lỗ thật:

- Completion lock ADR-0058 là `verify-patch`, và preset `ci` không gọi `run_full_gate`.
- `# ccba:allow-long-functions` skip cả file, không có `until`, không có issue. `cli.py` mang marker này từ dòng 3, nên peer-gate không bao giờ đo 18 hàm của nó.
- Checker nuốt mọi exception (`except Exception: continue`), fail-open khi file không parse được. Cổng gắn vào completion lock phải fail-closed, cùng cực với ADR-0065.

**Marker đề xuất vi phạm ngữ pháp ADR-0061.** Marker hợp lệ là:

```python
# ccba:quarantine seam_id=<id> reason=<reason> until=<YYYY-MM-DD> issue=<url>
```

`reason` chỉ thuộc bốn giá trị (`hardware_mismatch`, `seam_regression`, `health_timeout`, `version_conflict`). `issue` phải khớp `^https://github\.com/vvChu/ccba-agent-platform/issues/\d+$`. `until` so với `datetime.now(timezone.utc).date()`. Dòng `# ccba:quarantine module_budget=... issue=...` thiếu `seam_id` sẽ bị linter quarantine từ chối, hoặc bị scanner lỏng hiểu nhầm là seam quarantine. Dùng token khác, ví dụ `# ccba:budget-exception scope=function name=run_eval_cli until=YYYY-MM-DD issue=<url>`. So ngày bằng UTC. Baseline committed cho file cũ tốt hơn một rừng marker.

**Reuse-first.** Seam cần sửa là `check_ast_function_length` cộng một hàm đo số dòng file cạnh nó, cùng module `peer_gate`. Viết `scripts/check_module_budget.py` song song là silo mới, đúng anti-pattern mà ADR-0061 cấm.

**Thin shell chưa xảy ra khi chỉ đổi đường dẫn.** `run_peer_dispatch_cli` sau `parse_args` còn tự quyết định profile, đọc output, từ chối verdict khác `HANDOFF`, gọi `auto_apply_and_verify_patch`, và `atomic_write_text` gate file. `cli/commands/peer.py` chứa nguyên khối đó vẫn là God Handler. Trụ cột 3 là trụ quyết định xem refactor có xong hay chỉ đổi địa chỉ.

**Trụ cột 4 không cưỡng chế được.** “PR thêm > 150 dòng thì agent phải audit” là nghi thức. Chính nghi thức “thêm vào `cli.py` cho nhanh” đã tạo file này, trong khi peer-gate 50 dòng đã tồn tại và bị bypass. `execution_guardrails.md` đã có ngân sách ≤ 200 LOC cho PR logic. Ratchet “số dòng của file baseline không được tăng” mới chặn được 149 dòng thêm mười lần. Trigger theo delta từng PR thì hết hiệu lực ở PR kế tiếp.

**Bán kính lớn hơn harness.** `ccba_legal/cli.py` đã 1456 dòng. Gate chỉ cài trong đầu người review harness sẽ lặp lại cùng RCA ở package kế bên. Baseline monorepo là phạm vi đúng của pha 3.

## Phần kế hoạch giữ nguyên

- Package `cli/` với `__main__.py` là cách duy nhất giữ `python -m ccba_harness.cli`.
- Nhóm lệnh theo bounded context là đích đúng sau khi handler mỏng.
- Policy CLI chỉ parse và gọi seam là invariant đúng. Seam đích đã có sẵn, không cần package mới.
- Gắn kiểm tra tĩnh vào `verify-patch` là chỗ duy nhất agent không bỏ qua, vì ADR-0058 cấm tuyên bố xong khi lệnh này khác 0.

Sau khi bốn điều kiện blocking được viết lại vào kế hoạch, pha 0 có thể bắt đầu mà không cần thêm vòng thẩm định kiến trúc.