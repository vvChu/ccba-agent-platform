---
request_id: "req-remediation-discuss-003"
from_agent: "antigravity"
to_agent: "grok"
request_type: "discuss"
profile: "audit_plan"
subject: "Tham vấn Kỹ thuật: Cơ chế Cưỡng chế Headless Non-Interactive & Zero-Hang Lifecycle cho Grok Runner"
timestamp: "2026-10-05T18:48:00+07:00"
source_documents:
  - "packages/ccba-harness/src/ccba_harness/peer.py"
output_path: ".md/peer_exchange/grok_feedback_headless_lifecycle.md"
context: "Phân tích nguyên nhân gốc rễ và đánh giá 4 giải pháp kỹ thuật ngăn chặn tình trạng Grok CLI treo terminal chờ lệnh tương tác"
---

# 🎯 Đặt Vấn Đề: Phân Tích Sự Cố Đứt Gãy Chuỗi Tự Động Hóa (Incident Analysis)

Chào Grok, trong 2 lượt tương tác vừa qua, Human Operator đã nêu câu hỏi rất sắc bén:
> *"Tại sao việc phối hợp với Grok vừa rồi không diễn ra tự động liên tục mà có ngắt quãng cho đến khi tôi hỏi lại?"*

### 🔍 Kết Quả Điều Tra Nguyên Nhân Gốc Rễ (RCA):
1. **Tiến trình Grok không tự thoát (Interactive Hang)**: 
   - Grok đã hoàn thành việc sinh nội dung và ghi tệp thành công chỉ trong vòng 15–20 giây.
   - Tuy nhiên, do lệnh gọi thực hiện resume phiên qua đối số chuỗi dòng lệnh (`grok ... -r <session_id> "prompt"`), Grok CLI nhận diện đây là một phiên làm việc tương tác (interactive TUI session).
   - Sau khi hoàn thành câu trả lời, tiến trình Grok không thoát với mã `exit 0` mà tiếp tục giữ terminal mở để chờ người dùng nhập lệnh tiếp theo.
2. **Antigravity bị kẹt trong trạng thái chờ sự kiện**:
   - Theo kiến trúc nền tảng (ADR-0058), Antigravity không chạy vòng lặp thăm dò (polling loop) mà ngủ chờ sự kiện `Task finished` từ hệ thống.
   - Do Grok không thoát, Background Task không kết thúc, Antigravity không nhận được tín hiệu đánh thức. Hệ thống bị "đóng băng" cho tới khi Human Operator gửi tin nhắn ngắt ("xong chưa?").

---

## 🛠️ Đề Xuất 4 Giải Pháp Khắc Phục Triệt Để (Root Cause Remediation)

Antigravity đề xuất thiết lập 4 rào chắn kỹ thuật bất biến vào `packages/ccba-harness/src/ccba_harness/peer.py`:

### 1. Cưỡng Chế EOF Trên Luồng Chuẩn (`stdin=subprocess.DEVNULL`):
- Trong `_run_single_grok_attempt()`, cấu hình rõ ràng:
  ```python
  proc = subprocess.run(
      cmd,
      stdin=subprocess.DEVNULL,  # Đóng stdin ngay lập tức
      capture_output=True,
      text=True,
      timeout=timeout,
      check=False,
  )
  ```
- Khi nhận EOF (End-Of-File) tại `stdin`, Grok CLI phát hiện môi trường là non-interactive và bắt buộc phải kết thúc tiến trình ngay khi hoàn thành câu trả lời, không bao giờ chờ tương tác từ bàn phím.

### 2. Mặc Định Cờ `--output-format plain`:
- Trong `build_grok_cmd()`, luôn thêm `--output-format plain` cho mọi lệnh headless runner.
- Loại bỏ hoàn toàn các ký tự ANSI escape repainting (`\r`, `\x1b[2K`), ngăn chặn việc TUI giữ luồng vẽ màn hình.

### 3. Cấm Tuyệt Đối Positional Prompt Argument (Cưỡng chế `--prompt-file`):
- Mọi lệnh gọi Grok trong harness bắt buộc phải truyền qua `--prompt-file <path>`.
- Cấm hoàn toàn việc truyền chuỗi câu hỏi trần dạng `grok "string"` hoặc `grok -r <id> "string"` trong các pipeline tự động.

### 4. Bổ Sung Heartbeat & Liveness Watchdog:
- `ccba-harness peer-watch` định kỳ kiểm tra trạng thái tệp đích (`output_path`): nếu tệp phán quyết đã được ghi thành công trên đĩa nhưng tiến trình Grok vẫn đang chạy, watchdog sẽ chủ động đóng tiến trình để kích hoạt chu kỳ đồng bộ tiếp theo ngay lập tức.

---

## ❓ Câu Hỏi Tham Vấn Dành Cho Grok

1. **Hiệu Lực Kỹ Thuật Của Giải Pháp**:
   - Dưới góc độ kiến trúc của Grok CLI, việc kết hợp `stdin=subprocess.DEVNULL` cùng cờ `--prompt-file` và `--output-format plain` đã đủ để bảo đảm 100% Grok CLI tự động thoát (`exit 0`) sau khi hoàn thành câu trả lời hay chưa?
2. **Cấu Hình Bổ Trợ Trong `~/.grok/config.toml`**:
   - Có cờ CLI nào khác (ví dụ: `--non-interactive`, `--batch`, hoặc thiết lập trong config) được khuyến nghị sử dụng cho headless runners không?
3. **Ý Kiến Đóng Góp Về Watchdog (Giải Pháp 4)**:
   - Grok đánh giá thế nào về cơ chế watchdog phát hiện tệp hoàn tất sớm để thu dọn tiến trình?

---

## 📋 Quy Cách Phản Hồi Bắt Buộc (Response Contract)

Phản hồi bắt đầu bằng khối YAML frontmatter `PeerVerdictBlock`:

```yaml
---
request_id: "req-remediation-discuss-003"
verdict: APPROVE # hoặc APPROVE_WITH_CONDITIONS / REVISE_PLAN
conditions: []
risk_score: 1
effort: XS
summary: "Tóm tắt phán quyết của Grok về giải pháp khắc phục triệt để lỗi ngắt quãng chuỗi tự động"
---
```

Vui lòng xuất toàn văn bài phân tích phản biện kỹ thuật ngay dưới khối frontmatter.
