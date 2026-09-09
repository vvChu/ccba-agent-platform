---
name: ccba-update-spoke
description: Đồng bộ hóa các kỹ năng và cập nhật phiên bản giữa Hub và các Spoke (đơn
  lẻ hoặc hàng loạt)
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
gpi:
  s: 3.0
  k: 2.0
  a: 2.0
  p: 1.0
user-invocable: true
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
- ccba-sync-upstream
- sync-upstream
---

# Cập Nhật & Đồng Bộ Hóa CCBA Spoke Workspace (/ccba-update-spoke)

Kỹ năng này đồng bộ hóa các bản cập nhật mới nhất (kịch bản lệnh, kỹ năng, hiến pháp `AGENTS.md`, rào chắn test) từ **CCBA Agent Platform (Hub)** sang các dự án **Spoke**, hỗ trợ đồng bộ đơn lẻ, tải On-Demand và đồng bộ hàng loạt.
Quy trình áp dụng cơ chế **Safe-by-Default** 2 pha (Two-Phase Execution), bảo vệ Git working tree và tự động tạo snapshot sao lưu để có thể hoàn tác tức thì.

---

## 🛡️ Nguyên Tắc Safe-by-Default (Mặc định An toàn):
1. **Pha 1 (Xem trước Preview):** Lệnh mặc định luôn chạy mô phỏng trước, phân loại và in bảng kiểm tra 4 trạng thái tệp:
   - `🟢 NEW`: Kỹ năng mới từ Hub chưa có tại Spoke.
   - `🔄 UPDATED`: Kỹ năng đã có sự thay đổi từ Hub.
   - `⚪ UNCHANGED`: Tệp hoàn toàn trùng khớp, không cần cập nhật.
   - `🛡️ PRESERVED`: Kỹ năng tùy biến nội bộ của Spoke, được bảo toàn 100%.
2. **Pha 2 (Xác nhận Thực thi):** Người dùng xác nhận `[y/N]` để áp dụng, hoặc truyền cờ `--apply` / `-y`.
3. **Git Working Tree Guard:** Tự động kiểm tra `git status`. Nếu thư mục `.agents/` có uncommitted changes, hệ thống cảnh báo và yêu cầu commit/stash trước khi sync (hoặc dùng `--force`).
4. **Snapshot Backup & Rollback:** Tự động sao lưu thư mục `.agents/` vào `.md/backups/agents_backup_<timestamp>/` trước khi sửa đổi, cho phép hoàn tác qua cờ `--rollback`.

---

## 🎯 Khi Nào Dùng:
1. **Tại Hub:** Kiểm tra độ trễ phiên bản hoặc đồng bộ 1 chạm cho tất cả các Spoke kết nối (`--all`).
2. **Tại Spoke:** Cập nhật toàn bộ Skills của dự án hiện tại theo đúng nghiệp vụ (`project_type`).
3. **Tại Spoke (On-Demand):** Tải nhanh kỹ năng còn thiếu trên Hub (Lazy Loading).
4. **Khi Cần Hoàn Tác:** Khôi phục trạng thái `.agents/` trước lần đồng bộ gần nhất (`--rollback`).
5. **Đóng Vòng Hậu Hợp Nhất:** Khi PR đóng góp từ Spoke vừa được merge vào Hub (Bước 7 của `/ccba-contribute-to-hub`).

---

## 🛠️ Các Chế Độ Thực Hiện:

### 📊 Chế độ 1: Kiểm Tra Trạng Thái Sức Khỏe & Độ Lệch Phiên Bản (Tại Hub)
```powershell
python scripts\ccba_platform_cli.py spoke-status
```

### 🌐 Chế độ 2: Đồng Bộ Hàng Loạt Toàn Bộ Spoke Đang Đăng Ký (Từ Hub)
```powershell
# 1. Xem trước mô phỏng (Pha 1) | 2. Đồng bộ chính thức (Pha 2, bỏ qua sandbox):
python scripts\sync_spoke.py --all --dry-run
python scripts\sync_spoke.py --all --apply
# 3. Đồng bộ bao gồm cả Spoke Cá Nhân (ADR 0046):
python scripts\sync_spoke.py --all --apply --include-sandboxes
```

### 📁 Chế độ 3: Đồng Bộ Toàn Bộ Cho Spoke Hiện Tại (Tại Spoke)
```powershell
# Safe-by-Default (Hiện Preview -> Hỏi xác nhận [y/N]):
python [hub_path]\scripts\sync_spoke.py --spoke .
# Áp dụng ngay (Non-interactive / CI) hoặc Bỏ qua cảnh báo uncommitted:
python [hub_path]\scripts\sync_spoke.py --spoke . --apply
python [hub_path]\scripts\sync_spoke.py --spoke . --apply --force
# Đồng bộ nạp sẵn (Preload bootstrap skills & packages):
python [hub_path]\scripts\sync_spoke.py --spoke . --apply --bootstrap
```

### ⚡ Chế độ 4: Tải Bổ Sung Kỹ Năng Cụ Thể (On-Demand)
```powershell
python [hub_path]\scripts\sync_spoke.py --spoke . --sync-item [tên-kỹ-năng] --apply
```

### ⏪ Chế độ 5: Hoàn Tác & Quản Lý Snapshot Sao Lưu (Rollback & Undo)
```powershell
python [hub_path]\scripts\sync_spoke.py --spoke . --list-backups
python [hub_path]\scripts\sync_spoke.py --spoke . --rollback
```

### ⚖️ Chế độ 6: Đồng Bộ Tri Thức Pháp Lý Chuẩn OKF v2.4 (Two-Tier Legal Sync — ADR 0050)
- **🟢 Tự động đồng bộ cho Spoke liên quan (Pháp điển, Thẩm tra, Kiểm định, PCCC):** Quét và sao chép gói OKF v2.4 từ Tier 1 (Offline) hoặc Tier 2 (Cloud Drive Vault), thực hiện Non-Destructive Additive Registry Merge. Lệnh độc lập: `python -m ccba_legal sync --pull-latest`.
- **💡 Zero-Bloat cho Spoke còn lại (Phần mềm, BIM, Admin):** Mặc định bỏ qua để giữ repo tinh gọn. Khi cần tra cứu tải lẻ: `python -m ccba_legal sync --doc <doc_id>` hoặc truy vấn RAG qua `ccba-ai` trên LiteLLM Spark.

---

## 📋 Báo Cáo Kết Quả & Dọn Dẹp:
1. **Báo cáo đồng bộ:** Báo cáo chi tiết: `🟢 NEW`, `🔄 UPDATED`, `⚪ UNCHANGED`, `🛡️ PRESERVED`.
2. **Tổng kết tri thức pháp lý (ADR 0050):** Hiển thị số lượng gói OKF v2.4 đã đồng bộ.
3. **Đồng bộ Pre-commit Hooks & Cleanliness Gate (ADR 0044 §7):**
   ```powershell
   Copy-Item "$hub\scripts\spoke\check_hub_import_depth.py" -Destination ".\scripts\check_hub_import_depth.py" -Force
   Copy-Item "$hub\scripts\spoke\check_spoke_cleanliness.py" -Destination ".\scripts\check_spoke_cleanliness.py" -Force
   ```
4. **Kiểm tra Script Budget & Cleanliness:** Chạy `python .\scripts\check_spoke_cleanliness.py`.
5. **Kiểm định Hồi quy & Packages (Hậu Đóng Góp):** Chạy `pip install -e "[hub_path]\packages\[pkg]"` và chạy test cục bộ (ví dụ: `pytest` hoặc `python scripts\validate_legal_spoke.py` đối với Spoke Pháp điển).
6. **Kiểm tra sức khỏe tổng thể:** Chạy `ccba-spoke status` (hoặc `python "[hub_path]\scripts\ccba_platform_cli.py" spoke-status`) xác nhận trạng thái xanh.


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/upstream_sync_guide.md` | Hướng dẫn kiểm tra và kéo cập nhật tính năng mới từ Hub về dự án Spoke |

