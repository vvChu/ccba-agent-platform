# Cẩm Nang Bảo Trì & Khắc Phục Sai Lệch Kiểm Định (Verification Drift Guide)

Tài liệu hướng dẫn phát hiện, phân loại và khắc phục sai lệch (drift) giữa mã nguồn ứng dụng và bộ kỹ năng kiểm định tự động (`verify-<app>`), tuân thủ chuẩn mực **Pstack Phase 2 & ADR-0044**.

---

## 1. Nguyên Tắc Cốt Lõi: Phân Định Hồi Quy vs. Lệch Hợp Đồng (COND-01)

Khi bài kiểm định trong `verify-<app>` thất bại (exit code khác 0), AI Agent **tuyệt đối không được vội vã sửa code kiểm thử trong `harness/` để biến test thành màu xanh (Test Tampering / False Green)**.

Trước khi tiến hành bất kỳ chỉnh sửa nào, Agent bắt buộc phải thực hiện bước **Kiểm Tra Nguồn Gốc Thay Đổi (Pre-Remediation Provenance Check)**:

```mermaid
flowchart TD
    A[verify-app thất bại] --> B[Pre-Remediation Provenance Check]
    B --> C{Thay đổi là do đâu?}
    C -->|Chủ đích thiết kế\nĐổi route, port, schema| D["Cập nhật harness/\nhoặc features/INDEX.md (Drift Fix)"]
    C -->|Lỗi hồi quy ngoài ý muốn\nApp crash, logic hỏng, regression| E["GIỮ NGUYÊN harness/\nBáo cáo & Sửa mã nguồn ứng dụng"]
```

1. **Trường hợp 1: Sai lệch hợp đồng chủ đích (Intentional Contract Drift)**
   - Ứng dụng chủ động nâng cấp: đổi route `/api/v1/health` $\to$ `/api/v2/health`, đổi port mặc định `8000` $\to$ `8080`, hoặc thêm trường bắt buộc vào response JSON theo PR/Ticket đã duyệt.
   - **Hành động:** Tiến hành cập nhật kịch bản kiểm thử trong `harness/` và đồng bộ lại `features/INDEX.md`.

2. **Trường hợp 2: Lỗi hồi quy ngoài ý muốn (Unintended Application Regression)**
   - Ứng dụng bị crash, trả về mã 500, đứt gãy kết nối cơ sở dữ liệu, hoặc logic nghiệp vụ trả về kết quả sai do commit mã mới.
   - **Hành động:** **CẤM SỬA `harness/`**. Giữ nguyên bài test, phân tích nguyên nhân gốc (Root Cause) và yêu cầu sửa mã nguồn ứng dụng để phục hồi tính tương thích.

### 1.1. Bốn Trạng Thái Kết Quả Bảo Trì (`in_sync`, `updated`, `bug`, `blocked`) & Chốt Chặn `sync_commit` + Semantic Mutation Proof (Pstack v0.15.28)

Khi mã nguồn thay đổi mà bộ kiểm định không cập nhật, bài kiểm thử có thể tiếp tục trả về PASS giả tạo vì chỉ kiểm tra mô tả cũ đã lỗi thời (**Pass on Stale Description**). Để triệt tiêu rủi ro này, mỗi lượt chạy bảo trì bắt buộc phân loại kết quả vào đúng 1 trong 4 trạng thái chuẩn:

1. **`in_sync`**: Không có thay đổi nào từ `sync_commit` đến `HEAD` làm thay đổi hành vi/hợp đồng mà bộ kiểm định mô tả, và bài kiểm định PASS. Được phép nâng `sync_commit` lên commit hiện tại.
2. **`updated`**: Mã nguồn thay đổi có chủ đích (có bằng chứng trong commit message, docstring, PR hoặc ADR), kịch bản trong `harness/` đã được cập nhật từ chính mã nguồn mới, vượt qua **Semantic Mutation Proof** và PASS. Được phép nâng `sync_commit`.
3. **`bug`**: Bộ kiểm định phản ánh đúng hợp đồng hiện hành nhưng mã nguồn vi phạm tính chất cam kết. Tuyệt đối CẤM làm yếu bài kiểm định hoặc nâng `sync_commit`; báo cáo chuỗi bước tái lập lỗi (*counterexample*) và commit gây lỗi.
4. **`blocked`**: Không thể thực thi hoặc đồng bộ bộ kiểm định do rào cản môi trường/hạ tầng. Nêu rõ nguyên nhân và **tuyệt đối CẤM dịch chuyển `sync_commit`**.

#### Quy Trình Hoàn Nguyên Tất Định Cho Semantic Mutation Proof (`COND-01` & `COND-02`)
Để chứng minh bộ kiểm định mới hoặc vừa cập nhật (`updated`) thực sự có khả năng bắt lỗi mà không làm ô nhiễm cây mã nguồn:
1. **Tiền kiểm trạng thái sạch (`COND-01`)**: Chỉ thực hiện đột biến khi working tree hoàn toàn sạch:
   ```bash
   git diff --quiet && git diff --cached --quiet
   ```
2. **Đột biến ngữ nghĩa & Thu thập phản chứng (`COND-02`)**: Thực hiện một **đột biến ngữ nghĩa (Semantic Mutation)** tác động trực tiếp vào logic hợp đồng, điều kiện rẽ nhánh hoặc giá trị biên trên mã nguồn thực (ví dụ: đổi toán tử `>` thành `>=`, đảo ngược cờ boolean, hoặc bỏ qua một bước ghi trạng thái; **tuyệt đối cấm** chèn lỗi cú pháp `SyntaxError` hoặc đặt lệnh `raise` thô ở đầu hàm). Chạy `verify-<app>` và lưu lại nhật ký lỗi phản chứng (*counterexample failure log*) để chứng minh bộ kiểm định bắt trúng lỗi.
3. **Hoàn nguyên tự động & Hậu kiểm nguyên vẹn (`COND-01`)**: Ngay sau khi thu thập phản chứng, phục hồi mã nguồn và xác nhận trạng thái sạch trước khi nghiệm thu:
   ```bash
   git checkout -- <mutated_files>
   git diff --quiet <mutated_files> && git diff --cached --quiet <mutated_files>
   ```

---

## 2. Bốn Dạng Drift Phổ Biến & Quy Trình Khắc Phục

### 2.1. Endpoint & Command Drift (Sai Lệch Lệnh & Cổng Dịch Vụ)
- **Dấu hiệu:** `Clean-Slate Pre-flight` hoặc `Deterministic Health Barrier` báo lỗi Connection Refused, Port Conflict, hoặc Unknown CLI flag.
- **Khắc phục:**
  - Kiểm tra lệnh khởi chạy server mới trong tài liệu/cấu hình của ứng dụng.
  - Cập nhật lệnh gọi subprocess trong `harness/` để khớp với CLI cờ mới.
  - Điều chỉnh cổng thăm dò readiness probe.

### 2.2. Schema & Contract Drift (Sai Lệch Lược Đồ Dữ Liệu)
- **Dấu hiệu:** Server khởi động thành công, probe PASS, nhưng các bài assert trong `Evidence-Capture Test Suite` bị văng `KeyError`, `ValidationError`, hoặc sai kiểu dữ liệu.
- **Khắc phục:**
  - So sánh schema JSON thực tế nhận được qua `curl` / HTTP client với schema mong đợi trong `features/INDEX.md`.
  - Cập nhật assertions trong harness nếu schema mới là chuẩn thiết kế chính thức.

### 2.3. Readiness & Timing Drift (Sai Lệch Thời Gian Sẵn Sàng)
- **Dấu hiệu:** Server cần nhiều thời gian hơn để nạp mô hình AI, kết nối cơ sở dữ liệu, hoặc khởi tạo bộ nhớ cache, dẫn đến Health Barrier báo timeout.
- **Khắc phục:**
  - Tuyệt đối KHÔNG chèn `time.sleep(N)` tùy tiện.
  - Tăng trần thời gian chờ có giới hạn xác định (`max_wait_seconds: 30` hoặc `60`), kết hợp giảm chu kỳ thăm dò (poll interval `250ms`).

### 2.4. Process Tree Drift (Tiến Trình Nền Phức Hợp)
- **Dấu hiệu:** Sau khi kết thúc kiểm thử, còn sót lại các tiến trình con mồ côi (Celery workers, uvicorn reloaders, node daemons) chiếm dụng RAM hoặc port.
- **Khắc phục:**
  - Củng cố cơ chế dọn dẹp theo nhóm tiến trình (Process Group):
    - **Windows:** Bắt buộc dùng `taskkill /F /T /PID <pid>`.
    - **POSIX:** Bắt buộc dùng `os.killpg(os.getpgid(proc.pid), signal.SIGTERM)` kèm fallback `SIGKILL`.

---

## 3. Quy Tắc Vệ Sinh Spoke (ADR-0044 Spoke Cleanliness Rule)

Khi bảo trì và sửa lỗi cho kỹ năng `verify-<app>` tại Spoke repository:
1. **Cô Lập Triệt Để:** Toàn bộ các script sửa lỗi, file helper, test fixtures bắt buộc nằm gọn trong thư mục `.agents/skills/verify-<app>/harness/`.
2. **Cấm Ô Nhiễm Thư Mục Gốc:** TUYỆT ĐỐI CẤM tạo thêm script phụ tại thư mục gốc `scripts/` của Spoke repo. Việc tạo script rác ở `scripts/` sẽ vi phạm trần 15 kịch bản theo ADR-0044 và bị `check_spoke_cleanliness.py` chặn cứng tại CI.

---

*Tài liệu tham chiếu thuộc bộ chuẩn mực Pstack Phase 2 & Phase 3 — CCBA Agent Services Platform.*
