---
proposal_id: "2026-07-03_path-registry-normalizer"
type: "skill"
name: "path-registry-normalizer"
status: "merged"
priority: "Cao"
proposed_by_project: "ccba-agent-platform"
proposed_date: "2026-07-03"
applies_to:
  - "Tất cả"
---

## Mô tả
Helper/kỹ năng tự động chuẩn hóa các đường dẫn tuyệt đối (absolute path) sang dạng tương đối (repo-relative) tương thích chuẩn POSIX để phục vụ cho các registries lưu trữ di động.

## Vấn đề giải quyết
Khi các công cụ lưu trữ dữ liệu đối soát cục bộ (như Registry của NotebookLM hoặc Sources Registry) sử dụng đường dẫn tuyệt đối dạng `D:\GitHubProjects\ccba-agent-platform\...`, nó sẽ gây ra các lỗi nghiêm trọng khi chuyển giao dự án hoặc chạy trên môi trường khác:
1. **Lỗi phân quyền:** Đường dẫn tuyệt đối của máy tính này không tồn tại trên máy tính khác hoặc CI.
2. **Broken Link Error:** Các đường dẫn bị coi là không hợp lệ hoặc trỏ sai địa chỉ khi chạy Documentation Link Validator trên CI.
3. **Mất tính Portability:** Giảm khả năng di chuyển và cộng tác chéo OS (Windows vs Linux vs macOS).

## Giải pháp / Cấu trúc đề xuất
Xây dựng một module helper/kỹ năng dùng chung giúp tự động quét và phân dịch ngược đường dẫn:
1. Xác định thư mục root của workspace.
2. So khớp nếu đường dẫn tuyệt đối nằm bên trong workspace -> tự động rút gọn thành đường dẫn tương đối (ví dụ: `.md/legal_docs/...`).
3. Chuẩn hóa dấu phân cách thư mục Windows `\` sang POSIX `/` để chạy được trên mọi OS và hệ thống web/cloud RAG (Google Drive, NotebookLM).

## Nội dung mẫu / Code mẫu
```python
from pathlib import Path

def normalize_to_relative(path_str: str, root_path: Path) -> str:
    """Tự động chuyển đổi đường dẫn tuyệt đối thành tương đối POSIX-compatible
    đối với các tài nguyên nằm trong workspace.
    """
    try:
        p = Path(path_str).resolve()
        if p.is_relative_to(root_path):
            return p.relative_to(root_path).as_posix()
    except Exception:
        pass
    
    # Fallback cho các đường dẫn bên ngoài hoặc không hợp lệ
    return path_str.replace("\\", "/")
```
