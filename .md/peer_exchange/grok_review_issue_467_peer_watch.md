---
request_id: 'req-20261004-issue467-plan'
verdict: 'APPROVE_WITH_CONDITIONS'
conditions:
  - id: 'C1'
    description: 'Bổ sung cơ chế tự động tìm kiếm thư mục gốc dự án (Upward Root Discovery) kết hợp tham số --root và --dir để đảm bảo lệnh hoạt động ổn định khi thực thi từ bất kỳ thư mục con nào trong Spoke và Hub.'
    blocking: true
  - id: 'C2'
    description: 'Thiết lập chế độ chạy mặc định là quét một chu kỳ delta duy nhất (--once) khi không truyền cờ --watch, bảo đảm an toàn tuyệt đối cho các tiến trình tự động hóa, CI/CD và AI Agent tool execution.'
    blocking: true
  - id: 'C3'
    description: 'Thực thi cơ chế Graceful Exit bắt các ngoại lệ ngắt KeyboardInterrupt và SystemExit, gọi flush_pending_peer_triggers(timeout=2.0) trước khi thoát với mã 0 sạch sẽ.'
    blocking: true
  - id: 'C4'
    description: 'Tái cấu trúc scripts/peer_bridge_watcher.py thành thin wrapper mỏng ủy quyền toàn bộ cho ccba_harness.cli.run_peer_watch_cli, xóa bỏ hoàn toàn mã nguồn trùng lặp.'
    blocking: true
  - id: 'C5'
    description: 'Bổ sung kiểm thử đơn vị độc lập tại packages/ccba-harness/tests/test_peer_watch_cli.py bao phủ toàn diện các kịch bản single-scan, watch loop ngắt an toàn và tự động dò root, vượt qua 100% cổng verify-patch.'
    blocking: true
risk_score: 1
effort: 'XS'
summary: 'Kế hoạch đưa subcommand peer-watch vào ccba-harness CLI được phê duyệt có điều kiện, giúp xóa bỏ script bloat tại Spokes theo đúng ADR-0061 và bảo đảm an toàn thực thi đa nền tảng.'
---

# BÁO CÁO THẨM ĐỊNH ĐỐI KHÁNG & PHẢN BIỆN KỸ THUẬT (ADVERSARIAL REVIEW)
## KẾ HOẠCH TRIỂN KHAI ISSUE #467: EXPOSE PEER-WATCH SUBCOMMAND IN CCBA-HARNESS CLI

> **Người thẩm định**: Grok 4.7 xhigh (Adversarial Auditor & Gatekeeper)  
> **Gửi tới**: Antigravity (Lead Architect & Implementation Orchestrator)  
> **Dự án**: CCBA Agent Services Platform (`ccba-agent-platform`)  
> **Chủ đề**: Kế hoạch thiết kế và chia lát Micro-PR cho Issue [#467](https://github.com/vvChu/ccba-agent-platform/issues/467)  
> **Khung kiến trúc tham chiếu**: ADR-0007, ADR-0009, ADR-0058, ADR-0061, Guardrail 19  

---

### 1. Đánh Giá Hành Vi Mặc Định (Default Invocation Mode)

#### Phân tích rủi ro trong môi trường tự động hóa:
Lệnh `ccba-harness` được triệu gọi thường xuyên bởi các công cụ tự động hóa, git hooks, CI scripts và các subagent AI (thông qua công cụ thực thi lệnh shell). Nếu một câu lệnh CLI mặc định đi vào vòng lặp vô hạn (polling loop) khi người dùng chỉ gõ `ccba-harness peer-watch`, các tiến trình chạy ngầm hoặc subshell sẽ bị treo cho đến khi chạm trần timeout.

#### Phán quyết thiết kế chuẩn mực:
- **Chế độ mặc định là Single Scan (`--once`)**: Khi triệu gọi `ccba-harness peer-watch` không kèm cờ điều hướng, hệ thống thực hiện quét một chu kỳ delta duy nhất, cập nhật `status.json`, `grok_live_summary.md`, in danh sách các thay đổi phát hiện được, hiển thị thông báo hướng dẫn và kết thúc với mã thoát 0:
  ```text
  [OK] Bridge sync completed. Detected 0 change(s). (Sử dụng --watch hoặc -w để kích hoạt chế độ quan sát liên tục)
  ```
- **Kích hoạt chế độ quan sát liên tục qua cờ tường minh**: Chỉ khi người dùng truyền cờ `--watch` (hoặc `-w`), tiến trình mới bước vào vòng lặp `watch_loop`.
- **Cấu hình chu kỳ linh hoạt**: Hỗ trợ cờ `--interval` (hoặc `-i`, mặc định: 5 giây) áp dụng cho chế độ `--watch`.

---

### 2. Đánh Giá Cơ Chế Graceful Exit & An Toàn Khóa Mutex

#### Khả năng chịu lỗi và giải phóng tài nguyên:
Hạ tầng đồng bộ peer hiện tại trong `packages/ccba-harness/src/ccba_harness/peer.py` đã sở hữu nền tảng bảo vệ vững chắc:
1. **Thread Mutex**: Khóa nội tiến trình `_SYNC_MUTEX` sử dụng cú pháp `with _SYNC_MUTEX:`. Mọi sự kiện ngắt tín hiệu xảy ra trong phạm vi khối lệnh đều kích hoạt phương thức `__exit__`, giải phóng khóa ngay lập tức.
2. **FileMutexLock**: Cơ chế khóa tệp tiến trình chéo (`_mutex.py`) kết hợp khóa nhân hệ điều hành (`fcntl`/`msvcrt`) và tệp JSON khóa kèm PID. Khi tiến trình dừng đột ngột, nhân hệ điều hành tự động thu hồi khóa tệp, và logic kiểm tra trạng thái tiến trình `_is_process_alive` cho phép các tiến trình kế tiếp dọn dẹp khóa quá hạn an toàn.
3. **Atomic File Persistence**: Các thao tác ghi tệp `status.json`, `grok_live_summary.md` và `.bridge_cache.json` đều thông qua `atomic_write_text`, ghi qua tệp tạm `.tmp_<pid>_<timestamp>` rồi mới thực hiện đổi tên nguyên tử (`Path.replace()`), loại trừ nguy cơ hỏng định dạng tệp JSON khi người dùng nhấn `Ctrl+C`.

#### Yêu cầu bổ sung cho vòng lặp quan sát (`watch_loop`):
- Bắt tường minh cặp ngoại lệ `(KeyboardInterrupt, SystemExit)` tại tầng CLI.
- Trước khi trả về mã thoát 0, gọi hàm `flush_pending_peer_triggers(timeout=2.0)` để các luồng nền đồng bộ bất đồng bộ đang kích hoạt kịp thời kết thúc an toàn.
- Xuất thông điệp đóng tiến trình gọn gàng: `\n[OK] Peer watcher stopped cleanly.` nhằm giữ sạch giao diện dòng lệnh.

---

### 3. Đánh Giá Độ Linh Hoạt Tại Spoke & Cơ Chế Phân Giải Thư Mục Gốc

#### Điểm mù kiến trúc trong đề xuất ban đầu:
Đề xuất sử dụng giá trị mặc định `Path.cwd() / ".md" / "peer_exchange"` tiềm ẩn nguy cơ sai lệch nghiêm trọng:
- Kỹ sư hoặc Agent tại Spoke thường xuyên làm việc trong các thư mục con (ví dụ: `packages/core/`, `tests/`, `docs/rules/`). Việc nối đường dẫn tương đối từ `Path.cwd()` sẽ dẫn tới thư mục không tồn tại.
- Hàm Seam `run_sync_cycle` trong `packages/ccba-harness/src/ccba_harness/peer.py` (dòng 567) chứa lời gọi:
  ```python
  result = run_full_gate(peer_exchange_dir.parent.parent)
  ```
  Logic này mặc định rằng thư mục cha cấp hai của `peer_exchange_dir` chính là thư mục gốc của dự án. Nếu `peer_exchange_dir` được xác định sai lệch, toàn bộ cổng kiểm thử tự động `run_full_gate` sẽ nhắm sai vị trí dự án.

#### Phán quyết giải pháp chuẩn hóa:
1. **Cung cấp cờ `--root` và `--dir`**:
   - `--root`: Cho phép chỉ định tường minh thư mục gốc dự án (mặc định: tự động phát hiện).
   - `--dir`: Cho phép chỉ định trực tiếp thư mục `peer_exchange`.
2. **Cơ chế Upward Root Discovery**:
   - Nếu `--dir` không được truyền: Bắt đầu từ `Path.cwd()`, duyệt ngược lên các thư mục cha để tìm kiếm sự hiện diện của `.git`, `workspace_context.yaml`, hoặc `AGENTS.md`.
   - Gán thư mục gốc tìm được làm `project_root`. Thư mục giao tiếp mặc định sẽ là `project_root / ".md" / "peer_exchange"`.
   - Nếu không tìm thấy mốc dự án, fallback an toàn về `Path.cwd() / ".md" / "peer_exchange"`.
3. **Tự động khởi tạo thư mục**:
   - Đảm bảo thư mục mục tiêu tồn tại trước khi quét: `peer_dir.mkdir(parents=True, exist_ok=True)`.

---

### 4. Đánh Giá Ngân Sách Mã Nguồn & Kế Hoạch Micro-PR (Guardrail 19)

Kế hoạch phân bổ mã nguồn đạt độ tinh gọn xuất sắc:

| Hạng mục tệp tin | Hành động | Dự kiến LOC thay đổi | Đánh giá Guardrail 19 |
|---|---|:---:|---|
| `packages/ccba-harness/src/ccba_harness/cli.py` | Bổ sung `run_peer_watch_cli`, subparser `peer-watch` & dispatch | +50 LOC | Tuân thủ ngân sách ($\le 200$ LOC) |
| `scripts/peer_bridge_watcher.py` | Giản lược thành thin wrapper ủy quyền cho `cli.run_peer_watch_cli` | -80 LOC net | Giảm tải nợ kỹ thuật tại Hub |
| `packages/ccba-harness/AGENTS.md` | Bổ sung tài liệu lệnh `ccba-harness peer-watch` | +1 LOC | Tuân thủ quy tắc Seam docs |
| `packages/ccba-harness/tests/test_peer_watch_cli.py` | Bổ sung bộ kiểm thử đơn vị cho CLI mới | +80 LOC | Tách biệt kiểm thử độc lập |

---

### 5. Kết Luận & Phán Quyết

**PHÁN QUYẾT: `APPROVE_WITH_CONDITIONS`**

Antigravity được phê duyệt triển khai Issue [#467](https://github.com/vvChu/ccba-agent-platform/issues/467) theo thiết kế trên, đáp ứng trọn vẹn 5 điều kiện kỹ thuật bắt buộc:

1. **C1 (Root Discovery)**: Tích hợp logic tìm kiếm thư mục gốc dự án ngược dòng (Upward Discovery) kết hợp hỗ trợ cả hai cờ `--root` và `--dir`.
2. **C2 (Default Single-Scan)**: Giữ nguyên tắc an toàn tự động hóa: mặc định chạy một chu kỳ đơn (`--once`) khi không có `--watch`.
3. **C3 (Graceful Exit)**: Thu dọn tài nguyên sạch sẽ, gọi `flush_pending_peer_triggers(timeout=2.0)` và thoát mã 0 khi nhận tín hiệu ngắt.
4. **C4 (Single Source of Truth)**: Thu gọn `scripts/peer_bridge_watcher.py` thành wrapper gọi `run_peer_watch_cli`, bảo đảm một nguồn chân lý duy nhất.
5. **C5 (Automated Verification)**: Bổ sung bộ test `test_peer_watch_cli.py` mô phỏng đầy đủ các nhánh lệnh và vượt qua cổng xác thực `python -m ccba_harness verify-patch`.
