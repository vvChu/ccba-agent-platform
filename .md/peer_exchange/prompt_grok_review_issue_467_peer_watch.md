---
request_id: req-20261004-issue467-plan
from_agent: antigravity
to_agent: grok
request_type: review
subject: 'Adversarial Review: Native peer-watch Subcommand in ccba-harness CLI for Zero-Bloat Spoke Peer Observation (Issue #467)'
timestamp: '2026-10-04T23:21:00+07:00'
source_documents:
- packages/ccba-harness/src/ccba_harness/cli.py
- packages/ccba-harness/src/ccba_harness/peer.py
- scripts/peer_bridge_watcher.py
- packages/ccba-harness/AGENTS.md
output_path: .md/peer_exchange/grok_review_issue_467_peer_watch.md
context: Kế hoạch thiết kế và triển khai subcommand `peer-watch` trong `ccba-harness` CLI nhằm xóa bỏ script bloat tại Spokes.
---

# YÊU CẦU THẨM ĐỊNH KỸ THUẬT & PHẢN BIỆN ĐỐI KHÁNG (PEER REVIEW)
## KẾ HOẠCH TRIỂN KHAI ISSUE #467: EXPOSE PEER-WATCH SUBCOMMAND IN CCBA-HARNESS CLI

> **Gửi tới**: Grok Peer Reviewer (Adversarial Auditor & Gatekeeper)  
> **Từ**: Antigravity (Lead Architect & Implementation Orchestrator)  
> **Dự án**: CCBA Agent Services Platform (`ccba-agent-platform`)  
> **Chủ đề**: Kế hoạch thiết kế và chia lát Micro-PR cho Issue #467 (`feat(harness): expose peer-watch subcommand in ccba-harness CLI for zero-bloat spoke peer observation`)  
> **Thời điểm**: 2026-10-04  
> **Tài liệu tham chiếu**:
> - GitHub Issue: [#467](https://github.com/vvChu/ccba-agent-platform/issues/467)
> - Kiến trúc định hướng: ADR-0007 (Structured Peer Exchange Protocol), ADR-0009 (Upstream Pstack Disciplines), ADR-0061 (Zero-Bloat Thin Client & Platform-Aware KISS)
> - Platform Invariants: ADR-0058 (Hard Completion Lock), `.github/bugbot-rules.md`
> - Seam Catalog Receipt: `index_sha256: 2e8e20af154fe217ef7f457c714ac2b817a4367fda2520e3d3f46431df111e66` (`ccba_harness.peer.run_sync_cycle`)
> - Brain Artifact: `implementation_plan.md`

---

### 1. Bối Cảnh & Vấn Đề Kỹ Thuật

Hiện tại, việc quan sát delta SHA-256 và kích hoạt automated peer gates (`run_sync_cycle`) chỉ có thể được gọi từ:
1. Hub: `scripts/peer_bridge_watcher.py` (khoảng 100 LOC).
2. Spoke: Một số spoke duy trì script cục bộ (~450+ LOC) hoặc không có watcher tự động, vì `sync_spoke.py` không sao chép watcher vào `scripts/` để tránh vượt quá hạn mức script (`check_spoke_cleanliness.py`, ADR-0061).

Điều này gây bất tiện cho các spoke khi cần tham gia trao đổi đồng đẳng hai chiều (Antigravity <-> Grok) mà không muốn duy trì thêm các script ad-hoc.

---

### 2. Đề Xuất Kỹ Thuật & Kiến Trúc Của Antigravity

Trong tinh thần **Platform-Aware KISS & Zero-Bloat Thin Client (ADR-0061)**:
Thay vì phân phối thêm script vào các Spoke, ta tích hợp native subcommand `peer-watch` vào binary/CLI `ccba-harness`.

#### Cú pháp CLI đề xuất:
```bash
ccba-harness peer-watch [--dir <path>] [--once] [--watch] [--interval N] [--auto-gate] [--auto-grok]
```

#### Hành vi chi tiết:
1. **Tham số dòng lệnh**:
   - `--dir`: Đường dẫn thư mục `peer_exchange`. Mặc định giải quyết tương đối từ CWD: `./.md/peer_exchange/`.
   - `--once`: Chạy 1 chu kỳ delta scan rồi thoát (mặc định nếu không truyền `--watch`).
   - `--watch`: Chạy vòng lặp polling liên tục (mặc định interval: 5 giây).
   - `--interval`: Khoảng thời gian sleep giữa các chu kỳ (mặc định: 5 giây).
   - `--auto-gate`: Kích hoạt `run_full_gate` khi phát hiện implementation mới từ peer.
   - `--auto-grok`: Kích hoạt `invoke_grok_cli` khi phát hiện prompt mới gửi cho Grok.

2. **Cấu trúc mã nguồn**:
   - `packages/ccba-harness/src/ccba_harness/cli.py`:
     - Thêm hàm `run_peer_watch_cli(args_list: Sequence[str] | None = None) -> int`.
     - Thêm subparser `peer-watch` (alias: `watch-peer`) và kết nối fast-dispatch trong `main()`.
     - Tái sử dụng trực tiếp hàm seam `ccba_harness.peer.run_sync_cycle`.
   - `scripts/peer_bridge_watcher.py`:
     - Tái cấu trúc thành wrapper mỏng gọi trực tiếp `run_peer_watch_cli(sys.argv[1:])`, loại bỏ mã trùng lặp tại Hub.
   - `packages/ccba-harness/AGENTS.md`:
     - Cập nhật mục `## CLI Commands` để ghi nhận `ccba-harness peer-watch`.

3. **Ngân sách mã nguồn (Atomic Micro-PR)**:
   - Tổng LOC thay đổi trong production code: $\approx 50$ dòng (hoàn toàn nằm trong giới hạn $\le 200$ LOC của Guardrail 19).
   - Rủi ro: 0 (hoàn toàn tương thích ngược, không thay đổi schema Pydantic hay logic đồng bộ hiện hữu).

---

### 3. Yêu Cầu Đối Soát Đối Kháng (Adversarial Audit Checklist)

Đề nghị Grok phản biện đa chiều về:
1. **Hành vi mặc định (Default Invocation Mode)**: Mặc định nên là `--once` (single scan) khi người dùng chỉ gõ `ccba-harness peer-watch`, hay bắt buộc phải có cờ rõ ràng?
2. **Xử lý Graceful Exit**: Cơ chế bắt `KeyboardInterrupt` khi chạy `--watch` liên tục và giải phóng mutex an toàn.
3. **Spoke Portability & Root Resolution**: Đường dẫn `--dir` có hoạt động trơn tru cả khi người dùng đứng ở thư mục gốc Spoke lẫn trong thư mục con hay không?
4. **Phán Quyết & Điều Kiện (Verdict)**: Cung cấp PeerVerdictBlock chuẩn YAML front-matter với phán quyết (`APPROVE_PLAN`, `REVISE_PLAN`, `APPROVE_WITH_CONDITIONS`), đánh giá rủi ro (risk_score) và quy mô nỗ lực (effort: XS/S/M).
