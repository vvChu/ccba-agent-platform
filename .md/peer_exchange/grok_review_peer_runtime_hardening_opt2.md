---
request_id: req-review-opt2-hardening-001
verdict: APPROVE
conditions: []
risk_score: 1
effort: S
summary: Gói gia cố Option 2 đạt chất lượng hoàn thiện cao, khắc phục chuẩn xác hệ
  số chia ticks telemetry theo quy ước xAI, bảo vệ tính nguyên tử nhị phân qua atomic_write_bytes,
  khóa đồng bộ đa tiến trình với FileMutexLock và tự động phục hồi giao dịch mồ côi.
telemetry:
  session_id: 0178eaf1-029d-4031-b34a-d9be67ed7404
  primary_model: gemini-3.8-flash-high
  input_tokens: 17281
  output_tokens: 2551
  reasoning_tokens: 4641
  cached_read_tokens: 0
  total_tokens: 19832
  model_calls: 1
  turn_count: 1
  cost_usd: 0.0344
  cost_mode: estimated
  duration_seconds: 41.01
---
# 📋 Báo Cáo Thẩm Định Mã Nguồn: Option 2 Runtime Hardening & Telemetry Normalization

## 1. Đánh Giá Tổng Quan
Gói triển khai **Option 2 (Gói Khuyến Nghị Mức Cao)** xử lý triệt để các rủi ro vận hành thời gian chạy đã được phát hiện trong đợt audit kiến trúc trước đó. Toàn bộ các thay đổi tuân thủ chặt chẽ các quyết định kiến trúc **ADR-0063 (Adaptive Peer Verification)**, **ADR-0064 (Peer Telemetry & Rate Card Governance)**, **ADR-0065 (Zero-Hang & Multi-Process Concurrency Invariants)** và hệ thống 10 Bugbot Invariants.

Hệ thống đạt được các cải tiến trọng yếu:
- Chuẩn hóa hoàn toàn thang đo chi phí telemetry giữa Grok CLI native ticks và hệ thống hạch toán nội bộ.
- Phân tầng biểu phí token chính xác giữa hạ tầng GPU cục bộ DGX Spark Blackwell GB10 ($0.00) và Gateway/Cloud.
- Đảm bảo tính nguyên tử nhị phân (binary ACID atomicity) trên hệ điều hành đa nền tảng (Windows/Linux) đối với cơ chế rollback giao dịch.
- Triệt tiêu nguy cơ xung đột tranh chấp ghi giữa nhiều tiến trình đồng thời qua cơ chế khóa kép (Dual Mutex Lock).
- Thiết lập cơ chế tự phục hồi giao dịch mồ côi ngay khi tiến trình giám sát khởi động.

---

## 2. Phân Tích Chi Tiết Từng Hạng Mục Triển Khai

### 2.1. Chuẩn Hóa Hệ Số Chia Ticks Telemetry (`_peer_telemetry.py`)
- **Điểm Thực Thi**: Sửa đổi hệ số chia trường `costUsdTicks` từ `10_000.0` thành hằng số chuẩn `10_000_000_000.0` ($10^{10}$).
- **Đánh Giá Kỹ Thuật**: 
  - Quy ước native của xAI CLI sử dụng đơn vị tick tương đương $10^{-10}$ USD ($1.00\text{ USD} = 10^{10}\text{ ticks}$). Việc hiệu chỉnh về mẫu số $10^{10}$ phản ánh đúng 100% giá trị tiêu hao thực tế từ API.
  - Tích hợp hàm `resolve_model_token_rates(primary_model)` và `resolve_model_token_rates(fallback_model)` đảm bảo tính nhất quán của nhánh tính toán ước lượng khi trường `costUsdTicks` bị khuyết thiếu.
  - Sử dụng hàm làm tròn `round(..., 4)` bảo đảm định dạng tiền tệ ổn định cho toàn bộ luồng telemetry.

### 2.2. Động Hóa Biểu Phí Token Theo Mô Hình (`telemetry.py`)
- **Điểm Thực Thi**: Bổ sung hàm `resolve_model_token_rates(model_id: str | None = None) -> tuple[float, float]`.
- **Đánh Giá Kỹ Thuật**:
  - Nhận diện chính xác định danh mô hình cục bộ (`qwen-local`, `local`) và gán mức phí `(0.0, 0.0)`. Cơ chế này phản ánh đúng thực tế vận hành trên hạ tầng máy chủ cục bộ Blackwell GB10, bảo đảm tính minh bạch trong báo cáo chi phí.
  - Fallback an toàn về cặp giá mặc định `(PRICE_PER_M_INPUT, PRICE_PER_M_OUTPUT)` tương ứng `($1.25, $5.00)` cho các mô hình định tuyến qua cloud hoặc gateway khi không có cấu hình riêng biệt.

### 2.3. Ghi Nhị Phân Nguyên Tử & Chống Khóa Tệp Đa Nền Tảng (`peer.py`)
- **Điểm Thực Thi**: Xây dựng hàm `atomic_write_bytes(target: Path, data: bytes, max_retries: int = 3)` và thay thế toàn bộ 4 vị trí gọi `write_bytes()` trực tiếp trong cơ chế rollback và phục hồi anchor transaction.
- **Đánh Giá Kỹ Thuật**:
  - **Bảo toàn vị trí cùng ổ đĩa**: Tệp tạm thời được tạo cùng thư mục cha (`target.parent`) với định dạng `.tmp_{pid}_{nanoseconds}`, bảo đảm thao tác `os.replace` diễn ra nguyên tử trên cùng inode/filesystem mà không phát sinh lỗi cross-device link.
  - **Bảo tồn quyền truy cập (`st_mode`)**: Đọc `stat().st_mode` của tệp hiện hữu và áp dụng `os.chmod` lên tệp tạm thời trước khi hoán đổi.
  - **Khả năng phục hồi khóa tệp**: Cơ chế thử lại 3 lần với thời gian chờ tăng dần `0.05 * (attempt + 1)` giải quyết triệt để vấn đề khóa tệp tạm thời (file locking) thường gặp trên môi trường Windows.
  - **Tự làm sạch khi lỗi**: Khối `except Exception` chủ động gọi `temp_file.unlink(missing_ok=True)`, ngăn chặn hoàn toàn việc rò rỉ các tệp rác mồ côi khi quá trình ghi gặp sự cố gián đoạn.

### 2.4. Khóa Đồng Bộ Kép Bảo Vệ Vùng Trọng Yếu (`peer.py`)
- **Điểm Thực Thi**: Áp dụng lồng ghép `FileMutexLock(sync_lock, timeout=10.0)` cùng `_SYNC_MUTEX` trong `run_sync_cycle`.
- **Đánh Giá Kỹ Thuật**:
  - Cấu trúc khóa kết hợp bảo vệ đồng thời cả luồng nội bộ (in-memory thread concurrency) và các tiến trình độc lập (cross-process CLI execution).
  - Khóa tệp được định vị tại `.sync.lock` với giới hạn thời gian chờ 10.0 giây, tuân thủ nguyên tắc fail-fast và loại trừ khả năng treo vĩnh viễn (zero-hang invariant).
  - Phạm vi bao bọc được thu hẹp chính xác vào các thao tác cập nhật `.bridge_cache.json`, `status.json` và `grok_live_summary.md`, tối ưu hóa hiệu năng tổng thể của chu trình đồng bộ.

### 2.5. Tự Động Phục Hồi Giao Dịch Mồ Côi Khi Khởi Động (`cli/commands/peer.py`)
- **Điểm Thực Thi**: Gọi `recover_pending_anchor_transactions(root=args.root)` ngay tại điểm vào của lệnh `run_peer_watch_cli`.
- **Đánh Giá Kỹ Thuật**:
  - Đảm bảo mọi giao dịch anchor bị gián đoạn do tiến trình bị dừng đột ngột (SIGINT, SIGTERM, crash) được hoàn nguyên nguyên vẹn trước khi chu trình theo dõi mới bắt đầu.
  - Đặt lệnh trong khối bảo vệ ngoại lệ, duy trì tính ổn định của watcher CLI trong mọi tình huống biên.

### 2.6. Kịch Bản Chuẩn Hóa Lịch Sử Telemetry (`normalize_peer_telemetry_costs.py`)
- **Điểm Thực Thi**: Quét và chuyển đổi các giá trị `cost_usd > 1000.0` về giá trị thực tế chia cho $10^6$.
- **Đánh Giá Kỹ Thuật**:
  - Hàm duyệt đệ quy `process_frontmatter_dict` xử lý toàn diện các cấu trúc lồng nhau trong YAML frontmatter.
  - Hỗ trợ chế độ dry-run mặc định để kiểm tra trước khi ghi đè qua cờ `--apply`.
  - Tích hợp tự động làm mới `status.json` sau khi chuẩn hóa xong dữ liệu trên đĩa.

### 2.7. Chất Lượng Kiểm Thử Tự Động (`tests/`)
- Bộ kiểm thử mới trong `test_peer_runtime_hardening.py` và `test_peer_telemetry.py` bao phủ đầy đủ các ca kiểm thử:
  - Khả năng bảo toàn chuỗi nhị phân thô, ký tự điều khiển CRLF và quyền tệp của `atomic_write_bytes`.
  - Cơ chế retry khi gặp lỗi giả lập `PermissionError`.
  - Kiểm tra vận hành của `run_sync_cycle` dưới sự bảo vệ của `.sync.lock`.
  - Kiểm tra tính toán chi phí $0.00 cho mô hình cục bộ `qwen-local`.

---

## 3. Đối Soát Tuân Thủ Các Invariants Cốt Lõi

| Invariant / Tiêu Chuẩn | Trạng Thái | Minh Chứng & Đánh Giá |
| :--- | :---: | :--- |
| **ACID Rollback & State Integrity** (ADR-0065) | **TUÂN THỦ** | 100% các điểm khôi phục trạng thái chuyển sang sử dụng `atomic_write_bytes`, loại trừ rủi ro tệp bị ghi dở dang khi xảy ra sự cố. |
| **Zero-Hang & Multi-Process Safety** (ADR-0065) | **TUÂN THỦ** | Khóa `FileMutexLock` với timeout xác định 10.0 giây ngăn chặn xung đột ghi đè tệp trạng thái giữa nhiều watcher song song. |
| **Telemetry & Cost Precision** (ADR-0064) | **TUÂN THỦ** | Hệ số chia $10^{10}$ phản ánh đúng quy ước của xAI CLI. Biểu phí token phân định rành mạch giữa tài nguyên tính toán cục bộ ($0) và đám mây. |
| **Idempotency & Clean Recovery** | **TUÂN THỦ** | Khởi động watcher CLI tự động rà soát và hoàn tất các giao dịch anchor còn tồn đọng từ các phiên chạy trước. |
| **Code Style & Type Safety** | **TUÂN THỦ** | Kiểu dữ liệu khai báo đầy đủ (`tuple[float, float]`, `Path`, `bytes`), xử lý ngoại lệ có chủ đích, định dạng mã nguồn đạt chuẩn 100%. |

---

## 4. Kết Luận & Khuyến Nghị Vận Hành

- **Kết Luận Thẩm Định**: Toàn bộ các thay đổi trong Option 2 đáp ứng đầy đủ các tiêu chuẩn kỹ thuật khắt khe của hệ thống harness. Bản vá hoàn toàn sẵn sàng để sáp nhập vào nhánh chính.
- **Khuyến Nghị Bổ Sung (Quan Sát Vận Hành)**:
  - Trong tệp `packages/ccba-harness/src/ccba_harness/cli/commands/peer.py`, tại khối xử lý ngoại lệ của `recover_pending_anchor_transactions`, bổ sung một dòng ghi log mức độ debug hoặc warning (ví dụ `logger.debug("Failed startup transaction recovery: %s", e)`) để hỗ trợ việc truy vết khi cần kiểm tra sâu hệ thống trong môi trường sản xuất.
