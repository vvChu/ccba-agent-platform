Đã nhận handoff Sprint 3. Tôi sẽ đối chiếu mã sau PR #428 với seam sẵn có và ADR-0059, rồi đưa kế hoạch Sprint 4 bám đúng các điểm đó.Đã nhận Handoff Packet Sprint 3. PR #428 tại `68ae9f56` đóng đúng phần yield: `remaining_strategies()` short-circuit 0 token, trần token tính cả baseline, `choose_model("local")` / `qwen-local-primary`, và cooldown theo hash của `mutation_strategies.yaml`. Sprint 4 bám seam hiện có (`LegalFlatIndex`, `LegalVerbatimProvenanceScorer`, `GitRatchetOptimizer`, `NightlyTunerDaemon`). Không mở package mới và không đụng `miner.py`.

## Ràng buộc quyết định thiết kế

`miner.identify_failures()` phân loại transcript (`OUTDATED_CITATION`, `ROUTER_DISCLAIMER`, `TOOL_EXCEPTION`) rồi `generate_eval_spec_item()` sinh case mới. Sprint 4 cần tín hiệu đã có cấu trúc từ `ScoreResult.raw_output` của `LegalVerbatimProvenanceScorer` (`trap_doc`, `unknown_doc`, `fake_clause`, `target_law`, `pdf_sha256`). Hai đường đó khác nhau.

ADR-0059 cấm bịa điều khoản. Chỉ mục `legal_clauses_flat.json` có số hiệu, tiêu đề, số Công báo, `pdf_sha256` và `statutory_keys` (56 văn bản, 19.812 khóa). Không có nguyên văn điều luật. Mutator chỉ được in thẻ trích dẫn từ các trường đó, kèm cặp trong `replaces_map` (ví dụ `136/2020/NĐ-CP` → `105/2025/NĐ-CP`, `50/2014/QH13` → `135/2025/QH15`). Câu dạng «Điều N quy định rằng…» không được sinh ra.

Cổng Sprint 3 đang chặn Sprint 4. `daemon.py` bỏ qua skill khi `remaining_strategies()` rỗng và hash YAML không đổi. Skill pháp lý đã bão hòa YAML sẽ không bao giờ vào tuner. Cổng mới chỉ bỏ qua khi đồng thời hết chiến lược YAML và không còn tín hiệu lỗi chưa áp.

## Kiến trúc

Module mới `failure_mutator.py`, thuần hàm, không gọi LLM.

```text
EvalReport.item_results
        │  extract_failure_signals()
        ▼
FailureSignal (code, item_id, scorer, fingerprint, fields)
        │  persist → .md/cache/eval_failure_ledger/<skill>.json
        ▼
render_failure_patch(signal, LegalFlatIndex) → markdown card
        │
        ▼
GitRatchetOptimizer.propose_mutation()
   1. một thẻ lỗi chưa có trong SKILL.md
   2. nếu không có thẻ: remaining_strategies() như Sprint 3
        │
        ▼
ratchet sẵn có: chấm → giữ commit nếu điểm tăng → rollback nếu không
```

Năm mã lỗi, map thẳng từ `raw_output` đã có:

| Mã | Khóa `raw_output` | Nội dung thẻ |
| :--- | :--- | :--- |
| `NO_CITATION` | `citations_found == 0` | Số hiệu, tiêu đề, Công báo, `pdf_sha256` của `metadata.target_law` nếu văn bản còn trong chỉ mục |
| `EXPIRED_UNACKNOWLEDGED` | `trap_doc`, `replacement` | Cặp `replaces_map`. Yêu cầu câu trả lời nêu hết hiệu lực và viện văn bản thay thế |
| `UNKNOWN_DOCUMENT` | `unknown_doc` | Số hiệu không có trong chỉ mục. Không bịa văn bản thay thế |
| `UNKNOWN_CLAUSE` | `doc`, `fake_clause` | Khóa không thuộc `statutory_keys`. Liệt kê tối đa 8 khóa thật của đúng văn bản |
| `WRONG_TARGET` | `target_law` | Số hiệu bắt buộc, hoặc số hiệu thay thế nếu `is_expired_or_replaced` |

`fingerprint = sha256(scorer + code + doc + clause + item_id)`. Thẻ đã nằm trong body thì bỏ qua, cùng cách `remaining_strategies()` so khớp văn bản.

Thứ tự trong `propose_mutation()`: một thẻ lỗi mỗi vòng, tối đa 3 thẻ mỗi skill mỗi đêm (`tuner_config.yaml`: `max_failure_patches: 3`). Trần `hard_max_tokens_per_skill` giữ nguyên. Archetype được phép trong Sprint 4: `legal`, `legal_tooling`. Scorer được phép: `legal_verbatim_provenance`, `sha256_provenance`. Archetype khác vẫn chỉ dùng YAML.

Ledger nằm ở `.md/cache/eval_failure_ledger/<skill>.json` và được gitignore, để PR đêm không kéo theo file này. Mỗi bản ghi gồm `content_sha256` của `SKILL.md` và danh sách signal. Sau rollback, hash nội dung trùng lại nên signal còn dùng được. Sau commit giữ lại, hash đổi; signal cũ hết hiệu lực.

Ba nhánh của daemon:

1. Hết YAML, không có signal chưa áp, archetype không phải legal: `SKIP_EXHAUSTED`, 0 token, như Sprint 3.
2. Hết YAML, ledger cùng `content_sha256` còn signal chưa áp: vào tuner, không chấm baseline để «khám phá lại» chiến lược YAML.
3. Hết YAML, chưa có ledger, archetype `legal` hoặc `legal_tooling`: đúng một baseline để ghi ledger (`LEDGER_SEEDED`). Nếu baseline tạo được signal, vòng đó được đề xuất một thẻ. Skill không thuộc hai archetype này không đi vào nhánh seed.

## Hai micro-PR

**PR-A — renderer thuần.** Tạo `packages/ccba-harness/src/ccba_harness/evals/failure_mutator.py` và `packages/ccba-harness/tests/test_failure_mutator.py`. Re-export qua `evals/__init__.py`. Chưa nối daemon.

**PR-B — nối vòng ratchet.** Sửa `tuner.py` (`propose_mutation`, ghi ledger sau `evaluate_content`) và `daemon.py` (ba nhánh trên). Thêm `max_failure_patches` vào `tuner_config.yaml`. Thêm dòng gitignore cho `.md/cache/eval_failure_ledger/`.

## Ca kiểm thử

Dùng `load_legal_flat_index()` thật. Không viết nguyên văn điều luật trong fixture.

1. `EXPIRED_UNACKNOWLEDGED` với `136/2020/NĐ-CP`: thẻ chứa đúng `105/2025/NĐ-CP` và `pdf_sha256` của văn bản thay thế trong chỉ mục.
2. `UNKNOWN_CLAUSE` với một khóa không có trong `statutory_keys` của `135/2025/QH15`: thẻ ghi khóa đó vắng, và chỉ liệt kê khóa đọc từ chỉ mục.
3. `UNKNOWN_DOCUMENT` với số hiệu không có trong 56 văn bản: thẻ từ chối số hiệu đó và không sinh số hiệu thay thế.
4. `NO_CITATION` kèm `target_law=55/2024/QH15`: thẻ chứa `706a8bfb…` đủ 64 ký tự và Công báo `1187+1188/2024`.
5. Gọi renderer lần hai trên body đã chứa thẻ: danh sách thẻ chưa áp là rỗng.
6. Bộ lọc: `raw_output` của scorer regex không tạo signal.
7. Daemon: skill YAML-exhausted, ledger còn một signal → không `SKIP_EXHAUSTED`.
8. Daemon: skill YAML-exhausted, không ledger, archetype `coding` → `SKIP_EXHAUSTED`, 0 token.
9. Ratchet với task giả: output trước thẻ bị `is_critical_fail` vì viện `136/2020/NĐ-CP` mà không nêu thay thế; output sau thẻ nêu `105/2025/NĐ-CP` và điểm tăng → một commit. Output sau thẻ vẫn fail → rollback và fingerprint đó không được đề xuất lại.
10. `python -m ccba_harness verify-patch --preset eval` PASS trên cả hai PR.

`miner.py` giữ nguyên vai trò đào transcript. Khi cần nối sau này, `OUTDATED_CITATION` có thể map sang `EXPIRED_UNACKNOWLEDGED`, ngoài hai PR này.

Antigravity có thể phản biện hoặc bắt đầu PR-A từ `failure_mutator.py`.