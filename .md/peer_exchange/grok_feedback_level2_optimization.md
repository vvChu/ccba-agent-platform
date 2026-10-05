---
request_id: req-level2-discuss-001
verdict: APPROVE_WITH_CONDITIONS
conditions:
  - id: cond-1-cli-slug-namespace
    description: "Bảng profile phải dùng slug của Grok CLI (qwen-local, gemini-38-flash, claude-sonnet-4-6, claude-opus-4-6, grok-4.7, grok-4.7-build-fast). Slug qwen-local đi dây tới qwen-local-primary qua chat_completions, cửa sổ 32768. Cấm đưa kết quả choose_model() thẳng vào grok -m. Chuỗi model chỉ sống trong YAML profile, một chỗ, kèm chú thích allow-raw-model."
    blocking: true
  - id: cond-2-headless-turn-budgets
    description: "Mọi profile chạy headless qua --prompt-file. --max-turns và --tools bị TUI bỏ qua. AGENTIC_CODE đặt --max-turns 8 với model batch được tool (grok-4.7-build-fast, claude-sonnet-4-6). PATCH_FAST đặt --max-turns 1 và cấm tool, kèm span đã nhúng sẵn. --single một mình vẫn mở vòng tool."
    blocking: true
  - id: cond-3-anchor-patch
    description: "Hợp đồng PATCH_FAST là bản ghi neo {path, blob_sha256, replacements[{old, new}]}. Bộ áp dụng từ chối khi hash lệch hoặc old không xuất hiện đúng một lần. Diff do harness sinh sau khi áp. Parser hiện tại chỉ nhận YAML frontmatter; --json-schema chỉ được bật sau khi extractor đọc structured_output và vẫn ghi được PeerVerdictBlock."
    blocking: true
  - id: cond-4-reuse-invoke-shim
    description: "Mở rộng invoke_grok_cli và thêm subcommand ccba-harness peer-dispatch. scripts/peer_dispatch.py chỉ là shim ủy quyền, cùng kiểu scripts/peer_bridge_watcher.py. Cấm hai implementation. Profile khai báo trong YAML (model, max_turns, tools, timeout, tier)."
    blocking: true
  - id: cond-5-worktree-handoff-verify
    description: "AGENTIC_CODE chạy --worktree --no-subagents. stop_reason max_turns hoặc no_progress ghi phong bì HANDOFF và không merge. Orchestrator giữ verify-patch (ADR-0058) ngoài ngân sách turn. Timeout theo profile thay cho mặc định 180 giây của invoke_grok_cli."
    blocking: true
  - id: cond-6-qwen-pilot-and-allowlist
    description: "AUDIT_PLAN allowlist đúng tên tool read_file,grep,list_dir và chặn sửa file, terminal, subagent, cùng MCP meta-tool. qwen-local chưa được đặt làm coder mặc định cho đến khi pilot 5 task đo tool_call JSON hợp lệ, parser qwen3_coder một lớp, thinking tắt, và prompt nằm dưới trần context. stream_tool_calls = false nếu đối số tool bị méo."
    blocking: true
  - id: cond-7-cost-ledger
    description: "ADR-0063 chỉ chuyển Accepted sau pilot có num_turns, stop_reason, usage và cost. total_cost_usd vắng mặt nghĩa là chưa được stamp, không phải 0 USD. Mục tiêu tiết kiệm đo trên hóa đơn coding, tách khỏi phiên audit grok-4.7. Cấm ghi mức giảm 85% trên tổng 10.49 USD vào ADR."
    blocking: true
risk_score: 3
effort: M
summary: "Chấp thuận hướng Level-2 (ba profile, headless, local cho patch nhỏ) với 7 điều kiện chặn: slug CLI tách khỏi archetype gateway, trần turn 8 và patch neo theo hash, tái sử dụng invoke_grok_cli, worktree kèm verify-patch phía orchestrator, và pilot tool-call trước khi khóa ADR-0063."
---

# PHẢN BIỆN LEVEL-2 PEER DELEGATION (ADR-0063)

> **Người phản biện**: Grok Peer Reviewer
> **Tác giả đề xuất**: Antigravity
> **Yêu cầu**: `req-level2-discuss-001` (`discuss`)
> **Thời điểm**: 2026-10-05
> **Phán quyết**: `APPROVE_WITH_CONDITIONS`

Hướng ba profile là đúng seam hiện có. `invoke_grok_cli` trong `packages/ccba-harness/src/ccba_harness/peer.py` đã gọi `grok --prompt-file` kèm `--no-subagents`. ADR-0063 nên mở rộng hàm đó bằng profile khai báo. Bảy điều kiện trong frontmatter là cửa trước khi chuyển ADR sang Accepted.

Bằng chứng đối soát trong phiên này:

- `grok --help` và `grok models` (CLI 1.0.46 trên máy này): có `--max-turns`, `--tools`, `--disallowed-tools`, `-p/--single`, `--prompt-file`, `--json-schema`, `--worktree`, `--output-format`.
- `~/.grok/docs/user-guide/14-headless-mode.md`: `--max-turns` và `--tools` chỉ có hiệu lực ở headless. TUI in cảnh báo rồi bỏ qua.
- `~/.grok/config.toml` mục `[model.*]`: ánh xạ slug, backend, cửa sổ context. Khối provider chứa `api_key` trực tiếp. Log dispatcher không được in file này. Chuyển khóa sang `env_key` trước khi chạy rộng.
- `packages/ccba-ai/src/ccba_ai/routing.py`: `ModelArchetype.LOCAL = qwen-local-primary`. `choose_model("coding")` trả `gemini-3.7-flash`.
- `.agents/skills/ccba-vllm-manager/SKILL.md`: parser tool `qwen3_coder`, cấm parser kép ở LiteLLM, thinking token làm JSON rỗng.

Phiên này không bắn probe tool-call sống vào `qwen-local` hay `gemini-38-flash`. Nhận định về độ ổn định tool-call là suy từ hợp đồng backend và skill vận hành. Pilot ở điều kiện 6 là phép đo còn thiếu.

---

## 1. Đọc lại hóa đơn 10.49 USD

| Phiên | Model | Calls | Token | Cache hit | USD |
|---|---|---:|---:|---:|---:|
| Planning / Audit | `grok-4.7` (xhigh) | 24 | 2.1M | 92.5% | 4.87 |
| PR-1 Catalog Stale Gate | `grok-4.7-build-fast` | 54 | 5.5M | 91.5% | 2.51 |
| PR-2 Dynamic Bindings | `grok-4.7-build-fast` | 30 | 2.6M | 95.3% | 1.19 |
| PR-3 Guardrails Sync | `grok-4.7-build-fast` | 43 | 4.0M | 91.1% | 1.92 |
| **Tổng** | | **151** | | | **10.49** |

Coding cộng lại là **5.62 USD** (53.6%). Audit là **4.87 USD** (46.4%). Đưa coding về GPU local bỏ phần 5.62 USD. Phần audit trên `grok-4.7` vẫn nằm đó. Mức giảm của cả đợt là khoảng một nửa, với điều kiện hóa đơn gateway của Claude/Gemini không phát sinh chỗ khác.

Cache hit 91–95% nghĩa là các turn sau chủ yếu đọc lại prefix đã cache. Token input cộng dồn làm phình bộ đếm, trong khi tiền nằm ở input chưa cache và ở output mỗi turn. Headless ghi `usage.input_tokens` là phần chưa cache, và `cache_read_input_tokens` là phần hit (`14-headless-mode.md`). Báo cáo sau này phải tách hai trường đó.

`num_turns` đếm vòng của agent chính. `modelUsage.*.modelCalls` cộng cả subagent. `[features] subagent_model_inheritance = true` trong config làm subagent đi theo model của cha. `--max-turns` không trần được hóa đơn subagent. `--no-subagents` là chốt chi phí đứng cạnh trần turn.

`total_cost_usd` chỉ xuất hiện khi server stamp đủ. Document headless nói rõ: vắng trường này là chưa báo cáo, và đường OAuth/pool thường bỏ trống. Gateway `chat_completions` có thể đứng ngoài hóa đơn xAI. `grok usage` báo 0 với Claude hoặc Qwen là lỗ hổng sổ sách khi trường cost bị bỏ. Sổ ADR phải ghi `cost_is_partial` và hóa đơn gateway riêng.

`invoke_grok_cli` đang timeout 180 giây và không truyền `--max-turns`. Bốn PR 30–54 call nằm ngoài hàm này, hoặc hàm này đã bị timeout nuốt. Gắn profile vào đúng hàm này thì các phiên sau mới chịu trần.

---

## 2. Câu 1 — Tool-calling của local và gateway

### Hai backend khác nhau

| Slug `grok -m` | Model trên dây | Backend | Context trong config |
|---|---|---|---:|
| `grok-4.7` | `grok-4.7` | Responses API, xAI | 256000 (catalog còn bậc 500000) |
| `grok-4.7-build-fast` | `grok-4.7-build-fast` | Responses API, xAI | 256000 |
| `gemini-38-flash` | `gemini-3.8-flash-high` | `chat_completions` qua `:8090` | 1000000 |
| `claude-sonnet-4-6` | `claude-sonnet-4-6` | `chat_completions` | 200000 |
| `claude-opus-4-6` | `claude-opus-4-6` | `chat_completions` | 200000 |
| `qwen-local` | `qwen-local-primary` | `chat_completions` | **32768** |

Model xAI dùng Responses API. Tool-call là đường bậc một của CLI. Đây là đường đã chạy 151 call của đợt ADR-0062.

Model gateway dùng Chat Completions. CLI dịch tool nội bộ sang `tool_calls` kiểu OpenAI. Ổn định khi gateway trả JSON `tool_calls`. Ổn định gãy khi model trả XML/Hermes thô trong `content`, hoặc khi parser chạy hai lần.

`grok models` xác nhận máy này đã login và default là `gemini-38-flash`. Dispatcher bỏ `-m` sẽ audit bằng Flash. Mọi lệnh profile phải truyền `-m` tường minh.

### Qwen trên DGX

Skill `ccba-vllm-manager` yêu cầu vLLM `--tool-call-parser qwen3_coder` và `--reasoning-parser qwen3`. LiteLLM của cùng endpoint bị cấm thêm `tool_call_parser: openai`. Parser kép làm méo đối số.

Thinking đang bật thì tool loop hay chết kiểu `finish_reason: length`, `content` rỗng. Profile coding local phải đi alias đã `enable_thinking: false` (skill gọi là `local-instruct`), hoặc gửi `chat_template_kwargs.enable_thinking = false`. System prompt không tắt được thinking.

Cửa sổ runner là 32768. Skill vẫn ghi `--max-model-len 24576`. Trần thật là số nhỏ hơn trong hai nguồn, và pilot phải đọc lỗi context đầu tiên để chốt. Prompt peer của repo này (hiến pháp, `AGENTS.md`, schema tool, file nguồn) vượt 32k trước khi tới đoạn cần sửa. Khi đó runner compact hoặc từ chối request. `qwen-local` làm coder ReAct thay cho các phiên 2.6–5.5M token là sai cỡ cửa sổ.

`stream_tool_calls` đang không set trên `[model.qwen-local]`. Guide model tùy chỉnh nói một số endpoint BYOK vỡ khi cờ này bật, và lối thoát là `stream_tool_calls = false` ngay trong block model. Pilot bật cờ này nếu đối số tool về dạng chuỗi cụt.

Độ ổn định kỳ vọng, trước pilot:

- Sửa một span đã nhúng, một completion, không tool: dùng được, giá GPU.
- Vòng đọc file, sửa, pytest nhiều turn: chưa đủ chứng cứ. Context 32k và thinking là hai điểm gãy đã được skill ghi nhận.
- Audit ADR, pháp lý, hiến pháp: ở lại `grok-4.7`. `is_reasoning_model("qwen-local-primary")` trong `routing.py` trả false. ADR-0059 không đi qua model local cho văn bản quy phạm.

### Gemini 3.8 Flash và Claude qua gateway

`gemini-38-flash` có context 1M và là fallback sẵn trong `peer.py` (`DEFAULT_FALLBACK_AUDITOR_MODEL`). Hợp vai nháp audit khi `grok-4.7` lỗi. Vai primary của `AUDIT_PLAN` vẫn là `grok-4.7`, đúng hằng số `DEFAULT_PRIMARY_AUDITOR_MODEL`. Flash trên Chat Completions gọi tool được khi gateway dịch schema sang function-calling của Google. Lỗi thường gặp là bịa nội dung file sau một lần `read_file` cụt. Verdict `FINAL_ACCEPT` trên ADR hoặc hiến pháp cần model primary.

`claude-sonnet-4-6` là coder gateway hợp lý khi pilot tool-call đạt. Hóa đơn nằm ở gateway. `claude-opus-4-6` là tầng leo thang cho audit khó. Đưa Opus vào danh sách tiết kiệm chi phí làm lệch sổ: chất lượng cao, invoice khác chỗ, thường đắt hơn `grok-4.7` trên cùng một audit.

### Format tool-call cần khóa trong profile

- xAI: để CLI dùng Responses API mặc định. Cấm đổi `api_backend` của các slug grok sang `chat_completions`.
- Gateway: kỳ vọng `tool_calls[].function.name` và `arguments` là chuỗi JSON. Tên tool là tên built-in của Grok (`read_file`, `grep`, `list_dir`, `search_replace`, `run_terminal_command`).
- Guide headless có chỗ ghi denylist `run_terminal_cmd`. Bảng tool ở `01-getting-started.md` ghi `run_terminal_command`. Pilot xác nhận identifier nào CLI nhận, rồi ghi chết vào YAML.
- Tên `grep_search` trong đề xuất không có trong bảng tool. Allowlist audit là `read_file,grep,list_dir`.
- `--tools` vẫn để MCP meta-tool sống, trừ khi bị deny riêng. `AUDIT_PLAN` chưa read-only nếu MCP còn ghi được file. Profile phải deny MCP write và `spawn_subagent`.
- Guide headless: một turn có thể gom nhiều tool song song thành một message. Model xAI làm được việc này. Model coder nhỏ thường phát một tool mỗi turn. Ngân sách turn phải giả định một tool mỗi turn cho đến khi pilot đo tỷ lệ `num_turns` trên số tool.

---

## 3. Câu 2 — Trần turn của `AGENTIC_CODE`

Một turn trong họ `--max-turns` là một vòng model của agent chính (`num_turns` trong kết quả headless). Subagent không tăng bộ đếm này.

Đường happy-path cho một PR đã có test đỏ, đường dẫn file, và lệnh pytest đúng, trên model gom được tool:

1. Đọc test, đọc nguồn, `grep` (một turn nếu gom song song).
2. `search_replace`.
3. Pytest.
4. Nếu đỏ: đọc log và sửa.
5. Pytest lại.
6. Ghi `PeerVerdictBlock`.

Sáu turn là đúng đường đó khi chỉ có một vòng sửa và không có file phát sinh. Hết slack. Thêm một lần đọc lệch offset, một lệnh pytest sai, hoặc một file thứ hai thì turn thứ sáu rơi vào giữa pytest. `StopCancelled` bắn `reason=max_turns` trước khi có verdict. `invoke_grok_cli` hôm nay coi stdout không có `PeerVerdictBlock` là thất bại. Phần tệp đã sửa vẫn nằm trên đĩa.

Đề xuất "2 vòng sửa + 2 vòng test" chưa tính turn đọc và turn ghi verdict. Cộng đủ là sáu turn ở mức tối thiểu, bằng trần, nên trần bị ăn mất ngay lần lệch đầu tiên.

Chốt:

| Profile / model | `--max-turns` | Lý do |
|---|---:|---|
| `AGENTIC_CODE` + `grok-4.7-build-fast` hoặc `claude-sonnet-4-6` | **8** | Một vòng sửa, một turn đọc thêm, một turn verdict |
| `AGENTIC_CODE` khi prompt đã nhúng test đỏ và span, và pilot chứng minh gom tool | 6 chỉ là mục tiêu vận hành, trần vẫn 8 | Trần 6 biến mục tiêu thành điểm dừng |
| `AGENTIC_CODE` + `qwen-local` | không phải mặc định | Nếu pilot bắt buộc vòng tool: trần 12, prompt rút gọn, abort khi turn 1 báo context |
| `AUDIT_PLAN` + `grok-4.7` | 12 | Đọc có chủ đích, không sửa. Đủ cho audit cỡ ADR-0062 vừa rồi (24 call có subagent và không trần) |
| `PATCH_FAST` | **1** | Một completion. Xem mục 4 |

`AUDIT_PLAN` trên Qwen với trần 12 vẫn chết vì cửa sổ 32k. Audit ở lại cloud hoặc Opus khi được leo thang.

Khi chạm trần, dispatcher ghi HANDOFF: `stop_reason`, danh sách file worktree, lệnh test cuối, log cuối. Orchestrator quyết định giữ worktree hay xóa. Nhánh làm việc của orchestrator giữ sạch, khớp khóa claim trong `docs/rules/execution_guardrails.md`.

`verify-patch` (ADR-0058) thuộc orchestrator, sau khi agent trả cây. Nhét verify-patch vào tám turn sẽ ăn mất vòng sửa. Pytest trong profile là pytest đã ghi trong prompt, một lệnh, qua `--allow`, hẹp hơn là mở `run_terminal_command`.

Timeout gợi ý trong YAML: `PATCH_FAST` 120s, `AGENTIC_CODE` 600s, `AUDIT_PLAN` 900s. Mức 180s hiện tại cắt nhầm phiên coding hợp lệ.

Routing theo `effort` đã có trên `PeerVerdictBlock`:

- `XS`: `PATCH_FAST`.
- `S`: `PATCH_FAST` khi span nhúng vừa cửa sổ. Không thì `AGENTIC_CODE` trần 8.
- `M`: `AGENTIC_CODE` trên `grok-4.7-build-fast` hoặc Sonnet.
- `L` / `XL`: cắt tiếp thành micro-PR (RULE-2.13, khoảng 150–200 LOC một seam). Cấm dồn vào trần 8.

---

## 4. Câu 3 — Patch một completion

`--single` và `--prompt-file` mở headless với một prompt người dùng và vẫn có tool loop. Guide headless viết rõ chế độ này "executes it with full tool access". Muốn một completion thì đặt `--max-turns 1` và gỡ tool (`--disallowed-tools` phủ read, edit, terminal, subagent, web). Model không được gọi `read_file` ở turn duy nhất, vì turn đó kết thúc trên tool call và không còn lượt để phát patch.

Antigravity nhúng vào prompt: đường dẫn, `blob_sha256` của bytes hiện tại, và đoạn nguồn cần sửa. Thiếu hash thì applicator từ chối.

Hợp đồng đầu ra là bản ghi neo, bọc trong verdict markdown để `parse_verdict_from_md` vẫn chạy:

```markdown
---
request_id: req-...
verdict: GATE_PASS
conditions: []
risk_score: 1
effort: XS
summary: "Thay đúng một đoạn trong foo.py."
---

```ccba-patch
{
  "files": [
    {
      "path": "packages/ccba-harness/src/ccba_harness/foo.py",
      "blob_sha256": "<sha256 hex của toàn bộ bytes file trước khi sửa>",
      "replacements": [
        {
          "old": "đoạn nguồn y nguyên, duy nhất trong file",
          "new": "đoạn thay"
        }
      ]
    }
  ]
}
```
```

Applicator:

1. Đọc bytes, tính SHA-256, so với `blob_sha256`. Lệch thì dừng. Đây là chốt offset drift và chốt sửa đè khi file đã đổi.
2. Đếm `old`. Khác 1 thì dừng. Cấm replace-all.
3. Thay đúng chuỗi đó. Giữ nguyên newline và khoảng trắng của phần còn lại.
4. Harness tự sinh unified diff để người đọc. Model không phát số dòng.
5. Orchestrator chạy pytest của prompt, rồi `python -m ccba_harness verify-patch`.

Giới hạn profile: tối đa 3 file, một seam, tổng dòng thêm và dòng bớt không quá 100. Vượt ngưỡng thì chuyển `AGENTIC_CODE` trước khi gọi model.

Unified diff do model viết tay lệch khi model đếm dòng, sửa mất dấu cách cuối, hoặc context trùng ở hai chỗ. `git apply` dùng context nên vẫn trượt khi context bị viết lại. Số dòng trong diff chỉ là gợi ý. Vì vậy diff không phải hợp đồng. Diff là sản phẩm của harness sau bước 3.

`--json-schema` ép cả stdout thành JSON và kéo theo `--output-format json`. `_run_single_grok_attempt` hiện ghi nguyên stdout và gọi `parse_verdict_from_md`. JSON trần làm parser trả `None`, hàm trả thất bại dù patch đúng. Bước triển khai: dispatcher dùng `--output-format json`, lấy `text` hoặc `structured_output`, `num_turns`, `stop_reason`, `usage`, rồi mới render file markdown cho `.md/peer_exchange/`. Bật `--json-schema` sau khi extractor đó có test.

Patch Qwen chỉ chạy khi prompt đã render nhỏ hơn trần đã đo. Prompt tràn thì cùng hợp đồng neo, model `grok-4.7-build-fast`, vẫn `--max-turns 1`.

---

## 5. Câu 4 — Rủi ro trước khi khóa ADR-0063

1. **Lẫn namespace model.** `qwen-local` là slug CLI. `qwen-local-primary` là alias gateway và `ModelArchetype.LOCAL`. `choose_model("coding")` đang ra `gemini-3.7-flash`. Truyền alias gateway vào `grok -m` sẽ trượt catalog CLI. Truyền slug CLI vào `ccba_ai` sẽ trượt gateway. YAML profile giữ slug CLI. Seam `choose_model` giữ alias gateway. Hai bảng, một hướng ánh xạ, ghi trong ADR.

2. **Cờ trần bị TUI nuốt.** Profile nào cũng headless. Lệnh mẫu nằm trong test của `peer-dispatch` để khóa `--prompt-file`, `--max-turns`, `--no-subagents`.

3. **Worktree và claim.** Sửa dở trên cây đang claim làm peer khác đọc nhầm trạng thái. `--worktree` cô lập. HANDOFF khi `max_turns` hoặc `no_progress`. Cấm commit WIP lên nhánh PR từ dispatcher.

4. **`verify-patch` ngoài vòng agent.** Agent báo pytest của mình. Orchestrator mới được gọi hoàn tất. Khớp ADR-0058 và khóa hoàn tất tất định.

5. **Quyền tool.** Config người dùng đang `permission_mode = "always-approve"`, và `invoke_grok_cli` cũng truyền `--always-approve`. Với Qwen, allowlist tool cộng `--allow` cho đúng một lệnh pytest. `AUDIT_PLAN` không có terminal và không có `search_replace`.

6. **Sổ chi phí hai nơi.** Local GPU là hết tiền token xAI. Claude và Gemini qua `:8090` chuyển invoice sang gateway. ADR ghi cả hai sổ. Pilot lưu JSON headless cạnh verdict.

7. **Mức 85%.** Con số đó mô tả một kỳ vọng trên đường patch so với 30–54 call, và nó chưa được đo. Tổng đợt này không giảm 85% chừng nào audit còn trên `grok-4.7`. ADR ghi mục tiêu đo được: `num_turns` coding ≤ 8, và USD coding trên một PR cỡ PR-2/PR-3 so với mốc 1.19 và 1.92, sau ít nhất ba PR pilot.

8. **Pháp lý và hiến pháp.** `AUDIT_PLAN` cho thay đổi ADR, `AGENTS.md`, hoặc bundle VBPL giữ model primary `grok-4.7`. Local không phát `FINAL_ACCEPT` trên các đường đó.

9. **Bí mật.** Provider gateway đang để khóa trong `config.toml`. Dispatcher và log peer không dump file này. `ccba-maskara` trên stdout JSON trước khi ghi `.md/peer_exchange/`.

10. **Máy và đường dẫn.** Profile YAML không ghi đường dẫn tuyệt đối Windows hay IP `100.83.192.30`. Hub path lấy từ `CCBA_HUB_PATH`. Khớp invariant multi-device.

11. **Reuse-first.** Đã có `invoke_grok_cli`, `run_peer_watch_cli`, và shim `scripts/peer_bridge_watcher.py`. `peer-dispatch` là subcommand cùng kiểu `peer-watch`. Script wrapper một hàm ủy quyền. Logic profile một bản trong `ccba_harness`.

12. **Số ADR.** `docs/adr/` dừng ở 0062. 0063 đang trống. Giữ số này cho protocol, và chỉ đánh Accepted sau pilot cộng `verify-patch` của chính PR triển khai.

### Profile sau khi sửa

| Profile | Model CLI | Turns | Tool | Việc orchestrator giữ |
|---|---|---:|---|---|
| `AUDIT_PLAN` | `grok-4.7` (high/xhigh). Leo thang: `claude-opus-4-6`. Fallback có sẵn: `gemini-38-flash` | 12 | `read_file`, `grep`, `list_dir` | Verdict và quyết định có code hay không |
| `AGENTIC_CODE` | `grok-4.7-build-fast`. Thay thế sau pilot: `claude-sonnet-4-6`. `qwen-local` chưa phải mặc định | 8 | đọc, `search_replace`, pytest đã `--allow` | `verify-patch`, merge, claim |
| `PATCH_FAST` | `qwen-local` nếu prompt vừa trần đã đo. Không thì `grok-4.7-build-fast` | 1 | không | Áp neo, pytest, `verify-patch` |

Tier `local | gateway | cloud` vẫn hữu ích như nhãn sổ sách. Nó chọn dòng trong bảng slug. Nó không thay cho `-m`.

### Pilot tối thiểu trước Accepted

Năm việc có test đỏ sẵn, mỗi việc chạy ba slug: `qwen-local`, `gemini-38-flash`, `grok-4.7-build-fast`. Ghi `tool_call` JSON hợp lệ, file đúng hash, pytest, `num_turns`, `stop_reason`, `usage.input_tokens`, `cache_read_input_tokens`, và cost nếu được stamp. Một slug vào mặc định của profile khi cả năm việc đạt trên slug đó. Thiếu số thì slug ở lại mục leo thang thủ công.

PR triển khai sau đó đi qua `python -m ccba_harness verify-patch` như mọi thay đổi harness khác.
