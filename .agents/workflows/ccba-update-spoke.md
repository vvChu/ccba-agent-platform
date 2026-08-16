---
description: Đồng bộ hóa các kỹ năng, quy trình và cập nhật phiên bản giữa Hub và các Spoke (đơn lẻ hoặc hàng loạt)
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
disable-model-invocation: true
---
# Cập Nhật & Đồng Bộ Hóa CCBA Spoke Workspace (/ccba-update-spoke)

Workflow này cho phép đồng bộ hóa các bản cập nhật mới nhất (kịch bản lệnh, kỹ năng, hiến pháp `AGENTS.md`, rào chắn test) từ trung tâm **CCBA Agent Platform (Hub)** sang các dự án **Spoke**, hỗ trợ cả đồng bộ đơn lẻ, tải On-Demand và đồng bộ hàng loạt toàn bộ hệ sinh thái.

---

## 🎯 Khi Nào Dùng:
1. **Tại Hub:** Khi muốn kiểm tra độ trễ phiên bản hoặc đồng bộ 1 chạm cho tất cả các Spoke đang kết nối (`--all`).
2. **Tại Spoke:** Khi muốn cập nhật toàn bộ Skills/Workflows của dự án hiện tại theo đúng nghiệp vụ (`project_type`).
3. **Tại Spoke (On-Demand):** Khi Agent phát hiện cần một kỹ năng trên Hub nhưng Spoke chưa tải về (Lazy Loading).

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
# 1. (Khuyên dùng) Xem trước mô phỏng không ghi file:
python scripts\sync_spoke.py --all --dry-run

# 2. Thực thi đồng bộ chính thức:
python scripts\sync_spoke.py --all
```

---

### 📁 Chế độ 3: Đồng Bộ Toàn Bộ Cho Spoke Hiện Tại (Tại Spoke)
Định vị Hub Path qua `.md/workspace_context.yaml` hoặc biến môi trường `CCBA_HUB_PATH` và tiến hành đồng bộ:

```powershell
# 1. Xem trước thay đổi:
python [hub_path]\scripts\sync_spoke.py --spoke . --dry-run

# 2. Thực thi đồng bộ:
python [hub_path]\scripts\sync_spoke.py --spoke .
```

*Lưu ý:* Cơ chế **Selective Merge** sẽ tự động bảo vệ nguyên vẹn 100% các file workflows/skills nội bộ do Spoke tự viết (`🛡️ PRESERVED`).

---

### ⚡ Chế độ 4: Tải Bổ Sung Một Kỹ Năng / Workflow Cụ Thể (On-Demand)
Khi Agent cần bổ sung 1 kỹ năng cụ thể (ví dụ: `excalidraw-diagram`, `sharepoint-iac`) để xử lý yêu cầu tức thì của User:
1. Agent xin sự cho phép từ người dùng: *"Tôi cần tải bổ sung kỹ năng [tên-kỹ-năng] từ Hub, bạn có đồng ý không?"*
2. Sau khi người dùng đồng ý, chạy lệnh:
   ```powershell
   python [hub_path]\scripts\sync_spoke.py --spoke . --sync-item [tên-kỹ-năng]
   ```
3. Hệ thống sẽ tự động nạp kỹ năng mới (Auto-Discovery) mà không cần khởi động lại.

---

## 📋 Báo Cáo Kết Quả:
Sau khi hoàn tất, in bảng báo cáo tổng kết chi tiết gồm số lượng: `🟢 NEW`, `🔄 UPDATED`, `⚪ UNCHANGED`, `🛡️ PRESERVED`.
