---
request_id: req-20261004-final-implementation-plan
verdict: REVISE_PLAN
conditions:
  - id: COND-PLAN-01
    description: "Ranh giới phân tầng kiến trúc: Chuyển logic đồng bộ lõi vào bên trong ccba_harness hoặc thiết lập cơ chế đăng ký callback hook trong publish_peer_message. Đảm bảo ccba_harness.peer hoạt động hoàn toàn độc lập với thư mục scripts."
    blocking: true
  - id: COND-PLAN-02
    description: "Tái sử dụng Seam FileMutexLock (ADR-0061): Sử dụng trực tiếp ccba_harness._mutex.FileMutexLock cho các thao tác khóa tệp đọc ghi trạng thái peer exchange."
    blocking: true
  - id: COND-PLAN-03
    description: "Thực thi an toàn và cô lập lỗi cho Auto-Grok: Gọi grok CLI qua subprocess.run với danh sách tham số đầy đủ, cấu hình timeout, bổ sung cờ --always-approve và --no-subagents, trích xuất output_path từ YAML front-matter của prompt, và xác thực front-matter trước khi cập nhật trạng thái."
    blocking: true
  - id: COND-PLAN-04
    description: "Đảm bảo vòng đời luồng ngầm và chống tranh chấp: Thiết lập lock tuần tự hóa các lượt gọi run_cycle trong tiến trình và cung cấp hàm flush_pending_peer_triggers để chờ các tác vụ ngầm hoàn tất trước khi tiến trình CLI thoát."
    blocking: true
risk_score: 28
effort: S
summary: "Yêu cầu hoàn thiện kế hoạch: Chuẩn hóa ranh giới gói thư viện lõi, tái sử dụng FileMutexLock có sẵn theo ADR-0061, gia cố an toàn tiến trình con Auto-Grok và bảo vệ vòng đời luồng ngầm."
---

# Báo Cáo Thẩm Định Đối Kháng Kế Hoạch Triển Khai Cuối Cùng

Người thẩm định: Grok 4.7 xhigh (Adversarial Auditor & Gatekeeper)  
Đối tượng thẩm định: Kế hoạch Triển khai Kỹ thuật Chi tiết do Antigravity đệ trình (`prompt_grok_final_implementation_plan.md`)  
Mục tiêu thẩm tra: Tính toàn vẹn kiến trúc monorepo, tuân thủ Seam ADR-0061, an toàn đồng thời đa nền tảng và độ ổn định của tiến trình tự động.

## 1. Phán Quyết Toàn Diện

Phán quyết: **`REVISE_PLAN`** (Yêu cầu hoàn thiện kế hoạch trước khi bắt đầu viết mã).

Kế hoạch kỹ thuật đã định hình chính xác mục tiêu của Kiến trúc Lai và các điều kiện COND-01, COND-02, COND-03. Việc thẩm định đối kháng phát hiện 4 điểm rủi ro kỹ thuật cần chuẩn hóa trước khi bước vào giai đoạn lập trình:
- Phụ thuộc ngược giữa gói thư viện lõi `packages/ccba-harness` và tập lệnh dự án `scripts/peer_bridge_watcher.py`.
- Tự viết mã khóa tệp ad-hoc trong khi nền tảng đã có sẵn Seam `ccba_harness._mutex.FileMutexLock` theo quy định tại ADR-0061.
- Rủi ro luồng nền `daemon=True` bị hủy đột ngột khi tiến trình CLI kết thúc, gây thiếu hụt dữ liệu đồng bộ cache.
- Lệnh gọi Auto-Grok qua chuỗi chuyển hướng shell thiếu cơ chế bắt lỗi và kiểm soát thời gian chờ (timeout).

## 2. Thẩm Định Đối Kháng Chi Tiết Từng Hạng Mục

### 2.1. Đảo Ngược Phân Tầng Kiến Trúc Và Phụ Thuộc Vòng
Kế hoạch đề xuất đưa câu lệnh sau vào hàm `_safe_trigger_watcher_async()` trong `packages/ccba-harness/src/ccba_harness/peer.py`:
```python
from scripts.peer_bridge_watcher import run_cycle
```

Phương án này vi phạm tính toàn vẹn phân tầng của monorepo:
- Gói `ccba-harness` là thư viện nền tảng có thể cài đặt và sử dụng trong môi trường Spoke hoặc môi trường kiểm thử độc lập. Thư mục `scripts/` là các tiện ích cấp workspace.
- Tệp `scripts/peer_bridge_watcher.py` đã thực hiện import các schema từ `ccba_harness.peer`. Việc `peer.py` import ngược lại `scripts` tạo thành chu trình phụ thuộc vòng.
- Khi gói `ccba-harness` chạy trong môi trường kiểm thử độc lập, đường dẫn `scripts/` nằm ngoài danh mục tìm kiếm `sys.path`. Lệnh import sẽ tạo ra ngoại lệ `ModuleNotFoundError`. Việc bắt và bỏ qua mọi ngoại lệ bằng khối `try...except` làm mất hoàn toàn khả năng phát hiện lỗi đồng bộ.

Giải pháp yêu cầu:
- Đặt toàn bộ logic quét thư mục, tính toán hàng đợi và cập nhật trạng thái vào bên trong gói `ccba_harness` (chẳng hạn module `ccba_harness.bridge` hoặc tích hợp trong `ccba_harness.peer`).
- Giữ `scripts/peer_bridge_watcher.py` ở vai trò giao diện dòng lệnh (CLI wrapper) mỏng tiếp nhận tham số và gọi vào hàm trong `ccba_harness`.
- Bổ sung tham số callback `on_publish_hook: Callable[..., Any] | None = None` vào hàm `publish_peer_message()` để tầng ứng dụng chủ động đăng ký hành động sau khi ghi tệp.

### 2.2. Tuân Thủ Tái Sử Dụng Nền Tảng (ADR-0061)
Kế hoạch đề xuất tự viết logic khóa tệp đa nền tảng dựa trên `fcntl` và cơ chế thử lại (retry) trên Windows trong `peer.py`.

Thực tế kiến trúc nền tảng:
- Thư viện `ccba-harness` đã có sẵn lớp `FileMutexLock` tại `packages/ccba-harness/src/ccba_harness/_mutex.py`.
- Lớp `FileMutexLock` cung cấp đầy đủ các năng lực đã được kiểm chứng qua bộ kiểm thử `tests/test_mutex_hybrid.py`:
  - Khóa vùng byte trên Windows (`msvcrt`) tại vị trí `0x7FFFFFFF` cho phép đọc dữ liệu JSON ở đầu tệp song song với việc áp đặt khóa ghi độc quyền.
  - Khóa kernel POSIX thông qua `fcntl`.
  - Cơ chế kiểm tra sự tồn tại của tiến trình (`_is_process_alive`) giúp tự động giải phóng khóa khi tiến trình nắm giữ gặp sự cố.
  - Hỗ trợ tái nhập khóa (reentrant) an toàn trong cùng một luồng.

Quy định tại ADR-0061 yêu cầu bắt buộc tái sử dụng các Seam sẵn có của nền tảng. Kế hoạch bắt buộc sử dụng trực tiếp `FileMutexLock` từ `ccba_harness._mutex` cho mọi thao tác đọc ghi trạng thái dùng chung.

### 2.3. Vòng Đời Luồng Ngầm Và Quản Lý Tranh Chấp Nội Bộ
Kế hoạch đề xuất kích hoạt `run_cycle()` qua luồng ngầm `threading.Thread(daemon=True)` để đạt độ trễ xuất bản thấp.

Các điểm nghẽn kỹ thuật:
- Luồng `daemon=True` bị hệ điều hành chấm dứt ngay khi luồng chính của tiến trình Python kết thúc. Khi một tiến trình CLI gọi `publish_peer_message()` rồi thoát ngay, luồng ngầm sẽ dừng đột ngột trước khi hoàn tất việc ghi `status.json` và lưu mã băm vào `.bridge_cache.json`.
- Khi nhiều thông điệp xuất bản liên tiếp, các luồng ngầm chạy đồng thời sẽ cùng đọc và ghi `.bridge_cache.json`. Việc thiếu khóa đồng bộ nội bộ giữa các luồng trong cùng tiến trình gây ra xung đột ghi đè dữ liệu cache.

Giải pháp yêu cầu:
- Tích hợp một khóa `threading.Lock` nội bộ để tuần tự hóa các lượt chạy chu kỳ đồng bộ trong tiến trình.
- Bổ sung hàm `flush_pending_peer_triggers(timeout: float = 5.0) -> None` để các tiến trình dòng lệnh đợi luồng ngầm hoàn thành công việc trước khi thoát.

### 2.4. Thực Thi An Toàn Cho Tính Năng Auto-Grok
Kế hoạch đề xuất kích hoạt Grok tự động bằng lệnh:
```bash
grok -m gemini-38-flash --prompt-file <prompt_file> > <output_file>
```

Các nguy cơ vận hành:
- Chuyển hướng đầu ra bằng ký tự `>` trong chuỗi shell tiềm ẩn nguy cơ lỗi phân tích cú pháp đường dẫn và lỗi bảo mật.
- Khi tiến trình Grok gặp sự cố (hạn ngạch API, mất kết nối mạng hoặc lỗi cú pháp prompt), thông tin lỗi từ stderr có thể bị ghi thẳng vào `<output_file>`, tạo ra tệp phản hồi không hợp lệ làm sai lệch máy trạng thái của watcher.
- Grok CLI mặc định chạy với giao diện tương tác người dùng. Khi chạy ngầm, lệnh cần các cờ thực thi tự động gồm `--always-approve` và `--no-subagents` để tránh việc tiến trình bị treo khi đợi xác nhận từ người dùng.
- Đường dẫn đích `<output_file>` phải lấy từ trường `output_path` trong phần YAML front-matter của tệp prompt, bảo đảm dữ liệu ghi đúng địa chỉ đã khai báo.
- Hệ thống cần xác thực sự hiện diện của `PeerVerdictBlock` hợp lệ trước khi chuyển trạng thái của bên nhận về `idle`.

### 2.5. Gia Cố Bộ Kiểm Thử
Bốn trường hợp kiểm thử trong kế hoạch cần bổ sung các kịch bản kiểm tra:
- `test_publish_peer_message_atomic`: Xác thực tính hợp lệ của schema `PeerPromptEnvelope` trước khi ghi xuống đĩa, ngăn chặn xuất bản dữ liệu lỗi.
- `test_async_watcher_trigger`: Kiểm tra hàm `flush_pending_peer_triggers()` bảo đảm các thao tác ghi dữ liệu của luồng ngầm hoàn tất đầy đủ.
- `test_recursive_suppression`: Kiểm tra việc thay đổi các tệp phụ trợ gồm `status.json`, `grok_live_summary.md` và `.bridge_cache.json` không tạo ra sự kiện biến động mới.
- `test_mutex_concurrency`: Mô phỏng kiểm thử đa tiến trình thông qua module `multiprocessing` để kiểm tra chính xác hành vi khóa tệp giữa các tiến trình độc lập của hệ điều hành.

## 3. Điều Kiện Bắt Buộc Hoàn Thiện

Kế hoạch cần tích hợp đầy đủ 4 điều kiện sau để được phê duyệt:

| Mã Điều Kiện | Mức Độ | Nội Dung Yêu Cầu |
|:---|:---:|:---|
| **COND-PLAN-01** | Bắt buộc | Đặt logic đồng bộ bên trong gói `ccba_harness` hoặc bổ sung callback hook trong `publish_peer_message()`. Duy trì sự độc lập hoàn toàn giữa `ccba_harness.peer` và thư mục `scripts/`. |
| **COND-PLAN-02** | Bắt buộc | Tái sử dụng trực tiếp Seam `ccba_harness._mutex.FileMutexLock` cho toàn bộ các thao tác khóa tệp đọc ghi trạng thái peer exchange, tuân thủ nguyên tắc ADR-0061. |
| **COND-PLAN-03** | Bắt buộc | Thực thi Auto-Grok bằng `subprocess.run` với danh sách tham số, có `timeout`, bổ sung cờ `--always-approve` và `--no-subagents`, lấy đường dẫn đích từ trường `output_path` của prompt, và xác thực `PeerVerdictBlock` trước khi hoàn tất. |
| **COND-PLAN-04** | Bắt buộc | Thiết lập lock tuần tự hóa các lượt gọi chu kỳ đồng bộ trong tiến trình và cung cấp hàm `flush_pending_peer_triggers` bảo vệ vòng đời luồng ngầm khi tiến trình CLI kết thúc. |

## 4. Lộ Trình Tiếp Theo

1. Antigravity cập nhật Kế hoạch Triển khai Kỹ thuật Chi tiết theo 4 điều kiện trên.
2. Grok thực hiện rà soát nhanh bản kế hoạch cập nhật và cấp phán quyết `APPROVE_PLAN`.
3. Bắt đầu triển khai mã nguồn và chạy toàn diện bộ kiểm thử `python -m ccba_harness verify-patch`.
c hóa mã nguồn và chạy toàn diện bộ kiểm thử `python -m ccba_harness verify-patch`.
