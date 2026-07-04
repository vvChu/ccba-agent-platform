---
description: Kiểm tra cập nhật và đồng bộ tri thức từ ClaudeKit và MattPocock
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Đồng bộ tri thức từ các nguồn thượng nguồn (Upstream Sync)

Workflow này cho phép kiểm tra các bản cập nhật mới từ các kho chứa `claudekit-engineer`, `claudekit-marketing`, và `mattpocock/skills` trên remote GitHub, tự động clone hoặc pull về thư mục tạm cục bộ và thực hiện đánh giá để đưa ra khuyến nghị nâng cấp.

## Khi nào dùng:
- Khi kỹ sư muốn đồng bộ và xem có tri thức/kỹ năng mới nào từ thế giới bên ngoài (ClaudeKit, Matt Pocock) có thể áp dụng cho CCBA.
- Khi người dùng gõ lệnh `/ccba-sync-upstream`.

## Các bước thực hiện:

### 1. Thực thi script đồng bộ
Chạy script Python kiểm tra cập nhật và tự động clone/fetch cục bộ:
```powershell
python scripts/check_claudekit_updates.py
```

### 2. Xem kết quả và khuyến nghị
- Xem trạng thái đồng bộ được in ra trong log.
- Nếu có cập nhật mới và các khuyến nghị porting được tạo ra, hãy truy cập file [port_recommendations.md](../../.md/knowledge/port_recommendations.md) để xem chi tiết đánh giá từ AI Gateway.
