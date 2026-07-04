---
description: Cập nhật thủ công các lệnh và kỹ năng mới từ Hub về dự án Spoke hiện tại
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Cập nhật CCBA Spoke Workspace

Workflow này cho phép dự án (Spoke) hiện tại đồng bộ hóa và tải về các bản cập nhật mới nhất (kịch bản lệnh, kỹ năng) từ trung tâm CCBA Agent Platform (Hub) thông qua python sync script.

## Khi nào dùng:
- Khi khởi tạo hoặc cần cập nhật lại toàn bộ Skills và Workflows của Spoke theo nghiệp vụ.
- Khi Agent phát hiện yêu cầu của User cần đến kỹ năng trên Hub nhưng chưa được tải về Spoke (On-Demand / Lazy Loading).

## Các bước thực hiện:

### 1. Định vị Hub Path
Agent đọc tệp cấu hình `.md/workspace_context.yaml` hoặc biến môi trường `CCBA_HUB_PATH` để lấy đường dẫn Hub (`hub_path`). Mặc định sử dụng repository chung.

### 2. Đồng bộ toàn bộ theo nghiệp vụ
Chạy lệnh đồng bộ tự động dựa trên `project_type` khai báo trong `workspace_context.yaml`:
```powershell
python [hub_path]\scripts\sync_spoke.py --spoke .
```

### 3. Đồng bộ bổ sung một Kỹ năng/Workflow cụ thể (On-Demand)
Khi Agent nhận thấy cần bổ sung một skill cụ thể (ví dụ: `excalidraw-diagram`) để xử lý yêu cầu của User:
1. Agent xin sự cho phép từ người dùng: *"Tôi cần tải bổ sung kỹ năng [excalidraw-diagram] từ Hub để vẽ sơ đồ, bạn có đồng ý không?"*
2. Sau khi người dùng đồng ý, chạy lệnh:
   ```powershell
   python [hub_path]\scripts\sync_spoke.py --spoke . --sync-item excalidraw-diagram
   ```
3. Sau khi đồng bộ bổ sung, Antigravity sẽ tự động nhận diện skill mới nạp (Auto-Discovery) mà không cần khởi động lại. Agent tiếp tục thực thi yêu cầu của User.

## Báo cáo kết quả:
- In ra thông báo: *"Đã đồng bộ thành công các thành phần cập nhật từ Hub về Spoke."*
