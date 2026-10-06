---
request_id: req-plan-level3-auto-apply-001
verdict: REVISE_PLAN
conditions:
- id: COND-LEVEL3-TXN
  description: Hoàn nguyên phải dùng đúng pre-image bytes đã băm thành blob_sha256,
    giữ trong transaction của apply_anchor_patch (written_backups, peer.py) cho tới
    khi verify trả về hoặc ném lỗi, trong try/finally. Cấm đọc sidecar .bak làm nguồn
    phục hồi và cấm writer thứ hai. Trước khi sửa target, ghi journal cộng bản sao
    byte vào .md/backups/anchor-txn/<uuid>/ (thư mục đã gitignore) và giữ FileMutexLock
    riêng. Cấm giữ _SYNC_MUTEX suốt verify (ADR-0065 COND-03). Sau rollback, SHA-256
    từng file phải khớp pre-image thì mới được ghi rolled back cleanly. Phục hồi bằng
    write_bytes hoặc newline rỗng, vì atomic_write_text gọi write_text với newline=None
    và trên Windows sẽ đổi CRLF. Payload files rỗng bị từ chối. Lần gọi sau phải recover
    journal chưa có commit marker.
  blocking: true
  source_profile: audit_plan
  source_profiles: []
- id: COND-LEVEL3-ROOT
  description: root mặc định là git rev-parse --show-toplevel tính từ cwd, ghi đè
    bằng --root. Cấm Path.cwd() trần và cấm prompt_path.parent.parent.parent. Fail-closed
    khi không phải git repo, khi prompt nằm ngoài root, hoặc khi --worktree được bật
    mà chưa có đường dẫn worktree để ghim làm root. Cấm áp patch vào main checkout
    trong trường hợp đó. Root lúc áp phải trùng root đã dùng để đóng dấu blob_sha256.
  blocking: true
  source_profile: audit_plan
  source_profiles: []
- id: COND-LEVEL3-BACKUP
  description: Cấm sidecar Path.with_suffix(suffix + '.bak') cạnh source. with_suffix
    chỉ thay suffix cuối, nên foo.py thành foo.py.bak và đè archive .bak sẵn có dù
    .gitignore có *.bak*. Đuôi .bak.<timestamp> hoặc UUID cạnh source vẫn đua khi
    chạy song song và không phải nguồn hoàn nguyên. --keep-backups chỉ giữ thư mục
    txn dưới .md/backups/. Phase 1 từ chối nếu đường dẫn backup đã tồn tại hoặc trùng
    một target của payload.
  blocking: true
  source_profile: audit_plan
  source_profiles: []
- id: COND-LEVEL3-EXIT
  description: Verify fail và rollback đã chứng minh đúng byte thì exit 4 và verdict
    GATE_FAIL. Cấm exit 5 cho nhánh này. HANDOFF và exit 5 chỉ có nghĩa payload còn
    chờ orchestrator áp dụng (ADR-0065 mục 2.2). Rollback lệch byte hoặc ném lỗi thì
    exit 1 và cấm câu rolled back cleanly. peer-dispatch không có --auto-apply giữ
    nguyên exit 0/1. Có --auto-apply chỉ chạy sau khi invoke_grok_cli trả True. Co-review
    từ chối auto-apply thì giữ mã thoát consensus hiện có (APPROVE_WITH_CONDITIONS
    và APPROVE_WITH_RESERVATIONS = 2, REVISE_PLAN = 3, REJECT, REJECT_PLAN và GATE_FAIL
    = 4, HANDOFF = 5). Cấm dồn mọi từ chối về exit 2. Thành công chỉ được GATE_PASS
    và exit 0. Cấm thăng FINAL_ACCEPT. Cấm sửa YAML worker hoặc consensus tại chỗ.
    Ghi Orchestrator Gate riêng, giữ telemetry ADR-0064 và SHA-256 của bản output
    gốc.
  blocking: true
  source_profile: audit_plan
  source_profiles: []
- id: COND-LEVEL3-TRUST
  description: peer-dispatch --auto-apply chỉ khi profile đang chạy là patch_fast
    và verdict worker là HANDOFF, kể cả HANDOFF do nhánh COND-02 tổng hợp khi chỉ
    có AnchorPatchPayload. Verdict APPROVE, FINAL_ACCEPT hoặc GATE_PASS do worker
    tự ghi không phải giấy phép áp patch. Verdict REJECT, REJECT_PLAN hoặc REVISE_PLAN
    thì không áp. peer-co-review cấm gọi extract_anchor_payload trên markdown consensus.
    Chỉ áp một --patch-file đã ghim SHA-256 khi verdict thuộc APPROVE, APPROVE_PLAN
    hoặc FINAL_ACCEPT, risk_score nhỏ hơn hoặc bằng 3, và không có condition blocking
    true. Report thiếu hoặc không parse được thì không áp.
  blocking: true
  source_profile: audit_plan
  source_profiles: []
- id: COND-LEVEL3-SCOPE
  description: Preset ci không chạy packages/ccba-harness/tests/test_peer*.py. Lệnh
    pytest của ci chỉ gồm test_telemetry.py, test_verify_patch.py và tests/governance.
    GATE_PASS của vòng Level-3 phải chạy thêm các test peer đó cùng preset ci. --verify-preset
    là choices của các preset đã biết và chỉ được đưa vào resolve_preset_commands.
    Cấm nội suy chuỗi preset vào shell vì _execute_single_command dùng shell=True.
    Test rollback dùng tmp_path thật, được mock verify_patch_execution, và cấm mock
    apply_anchor_patch. Test CLI phải mock invoke_grok_cli.
  blocking: true
  source_profile: audit_plan
  source_profiles: []
- id: COND-LEVEL3-RESULT
  description: Nên trả một Pydantic model extra forbid thay cho tuple (success, report,
    summary), gồm gate_verdict, rollback_proven và preimage_sha256, để CLI --json
    và parser dùng chung một hợp đồng. Seam mới phải có mặt trong __all__ của ccba_harness
    và trong Deep Seam của packages/ccba-harness/AGENTS.md.
  blocking: false
  source_profile: audit_plan
  source_profiles: []
risk_score: 4
effort: L
summary: Hướng Level-3 đúng ADR-0058 và ADR-0065 (dry-run trước, cấm APPROVE giả,
  verify xong mới GATE_PASS) nhưng chưa được viết code. Hoàn nguyên đang đọc .bak
  cạnh source, root suy từ ba cấp cha, và exit 5 sẽ nuốt một gate đã thất bại. Phải
  khóa transaction đúng byte, root git toplevel, và exit 4 trước khi triển khai.
telemetry:
  session_id: 9193c4fb-5afa-473c-933f-10bbea4cc2a6
  primary_model: grok-4.7-build
  input_tokens: 442236
  output_tokens: 28444
  reasoning_tokens: 23342
  cached_read_tokens: 322688
  total_tokens: 470680
  model_calls: 11
  turn_count: 1
  cost_usd: 194175.36
  cost_mode: exact
  duration_seconds: 413.09
---
# Thẩm định phản biện: Level-3 Autonomous Loopback (`--auto-apply`)

**Người thẩm định**: Grok (profile `audit_plan`)  
**Phán quyết**: `REVISE_PLAN`  
**Điểm rủi ro**: 4/5  
**Yêu cầu**: `req-plan-level3-auto-apply-001`

Năm rào chắn trong mục 2 của bản kế hoạch là đúng hợp đồng: bản vá của `patch_fast` chỉ là `HANDOFF`, `dry_run` chạy trước khi ghi, verify thuộc ADR-0058, và consensus có điều kiện chặn thì không được tự áp. Phần chưa đạt là cơ chế bốn pha ở mục 3. Viết code đúng bản phác đó sẽ hoàn nguyên từ một sidecar có thể đè file khác, và có đường thoát mà cây làm việc không được phục hồi.

Seam hiện có phải được kéo dài, không được viết lại: `apply_anchor_patch` (`packages/ccba-harness/src/ccba_harness/peer.py`), `verify_patch_execution` (`packages/ccba-harness/src/ccba_harness/verifier.py`), `FileMutexLock`, và thư mục `.md/backups/` đã nằm trong `.gitignore`.

## Ba quyết định kiến trúc

### 1. Root là git toplevel, kèm `--root`

`root` mặc định lấy từ `git rev-parse --show-toplevel` của cwd. Cờ `--root` ghi đè giá trị đó, cùng kiểu `apply-anchor-patch` đang nhận `--root` tại `cli.py`. Giá trị này phải là đúng root đã dùng khi đóng dấu `blob_sha256`, và được truyền tường minh vào `auto_apply_and_verify_patch`.

`prompt_path.parent.parent.parent` chỉ đúng khi prompt nằm tại `<repo>/.md/peer_exchange/<file>.md`. Prompt đặt ngay tại root repo thì ba lần `.parent` ra khỏi repo (ví dụ lên `/home/vvc`). Payload dạng `ccba/ccba-agent-platform/...` khi đó vẫn qua được `is_relative_to` của root đã leo lên, miễn SHA-256 khớp. `Path.cwd()` cũng lệch khi CLI được gọi từ `packages/ccba-harness`.

Fail-closed khi cwd không phải git repo, khi file prompt nằm ngoài root, hoặc khi `--worktree` bật mà dispatcher chưa trả về đường dẫn worktree. Tổ hợp `--worktree` và `--auto-apply` bị từ chối cho tới khi root áp dụng chính là worktree đó. `patch_fast` không sửa đĩa, nên áp nhầm vào main checkout là lỗi của orchestrator.

### 2. Bản sao an toàn là journal byte trong `.md/backups/`, không phải đuôi `.bak`

Nguồn hoàn nguyên là byte gốc đang nằm trong transaction, cộng một journal đã fsync trước lần ghi target đầu tiên. `--keep-backups` giữ thư mục `.md/backups/anchor-txn/<uuid>/`. Phase 1 từ chối nếu đích backup đã tồn tại hoặc trùng một path trong payload.

`apply_anchor_patch` hôm nay làm sidecar bằng `target.with_suffix(target.suffix + ".bak")`. `with_suffix` chỉ thay suffix cuối: `foo.py` thành `foo.py.bak`, `Makefile` thành `Makefile.bak`. File `foo.py.bak` nằm cạnh source sẽ bị đè. Repo này dùng archive `.bak` (workflow ADR-0056, `issue_tracker.md.bak`, backup registry). `.gitignore` có `*.bak*` và `.md/backups/`, nên git status có thể im, nhưng file local vẫn mất. Đuôi `.bak.<timestamp>` vẫn trùng khi hai tiến trình chạy cùng giây, và vẫn là sidecar cạnh source. `apply_anchor_patch` còn giữ `written_backups` trong RAM rồi bỏ map đó ngay khi return. Pha 4 của bản kế hoạch đọc lại `.bak` sau khi map đã mất, nên nguồn yếu hơn chính transaction đang có.

`atomic_write_text` ghi bằng `Path.write_text` với `newline=None`. Trên Windows, `\n` thành `os.linesep`, và chuỗi đã chứa `\r\n` có thể thành `\r\r\n`. Khôi phục qua đường đó không giữ SHA-256 của pre-image. Phải `write_bytes` của đúng `raw_bytes` đã băm.

### 3. Verify fail và rollback sạch thì exit 4 (`GATE_FAIL`)

Mã thoát là **4**. Lattice đã xếp `GATE_FAIL` ở rank 90, và `run_peer_co_review_cli` đã map `REJECT`, `REJECT_PLAN`, `GATE_FAIL` về 4. `HANDOFF` là rank 70 và exit 5.

ADR-0065 mục 2.2 định nghĩa `HANDOFF` là bản vá đã sinh và còn chờ orchestrator áp dụng rồi verify. Sau khi verify đã chạy và thất bại, việc bàn giao đã xong. Exit 5 báo cho caller rằng payload còn chờ được áp. Caller sẽ áp lại đúng bản vá vừa bị gate từ chối.

Phân nhánh bắt buộc:

| Kết quả | Verdict ghi ở Orchestrator Gate | Exit |
|---|---|---|
| Worker chưa xong, hoặc `--auto-apply` không được yêu cầu | Giữ verdict worker. `HANDOFF` vẫn là `HANDOFF` | 0 nếu dispatch hợp lệ, 1 nếu worker hỏng. Giữ map hiện tại của `peer-dispatch` |
| `--auto-apply` nhưng không có payload hợp lệ, hoặc profile không được phép | Không đụng đĩa | 1 |
| Verify `all_passed` và pre-image đã được thả có chủ đích | `GATE_PASS` | 0 |
| Verify fail hoặc `all_passed == False`, và mọi file đã khớp lại SHA pre-image | `GATE_FAIL` | 4 |
| Verify ném lỗi, timeout, hoặc rollback không khớp byte | `GATE_FAIL` kèm `COND-ROLLBACK-DIRTY` | 1 |

`all_passed` đã fail-closed khi không có lệnh nào (`len(results) > 0` trong `verify_patch_execution`). Giữ điều kiện đó. Thành công chỉ được nâng `HANDOFF` lên `GATE_PASS`. `FINAL_ACCEPT` là token nghiệm thu deliverable, rank 35 so với 30 của `GATE_PASS`. Orchestrator không được tự đúc token đó.

Co-review không được đổi mọi lần từ chối auto-apply thành exit 2. Exit 2 hôm nay là `APPROVE_WITH_CONDITIONS` và `APPROVE_WITH_RESERVATIONS`. Consensus `REJECT` phải vẫn exit 4. Consensus `REVISE_PLAN` phải vẫn exit 3. Chỉ nhánh đủ điều kiện áp dụng mà verify fail mới chuyển sang 4 sau khi rollback đã được chứng minh.

Cấm sửa YAML frontmatter của worker hoặc của consensus tại chỗ. `invoke_grok_cli` đã gắn telemetry vào block đó (ADR-0064). Ghi một bản Orchestrator Gate riêng và lưu SHA-256 của output gốc mà `safe_read_and_hash` đã đọc.

## Kẽ hở bắt buộc sửa trước khi code

**Verify nằm ngoài transaction.** Bản phác bắt `ValueError` ở pha 1, rồi gọi `verify_patch_execution` trần. Timeout, `OSError`, hoặc preset không hợp lệ bỏ qua pha 4. `finally` phải hoàn nguyên trừ khi bit commit đã bật. Journal trên đĩa cần có vì `finally` không chạy khi process bị kill giữa lúc preset `ci` đang chạy subprocess. Journal đặt ở `.md/backups/anchor-txn/<uuid>/`, tái sử dụng thư mục backup sẵn có. Lần vào seam sau đó thấy journal chưa commit thì phục hồi trước khi làm việc khác.

**Khóa đúng chỗ.** Dùng `FileMutexLock` cho cả transaction. Không cầm `_SYNC_MUTEX` trong lúc verify. ADR-0065 COND-03 cấm giữ mutex đó suốt I/O dài.

**`--auto-apply` chưa gắn với COND-PATCHFAST-APPROVE.** Mục 2 cấm tin `APPROVE` do worker tự viết. Đoạn CLI mục 3.2 chỉ cần `extract_anchor_payload` khác rỗng là áp. Profile `audit_plan`, `code_review`, và `arch_audit` được phép trích JSON. Regex lấy fence JSON đầu tiên. Một báo cáo trích đúng một `AnchorPatchPayload` mẫu sẽ bị áp lên đĩa. `peer-dispatch --auto-apply` chỉ mở cho `patch_fast` khi verdict là `HANDOFF`.

**Co-review không có payload của chính nó.** `code_review` và `arch_audit` xuất `PeerVerdictBlock`, không xuất bản vá được phép áp. Cấm `extract_anchor_payload` trên markdown consensus. Muốn áp thì nhận `--patch-file` đã ghim hash, và chỉ khi verdict thuộc `APPROVE`, `APPROVE_PLAN`, `FINAL_ACCEPT`, `risk_score <= 3`, và không có `blocking: true`.

**Preset `ci` không chứng minh seam mới.** Sáu lệnh `ci` gọi pytest trên `test_telemetry.py`, `test_verify_patch.py`, và `tests/governance/`. Chúng không chạy `test_peer_auto_apply.py` hay `test_peer_runtime_hardening.py`. `GATE_PASS` của vòng này phải gắn thêm các test đó. `--verify-preset` là `choices` của preset đã khai báo. `_execute_single_command` dùng `shell=True`, nên chuỗi preset không được ghép vào shell.

**File mới nằm ngoài seam.** `apply_anchor_patch` từ chối path chưa tồn tại. Level-3 không tạo file. Payload khai báo file mới phải fail ở pha 1, trước khi ghi.

**Hai lần gọi apply vẫn nên giữ.** `dry_run=True` rồi gọi thật: lần gọi thật tự kiểm lại SHA-256, nên TOCTOU giữa hai pha đã fail-closed. Verify thì phải chèn vào trong lần gọi thật, trước khi pre-image bị hủy, bằng hook hoặc context của chính `apply_anchor_patch`.

## Phần được giữ

- Cấm thăng `APPROVE` từ payload trần. Nhánh tổng hợp `HANDOFF` ở `invoke_grok_cli` đã làm đúng ADR-0065 mục 2.2.
- Pha 1 tái sử dụng hash, path traversal, `target_files_seen`, và anchor đúng một lần.
- `keep_backups` mặc định tắt.
- Ngưỡng consensus `risk_score >= 4` hoặc có condition chặn thì không áp. So sánh trên số nguyên của report đã parse. Report thiếu thì không áp.
- Test rollback phải thấy nội dung gốc trên đĩa. Mock `verify_patch_execution` là đủ. Mock `apply_anchor_patch` làm test đó mất giá trị. Test CLI mock `invoke_grok_cli`, vì gọi Grok thật sẽ vượt ngân sách 1,5 giây và không còn là unit test.

Bộ test tối thiểu trước khi rời `REVISE_PLAN`: CRLF khôi phục đúng byte, sibling `.bak` có sẵn không đổi, verify ném exception vẫn rollback, journal thiếu commit marker được recover, prompt ở root repo không leo ra ngoài, profile `audit_plan` có JSON mẫu không ghi đĩa, consensus `REJECT` kèm `--auto-apply` vẫn exit 4, payload `files: []` bị từ chối, worker tự ghi `APPROVE` không thành `GATE_PASS`.