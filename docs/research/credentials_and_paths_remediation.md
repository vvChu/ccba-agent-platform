# Báo cáo Bảo mật Credentials & Kiểm kê Hardcoded Paths (WF-OS-02 & WF-OS-03)

> **Mã hiệu:** REPORT-2026-004  
> **Trạng thái:** Hoàn thành  
> **Người thực hiện:** Antigravity (AI Agent)  
> **Ngày:** 2026-07-19  

Báo cáo này trình bày kết quả điều tra chi tiết về (1) cơ chế đọc/ghi tệp tin xác thực Google Drive trong dự án và (2) danh sách các đường dẫn `.md/` bị viết cứng (hardcoded) trong mã nguồn của các packages. Đồng thời đề xuất giải pháp remediate khả thi.

---

## 1. Kết quả WF-OS-02: Cơ chế Google Drive Credentials

### 1.1. Hiện trạng
Các tệp tin cấu hình và khóa bí mật OAuth2 hiện tại đang được đọc/ghi ở hai script:
- `scripts/drive_auth_helper.py` (OAuth local flow server)
- `scripts/legal_sync.py` (Đồng bộ registry lên NotebookLM)

Đường dẫn viết cứng:
- `CLIENT_SECRETS_PATH = Path(".md/scratch/client_secrets.json")`
- `TOKEN_PATH = Path(".md/scratch/drive_token.json")`

### 1.2. Rủi ro
- Mặc dù thư mục `.md/scratch/` đã nằm trong `.gitignore` bảo vệ 2 lớp, việc lưu trữ khóa API (OAuth client secrets) và Access Tokens trong thư mục dự án vẫn vi phạm quy tắc an toàn thông tin cơ bản.
- Kỹ sư phải re-authenticate (đăng nhập lại) và tải lại file `client_secrets.json` cho từng Spoke mới khởi tạo, gây bất tiện lớn cho trải nghiệm nhà phát triển.

### 1.3. Giải pháp đề xuất: Safe Home Directory & SSO
Di chuyển toàn bộ credential files ra khỏi không gian dự án, đưa về thư mục cấu hình an toàn của người dùng (User Profile Home):

```python
import os
from pathlib import Path

def get_credentials_dir() -> Path:
    # 1. Ưu tiên biến môi trường cấu hình tùy chọn
    env_dir = os.environ.get("CCBA_CREDENTIALS_DIR")
    if env_dir:
        return Path(env_dir)
    
    # 2. Mặc định dùng thư mục ẩn trong User Home profile (hoạt động đa nền tảng)
    return Path.home() / ".ccba" / "credentials"
```

Khi đó:
- `client_secrets.json` và `drive_token.json` sẽ nằm tại `%USERPROFILE%\.ccba\credentials\` (trên Windows).
- **Lợi ích SSO (Single Sign-On):** Kỹ sư chỉ cần xác thực **1 lần duy nhất** trên máy cục bộ. Tất cả các dự án Spoke sau này (kể cả tạo mới) sẽ tự động sử dụng chung token đã xác thực này mà không cần đăng nhập lại.

---

## 2. Kết quả WF-OS-03: Kiểm kê Hardcoded Paths `.md/` trong Packages

Quét đệ quy thư mục `packages/` phát hiện **21 vị trí** hardcode đường dẫn `.md/` tập trung chủ yếu trong package `ccba-notebooklm`:

| Package | Tệp tin | Dòng | Dòng code chứa hardcode | Đánh giá rủi ro & Đề xuất |
| :--- | :--- | :---: | :--- | :--- |
| `ccba-legal-intel` | `ccba_legal/adr.py` | 8, 74 | `.md/knowledge/adr/` | **Rủi ro Thấp.** Nên thay đổi thành đường dẫn động trỏ tới thư mục cấu hình `docs/adr/` khi ở mode `software`/`hybrid`. |
| `ccba-legal-intel` | `ccba_legal/crawler.py` | 600 | `.md/data/cache/` | **Rủi ro Thấp.** Thư mục cache thô có thể cấu hình động. |
| `ccba-notebooklm` | `src/ccba_notebooklm/_client.py` | 258 | `Path(".md/scratch")` | **Rủi ro Thấp.** Thư mục scratch luôn tồn tại trên cả 3 modes, không lo lỗi crash. |
| `ccba-notebooklm` | `src/ccba_notebooklm/_registry.py` | 9 | `Path(".md/workspace_context.yaml")` | **Rủi ro Cao.** Đây là file onboarding của Agent. Phải giữ nguyên đường dẫn này để đảm bảo các package nhận diện được dự án. |
| `ccba-notebooklm` | `src/ccba_notebooklm/_registry.py` | 10 | `Path(".md/data/sources_registry.yaml")` | **Rủi ro Trung bình.** Mode `software` không có `.md/data/`. File registry này nên được tự động đổi hướng sang `.md/scratch/` hoặc `docs/` nếu chạy ở mode `software`. |
| `ccba-notebooklm` | `src/ccba_notebooklm/_registry.py` | 11 | `Path(".md/scratch/notebooklm_task_state.yaml")` | **Rủi ro Thấp.** Scratch luôn tồn tại. |
| `ccba-notebooklm` | `src/ccba_notebooklm/_security.py` | 81 | `Path(".md/scratch/redacted")` | **Rủi ro Thấp.** Scratch luôn tồn tại. |
| `ccba-notebooklm` | `src/ccba_notebooklm/__main__.py` | 68 | `--output` mặc định `.md/extracted_docs/...` | **Rủi ro Thấp.** Đây chỉ là giá trị mặc định của parser CLI. Người dùng hoặc Agent hoàn toàn có thể truyền flag `--output` khác khi chạy lệnh. |
| `ccba-notebooklm` | `src/ccba_notebooklm/__main__.py` | 79-176 | `--output` mặc định `.md/scratch/...` | **Rủi ro Thấp.** Scratch luôn tồn tại. |

### Đánh giá tổng quan về rủi ro Refactor
- Rủi ro crash runtime khi chạy ở các mode khác là **cực kỳ thấp** vì hầu hết các đường dẫn hardcode đều trỏ vào `.md/scratch/` (thư mục luôn tồn tại trên cả 3 modes).
- Vấn đề duy nhất cần xử lý là file **`sources_registry.yaml`** (dòng 10 của `_registry.py`). File này nằm ở `.md/data/` - thư mục không có trong mode `software`. 

**Phương án đề xuất cho `sources_registry.yaml`:**
Sửa đổi logic nạp registry trong package `ccba-notebooklm` để tự động kiểm tra mode và chuyển hướng:
```python
# Tự động chuyển hướng registry nếu chạy ở mode software
context_file = Path(".md/workspace_context.yaml")
if context_file.exists():
    # Đọc mode...
    if mode == "software":
        REGISTRY_FILE = Path(".md/scratch/sources_registry.yaml")
```
