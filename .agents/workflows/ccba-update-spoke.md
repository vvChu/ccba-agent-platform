---
description: Đồng bộ hóa các kỹ năng, quy trình và cập nhật phiên bản giữa Hub và
  các Spoke (đơn lẻ hoặc hàng loạt)
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
- BIM
- Tác vụ Admin
- Pháp điển
bundle: _core
disable-model-invocation: true
command: /ccba-update-spoke
triggers:
- update spoke
- đồng bộ hub
- lấy lệnh mới
- cập nhật dự án
- sync all
- sync all spokes
- đồng bộ toàn bộ spoke
- spoke status
- kiểm tra spoke
---
# Cập Nhật & Đồng Bộ Hóa CCBA Spoke Workspace (/ccba-update-spoke)

Workflow này cho phép đồng bộ hóa các bản cập nhật mới nhất (kịch bản lệnh, kỹ năng, hiến pháp `AGENTS.md`, rào chắn test) từ trung tâm **CCBA Agent Platform (Hub)** sang các dự án **Spoke**, hỗ trợ cả đồng bộ đơn lẻ, tải On-Demand và đồng bộ hàng loạt toàn bộ hệ sinh thái.

Quy trình áp dụng cơ chế **Mặc định An toàn (Safe-by-Default)** 2 pha (Two-Phase Execution), bảo vệ Git working tree và tự động tạo snapshot sao lưu để có thể hoàn tác tức thì.

---

## 🛡️ Nguyên Tắc Safe-by-Default (Mặc định An toàn):
1. **Pha 1 (Xem trước Preview):** Lệnh mặc định luôn chạy mô phỏng trước, phân loại và in bảng kiểm tra 4 trạng thái tệp:
   - `🟢 NEW`: Kỹ năng / quy trình mới từ Hub chưa có tại Spoke.
   - `🔄 UPDATED`: Kỹ năng / quy trình đã có sự thay đổi nội dung từ Hub.
   - `⚪ UNCHANGED`: Tệp hoàn toàn trùng khớp, không cần cập nhật.
   - `🛡️ PRESERVED`: Kỹ năng / quy trình tùy biến nội bộ của Spoke, được bảo toàn 100%.
2. **Pha 2 (Xác nhận Thực thi):** Sau khi xem bảng Preview, người dùng xác nhận `[y/N]` để áp dụng, hoặc truyền cờ `--apply` / `-y` khi chạy script tự động.
3. **Git Working Tree Guard:** Tự động kiểm tra `git status`. Nếu thư mục `.agents/` đang có uncommitted changes, hệ thống sẽ cảnh báo và yêu cầu commit/stash trước khi sync (hoặc dùng `--force` để bỏ qua).
4. **Snapshot Backup & Rollback:** Tự động sao lưu thư mục `.agents/` hiện tại vào `.md/backups/agents_backup_<timestamp>/` trước khi sửa đổi, cho phép hoàn tác 1 chạm qua cờ `--rollback`.

---

## 🎯 Khi Nào Dùng:
1. **Tại Hub:** Khi muốn kiểm tra độ trễ phiên bản hoặc đồng bộ 1 chạm cho tất cả các Spoke đang kết nối (`--all`).
2. **Tại Spoke:** Khi muốn cập nhật toàn bộ Skills/Workflows của dự án hiện tại theo đúng nghiệp vụ (`project_type`).
3. **Tại Spoke (On-Demand):** Khi Agent phát hiện cần một kỹ năng trên Hub nhưng Spoke chưa tải về (Lazy Loading).
4. **Khi Cần Hoàn Tác:** Khi muốn khôi phục lại trạng thái `.agents/` trước lần đồng bộ gần nhất (`--rollback`).
5. **Đóng Vòng Hậu Hợp Nhất:** Khi PR đóng góp từ Spoke vừa được merge vào Hub (Bước 7 của `/ccba-contribute-to-hub`).

---

## 🛠️ Các Chế Độ Thực Hiện:

### 📊 Chế độ 1: Kiểm Tra Trạng Thái Sức Khỏe & Độ Lệch Phiên Bản (Tại Hub)
Trước khi đồng bộ, kiểm tra xem các Spoke đang kết nối có bị thiếu hoặc quá hạn đồng bộ (> 30 ngày) hay không:
```powershell
python scripts\ccba_platform_cli.py spoke-status
```

---

### 🌐 Chế độ 2: Đồng Bộ Hàng Loạt Toàn Bộ Spoke Đang Đăng Ký (Từ Hub)
Tự động duyệt qua danh sách trong Hub Registry (`.md/data/spoke_registry.yaml`) và đồng bộ lần lượt tất cả Spoke còn hoạt động:

```powershell
# 1. Xem trước mô phỏng (Pha 1):
python scripts\sync_spoke.py --all --dry-run

# 2. Thực thi đồng bộ chính thức (Pha 2 - Mặc định bỏ qua Sandbox cá nhân):
python scripts\sync_spoke.py --all --apply

# 3. Đồng bộ bao gồm cả Spoke Cá Nhân (ADR 0046):
python scripts\sync_spoke.py --all --apply --include-sandboxes
```

*Lưu ý (ADR 0046):* Lệnh `--all` mặc định loại trừ các Spoke Cá Nhân (`is_sandbox: true`). Thêm `--include-sandboxes` để đồng bộ toàn bộ.

---

### 📁 Chế độ 3: Đồng Bộ Toàn Bộ Cho Spoke Hiện Tại (Tại Spoke)
Định vị Hub Path qua `.md/workspace_context.yaml` hoặc biến môi trường `CCBA_HUB_PATH` và tiến hành đồng bộ:

```powershell
# 1. Chế độ Safe-by-Default (Mặc định: Hiện bảng Preview -> Hỏi xác nhận [y/N]):
python [hub_path]\scripts\sync_spoke.py --spoke .

# 2. Chế độ Xem trước mô phỏng:
python [hub_path]\scripts\sync_spoke.py --spoke . --dry-run

# 3. Chế độ Áp dụng ngay (Non-interactive / CI):
python [hub_path]\scripts\sync_spoke.py --spoke . --apply

# 4. Bỏ qua cảnh báo uncommitted changes:
python [hub_path]\scripts\sync_spoke.py --spoke . --apply --force
```

*Lưu ý:* Cơ chế **Selective Merge** sẽ tự động bảo vệ nguyên vẹn 100% các file workflows/skills nội bộ của Spoke (`🛡️ PRESERVED`).

---

### ⚡ Chế độ 4: Tải Bổ Sung Một Kỹ Năng / Workflow Cụ Thể (On-Demand)
Khi Agent cần bổ sung 1 kỹ năng cụ thể (ví dụ: `excalidraw-diagram`, `sharepoint-iac`) để xử lý yêu cầu tức thì:
```powershell
python [hub_path]\scripts\sync_spoke.py --spoke . --sync-item [tên-kỹ-năng] --apply
```
Hệ thống sẽ tự động nạp kỹ năng mới (Auto-Discovery) mà không cần khởi động lại.

---

### ⏪ Chế độ 5: Hoàn Tác & Quản Lý Snapshot Sao Lưu (Rollback & Undo)
Khôi phục lại cấu hình `.agents/` về trạng thái trước khi đồng bộ:

```powershell
# 1. Xem danh sách các bản snapshot sao lưu:
python [hub_path]\scripts\sync_spoke.py --spoke . --list-backups

# 2. Khôi phục từ bản sao lưu gần nhất:
python [hub_path]\scripts\sync_spoke.py --spoke . --rollback
```

---

### ⚖️ Chế độ 6: Đồng Bộ Tri Thức Pháp Lý Chuẩn OKF v2.4 (Two-Tier Legal Sync — ADR 0050)

Cơ chế phân luồng dữ liệu thông minh giúp đồng bộ tri thức pháp luật chuẩn hóa mà không làm phình dung lượng của các Spoke không liên quan:

#### 1. 🟢 Tự động đồng bộ cho các Spoke liên quan:
* **Đối tượng áp dụng:** Các Spoke thuộc phân hệ `Pháp điển`, `Thẩm tra thiết kế`, `Kiểm định`, `PCCC`, `Tư vấn pháp lý` hoặc dự án có thư mục `legal_docs/` / `legal_registry.yaml`.
* **Hành vi tự động:** Lệnh `sync_spoke.py` tự động kích hoạt `LegalKnowledgeSyncOrchestrator` để:
  - Quét và sao chép các gói văn bản OKF v2.4 chuẩn từ `ccba-legal-knowledge` (Tier 1 Offline siêu tốc) hoặc Google Drive Vault (Tier 2 Cloud).
  - Tự động sao lưu bản `.bak` và thực hiện **Non-Destructive Additive Registry Merge** cho `legal_registry.yaml` (bảo toàn 100% các ghi chú và trường dữ liệu tùy biến riêng của Spoke).
* **Lệnh kích hoạt độc lập hoặc ép buộc đồng bộ:**
  ```powershell
  python -m ccba_legal sync --pull-latest
  ```

#### 2. 💡 Khuyến nghị Zero-Bloat cho các Spoke còn lại (Phần mềm, BIM, Admin):
* **Nguyên tắc:** Hệ thống **mặc định bỏ qua** việc tải toàn bộ kho văn bản luật hàng chục GB để đảm bảo Spoke luôn tinh gọn và khởi động siêu tốc.
* **Tra cứu On-Demand khi cần:** Khi dự án phần mềm hoặc BIM cần tra cứu một văn bản quy chuẩn cụ thể, kỹ sư chỉ cần kéo riêng văn bản đó:
  ```powershell
  # Tải lẻ 1 văn bản cụ thể:
  python -m ccba_legal sync --doc <doc_id>    # Ví dụ: --doc LXD-2025 hoặc --doc ND-207-2026
  ```
* **Hoặc tra cứu qua AI Gateway:** Sử dụng `ccba-ai` để truy vấn ngữ nghĩa (RAG) trực tiếp qua endpoint LiteLLM trên Server Spark mà không cần lưu file cục bộ.

---

## 📋 Báo Cáo Kết Quả & Dọn Dẹp:
1. **Tổng kết đồng bộ kỹ năng:** Báo cáo chi tiết: `🟢 NEW`, `🔄 UPDATED`, `⚪ UNCHANGED`, `🛡️ PRESERVED`.
2. **Tổng kết tri thức pháp lý (ADR 0050):** Hiển thị số lượng gói OKF v2.4 đã đồng bộ hoặc khuyến nghị Zero-Bloat tương ứng.
3. **Snapshot sao lưu:** Hiển thị đường dẫn bản sao lưu đã tạo (ví dụ: `.md/backups/agents_backup_<timestamp>/`).
4. **Đồng bộ Pre-commit Hooks & Cleanliness Gate (ADR 0044 §7):** Cập nhật guardrail scripts từ Hub:
   ```powershell
   Copy-Item "$hub\scripts\spoke\check_hub_import_depth.py" -Destination ".\scripts\check_hub_import_depth.py" -Force
   Copy-Item "$hub\scripts\spoke\check_spoke_cleanliness.py" -Destination ".\scripts\check_spoke_cleanliness.py" -Force
   ```
5. **Kiểm tra Script Budget & Cleanliness:** Chạy `python .\scripts\check_spoke_cleanliness.py`.
6. **Rà soát Kỹ năng Mồ côi:** Dọn dẹp các kỹ năng không còn nằm trong `catalog.yaml`.
7. **Kiểm định Hồi quy & Packages (Hậu Đóng Góp):** Nếu Spoke vừa đóng góp tool, chạy `pip install -e "[hub_path]\packages\[pkg]"` và chạy bộ test cục bộ (ví dụ: `python scripts\validate_legal_spoke.py`) để đảm bảo không gãy chức năng.
8. **Kiểm tra sức khỏe tổng thể:** Chạy `python scripts\ccba_platform_cli.py spoke-status` để xác nhận trạng thái xanh.

