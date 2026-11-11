# Software Factory — Ngôn Ngữ Chung Thiết Kế Hệ Thống Tác Nhân Tự Động

> **Nguồn tham chiếu (Upstream Attribution):** Chuyển thể và bản địa hóa từ `mattpocock/skills` (`skills/in-progress/software-factory`, commit `4ae2317d`, MIT License) tích hợp với kiến trúc quản trị CCBA Agent Services Platform.

Một **Software Factory** là hệ thống các tác nhân tự động chuyển hóa các tickets, Pull Requests (PRs) và lịch chạy định kỳ thành mã nguồn đã kiểm định và hợp nhất trên hạ tầng từ xa. Tài liệu này định nghĩa bộ từ vựng chuẩn mực khi thiết kế hoặc thảo luận kiến trúc Software Factory: chỉ sử dụng đúng thuật ngữ chính tắc (canonical terms); khi gặp từ nằm trong danh sách `_Avoid_`, hãy quy chiếu ngay về thuật ngữ chuẩn.

---

## 1. Tác Vụ & Lượt Thực Thi (Tasks and Runs)

- **Task**: Một loại công việc được định nghĩa một lần và thực thi lặp lại nhiều lần trong factory (ví dụ: explore, implement, review, ratchet). Một task có thể thao tác trên một ticket, một PR, hoặc toàn bộ codebase.
  - _Avoid_: `job`, `workflow`, `action`
- **Trigger**: Sự kiện khởi phát một lượt chạy: thay đổi trạng thái trên ticket tracker hoặc git host, bộ đếm thời gian (clock) trong orchestrator, hoặc kết quả đầu ra từ một run khác.
- **Run**: Một lần thực thi cụ thể của một **Task** trên một **Runner**, tính từ lúc nhận **Trigger** đến khi kết thúc, được đối xử như một hộp đen (black box). Một run **không bao giờ đứng chờ con người**: nó kết thúc dứt điểm, và thao tác phản hồi của con người sau đó trên ticket tracker hoặc git host sẽ khởi phát một run mới.
  - _Avoid_: `session`
- **Runner**: Máy ảo hoặc môi trường thực thi dùng một lần (disposable environment) nơi một **Run** diễn ra. Không trạng thái cục bộ nào được phép tồn tại qua biên giới giữa các runs, ngay cả khi máy vật lý chạy dài hạn: bộ nhớ duy nhất nối giữa các runs nằm ở **Ticket tracker**, **Git host** và **Orchestrator**.
  - _Avoid_: `server`, `host`, `box`, `compute`, `sandbox`

---

## 2. Sáu Khe Dịch Vụ Hạ Tầng (Six Service Slots)

Thiết kế một Software Factory gồm hai nửa tách biệt: **Services** (các khe hạ tầng dùng sản phẩm sẵn có — *buy the services*) và **Tasks** (luồng nghiệp vụ đặc thù mang thiết kế của đội ngũ — *build the tasks*).

- **Ticket tracker**: Nơi lưu trữ tickets và là giao diện giao tiếp chính của con người với factory (lên lịch việc bằng cách mở/gán nhãn ticket, trao đổi qua comments). Ưu tiên sản phẩm sẵn có (off-the-shelf) để dễ mở quyền cộng tác.
  - _Avoid_: `issue tracker`, `ticket manager`, `project board`
- **Ticket source**: Bất kỳ nguồn bên ngoài factory nào tự động tạo tickets vào ticket tracker (nút báo lỗi người dùng, bộ giám sát lỗi runtime/chậm truy vấn, hộp thư tiếp nhận).
  - _Avoid_: `data source`, `trigger source`, `intake`
- **Git host**: Nơi quản lý branches, Pull Requests và lịch sử code reviews.
  - _Avoid_: `code host`, `forge`, `repo`
- **Orchestrator**: Thành phần tiếp nhận triggers, cấp phát runs lên runners, và ghi nhận trạng thái hàng đợi (`queued`, `in flight`, `finished`).
  - _Avoid_: `dispatcher`, `scheduler`, `control plane`
- **Observability platform**: Nơi runners đẩy logs, traces và telemetry để con người quan sát diễn biến bên trong mỗi run (tùy chọn — có thể chủ đích chọn `none` nếu trang trạng thái của runner/orchestrator đã đủ rõ). Một run không bao giờ lấy observability platform làm nguồn sự thật cho đến khi thông tin được ghi vào ticket tracker hoặc git host.
  - _Avoid_: `observability`, `logs`, `monitoring`, `dashboard`

### Ma Trận Lấp Đầy Sáu Khe Dịch Vụ (Service Slot Profiles)

Một sản phẩm có thể đảm nhiệm nhiều khe dịch vụ cùng lúc:

| Service Slot | All on GitHub | Linear + Sandboxes | Own Tracker | CCBA Platform Profile |
| :--- | :--- | :--- | :--- | :--- |
| **Ticket tracker** | GitHub Issues | Linear | Own app | GitHub Issues (kèm nhãn `in-progress` & Claim Lock) |
| **Ticket source** | Feedback button | Feedback button, monitor | Feedback button, monitor | `upstream_evaluator.py`, CI Drift Detectors, User Issues |
| **Git host** | GitHub | GitHub | GitHub | GitHub (Atomic Micro-PRs $\le 200$ LOC) |
| **Orchestrator** | GitHub Actions | Own server + DB | Own app | GitHub Actions + `ccba-harness` CLI |
| **Runner** | Actions runner | Actions, E2B, Daytona, VPS | Own app / sandboxes | Ephemeral Git Worktrees & Actions Runners |
| **Observability platform** | `none` (Actions pages suffice) | LLM tracing platform | Own app | Session JSONL Telemetry & `peer_exchange` Audit Logs |

---

## 3. Khởi Động Chậm & Ba Phanh Hãm (Start Slow & The Three Brakes)

Mọi **Trigger** đều là chân ga (accelerator). Chân ga thiếu phanh hãm sẽ biến hệ thống thành cỗ máy xả rác tự động (*slop cannon*). Bắt buộc thiết lập **Ba Phanh Hãm (Three Brakes)** trước khi mở rộng tần suất tự động hóa:

1. **Automated checks (Cổng kiểm định tất định):** Các rào chắn tất định về kiểu dữ liệu, lint, kiến trúc và kiểm thử mà mọi run bắt buộc vượt qua 100% (`python -m ccba_harness verify-patch --preset ci`, `ruff`, `mypy`, `pytest`).
2. **Automated review (Thẩm định độc lập lạnh):** Một run tách biệt đọc bản diff hoàn toàn độc lập (cold review) đối chiếu với quy chuẩn codebase và ticket gốc (`/ccba-code-review`, Read-Only Advisory AI Review theo `.github/bugbot-rules.md`, hoặc `ccba-harness peer-dispatch --profile signoff_diff`).
3. **Human review (Nghiệm thu của con người):** Con người duyệt PR trước khi squash-merge (`ccba-harness door-triage` kèm Tradeoff Card cho `ONE_WAY_DOOR`). Mọi lỗi do con người phát hiện phải được kết tinh ngược thành **Automated checks** mới hoặc quy tắc **Automated review** sắc bén hơn.

**Nguyên tắc mở ga (Throttle Discipline):** Bổ sung từng trigger tự động một, bóp băng thông ban đầu (ví dụ: 1/10 báo cáo lỗi, hoặc lịch chạy 1 lần/ngày) kèm Human review trên mọi PR. Khống chế trần số vòng lặp sửa lỗi tự động (tối đa vài lượt thử) trước khi gắn nhãn chuyển về trạng thái chờ con người.

---

## 4. Năm Câu Hỏi Kiểm Định Thiết Kế Task & Chống Trùng Lặp

Một thiết kế Software Factory chỉ hoàn tất khi mọi khe dịch vụ đã định danh rõ sản phẩm (hoặc chủ đích `none` cho observability) và mỗi **Task** trả lời minh bạch 5 câu hỏi:

1. **What triggers it?** — Sự kiện cụ thể nào khởi phát run?
2. **What does it do, and which services does it read and write?** — Hành vi cốt lõi và bề mặt đọc/ghi trên các khe dịch vụ?
3. **What does it trigger next?** — Khi thành công hoặc thất bại, nó kích hoạt run nào tiếp theo?
4. **Where does a human re-enter?** — Điểm dừng nào bàn giao quyền quyết định lại cho con người?
5. **What stops two runs doing the same work?** — Cơ chế khóa chống đua song song (trên CCBA Platform: **Multi-Client Peer Claim Locking** với `CCBA_PEER_CLAIM_LOCK` TTL 24h cho Issue và `CCBA_PR_CLAIM_LOCK` TTL 4h + `--force-with-lease` cho PR).

Đồng thời, với mỗi **Ticket source**, bắt buộc trả lời: **What stops it filing the same ticket twice?** (Trên CCBA Platform: **Remote Mutation Idempotency & State Inspection Gate** và sổ cái `triage_ledger` — kiểm tra ticket đang mở và comment bổ sung thay vì tạo trùng; chỉ mở lại nếu lỗi tái phát sau khi bản vá đã merge).

---

## 5. Chín Mẫu Task Kinh Điển Giải Quyết Nút Thắt Thực Tế

Bắt đầu từ nỗi đau thực tế của đội ngũ thay vì dựng toàn bộ nhà máy ngay từ đầu:

| Mẫu Task | Nỗi Đau Giải Quyết | Trigger Khởi Phát | Hành Vi Thực Thi & Chuỗi Kích Hoạt Kế Tiếp |
| :--- | :--- | :--- | :--- |
| **Explore** | Tickets tồn đọng chưa phân loại | Ticket mới tạo hoặc được gán nhãn | Đối chiếu ticket với codebase, phân nhóm (`easy call`, `needs a human`, `not a bug`). Kích hoạt **Implementer** cho `easy call`; các nhóm còn lại gán nhãn chờ người dùng (`/ccba-grilling`). |
| **Implementer** | Tickets sẵn sàng nhưng chờ người code | Ticket có nhãn `ready` | Triển khai mã nguồn (`/ccba-implement`) cho tới khi vượt qua **Automated checks**, mở PR nguyên tử và kích hoạt **Automated review**. |
| **Automated review** | PRs xếp hàng chờ review | PR mới mở chưa có review hoặc được gán nhãn | Đối chiếu diff với quy chuẩn codebase & ticket. Nếu trượt $\rightarrow$ kích hoạt **Rework**; nếu đạt $\rightarrow$ dừng run và chờ **Human review** trước khi merge. |
| **Rework** | PR trượt review tự động bị bỏ ngỏ | **Automated review** báo không đạt | Chỉ sửa đúng các điểm bị chỉ ra rồi push lại. Sau $N$ lượt trượt liên tiếp, dừng chuỗi lặp và gán nhãn chờ con người. |
| **Decompose** | Đặc tả (spec) quá lớn cho một lượt chạy | Spec ticket được gán nhãn phân rã | Tách spec thành các tickets nguyên tử kèm đồ thị phụ thuộc (`/ccba-to-spec`), sau đó kích hoạt **Implementer** nhặt tuần tự từng ticket đã khép hết phụ thuộc. |
| **Ratchet** | Chuyển đổi sang quy tắc kiểm tra nghiêm ngặt hơn | Bộ đếm thời gian hằng ngày (daily clock) | Rút đúng **1 tệp** khỏi danh sách miễn trừ (exception/quarantine list), sửa cho đạt quy tắc mới, mở 1 PR nhỏ mỗi ngày để giữ chi phí Human review thấp cho tới khi danh sách rỗng. |
| **Fix** | Chính các runs của factory bị lỗi | Orchestrator báo một run thất bại | Ghi log lỗi thành ticket và thử mở PR khắc phục (`/ccba-diagnosing-bugs`). **Rào chắn chống lặp vô hạn:** nếu bản thân **Fix** run thất bại thì không kích hoạt gì thêm; mọi PR sửa chính factory bắt buộc qua **Human review**. |
| **Architecture** | Codebase trôi dạt kiến trúc (drift) | Lịch chạy ban đêm (nightly clock) | Quét các thay đổi gần đây để phát hiện ứng viên làm sâu module (deepening) và gom thành 1 ticket đề xuất. Không tự kích hoạt sửa đổi; chờ con người chọn ứng viên và gán nhãn. |
| **Retro** | Cùng một dạng sai sót lặp đi lặp lại | PR được merge (bóp băng thông 1/10 PRs) | Đọc lại PR, ticket, nhận xét review và run logs để đề xuất PR cập nhật quy tắc hướng dẫn (`AGENTS.md` / `SKILL.md`), kích hoạt **Automated review**. |
