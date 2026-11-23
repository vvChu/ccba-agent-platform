---
name: ccba-maskara
description: Phát hiện, che giấu (redact) thông tin nhạy cảm (API keys, passwords,
  private keys) trong files/logs và cài đặt guardrails bảo mật.
metadata:
  version: "1.0.1"
  author: "CCBA Hub"
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
scope: universal
posture: package-bound
seam_ids:
  - maskara_scanner.v1
tier: kernel
command: /ccba-maskara
gpi:
  s: 3.0
  k: 3.0
  a: 4.0
  p: 1.0
triggers:
- ccba-maskara
- privacy
- redact
- scan secret
- leak
- che giấu key
package_path: packages/ccba-maskara
---

# Maskara Privacy - Bảo mật thông tin nhạy cảm CCBA

> **Vai trò**: Đây là kỹ năng bảo mật cốt lõi giúp phát hiện và che giấu (redact) các thông tin nhạy cảm (OpenAI API key, Google API key, AWS keys, JWT, Database URLs, Private key...) trong logs và files của dự án trước khi commit hoặc chia sẻ.

## 1. Cú pháp sử dụng lệnh

Lệnh CLI đa môi trường (chạy được trên cả Spoke và Hub; **không** chạy `python -m ccba_maskara` vì gói chưa có `__main__.py`; `scripts/maskara.py` chỉ tồn tại tại Hub):
```bash
maskara [subcommand] [arguments]
# Hoặc gọi trực tiếp qua module CLI:
python -m ccba_maskara.cli [subcommand] [arguments]
```

### Quét phát hiện (scan)
Quét và in ra danh sách các secrets phát hiện được mà không thay đổi file:
```bash
# Quét các tệp đã staged trước khi commit (được .githooks/pre-commit gọi tự động)
python -m ccba_maskara.cli scan --staged

# Quét danh sách tệp chỉ định
python -m ccba_maskara.cli scan --files path/to/file1.md path/to/file2.yaml

# Quét mặc định tự động tìm các agent đang cài đặt
python -m ccba_maskara.cli scan

# Quét một agent cụ thể hoặc thư mục log tùy chỉnh
python -m ccba_maskara.cli scan --agent claude
python -m ccba_maskara.cli scan -a gemini
python -m ccba_maskara.cli scan --root .md/scratch/temp_logs

# Quét kết hợp đối soát sâu bằng AI Gateway (LiteLLM) để tránh false positives
python -m ccba_maskara.cli scan --llm
```

### Python Seam API (`maskara_scanner.v1`) & Tự động hóa Pre-Commit
- **Tự động hóa khi commit:** Hook `.githooks/pre-commit` (cài qua `python -m ccba_maskara.cli init-hooks`) tự động chạy `maskara scan --staged` hoặc `python -m ccba_maskara.cli scan --staged` (chặn `critical`/`high`/`medium`) mỗi lần `git commit`, nên không cần viết one-liner quét thủ công trước commit thường lệ.
- **Gọi trực tiếp trong Python:** Chữ ký bắt buộc đủ 2 tham số `(agent, path)` để tránh `TypeError`:
  ```python
  from pathlib import Path
  from ccba_maskara import MaskaraScanner, detect_secrets_in_text

  findings, scanned, skipped = MaskaraScanner().scan_file("spoke", Path(f))
  # Lưu ý: scan_file chỉ quét tệp văn bản/session (looks_like_session_text), bỏ qua tệp .py.
  # Để quét mã nguồn .py hoặc chuỗi tùy ý, dùng:
  py_findings = detect_secrets_in_text(Path(f).read_text(encoding="utf-8"), filepath=str(f), agent="spoke")
  ```

### Che giấu secrets (redact)
Tự động quét, tạo file backup tập trung tại `.md/scratch/backups/`, và ghi đè che giấu secrets trong các files gốc:
```bash
# Quét và che giấu toàn bộ logs phát hiện được
python -m ccba_maskara.cli redact
```
*Lưu ý: Chuỗi secrets sẽ được thay thế bằng định dạng: `[MASKARA_REDACTED:rule-id]`.*

### Xuất báo cáo (report)
Tạo báo cáo chi tiết về tình trạng leak secrets (mặc định xuất ra file Markdown hoặc JSON):
```bash
# Xuất báo cáo Markdown mặc định (maskara-report.md)
python -m ccba_maskara.cli report

# Xuất báo cáo JSON
python -m ccba_maskara.cli report --json

# Chỉ định file đầu ra
python -m ccba_maskara.cli report -o .md/knowledge/security_report.md
```

### Cài đặt Guardrails (guardrails) & Pre-Commit Hook
Cài đặt tệp chỉ dẫn bảo mật, privacy skill mẫu và hooks kiểm tra trước khi chạy lệnh cho agent cục bộ:
```bash
# Cài đặt pre-commit hook (.githooks/pre-commit)
python -m ccba_maskara.cli init-hooks

# Cài đặt guardrails cho claude hoặc dry-run
python -m ccba_maskara.cli guardrails -a claude
python -m ccba_maskara.cli guardrails --dry-run
```

---

## 2. Quy tắc bảo mật cho Agent (Rules for Agent)

Khi làm việc trong dự án có xử lý credentials, Agent **BẮT BUỘC** tuân thủ các quy tắc sau:
1. **Không in khóa cấu hình ra màn hình:** Không in raw secrets hoặc nội dung file `.env` lên transcript trò chuyện với user.
2. **Sử dụng bypass APPROVED:** Nếu thực sự cần đọc hoặc thao tác trên file nhạy cảm được bảo vệ bởi hook `privacy_block.py`, hãy xin phép user và sử dụng tiền tố `APPROVED:` (ví dụ: `APPROVED:.env`).
3. **Quét dọn trước khi kết thúc:** Trước khi chạy lệnh `/ccba-session-retrospective` hoặc đóng phiên, chạy `python -m ccba_maskara.cli redact` (hoặc `python scripts/maskara.py redact` tại Hub) để đảm bảo không để lại raw keys trong log files hoặc workspace files.

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*

## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (ADR-0058)
* **Tiêu chí hoàn thành tất định:** Mọi thay đổi mã nguồn, kỹ năng hoặc tài liệu bắt buộc phải vượt qua bộ kiểm thử tự động.
* **Hard Completion Lock:** Nghiêm cấm tuyên bố hoàn thành task hoặc yêu cầu nghiệm thu nếu lệnh xác minh chưa vượt qua:
  ```bash
  python -m ccba_harness verify-patch
  ```
* **Zero Tolerance Exit Code:** Lệnh kiểm thử phải thoát với mã exit code 0; tuyệt đối không bỏ qua các lỗi linter hay hồi quy.

## Kỷ Luật Rà Soát Hai Vòng (Double-Pass Adversarial Review)
* **Vòng 1 (Code-First Research):** Luôn đọc implementation thực tế và kiểm tra data flow end-to-end trước khi sửa đổi. Không suy đoán hành vi từ tên hàm hay docstring.
* **Vòng 2 (Self-Adversarial Review):** Tự đặt câu hỏi: *Đề xuất này có thể SAI ở đâu?* Kiểm chứng tối thiểu 3 giả định cốt lõi bằng dữ liệu và kiểm thử thực tế trước khi bàn giao.
* **Bảo tồn Invariants:** Không bao giờ xóa hoặc nới lỏng (weaken) các bài test hiện có để làm cho bài test vượt qua.

## Chuẩn Mực Thiết Kế Mã Nguồn: KISS, Idempotency & Error Handling
* **KISS (Keep It Simple, Stupid):** Ưu tiên giải pháp đơn giản nhất; không tạo abstraction/seam giả định khi chưa có ít nhất 2 adapter thực tế.
* **Idempotency:** Mọi script thao tác tệp, database hay git worktree phải đảm bảo tính lũy kế an toàn (chạy nhiều lần cho ra cùng một kết quả vững chắc).
* **Explicit Error Handling:** Xử lý ngoại lệ cụ thể (Specific Exceptions); nghiêm cấm sử dụng bare `except:` hoặc nuốt lỗi âm thầm.
* **Type Hints & Docstrings:** Mọi hàm/phương thức public bắt buộc có type annotations đầy đủ và docstrings chuẩn mực.
