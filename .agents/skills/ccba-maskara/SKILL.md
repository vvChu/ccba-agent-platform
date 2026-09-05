---
name: ccba-maskara
description: Phát hiện, che giấu (redact) thông tin nhạy cảm (API keys, passwords,
  private keys) trong files/logs và cài đặt guardrails bảo mật.
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
triggers:
- ccba-maskara
- privacy
- redact
- scan secret
- leak
- che giấu key
---
# Maskara Privacy - Bảo mật thông tin nhạy cảm CCBA

> **Vai trò**: Đây là kỹ năng bảo mật cốt lõi giúp phát hiện và che giấu (redact) các thông tin nhạy cảm (OpenAI API key, Google API key, AWS keys, JWT, Database URLs, Private key...) trong logs và files của dự án trước khi commit hoặc chia sẻ.

## 1. Cú pháp sử dụng lệnh

Lệnh CLI được thực thi qua Python:
```bash
python scripts/maskara.py [subcommand] [arguments]
```

### Quét phát hiện (scan)
Quét và in ra danh sách các secrets phát hiện được mà không thay đổi file:
```bash
# Quét mặc định tự động tìm các agent đang cài đặt
python scripts/maskara.py scan

# Quét một agent cụ thể
python scripts/maskara.py scan --agent claude
python scripts/maskara.py scan -a gemini

# Quét một thư mục log tùy chỉnh
python scripts/maskara.py scan --root .md/scratch/temp_logs

# Quét kết hợp đối soát sâu bằng AI Gateway (LiteLLM) để tránh false positives
python scripts/maskara.py scan --llm
```

### Che giấu secrets (redact)
Tự động quét, tạo file backup tập trung tại `.md/scratch/backups/`, và ghi đè che giấu secrets trong các files gốc:
```bash
# Quét và che giấu toàn bộ logs phát hiện được
python scripts/maskara.py redact
```
*Lưu ý: Chuỗi secrets sẽ được thay thế bằng định dạng: `[MASKARA_REDACTED:rule-id]`.*

### Xuất báo cáo (report)
Tạo báo cáo chi tiết về tình trạng leak secrets (mặc định xuất ra file Markdown hoặc JSON):
```bash
# Xuất báo cáo Markdown mặc định (maskara-report.md)
python scripts/maskara.py report

# Xuất báo cáo JSON
python scripts/maskara.py report --json

# Chỉ định file đầu ra
python scripts/maskara.py report -o .md/knowledge/security_report.md
```

### Cài đặt Guardrails (guardrails)
Cài đặt tệp chỉ dẫn bảo mật, privacy skill mẫu và hooks kiểm tra trước khi chạy lệnh cho agent cục bộ:
```bash
# Cài đặt guardrails cho claude
python scripts/maskara.py guardrails -a claude

# Xem thử các thay đổi sẽ được thực hiện (không ghi file)
python scripts/maskara.py guardrails --dry-run
```

---

## 2. Quy tắc bảo mật cho Agent (Rules for Agent)

Khi làm việc trong dự án có xử lý credentials, Agent **BẮT BUỘC** tuân thủ các quy tắc sau:
1. **Không in khóa cấu hình ra màn hình:** Không in raw secrets hoặc nội dung file `.env` lên transcript trò chuyện với user.
2. **Sử dụng bypass APPROVED:** Nếu thực sự cần đọc hoặc thao tác trên file nhạy cảm được bảo vệ bởi hook `privacy_block.py`, hãy xin phép user và sử dụng tiền tố `APPROVED:` (ví dụ: `APPROVED:.env`).
3. **Quét dọn trước khi kết thúc:** Trước khi chạy lệnh `/ccba-session-retrospective` hoặc đóng phiên, chạy `python scripts/maskara.py redact` để đảm bảo không để lại raw keys trong log files hoặc workspace files.

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
