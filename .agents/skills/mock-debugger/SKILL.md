---
name: mock-debugger
description: Automated debugger and self-healing trace analyzer. Runs scripts, captures
  tracebacks, and provides root cause analysis and code patch suggestions via AI.
disable-model-invocation: true
bundle: _software
triggers:
- debug
- mock-debugger
- sửa lỗi
- self-healing
- gỡ lỗi
---
# Mock Debugger (`mock-debugger`)

Kích hoạt bộ tự động gỡ lỗi và tự phục hồi mã nguồn Python (Self-Healing Debugger).

## Cách sử dụng

Khi chạy thử nghiệm mã nguồn Python bị lỗi crash hoặc gặp lỗi logic:
1. Chạy gỡ lỗi và phân tích vết traceback:
   ```bash
   python scripts/security/mock_debugger.py path/to/failing_script.py [arguments]
   ```
2. AI sẽ tự động phân tích và đưa ra:
   * Nguyên nhân lỗi (RCA).
   * Đoạn mã sửa lỗi mẫu (Git diff/patch).
   * Khuyến nghị phòng ngừa.
