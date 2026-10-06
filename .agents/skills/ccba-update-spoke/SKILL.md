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
tier: kernel
disable-model-invocation: true
command: /ccba-update-spoke
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
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
---

# Cập Nhật & Đồng Bộ Hóa CCBA Spoke Workspace (/ccba-update-spoke)

Kỹ năng này đồng bộ hóa các bản cập nhật mới nhất (kịch bản lệnh, kỹ năng, hiến pháp `AGENTS.md`, rào chắn test) từ **CCBA Agent Platform (Hub)** sang các dự án **Spoke**, hỗ trợ đồng bộ đơn lẻ, tải On-Demand và đồng bộ hàng loạt.
Quy trình áp dụng cơ chế **Safe-by-Default** 2 pha (Two-Phase Execution), bảo vệ Git working tree và tự động tạo snapshot sao lưu để có thể hoàn tác tức thì.

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`seam-exempt`** (SOP downstream đồng bộ Hub sang Spoke). Skill hướng dẫn quy trình đồng bộ hóa kỹ năng, hiến pháp và rào chắn vệ sinh hai pha Safe-by-Default; hai parser đồng bộ (`scripts/ccba_platform_cli.py sync-spoke` cho các cờ cơ bản và wrapper `scripts/sync_spoke.py` cho rollback/backup/dirty) vận hành song song trên cùng engine `scripts/spoke/sync_project.py`. Không phụ thuộc Seam Contract ứng dụng cụ thể.

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

> [!NOTE]
> Lệnh `/ccba-update-spoke` chỉ phục vụ đồng bộ theo chiều **Downstream (Hub $\rightarrow$ Spoke)**. Nếu bạn muốn kiểm tra và đồng bộ tính năng từ các kho chứa GitHub thượng nguồn về Hub, vui lòng sử dụng lệnh độc lập `/ccba-sync-upstream`.

---

## 🛠️ Các Chế Độ Thực Hiện:

### 📊 Chế độ 1: Kiểm Tra Trạng Thái Sức Khỏe & Độ Lệch Phiên Bản (Tại Hub)
```bash
# POSIX (Linux / macOS / WSL):
python scripts/ccba_platform_cli.py spoke-status

# PowerShell (Windows):
python scripts\ccba_platform_cli.py spoke-status
```

### 🌐 Chế độ 2: Đồng Bộ Hàng Loạt Toàn Bộ Spoke Đang Đăng Ký (Từ Hub)
```bash
# 1. Xem trước mô phỏng (Pha 1) | 2. Đồng bộ chính thức (Pha 2, bỏ qua sandbox):
python scripts/sync_spoke.py --all --dry-run
python scripts/sync_spoke.py --all --apply

# 3. Đồng bộ bao gồm cả Spoke Cá Nhân (ADR 0046):
python scripts/sync_spoke.py --all --apply --include-sandboxes

# 4. Đồng bộ kèm xác thực tự động (ADR-0058 Hard Completion Lock):
python scripts/sync_spoke.py --all --apply --verify
```

### 📁 Chế độ 3: Đồng Bộ Toàn Bộ Cho Spoke Hiện Tại (Tại Spoke)
> [!TIP]
> Sử dụng biến môi trường `$CCBA_HUB_PATH` (POSIX) hoặc `$env:CCBA_HUB_PATH` (PowerShell) để đảm bảo tính độc lập trạng thái máy (Machine-State Decoupling — ADR-0061).

```bash
# POSIX (Linux / macOS / WSL):
# Safe-by-Default (Hiện Preview -> Hỏi xác nhận [y/N]):
python "$CCBA_HUB_PATH/scripts/sync_spoke.py" --spoke .

# Áp dụng ngay (Non-interactive / CI) hoặc Bỏ qua cảnh báo uncommitted (--force hoặc --ignore-dirty):
python "$CCBA_HUB_PATH/scripts/sync_spoke.py" --spoke . --apply
python "$CCBA_HUB_PATH/scripts/sync_spoke.py" --spoke . --apply --force

# Đồng bộ nạp sẵn (Bootstrap editable links tới packages Hub — ADR-0044) và kiểm thử Spoke (--verify):
python "$CCBA_HUB_PATH/scripts/sync_spoke.py" --spoke . --apply --bootstrap --verify
```

```powershell
# PowerShell (Windows):
# Safe-by-Default (Hiện Preview -> Hỏi xác nhận [y/N]):
python "$env:CCBA_HUB_PATH\scripts\sync_spoke.py" --spoke .

# Áp dụng ngay (Non-interactive / CI) hoặc Bỏ qua cảnh báo uncommitted:
python "$env:CCBA_HUB_PATH\scripts\sync_spoke.py" --spoke . --apply
python "$env:CCBA_HUB_PATH\scripts\sync_spoke.py" --spoke . --apply --force

# Đồng bộ nạp sẵn (Bootstrap editable links) và kiểm thử Spoke:
python "$env:CCBA_HUB_PATH\scripts\sync_spoke.py" --spoke . --apply --bootstrap --verify
```

### ⚡ Chế độ 4: Tải Bổ Sung Kỹ Năng Cụ Thể (On-Demand / Lazy Loading)
> [!NOTE]
> Khi sử dụng `--sync-item`, hệ thống chỉ sao chép duy nhất mục kỹ năng được chỉ định và thực hiện Non-Destructive Merge cho `AGENTS.md`, giữ nguyên các kỹ năng khác.

```bash
# POSIX:
python "$CCBA_HUB_PATH/scripts/sync_spoke.py" --spoke . --sync-item [tên-kỹ-năng] --apply

# PowerShell:
python "$env:CCBA_HUB_PATH\scripts\sync_spoke.py" --spoke . --sync-item [tên-kỹ-năng] --apply
```

### ⏪ Chế độ 5: Hoàn Tác & Quản Lý Snapshot Sao Lưu (Rollback & Undo)
```bash
# POSIX:
# Liệt kê danh sách sao lưu snapshot:
python "$CCBA_HUB_PATH/scripts/sync_spoke.py" --spoke . --list-backups

# Hoàn tác về snapshot gần nhất (--rollback hoặc --undo):
python "$CCBA_HUB_PATH/scripts/sync_spoke.py" --spoke . --rollback
```

```powershell
# PowerShell:
python "$env:CCBA_HUB_PATH\scripts\sync_spoke.py" --spoke . --list-backups
python "$env:CCBA_HUB_PATH\scripts\sync_spoke.py" --spoke . --rollback
```

### ⚖️ Chế độ 6: Đồng Bộ Tri Thức Pháp Lý Chuẩn OKF v2.4 (Two-Tier Legal Sync — ADR 0050)
- **💡 Mặc định Zero-Bloat (Reference-Only):** Mặc định Spoke không bị phình to dữ liệu (không copy các gói tệp văn bản lớn). Spoke tra cứu pháp điển trực tiếp từ Hub hoặc gọi RAG qua `ccba-ai` trên LiteLLM Spark.
- **📦 Kéo gói pháp lý vật lý (`--pull-assets`):** Dành riêng cho các Spoke chuyên trách pháp điển cần dữ liệu tĩnh ngoại tuyến:
  ```bash
  # POSIX:
  python "$CCBA_HUB_PATH/scripts/sync_spoke.py" --spoke . --apply --pull-assets
  ```
  ```powershell
  # PowerShell:
  python "$env:CCBA_HUB_PATH\scripts\sync_spoke.py" --spoke . --apply --pull-assets
  ```
- **Lệnh đồng bộ pháp lý độc lập:** `python -m ccba_legal sync --pull-latest` hoặc tải lẻ: `python -m ccba_legal sync --doc <doc_id>`.

---

## ⚙️ Các Cờ Dòng Lệnh & Biến Môi Trường Chi Tiết

| Cờ CLI / Biến | Tên đầy đủ / Bí danh | Ý nghĩa & Hành vi |
| :--- | :--- | :--- |
| `--apply` | `-y` | Áp dụng thay đổi trực tiếp lên đĩa (bỏ qua bước hỏi xác nhận TTY). |
| `--force` | `--ignore-dirty` | Bỏ qua cảnh báo uncommitted changes trong thư mục `.agents/`. |
| `--bootstrap` | `-b` | Tự động cài đặt liên kết editable (`pip install -e`) từ Hub monorepo cho Spoke venv. |
| `--verify` | | Chạy kiểm tra tự động tại Spoke hậu đồng bộ: `check_spoke_cleanliness.py`, `check_hub_import_depth.py`, và `pytest` (nếu có test suite; nếu không có test sẽ trả về 0 an toàn). |
| `--rollback` | `--undo` | Khôi phục thư mục `.agents/` từ snapshot sao lưu gần nhất. |
| `--pull-assets` | | Kéo bản sao vật lý các gói tri thức pháp lý OKF v2.4 về Spoke (mặc định: `False`). |
| `--allow-stale-catalog` | | Cho phép thực thi `--apply` ngay cả khi `catalog.yaml` chưa được biên dịch lại (Emergency Override). |
| `CCBA_SKIP_GIT_PULL` | Env var (`=1`) | Bỏ qua bước tự động gọi `git pull` trên repo Hub khi thực thi đồng bộ (chỉ nhận đúng giá trị `"1"`; gán khác `"1"` như `"true"` vẫn sẽ kích hoạt pull). |

---

## 📋 Báo Cáo Kết Quả & Dọn Dẹp:
1. **Báo cáo đồng bộ:** Báo cáo chi tiết: `🟢 NEW`, `🔄 UPDATED`, `⚪ UNCHANGED`, `🛡️ PRESERVED`.
2. **Tổng kết tri thức pháp lý (ADR 0050):** Hiển thị số lượng gói OKF v2.4 đã đồng bộ (nếu bật `--pull-assets`).
3. **Đồng bộ Pre-commit Hooks & Cleanliness Gate (Tự động hóa 100% qua `--apply` — ADR 0044 §7):**
   * Lệnh `sync_spoke.py --apply` tự động đồng bộ và kích hoạt toàn bộ guardrails bảo vệ tại Spoke:
     - `.githooks/pre-commit` (Khiên bảo vệ quét secret/credentials tự động của Maskara v1.2.0, tự động cấu hình `core.hooksPath=.githooks`, `chmod +x`, và `.gitattributes` chuẩn hóa LF)
     - `scripts/safe_pytest.py` (Test runner an toàn)
     - `scripts/check_hub_import_depth.py` (Kiểm soát độ sâu import)
     - `scripts/check_spoke_cleanliness.py` (Rào chắn cleanliness & script budget)
4. **Kiểm tra Script Budget & Cleanliness:** Chạy `python scripts/check_spoke_cleanliness.py`.
5. **Kiểm định Hồi quy & Packages (Hậu Đóng Góp):** Chạy `pip install -e "$CCBA_HUB_PATH/packages/[pkg]"` và chạy test cục bộ (`pytest`).
6. **Kiểm tra sức khỏe tổng thể:** Chạy `python scripts/ccba_platform_cli.py spoke-status` xác nhận trạng thái xanh.


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/upstream_sync_guide.md` | Tài liệu chỉ dẫn chuyển tiếp (Pointer Guide). Để trinh sát và kéo cập nhật từ GitHub thượng nguồn về Hub, sử dụng lệnh độc lập `/ccba-sync-upstream`. |

