---
request_id: "req-remediation-discuss-003"
verdict: APPROVE_WITH_CONDITIONS
conditions:
  - id: cond-1-popen-lifecycle
    description: "Chuyển _run_single_grok_attempt từ subprocess.run() blocking sang subprocess.Popen() có vòng lặp polling để Watchdog có thể can thiệp thu dọn tiến trình theo thời gian thực."
    blocking: true
  - id: cond-2-strict-prompt-file
    description: "Cưỡng chế 100% lệnh gọi Grok Runner phải đi qua cờ --prompt-file trong build_grok_cmd(), cấm truyền prompt dạng chuỗi đối số vị trí (kể cả khi tiếp tục phiên với -r)."
    blocking: true
  - id: cond-3-verdict-atomic-validation
    description: "Watchdog chỉ kích hoạt thu dọn tiến trình khi tệp đích output_path đã được ghi hoàn tất trên đĩa và vượt qua hàm parse_verdict_from_md() hợp lệ."
    blocking: true
risk_score: 1
effort: XS
summary: "Chấp thuận đề xuất 4 giải pháp xử lý triệt để sự cố Grok Runner treo terminal với 3 điều kiện bổ trợ: chuyển Popen cho Watchdog, cưỡng chế tuyệt đối --prompt-file và thẩm định tính toàn vẹn của tệp phán duyệt trước khi đóng tiến trình."
---

# 🏛️ PHÁN BIỆN VÀ THAM VẤN KỸ THUẬT: CƠ CHẾ CƯỠNG CHẾ HEADLESS & ZERO-HANG CHO GROK RUNNER

> **Bên phản biện**: Grok AI Peer Auditor  
> **Bên yêu cầu**: Antigravity  
> **Mã tham vấn**: `req-remediation-discuss-003` (`discuss`)  
> **Trọng tâm**: Xử lý triệt để sự cố Grok CLI treo terminal chờ lệnh tương tác, khôi phục chuỗi tự động hóa liên tục  
> **Phán quyết**: `APPROVE_WITH_CONDITIONS` (Điểm rủi ro: 1/5 | Mức độ công việc: XS)

---

## 1. Xác Nhận Nguyên Nhân Gốc Rễ (RCA Confirmation)

Điều tra từ kiến trúc thực thi của Grok CLI (phiên bản `1.0.46` phân tích qua `grok --help` và tài liệu kiến trúc headless tại `~/.grok/docs/user-guide/14-headless-mode.md`) xác nhận:

1. **Quy ước tham số dòng lệnh của Grok CLI**:
   - Cú pháp chuẩn của CLI là: `grok [OPTIONS] [PROMPT] [COMMAND]`.
   - Tham số vị trí `[PROMPT]` được định nghĩa là *Initial prompt for the interactive session*. Khi truyền một chuỗi trần vị trí (ví dụ: `grok "abc"` hoặc `grok -r <id> "abc"`), Grok CLI luôn khởi tạo môi trường Terminal User Interface (TUI). Sau khi in câu trả lời, tiến trình giữ nguyên vòng lặp sự kiện giao diện (TUI event loop) để chờ người dùng gõ phím tiếp theo.
2. **Kích hoạt chế độ Headless Non-Interactive**:
   - Chế độ chạy ngầm tự động (headless) của Grok chỉ được kích hoạt khi cung cấp cờ `--prompt-file <path>` hoặc `-p / --single <prompt>`.
   - Khi ở chế độ headless, Grok thực thi vòng lặp công cụ (tool loop) đến khi hoàn tất hoặc chạm ngưỡng `--max-turns`, xuất kết quả ra luồng chuẩn (`stdout`), và tự động gọi `exit 0`.
   - Khi phiên tương tác vô tình được kích hoạt trong subprocess không có TTY chuẩn, Grok ghi toàn bộ chuỗi thoát ANSI repainting vào luồng xuất (như đã ghi nhận trong sự cố thực tế), gây đóng băng toàn bộ pipeline tự động hóa.

---

## 2. Đánh Giá Chi Tiết 4 Giải Pháp Kỹ Thuật

### Giải Pháp 1: Cưỡng chế EOF trên luồng chuẩn (`stdin=subprocess.DEVNULL`)
- **Hiệu lực**: **Rất cao (Bắt buộc)**.
- **Phân tích kỹ thuật**:
  - Khi đặt `stdin=subprocess.DEVNULL`, luồng đầu vào đóng ngay lập tức bằng tín hiệu EOF. Mọi thư viện hay tiến trình con (như git credential helper, subshell commands) đều bị tước bỏ khả năng dừng chờ input.
  - Tuy nhiên, `stdin=subprocess.DEVNULL` đóng vai trò là chốt chặn an toàn lớp dưới; nó cần đi kèm với chế độ headless để bảo đảm tiến trình không bị crash do lỗi đọc thiết bị TTY.

### Giải Pháp 2: Mặc định cờ `--output-format plain`
- **Hiệu lực**: **Cao**.
- **Phân tích kỹ thuật**:
  - Trong tài liệu headless mode, `--output-format plain` là chế độ xuất văn bản thô chuẩn xác, loại bỏ các ký tự điều khiển phân trang hoặc streaming JSON phức tạp.
  - Việc đưa `--output-format plain` vào danh sách tham số cố định trong `build_grok_cmd()` bảo đảm kết quả trả về luôn ở định dạng Markdown thuần, phục vụ bóc tách YAML frontmatter trơn tru qua `parse_verdict_from_md()`.

### Giải Pháp 3: Cấm tuyệt đối Positional Prompt Argument (Cưỡng chế `--prompt-file`)
- **Hiệu lực**: **Tuyệt đối (Chìa khóa gốc rễ)**.
- **Phân tích kỹ thuật**:
  - Đây là giải pháp giải quyết tận gốc nguyên nhân của sự cố. Bằng cách loại bỏ hoàn toàn việc truyền chuỗi vị trí và ép buộc mọi yêu cầu phải ghi ra file tạm rồi nạp qua `--prompt-file <path>`, Grok CLI luôn nhận diện cờ headless và thoát ngay sau khi hoàn thành lượt xử lý.
  - Quy tắc này áp dụng đồng nhất cho cả lượt tạo mới lẫn các lượt tiếp tục (`-r <session_id> --prompt-file <path>`).

### Giải Pháp 4: Bổ sung Heartbeat & Liveness Watchdog
- **Hiệu lực**: **Rất cao (Phòng vệ chiều sâu - Defense in Depth)**.
- **Phân tích kỹ thuật**:
  - Cơ chế Watchdog giám sát sự xuất hiện của tệp đích `output_path` là giải pháp hữu hiệu nhằm ngắt sớm các tiến trình bị trễ pha thu dọn tài nguyên.
  - Để Watchdog vận hành được, cấu trúc thực thi của `_run_single_grok_attempt()` cần được chuyển từ hàm chặn đồng bộ (`subprocess.run`) sang tiến trình không đồng bộ (`subprocess.Popen`).

---

## 3. Trả Lời Các Câu Hỏi Tham Vấn Kỹ Thuật

### Câu 1: Kết hợp `stdin=DEVNULL`, `--prompt-file` và `--output-format plain` đã đủ bảo đảm 100% tự động thoát?
**Trả lời**: **Đã đủ ở tầng Grok CLI**, với điều kiện đi kèm 2 cờ đã có trong `build_grok_cmd()`:
1. `--always-approve`: Triệt tiêu mọi hộp thoại xin quyền tương tác trên terminal đối với các công cụ đọc/ghi tệp.
2. `--no-subagents`: Ngăn chặn việc sinh các subagent nền có thể chạy vượt vòng đời của agent chính.

### Câu 2: Các cờ bổ trợ và cấu hình trong `~/.grok/config.toml`
Grok CLI không sử dụng cờ `--batch` riêng biệt vì cờ `--prompt-file` đã là cờ chuyên dụng để kích hoạt headless mode. Các thiết lập bổ trợ cần duy trì:
- **Cờ CLI**: Giữ vững `--max-turns <N>` cho từng profile để chặn đứng nguy cơ lặp vô hạn ở các tác vụ phức tạp.
- **Cấu hình `~/.grok/config.toml`**: Đảm bảo mục `[ui]` có `screen_mode = "minimal"` hoặc giữ cấu hình mặc định, không bật các chế độ cưỡng chế toàn màn hình.

### Câu 3: Đánh giá cơ chế Watchdog (Giải Pháp 4)
Cơ chế Watchdog là cần thiết để bảo vệ hệ thống trước mọi tình huống treo bất khả kháng. Khi cài đặt Watchdog, cần tuân thủ:
- Kiểm tra tính đầy đủ của tệp: Tệp trên đĩa phải chứa đầy đủ khối YAML `PeerVerdictBlock` hợp lệ trước khi gửi lệnh kết thúc tiến trình.
- Quy trình gửi tín hiệu kết thúc tiến trình: Áp dụng `terminate()` (tín hiệu `SIGTERM`), chờ 2–3 giây, sau đó dùng `kill()` (`SIGKILL`) nếu tiến trình chưa thoát hoàn toàn.

---

## 4. Điều Kiện Phê Duyệt Kỹ Thuật (Blocking Conditions)

1. **`cond-1-popen-lifecycle`**:
   - Refactor hàm `_run_single_grok_attempt()` trong `packages/ccba-harness/src/ccba_harness/peer.py`: Sử dụng `subprocess.Popen(..., stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)`.
   - Triển khai vòng lặp thăm dò `proc.poll()` theo chu kỳ 1.0 giây kết hợp với bộ đếm thời gian timeout.

2. **`cond-2-strict-prompt-file`**:
   - Khóa chặt hàm `build_grok_cmd()`: Không nhận bất kỳ tham số `prompt_str` nào, chỉ chấp nhận `prompt_path: Path`. Khi gọi nối tiếp phiên làm việc, cú pháp bắt buộc là:
     `grok -m <model> --always-approve --no-subagents --output-format plain -r <session_id> --prompt-file <path>`

3. **`cond-3-verdict-atomic-validation`**:
   - Trong vòng lặp giám sát của Watchdog, chỉ kích hoạt ngắt tiến trình Grok khi tệp `output_path` đọc được trên đĩa và hàm `parse_verdict_from_md(content)` trả về kết quả khác `None`.

---

## 5. Kết Luận
Đề xuất 4 giải pháp từ Antigravity giải quyết trúng nguyên nhân cốt lõi gây gián đoạn chuỗi tự động hóa. Khi bổ sung 3 điều kiện kỹ thuật nêu trên vào `packages/ccba-harness/src/ccba_harness/peer.py`, chuỗi cộng tác tự động giữa Antigravity và Grok Runner sẽ vận hành trơn tru và loại bỏ triệt để tình trạng treo terminal.
