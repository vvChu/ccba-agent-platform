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

*Lưu ý (ADR 0046):* Lệnh `--all` mặc định loại trừ các Spoke Cá Nhân (`is_sandbox: true`) để tiết kiệm tài nguyên máy chủ. Sử dụng thêm cờ `--include-sandboxes` khi muốn đồng bộ toàn bộ.

---

### 📁 Chế độ 3: Đồng Bộ Toàn Bộ Cho Spoke Hiện Tại (Tại Spoke)
Định vị Hub Path qua `.md/workspace_context.yaml` hoặc biến môi trường `CCBA_HUB_PATH` và tiến hành đồng bộ:

```powershell
# 1. Chế độ Safe-by-Default (Mặc định: Hiện bảng Preview -> Hỏi xác nhận [y/N]):
python [hub_path]\scripts\sync_spoke.py --spoke .

# 2. Chế độ Xem trước mô phỏng thuần túy:
python [hub_path]\scripts\sync_spoke.py --spoke . --dry-run

# 3. Chế độ Áp dụng ngay (Non-interactive / CI):
python [hub_path]\scripts\sync_spoke.py --spoke . --apply

# 4. Bỏ qua cảnh báo uncommitted changes nếu cần:
python [hub_path]\scripts\sync_spoke.py --spoke . --apply --force
```

*Lưu ý:* Cơ chế **Selective Merge** sẽ tự động bảo vệ nguyên vẹn 100% các file workflows/skills nội bộ do Spoke tự viết (`🛡️ PRESERVED`).

---

### ⚡ Chế độ 4: Tải Bổ Sung Một Kỹ Năng / Workflow Cụ Thể (On-Demand)
Khi Agent cần bổ sung 1 kỹ năng cụ thể (ví dụ: `excalidraw-diagram`, `sharepoint-iac`) để xử lý yêu cầu tức thì của User:
1. Agent xin sự cho phép từ người dùng: *"Tôi cần tải bổ sung kỹ năng [tên-kỹ-năng] từ Hub, bạn có đồng ý không?"*
2. Sau khi người dùng đồng ý, chạy lệnh:
   ```powershell
   python [hub_path]\scripts\sync_spoke.py --spoke . --sync-item [tên-kỹ-năng] --apply
   ```
3. Hệ thống sẽ tự động nạp kỹ năng mới (Auto-Discovery) mà không cần khởi động lại.

---

### ⏪ Chế độ 5: Hoàn Tác & Quản Lý Snapshot Sao Lưu (Rollback & Undo)
Khi cần khôi phục lại cấu hình `.agents/` về trạng thái trước khi đồng bộ:

```powershell
# 1. Xem danh sách các bản snapshot sao lưu đã tạo:
python [hub_path]\scripts\sync_spoke.py --spoke . --list-backups

# 2. Khôi phục từ bản sao lưu gần nhất:
python [hub_path]\scripts\sync_spoke.py --spoke . --rollback
```

---

## 📋 Báo Cáo Kết Quả & Dọn Dẹp:
1. **Tổng kết đồng bộ:** In bảng báo cáo tổng kết chi tiết gồm số lượng: `🟢 NEW`, `🔄 UPDATED`, `⚪ UNCHANGED`, `🛡️ PRESERVED`.
2. **Snapshot sao lưu:** Hiển thị đường dẫn bản sao lưu đã tạo (ví dụ: `.md/backups/agents_backup_20260822_120000`).
3. **Đồng bộ Pre-commit Hooks (ADR 0044 §7):** Nếu Spoke là Python project, tự động cập nhật `check_hub_import_depth.py` từ Hub:
   ```powershell
   Copy-Item "$hub\scripts\spoke\check_hub_import_depth.py" -Destination ".\scripts\check_hub_import_depth.py" -Force
   ```
4. **Rà soát Kỹ năng Mồ côi (Orphaned / Deprecated Skills):** Nếu Hub đã xóa bỏ hoặc đổi tên một Skill cũ nhưng tại `.agents/skills/` của Spoke vẫn còn file cũ, Agent chủ động thông báo cho người dùng để xác nhận dọn dẹp các kỹ năng không còn nằm trong `catalog.yaml`.
5. **Kiểm tra sức khỏe tổng thể:** Tại Hub, có thể chạy lại lệnh `python scripts\ccba_platform_cli.py spoke-status` để xác nhận toàn bộ hệ sinh thái đã xanh (Synced & Healthy).

