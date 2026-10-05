# HUB-ADR 0065: Cương Xương Vận Hành Tác Nhân Ngang Hàng, Khóa Topo Fail-Closed và Chuẩn Hóa Phán Quyết

- **Trạng thái**: ✅ ACCEPTED
- **Ngày quyết định**: 2026-10-06
- **Tác giả**: CCBA Core Architecture & Antigravity Agent
- **Người phản biện**: Grok Peer Reviewer (`APPROVE_WITH_CONDITIONS`, req-arch-audit-adrs-001)
- **Tương thích**: ADR-0030 (Telemetry), ADR-0058 (Deterministic Gate), ADR-0061 (Platform-Aware KISS v2), ADR-0062 (Declarative Sync Registry), ADR-0063 (Level-2 Peer Delegation Protocol), ADR-0064 (Peer Exchange Telemetry)

---

## 1. Bối Cảnh (Context)

Sau đợt thẩm định kiến trúc chuyên sâu toàn diện trên chuỗi 5 quyết định kiến trúc gần nhất (ADR-0060 $\to$ ADR-0064) được thực hiện bởi Grok-4.7 với cấu hình suy luận chuyên sâu (`--reasoning-effort xhigh`, 740,396 tokens, $0.2545 chi phí chính xác - PR #484), phán quyết chính thức đạt `APPROVE_WITH_CONDITIONS` kèm theo 4 điều kiện chặn vận hành (Blocking Conditions `COND-01` $\to$ `COND-04`) cần phải được giải quyết triệt để trước khi nâng cấp hệ thống lên Level-3 Autonomous Loopback:

1. **Lệch cấu hình Sandbox & Profile (`COND-01`)**:
   - Profile `patch_fast` trong `PROFILE_SPECS` thiếu giới hạn cứng `max_turns: 1` theo đặc tả ADR-0063.
   - Profile `agentic_code` chưa hạn chế đúng bộ công cụ đã cam kết (`read_file`, `search_replace`, `list_dir`), chưa đặt `reasoning_effort: "high"`.
   - Profile `arch_audit` đang chạy trong mã nguồn (`max_turns: 14`, `timeout: 600s`, `reasoning_effort: xhigh`) nhưng chưa được văn bản hóa chính thức trong bảng profile.
   - `PeerVerdictBlock` cần chuẩn hóa ràng buộc `risk_score` trong thang điểm 1–5 và quy định rõ cơ chế thích ứng `extra="ignore"` cho khả năng tiến hóa lược đồ giữa các tác nhân.

2. **Nguy cơ phán quyết chấp thuận giả lập từ Anchor Patch (`COND-02`)**:
   - Khi worker phụ trợ chỉ xuất payload bản vá neo `AnchorPatchPayload` mà không có khối `PeerVerdictBlock` chính thức, mã nguồn cũ tự động tổng hợp một `PeerVerdictBlock` mang trạng thái `verdict: APPROVE`.
   - Điều này vi phạm nghiêm ngặt Hiến pháp Layer 1 và ADR-0058: Bản vá neo chỉ là dữ liệu đầu vào cho lệnh `apply_anchor_patch`. Quyền phán quyết nghiệm thu (`APPROVE`) bắt buộc phải do tác nhân thẩm định chuyên trách ban hành hoặc do tiến trình orchestrator xác nhận sau khi `verify-patch` thoát mã 0.

3. **Hiện tượng nghẽn đơn luồng và tiến trình con mồ côi (`COND-03`)**:
   - Khóa `_SYNC_MUTEX` là một `threading.Lock` cục bộ trong tiến trình nhưng bị chiếm giữ xuyên suốt toàn bộ thời gian chạy subprocess `invoke_grok_cli` (120s – 900s), làm đóng băng toàn bộ luồng quan sát và cập nhật trạng thái khác.
   - Nhánh xử lý timeout chỉ gọi `proc.kill()` mà không tiêu diệt cả nhóm tiến trình (`process group`), có nguy cơ để lại các tiến trình con mồ côi (zombie processes).
   - `session_id` bị dùng chung giữa các mô hình trong vòng lặp fallback, dẫn đến nguy cơ sai lệch telemetry.
   - Tệp tóm tắt `grok_live_summary.md` được ghi mà không qua cơ chế khóa tệp `FileMutexLock`.

4. **Khuất phục chu trình phụ thuộc trong thuật toán sắp xếp Topo (`COND-04`)**:
   - Trong `discover_package_topology`, khi phát hiện chu trình phụ thuộc giữa các package trong monorepo, mã nguồn cũ lại tự động nối các nút kẹt chu trình vào cuối danh sách, biến một đồ thị có chu trình thành một thứ tự giả định thay vì kích hoạt cơ chế an toàn **Fail-Closed** trở về `DEFAULT_PACKAGE_TOPOLOGY_ORDER` như đã cam kết tại ADR-0062.
   - Các thao tác ghi tệp hoàn nguyên (rollback) trên hệ điều hành Windows gặp nguy cơ xung đột khóa tệp tạm thời (`PermissionError`) nếu thiếu cơ chế thử lại có khoảng đệm (retry with backoff).

---

## 2. Quyết Định Thiết Kế (Decision)

ADR-0065 thiết lập 4 quy chuẩn cương xương kỹ thuật nhằm giải quyết dứt điểm các điều kiện chặn trên:

### 2.1. Cương Xương Profile & Chuẩn Hóa Lược Đồ Phán Quyết (COND-01)
- Chuẩn hóa cứng `PROFILE_SPECS` trong `ccba_harness.peer`:
  - `patch_fast`: Cưỡng chế `max_turns: 1`, `deny: ["*"]`, `timeout: 120.0`.
  - `agentic_code`: Allowlist chính xác `["read_file", "search_replace", "list_dir"]`, cấm `spawn_subagent` và `run_terminal_command`, cấu hình `reasoning_effort: "high"`, `timeout: 600.0`.
  - `arch_audit`: Chính thức bổ sung vào bảng tiêu chuẩn với `max_turns: 14`, `timeout: 600.0`, `reasoning_effort: "xhigh"`, công cụ `["read_file", "grep", "list_dir"]`.
- `PeerVerdictBlock`: Thêm kiểm tra biên độ `risk_score: int | None = Field(default=None, ge=1, le=5)`. Giữ `extra="ignore"` và bộ chuyển đổi `_normalize_conditions` như một lớp tương thích ngược có kiểm soát (Compatibility Shim), bảo đảm các tác nhân thế hệ sau có thể bổ sung trường mở rộng mà không làm gãy parser của tác nhân hiện tại.

### 2.2. Xóa Bỏ APPROVE Giả Lập — Áp Đặt HANDOFF Cho Tệp Vá Neo (COND-02)
- Khi đầu ra từ worker chỉ chứa `AnchorPatchPayload` mà thiếu `PeerVerdictBlock`:
  - Mã nguồn **tuyệt đối không được** sinh phán quyết `APPROVE`.
  - Trạng thái bắt buộc phải là `HANDOFF` với tóm tắt: `"Fast-path anchor patch generated; pending orchestrator apply and verification."`.
  - Tiến trình orchestrator chịu trách nhiệm áp dụng bản vá qua `apply_anchor_patch` và chỉ xác nhận thành công sau khi `python -m ccba_harness verify-patch` đạt mã thoát 0.

### 2.3. Thu Hẹp Phạm Vi Mutex, Tiêu Diệt Process Group & Tránh Rò Bộ Nhớ (COND-03)
- **Thu hẹp phạm vi `_SYNC_MUTEX`**: Chỉ bao bọc đoạn mã đọc cache, quét delta, cập nhật `status.json` và `grok_live_summary.md`. Các lệnh gọi I/O dài hạn (`invoke_grok_cli`, `run_full_gate`) bắt buộc phải được kích hoạt **bên ngoài** khối `with _SYNC_MUTEX`.
- **Dọn sạch tiến trình con theo nhóm (`Process Group Cleanup`)**:
  - Subprocess được khởi chạy với `start_new_session=True` (trên POSIX) để tạo process group riêng biệt.
  - Hàm dọn dẹp `_terminate_proc_tree(proc)`: Gửi tín hiệu `SIGTERM` tới toàn bộ nhóm tiến trình (`os.killpg(os.getpgid(proc.pid), signal.SIGTERM)`), chờ tối đa 2.0s; nếu chưa dừng hẳn, gửi tiếp `SIGKILL` (`os.killpg(..., signal.SIGKILL)`) kèm theo lệnh `proc.wait(timeout=2.0)` lần thứ hai để loại bỏ hoàn toàn zombie processes.
- **Cách ly Session ID**: Di chuyển lệnh khởi tạo `session_id = str(uuid.uuid4())` vào bên trong vòng lặp thử nghiệm từng mô hình fallback, bảo đảm telemetry của mỗi mô hình độc lập tuyệt đối.
- **Giới hạn kích thước đọc `chat_history.jsonl`**: Kiểm tra dung lượng tệp trước khi đọc; nếu vượt quá 2MB, chỉ tìm kiếm và phân tích 2MB cuối cùng của tệp, tránh tràn bộ nhớ (OOM).
- **Khóa tệp cho Live Summary**: Bao bọc thao tác ghi `grok_live_summary.md` bằng `FileMutexLock(..., timeout=5.0)` và chuẩn hóa mốc thời gian sang định dạng UTC ISO 8601 (`YYYY-MM-DD HH:MM:SSZ`).

### 2.4. Thuật Toán Topo Fail-Closed Tuyệt Đối (COND-04)
- Trong `discover_package_topology`:
  - Khi thuật toán Kahn kết thúc, nếu số lượng package đã sắp xếp nhỏ hơn tổng số package trong đồ thị (`len(ordered) < len(dep_graph)`), tức là tồn tại chu trình phụ thuộc (circular dependency):
  - Hệ thống áp dụng cơ chế **Fail-Closed dứt khoát**: Hủy bỏ thứ tự dở dang và hoàn nguyên ngay lập tức về `list(DEFAULT_PACKAGE_TOPOLOGY_ORDER)`. Tuyệt đối cấm hành vi nối đuôi các nút kẹt chu trình vào cuối danh sách.
- **Khắc phục khóa tệp trên Windows**:
  - Trong `atomic_write_text`: Bổ sung cơ chế thử lại 3 lần với khoảng chờ lũy tiến (50ms) khi gặp `PermissionError` trên Windows trong bước `temp_file.replace(target)`.

---

## 3. Hệ Quả & Lợi Ích (Consequences)

### Lợi Ích (Positive)
1. **Hoàn toàn thỏa mãn 4 điều kiện chặn của Grok Audit (PR #484)**, mở đường vững chắc để kích hoạt Level-3 Autonomous Loopback (`peer-dispatch --auto-apply`).
2. **Loại bỏ triệt để hiện tượng Deadlock/Freeze**: Tiến trình quan sát nền (watcher) không còn bị kẹt hàng trăm giây khi Grok đang suy luận chuyên sâu.
3. **Bảo toàn tính toàn vẹn của cổng chất lượng**: Không còn phán quyết `APPROVE` giả mạo khi chưa vượt qua kiểm thử thực tế.
4. **An toàn hệ thống cao**: Loại bỏ hoàn toàn tiến trình con mồ côi (zombie processes) ngốn tài nguyên CPU/GPU khi xảy ra sự cố timeout.

### Tác Động Đến Mã Nguồn Hiện Tại
- `packages/ccba-harness/src/ccba_harness/peer.py`: Cập nhật `PROFILE_SPECS`, `PeerVerdictBlock`, `_run_single_grok_attempt`, `_terminate_proc_tree`, `run_sync_cycle`, `update_live_summary`, và `atomic_write_text`.
- `scripts/spoke/spoke_bootstrap.py`: Tinh chỉnh `discover_package_topology` thành fail-closed khi phát hiện chu trình.
- Bổ sung bộ kiểm thử đơn vị hồi quy chuyên biệt trong `packages/ccba-harness/tests/test_peer_runtime_hardening.py`.
