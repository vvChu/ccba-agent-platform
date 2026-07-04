# Kỹ năng: Đồng bộ hóa Thượng nguồn (Upstream Sync Skill)

Kỹ năng này hỗ trợ kiểm tra các bản cập nhật mới từ các kho chứa `claudekit-engineer`, `claudekit-marketing`, và `mattpocock/skills` trên remote GitHub, tự động clone hoặc pull về thư mục tạm cục bộ và thực hiện đánh giá để đưa ra khuyến nghị nâng cấp.

## Chỉ dẫn thực hiện:

### 1. Đồng bộ hóa mã nguồn Upstream
Chạy script Python để tự động clone/fetch các repository từ GitHub về thư mục tạm cục bộ `.md/scratch/repos/`:
```powershell
python scripts/check_claudekit_updates.py
```

### 2. Nghiên cứu và Phân tích Khuyến nghị
Chạy script phân tích cấu trúc của các repository thượng nguồn bằng AI Gateway để tự động tạo ra báo cáo khuyến nghị:
```powershell
python scripts/assess_upstream_features.py
```
Sau khi chạy xong, hãy đọc báo cáo tại [port_recommendations.md](../../../.md/knowledge/port_recommendations.md) để xem chi tiết các tính năng có thể porting.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
