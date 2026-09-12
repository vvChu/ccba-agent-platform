# ccba-server-deploy — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Hướng dẫn triển khai cấu hình server và hạ tầng phục vụ Agent
> **Mô tả gốc:** Tự động triển khai và cấu hình nền tảng CCBA Agent Platform trên Server Spark

---

# Workflow: Tự Động Triển Khai Nền Tảng Trên Server Spark (/ccba-init-spoke)

Quy trình tự động hóa triển khai, cấu hình và giám sát sức khỏe nền tảng CCBA Agent Services Platform trên máy chủ tính toán Server Spark.

Tài liệu tham chiếu chi tiết: [server_spark_agent_instructions.md](../../../../docs/playbooks/server_spark_agent_instructions.md).

## Yêu cầu tiên quyết (Prerequisites)
- Quyền truy cập SSH vào Server Spark thông qua Tailscale VPN (`100.83.192.30`).
- Môi trường Python runtime tối thiểu `>= 3.10` và Git client.
- Dịch vụ LiteLLM Gateway đang hoạt động tại cổng `:8090`.

---

## Các bước thực hiện

### Bước 1: Khảo sát môi trường và kết nối mạng (Pre-flight Inspection)
1. Kiểm tra phiên bản Python runtime: `python3 --version` (yêu cầu `>= 3.10`).
2. Xác minh trạng thái dịch vụ mạng Tailscale và kết nối cục bộ: `tailscale status`.
3. Kiểm tra tính sẵn sàng của LiteLLM AI Gateway: `curl -s http://127.0.0.1:8090/health`.
- **Tiêu chí hoàn thành:** Môi trường runtime hợp lệ, Tailscale online và endpoint LiteLLM trả về mã HTTP 200.

### Bước 2: Khởi tạo cấu trúc thư mục lưu trữ (Directory Bootstrap)
1. Tạo thư mục làm việc chuẩn tại `~/ccba/`.
2. Clone repository trung tâm `ccba-agent-platform` vào thư mục đích.
3. Clone repository tri thức pháp lý `ccba-legal-knowledge` nằm ngang hàng tại `~/ccba/ccba-legal-knowledge`.
- **Tiêu chí hoàn thành:** Cả hai kho mã nguồn được clone thành công với cấu trúc thư mục chuẩn mực.

### Bước 3: Thiết lập môi trường ảo và cài đặt Packages (Virtualenv & Packages)
1. Tạo môi trường ảo chuyên biệt: `python3 -m venv ~/ccba/venv`.
2. Kích hoạt môi trường và cập nhật pip: `source ~/ccba/venv/bin/activate && pip install --upgrade pip`.
3. Cài đặt các gói cốt lõi ở chế độ editable:
   - `pip install -e ~/ccba/ccba-agent-platform/packages/ccba-ai`
   - `pip install -e ~/ccba/ccba-agent-platform/packages/ccba-harness`
   - `pip install -e ~/ccba/ccba-agent-platform/packages/ccba-legal-intel`
- **Tiêu chí hoàn thành:** 100% các package cốt lõi cài đặt thành công không có xung đột phụ thuộc.

### Bước 4: Đăng ký lịch trình định kỳ (Cron Automation Registration)
1. Kiểm tra tệp thực thi `run_nightly_tuner.sh` và cấp quyền thực thi: `chmod +x run_nightly_tuner.sh`.
2. Đăng ký tiến trình chạy nền tự động hàng đêm vào `crontab` với biểu thức `0 0 * * *`:
   ```bash
   crontab -l > /tmp/crontab.tmp || true
   echo "0 0 * * * /bin/bash ~/ccba/ccba-agent-platform/scripts/eval/run_nightly_tuner.sh >> ~/ccba/logs/cron.log 2>&1" >> /tmp/crontab.tmp
   crontab /tmp/crontab.tmp && rm /tmp/crontab.tmp
   ```
3. Khởi tạo thư mục nhật ký `~/ccba/logs/` nếu chưa tồn tại.
- **Tiêu chí hoàn thành:** Cron job đăng ký chính xác trong crontab hệ thống và ghi nhận log đường dẫn.

### Bước 5: Kiểm thử khép kín và nghiệm thu (Dry-run & Health Verification)
1. Chạy thử nghiệm chế độ mô phỏng: `python scripts/eval/nightly_tuner_daemon.py --dry-run`.
2. Xác minh kết nối gửi thông báo Telegram Alert: `python scripts/verify_telegram_alert.py`.
3. Lập báo cáo bàn giao chi tiết các tham số vận hành cho người quản trị.
- **Tiêu chí hoàn thành:** Dry-run thành công không phát sinh exception, thông báo test gửi về Telegram chuẩn xác.
