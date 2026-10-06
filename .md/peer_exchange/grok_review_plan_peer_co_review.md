---
request_id: req-plan-peer-co-review-001
verdict: REVISE_PLAN
conditions:
- id: COND-01
  description: Lập bậc ưu tiên tổng trên mọi thành viên VerdictType trong peer.py,
    gồm APPROVE, APPROVE_WITH_CONDITIONS, APPROVE_WITH_RESERVATIONS, APPROVE_PLAN,
    REVISE_PLAN, REJECT_PLAN, REJECT, FINAL_ACCEPT, GATE_PASS, GATE_FAIL và HANDOFF.
    Lớp chặn gồm REJECT, REJECT_PLAN và GATE_FAIL. Cấm nhánh else gán APPROVE. Test
    bắt buộc set(precedence) bằng set(get_args(VerdictType)). Nếu mọi tác nhân cùng
    một token thì consensus giữ nguyên token đó. HANDOFF của profile bắt buộc thắng
    APPROVE và APPROVE_WITH_CONDITIONS. Chỉ điều kiện blocking true mới được nâng
    lớp PASS lên APPROVE_WITH_CONDITIONS. APPROVE_WITH_RESERVATIONS không được đổi
    thành APPROVE.
  blocking: true
- id: COND-02
  description: Hợp đồng quorum gồm expected_profiles, completed_profiles và failed_profiles.
    invoke_grok_cli chỉ trả bool. False, timeout, hoặc parse_verdict_from_md bằng
    None là profile thất bại và không được tổng hợp thành lớp PASS. Orchestrator không
    trả None khi lỗi. Trước mỗi lần gọi, bản sao envelope phải ghi đè profile và output_path,
    vì file kết quả luôn là thư mục của prompt cộng basename của envelope.output_path,
    và session id đã được tạo bên trong invoke. Giữ nguyên chữ ký invoke_grok_cli.
    Khi CCBA_GROK_MODEL có giá trị, truyền model lấy từ PROFILE_SPECS của đúng profile.
    Timeout mặc định lấy từ spec của profile, code_review 300 giây và arch_audit 600
    giây. Một cờ timeout trên CLI chỉ là override có chủ đích.
  blocking: true
- id: COND-03
  description: synthesize_verdicts duyệt đúng thứ tự profiles đầu vào, không theo
    thứ tự future hoàn thành. Khóa chống trùng mô tả phải gộp blocking bằng phép OR
    và giữ đủ source_profile. Thêm trường tùy chọn PeerCondition.source_profile vì
    extra ignore sẽ bỏ trường lạ khi parse lại. Không nhét prefix hồ sơ vào id hoặc
    description. risk_score hợp nhất là max các điểm hợp lệ từ 1 đến 5. Verdict lớp
    PASS đi kèm risk từ 4 trở lên phải thành APPROVE_WITH_CONDITIONS hoặc REVISE_PLAN.
  blocking: true
- id: COND-04
  description: File trung gian đặt trong TemporaryDirectory chế độ 0700, ngoài cây
    peer_exchange. Profile chỉ được khớp mẫu chữ thường, chữ số và gạch dưới, dài
    1 đến 32 ký tự. Không ghi stem.profile.tmp.md cạnh prompt. scan_peer_exchange
    đọc mọi file kết thúc bằng .md, và classify_file_role gắn tiền tố prompt_ thành
    PROMPT_TO_GROK, nên auto_grok sẽ gọi thêm grok trên bản sao. Chỉ publish một file
    phản hồi grok_*.md bằng atomic_write_text sẵn có. Giữ verdict từng profile ngoài
    thư mục scan, nếu không status.json cộng trùng token và latest_verdict đổi theo
    mtime. Trên Windows invoke không đặt start_new_session, nên timeout phải hủy cả
    cây tiến trình con. Dọn thư mục run trong finally. Hai lần chạy đồng thời không
    được dùng chung một đường dẫn output.
  blocking: true
- id: COND-05
  description: Constructor PeerVerdictTelemetry trong kế hoạch thiếu session_id và
    primary_model, trong khi model đang extra forbid và cost_mode chỉ nhận exact,
    estimated hoặc unknown, nên bước hợp nhất sẽ ném ValidationError. Tạo model CombinedTelemetry
    riêng, có breakdown theo profile gồm model, input, output, reasoning_tokens, cached_read_tokens,
    cost và duration, cộng wall_seconds tách khỏi sum_agent_seconds. cost_mode exact
    chỉ khi mọi thành phần là exact. Khối frontmatter công bố ra cầu nối phải có khóa
    conditions bằng danh sách đã gộp. Tên consolidated_conditions bị parse_verdict_from_md
    bỏ qua, và số điều kiện chặn trên status sẽ bằng 0.
  blocking: true
- id: COND-06
  description: Không thêm majority vote. Không gắn veto tuyệt đối cứng cho arch_audit.
    Bảng precedence và danh sách profile bắt buộc là cấu hình khai báo. Tái sử dụng
    PROFILE_SPECS và atomic_write_text. max_workers mặc định bằng số profile và có
    trần nhỏ, không dùng mặc định ThreadPoolExecutor. Dry-run in kế hoạch dispatch
    và không gọi model. Mã thoát CLI tách PASS, CONDITIONS, REVISE, REJECT, INCOMPLETE
    và lỗi usage. Đăng ký orchestrate_peer_co_review, synthesize_verdicts, PeerConsensusReport
    và run_peer_co_review_cli trong AGENTS.md của package cùng __all__ của ccba_harness.
    Kế hoạch phải kèm test cho lattice đầy đủ, quorum, dedup OR, thứ tự tất định,
    cách ly watcher, telemetry hai model, và CLI, trước khi mở nhánh mã.
  blocking: true
risk_score: 4
effort: L
summary: REVISE_PLAN. Hướng pessimistic merge phù hợp ADR-0065, nhưng bậc ưu tiên
  hiện tại biến REJECT_PLAN và GATE_FAIL thành APPROVE, constructor telemetry không
  khớp PeerVerdictTelemetry, và file tạm *.tmp.md trong peer_exchange bị watcher dispatch
  lại. Chưa viết mã cho đến khi COND-01 đến COND-06 nằm trong kế hoạch.
telemetry:
  session_id: cfe9e556-7389-49b8-a0ed-f71723f3757c
  primary_model: grok-4.7-build
  input_tokens: 518042
  output_tokens: 40128
  reasoning_tokens: 35245
  cached_read_tokens: 457600
  total_tokens: 558170
  model_calls: 12
  turn_count: 1
  cost_usd: 200753.68
  cost_mode: exact
  duration_seconds: 636.15
---
# Phán quyết: REVISE_PLAN

Risk 4/5. Level-2.5 nên đi tiếp bằng pessimistic merge, cách ly session, và giữ nguyên chữ ký `invoke_grok_cli`. Đoạn hợp nhất trong kế hoạch chưa được phép đưa vào nhánh mã. Ba lỗi này phá cổng đang chạy trên `main`:

- `REJECT_PLAN` và `GATE_FAIL` rơi xuống nhánh `else` và thành `APPROVE`.
- `PeerVerdictTelemetry(...)` trong kế hoạch thiếu field bắt buộc, `extra=forbid`, nên `synthesize_verdicts` ném lỗi trên đường thành công.
- File `*.tmp.md` đặt cạnh prompt trong `.md/peer_exchange` bị `scan_peer_exchange` đọc lại và có thể bị `auto_grok` dispatch thêm.

Bất biến đã khóa ở `peer.py` (ADR-0065): không bịa `APPROVE`. Nhánh `else: consensus_verdict = "APPROVE"` vi phạm bất biến đó.

## 1. Bậc ưu tiên và điều kiện

`VerdictType` hiện có 11 token (`peer.py` dòng 49–61). Bậc trong kế hoạch chỉ gọi tên 5 token. Mọi token còn lại đi vào `else` và thành `APPROVE`.

| Tập đầu vào | Đoạn mã trong kế hoạch | Token cần ra |
|---|---|---|
| `REJECT_PLAN` | `APPROVE` | `REJECT_PLAN` |
| `GATE_FAIL` | `APPROVE` | `GATE_FAIL` |
| `APPROVE_PLAN` | `APPROVE` | `APPROVE_PLAN` |
| `APPROVE_WITH_RESERVATIONS` | `APPROVE` | `APPROVE_WITH_RESERVATIONS` |
| `REJECT_PLAN` + `APPROVE_WITH_CONDITIONS` | `APPROVE_WITH_CONDITIONS` | `REJECT_PLAN` |
| `HANDOFF` kèm `conditions` | `APPROVE_WITH_CONDITIONS` | `HANDOFF` |
| `HANDOFF` + `APPROVE` | `HANDOFF` | `HANDOFF` |
| `REJECT` + `REVISE_PLAN` | `REJECT` | `REJECT` |
| Một profile lỗi, profile kia `APPROVE` | `APPROVE` vì profile lỗi không vào dict | `HANDOFF` |
| `APPROVE` + điều kiện `blocking=false` | `APPROVE_WITH_CONDITIONS` | `APPROVE` |
| `APPROVE` + điều kiện `blocking=true` | `APPROVE_WITH_CONDITIONS` | `APPROVE_WITH_CONDITIONS` |

`parse_verdict_from_md` loại token nằm ngoài `Literal` trước khi vào hàm hợp nhất. Lỗ hổng nằm ở token đã hợp lệ nhưng chưa có trong bậc: `REJECT_PLAN`, `GATE_FAIL`, `APPROVE_PLAN`, `APPROVE_WITH_RESERVATIONS`, `FINAL_ACCEPT`, `GATE_PASS`.

Câu chữ kế hoạch và đoạn mã cũng lệch nhau. Câu “chỉ có `HANDOFF`” đọc như mọi người đều `HANDOFF`. Mã lại coi một `HANDOFF` là đủ, rồi vẫn để nhánh `conditions` chạy trước và hạ `HANDOFF` có điều kiện thành `APPROVE_WITH_CONDITIONS`.

`blocking` được copy sang điều kiện gộp nhưng không tham gia bậc ưu tiên. `any(v.conditions)` nâng cả ghi chú không chặn thành cổng. Dedup theo `description.strip().lower()` giữ bản gặp trước và bỏ bản sau. Nếu bản `blocking=false` vào dict trước, bản `blocking=true` cùng mô tả bị mất. Thứ tự này theo completion của thread thì người thắng còn đổi giữa các lần chạy.

Không có deadlock trong `synthesize_verdicts` vì hàm thuần. Hai kẹt vận hành khác là có thật:

- Cổng CI đòi `APPROVE` sạch, trong khi mọi ghi chú đều thành `APPROVE_WITH_CONDITIONS`, nên vòng review không thoát.
- Watcher thấy prompt tạm, gọi thêm `invoke_grok_cli`, và các tiến trình chồng tới timeout của profile.

Thuật toán cần bốn quy tắc, viết thành bảng khai báo:

1. Mọi token của `VerdictType` có đúng một hạng. Test khóa `set(precedence) == set(get_args(VerdictType))`.
2. Nếu mọi tác nhân cùng một token, consensus giữ đúng token đó.
3. Lớp giảm dần: chặn (`REJECT`, `REJECT_PLAN`, `GATE_FAIL`), rồi `REVISE_PLAN`, rồi `HANDOFF` của profile bắt buộc, rồi có điều kiện (`APPROVE_WITH_CONDITIONS`, `APPROVE_WITH_RESERVATIONS`), rồi PASS (`APPROVE_PLAN`, `FINAL_ACCEPT`, `GATE_PASS`, `APPROVE`).
4. Điều kiện `blocking=true` chỉ được nâng một token lớp PASS lên `APPROVE_WITH_CONDITIONS`. Điều kiện gắn với `HANDOFF` hoặc `REJECT*` không được đổi lớp.

Verdict công bố phải thuộc `VerdictType` hiện tại. Profile thiếu hoặc timeout dùng `HANDOFF` cộng một điều kiện blocking mô tả profile lỗi. Token mới kiểu `INCOMPLETE` chỉ được thêm khi `Literal` và mọi consumer đổi trong cùng một thay đổi.

`risk_score` lấy max trong các điểm từ 1 đến 5 là đúng. `max(S)` khi `S` rỗng thì bằng 1, khớp `ge=1`. PASS với risk từ 4 trở lên không được mang token `APPROVE` trần.

## 2. Cách ly file

Hậu tố `<stem>.<profile>.tmp.md` chưa đủ trên Linux lẫn Windows.

`invoke_grok_cli` không nhận đường dẫn output từ ngoài. Nó luôn ghi `prompt_path.parent / Path(envelope.output_path).name` (`peer.py` khoảng dòng 1323–1324). Session id cũng đã là `uuid.uuid4()` bên trong hàm (khoảng dòng 1369). Bản sao prompt chỉ an toàn khi envelope được ghi đè cả `profile` lẫn `output_path` trước khi gọi, và chữ ký hàm giữ nguyên.

`scan_peer_exchange` nhận mọi tên kết thúc bằng `.md` (khoảng dòng 529–530). `classify_file_role` gán `prompt_*` thành `PROMPT_TO_GROK` (khoảng dòng 468–469). File `prompt_foo.code_review.tmp.md` trong `.md/peer_exchange` là một prompt mới. `auto_grok` sẽ gọi thêm một Grok nữa trên bản sao đó.

Nếu nhiều file `grok_*.md` cùng `request_id` nằm trong thư mục scan:

- `update_status_json` cộng token của từng file (khoảng dòng 632–646), nên telemetry cá nhân cộng với telemetry consensus bị tính hai lần.
- `_build_latest_verdict` chọn theo `mtime` (khoảng dòng 604), nên phán quyết “mới nhất” đổi theo file nào ghi sau.

`atomic_write_text` đã có (khoảng dòng 390): ghi file tạm kèm pid và `time_ns`, retry khi Windows khóa file. Kế hoạch nên gọi hàm đó cho đúng một file `grok_*.md` cuối. File nháp nằm trong `TemporaryDirectory` mode `0700`, xóa trong `finally`.

Trên Windows còn ba điểm hậu tố không xử lý: đĩa không phân biệt hoa thường (`Arch_Audit` và `arch_audit` thành một file), tên thiết bị `CON`, `AUX`, `NUL`, `PRN`, và `invoke` không đặt `start_new_session` (`peer.py` khoảng dòng 1196–1197) nên `proc.terminate()` không hạ cây con. Timeout trên Windows phải hủy cả cây. Hai lần `peer-co-review` cùng prompt phải có `run_id` riêng.

## 3. Majority vote và veto

Không thêm majority vote. Với hai hoặc ba profile, đa số giấu một phiếu chặn. Cổng này lấy mức nghiêm hơn, cùng hướng với quy tắc không bịa `APPROVE`.

Không gắn veto tuyệt đối cứng cho `arch_audit`. `REJECT` của profile nào trong lần dispatch cũng đã là veto sau khi lattice đủ. Veto riêng sẽ làm `REJECT` của `code_review` thành ngoại lệ khó thấy. Profile bắt buộc là dữ liệu của lần chạy: mặc định mọi profile được dispatch đều bắt buộc. Profile optional là cấu hình sau này, không phải nhánh đặc biệt trong code.

## 4. Ngân sách máy trạm

`ThreadPoolExecutor` là chỗ chờ đúng, vì `invoke_grok_cli` đã tạo subprocess và đã có `_terminate_proc_tree`. Không cần `ProcessPoolExecutor` cho bước chờ này.

`PROFILE_SPECS` đang cấp `code_review` model `gemini-38-flash`, timeout 300 giây, và `arch_audit` model `grok-4.7`, timeout 600 giây. Wall clock một lần song song là max của hai bên, cộng fallback nếu model chính trả bool `False`. Hai tiến trình CLI gọi model cloud/gateway, nên CPU máy trạm không phải điểm nghẽn. RAM hai client CLI nhỏ.

Điểm nghẽn thật:

- `CCBA_GROK_MODEL` đang được xét trước model của profile (`peer.py` khoảng dòng 1356–1367). Cả hai profile sẽ chạy cùng một model, và có thể là model đắt, nếu orchestrator không truyền `model=` từ `PROFILE_SPECS`.
- Quota gateway khi số profile tăng. `max_workers` phải bằng số profile và có trần nhỏ. Mặc định của `ThreadPoolExecutor` (tới 32) không dùng được.
- Watcher dispatch đệ quy làm số tiến trình nhân lên.
- Model local chỉ thành điểm nghẽn GPU khi env kéo cả hai profile về model local.

Giữ chạy song song làm mặc định để còn đủ điều kiện của cả hai profile. `--fail-fast` hủy profile còn lại sau một token lớp chặn là tùy chọn tiết kiệm, không phải mặc định. Dry-run in profile, model, timeout, đường dẫn output, rồi thoát, không gọi CLI.

## Tương thích với cầu nối đang chạy

`PeerVerdictTelemetry` bắt buộc `session_id` và `primary_model`, `extra=forbid`, `cost_mode` chỉ `exact | estimated | unknown` (khoảng dòng 224–243). Constructor trong kế hoạch không qua được `model_validate`. Cần model `CombinedTelemetry` mới, breakdown theo profile, `wall_seconds` tách `sum_agent_seconds`. Cộng `reasoning_tokens` và `cached_read_tokens` cùng cost. `cost_mode=exact` chỉ khi mọi thành phần là `exact`.

`parse_verdict_from_md` nhận mọi frontmatter có khóa `verdict` và bỏ field lạ (`extra=ignore`). `consolidated_conditions` sẽ không thành `conditions`. `status.json` đếm `blocking_conditions` bằng 0 dù consensus đang `APPROVE_WITH_CONDITIONS`. File công bố phải điền `conditions` bằng danh sách đã gộp. Một file `grok_*.md` duy nhất là phản hồi chính thức của `request_id`.

Seam mới phải vào `packages/ccba-harness/AGENTS.md` và `__all__` của `ccba_harness` trước khi compile catalog (ADR-0061). Hàm cũ trong `peer.py` và `cli.py` giữ nguyên chữ ký.

## Phần giữ lại

Giữ pessimistic merge, `risk = max`, cộng cost, thời gian wall clock theo nhịp song song, session id riêng (đã có trong `invoke`), tool policy đọc từ `PROFILE_SPECS`, và việc không đổi chữ ký các hàm hiện có. `code_review` và `arch_audit` đang cấm ghi file và cấm shell, nên hai subprocess đọc trên cùng worktree là chấp nhận được. Chưa bật `--worktree` trừ khi một profile sau này có quyền ghi.

Sau khi kế hoạch sửa COND-01 đến COND-06, có thể mở nhánh mã. Lattice, quorum, và vị trí file tạm cần được chốt trong kế hoạch trước dòng implement đầu tiên.