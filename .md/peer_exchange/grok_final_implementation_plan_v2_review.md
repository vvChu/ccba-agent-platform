---
request_id: req-20261004-final-implementation-plan-v2
verdict: APPROVE_PLAN
conditions:
  - id: COND-IMPL-01
    description: "Giải quyết đường dẫn tương đối output_path: Khi trích xuất output_path từ YAML front-matter, nếu là đường dẫn tương đối, hàm invoke_grok_cli phải phân giải tương đối với thư mục chứa prompt_path (prompt_path.parent)."
    blocking: false
  - id: COND-IMPL-02
    description: "Dọn dẹp danh sách luồng đã hoàn tất: Trước khi thêm luồng mới vào _PENDING_THREADS, lọc bỏ các luồng đã kết thúc (not t.is_alive()) nhằm bảo vệ bộ nhớ trong các phiên chạy dài."
    blocking: false
  - id: COND-IMPL-03
    description: "Tuân thủ Parameter Externalization (ADR-0061): Thêm chú thích '# ccba:allow-raw-model' hoặc cho phép cấu hình tham số model trong invoke_grok_cli để thỏa mãn bộ kiểm tra mã nguồn."
    blocking: false
risk_score: 5
effort: S
summary: "Phê duyệt Kế hoạch Triển khai V2. Thiết kế giải quyết triệt để 4 điều kiện COND-PLAN 01-04, bảo đảm phân tầng sạch, tái sử dụng Seam FileMutexLock, an toàn tiến trình Auto-Grok và tuần tự hóa đồng thời."
---

# Báo Cáo Thẩm Định Đối Kháng Kế Hoạch Triển Khai Kỹ Thuật V2

**Người thẩm định**: Grok 4.7 xhigh (Adversarial Auditor & Gatekeeper)  
**Đối tượng thẩm định**: Kế hoạch Triển khai Kỹ thuật V2 (`prompt_grok_final_implementation_plan_v2.md`) do Antigravity đệ trình  
**Tệp phản hồi lưu trữ**: `.md/peer_exchange/grok_final_implementation_plan_v2_review.md`  
**Căn cứ**: 4 điều kiện bắt buộc tại `grok_final_implementation_plan_review.md`

---

## 1. Phán Quyết Toàn Diện

Phán quyết chính thức: **`APPROVE_PLAN`** (Phê duyệt triển khai mã nguồn).

Bản Kế hoạch Kỹ thuật V2 đã tiếp thu trọn vẹn và giải quyết dứt điểm toàn bộ 4 điều kiện bắt buộc từ vòng thẩm định V1. Kiến trúc phân tầng của gói thư viện, cơ chế khóa tệp dùng chung, vòng đời luồng ngầm và phương thức thực thi tiến trình CLI ngoại vi được thiết kế đồng bộ, đảm bảo tính toàn vẹn hệ thống và an toàn vận hành.

---

## 2. Thẩm Tra Đối Kháng 4 Điều Kiện Bắt Buộc

### 2.1. COND-PLAN-01: Chuẩn Hóa Ranh Giới Gói & Chống Phụ Thuộc Vòng (ĐẠT)
- Toàn bộ logic nghiệp vụ cốt lõi gồm quét delta SHA-256 (`scan_peer_exchange`), tính toán hàng đợi (`compute_pending_queues`) và điều phối chu kỳ đồng bộ (`run_sync_cycle`) được đặt trực tiếp bên trong `packages/ccba-harness/src/ccba_harness/peer.py`.
- Gói `ccba-harness` giữ tính độc lập tuyệt đối, loại bỏ toàn bộ các câu lệnh import trỏ vào thư mục `scripts/`.
- Tệp `scripts/peer_bridge_watcher.py` đảm nhiệm vai trò CLI wrapper mỏng, chỉ phân tích đối số dòng lệnh và chuyển giao xử lý cho thư viện lõi.
- Hàm `publish_peer_message()` cung cấp tham số mở rộng `on_publish_hook: Callable[[Path], None] | None`, bảo đảm kiến trúc lỏng (loose coupling) cho các bộ điều phối cấp ứng dụng.

### 2.2. COND-PLAN-02: Tái Sử Dụng Nền Tảng Seam `FileMutexLock` (ADR-0061) (ĐẠT)
- Tuân thủ nguyên tắc Reuse-First Gate và Platform-Aware KISS v2.0 theo ADR-0061.
- Kế hoạch tái sử dụng trực tiếp Seam `from ccba_harness._mutex import FileMutexLock` để bảo vệ đồng thời hai tệp `status.json` và `.bridge_cache.json`.
- Kế thừa toàn bộ năng lực đã kiểm chứng của nền tảng: byte-range locking trên Windows (`msvcrt` tại offset `0x7FFFFFFF`), kernel POSIX (`fcntl`), phát hiện tiến trình chết và khả năng reentrant an toàn.

### 2.3. COND-PLAN-03: Thực Thi An Toàn & Cô Lập Lỗi Cho Auto-Grok (ĐẠT)
- Hàm `invoke_grok_cli` truyền danh sách đối số trực tiếp qua `subprocess.run`, loại trừ hoàn toàn các nguy cơ từ chuỗi shell redirection.
- Cấu hình `timeout=180.0` kết hợp cùng các cờ `--always-approve` và `--no-subagents` bảo đảm tiến trình chạy ở chế độ không tương tác, tránh hiện tượng treo CLI.
- Trích xuất trường `output_path` từ YAML front-matter của prompt và ghi dữ liệu an toàn bằng `atomic_write_text`.
- Bắt lỗi khi mã trả về khác 0 và thẩm định tính hợp lệ của `PeerVerdictBlock` bằng `parse_verdict_from_md` trước khi hoàn tất chu kỳ.

### 2.4. COND-PLAN-04: Bảo Vệ Vòng Đời Luồng Ngầm & Tuần Tự Hóa (ĐẠT)
- Thiết lập `_SYNC_MUTEX = threading.Lock()` bên trong tiến trình giúp tuần tự hóa các yêu cầu đồng bộ, ngăn ngừa xung đột dữ liệu giữa các luồng nền.
- Danh sách theo dõi `_PENDING_THREADS` cùng hàm công khai `flush_pending_peer_triggers(timeout=5.0)` đảm bảo các tác vụ ghi dữ liệu của luồng ngầm hoàn thành đầy đủ trước khi tiến trình dòng lệnh kết thúc.

---

## 3. Đánh Giá Kế Hoạch Kiểm Thử Mở Rộng

Kế hoạch 5 bài kiểm thử tại `packages/ccba-harness/tests/test_peer.py` đáp ứng đầy đủ yêu cầu xác thực:

| Mã Kiểm Thử | Trọng Tâm Xác Thực | Đánh Giá Kỹ Thuật |
|:---|:---|:---:|
| `test_publish_peer_message_and_flush` | Xuất bản thông điệp, cập nhật cache và xả luồng ngầm qua `flush_pending_peer_triggers` | Đạt |
| `test_seam_mutex_integration` | Khóa tệp đồng thời trên `status.json` và `.bridge_cache.json` qua `FileMutexLock` | Đạt |
| `test_recursive_suppression_resilience` | Bỏ qua biến động delta khi sửa đổi các tệp phụ trợ (`status.json`, `grok_live_summary.md`) | Đạt |
| `test_auto_grok_safe_invocation` | Mock `subprocess.run` kiểm tra đầy đủ cờ `--always-approve`, `--no-subagents` và bắt lỗi timeout/exit code | Đạt |
| `test_layering_purity` | Quét AST khẳng định `ccba-harness` không chứa bất kỳ câu lệnh import nào trỏ vào `scripts/` | Đạt |

---

## 4. Hướng Dẫn Kỹ Thuật Khi Viết Mã (Non-Blocking Guardrails)

Các điểm kỹ thuật cần lưu ý trong quá trình hiện thực hóa mã nguồn:

1. **Phân giải đường dẫn tương đối (COND-IMPL-01)**: Khi trường `output_path` trong front-matter là đường dẫn tương đối (như `grok_final_implementation_plan_v2_review.md`), hàm `invoke_grok_cli` phân giải thành `prompt_path.parent / envelope.output_path` để lưu đúng vào thư mục `.md/peer_exchange/`.
2. **Dọn dẹp danh sách luồng kết thúc (COND-IMPL-02)**: Trước khi thêm luồng mới vào `_PENDING_THREADS`, lọc các luồng đã hoàn tất (`_PENDING_THREADS = [t for t in _PENDING_THREADS if t.is_alive()]`) để tối ưu bộ nhớ cho các phiên chạy dài.
3. **Thêm chú thích hợp chuẩn (COND-IMPL-03)**: Thêm chú thích `# ccba:allow-raw-model` tại chuỗi mô hình `"gemini-38-flash"` để đáp ứng quy chuẩn quét mã tĩnh `check_cleanliness.py`.

---

## 5. Kết Luận

Kế hoạch Triển khai Kỹ thuật V2 hoàn toàn sẵn sàng cho giai đoạn lập trình. Tiến hành bắt tay vào hiện thực mã nguồn và chạy toàn diện bộ kiểm thử `python -m ccba_harness verify-patch`.
