---
request_id: req-code-review-pr482-001
verdict: APPROVE_WITH_CONDITIONS
conditions:
- id: COND-01
  description: Bổ sung cơ chế thu thập lỗi trong khối rollback thay vì âm thầm bỏ
    qua bằng pass để cảnh báo trạng thái tệp bị hỏng.
  blocking: true
- id: COND-02
  description: Bổ sung kiểm tra target_file.is_file() tại Phase 1 để trả về lỗi định
    dạng rõ ràng khi gặp thư mục.
  blocking: true
- id: COND-03
  description: Xem xét bảo tồn quyền thực thi POSIX (stat.st_mode) trong atomic_write_text
    khi thao tác trên các tệp script có cờ execute.
  blocking: true
risk_score: 2
effort: S
summary: 'PR #482 hoàn thiện xuất sắc mô hình 2-Phase Commit với transactional rollback,
  kiểm soát bảo mật đường dẫn và giao diện CLI chuẩn Unix. Cần xử lý triệt để việc
  thông báo lỗi rollback và kiểm tra loại tệp để đạt độ vững chắc tuyệt đối.'
telemetry:
  session_id: bd03f5a9-3d3b-47d4-97ae-f5f0ecc47fe6
  primary_model: gemini-3.8-flash-high
  input_tokens: 239875
  output_tokens: 2981
  reasoning_tokens: 7695
  cached_read_tokens: 171288
  total_tokens: 242856
  model_calls: 10
  turn_count: 1
  cost_usd: 0.3147
  cost_mode: estimated
  duration_seconds: 64.02
---
# Báo Cáo Thẩm Định Kỹ Thuật (Peer Code Review) — PR #482

**Đối tượng thẩm định:** Pull Request #482 (`packages/ccba-harness/src/`)  
**Hồ sơ thực thi:** `code_review`  
**Căn cứ đối soát:** 10 Bugbot Invariants (`.github/bugbot-rules.md`), ADR-0058, ADR-0063, ADR-0064.

---

## 1. Kết Quả Đánh Giá Tổng Quan

PR #482 cung cấp cơ chế triển khai bản vá neo (anchor patch) nguyên tử cho giao thức Level-2 Peer Delegation. Kiến trúc chia tách rõ ràng thành hai pha: Pha 1 kiểm tra điều kiện tiên quyết (Fail-Fast Validation) và Pha 2 thực thi giao dịch có khả năng hoàn nguyên (Transactional Rollback).

| Tiêu chí | Đánh giá | Trạng thái |
| :--- | :--- | :--- |
| **Toàn vẹn giao dịch (ACID)** | Cơ chế snapshot bộ nhớ kết hợp `atomic_write_text` khôi phục nội dung gốc khi ghi thất bại | **Đạt (Cần gia cố)** |
| **An toàn hệ thống tệp** | Chặn Path Traversal bằng `is_relative_to`, chặn duplicate target paths | **Đạt** |
| **Chuẩn hóa đa nền tảng** | Chuẩn hóa CRLF sang LF linh hoạt, hash SHA-256 trên raw bytes thực tế | **Đạt** |
| **Xử lý ngoại lệ & CLI** | Hỗ trợ đầy đủ cờ chuẩn Unix (`-f -`, `--json`, `--quiet`, `--backup`, `--dry-run`) | **Đạt** |
| **Tuân thủ 10 Bugbot Invariants** | Tái sử dụng Seam chuẩn, cô lập machine-state, đầy đủ test parity | **Đạt** |

---

## 2. Phân Tích Kỹ Thuật Chi Tiết Theo 5 Trọng Tâm

### 2.1. Toàn Vẹn & Khôi Phục Giao Dịch (Transactional Rollback)
* **Điểm mạnh:**
  * Thuật toán Phase 1 tải toàn bộ nội dung tệp vào danh sách bộ nhớ `prepared_writes: list[tuple[Path, str, str]]` trước khi thực hiện bất kỳ thao tác ghi nào lên đĩa.
  * Khi xuất hiện lỗi ở Phase 2, vòng lặp `for failed_file, old_content in written_backups.items()` tự động ghi đè lại nội dung gốc của các tệp đã bị sửa đổi trước đó.
* **Rủi ro tiềm ẩn (Điều kiện 1):**
  * Tại khối rollback:
    ```python
    for failed_file, old_content in written_backups.items():
        try:
            atomic_write_text(failed_file, old_content)
        except Exception:
            pass
    ```
    Việc sử dụng `pass` trong khối `except Exception` triệt tiêu thông tin khi đĩa đầy hoặc lỗi phân quyền phát sinh ngay trong lúc rollback. Hệ thống cần ghi nhận danh sách các tệp rollback thất bại vào một mảng `rollback_errors` và đưa thông tin này vào thông báo lỗi ngoại lệ cuối cùng để người vận hành nhận diện chính xác trạng thái tệp trên đĩa.
  * Khi bật cờ `--backup`, các tệp `.bak` của những tệp đã ghi trước thời điểm giao dịch bị huỷ vẫn tồn tại trên đĩa. Đây là bản lưu nội dung gốc nên an toàn cho dữ liệu, nhưng có thể bổ sung ghi chú dọn dẹp nếu muốn giao dịch hoàn toàn vô vết.

### 2.2. An Toàn Hệ Thống Tệp (Filesystem & Path Traversal)
* **Điểm mạnh:**
  * Cơ chế bảo vệ `not target_file.is_relative_to(root_resolved)` ngăn chặn triệt để các kỹ thuật vượt cấp thư mục (`../../`) cũng như các đường dẫn tuyệt đối trỏ ra ngoài không gian làm việc.
  * Cấu trúc `target_files_seen: set[Path]` loại trừ hoàn toàn nguy cơ một tệp đích bị khai báo nhiều lần trong cùng một payload dẫn đến xung đột ghi đè không xác định.
* **Rủi ro tiềm ẩn (Điều kiện 2):**
  * Mã nguồn hiện tại kiểm tra `if not target_file.exists(): raise ValueError(...)`. Nếu đường dẫn trong payload trỏ tới một thư mục (ví dụ `.` hoặc thư mục con hợp lệ nằm trong `root_resolved`), lệnh `target_file.read_bytes()` sẽ phát sinh `IsADirectoryError` thay vì trả về thông điệp lỗi nghiệp vụ rõ ràng. Bổ sung `if not target_file.is_file(): raise ValueError(f"Target path is not a regular file: {file_patch.path}")` sẽ tăng tính nhất quán cho Pha 1.

### 2.3. Chuẩn Hóa Đa Nền Tảng (Cross-OS & CRLF)
* **Điểm mạnh:**
  * Việc băm SHA-256 thực hiện trên `raw_bytes` trước khi chuẩn hóa chuỗi, bảo đảm tính toàn vẹn chữ ký mật mã theo chuẩn Git blob và ADR-0059.
  * Việc áp dụng `.replace("\r\n", "\n")` đồng bộ cho cả `text`, `rep.old`, và `rep.new` giải quyết dứt điểm sự sai lệch về ký tự ngắt dòng giữa môi trường Windows và Linux/macOS.
* **Lưu ý kỹ thuật:**
  * Tệp sau khi áp bản vá sẽ được ghi xuống đĩa với ký tự dòng LF. Đây là chuẩn mực tối ưu cho các kho mã nguồn Git monorepo.

### 2.4. Xử Lý Lỗi (Exception Handling) & AST Hygene
* **Điểm mạnh:**
  * Các chuỗi định danh mô hình nội bộ trong `PEER_EXECUTION_PROFILES` (`code_review`, `arch_audit`) được đánh dấu chú thích `# ccba:allow-raw-model` chuẩn quy định AST Span Inspection (Rule-03).
  * Hàm `extract_frontmatter` bổ sung xử lý bóc tách markdown code fence (`re.sub(r"^```[a-zA-Z0-9_-]*\r?\n", "", content)`), hỗ trợ dung sai cao khi LLM phản hồi khối YAML bọc trong cú pháp code block.
* **Lưu ý kiểm tra:**
  * Khi frontmatter được bọc hoàn toàn trong cặp fence ````yaml ... ````, phần thân tài liệu `body` có thể giữ lại ký tự đóng fence ```` ở đầu dòng đầu tiên. Đây là trường hợp viền nhỏ, có thể xử lý triệt để bằng cách cắt bỏ fence đóng nếu có.

### 2.5. Giao Diện CLI & Usability
* **Điểm mạnh:**
  * Giao diện CLI hỗ trợ đầy đủ các cờ thiết yếu: `--patch-file` / `-f`, `--root` / `-r`, `--dry-run`, `--backup`, `--quiet` / `-q`, và `--json`.
  * Hỗ trợ `-f -` đọc dữ liệu từ `sys.stdin`, cho phép kết nối đường ống lệnh Unix (`cat patch.md | ccba-harness apply-anchor-patch -f -`).
  * Trả về định dạng JSON có cấu trúc khi có cờ `--json` cho cả luồng thành công (`DRY_RUN_OK`, `APPLIED`) lẫn luồng thất bại (`ERROR`).
  * Đăng ký alias đầy đủ (`apply-anchor-patch`, `peer-apply`, `apply-patch`) tại cả bộ phân tích ngữ pháp chính và bộ điều phối nhanh (Fast-Path dispatch).

---

## 3. Đối Chiếu 10 Bugbot Invariants (.github/bugbot-rules.md)

1. **`[RULE-01] SEAM_REUSE`**: Đạt. Tái sử dụng trực tiếp Seam `atomic_write_text` và Pydantic schema `AnchorPatchPayload`.
2. **`[RULE-02] DECOUPLED_CONNECTION`**: Đạt. Module nằm trong tầng công cụ `ccba-harness`, độc lập với tầng kết nối API.
3. **`[RULE-03] AST_SPAN_INSPECTION`**: Đạt. Chú thích `# ccba:allow-raw-model` được đặt chính xác trên cùng dòng khai báo chuỗi model.
4. **`[RULE-04] MULTI_KEY_SORT`**: Đạt. Không có thao tác sắp xếp đa tiêu chí gây mất tính đơn định.
5. **`[RULE-05] INODE_INVARIANCE`**: Đạt. Danh sách tệp được xử lý tuần tự theo đúng thứ tự khai báo trong payload, kết hợp `target_files_seen` ngăn ngừa trùng lặp.
6. **`[RULE-06] POSIX_PERMISSIONS`**: Cần lưu ý (Điều kiện 3). Hàm `atomic_write_text` tạo tệp tạm rồi hoán đổi qua `temp_file.replace(target)`. Thao tác này có thể thiết lập lại quyền tệp theo umask mặc định, làm mất cờ thực thi (`stat.S_IXUSR`) nếu tệp đích là script thực thi. Cần xem xét bảo tồn thuộc tính `st_mode` trước khi hoán đổi.
7. **`[RULE-07] MACHINE_STATE_DECOUPLING`**: Đạt. Sử dụng `Path.cwd()` và tham số `--root`, không chứa đường dẫn máy cục bộ cứng.
8. **`[RULE-08] SECRETS_MASKARA`**: Đạt. Không có khóa bí mật, token hay mật khẩu trong mã nguồn.
9. **`[RULE-09] VERIFIER_TEST_PARITY`**: Đạt. Bộ kiểm thử trong `test_peer.py` đã bao phủ toàn diện các ca kiểm thử: `dry_run`, `duplicate_target_file`, `crlf_normalization`, `transactional_rollback`, `backup`, và các luồng CLI stdin/JSON.
10. **`[RULE-10] ATOMIC_MICRO_PR`**: Đạt. Kích thước thay đổi tập trung trong phạm vi micro-PR (~250 dòng mã nguồn chức năng).

---

## 4. Kết Luận & Khuyến Nghị

PR #482 đạt chất lượng kỹ thuật cao, đáp ứng toàn diện yêu cầu kiến trúc Level-2 Peer Delegation. Sau khi hoàn thiện 2 điều kiện gia cố (thu thập lỗi rollback và kiểm tra tệp tin thông thường), PR đủ điều kiện hợp nhất vào nhánh chính.
