# ADR 0044: Hub-Spoke Package Bootstrap Standardization & Editable Install Protocol

## Context

Trong quá trình phát triển các Spoke (đặc biệt là Spoke Tri thức Pháp luật `ccba-legal-knowledge` và các Spoke Chức năng khác), nhiều script đã sử dụng anti-pattern chèn đường dẫn tuyệt đối hoặc tương đối thông qua `sys.path.insert(0, str(HUB_SRC))` để import các module từ Hub packages (`ccba-legal-intel`, `ccba-ai`, `ccba-harness`...).

### Hậu quả của Anti-Pattern `sys.path.insert`:
1. **Mù lòa IDE & Linter**: IDE (VSCode, Cursor, PyCharm) và Static Linters (Mypy, Ruff) không nhận diện được module $\rightarrow$ Mất hoàn toàn autocomplete, type hint checking và phát hiện lỗi cú pháp sớm.
2. **Dễ đổ vỡ (Brittle Links)**: Khi Hub tái cấu trúc hoặc di chuyển thư mục `src/`, toàn bộ các script tại Spoke bị gãy mà không có cảnh báo trước.
3. **Lặp lại mã rác (Boilerplate Bloat)**: Mỗi script tại Spoke phải lặp lại 3–5 dòng cấu hình đường dẫn và monkey-patching `sys.path`.
4. **Vi phạm chuẩn phân phối Python**: Không tận dụng được cơ chế packaging chuẩn (`pyproject.toml`, `site-packages`, editable installs).

Do đó, Hub cần ban hành một tiêu chuẩn kết nối chính thức, nhất quán và tự động hóa cho mọi Spoke Python hiện tại và tương lai.

---

## Decision

Chúng tôi quyết định thiết lập **Quy chuẩn Hub-Spoke Package Bootstrap (Standard Editable Link Protocol)** với các trụ cột sau:

### 1. Phân Tầng Package (Tiered Hub Packages)

Hub phân loại toàn bộ 8 packages theo 3 tầng ưu tiên cài đặt:

| Tier | Package | Phạm vi áp dụng | Mục đích |
| :--- | :--- | :--- | :--- |
| **Tier 0** (Core Platform) | `ccba-harness`, `ccba-ai` | **Bắt buộc** cho mọi Spoke có Python (`is_python_project = True`) | Cung cấp Singleton Process Lock, Telemetry, Guardrails, AI Gateway SDK và Circuit Breaker. |
| **Tier 1** (Archetype Core) | `ccba-legal-intel` | Mặc định cho Archetype `knowledge_corpus` | Pipeline cào TVPL VIP, bóc tách phụ lục, AST diffing, đóng gói OKF Bundle v2.0. |
| **Tier 1** (Archetype Core) | `ccba-ooxml`, `ccba-pdf-prep`, `mdconverter` | Mặc định cho `project_delivery`, `enterprise_governance` | Xử lý Office DOM, tái dựng bảng vỡ, bóc tách khung tên PDF bản vẽ. |
| **Tier 2** (Optional Extras) | `ccba-notebooklm`, `ccba-maskara` | Theo nhu cầu khai báo của Spoke | Google NotebookLM Cloud RAG, Redaction scan. |

> [!NOTE]
> Đối với Spoke thuần túy tài liệu/Markdown/Tư vấn không chứa mã Python (`is_python_project = False`), toàn bộ quy trình bootstrap Python SDK được bỏ qua an toàn.

---

### 2. Khai Báo Phụ Thuộc Tại Spoke (`workspace_context.yaml`)

Spoke quản lý danh sách Hub packages cần dùng thông qua trường `hub_packages` trong file Single Source of Truth `workspace_context.yaml`:

```yaml
project:
  name: "ccba-legal-knowledge"
  archetype: "knowledge_corpus"
  type: "Phần mềm"
  mode: "software"

hub_packages:
  # Tier 0 (ccba-harness, ccba-ai) luôn được tự động bổ sung
  - ccba-legal-intel
  - ccba-notebooklm
```

---

### 3. Tự Động Hóa Bootstrap & Thứ Tự Phụ Thuộc (Dependency Ordering)

Hub cung cấp công cụ tự động hóa `spoke_bootstrap.py` (kèm wrapper `spoke_bootstrap.ps1`):
1. **Kiểm tra môi trường**: Tự động phát hiện hoặc tạo virtual environment (`.venv`) tại Spoke.
2. **Giải quyết thứ tự cài đặt**: Luôn cài đặt theo thứ tự topo không bị vòng:
   $$\text{ccba-harness} \longrightarrow \text{ccba-ai} \longrightarrow \text{ccba-legal-intel / ccba-ooxml / mdconverter...}$$
3. **Editable Installation**: Thực thi `pip install -e "[hub_path]/packages/<pkg_name>"` vào virtualenv của Spoke.
4. **Sinh Lockfile & Cách Ly Git**:
   - Tự động sinh file `requirements-hub.txt` tại Spoke root chứa danh sách `-e <path>`.
   - **Bắt buộc**: File `requirements-hub.txt` phải được thêm vào `.gitignore` của Spoke vì chứa đường dẫn tuyệt đối theo máy cục bộ.

---

### 4. Ranh Giới Public API (`__all__` Guard Contract)

Để tránh tình trạng Hub refactor nội bộ làm gãy Spoke:
- Mọi Hub package phải khai báo tường minh danh sách `__all__` tại `src/<pkg_name>/__init__.py`.
- Spoke chỉ được phép import các Deep Seams và Models nằm trong `__all__` của package.
- Không tách riêng package `ccba-legal-sdk` trong giai đoạn hiện tại (tuân thủ KISS); thay vào đó dùng `__all__` làm hợp đồng giao diện công khai (Public API Surface).

---

### 5. Lộ Trình Semantic Versioning (SemVer) & Breaking Changes

1. **Phase 0 (Hiện tại)**: Toàn bộ packages Hub tuân theo `0.x.y` (API đang hoàn thiện).
2. **Phase 1 (Q4 2026)**: Khi có $\ge 2$ Spoke triển khai production ổn định, các core packages được nâng lên `1.0.0` và tuân thủ SemVer nghiêm ngặt.
3. **Cơ chế Cảnh báo Breaking Change**:
   - Mỗi package Hub duy trì `CHANGELOG.md` theo chuẩn Keep a Changelog. Mọi thay đổi phá vỡ tương thích phải đánh dấu `⚠️ BREAKING`.
   - `SharedSdkInspector` trong `sync_spoke.py` quét phiên bản trong `dist-info` của `.venv` Spoke so với Hub và hiển thị cảnh báo nếu có phiên bản lệch pha.

---

### 6. Branch Guard & Commit Hash Tracking (Grilling Q1-Q2)

Editable install (`pip install -e`) trỏ trực tiếp vào working directory của Hub. Để giảm rủi ro "Phantom Dependency" khi Hub đang trên feature branch:

1. **Branch Guard**: `spoke_bootstrap.py` kiểm tra `git branch --show-current` tại Hub. Nếu **không phải** `main` hoặc `master`, bootstrap bị chặn trừ khi dùng cờ `--force`.
2. **Commit Hash Snapshot**: Khi sinh `requirements-hub.txt`, ghi thêm comment `# hub_commit: <short_hash>` để Spoke lưu vết Hub commit nào đang được link. `SharedSdkInspector` có thể so sánh hash này với HEAD hiện tại của Hub để phát hiện drift.

---

### 7. Import Depth Rule & Pre-commit Enforcement (Grilling Q6-Q8)

`__all__` trong Python chỉ ảnh hưởng đến `from package import *`, không ngăn deep imports trực tiếp. Để enforce ranh giới API thực sự:

1. **Quy tắc**: Spoke code chỉ được import từ top-level Hub package (depth ≤ 2). Cấm `from ccba_legal.crawler.chrome_cdp import X` — phải dùng `from ccba_legal import X`.
2. **Enforcement**: Pre-commit script `check_hub_import_depth.py` tại `scripts/spoke/` quét pattern `from ccba_xxx.submodule.deep_module`.
3. **Phân phối**: Script được copy vào Spoke bởi workflow `/ccba-init-spoke` và đồng bộ lại qua `/ccba-update-spoke`.
4. **Ngoại lệ**: Nếu Spoke cần symbol chưa có trong `__all__`, tạo issue đề xuất Hub bổ sung vào Public API Surface.

---

## Consequences

### Tích cực (Positive)
- **Chuẩn hóa 100%**: Loại bỏ hoàn toàn anti-pattern `sys.path.insert` trên toàn mạng lưới Spokes.
- **IDE & Type Safety**: Phục hồi đầy đủ tính năng autocomplete, type hints, refactoring tool của IDE trong Spoke.
- **Zero Configuration Drift**: Spoke chỉ cần 1 lệnh `/ccba-init-spoke` hoặc `spoke_bootstrap.ps1` là có ngay môi trường tích hợp đầy đủ SDK.
- **Bảo mật Git**: `requirements-hub.txt` được cách ly khỏi Git, không làm rò rỉ đường dẫn máy cá nhân lên remote repo.
- **Branch Guard**: Ngăn chặn bootstrap khi Hub đang trên branch không ổn định, giảm rủi ro Phantom Dependency.
- **Commit Hash Tracking**: Cho phép phát hiện version drift giữa Hub commit đã link và HEAD hiện tại.
- **Import Depth Enforcement**: Pre-commit hook chặn deep imports, buộc Spoke tuân thủ `__all__` API contract.

### Tiêu cực / Ràng buộc (Trade-offs)
- Spoke Python cần có `.venv` cục bộ (tăng dung lượng đĩa ~100-200MB cho virtual environment).
- Khi Hub cập nhật dependencies bên ngoài của một package (ví dụ thêm thư viện `requests` mới), Spoke cần chạy lại `spoke_bootstrap.ps1` hoặc `sync_spoke.py` để cập nhật.
- Pre-commit hook yêu cầu Spoke cài đặt `pre-commit` (one-time setup qua `/ccba-init-spoke`).

