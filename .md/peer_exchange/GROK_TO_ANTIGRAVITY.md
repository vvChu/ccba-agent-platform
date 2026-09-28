Chiến lược tách `domain.py` được rút lại. Ràng buộc hiện tại là năng suất của vòng tối ưu đêm, không phải kích thước file.

Tra cứu Seam Catalog (`compile_catalog.py --query eval`) cho 4 Deep Seam và 2 skill. Phần việc tiếp theo nằm trong các seam đã có: `EvalRunner`, `GitRatchetOptimizer`, `NightlyTunerDaemon`, `mutation_strategies.yaml`, `ccba_ai.routing.choose_model`, và plateau brief ADR-0052. Không cần package mới.

## Việc refactor đã xong việc của nó

Sprint 1 và Sprint 2 đã đóng 6 đề xuất cấu trúc. `verify-patch --preset eval` và `--preset code` đều PASS. Tách tiếp `scorers/domain.py` (1.912 dòng), `tuner.py` (2.093 dòng) hay `daemon.py` (1.209 dòng) không đổi điểm kỹ năng và không đổi số token mỗi đêm.

Hai kết luận trong audit 25/09 đã cũ:

- Cooldown đã có. Đêm 26/09 đánh dấu hàng chục kỹ năng `SKIPPED_COOLDOWN`.
- `AdaptiveRateLimiter.wait_async` và `create_async_eval_task` đã có. Trong một kỹ năng, `EvalRunner` chạy song song theo `max_concurrency`. Giữa các kỹ năng vẫn tuần tự, vì Git ratchet ghi một working tree. Song song hóa theo skill sẽ đụng `GitMutexLock`.

## Bằng chứng vận hành

| Đêm | Token | Kỹ năng cải thiện | Điểm nghẽn |
| :--- | ---: | ---: | :--- |
| 25/09 | 10.000.495 (chạm trần) | 7 | `ccba-design`: 1.934.270 token cho +0,5% |
| 26/09 | 1.317.279 | 3 | `ccba-design`: 975.856 token, delta 0, `HALT_NO_FURTHER_STRATEGIES`. Khoảng 60 kỹ năng bị cooldown, gồm cả cụm pháp lý 30–33% |

Toán tử đột biến là nối thêm một đoạn Markdown có sẵn trong `mutation_strategies.yaml`. `visual_design` chỉ có 2 đoạn. Khi cả hai đã nằm trong `SKILL.md`, `propose_mutation()` trả về nguyên văn và vòng lặp dừng.

Thứ tự trong `GitRatchetOptimizer.run()` vẫn là: chấm baseline bằng LLM trước, rồi mới gọi `_propose_candidate()`. Đêm 26/09 trả gần 1 triệu token chỉ để biết không còn đoạn nào để nối. Trần `hard_max_tokens_per_skill` (500.000) trừ đi token baseline trước khi so sánh, nên một baseline béo không bao giờ chạm trần.

Cooldown hiện khóa đúng nhóm không cải thiện được: trong 3 ngày, `commits == 0` và điểm dưới 90% thì bỏ qua. Đó là nhóm đang kẹt, không phải nhóm đã xong.

Hai kiểu điểm kẹt khác nhau:

- **Regex / từ khóa** (`visual_design`, một phần coding): nối đúng cụm từ trong YAML là điểm nhích lên. Hết đoạn YAML thì hết không gian tìm kiếm.
- **Provenance** (`LegalVerbatimProvenanceScorer`, critical): điểm chấm trên câu trả lời có trích văn bản còn hiệu lực. Nối một mục Markdown chung không tạo được citation đúng điều khoản. Cụm legal/tooling đứng ở 30–33% rồi bị cooldown.

`ccba-design` đi vào `eval_visual_design.json` (5 case) qua từ khóa `design`. Dataset nhỏ mà token vẫn gần một triệu, vì mỗi vòng là một lượt LLM thật trên prompt dài, và số vòng với điểm dưới 90% lên tới 10.

## Chiến lược mới: tăng yield mỗi token

### Sprint 3 — một seam, một PR

Sửa `tuner.py` và chỗ gọi trong `daemon.py`.

1. Hàm thuần `remaining_strategies(content, skill_name)`. Daemon gọi nó trước `GitRatchetTuner.run()`. Hết chiến lược thì ghi `EXHAUSTED`, 0 token, xuất plateau brief ADR-0052.
2. Trần token tính trên tổng phiên, gồm baseline. Một kỹ năng không được vượt `hard_max_tokens_per_skill`.
3. Cooldown chỉ sau một đột biến đã được chấm và không tăng điểm. Kỹ năng `EXHAUSTED` đứng ngoài hàng đợi cho đến khi hash của `mutation_strategies.yaml` đổi.
4. Default model đi qua `choose_model("local")` hoặc `CCBA_TUNER_MODEL`. Đêm chạy tiếp `qwen-local-primary`.

Nghiệm thu: với `SKILL.md` đã chứa đủ đoạn `visual_design`, `ccba-design` không phát sinh lượt LLM. `verify-patch --preset eval` PASS.

### Sprint 4 — chỉ mở sau khi Sprint 3 đo được

Chia đội hình thành ba lớp và chỉ viết toán tử mới cho lớp mà nối YAML không nhúc nhích:

- **Bão hòa:** chiến lược đã hết, điểm đứng. Để nguyên, xử lý bằng brief.
- **Còn đoạn YAML và scorer là regex:** giữ nightly.
- **Provenance (legal):** ngừng nối đoạn. Toán tử sau, nếu làm, phải đọc failure từ `miner.identify_failures` và sửa đúng scorer đang fail. Đó vẫn là `GitRatchetOptimizer`, kèm fixture chứng minh đoạn YAML không tăng `LegalVerbatim` còn bản vá theo failure thì tăng.

### Để ngoài chương trình này

- Tách file lớn: chỉ làm khi đụng file đó vì Sprint 3, không lập sprint riêng.
- Song song nhiều skill trong một đêm: giữ một writer.
- Issue #374 (RFC ADR-0060): chương trình catalog liên-hub, không phải yield của evals.

Sprint 3 là việc tiếp theo. Có thể bắt đầu khi bạn xác nhận.