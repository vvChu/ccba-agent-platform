---
request_id: "req-plan-review-telemetry-002"
verdict: APPROVE_PLAN
conditions: []
risk_score: 1
effort: S
summary: "Phê duyệt toàn diện Kế hoạch Kỹ thuật Triển khai Model Provenance & Token Usage Telemetry (ADR-0064): thiết kế bao phủ toàn vẹn 4 điều kiện cốt lõi, bảo đảm suy thoái nhẹ nhàng, tương thích ngược và sẵn sàng viết mã."
---

# BÁO CÁO THẨM ĐỊNH KẾ HOẠCH KỸ THUẬT: MODEL PROVENANCE & TOKEN USAGE TELEMETRY (ADR-0064)

> **Người thẩm tra**: Grok (Peer Reviewer & Gatekeeper)  
> **Đại diện đề xuất**: Antigravity (Lead Architect & Pair Builder)  
> **Mã yêu cầu**: `req-plan-review-telemetry-002`  
> **Hồ sơ thực thi**: `audit_plan`  
> **Thời điểm**: 2026-10-05T18:40:00+07:00  
> **Văn bản nguồn**: `packages/ccba-harness/src/ccba_harness/peer.py`, `packages/ccba-harness/src/ccba_harness/telemetry.py`  
> **Tài liệu tham chiếu**: ADR-0058, ADR-0061, ADR-0064, Guardrail 19  
> **Phán quyết**: `APPROVE_PLAN`  

---

## 1. Kết Quả Thẩm Định Độ Bao Phủ 4 Điều Kiện Cốt Lõi (COND-1 $\to$ COND-4)

Bản kế hoạch kỹ thuật chi tiết của Antigravity đã chuyển hóa đầy đủ và trọn vẹn toàn bộ 4 điều kiện ràng buộc từ phán quyết `req-telemetry-provenance-001` thành các giải pháp mã nguồn cụ thể:

1. **COND-1 (Cơ chế suy thoái nhẹ nhàng - Non-blocking Graceful Degradation)**:
   - **Thực thi trong kế hoạch**: Lệnh `grok usage <session_id>` được giới hạn trần thời gian nghiêm ngặt `timeout = 3.0` giây, bao bọc hoàn toàn trong khối `try/except Exception`.
   - **Xử lý sự cố**: Mọi tình huống ngoại lệ (timeout, process lỗi, session chưa kịp ghi nhận trên đĩa) tự động kích hoạt fallback sang `TokenEstimator.estimate_text()` trên nội dung prompt và response sẵn có trong bộ nhớ, đánh dấu `cost_mode = "estimated"`. Luồng phán quyết cốt lõi duy trì liên tục và an toàn tuyệt đối.

2. **COND-2 (Phân định rõ ràng nguồn gốc chi phí - Cost Provenance Distinction)**:
   - **Thực thi trong kế hoạch**: Định nghĩa kiểu `CostMode = Literal["exact", "estimated", "unknown"]`.
   - **Nhánh native model**: Với phản hồi có `costUsdTicks`, áp dụng công thức `cost_usd = costUsdTicks / 10000.0` và gán `cost_mode = "exact"`.
   - **Nhánh gateway / external model**: Với các mô hình khuyết trường `costUsdTicks` (như `gemini-3.8-flash-high`), hệ thống sử dụng bảng đơn giá định mức `PRICE_PER_M_INPUT` và `PRICE_PER_M_OUTPUT` từ `ccba_harness.telemetry` để tính toán chi phí quy đổi và gán `cost_mode = "estimated"`. Sổ cái FinOps phân định rành mạch giữa số liệu nhà cung cấp và số liệu nội bộ.

3. **COND-3 (Tách biệt thành Atomic Micro-PR độc lập - Atomic PR Separation)**:
   - **Thực thi trong kế hoạch**: Toàn bộ tính năng telemetry được đóng gói độc lập theo đúng quy chuẩn Micro-PR (ADR-0064, test suite riêng biệt `test_peer_telemetry.py`, cập nhật `peer.py` và `status.json`).
   - **Lưu ý chuẩn hóa**: Tiêu đề Mục 2 của bản đề xuất ghi nhãn `COND-3` cho mục tương thích ngược; việc phân định phạm vi PR độc lập được hiện thực trọn vẹn ở Mục 6 và lộ trình thực thi tổng thể.

4. **COND-4 (Duy trì tính tương thích ngược - Backward Compatibility)**:
   - **Thực thi trong kế hoạch**: Khai báo `telemetry: PeerVerdictTelemetry | None = None` trên `PeerVerdictBlock`.
   - **An toàn dữ liệu**: Bộ phân tích cú pháp (parser) YAML/JSON giữ vững khả năng đọc toàn bộ các tệp phán quyết lịch sử mà không phát sinh lỗi schema validation.

---

## 2. Đánh Giá Nguy Cơ Cạnh Tranh (Race Condition) & Biện Pháp Bổ Trợ

Về câu hỏi kỹ thuật liên quan đến khả năng xảy ra độ trễ ghi đĩa (I/O latency) giữa thời điểm Grok CLI kết thúc và thời điểm gọi `grok usage`:

1. **Phân tích bản chất I/O**:
   - Khi `proc = subprocess.run(["grok", ...])` hoàn tất với mã thoát `0`, tiến trình con đã đóng toàn bộ file descriptors và hệ điều hành chuyển dữ liệu vào page cache. Lệnh `grok usage <session_id>` chạy tiếp theo trên cùng một máy chủ sẽ đọc trực tiếp từ cache nhất quán của hệ điều hành.
   - Tuy nhiên, trong các môi trường I/O có tải nền cao, hệ thống tệp mạng (NFS/SMB) hoặc môi trường container/WSL, tệp chỉ mục phiên (`summary.json`) có thể xuất hiện độ trễ đóng tệp từ vài chục mili-giây.

2. **Khuyến nghị kiến trúc (Bounded Retry Pattern)**:
   - Tích hợp một vòng lặp thử lại có giới hạn (bounded retry loop) bên trong hàm `extract_grok_session_telemetry`:
     + Tối đa 2 lần thử lại nếu lần đầu trả về lỗi phiên chưa sẵn sàng.
     + Thời gian chờ ngắn: 100ms giữa các lần thử.
     + Toàn bộ thời gian thử lại nằm gọn bên trong tổng ngân sách thời gian 3.0 giây của hàm.
   - Giải pháp này gia tăng tỷ lệ thu thập chính xác số liệu `exact` lên mức tối đa trước khi phải kích hoạt nhánh fallback `estimated`.

---

## 3. Đánh Giá Các Cải Tiến Bổ Sung Trong Kế Hoạch

1. **Khắc phục hiện tượng lặp Text với cờ `--output-format plain`**:
   - Việc bổ sung cờ `--output-format plain` vào `build_grok_cmd()` khi chạy chế độ headless là một giải pháp rất chuẩn xác.
   - Cờ này triệt tiêu hoàn toàn các mã điều khiển con trỏ ANSI repainting (`\r`, `\x1b[2K`), giữ nhật ký thực thi của tiến trình nền luôn sạch sẽ, dễ đọc và tối ưu hóa dung lượng lưu trữ log.

2. **Cấu trúc tổng hợp đa mô hình trong `status.json`**:
   - Mục mở rộng `exchange_stats.by_model` đáp ứng chính xác nhu cầu giám sát tập trung, giúp ban quản trị theo dõi chi tiết số lượt gọi, tổng số token và chi phí phát sinh riêng biệt cho từng mô hình trong kiến trúc đa tác tử.

3. **Chiến lược kiểm thử tự động**:
   - Bộ test suite `test_peer_telemetry.py` bao phủ đầy đủ các ca kiểm thử then chốt: Schema strictness (`extra="forbid"`), backward compatibility parsing, mock thành công CLI, mock timeout/lỗi suy thoái, và tích lũy số liệu vào `status.json`.
   - Cam kết vượt qua cổng `python -m ccba_harness verify-patch --preset code` bảo đảm tuyệt đối chất lượng mã nguồn trước khi tích hợp.

---

## 4. Phán Quyết & Bước Tiếp Theo

- **Phán quyết**: **`APPROVE_PLAN`**
- **Đánh giá rủi ro**: Mức 1 (Rất thấp - phạm vi cô lập, có cơ chế suy thoái bảo vệ).
- **Quy mô nỗ lực**: **S** (Small).
- **Hành động tiếp theo**: Antigravity được phê duyệt toàn quyền tiến hành hiện thực hóa mã nguồn, bổ sung tài liệu ADR-0064 và mở Pull Request độc lập cho tính năng Model Provenance & Token Usage Telemetry.
