---
id: 228
title: "fix(sync): spoke sync robustness, master corpus self-loop guard, utf-8 linter & 1-click bootstrap"
state: "ready-for-agent"
labels:
  - "bug"
  - "ready-for-agent"
assignee: "none"
created_at: "2026-09-02T06:20:30Z"
updated_at: "2026-09-02T06:40:00Z"
---

# 📖 Mô tả (Description)
### 1. Bối cảnh & Vấn đề (Context & Problem)
Trong quá trình vận hành đồng bộ hóa từ Hub sang các Spoke (đặc biệt là Spoke Tri thức Pháp lý `ccba-legal-knowledge`), đã phát hiện 4 điểm nghẽn kỹ thuật cần được chuẩn hóa và nâng cấp trên Hub `ccba-agent-platform`:

1. **Vòng lặp tự sao chép dữ liệu trên Master Legal Corpus (ADR 0050):** Khi chạy `sync_spoke.py` tại Spoke `ccba-legal-knowledge` (vốn là Master Knowledge Base), `LegalKnowledgeSyncOrchestrator` kích hoạt `sync_legal_assets()` dẫn tới việc copy ngược `legal_docs/` thành `.md/legal_docs/` và sinh cảnh báo thiếu `.md/data/legal_registry.yaml`, vi phạm Nguyên tắc Đường dẫn Nông (Shallow Path Invariant - ADR 0036).
2. **Lỗi quét đệ quy & Crash UTF-8 trên Windows của `check_hub_import_depth.py`:** Script kiểm tra Import Depth sử dụng `scan_dir.rglob('*.py')` trên thư mục gốc, quét nhầm vào `.agents/`, `.md/backups/`, `.md/archive/` gây false-positives; đồng thời in emoji `\u274c` (`❌`) trên terminal Windows (mã hóa cp1252) gây ra `UnicodeEncodeError`.
3. **Thiếu liên kết 1-chạm giữa `sync_spoke.py` và `SpokeBootstrapper`:** Sau khi sync, hệ thống chỉ in text gợi ý chạy thủ công các lệnh `pip install -e`, trong khi Hub đã có sẵn module `SpokeBootstrapper` (`scripts/spoke/spoke_bootstrap.py`) xử lý `PACKAGE_TOPOLOGY_ORDER` rất hoàn chỉnh.
4. **Tồn dư `sys.path.insert` trong các file mẫu/template:** Một số script template phân phối từ Hub vẫn còn sót lại pattern fallback `sys.path.insert(0, str(hub_src))`, trực tiếp vi phạm cổng kiểm soát sạch sẽ `check_spoke_cleanliness.py`.

---

### 2. Đề xuất giải pháp kỹ thuật (RFC Proposal)

1. **Self-Loop Duplication Guard (`sdk_inspector.py`):**
   - Bổ sung hàm kiểm tra `is_master_legal_corpus()` trong `LegalKnowledgeSyncOrchestrator` để nhận diện Spoke hiện tại là Master Legal Corpus (`project_type == 'Pháp điển'` hoặc có `legal_registry.yaml` ở root), từ đó bỏ qua bước pull assets vào chính nó.
2. **Nâng cấp Linter `check_hub_import_depth.py`:**
   - Cấu hình chỉ quét `root.glob('*.py')` và `rglob('*.py')` trong `scripts/`, `src/`, `tests/`.
   - Bổ sung `.agents` và `.md` vào danh sách exclude.
   - Bổ sung `if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')`.
3. **Tích hợp cờ `--bootstrap` vào `sync_spoke.py`:**
   - Thêm cờ `--bootstrap` / `-b` vào CLI của `sync_spoke.py`.
   - Tự động gọi `SpokeBootstrapper(spoke_root, hub_root).bootstrap()` khi cờ được bật hoặc khi phát hiện thiếu package cốt lõi.
4. **Chuẩn hóa Cleanliness cho Hub Templates:**
   - Rà soát và thay thế toàn bộ pattern `sys.path.insert` bằng mô hình `try: from ccba_xxx import ... except ImportError: ...` kèm hướng dẫn dùng `spoke_bootstrap.py`.

---

### 3. Tiêu chí nghiệm thu (Acceptance Criteria)

- [ ] `sync_spoke.py` chạy trên `ccba-legal-knowledge` không sinh ra thư mục rác `.md/legal_docs/` và `.md/data/legal_registry.yaml`.
- [ ] `check_hub_import_depth.py` chạy an toàn trên Windows PowerShell, không bị crash mã hóa và không quét vào thư mục backup/archive.
- [ ] `sync_spoke.py --bootstrap` tự động thiết lập và cài đặt các package Hub theo đúng topology.
- [ ] Mọi script template trong Hub vượt qua kiểm tra của `check_spoke_cleanliness.py`.

---
*Được đề xuất tự động từ Spoke `ccba-legal-knowledge` qua workflow `/ccba-issue-to-hub`.*

---

# 💬 Thảo luận (Discussion Log)
> **@Antigravity AI Agent (Triage)** (2026-09-02T06:40:00Z):
> Đã hoàn tất quy trình sàng lọc và thẩm định kỹ thuật (Triage).
> Xác nhận lỗi sao chép tự lặp (Self-Loop Duplication) tại `LegalKnowledgeSyncOrchestrator` và các vấn đề về UTF-8 / thiếu cờ bootstrap trong `sync_spoke.py`.
> Đã gán nhãn `bug` và chuyển trạng thái sang `ready-for-agent`. Đính kèm Agent Brief hoàn chỉnh bên dưới.

---

## Agent Brief

**Phân loại:** bug
**Tóm tắt yêu cầu:** Sửa lỗi tự lặp sao chép Master Legal Corpus trong sync, gia cố `check_hub_import_depth.py`, bổ sung cờ `--bootstrap` vào `sync_spoke.py` và chuẩn hóa template cleanliness.

### Hành vi hiện tại (Current behavior)
1. `LegalKnowledgeSyncOrchestrator.is_legal_related_spoke()` trả về True khi quét thấy `legal_registry.yaml` tại Spoke Master Legal Corpus (`ccba-legal-knowledge`), dẫn đến việc gọi `sync_legal_assets` tải đè lên chính nó thành `.md/legal_docs/` và báo lỗi thiếu registry cục bộ.
2. `check_hub_import_depth.py` có thể gặp lỗi mã hóa ký tự emoji trên Windows nếu chưa reconfigure stdout, đồng thời có nguy cơ quét vào các thư mục `.agents/` và `.md/`.
3. `scripts/sync_spoke.py` thiếu cờ `-b` / `--bootstrap` để gọi trực tiếp `SpokeBootstrapper`.
4. Một số template vẫn còn `sys.path.insert`.

### Hành vi mong muốn (Desired behavior)
1. Thêm phương thức `is_master_legal_corpus()` trong `LegalKnowledgeSyncOrchestrator`: nếu spoke hiện tại là Master Legal Corpus (`legal_registry.yaml` tồn tại ở root và `project_type == 'Pháp điển'`), in thông báo giữ nguyên Master Corpus và bỏ qua copy assets.
2. Gia cố `check_hub_import_depth.py` với cấu hình mã hóa stdout UTF-8 an toàn và danh sách exclude đầy đủ (`.agents`, `.md`, `.venv`, `__pycache__`).
3. Bổ sung tham số `--bootstrap` / `-b` vào `scripts/sync_spoke.py` để tự động kích hoạt `SpokeBootstrapper.bootstrap()`.
4. Đảm bảo toàn bộ template scripts vượt qua kiểm tra của `check_spoke_cleanliness.py`.

### Các Interface & Kiểu dữ liệu chính (Key interfaces)
- `scripts/spoke/sync/sdk_inspector.py`: `LegalKnowledgeSyncOrchestrator.is_master_legal_corpus()`
- `scripts/sync_spoke.py`: Parser argument `--bootstrap` / `-b`
- `scripts/spoke/check_hub_import_depth.py`: Scoped scan & UTF-8 reconfigure

### Tiêu chuẩn nghiệm thu (Acceptance criteria)
- [ ] `LegalKnowledgeSyncOrchestrator` nhận diện chính xác Master Legal Corpus và không tạo folder rác `.md/legal_docs/`.
- [ ] `sync_spoke.py --bootstrap` / `-b` hoạt động trơn tru với `SpokeBootstrapper`.
- [ ] `check_hub_import_depth.py` chạy không lỗi trên Windows PowerShell.
- [ ] Toàn bộ test suite đồng bộ (`tests/test_spoke_synchronizer.py`...) pass 100%.

### Phạm vi loại trừ (Out of scope)
- Không thay đổi cấu trúc dữ liệu OKF v2.4 hay logic parse AST của `ccba-legal-intel`.

### Đề xuất chế độ thực thi (Recommended Execution Strategy)
- **Mức độ phức tạp**: Gọn nhẹ / Cục bộ trong `scripts/`
- **Khuyến nghị thực thi**:
  - `[x]` 🟢 **Standard** (`/ccba-implement`): Triển khai tuần tự, scoped tests.
  - `[ ]` 🟣 **Deep Reasoning** (`/boost`): Điều tra chuyên sâu root-cause / phản biện đa vòng.
  - `[ ]` 🔵 **Multi-Agent Orchestration** (`/ccba-teamwork` hoặc `/teamwork-preview`): Phân rã Seams và chạy đa tác nhân song song.
