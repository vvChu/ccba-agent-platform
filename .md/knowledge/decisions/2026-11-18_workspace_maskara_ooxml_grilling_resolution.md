# Biên Bản Phỏng Vấn Grilling & Kế Hoạch Triển Khai v1.1: Làm Sâu 3 Seam Workspace/Hub, Maskara & OOXML

> **Ngày chốt Grilling:** `2026-11-18` | **Phiên bản Kế hoạch:** `v1.1` (Cập nhật đầy đủ `8/8` điều kiện Pass 1 từ Grok session `bbf5de60-3b77-4605-b224-1cad5dc02335`)  
> **Trạng thái Thực thi:** `COMPLETED` *(Peer Audit `WF-02` `APPROVE_PLAN` `f044627a-7a05-410f-afff-6fd52351166d` + Hợp nhất đủ PRs `#804`, `#805`, `#806` `--merge`, `#807`, `#808` `--merge`, và Rollup PR)*  
> **Bản đồ Wayfinder:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../../wayfinder/workspace-maskara-ooxml-deepening/map.md) (`WAYFINDER-WORKSPACE-MASKARA-OOXML-20261118`)  
> **Báo cáo Kiến trúc Nguồn:** `.md/scratch/architecture-review/architecture-review-20261118-0605.html`  
> **Biên lai Đối soát Seam (`ADR-0061`):** `maskara_scanner.v1` $\to$ `ccba_maskara:MaskaraScanner` (`MATCH`), `ooxml_processor.v1` $\to$ `ccba_ooxml:DocxDocument` (`MATCH`), `statutory_currency.v1` $\to$ `ccba_legal:DynamicStatutoryResolver` (`MATCH`) | `index_sha256`: `84408980fb63f7f7f2d4a5f493411abf42c8e35217a36c491de454ee4ea4bc9b`

---

## 1. Bảng Giải Trình `8/8` Điều Kiện Từ Pass 1 (`bbf5de60-3b77-4605-b224-1cad5dc02335`)

| Mã | Phân loại | Dẫn chứng mã nguồn (`file:line`) | Biện pháp khắc phục triệt để trong Kế hoạch `v1.1` |
| :--- | :--- | :--- | :--- |
| **`COND-PII-DIALECT`** | **`[ADOPT_AS_IS]`** | [_miner_catalog.py](../../../packages/ccba-harness/src/ccba_harness/evals/_miner_catalog.py#L14-L78), [_miner_catalog.py](../../../packages/ccba-harness/src/ccba_harness/evals/_miner_catalog.py#L297-L330), [style.py](../../../packages/mdconverter/src/mdconverter/style.py#L35-L49), [ccba-harness/pyproject.toml](../../../packages/ccba-harness/pyproject.toml#L10-L12), [check_dependency_contracts.py](../../../scripts/governance/check_dependency_contracts.py#L512-L521) | Khóa bảng map `rule_id -> token` và thứ tự thế cho cả `3` dialect tại Mục 2 (`Q3`); giữ biên `\b` ở hai đầu regex SĐT (`\b(?:0\d{9,10}\|\+84\d{9,10})\b`) để `0\d{9,10}` không nuốt 11 số đầu của CCCD 12 số; giữ nhánh `try/except ImportError` fallback ở `_miner_catalog.py` (không thêm dependency vào `ccba-harness/pyproject.toml`), xóa hằng chết `SENSITIVE_PATTERNS`; giữ `_get_default_scanner()` nội bộ (tuyệt đối không đưa vào `_LAZY_EXPORTS` / `__all__`). |
| **`COND-WS-ANCHOR`** | **`[ADOPT_AS_IS]`** | [registry.py](../../../packages/ccba-legal-intel/src/ccba_legal/registry.py#L27-L145), [currency_resolver.py](../../../packages/ccba-legal-intel/src/ccba_legal/currency_resolver.py#L227-L276), [_daemon_reporting.py](../../../packages/ccba-harness/src/ccba_harness/evals/_daemon_reporting.py#L57-L67), [peer.py](../../../packages/ccba-harness/src/ccba_harness/cli/commands/peer.py#L17-L29), [spoke_bootstrap.py](../../../scripts/spoke/spoke_bootstrap.py#L354-L404), [daemon.py](../../../packages/ccba-harness/src/ccba_harness/evals/daemon.py#L108-L121), [test_parser_registry.py](../../../packages/ccba-legal-intel/tests/test_parser_registry.py#L85-L108) | Khóa bảng chữ ký `start_dir` & fallback từng adapter tại Mục 2 (`Q2`): `resolve_project_root()` truyền `start_dir=Path(__file__).resolve()`; `discover_master_registry_path()` kiểm tra thêm `Path.cwd()` trước khi fallback về `resolve_project_root()`; walker chung đặt `include_agents_md=False` (không dừng ở `AGENTS.md`) và cấm fallback `parents[5]`; giữ nguyên `_discover_currency_card_path()` 3 tầng tại `currency_resolver.py:251-277` (chỉ L227 thừa hưởng `resolve_project_root()` đã sửa); `wslpath` chỉ chạy khi có binary + drive Windows; `spoke_bootstrap` giữ check `packages/ccba-harness` + fallback `parents[3]`; internal `ccba_harness` import `ccba_harness._workspace_roots`; không cache `hub_root` lúc import (`conftest.py`); `daemon.py` giữ nguyên thứ tự `.env`. |
| **`COND-OOXML-SHARE`** | **`[ADOPT_AS_IS]`** | [validator.py](../../../packages/ccba-ooxml/src/ccba_ooxml/validation/validator.py#L64-L78), [base.py](../../../packages/ccba-ooxml/src/ccba_ooxml/validation/base.py#L168-L945), [docx.py](../../../packages/ccba-ooxml/src/ccba_ooxml/validation/docx.py#L84-L259), [redlining.py](../../../packages/ccba-ooxml/src/ccba_ooxml/validation/redlining.py#L32-L246), [pack.py](../../../packages/ccba-ooxml/src/ccba_ooxml/pack.py#L41-L67), [unpack.py](../../../packages/ccba-ooxml/src/ccba_ooxml/unpack.py#L29-L37) | Liệt kê trọn bộ `13` điểm `etree.parse` + `2` `fromstring` (`base.py` + `docx.py`) + `3` `ET.parse` (`redlining.py`) và `5` điểm đột biến DOM bắt buộc gọi `clone_root()` (`base.py:247,822,830,919` + `redlining.py:91-92`) tại Mục 2 (`Q4`); tất cả `validate_*` trả `list[ValidationIssue]`; mọi `print()` (kể cả `docx.py:259` `compare_paragraph_counts()`) chỉ chạy khi `self.verbose=True`; `pack.py` cố định `ZipInfo.date_time=(1980, 1, 1, 0, 0, 0)` và `unpack.py:29` gộp sort 1 list duy nhất (đủ `8` call site `rglob`); giữ nguyên thông báo `stderr` `bug_path_4`. |
| **`COND-DOOR-STREAK`** | **`[ADOPT_AS_IS]`** | [door_policy.py](../../../packages/ccba-harness/src/ccba_harness/door_policy.py#L24-L34), [door_policy.py](../../../packages/ccba-harness/src/ccba_harness/door_policy.py#L143), [door_policy.py](../../../packages/ccba-harness/src/ccba_harness/door_policy.py#L261-L264) | Sửa văn bản `Q1` & `TradeoffCard`: `exceeded_loc_budget` là trường `bool` của `DoorClassificationResult` (không phải `OneWayDoorCategory`); `compute_cumulative_streak` `break` ngay khi gặp `ONE_WAY_DOOR` nên `5` PR `ONE_WAY_DOOR` không kích hoạt `K >= 3`. |
| **`COND-BUDGET-CLIENT`** | **`[ADOPT_AS_IS]`** | [module_budget_baseline.json](../../../packages/ccba-harness/src/ccba_harness/module_budget_baseline.json#L1-L11), [client.py](../../../packages/ccba-ai/src/ccba_ai/client.py) (`753 LOC` `[đo thực tế]`) | Dời việc xóa mục `ccba_ai/client.py: 1216` sang `PR-4` (Rollup) để `PR-3a` chỉ chạm `validation/base.py`, không kéo `ccba-ai` vào blast radius của `ccba-ooxml`. |
| **`COND-PPTX-DEFER`** | **`[ADOPT_AS_IS]`** | [pptx.py](../../../packages/ccba-ooxml/src/ccba_ooxml/validation/pptx.py#L87-L251) | Ghi rõ `PPTXSchemaValidator` nằm ngoài phạm vi `PR-3a`/`PR-3b` (xếp hạng mục sau); ngưỡng benchmark `<= 16` lượt parse tệp unpacked chỉ áp dụng cho `DOCXSchemaValidator` + `RedliningValidator` trên fixture `.docx`. |
| **`COND-SHA-SCOPE`** | **`[ADOPT_AS_IS]`** | `packages/ccba-harness/.agents/skills/verify-ccba-*/SKILL.md` | Chỉ chạy `Semantic Mutation Proof` & cập nhật `covered_sha256` / `sync_commit` cho verifier có tệp trong `covered_paths` đổi byte: **`verify-ccba-maskara`** (`PR-2`) và **`verify-ccba-ooxml`** (`PR-3b`). Không đụng `verify-ccba-legal-intel` (vì `currency_resolver.py` giữ nguyên byte), `verify-ccba-harness` và `verify-ccba-mdconverter`. |
| **`COND-PARSER-REUSE`** | **`[ADOPT_AS_IS]`** | [base.py](../../../packages/ccba-ooxml/src/ccba_ooxml/validation/base.py#L846-L848) | Dùng factory `_make_secure_xml_parser() -> lxml.etree.XMLParser` tạo parser mới cho mỗi lần parse (`XMLParser(resolve_entities=False, no_network=True)`), không dùng singleton parser cấp module để tránh tích lũy `error_log` và bảo đảm an toàn đa luồng. |

---

## 2. Tóm Tắt `5` Quyết Định Thiết Kế Đã Khóa (`Q1`–`Q5` — Bản Chuẩn Hóa `v1.1`)

### `Q1` — Chiến lược cắt lát Micro-PR, `TradeoffCard` & Khóa `sync_commit` (`[FOG-001]` Resolved)
- Chạy **1 vòng thẩm định kế hoạch tổng thể tại `WF-02`** (`audit_plan` $\to$ `signoff_diff`) phủ trọn chuỗi **5 Micro-PR thực thi + 1 PR Rollup (`PR-1a`, `PR-1b`, `PR-2`, `PR-3a`, `PR-3b`, `PR-4`)**.
- Mỗi PR thực thi đi kèm `TradeoffCard` (`#L<a>-L<b>` `<= 30` dòng) do thuộc các danh mục `ONE_WAY_DOOR` hợp lệ của [door_policy.py](../../../packages/ccba-harness/src/ccba_harness/door_policy.py#L24-L87) (`PUBLIC_API_SEAM`, `CROSS_SPOKE_CONTRACT`, `AUTHZ_SECURITY`, `DEPENDENCY_LICENSE`) kèm cờ `DoorClassificationResult.exceeded_loc_budget=True` khi diff vượt `200` LOC (lưu ý: `compute_cumulative_streak` dừng ngay khi gặp `ONE_WAY_DOOR` tại `door_policy.py:261-264`, không kích hoạt leo thang `K >= 3`).
- Hợp nhất bằng `gh pr merge --merge` đối với các PR cập nhật `covered_sha256` (`PR-2`, `PR-3b`) để giữ `sync_commit` truy vết được trên `main` (`RULE-2.21`).

### `Q2` — Seam Phân Giải Workspace & Hub Root (`resolve_workspace_and_hub_roots` / `WorkspaceHubContext`)
- **Seam công khai tại `ccba_harness`:** `[NEW] packages/ccba-harness/src/ccba_harness/_workspace_roots.py` (`<= 250 LOC`, thuần Python stdlib + nạp `yaml` tùy chọn kèm fallback đơn dòng `hub_path`). Export công khai `WorkspaceHubContext` và `resolve_workspace_and_hub_roots(start_dir: Path | None = None) -> WorkspaceHubContext` qua `_LAZY_EXPORTS = {...}` (`ast.Assign`) tại [ccba_harness/__init__.py](../../../packages/ccba-harness/src/ccba_harness/__init__.py) & [ccba-harness/AGENTS.md](../../../packages/ccba-harness/AGENTS.md#L5).
- **Quy tắc Walker & Phân giải Env (Không Cache lúc Import):**
  1. Walker chung (`include_agents_md=False` — tuyệt đối không dừng ở `AGENTS.md`) duyệt ngược `[start, *start.parents]` tìm `.md/workspace_context.yaml`, `.agents/workspace_context.yaml`, `workspace_context.yaml`, `.git`, `.agents`, hoặc `pyproject.toml` **với điều kiện bỏ qua `packages/<pkg>/pyproject.toml` nội bộ** nếu có tổ tiên chứa `seam-contracts.yaml`.
  2. Không dùng fallback `parents[5]` (`_daemon_reporting.py:63-66`).
  3. Đọc mới `os.environ` (`CCBA_HUB_PATH`, `HUB_PATH`) ở mỗi lần gọi (không đóng băng lúc import để giữ sạch `conftest.py` sandbox).
  4. Dịch đường dẫn Windows qua `wslpath` **chỉ khi** `os.name != "nt"`, khớp ổ `^[A-Za-z]:[\\/]` và `shutil.which("wslpath")` tồn tại; nếu thiếu binary thì bỏ qua fail-soft giống [registry.py](../../../packages/ccba-legal-intel/src/ccba_legal/registry.py#L138-L139).
  5. Mọi caller nội bộ trong `ccba_harness` import trực tiếp `from ccba_harness._workspace_roots import ...` (tránh circular import qua `__init__.py`); caller ngoài (`ccba_legal`, `scripts/spoke`) dùng PEP 562 public seam.
- **Bảng Hợp Đồng `start_dir` & Fallback Từng Adapter (`10` Direct Adapters + `currency_resolver.py:227`):**

| Adapter (`file:line`) | `start_dir` truyền vào seam | Hành vi bảo toàn đặc thù & fallback |
| :--- | :--- | :--- |
| `ccba_legal.registry.resolve_project_root` (`registry.py:27`) | `Path(__file__).resolve()` | Vẫn neo tại `__file__`, bỏ qua `packages/ccba-legal-intel/pyproject.toml` để trả đúng Hub root (`test_parser_registry.py:103-108` & `load_relation_synonyms()` giữ nguyên); tiếp tục là target mock cho `test_registry_discovery.py`. |
| `ccba_legal.registry.discover_master_registry_path` (`registry.py:85`) | Gọi `resolve_project_root()` + kiểm tra thêm `Path.cwd()` cho Tier 3/4 | Kiểm tra `workspace_context.yaml` tại `resolve_workspace_and_hub_roots(Path.cwd())` (ưu tiên nếu có `.md/workspace_context.yaml`), rồi vẫn gọi `resolve_project_root()` tại `L85` để giữ mock `patch("ccba_legal.registry.resolve_project_root")`. |
| `ccba_legal.sync.engine` (`engine.py:188, 274`) | `self.project_root` | Đọc `hub_path` / `project.hub_path` qua seam; giữ nguyên logic nhận diện `ccba-legal-knowledge` & `_find_corpus_in_default_candidates()`. |
| `ccba_legal.currency_resolver` (`L227`, `L251`) | Không sửa `_discover_currency_card_path()` (`L251-277`) | `L227` thừa hưởng `resolve_project_root()` đã sửa; **giữ nguyên byte** `_discover_currency_card_path()` (3 tầng tìm file `legal_currency_card.json`: env hub, `__file__.parents`, `cwd.parents`), tránh phá `covered_sha256` của `verify-ccba-legal-intel`. |
| `ccba_harness.cli.commands.peer.find_workspace_root` (`peer.py:17`) | `start_dir or Path.cwd()` | Bỏ mốc `AGENTS.md`, kiểm tra `.git` / `workspace_context.yaml` / `.md/workspace_context.yaml`; thỏa `test_peer_watch_cli.py:77-87`. |
| `ccba_harness.evals._daemon_reporting.find_project_root` (`L57`) | `start_dir or Path.cwd()` | Bỏ fallback `parents[5]`; kiểm tra `.git` / `.agents` / `workspace_context.yaml`, fallback cuối cùng `current`. |
| `ccba_harness.evals.daemon._find_hub_root_candidate` (`L88`) & `resolve_telegram_credentials` (`L108`) | `source_file or Path(__file__)` (hub) | Tìm editable Hub root chứa `seam-contracts.yaml`; giữ nguyên thứ tự quét `.env` (`cwd`, `find_project_root()`, `CCBA_HUB_PATH`, `_find_hub_root_candidate()`). |
| `ccba_harness.evals._miner_catalog._find_project_root` (`L359`) | `Path(__file__).resolve()` | Giữ kiểm tra tổ tiên có `.agents/skills/platform-loader/catalog.yaml`, fallback `Path.cwd()`. |
| `ccba_harness.evals.runner._resolve_project_root` (`L360`) | `project_root` (nếu có) else `Path.cwd()` | Bỏ qua `packages/<pkg>/pyproject.toml` nội bộ khi tổ tiên có `seam-contracts.yaml`. |
| `ccba_harness.evals.tuner._resolve_project_root` (`L129`) | `effective_root` else `self.target_file.parent` | Giữ neo `self.target_file.parent`; bỏ qua `packages/<pkg>/pyproject.toml` nội bộ. |
| `scripts/spoke/spoke_bootstrap._resolve_hub_root` (`L354`) & `check_hub_import_depth` (`L45, 81`) | `self.spoke_root` / `directory` | Đồng bộ `_workspace_roots.py` sang `scripts/_guardrails/_workspace_roots.py` trong [sdk_inspector.py](../../../scripts/spoke/sync/sdk_inspector.py#L64-L80) & `catalog_base.yaml`; giữ check candidate chứa `packages/ccba-harness` và fallback `Path(__file__).resolve().parents[3]` khi seam trả rỗng. |

### `Q3` — Seam Che Giấu Secret & PII Việt Nam (`ccba_maskara` — `[FOG-002]` Resolved)
- **Tách `PII_REGEX_PATTERNS` khỏi Pre-commit & Giữ Fallback `_miner_catalog`:**
  - `ccba_maskara/_rules.py`: giữ nguyên `REGEX_PATTERNS` (`14` rules) và mặc định `scan_text(..., include_pii: bool = False)` cho pre-commit hook. Định nghĩa `PII_REGEX_PATTERNS` gồm `email`, `phone` (`\b(?:0\d{9,10}|\+84\d{9,10})\b`), `ip-private` (`\b(?:100\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3})\b` — giữ chính xác pattern hiện tại của `_miner_catalog.py:61`), `cccd` (`(?<![-\w.])\d{12}(?![-\w.])`), và `cmnd` (`(?<![-\w.])\d{9}(?![-\w.])`).
  - **Thứ tự áp dụng bất biến:** `14` Secret rules (`env-secret` trước/theo dict `REGEX_PATTERNS`) $\to$ `email` $\to$ `phone` (biên `\b` ở hai đầu đảm bảo `001090123456` 12 số không bị `phone` ăn 11 số đầu) $\to$ `cccd` (12 số) $\to$ `cmnd` (9 số) $\to$ `ip-private`.
  - `_default_scanner` trong `ccba_maskara/__init__.py` đổi sang getter nội bộ `_get_default_scanner()` (**không** đặt trong `_LAZY_EXPORTS` / `__all__` để `check_init_lazy_exports_parity` = `0` lỗi).
  - Trong `packages/ccba-harness/src/ccba_harness/evals/_miner_catalog.py`: giữ nguyên `packages/ccba-harness/pyproject.toml` (`dependencies = ["pyyaml"]`); ưu tiên gọi `from ccba_maskara import redact_secrets_and_pii` với `dialect="bracket_suffix"`, giữ nhánh `except ImportError` fallback nhẹ khi `ccba-maskara` vắng mặt, và xóa hằng chết `SENSITIVE_PATTERNS` (`L67-L78`). Trong `packages/mdconverter/pyproject.toml`: thêm `"ccba-maskara"` (`>=1.2.0` / workspace).
- **Bảng Map `rule_id -> Token` Theo Từng `dialect` (`redact_secrets_and_pii`):**

| Nhóm Rule (`rule_id`) | `dialect="maskara"` | `dialect="bracket_suffix"` (`_miner_catalog`) | `dialect="bracket_prefix"` (`mdconverter.style`) |
| :--- | :--- | :--- | :--- |
| `env-secret` | `[MASKARA_REDACTED:env-secret]` | Giữ prefix biến + `[SECRET_REDACTED]` ở `group(1)` | Giữ prefix biến + `[REDACTED_SECRET]` ở `group(1)` |
| `anthropic-api-key`, `openai-api-key`, `google-api-key`, `github-token`, `aws-access-key`, `slack-token`, `stripe-live-key` | `[MASKARA_REDACTED:<rule_id>]` | `[API_KEY_REDACTED]` | `[REDACTED_API_KEY]` |
| `database-url` | `[MASKARA_REDACTED:database-url]` | `[DB_URL_REDACTED]` | `[REDACTED_SECRET]` |
| `private-key` | `[MASKARA_REDACTED:private-key]` | `[PRIVATE_KEY_REDACTED]` | `[REDACTED_SECRET]` |
| `jwt` | `[MASKARA_REDACTED:jwt]` | `[JWT_REDACTED]` | `[REDACTED_SECRET]` |
| `telegram-bot-token`, `groq-api-key`, `litellm-master-key` | `[MASKARA_REDACTED:<rule_id>]` | `[{RULE_ID.upper().replace('-', '_')}_REDACTED]` | `[REDACTED_API_KEY]` |
| `email` | `[MASKARA_REDACTED:email]` | `[EMAIL_REDACTED]` | `[REDACTED_EMAIL]` |
| `phone` | `[MASKARA_REDACTED:phone]` | `[PHONE_REDACTED]` | `[REDACTED_PHONE]` |
| `ip-private` | `[MASKARA_REDACTED:ip-private]` | `[IP_REDACTED]` | *(bỏ qua như `style.py`)* |
| `cccd` (`12` số) | `[MASKARA_REDACTED:cccd]` | *(bỏ qua để không đổi nghĩa log eval miner)* | `[REDACTED_CCCD]` |
| `cmnd` (`9` số) | `[MASKARA_REDACTED:cmnd]` | *(bỏ qua để không đổi nghĩa log eval miner)* | `[REDACTED_CMND]` |

### `Q4` — Phân Rã `validation/base.py` (`< 800 LOC`), Cache DOM `ParsedOOXMLPackage` & ZIP Tất Định
- **Phân rã Composition (`<= 350 LOC`/tệp, `<= 50 LOC`/hàm):** Tách `validation/base.py` (`949 LOC`) thành facade `base.py` (`~260 LOC`) + `_parsed_package.py` + `_relationship_checks.py` + `_xsd_engine.py`.
- **Factory parser an toàn (`COND-PARSER-REUSE`):** Hàm `_make_secure_xml_parser() -> lxml.etree.XMLParser` tạo instance mới `XMLParser(resolve_entities=False, no_network=True)` cho mỗi lần parse (không dùng chung parser toàn cục để tránh lỗi đa luồng và tích lũy `error_log`).
- **Kiểm kê toàn bộ điểm parse, điểm đột biến DOM cần `clone_root()` & phạm vi `pptx.py`:**
  - **`15` điểm gọi parse tệp unpacked (cổng nghiệm thu `<= 16` parse trên fixture `.docx` 16 tệp XML):** `base.py:184,210,239,347,444,465,558,613` + `base.py:848` khi gọi từ `base.py:671` (`9` điểm trong `base.py`) + `docx.py:84,133,175,220` (`4` điểm trong `docx.py`) + `redlining.py:32,82` (`2` điểm trên `word/document.xml` đã sửa cũng đọc từ `ParsedOOXMLPackage`).
  - **Nhánh kép `_validate_single_file_xsd` (`COND-XSD-DUAL-PATH`) & `3` điểm đọc tệp gốc ngoài cache (`_make_secure_xml_parser()`):** `_validate_single_file_xsd` (`base.py:835`, parse `L848`) phân tách `2` đường — lời gọi từ `base.py:671` trên file unpacked đọc `ParsedOOXMLPackage`, còn lời gọi từ `base.py:903` (`_get_original_file_errors` trên bản giải nén tạm của `original_file`) bắt buộc parse mới bằng `_make_secure_xml_parser()`; tương tự `docx.py:197` và `redlining.py:84` đọc `original_file/word/document.xml` dùng `_make_secure_xml_parser()`; `base.py:61` giữ cache XSD schema trong `_COMPILED_SCHEMA_CACHE`.
  - **5 điểm đột biến DOM bắt buộc gọi `clone_root()` (`copy.deepcopy`):** `base.py:247` (xóa `mc:AlternateContent`), `base.py:822` (`_remove_ignorable_elements`), `base.py:830` (xóa `mc:Ignorable`), `base.py:778`/`L919-921` (`_clean_ignorable_namespaces` & `_remove_template_tags_from_text_nodes` dùng `copy.deepcopy` thay `fromstring`), và `redlining.py:91-92` (`_remove_claude_tracked_changes` tại `L224,246`, chuyển `redlining.py` từ `xml.etree.ElementTree` sang `lxml.etree` dùng `clone_root()`).
  - **`pptx.py` (`pptx.py:87,141,154,204,251`):** Nằm ngoài phạm vi `PR-3a`/`PR-3b` (xếp hạng mục kế tiếp); cổng kiểm định `<= 16` parse tệp unpacked áp dụng cho `DOCXSchemaValidator` + `RedliningValidator`.
- **Chẩn đoán có cấu trúc & Quiet `stdout`:** Mọi `validate_*` trả `list[ValidationIssue]` (gắn đúng `file_path` + `line_number`). `OOXMLValidator.validate_report()` tổng hợp đủ mọi issue từ các validator con. Toàn bộ lệnh `print()` (kể cả `compare_paragraph_counts()` tại `docx.py:259` và các `FAILED`/`PASSED`) chỉ in khi `self.verbose` là `True`.
- **`8` điểm sắp xếp `glob`/`rglob` + `ZipInfo.date_time` cố định:** Sắp xếp theo `relative_to(...).as_posix()` tại cả `8` vị trí (`base.py:168,320,329,599`, `pack.py:42,48`, và gộp 2 lời gọi `unpack.py:29` thành 1 list `sorted(...)` duy nhất). Trong `pack.py:47-50`, dùng `zipfile.ZipInfo(rel_posix, date_time=(1980, 1, 1, 0, 0, 0))` + `compress_type=zipfile.ZIP_DEFLATED` để tạo tệp `.docx`/`.pptx` tất định từng byte. Giữ nguyên văn thông báo `stderr` của `bug_path_4` (`Warning: Could not pretty print` ở `unpack.py:37` và `Warning: Could not condense` ở `pack.py:67`).

### `Q5` — Thu Gọn `module_budget_baseline.json`, Đồng Bộ `AGENTS.md` / `catalog.yaml` & Tri Thức
- `PR-3a` chỉ gỡ `validation/base.py` khỏi [module_budget_baseline.json](../../../packages/ccba-harness/src/ccba_harness/module_budget_baseline.json#L1-L11); việc gỡ mục `ccba_ai/client.py: 1216` (đã xác minh `wc -l` = `753 LOC` `[đo thực tế]`) chuyển sang `PR-4` (Rollup) để tách sạch blast radius.
- Chỉ neo lại `covered_sha256` và `sync_commit` cho verifier có tệp trong `covered_paths` đổi byte (`verify-ccba-maskara` tại `PR-2` và `verify-ccba-ooxml` tại `PR-3b`), merge bằng `gh pr merge --merge`.
- Đăng ký biên bản này vào `.md/knowledge/index.md` và `.md/knowledge/log.md` tại `PR-4`.

---

## 3. Lộ Trình `5` Micro-PR Thực Thi + `1` Rollup PR (`WF-03` $\to$ `WF-06`)

| PR | Ticket | Tệp đích chính & Phạm vi thay đổi | Ước lượng `ADDED+DELETED` LOC | Phân loại `ADR-0067` | Cổng kiểm định bắt buộc |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`PR-1a`** | [WF-03](../../wayfinder/workspace-maskara-ooxml-deepening/tickets/wf_03_deepen_workspace_and_hub_root_seam.md) | `[NEW]` `_workspace_roots.py` (`<= 250 LOC` stdlib + optional `yaml`), export `WorkspaceHubContext` / `resolve_workspace_and_hub_roots` tại `ccba_harness/__init__.py` (`ast.Assign`), `packages/ccba-harness/AGENTS.md`, `catalog_base.yaml`, `sdk_inspector.py`, unit tests Delivery Spoke + `wslpath` | `~320 LOC` | `ONE_WAY_DOOR` (`PUBLIC_API_SEAM`, `CROSS_SPOKE_CONTRACT`; `exceeded_loc_budget=True`) | `check_dependency_contracts.py`, `mypy --strict`, `pytest packages/ccba-harness/tests`, `compile_catalog.py --check`, subprocess `import ccba_harness` `< 15 ms` |
| **`PR-1b`** | [WF-03](../../wayfinder/workspace-maskara-ooxml-deepening/tickets/wf_03_deepen_workspace_and_hub_root_seam.md) | Nối `10` thin adapters (`ccba_legal/registry.py`, `sync/engine.py`, `peer.py`, `_daemon_reporting.py`, `daemon.py`, `_miner_catalog.py`, `runner.py`, `tuner.py`, `spoke_bootstrap.py`, `check_hub_import_depth.py`) giữ nguyên `currency_resolver.py:251-277` (`L227` tự hưởng fix) | `~240 LOC` | `ONE_WAY_DOOR` (`CROSS_SPOKE_CONTRACT`; `exceeded_loc_budget=True`) | `test_registry_discovery.py`, `test_parser_registry.py`, `test_currency_resolver.py`, `test_tuner_daemon.py`, `test_peer_watch_cli.py`, `scripts/tests/` |
| **`PR-2`** | [WF-04](../../wayfinder/workspace-maskara-ooxml-deepening/tickets/wf_04_unify_maskara_secret_and_pii_seam.md) | Mở rộng `ccba_maskara` (`_rules.py` `PII_REGEX_PATTERNS`, `_scanner.py`, `__init__.py` `_get_default_scanner()` + `redact_secrets_and_pii` `3` dialects), `ccba-maskara/AGENTS.md`, nối `mdconverter/style.py` + `mdconverter/pyproject.toml` + `_miner_catalog.py` (giữ `ImportError` fallback) + neo `verify-ccba-maskara` (`--merge`) | `~340 LOC` | `ONE_WAY_DOOR` (`AUTHZ_SECURITY`, `PUBLIC_API_SEAM`, `DEPENDENCY_LICENSE`; `exceeded_loc_budget=True`) | `check_dependency_contracts.py`, `test_scanner.py`, `test_miner.py`, `test_log_eval_miner.py`, `test_phase1_mdconverter_seams.py`, `Semantic Mutation Proof` + `run_verify_maskara.py` |
| **`PR-3a`** | [WF-05](../../wayfinder/workspace-maskara-ooxml-deepening/tickets/wf_05_deepen_ooxml_validator_and_pack_seam.md) | Phân rã `validation/base.py` (`949 LOC` $\to$ `base.py` + `_parsed_package.py` + `_relationship_checks.py` + `_xsd_engine.py`, `<= 350 LOC`/tệp, `<= 50 LOC`/hàm), `_make_secure_xml_parser()`, `clone_root()`, gỡ riêng `validation/base.py` khỏi `module_budget_baseline.json` | `~950 LOC` (di dời cơ học + cache DOM) | `ONE_WAY_DOOR` (`exceeded_loc_budget=True` trên `packages/*`) | `check_ast_function_length`, `check_module_size_budget`, `mypy --strict`, `test_validation.py`, `test_deck_builder.py`, `verify-patch --preset code --target packages/ccba-ooxml` |
| **`PR-3b`** | [WF-05](../../wayfinder/workspace-maskara-ooxml-deepening/tickets/wf_05_deepen_ooxml_validator_and_pack_seam.md) | Nối `ParsedOOXMLPackage` vào `OOXMLValidator`, `docx.py` (`L84,133,175,220`) & `redlining.py`, trả `list[ValidationIssue]` có `line_number`, tắt `stdout` khi `verbose=False`, sắp xếp `8` `rglob()`, `ZipInfo.date_time` cố định (`pack.py`) + neo `verify-ccba-ooxml` (`--merge`) | `~260 LOC` | `ONE_WAY_DOOR` (`exceeded_loc_budget=True` trên `packages/*`) | Benchmark `<= 16` `etree.parse()` trên unpacked `.docx`, test `line_number is not None`, test deterministic ZIP SHA-256, `test_ooxml.py`, `Semantic Mutation Proof` + `run_verify_ooxml.py` |
| **`PR-4`** | [WF-06](../../wayfinder/workspace-maskara-ooxml-deepening/tickets/wf_06_ci_verification_and_wayfinder_rollup.md) | Gỡ `ccba_ai/client.py` (`753 LOC`) khỏi `module_budget_baseline.json`, chạy `verify-patch --preset ci`, `3` SSOT writers, đăng ký `.md/knowledge/index.md` + `log.md`, chốt `[FOG-003]` & đóng bản đồ `COMPLETED` | `~70 LOC` | `PAVED_ROAD` / Rollup | `verify-patch --preset ci` exit `0`, `WikiHealthLinter` & `validate_docs.py --changed` exit `0` |

---

## 4. Bộ `5` Tradeoff Cards Cho Từng Micro-PR (`RULE-1.23`)

### Card `PR-1a` (`ccba_harness` Workspace/Hub Seam & Tier-0 Sync)
- **Core Invariant:** Xuất `WorkspaceHubContext` và `resolve_workspace_and_hub_roots` (`include_agents_md=False`, bỏ qua `packages/<pkg>/pyproject.toml` nội bộ, không cache env lúc import, `wslpath` fail-soft) qua `_LAZY_EXPORTS = {...}` (`ast.Assign`) tại `ccba_harness/__init__.py` (`PUBLIC_API_SEAM`), và đồng bộ sang `scripts/_guardrails/_workspace_roots.py` (`CROSS_SPOKE_CONTRACT`).
- **Invalidation Condition:** Hoàn tác tức thì `git revert` trên `PR-1a` nếu `check_init_lazy_exports_parity` báo vi phạm AST, `import ccba_harness` vượt `15 ms`, hoặc `test_harness_suite.py` phát sinh lỗi hồi quy.
- **Git Hunk Reference:** `packages/ccba-harness/src/ccba_harness/__init__.py#L1-L25`

### Card `PR-1b` (`10` Thin Adapters & `ccba_legal` Mock Surface Preservation)
- **Core Invariant:** Nối `10` hàm dò root trên `ccba_legal`, `ccba_harness`, `scripts/spoke` thành thin adapters truyền `start_dir` tương ứng (`Path(__file__).resolve()` cho `resolve_project_root()`), bỏ `parents[5]` fallback ở `_daemon_reporting.py`, giữ nguyên `discover_master_registry_path()` gọi `resolve_project_root()` tại `L85` và giữ nguyên `_discover_currency_card_path()` (`CROSS_SPOKE_CONTRACT`).
- **Invalidation Condition:** Revert `PR-1b` nếu `test_registry_discovery.py`, `test_parser_registry.py`, `test_currency_resolver.py`, `test_tuner_daemon.py` hoặc `test_peer_watch_cli.py` thất bại.
- **Git Hunk Reference:** `packages/ccba-legal-intel/src/ccba_legal/registry.py#L27-L54`

### Card `PR-2` (`ccba_maskara` PII Separation, `3` Placeholder Dialects & `mdconverter`)
- **Core Invariant:** Giữ `REGEX_PATTERNS` mặc định cho pre-commit hook (`include_pii=False`), tách `PII_REGEX_PATTERNS` với `\b` trên SĐT trước guard UUID `(?<![-\w.])\d{12}(?![-\w.])`, dùng `_get_default_scanner()` nội bộ (không đưa vào `_LAZY_EXPORTS`), nối `mdconverter.style` + `_miner_catalog` (`ImportError` fallback, `ccba-maskara` ở `mdconverter/pyproject.toml`), và neo `verify-ccba-maskara` bằng `--merge` (`AUTHZ_SECURITY`, `PUBLIC_API_SEAM`, `DEPENDENCY_LICENSE`).
- **Invalidation Condition:** Revert `PR-2` nếu `check_dependency_contracts.py` báo lỗi, `test_maskara_suite.py` / `test_miner.py` / `test_log_eval_miner.py` / `test_phase1_mdconverter_seams.py` gãy assertion placeholder, hoặc pre-commit chặn nhầm metadata.
- **Git Hunk Reference:** `packages/ccba-maskara/src/ccba_maskara/__init__.py#L30-L56`

### Card `PR-3a` (`validation/base.py` Composition Split & Safe `ParsedOOXMLPackage`)
- **Core Invariant:** Chia nhỏ `validation/base.py` (`949 LOC`) thành facade + `_parsed_package.py` + `_relationship_checks.py` + `_xsd_engine.py` (`<= 350 LOC`/tệp, `<= 50 LOC`/hàm), dùng factory `_make_secure_xml_parser()` (`resolve_entities=False, no_network=True`) mỗi lần parse kèm `clone_root()` (`copy.deepcopy`) cho mọi đột biến DOM, và chỉ gỡ `validation/base.py` khỏi `module_budget_baseline.json` (`exceeded_loc_budget`).
- **Invalidation Condition:** Revert `PR-3a` nếu `test_validation.py` hoặc `test_deck_builder.py` phát hiện sai khác kết quả XSD/unique ID hay `check_ast_function_length` báo hàm vượt `50 LOC`.
- **Git Hunk Reference:** `packages/ccba-ooxml/src/ccba_ooxml/validation/base.py#L155-L182`

### Card `PR-3b` (`OOXMLValidator` Structured Diagnostics, Quiet `stdout` & Deterministic ZIP)
- **Core Invariant:** Chia sẻ `1` `ParsedOOXMLPackage` qua `DOCXSchemaValidator` (`docx.py:84,133,175,220`) và `RedliningValidator` (`clone_root()`), trả `list[ValidationIssue]` có `file_path` + `line_number`, gated `print()` sau `self.verbose`, sắp xếp `8` điểm `rglob()`, cố định `ZipInfo.date_time=(1980, 1, 1, 0, 0, 0)` ở `pack.py` (giữ `stderr` `bug_path_4`), và neo `verify-ccba-ooxml` bằng `--merge`.
- **Invalidation Condition:** Revert `PR-3b` nếu `run_verify_ooxml.py` lệch `bug_path_4`, `test_ooxml.py` lỗi pack/unpack, `lxml.etree.parse()` vượt `16` lần trên unpacked `.docx`, hoặc 2 lần `pack_document()` khác byte SHA-256.
- **Git Hunk Reference:** `packages/ccba-ooxml/src/ccba_ooxml/pack.py#L40-L65`

---

## 5. Nhật Ký Thẩm Định Ngang Hàng (`WF-02` Peer Plan Audit Trail)

| Vòng | Profile | Phiên Grok (`session_id`) | Phán quyết (`verdict`) | `risk_score` | `blocking_conditions` | Biên bản cục bộ |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| Pass 1 | `audit_plan` | `bbf5de60-3b77-4605-b224-1cad5dc02335` | `REVISE_PLAN` | `4` | `3` (`COND-PII-DIALECT`, `COND-WS-ANCHOR`, `COND-OOXML-SHARE`) + `5` non-blocking | `.md/peer_exchange/grok_workspace_maskara_ooxml_plan.md` |
| Pass 2 | `signoff_diff` | `f044627a-7a05-410f-afff-6fd52351166d` | `APPROVE_PLAN` | `2` | `0` (`2` non-blocking pins: `COND-XSD-DUAL-PATH`, `COND-MAP-SYNC`; `$0.299`, `192.25s`) | `.md/peer_exchange/grok_workspace_maskara_ooxml_plan_signoff_p2.md` |

- **Kiểm tra hợp lệ `door-triage --enforce-tradeoff-card` (`PR-1a`..`PR-3b`):** `5/5` card trả `exit=0`, `tradeoff_card_valid=true`, `tradeoff_card_errors=[]`, `status=approval_required` (`ADR-0067` chờ xác nhận `proceed` từ Kỹ sư Trưởng).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
