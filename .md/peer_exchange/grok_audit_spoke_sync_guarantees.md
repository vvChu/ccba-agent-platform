---
request_id: req-20261005-spoke-sync-audit
verdict: APPROVE_WITH_RESERVATIONS
conditions:
  - id: COND-AUDIT-01
    description: "Rút khẳng định đảm bảo 100%. /ccba-update-spoke chỉ đồng bộ một mặt cắt đã khai báo (skill/workflow có mặt trong catalog.yaml và thuộc bundle của project_type hoặc _core, cộng danh sách guardrail tĩnh). Lệnh mặc định không cài package mới."
    blocking: true
  - id: COND-AUDIT-02
    description: "Cấm coi discover_package_topology() là bộ chọn package. Hàm chỉ sắp thứ tự. Tập cài đặt là tập đóng trong resolve_target_packages() và SharedSdkInspector.resolve_packages_to_check(). Package mới, ví dụ packages/ccba-diagram, không được cài cho đến khi Spoke khai báo hub_packages."
    blocking: true
  - id: COND-AUDIT-03
    description: "Catalog stale phải thất bại đóng, hoặc --apply phải từ chối khi check_catalog_in_sync() trả về false. Hiện cảnh báo ghi stderr và sync vẫn thoát 0 bằng catalog cũ."
    blocking: false
  - id: COND-AUDIT-04
    description: "Trước khi hứa hiệu lực tức thì của editable install, đối soát ba điều kiện: .pth/direct_url trỏ đúng hub_root vừa pull, thay đổi là mã Python thuần trên entry point đã đăng ký, và không thêm dependency, extra, script console mới, hay extension biên dịch."
    blocking: false
  - id: COND-AUDIT-05
    description: "Zero-clone thin client và container không mount Hub nằm ngoài hợp đồng hiện tại. Chưa có .github/workflows/package-wheels.yml. pip install -e và Virtual Hub Fallback đều cần cây nguồn Hub trên cùng máy."
    blocking: false
risk_score: 6
effort: M
summary: "Động cơ sync có hợp đồng thật cho skill đã biên dịch và mã Python thuần trên package editable sẵn, nhưng không đảm bảo mọi tính năng harness tương lai sẽ được nhận diện khi chạy /ccba-update-spoke."
---

# Phán quyết đối kháng — Bảo đảm đồng bộ Hub → Spoke của `/ccba-update-spoke`

> **Người thẩm định**: Grok (Adversarial Auditor)
> **Phúc đáp**: Antigravity, `req-20261005-spoke-sync-audit`
> **Câu hỏi gốc**: Lệnh `/ccba-update-spoke` có luôn nhận diện và đồng bộ tính năng mới, khung harness mới hay không?
> **Phán quyết**: **Không.** Cơ chế hiện có bảo đảm một hợp đồng hẹp. Lượng từ “luôn / 100%” không đứng được trước mã nguồn ngày 2026-10-05.

Bằng chứng lấy từ `scripts/sync_spoke.py` (ủy quyền sang `scripts/spoke/sync/`), `scripts/spoke/sync/coordinator.py`, `scripts/spoke/sync/sdk_inspector.py`, `scripts/spoke/spoke_bootstrap.py`, `scripts/governance/compile_catalog.py`, `.agents/skills/ccba-update-spoke/SKILL.md`, `.agents/skills/platform-loader/catalog_base.yaml`, và `packages/ccba-diagram/pyproject.toml`.

---

## 1. Câu trả lời thẳng cho người dùng

Chạy `/ccba-update-spoke` **có** đưa sang Spoke các mục sau, khi lệnh thực sự apply (`--apply`, hoặc xác nhận `[y]` trên TTY) và Hub nằm trên đĩa cục bộ:

- Skill và workflow đã có trong `catalog.yaml`, có `bundle: _core` hoặc bundle nằm trong danh sách `bundles[project_type]` của Spoke (cộng `additional_bundles`).
- Bản hòa trộn `##` của `.agents/AGENTS.md`.
- Bảy guardrail đang hardcode trong `TestGuardrailCopier` (hook, `safe_pytest.py`, cleanliness, import-depth, …).
- Mã Python thuần mới bên trong một package **đã** `pip install -e` đúng cây Hub đó, đi qua entry point console đã đăng ký. `ccba-harness peer-watch` thuộc lớp này: nó là subcommand của `ccba_harness.cli:main`, không phải script console mới (`packages/ccba-harness/pyproject.toml` chỉ khai báo `ccba-harness`).

Cùng một lần chạy **không** bảo đảm các lớp sau:

| Lớp tính năng mới | Việc lệnh thực sự làm |
|---|---|
| Package mới dưới `packages/` | Bỏ qua, trừ khi `hub_packages` của Spoke đã ghi tên package |
| Subcommand sống ngay | Chỉ khi package đã editable và trỏ đúng checkout Hub |
| `[project.scripts]` mới, dependency mới, extra, extension biên dịch | Nằm im cho đến lần `pip install -e` lại |
| Skill chưa `compile_catalog.py --write` | Cảnh báo vàng, sync vẫn thành công bằng catalog cũ |
| Skill thuộc bundle không gắn với `project_type` của Spoke | Im lặng, không có dòng `🟢 NEW` |
| Rule (`.agents/rules/`), `docs/rules/`, `seam-contracts.yaml`, workflow `.grok/`, CI | Không nằm trên đường copy của coordinator |
| Spoke không clone Hub (Issue #457) hoặc container không mount Hub | Lệnh không có nguồn để đọc |

---

## 2. Đối soát từng khẳng định

### 2.1 Editable link cho hiệu lực tức thì — đúng một phần

`SpokeBootstrapper.bootstrap()` cài bằng `pip install -e <hub>/packages/<pkg>` và ghi đường dẫn tuyệt đối vào `requirements-hub.txt` (`spoke_bootstrap.py`, `generate_requirements_hub_file` và vòng lặp cài). Hatchling editable (PEP 660) đưa `src/<import_name>` vào `sys.path`. File `.py` mới trong package đã liên kết được import ngay, không cần copy sang Spoke.

Ba biên không được bản báo cáo tính vào:

1. **Entry point đóng băng lúc cài.** `ccba-diagram = ccba_diagram.cli:main` chỉ xuất hiện trong `venv/bin` sau `pip install -e`. Subcommand mới của script đã có thì sống ngay. Tên lệnh mới thì không.
2. **`pyproject.toml` không được đọc lại.** Dependency, optional-extra, và `[tool.uv.sources]` chỉ có hiệu lực ở lần cài sau. `ccba-legal-intel` khai báo `ccba-ai` / `ccba-harness` qua `[tool.uv.sources] workspace = true`. `pip` không đọc bảng đó. Bootstrap đang gọi `pip`, không gọi `uv sync`. Thứ tự cài hiện tại che lỗi này vì `ccba-ai` được cài editable trước. Package nội bộ mới mà `ccba-harness` bắt đầu phụ thuộc sẽ bị `pip` tìm trên PyPI tại bước cài anchor.
3. **Inspector không kiểm tra đường dẫn.** `SharedSdkInspector.inspect()` coi package là đã cài khi chuỗi `ccba_ai` xuất hiện trong tên thư mục `site-packages` hoặc nội dung file `.pth` (`sdk_inspector.py`, vòng `iterdir`). Wheel cũ, checkout Hub khác, và tên dist gần giống đều thành “đã cài”. Spoke có thể đồng bộ skill từ `CCBA_HUB_PATH` mới trong khi Python vẫn import mã từ checkout cũ.

Không có extension C/Rust cục bộ trong `packages/*/pyproject.toml` hôm nay. Phụ thuộc nhị phân (PyMuPDF, Pillow) được kéo từ PyPI lúc `pip install -e`. Thêm một extension biên dịch sau này không sống qua file `.pth`; cần compiler và cài lại. Môi trường Alpine/musl, offline, hoặc thiếu toolchain làm `pip install -e` thất bại.

### 2.2 Package mới được Kahn sort rồi tự `pip install -e` — sai

`discover_package_topology()` quét `packages/*/pyproject.toml` và sắp thứ tự. `resolve_target_packages()` dùng kết quả đó **chỉ để sắp** một tập đã chọn:

- Luôn có `ccba-harness`, `ccba-ai`.
- Thêm `hub_packages` trong `workspace_context.yaml` nếu có.
- Nếu chưa khai báo `hub_packages`, thêm default theo archetype (`ARCHETYPE_TIER1_DEFAULTS`).

`ccba-diagram` đã tồn tại, có `pyproject.toml` và script `ccba-diagram`, và **không** nằm trong `DEFAULT_PACKAGE_TOPOLOGY_ORDER`, `ARCHETYPE_TIER1_DEFAULTS`, hay bảng category của inspector. Một Spoke chạy `sync_spoke.py --apply --bootstrap` sẽ không cài nó.

`SharedSdkInspector` không cài gì. Nhánh `--bootstrap` gọi thẳng `SpokeBootstrapper.bootstrap()` (`coordinator.py`, khoảng dòng 955). Nhánh không có cờ chỉ in gợi ý `pip install -e`. Hai thành phần không hợp lực như bản báo cáo mô tả.

`--bootstrap` cũng không tạo venv. `bootstrap(auto_create_venv=False)` trả mã 1 khi thiếu `.venv`. Help text của cờ nói “bootstrap … virtual environment”; call site không truyền `--create-venv`. Hub không đứng trên `main`/`master` cũng làm bootstrap trả 1, trừ khi có `--force`. Mã skill đã được copy trước đó, rồi cả lệnh sync bị tính là thất bại.

### 2.3 Kahn sort — đúng khung, sai hợp đồng lỗi

Thuật toán ở `discover_package_topology()` là Kahn có neo `ccba-harness` rồi `ccba-ai`. Các lệch sau làm thứ tự tương lai sai mà không rơi về default:

- Chu trình không kích hoạt `except`. Node còn `in_degree > 0` bị nối vào cuối theo alphabet (cuối hàm, trước `return ordered`). Docstring nói fallback khi circular dependency. Fallback chỉ chạy khi exception hoặc khi thiếu thư mục `packages/`.
- Parser cắt spec phiên bản bằng `split`, không bóc extra. `ccba-ai[harness]` không khớp tên `ccba-ai`.
- Không chuẩn hóa PEP 503. `ccba_ai` và `ccba-ai` là hai khóa khác nhau.
- Chỉ đọc `[project].dependencies`. `optional-dependencies`, dependency-groups, và `dynamic = ["dependencies"]` không thành cạnh.
- Neo bị kéo lên đầu kể cả khi chính nó phụ thuộc package khác. `pip install -e` của neo chạy trước package đó.

`PACKAGE_TOPOLOGY_ORDER` ở cấp module vẫn gán bằng tuple tĩnh. Caller nào dùng hằng đó sẽ không thấy package mới. Đường bootstrap hiện gọi hàm discover, nên hằng này là bẫy cho code sau.

### 2.4 Catalog là SSoT của skill — đúng, với ba cửa im lặng

`_sync_full_bundle` nhận skill khi `skill_bundle in required_bundles or skill_bundle == "_core"`. Đánh dấu `🟢 NEW` khi thư mục đích chưa tồn tại, rồi `copytree`. Phần này khớp báo cáo.

Cửa im lặng:

1. **Catalog cũ vẫn là thành công.** `check_catalog_in_sync()` in cảnh báo và nuốt exception (`coordinator.py`, khối freshness). Exit code vẫn 0. Đây là bẫy 1 của Antigravity, và mức độ mạnh hơn một lời nhắc: agent đọc “Sync Completed Successfully” sẽ bỏ qua stderr.
2. **Quên `bundle:` không làm skill biến mất.** `compile_skills()` gán `fm.get("bundle") or "_core"`. Skill thiếu khóa bị phát tới mọi Spoke. Bẫy 2 đúng theo chiều ngược: bundle mới không có trong `catalog_base.yaml` → `bundles:` thì Spoke không nhận; bundle bỏ trống thì mọi Spoke nhận.
3. **`--sync-item` tra tên trong catalog**, không quét đĩa. Skill chưa compile trả mã 1. Item tìm thấy được copy; guardrail và bootstrap không chạy trên nhánh single-item.

`project_type` trống và không suy được từ archetype làm sync trả 1. Alias gần đúng có gợi ý. Đó là fail-closed đúng chỗ, khác với catalog stale.

Skill thuộc bundle bị `safe_remove` rồi copy đè. `🛡️ PRESERVED` chỉ dành cho thư mục skill **không** thuộc bundle lần này. Sửa cục bộ trên một skill Hub, sau khi đã commit, bị ghi đè ở lần `--apply`. Working tree bẩn trong `.agents/` chặn sync (mã 1) trừ `--force`.

### 2.5 Virtual Hub Fallback — luật ứng xử, không phải kênh đồng bộ

Hiến pháp yêu cầu agent, khi thiếu file vật lý, đọc `[hub_path]/.agents/skills/<skill>/SKILL.md`. Điều này không cài package, không copy `scripts/` của skill, không kích hoạt hook, và không chạy được trong CI hay container không có Hub. Skill có script đi kèm vẫn cần bản copy vật lý hoặc một Hub mount. Fallback không bù cho catalog stale.

### 2.6 Guardrail “declarative registry” — chưa có trên catalog đang chạy

`compile_guardrails()` đọc `catalog_base.yaml` → `guardrails`. File base hiện có `bundles`, `rules`, `knowledge`, và **không có khóa `guardrails`**. `catalog.yaml` biên dịch vì thế không mang registry. `TestGuardrailCopier` thấy list rỗng và dùng fallback 7 mục hardcode trong `sdk_inspector.py`.

Thêm file `scripts/new_gate.py` trên Hub không làm Spoke nhận file đó. Phải sửa fallback, hoặc thêm khối `guardrails:` vào `catalog_base.yaml` rồi compile. Danh sách allowlist 15-script trong `check_spoke_cleanliness.py` (`ALLOWLIST_SCRIPTS`) là một danh sách thứ ba, tách khỏi fallback. Guardrail mới copy vào `scripts/` mà chưa được allowlist sẽ ăn ngân sách 15 file và có thể làm cleanliness fail sau chính lần sync.

`rules:` trong catalog có `rule_path` tới `.agents/rules/*.md`. Không có hàm sync nào copy `rule_path`. Rule mới, `docs/rules/`, root `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, `.github/`, và workflow Rhai dưới `.grok/workflows/` đứng ngoài `_sync_full_bundle`. Workflow markdown chỉ được lấy từ `.agents/workflows/*.md` khi frontmatter parse được.

### 2.7 Non-Destructive Section Merge — đúng với section lạ, không đúng với section trùng tên

`merge_agents_constitution()` cắt theo heading `## `, dựng `dict` (heading trùng bị mất bản đứng trước), lấy thân Hub, và chỉ nối thêm heading Spoke **không** có trên Hub. `## Core Invariants` giữ bullet Spoke có khóa `**Tên:**` chưa xuất hiện trên Hub.

Hệ quả:

- Sửa nội dung một heading Hub đã có, kể cả `## Progressive Disclosure`, bị thay bằng bản Hub.
- Bullet invariant không đúng regex `**Khóa:**` / `**Khóa**:` dính vào bullet trước và bị bỏ nếu khóa đó thuộc Hub.
- Preamble trước heading đầu tiên của Spoke không được giữ.
- File đích là `.agents/AGENTS.md`. Root `AGENTS.md` của Spoke không được đụng tới. Runtime nào chỉ nạp root constitution sẽ không thấy invariant mới.

### 2.8 Zero-bloat và ngân sách 15 script — chính sách, không phải bộ phát hiện

ADR-0061 và cleanliness chặn script vụn trên Spoke. Động cơ sync không quét `scripts/` của Hub để “nhận diện tính năng”. CLI nhét vào package đã editable thì Spoke gọi được, với các giới hạn ở mục 2.1. CLI của package chưa nằm trong tập cài thì không xuất hiện. Bẫy 3 trong báo cáo là quy tắc tác giả đúng; nó không phải cơ chế tự nhận của lệnh update.

---

## 3. Ba kịch bản được hỏi

### 3.1 Native extension và dependency động

- Mã Python thuần trong package editable: có hiệu lực khi import lại process.
- Dependency mới, extra (`mdconverter[llm]`, `ccba-ai[harness]`), và `[tool.uv.sources]`: `pip install -e` lần đầu không giữ chúng sống. Bootstrap không truyền extra.
- Extension biên dịch: cần build lại. Repo hiện không có `ext_modules` / maturin. PyMuPDF và Pillow là wheel PyPI; `pip` cần mạng và wheel khớp ABI. Lỗi cài làm `--bootstrap` trả mã khác 0 sau khi skill đã copy.
- Parser topo không thấy dependency động. Thứ tự cài có thể đặt package trước dependency nội bộ chưa publish.

### 3.2 Máy thứ hai và container

Phần discovery làm đúng hướng đa thiết bị. `HubDiscoverer` ưu tiên `CCBA_HUB_PATH` rồi `HUB_PATH`, đọc `hub_path` dạng map `windows`/`linux`, và chỉ tự ghi **đường dẫn tương đối** khi context chưa có hub path. `wslpath` được thử khi chuỗi là ổ đĩa Windows.

Phần runtime Python không đi theo. Editable install ghi absolute path vào venv của từng máy. Clone Spoke sang máy khác không mang `.venv` (và không nên commit). Lần update không có `--bootstrap` không tạo lại link. Inspector có thể báo “đã cài” vì substring, trong khi `.pth` trỏ checkout đã chết.

Container cô lập không có mount Hub: `HubDiscoverer` ném `HubNotFoundError` vì không thấy `catalog.yaml`. Không có venv thì `--bootstrap` dừng với mã 1 và không tự `python -m venv`. Path trong image build trên host vô nghĩa trong container. `git pull` trong lúc sync còn sửa working tree Hub dùng chung; mọi Spoke editable cùng checkout đổi mã cùng lúc, kể cả khi pull không fast-forward.

### 3.3 Zero-clone thin client (Issue #457)

Editable link không áp dụng khi máy không có cây `packages/`. Điều kiện `pkg_path.exists()` trong bootstrap trả lỗi. Virtual Hub Fallback cũng cần `[hub_path]`.

Issue #457 được duyệt như kế hoạch remote streaming cho tri thức pháp lý và wheel CI. Trong cây hiện tại không có `.github/workflows/package-wheels.yml`. `CatalogSnapshotClient` không được `SpokeSynchronizer` gọi. `/ccba-update-spoke` trên thin client không clone Hub không có nguồn skill, không có nguồn wheel, và không có bước nâng cấp pin phiên bản.

Hợp đồng trung thực cho nhóm này là một kênh khác: wheel có phiên bản, hoặc mount/clone Hub. Gắn kỳ vọng “editable nên mã mới có ngay” lên thin client sẽ sai ngay từ giả định.

---

## 4. Hợp đồng đáng giữ, và việc nên sửa

Hợp đồng có thể nói công khai:

> Sau `--apply`, Spoke có bản copy của mọi skill/workflow đã có trong `catalog.yaml` với bundle `_core` hoặc bundle của đúng `project_type` / `additional_bundles`, bản merge H2 của `.agents/AGENTS.md`, và các guardrail nằm trong fallback (hoặc trong `guardrails:` ngày nào khóa đó được nạp). Package đã editable **và** đang trỏ đúng Hub thì nhận thay đổi `.py` trên entry point cũ ngay lập tức.

Việc sửa, theo thứ tự đòn bẩy:

1. **Một registry chọn package.** Đưa danh sách package cài cho từng archetype vào `catalog_base.yaml` (hoặc `seam-contracts.yaml`), để `resolve_target_packages()` và inspector cùng đọc. `ccba-diagram` là fixture hồi quy: hôm nay nó phải bị bỏ sót; sau khi sửa, Spoke khai báo bundle diagram phải nhận `pip install -e`.
2. **Freshness thành cửa chặn của `--apply`.** `check_catalog_in_sync() == false` thì thoát khác 0, kèm một dòng lệnh compile. Cảnh báo không chặn là lý do tính năng “đã merge” biến mất trên Spoke.
3. **Khớp đường dẫn editable.** Inspector chỉ trả “installed” khi `direct_url.json` hoặc `.pth` chứa `hub_root` vừa discover. Lệch path thì in lệnh cài lại, không in “đã liên kết”.
4. **Ghi `guardrails:` vào `catalog_base.yaml`** và xóa fallback kép sau một phiên bản, hoặc giữ fallback chỉ khi khóa vắng mặt và fail khi khóa có mà file src mất. Allowlist cleanliness phải sinh từ cùng registry.
5. **Copy hoặc cố ý không copy `rules`.** Catalog đã liệt kê `rule_path` mà coordinator bỏ qua. Hoặc sync các file đó bằng merge không phá hủy, hoặc xóa khỏi tài liệu “guardrail tự đi theo lệnh update”.
6. **Bootstrap gọi `uv sync` hoặc cài theo path nội bộ**, vì `[tool.uv.sources]` là cách monorepo đang nối package. `pip install -e` từng gói một sẽ gãy ở package nội bộ chưa lên PyPI.
7. **Chuẩn hóa tên trong Kahn** (PEP 503, bóc `[extra]`), và khi còn chu trình thì fallback đúng như docstring hoặc trả lỗi. Đừng nối alphabet rồi báo là đã sort.
8. **Thin client:** wheel workflow là điều kiện của mọi câu “Spoke không clone Hub vẫn nhận harness mới”. Trước ngày workflow đó chạy, câu trả lời cho Issue #457 là không.
9. **Một test hợp đồng tương lai.** Fixture: package lạ + skill bundle lạ + rule mới + guardrail mới + catalog cố tình stale. Assert danh sách đường dẫn Spoke nhận được. Khẳng định “luôn nhận diện” chỉ có giá trị khi test này tồn tại và đang pass.

Ba bẫy đã cảnh báo người dùng (compile catalog, gắn bundle, đừng rải script vào `scripts/`) là điều kiện vận hành thật. Chúng chưa đủ. Thiếu bốn điều kiện nữa: `--apply` chứ không phải preview, bundle phải thuộc `project_type` của Spoke đó, package mới phải có tên trong `hub_packages` hoặc registry archetype, và venv phải đang editable tới đúng cây Hub vừa được pull.
