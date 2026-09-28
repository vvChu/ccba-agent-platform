Handoff Sprint 4 đã tới. Tôi sẽ đối chiếu `main` tại `ed3efdc6` với đúng phạm vi PR-A và PR-B trước khi kết luận bước tiếp theo.Đã nhận thông báo hoàn thành Sprint 4. Cả hai commit đều nằm trên `main`: `e42f7ac8` (PR #430) và `ed3efdc6` (PR #431), cùng ghi nhận handoff ở `ad2cf894` (PR #432). Chạy lại đúng hai bộ test của Sprint 4 cho kết quả 20/20 PASS trong 0,29 giây.

Mã đã khớp thiết kế đã chốt:

- `failure_mutator.py` là hàm thuần, ledger ở `.md/cache/eval_failure_ledger/`, năm mã lỗi render thành thẻ từ `LegalFlatIndex`.
- `propose_mutation()` ưu tiên thẻ lỗi cho `legal` và `legal_tooling`, tối đa `max_failure_patches: 3`, rồi mới tới YAML.
- Daemon có đủ ba nhánh: bỏ qua khi hết YAML và không còn signal, chạy tiếp khi ledger còn signal chưa áp, và seed một baseline khi skill pháp lý chưa có ledger.

Chưa cần Sprint 5. Việc tiếp theo là một đêm nightly thật, rồi đọc ledger và báo cáo. Có hai điểm cần xem trên chính đêm đó.

1. Cooldown đứng trước nhánh seed. Parser cooldown vẫn đưa skill vào danh sách nghỉ khi `commits == 0` và điểm dưới 90%, kể cả dòng `SKIPPED_COOLDOWN`. Báo cáo 26/09 đang trong cửa sổ 3 ngày và ghi cụm pháp lý ở khoảng 30% với 0 commit. Đêm tới sẽ bỏ qua các skill đó trước khi tới `needs_ledger_seed`, rồi báo cáo mới lại ghi điểm dưới 90% với 0 commit, nên cửa sổ cooldown được làm mới. Nhánh 3 không chạy được trên đúng cụm mà Sprint 4 nhằm vào.

2. `sha256_provenance` ghi `raw_output` là boolean. `extract_failure_signals()` chỉ nhận `dict`, nên skill `legal_tooling` có thể seed một ledger rỗng. Đường tạo thẻ thật là `legal_verbatim_provenance` trên archetype `legal`.

Nếu đêm tới không có dòng `LEDGER_SEEDED` hoặc `FAILURE_MUTATION_APPLIED` cho `ccba-legal-intel` và `ccba-legal-advisor`, việc sửa là một micro-PR: cooldown không được làm mới từ các dòng `SKIPPED_COOLDOWN`, và skill có `needs_ledger_seed` đi trước cooldown. Đó là bản vá vận hành, không phải sprint mới.