---
description: Tự động triển khai và cấu hình nền tảng CCBA Agent Platform trên Server
  Spark
applies_to:
- Tác vụ Admin
- Phần mềm
bundle: _core
disable-model-invocation: true
---
# Workflow: Tự Động Triển Khai Nền Tảng Trên Server Spark (/ccba-server-deploy)

Khi người dùng kích hoạt lệnh này, Agent hãy đọc và thực thi chỉ dẫn triển khai tự động theo tài liệu [server_spark_agent_instructions.md](../../docs/playbooks/server_spark_agent_instructions.md).

---

## Các bước thực hiện:
1. **Khảo sát môi trường:** Kiểm tra Python 3.10+, Git, Tailscale VPN và LiteLLM Gateway (`:8090`).
2. **Khởi tạo thư mục:** Clone `ccba-agent-platform` và `ccba-legal-knowledge` nằm ngang hàng tại `~/ccba/`.
3. **Cài đặt packages:** Thiết lập Virtualenv và cài đặt editable packages (`ccba-ai`, `ccba-harness`, `ccba-legal-intel`).
4. **Cấu hình Cron:** Đăng ký lịch chạy `run_nightly_tuner.sh` lúc `0 0 * * *` (nửa đêm hàng ngày).
5. **Kiểm thử khép kín:** Chạy dry-run `nightly_tuner_daemon.py` và báo cáo kết quả cho người dùng.
