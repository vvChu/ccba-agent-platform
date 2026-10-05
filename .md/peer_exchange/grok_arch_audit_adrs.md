---
request_id: "req-arch-audit-adrs-001"
verdict: APPROVE_WITH_CONDITIONS
conditions:
  - id: COND-01
    description: "Khóa lại lệch sandbox trước mọi vòng peer tiếp theo. PATCH_FAST phải có --max-turns 1 như ADR-0063 (hiện PROFILE_SPECS để max_turns null và chỉ --deny *). agentic_code phải allowlist đúng công cụ đã cam kết (đọc, search_replace, pytest có phạm vi) và reasoning_effort high. Profile arch_audit phải được ghi vào bảng ADR-0063 hoặc bị gỡ khỏi mã. PeerVerdictBlock phải thống nhất extra=forbid với đoạn schema trong ADR-0064, hoặc ADR phải sửa thành extra=ignore và liệt kê đúng các phép cưỡng chế."
    blocking: true
  - id: COND-02
    description: "Cấm ghép verdict APPROVE khi stdout chỉ có AnchorPatchPayload. _run_single_grok_attempt đang tự tạo PeerVerdictBlock APPROVE. Patch neo chỉ là đầu vào của apply_anchor_patch. Phán quyết giữ nguyên HANDOFF cho đến khi một profile reviewer trả về PeerVerdictBlock thật và verify-patch thoát 0 ở tiến trình orchestrator, ngoài worker."
    blocking: true
  - id: COND-03
    description: "Bỏ khẳng định zero-hang tuyệt đối. _SYNC_MUTEX là threading.Lock trong một tiến trình và đang được giữ suốt invoke_grok_cli (timeout profile 120s–900s). update_live_summary ghi grok_live_summary.md không qua FileMutexLock. Nhánh timeout gọi kill() mà không wait() lần hai và không giết process group. session_id dùng chung cho mọi model fallback. Fallback chat_history.jsonl đọc cả tệp, không trần kích thước. ADR-0065 phải sửa các điểm này trước khi mở watcher đa tiến trình."
    blocking: true
  - id: COND-04
    description: "ADR-0062 nói vòng phụ thuộc hoặc lỗi đọc trong discover_package_topology trả về DEFAULT_PACKAGE_TOPOLOGY_ORDER. Mã chỉ trả default khi exception hoặc kết quả rỗng. Nút kẹt chu trình bị nối thêm vào cuối danh sách. Neo ccba-harness và ccba-ai bị kéo lên vị trí 0 và 1 kể cả khi in_degree khác 0. Hằng PACKAGE_TOPOLOGY_ORDER cấp module vẫn trỏ danh sách tĩnh. Sửa cho khớp lời ADR trước lần sync --apply kế tiếp trên hub có package mới."
    blocking: true
  - id: COND-05
    description: "Trước peer thứ ba, đưa AgentIdentity, tiền tố tệp, PROFILE_SPECS và bảng giá token ra cấu hình khai báo. Envelope hiện là Literal antigravity|grok với extra=forbid. classify_file_role và status.json gắn cứng hai tên. seam-contracts.yaml chưa có thẻ cho ccba_harness.peer. Cấm mở N-agent bằng cách nối thêm tên vào Literal."
    blocking: false
  - id: COND-06
    description: "Ban hành phụ lục truy vết cho ADR-0060, ADR-0063 và ADR-0064. ADR-0060 tự gọi là 4 hub nhưng mục quyết định nêu năm tên (dgx-spark-toolkit, ccba-agent-platform, ccba-legal-knowledge, VvC_Notes, IDOP-CCBA-WAY). ADR-0063 và ADR-0064 dẫn ADR-0007 là Peer Exchange và ADR-0009 là Pstack. Trong thư mục docs/adr, 0007 là multimodal YouTube và 0009 là hub-spoke sync. Module peer.py cũng ghi docstring ADR-0007. Sửa trích dẫn và bảng đếm hub. Không đưa .agents/teams hay giao thức gRPC vào ADR-0060 khi văn bản quyết định không có các mục đó."
    blocking: false
risk_score: 3
effort: L
summary: "Chuỗi ADR-0060 đến ADR-0064 đứng được như các quyết định đã Accepted. Bốn lệch đang có hiệu lực trong mã (sandbox, APPROVE giả, khóa chỉ trong một tiến trình, topo nuốt chu trình) chặn Level-3 và chặn peer thứ ba cho đến ADR-0065."
telemetry:
  session_id: "dad11d76-1486-4976-baed-bdebc12413c7"
  primary_model: "grok-4.7-build"
  input_tokens: 713399
  output_tokens: 26997
  reasoning_tokens: 19321
  cached_read_tokens: 560256
  total_tokens: 740396
  model_calls: 13
  turn_count: 3
  cost_usd: 0.2545
  cost_mode: "exact"
  duration_seconds: 546.0
---

# Báo Cáo Thẩm Định Kiến Trúc (Architecture Audit Report)

**Phạm vi:** ADR-0060, ADR-0061, ADR-0062, ADR-0063, ADR-0064, đối chiếu Hiến pháp Layer 1 (`AGENTS.md`) và mã đã nạp: `packages/ccba-harness/src/ccba_harness/peer.py`, `peer_gate.py`, `telemetry.py`, `_mutex.py`, `scripts/spoke/spoke_bootstrap.py`, `scripts/spoke/sync/coordinator.py`, `scripts/governance/check_dependency_contracts.py`, `seam-contracts.yaml`, `packages/ccba-harness/AGENTS.md`, `.gitignore`.

**Cách đọc số đo.** Khối `telemetry` mang `cost_mode: unknown` và các số 0 vì ADR-0064 cấm mô hình tự kê token. Harness ghi đè bằng `grok usage` sau khi tiến trình kết thúc. Các số trong khối này không phải số đo phiên.

**Phán quyết.** `APPROVE_WITH_CONDITIONS`, rủi ro 3, effort L. Hướng kiến trúc giữ nguyên trạng thái Accepted. Bốn điều kiện chặn áp vào bước tiến hóa kế tiếp và vào mọi vòng tự động hóa mới. Chúng không đòi hủy năm ADR.

## 1. Tính nhất quán và phân tách trách nhiệm

Đặt Peer Exchange, anchor patch, dispatcher và telemetry vào `ccba_harness.peer` khớp vai trò harness: cổng xác minh ADR-0058, điều phối tiến trình, hợp đồng phán quyết. `packages/ccba-harness/AGENTS.md` đã khai báo Deep Seam công khai `apply_anchor_patch`, `extract_anchor_payload`, `run_apply_anchor_patch_cli`, `run_peer_dispatch_cli`. `__init__.py` xuất `apply_anchor_patch` và `invoke_grok_cli`. Tách một package `ccba-peer` mới sẽ đẻ silo thứ hai cho cùng một việc điều phối.

Ranh giới với `ccba-ai` được ADR-0063 viết rõ và mã tuân theo hướng đó. `PROFILE_SPECS` và `TIER_DEFAULT_MODELS` chứa slug CLI (`grok-4.7`, `qwen-local`, `gemini-38-flash`, `claude-sonnet-4-6`) kèm chú thích `# ccba:allow-raw-model`. `ccba_ai.routing.choose_model` giữ alias gateway. Test routing map `audit` tới `ModelArchetype.REASONING`. Dispatcher không đưa kết quả `choose_model()` vào `grok -m`. Đây là tách mặt phẳng đúng, có ngoại lệ hiến pháp được đánh dấu.

Chồng lấn còn lại nằm ở giá và ở chỉ mục seam:

- `ccba_harness.telemetry` định giá một bảng duy nhất: 1.25 USD / 1M token vào và 5.00 USD / 1M token ra. `extract_grok_session_telemetry` dùng bảng này cho mọi model khi thiếu `costUsdTicks`, kể cả `qwen-local`. Reasoning token và cached token được lưu, rồi bị bỏ qua khi nhân giá. Sổ `status.json` làm tròn bốn chữ số nên một ước lượng sai vẫn trông như số quyết toán.
- `seam-contracts.yaml` có các thẻ `legal_markdown.v1`, `ooxml_processor.v1`, `pdf_preprocessor.v1`, `legal_ingest.v1`, `legal_advisor.v1`. Không có thẻ nào cho `ccba_harness.peer` hay `peer-dispatch`. ADR-0061 bắt buộc chỉ mục máy đọc. `find-seam` không thể phát biên lai cho năng lực này. Peer thứ ba sẽ không có hợp đồng để tái sử dụng.

`peer.py` gánh schema, quét thư mục, status, patch, subprocess và telemetry trong một module hơn một nghìn dòng. Vị trí package là đúng. Độ rộng module là điểm ma sát cho ADR-0065, giải bằng cấu hình khai báo, không bằng package mới.

Bảng đếm hub của ADR-0060 lệch với chính nó và lệch với hồ sơ yêu cầu thẩm định. Mục quyết định đặt tên năm hub: Compute `dgx-spark-toolkit`, Governance `ccba-agent-platform`, Legal `ccba-legal-knowledge`, Synthesis `VvC_Notes`, Operations `IDOP-CCBA-WAY`. Tiêu đề ADR ghi "4-Hubs". Hồ sơ yêu cầu ghi `ccba-ai-gateway` và `ccba-bim-knowledge` là hai hub. Trong văn bản ADR, LiteLLM là proxy trên Compute Hub. BIM nằm ở nhóm Federated Spokes (`bim-planner`), không phải hub thứ tư. Văn bản ADR-0060 cũng không lập `.agents/teams/` và không chuẩn hóa CLI/REST/gRPC. Những mục đó đứng ngoài quyết định đã Accepted.

ADR-0063 dòng tương thích và ADR-0064 dòng tương thích cùng dẫn "ADR-0007 (Peer Exchange)" và "ADR-0009 (Pstack Disciplines)". Tệp `0007` là multimodal YouTube. Tệp `0009` là hub-spoke sync. Docstring của `peer.py` lặp lại "ADR-0007". Ma trận truy vết Layer 1 đang trỏ sai quyết định. Đây là lỗi sổ, chưa phải lỗi runtime.

## 2. Hiến pháp Layer 1 và Platform-Aware KISS v2.0

Hai pha trong `apply_anchor_patch` là bước kiểm tối giản đúng việc nó làm. Pha 1 chặn path traversal bằng `is_relative_to`, chặn tệp trùng, đối chiếu SHA-256 từng byte, yêu cầu mỗi chuỗi `old` xuất hiện đúng một lần, chuẩn hóa CRLF về LF trước khi so. Pha 2 ghi bằng `atomic_write_text` và hoàn nguyên từ bản trong bộ nhớ nếu một bước ghi ném exception. Khoảng một trăm dòng cho hợp đồng neo là KISS.

Lời "transactional rollback ACID" vượt quá cơ chế đó. Không có undo log bền. Tiến trình chết giữa tệp thứ nhất và tệp thứ hai để lại commit một phần. `atomic_write_text` không `fsync` trước `replace`. Tệp `.bak` không nằm trong tập hoàn nguyên. Thân ADR-0063 mô tả hash và uniqueness. Cụm ACID xuất hiện ở help CLI và ở mô tả yêu cầu thẩm định. Giữ hai pha. Bỏ chữ ACID khỏi hợp đồng.

Cưỡng chế Pydantic đang lệch schema đã in trong ADR-0064. ADR in `PeerVerdictBlock` với `extra="forbid"`. Mã đặt `extra="ignore"`. `PeerCondition` cũng `extra="ignore"`, và validator đổi điều kiện dạng chuỗi thành object có `blocking: true`. `risk_score` là `int | None`, không có biên 1–5. `PeerVerdictTelemetry` lại `extra="forbid"`. Lớp telemetry khắt khe, lớp phán quyết nuốt trường lạ. Nuốt trường lạ che lệch schema giữa các peer. Phép đổi chuỗi điều kiện là shim tương thích có ích. Nó cần được ghi trong ADR nếu được giữ.

Các mảng ADR-0061 đã có mã đối ứng:

- `check_dependency_contracts.py` duyệt `[node.lineno, end_lineno]`, đọc marker `# ccba:quarantine`, cấm `..` `/` `\` trong `seam_id`, kiểm `seam_id` thuộc card và card có quản trị module bị cấm, kiểm `until` theo ngày UTC, và có rule `QuarantineExpiredViolation`.
- ADR ghi giới hạn thật: client HTTP thô (`urllib`, `requests`) không đi qua import thuộc danh mục cấm thì AST không thấy. Giới hạn này vẫn mở.
- `assess_catalog_freshness` khớp ADR-0062. Catalog lệch khi `--apply` và không có cờ vượt trả `catalog_stale`. `dry_run` cảnh báo rồi trả `None`. `--allow-stale-catalog` in `CATALOG_STALE_BYPASS` rồi trả `None`, kể cả khi `check_catalog_in_sync` ném exception. `--force` không nằm trong hàm này. Đây là cổng fail-closed đạt.

Topo package là chỗ ADR-0062 nói một đằng, mã làm một nẻo. Docstring và ADR: chu trình hoặc lỗi đọc thì trả `DEFAULT_PACKAGE_TOPOLOGY_ORDER`. Mã trả default khi `except` hoặc khi `ordered` rỗng. Vòng lặp cuối nối mọi nút chưa xếp vào danh sách đã xếp. Chu trình bị nuốt thành một thứ tự trông hợp lệ. Hai neo bị `append` trước khi xét `in_degree` của chính chúng, rồi trừ `in_degree` của hàng xóm. Kết quả có thể không phải thứ tự topo. `PACKAGE_TOPOLOGY_ORDER = DEFAULT_PACKAGE_TOPOLOGY_ORDER` vẫn còn ở cấp module. `resolve_target_packages` gọi `discover_package_topology` trên nhánh fallback, nên đường bootstrap chính có dùng hàm discover. Hằng tĩnh vẫn là bẫy cho caller sau.

Hiến pháp đòi từ khóa và trọng số ở cấu hình khai báo. ADR-0062 đã làm vậy cho guardrail. Profile peer, giá token và danh tính agent vẫn là literal Python. Thêm một agent là sửa mã và sửa parser. Đó là vi phạm OCP ngay trong chuỗi ADR vừa viết ra nguyên tắc OCP.

Cô lập trạng thái máy đạt một phần. Đường session dùng `Path.home() / ".grok" / "sessions"`, không commit ổ đĩa Windows. ADR-0061 cấm đường dẫn tuyệt đối trong `workspace_context.yaml` và đưa regex raw-string / ổ đĩa vào linter. `.gitignore` chỉ loại `.md/peer_exchange/.bridge_cache.json` và `*.lock`. `status.json` cùng `grok_live_summary.md` vẫn là trạng thái sống, dấu thời gian gắn cứng `UTC+7` trong `update_status_json` và `update_live_summary`. ADR-0060 RULE-5.5 yêu cầu mốc thời gian vận hành đổi sang UTC trước khi so chỉ mục. Hai máy clone cùng một cây sẽ ghi đè hai tệp này. `publish_peer_message` chạy đồng bộ trong thread daemon và nuốt mọi exception. Mất cập nhật status thì không có dấu vết.

`peer_gate.check_ast_function_length` chặn hàm dài hơn 50 dòng. `apply_anchor_patch`, `extract_grok_session_telemetry`, `_run_single_grok_attempt`, `invoke_grok_cli` và `update_status_json` đều vượt ngưỡng đó theo khoảng dòng đã đọc. Lượt này không chạy `verify-patch`. Đây là sức căng với ADR-0058, chưa phải một lần CI thất bại đã quan sát.

## 3. Zero-hang, deadlock, và thang N-agent

Những chốt headless sau đã có trong mã và đáng giữ:

- `build_grok_cmd` luôn kết thúc bằng `--prompt-file`. Không có prompt vị trí.
- `stdin=subprocess.DEVNULL`, `--output-format plain`, `--always-approve`, `--no-subagents`.
- Vòng `Popen.poll()` có deadline theo timeout của profile.
- `grok usage` nằm trong ngân sách 3.0 giây, tối đa ba lần, ngủ 100 ms, rồi `TokenEstimator`. Có `costUsdTicks` thì `cost_usd = ticks / 10000` và `cost_mode = exact`.
- `FileMutexLock` bảo vệ `status.json` và `.bridge_cache.json`, có nhận PID chết và hạn 300 giây trong lớp khóa tệp.
- `_clean_completed_threads` gỡ thread đã chết khỏi `_PENDING_THREADS`.

Những chốt đó không triệt tiêu deadlock, zombie, hay rò bộ nhớ.

`_SYNC_MUTEX` chỉ có hiệu lực trong một process. `run_sync_cycle` giữ khóa này trong lúc gọi `invoke_grok_cli`. Timeout theo profile là 900 giây (`audit_plan`), 600 giây (`agentic_code`, `arch_audit`), 300 giây (`code_review`), 120 giây (`patch_fast`). Mốc 180 giây chỉ là default của profile không tên và timeout lệnh trong `peer_gate`. Watcher và publisher là hai process thì không thấy khóa này. Ghi `status.json` được khóa tệp theo kiểu last-writer-wins trên một registry đã đọc từ trước. `update_live_summary` không lấy `FileMutexLock`.

Nhánh hết hạn gọi `terminate()`, `wait(2)`, rồi `kill()` và `return False` không `wait()` lần hai. Không có `start_new_session` hay kill theo process group. Tiến trình cháu của CLI có thể sống sau khi process cha đã bị SIGKILL. `--no-subagents` thu hẹp bề mặt, không đóng nó.

Watchdog thấy `output_path` có mtime sau lúc bắt đầu và nội dung parse được verdict hoặc anchor thì giết CLI. Tệp còn dở mà đã parse được sẽ cắt phiên trước khi `grok usage` kịp ghi. Telemetry rơi về estimator. An toàn vận hành giữ được. Xuất xứ mô hình thì yếu đi.

`session_id` được tạo một lần rồi truyền cho mọi model trong vòng fallback. Lần thử sau dùng lại UUID của lần thử trước. Usage có thể trộn hai model hoặc không thấy phiên.

Fallback `chat_history.jsonl` quét `~/.grok/sessions/**/<session_id>/chat_history.jsonl` và `read_text()` cả tệp. Không có trần byte. Đây là đỉnh bộ nhớ thật, không phải rò rỉ thread. Thread daemon chết theo process nếu không ai gọi `flush_pending_peer_triggers`. Đó là mất việc, không phải leak dài hạn.

Mỗi `scan_peer_exchange` đọc mọi tệp `.md` để dựng registry. Cache SHA-256 chỉ lọc danh sách delta. Thư mục peer lớn thì mỗi chu kỳ là O(n) lần đọc đầy. Không có chính sách lưu trữ.

Thang N-agent dừng ở kiểu dữ liệu:

- `AgentIdentity = Literal["antigravity", "grok"]`. Envelope `extra="forbid"`. Tên thứ ba không qua parser.
- `classify_file_role` nhận `prompt_grok_`, `grok_`, `antigravity_response_`, `grok_request_antigravity_`.
- `status.json` khai báo đúng hai peer.
- `compute_pending_queues` khóa theo `request_id` toàn cục, không theo cặp `(request_id, to_agent)`. Trùng id thì một phản hồi đóng nhầm prompt khác.
- Một `grok_live_summary.md` là điểm ghi chung. N watcher sửa tệp này tái lập vòng inotify đã được ghi trong trao đổi peer trước. Mutex trong process không xử lý việc đó.

`cost_mode: unknown` có trong `Literal` và không bao giờ được gán. Cả nhánh estimator cũng ghi `estimated`. Giá một bảng làm sổ FinOps của `qwen-local` (ADR-0063 ghi 0 USD) và của model cloud dùng chung một đơn giá.

## 4. Lệch có hiệu lực giữa ADR và mã

| Điểm | Văn bản đã Accepted | Mã đang chạy |
|---|---|---|
| PATCH_FAST | Trần 1 turn, không tool | `max_turns: None`, cờ `--max-turns` bị bỏ, có `--deny *` |
| agentic_code | Đọc, `search_replace`, pytest có phạm vi. ADR-0064: effort `high` | `tools: None`, cấm mỗi `spawn_subagent`, `reasoning_effort: None` |
| arch_audit | Không có trong bảng ADR-0063 | Có trong `PROFILE_SPECS`: 8 turn, 600 giây, `xhigh`, cấm terminal và ghi |
| PeerVerdictBlock | ADR-0064 in `extra=forbid` | `extra=ignore`, cưỡng chế điều kiện dạng chuỗi, `risk_score` không biên |
| APPROVE | Phán quyết do peer trả về | Anchor JSON hợp lệ được bọc thành `verdict: APPROVE` |
| Watchdog 180 giây | Hồ sơ thẩm định nêu 180 giây là mặc định | 180 giây chỉ cho profile lạ. Profile có tên dùng 120–900 giây |
| Khóa đồng bộ | Mô tả như chốt tuần tự an toàn | `threading.Lock` một process. Summary không khóa tệp |
| Chu trình topo | Trả `DEFAULT_PACKAGE_TOPOLOGY_ORDER` | Nối nút còn lại vào cuối danh sách |
| Đếm hub | Tiêu đề 4 hub | Thân ADR nêu 5 tên. Hồ sơ yêu cầu nêu một bộ 4 tên khác |
| Trích dẫn | ADR-0007 Peer Exchange, ADR-0009 Pstack | 0007 YouTube, 0009 hub-spoke sync |
| Seam card | ADR-0061 bắt buộc chỉ mục | `seam-contracts.yaml` không có peer dispatch |
| Giá | Exact khi có `costUsdTicks`, ước lượng khi không | Ước lượng dùng một đơn giá, không theo `primary_model` |

ADR-0063 tuyên bố phủ test 100% cho profile, `build_grok_cmd` và `apply_anchor_patch`. Lượt thẩm định này không chạy pytest và không chạy `verify-patch`. Tuyên bố phủ đó chưa được xác nhận lại ở đây.

## 5. ADR-0065 và Level-3 Autonomous Loopback

Level-3 theo nghĩa peer đề xuất patch, CI tự verify, rồi tự commit và tự prompt lại: chưa đủ điều kiện. Năm lý do cùng đứng trong mã hiện tại.

1. Worker tự cấp `APPROVE` cho một JSON neo. Cổng chất lượng mất nghĩa ngay khi vòng lặp tin trường `verdict`.
2. ADR-0058 giữ `verify-patch` ở orchestrator. Worker không được tự nhận hoàn tất khi mã thoát khác 0. Quyền commit và claim issue cũng nằm ngoài worker, theo invariant khóa claim đa client.
3. `agentic_code` rộng hơn bảng công cụ đã cam kết. Vòng tự sửa sẽ có terminal mà ADR nói là không có.
4. Trần turn là theo lần gọi. Không có trần USD tích lũy cho vòng re-prompt. Chuỗi audit 12 turn nhân nhiều vòng vượt bài học chi phí mà ADR-0063 dùng để biện minh cho chính nó (151 lần gọi, 10.49 USD).
5. Danh tính và hàng đợi chưa có chỗ cho peer thứ ba. Vòng loopback cài thêm Claude hoặc Codex sẽ vá literal và tiền tố tệp, đúng việc hiến pháp cấm khi đã có seam.

ADR-0065 nên là một phụ lục siết hợp đồng, không phải một nền điều phối mới. Phạm vi đủ để gỡ bốn điều kiện chặn:

- Một tệp khai báo profile (slug, turn, tool, deny, effort, timeout). Mã chỉ nạp tệp đó. Chú thích allow-raw-model đứng trên tệp đó.
- Anchor không verdict thì HANDOFF. `apply_anchor_patch` chỉ chạy khi orchestrator gọi. `verify-patch` chạy sau apply, cùng process với orchestrator.
- Khóa tệp cho cả status và summary. Không giữ khóa trong lúc subprocess chạy. Kill theo process group rồi `wait`. UUID mới cho mỗi lần thử model. Đọc `chat_history.jsonl` có trần byte.
- Chu trình topo trả default, đúng câu ADR-0062, hoặc fail-closed với mã riêng. Hằng module `PACKAGE_TOPOLOGY_ORDER` trở thành lời gọi `discover_package_topology`.
- Thẻ `peer_dispatch.v1` trong `seam-contracts.yaml`, `binding.mode: local_import`, cấm Spoke gọi CLI grok trần như một substitute. Bảng giá theo model, hoặc `cost_mode: unknown` khi không có đơn giá của đúng `primary_model`.
- Phụ lục sửa năm tên hub, bỏ trích dẫn 0007/0009 sai, và ghi rõ teams cùng gRPC không thuộc ADR-0060.
- `status.json` và `grok_live_summary.md` là trạng thái sinh ra. Timestamp UTC. Chúng cần luật merge hoặc nằm ngoài cây commit.

Hình Level-3 chỉ được viết thành ADR sau khi các mục trên đã xanh `verify-patch`. Hình đó, khi tới lượt, là: orchestrator áp anchor, chạy verify, commit trên nhánh không phải `main`, push bằng `--force-with-lease`, không tự merge. Re-prompt dừng khi hết trần USD của vòng. Quyền vào `main` vẫn ở ngoài vòng máy.

## 6. Điều kiện, theo thứ tự thi công

COND-01 và COND-02 sửa trong `peer.py` cùng một lần với test đối ứng trong `packages/ccba-harness/tests/test_peer.py`. Đó là lỗ hổng đang mở trên mọi lần dispatch.

COND-03 sửa vòng đời subprocess và đường ghi status/summary trước khi bật watcher đa process.

COND-04 sửa `discover_package_topology` cho khớp câu chữ ADR-0062 trước lần `--apply` trên cây package có chu trình hoặc có package mới.

COND-05 và COND-06 là việc của ADR-0065 và của một phụ lục truy vết. Chúng không chặn vận hành hai peer hiện tại.

Phán quyết này không yêu cầu hạ trạng thái Accepted của ADR-0060 đến ADR-0064. Nó cấm dùng chuỗi đó làm căn cứ để mở Level-3 hoặc thêm danh tính peer khi bốn điều kiện chặn còn mở.
